import logging

import ansys.api.additive.v0.additive_materials_pb2 as additive_materials_pb2
import ansys.api.additive.v0.additive_materials_pb2_grpc as additive_materials_pb2_grpc
import ansys.api.additive.v0.additive_simulation_pb2 as additive_simulation_pb2
import ansys.api.additive.v0.additive_simulation_pb2_grpc as additive_simulation_pb2_grpc
from google.protobuf.empty_pb2 import Empty
import grpc

from ansys.additive.material import AdditiveMaterial
import ansys.additive.microstructure as microstructure
from ansys.additive.microstructure import MicrostructureInput
import ansys.additive.misc as misc
import ansys.additive.porosity as porosity
from ansys.additive.porosity import PorosityInput
import ansys.additive.progress_logger as progress_logger
import ansys.additive.single_bead as single_bead
from ansys.additive.single_bead import SingleBeadInput

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

    def simulate_single_bead(
        self, input: SingleBeadInput, log_progress: bool = True
    ) -> single_bead.SingleBeadSummary:
        """Execute a single bead simulation

        Parameters
        ----------
        input: SingleBeadInput
            Parameters to use during simulation.

        log_progress: bool
            If ``True``, call log_progress() method of :class:`progress_logger.ProgressLogger` when
            progress updates are received.

        Returns
        -------
        SingleBeadSummary
            The simulation summary, see :class:`single_bead.SingleBeadSummary`

        """

        logger = progress_logger.ProgressLogger(self.simulate_single_bead.__name__)

        request = additive_simulation_pb2.SimulateSingleBeadRequest(
            machine=input.machine.to_machine_message(),
            material=input.material.to_material_message(),
            bead_length=input.bead_length,
        )
        if input.bead_type is single_bead.BeadType.BEAD_ON_BASE_PLATE:
            request.bead_type = additive_simulation_pb2.BEAD_TYPE_BEAD_ON_BASE_PLATE
        elif input.bead_type is single_bead.BeadType.BEAD_ON_POWDER:
            request.bead_type = additive_simulation_pb2.BEAD_TYPE_BEAD_ON_POWDER_LAYER
        else:
            raise ValueError("Invalid bead type: " + input.bead_type)

        for response in self._simulation_stub.SimulateSingleBead(request):
            if log_progress and response.HasField("progress"):
                logger.log_progress(response.progress)
            if response.HasField("melt_pool"):
                return single_bead.SingleBeadSummary(input, response.melt_pool)

    def get_materials_list(self):
        return self._materials_stub.GetMaterialsList(Empty())

    def get_material(self, name: str) -> AdditiveMaterial:
        request = additive_materials_pb2.GetMaterialRequest()
        request.name = name
        result = self._materials_stub.GetMaterial(request)
        return AdditiveMaterial.from_material_message(result)

    def simulate_porosity(
        self, input: PorosityInput, log_progress: bool = True
    ) -> porosity.PorosityResult:
        """Simulate the additive manufacture of a sample cube and calculate its porosity

        Parameters
        ----------
        input : PorosityInput
            Parameters to use during simulation.

        log_progress: bool
            If True, call log_progress() method of :class:`progress_logger.ProgressLogger` when
            progress updates are received.


        Returns
        -------
        PorosityResult
            The simulation result, see :class:`porosity.PorosityResult`

        """

        logger = progress_logger.ProgressLogger(self.simulate_porosity.__name__)

        request = additive_simulation_pb2.SimulatePorosityRequest(
            machine=input.machine.to_machine_message(),
            material=input.material.to_material_message(),
            size_x=input.size_x,
            size_y=input.size_y,
            size_z=input.size_z,
        )

        for response in self._simulation_stub.SimulatePorosity(request):
            if log_progress and response.HasField("progress"):
                logger.log_progress(response.progress)
            if response.HasField("porosity_result"):
                return porosity.PorositySummary(input, response.porosity_result)

    def simulate_microstructure(
        self, input: MicrostructureInput, log_progress: bool = True
    ) -> microstructure.MicrostructureResult:
        """Simulate the additive manufacture of a sample cube and determine its microstructure

        Parameters
        ----------
        input : MicrostructureInput
            Parameters to use during simulation.

        log_progress: bool
            If True, call log_progress() method of :class:`progress_logger.ProgressLogger` when
            progress updates are received.


        Returns
        -------
        MicrostructureResult
            The simulation result, see :class:`microstructure.MicrostructureResult`

        """

        logger = progress_logger.ProgressLogger(self.simulate_microstructure.__name__)

        for response in self._simulation_stub.SimulateMicrostructure(input.to_simulation_request()):
            if log_progress and response.HasField("progress"):
                logger.log_progress(response.progress)
            if response.HasField("microstructure_result"):
                return microstructure.MicrostructureSummary(input, response.microstructure_result)


def launch_additive(ip: str, port: int) -> Additive:
    return Additive(ip, port)
