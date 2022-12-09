import logging

import ansys.api.additive.v0.additive_materials_pb2 as additive_materials_pb2
import ansys.api.additive.v0.additive_materials_pb2_grpc as additive_materials_pb2_grpc
import ansys.api.additive.v0.additive_simulation_pb2_grpc as additive_simulation_pb2_grpc
from google.protobuf.empty_pb2 import Empty
import grpc

from ansys.additive.material import AdditiveMaterial
import ansys.additive.microstructure as microstructure
import ansys.additive.misc as misc
import ansys.additive.porosity as porosity
import ansys.additive.progress_logger as progress_logger
import ansys.additive.single_bead as single_bead

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
        self._materials_stub = additive_materials_pb2_grpc.MaterialsServiceStub(self._channel)
        self._simulation_stub = additive_simulation_pb2_grpc.SimulationServiceStub(self._channel)

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
            If ``True``, call log_progress() method of :class:`progress_logger.ProgressLogger` when
            progress updates are received.

        Returns
        -------
        SingleBeadSummary or PorositySummary or MicrostructureSummary or ThermalHistorySummary
            The simulation summary, see :class:`single_bead.SingleBeadSummary`,
            :class:`porosity.PorositySummary`, :class:`microstructure.MicrostructureSummary`

        """
        # TODO: Add reference to ThermalHistorySummary above

        logger = progress_logger.ProgressLogger("Simulation")

        for response in self._simulation_stub.Simulate(input.to_simulation_request()):
            if log_progress and response.HasField("progress"):
                logger.log_progress(response.progress)
            if response.HasField("melt_pool"):
                return single_bead.SingleBeadSummary(input, response.melt_pool)
            if response.HasField("porosity_result"):
                return porosity.PorositySummary(input, response.porosity_result)
            if response.HasField("microstructure_result"):
                return microstructure.MicrostructureSummary(input, response.microstructure_result)
            # TODO: Return thermal history summary

    def get_materials_list(self):
        return self._materials_stub.GetMaterialsList(Empty())

    def get_material(self, name: str) -> AdditiveMaterial:
        request = additive_materials_pb2.GetMaterialRequest()
        request.name = name
        result = self._materials_stub.GetMaterial(request)
        return AdditiveMaterial.from_material_message(result)


def launch_additive(ip: str, port: int) -> Additive:
    return Additive(ip, port)
