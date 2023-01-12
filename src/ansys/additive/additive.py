# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
    additive.py
    -----------

    This module contains the Additive class which interacts with the Additive service.
"""
import hashlib
import logging
import os
from typing import Iterator

from ansys.api.additive.v0.additive_domain_pb2 import ProgressState
from ansys.api.additive.v0.additive_materials_pb2 import GetMaterialRequest
from ansys.api.additive.v0.additive_materials_pb2_grpc import MaterialsServiceStub
from ansys.api.additive.v0.additive_simulation_pb2 import UploadFileRequest
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub
import ansys.platform.instancemanagement as pypim
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
DEFAULT_ADDITIVE_SERVICE_PORT = 50052
LOCALHOST = "127.0.0.1"


class Additive:
    """
    Client interface to Additive service. The method :meth:`simulate` is
    used to execute simulations.
    """

    def __init__(
        self,
        ip: str = None,
        port: int = None,
        loglevel: str = "INFO",
        log_file: str = "",
        channel: grpc.Channel = None,
    ):
        """Initialize connection to the server."""
        if channel is not None and (ip is not None or port is not None):
            raise ValueError("If `channel` is specified, neither `port` nor `ip` can be specified.")

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

    def __del__(self):
        """Destructor, used to clean up service connection."""
        if self._server_instance:
            self._server_instance.delete()

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

    def _create_channel(self, ip: str = None, port: int = None, product_version: str = None):
        """
        Create an insecure grpc channel.

        A channel connection will be established using one of the following methods.
        The methods are listed in order of precedence.
            1. Using the user provided ip and port values, if any
            2. Using PyPim if the client is running in a PyPim enabled environment
                such as Ansys Lab
            3. Using an ip and port definition string defined by the
                ANSYS_ADDITIVE_ADDRESS environment variable
            4. Using a default ip and port, `localhost:50052`

        Parameters
        ----------

        ip: str
            Internet protocol address of remote server host in IPv4 dotted-quad string format.

        port: int
            Port number on server to connect to.

        product_version: str
            Additive server product version. Only applies in PyPim environments.

        """

        if ip and port:
            misc.check_valid_ip(ip)
            misc.check_valid_port(port)
            return self.__open_insecure_channel(f"{ip}:{port}")

        elif pypim.is_configured():
            pim = pypim.connect()
            self._server_instance = pim.create_instance(
                product_name="additive", product_version=product_version
            )
            self._log.info("Waiting for server to initialize")
            self._server_instance.wait_for_ready()
            (_, target) = self._server_instance.services["grpc"].uri.split(":", 1)
            return self.__open_insecure_channel(target)

        elif os.getenv("ANSYS_ADDITIVE_ADDRESS"):
            return self.__open_insecure_channel(os.getenv("ANSYS_ADDITIVE_ADDRESS"))

        else:
            return self.__open_insecure_channel(f"{LOCALHOST}:{DEFAULT_ADDITIVE_SERVICE_PORT}")

    def __open_insecure_channel(self, target: str) -> grpc.Channel:
        """Open an insecure grpc channel to a given target."""
        self._log.info("Opening insecure channel at %s", target)
        return grpc.insecure_channel(
            target, options=[("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH)]
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
        """Execute an additive simulation.

        Parameters
        ----------
        input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput
            Parameters to use during simulation.

        log_progress: bool
            If ``True``, send progress updates to user interface.

        Returns
        -------
        :class:`SingleBeadSummary`
        or :class:`PorositySummary`
        or :class:`MicrostructureSummary`
        or :class:`ThermalHistorySummary`

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
            request = input._to_simulation_request(remote_geometry_path=remote_geometry_path)
        else:
            request = input._to_simulation_request()

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

    def get_materials_list(self) -> list[str]:
        """Retrieve a list of material names used in additive simulations.

        Returns
        -------
        list[str]
            Names of available additive materials.

        """
        return self._materials_stub.GetMaterialsList(Empty())

    def get_material(self, name: str) -> AdditiveMaterial:
        """Return a specified material for use in an additive simulation.

        Parameters
        ----------

        name: str
            Name of material.

        Returns
        -------
        AdditiveMaterial

        """
        request = GetMaterialRequest()
        request.name = name
        result = self._materials_stub.GetMaterial(request)
        return AdditiveMaterial._from_material_message(result)

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
        """Download results for a simulation."""
        if isinstance(summary, ThermalHistorySummary):
            path = os.path.join(folder, summary.input.id)
            return download_file(self._simulation_stub, summary.remote_coax_ave_zip_file, path)
        raise ValueError("Only thermal history summaries have remote results that require download")
