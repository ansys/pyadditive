# (c) ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import hashlib
import logging
import os
from typing import Iterator

from ansys.api.additive.v0.additive_domain_pb2 import ProgressState
from ansys.api.additive.v0.additive_materials_pb2 import GetMaterialRequest
from ansys.api.additive.v0.additive_materials_pb2_grpc import MaterialsServiceStub
from ansys.api.additive.v0.additive_simulation_pb2 import UploadFileRequest
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub
from google.protobuf.empty_pb2 import Empty
import grpc

from ansys.additive.download import download_file
from ansys.additive.material import AdditiveMaterial
from ansys.additive.microstructure import MicrostructureSummary
import ansys.additive.misc as misc
from ansys.additive.porosity import PorositySummary
from ansys.additive.progress_logger import ProgressLogger, ProgressState
from ansys.additive.single_bead import SingleBeadSummary
from ansys.additive.thermal_history import ThermalHistoryInput, ThermalHistorySummary

MAX_MESSAGE_LENGTH = int(256 * 1024**2)
DEFAULT_ADDITIVE_SERVICE_PORT = 5000


class Additive:
    """Additive simulation runner"""

    def __init__(
        self,
        ip: str = None,
        port: int = None,
        loglevel: str = "INFO",
        log_file: str = "",
        channel: grpc.Channel = None,
    ):
        """Initialize connection to the server"""
        if channel is not None:
            if ip is not None or port is not None:
                raise ValueError(
                    "If `channel` is specified, neither `port` nor `ip` can be specified."
                )
        else:
            if ip is None:
                ip = "127.0.0.1"
            if port is None:
                port = DEFAULT_ADDITIVE_SERVICE_PORT

        self._log = self._create_logger(log_file, loglevel)
        self._log.debug("Logging set to %s", loglevel)

        if channel:
            self._channel = channel
        else:
            self._channel = self._create_channel(ip, port)
        self._log.info("Connected to %s", self._channel_str)

        # assign service stubs
        self._materials_stub = MaterialsServiceStub(self._channel)
        self._simulation_stub = SimulationServiceStub(self._channel)

    def _create_logger(self, log_file, loglevel) -> logging.Logger:
        """Create the logger for this module"""
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError("Invalid log level: %s" % loglevel)
        if log_file:
            if not isinstance(log_file, str):
                log_file = "instance.log"
            logging.basicConfig(filename=log_file, level=numeric_level)
        else:
            logging.basicConfig(level=numeric_level)
        return logging.getLogger(__name__)

    def _create_channel(self, ip, port):
        """Create an insecured grpc channel."""
        misc.check_valid_ip(ip)
        misc.check_valid_port(port)

        # open the channel
        channel_str = f"{ip}:{port}"
        self._log.debug("Opening insecure channel at %s", channel_str)
        return grpc.insecure_channel(
            channel_str,
            options=[
                ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
            ],
        )

    @property
    def _channel_str(self):
        """Return the target string.

        Generally of the form of "ip:port", like "127.0.0.1:50052".

        """
        if self._channel is not None:
            return self._channel._channel.target().decode()
        return ""

    def simulate(self, input, log_progress: bool = True):
        """Execute a single bead simulation

        Parameters
        ----------
        input: SingleBeadInput or PorosityInput or MicrostructureInput or ThermalHistoryInput
            Parameters to use during simulation.

        log_progress: bool
            If ``True``, call log_progress() method of
            :class:`ansys.additive.progress_logger.ProgressLogger`
            when progress updates are received.

        Returns
        -------
        SingleBeadSummary or PorositySummary or MicrostructureSummary or ThermalHistorySummary
            The simulation summary, see
            :class:`ansys.additive.single_bead.SingleBeadSummary`,
            :class:`ansys.additive.porosity.PorositySummary`,
            :class:`ansys.additive.microstructure.MicrostructureSummary`,
            :class:`ansys.additive.thermal_history.ThermalHistorySummary`

        """
        logger = ProgressLogger("Simulation")

        remote_geometry_path = ""
        request = None
        if isinstance(input, ThermalHistoryInput):
            if input.geometry == None or input.geometry.path == "":
                raise ValueError("Geometry path not defined")
            for response in self._simulation_stub.UploadFile(
                self.__file_upload_reader(input.geometry.path)
            ):
                remote_geometry_path = response.remote_file_name
                if log_progress:
                    logger.log_progress(response.progress)
                if response.progress.state == ProgressState.PROGRESS_STATE_ERROR:
                    # TODO: figure out a better way to notify user of error
                    print("ERROR: " + response.progress.message)
                    return None
            request = input.to_simulation_request(remote_geometry_path=remote_geometry_path)
        else:
            request = input.to_simulation_request()

        for response in self._simulation_stub.Simulate(request):
            if log_progress and response.HasField("progress"):
                logger.log_progress(response.progress)
            if response.HasField("melt_pool"):
                return SingleBeadSummary(input, response.melt_pool)
            if response.HasField("porosity_result"):
                return PorositySummary(input, response.porosity_result)
            if response.HasField("microstructure_result"):
                return MicrostructureSummary(input, response.microstructure_result)
            if response.HasField("thermal_history_result"):
                return ThermalHistorySummary(input, response.thermal_history_result)

    def get_materials_list(self):
        return self._materials_stub.GetMaterialsList(Empty())

    def get_material(self, name: str) -> AdditiveMaterial:
        request = GetMaterialRequest()
        request.name = name
        result = self._materials_stub.GetMaterial(request)
        return AdditiveMaterial.from_material_message(result)

    def __file_upload_reader(
        self, file_name: str, chunk_size=2 * 1024 * 1024
    ) -> Iterator[UploadFileRequest]:
        """Read a file and return an iterator of UploadFileRequests"""
        file_size = os.path.getsize(file_name)
        short_name = os.path.basename(file_name)
        with open(file_name, mode="rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield UploadFileRequest(
                    name=short_name,
                    total_size=file_size,
                    content=chunk,
                    content_md5=hashlib.md5(chunk).hexdigest(),
                )

    def download_results(self, summary, folder: str) -> str:
        if isinstance(summary, ThermalHistorySummary):
            path = os.path.join(folder, summary.input.id)
            return download_file(self._simulation_stub, summary.remote_coax_ave_zip_file, path)
        raise ValueError("Only thermal history summaries have remote results that require download")


def launch_additive(ip: str, port: int) -> Additive:
    return Additive(ip, port)
