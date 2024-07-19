# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Provides a client for interacting with the Additive service."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
import hashlib
import logging
import os
import zipfile

from ansys.api.additive import __version__ as api_version
from ansys.api.additive.v0.additive_materials_pb2 import GetMaterialRequest, TuneMaterialResponse
from ansys.api.additive.v0.additive_operations_pb2 import OperationMetadata
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationResponse, UploadFileRequest
from google.longrunning.operations_pb2 import Operation
from google.protobuf.any_pb2 import Any
from google.protobuf.empty_pb2 import Empty
import grpc

from ansys.additive.core import USER_DATA_PATH, __version__
from ansys.additive.core.exceptions import BetaFeatureNotEnabledError
from ansys.additive.core.logger import LOG
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.material_tuning import MaterialTuningInput, MaterialTuningSummary
from ansys.additive.core.microstructure import MicrostructureInput, MicrostructureSummary
from ansys.additive.core.microstructure_3d import Microstructure3DInput, Microstructure3DSummary
import ansys.additive.core.misc as misc
from ansys.additive.core.porosity import PorosityInput, PorositySummary
from ansys.additive.core.progress_handler import (
    DefaultSingleSimulationProgressHandler,
    IProgressHandler,
    Progress,
    ProgressState,
)
from ansys.additive.core.server_connection import DEFAULT_PRODUCT_VERSION, ServerConnection
from ansys.additive.core.simulation import SimulationError
from ansys.additive.core.simulation_task import SimulationTask
from ansys.additive.core.single_bead import SingleBeadInput, SingleBeadSummary
from ansys.additive.core.thermal_history import ThermalHistoryInput, ThermalHistorySummary


class Additive:
    """Provides the client interface to one or more Additive services.

    In a typical cloud environment, a single Additive service with load balancing and
    auto-scaling is used. The ``Additive`` client connects to the service via a
    single connection. However, for atypical environments or when running on localhost,
    the ``Additive`` client can perform crude load balancing by connecting to multiple
    servers and distributing simulations across them. You can use the ``server_connections``,
    ``nservers``, and ``nsims_per_server`` parameters to control the
    number of servers to connect to and the number of simulations to run on each
    server.

    Parameters
    ----------
    server_connections: list[str, grpc.Channel], None
        List of connection definitions for servers. The list may be a combination of strings and
        connected :class:`grpc.Channel <grpc.Channel>` objects. Strings use the format
        ``host:port`` to specify the server IPv4 address.
    host: str, default: None
        Host name or IPv4 address of the server. This parameter is ignored if the
        ``server_channels`` or ``channel`` parameters is other than ``None``.
    port: int, default: 50052
        Port number to use when connecting to the server.
    nsims_per_server: int, default: 1
        Number of simultaneous simulations to run on each server. Each simulation
        requires a license checkout. If a license is not available, the simulation
        fails.
    nservers: int, default: 1
        Number of Additive servers to start and connect to. This parameter is only
        applicable in `PyPIM`_-enabled cloud environments and on localhost. For
        this to work on localhost, the Additive portion of the Ansys Structures
        package must be installed. This parameter is ignored if the ``server_connections``
        parameter or ``host`` parameter is other than ``None``.
    product_version: str
        Version of the Ansys product installation in the form ``"YYR"``, where ``YY``
        is the two-digit year and ``R`` is the release number. For example, the release
        2024 R1 would be specified as ``241``. This parameter is only applicable in
        `PyPIM`_-enabled cloud environments and on localhost. Using an empty string
        or ``None`` uses the default product version.
    log_level: str, default: "INFO"
        Minimum severity level of messages to log.
    log_file: str, default: ""
        File name to write log messages to.
    enable_beta_features: bool, default: False
        Flag indicating if beta features are enabled.
    linux_install_path: os.PathLike, None, default: None
        Path to the Ansys installation directory on Linux. This parameter is only
        required when Ansys has not been installed in the default location. Example:
        ``/usr/shared/ansys_inc``. Note that the path should not include the product
        version.

    Examples
    --------
    Connect to a list of servers. Multiple connections to the same host are permitted.

    >>> additive = Additive(server_connections=["localhost:50052", "localhost:50052", "myserver:50052"])

    Connect to a single server using the host name and port number.

    >>> additive = Additive(host="additive.ansys.com", port=12345)

    Start and connect to two servers on localhost or in a
    `PyPIM`_-enabled cloud environment. Allow each server to run two
    simultaneous simulations.

    >>> additive = Additive(nsims_per_server=2, nservers=2)

    Start a single server on localhost or in a `PyPIM`_-enabled cloud environment.
    Use version 2024 R1 of the Ansys product installation.

    >>> additive = Additive(product_version="241")

    .. _PyPIM: https://pypim.docs.pyansys.com/version/stable/index.html
    """

    DEFAULT_ADDITIVE_SERVICE_PORT = 50052

    def __init__(
        self,
        server_connections: list[str | grpc.Channel] = None,
        host: str | None = None,
        port: int = DEFAULT_ADDITIVE_SERVICE_PORT,
        nsims_per_server: int = 1,
        nservers: int = 1,
        product_version: str = DEFAULT_PRODUCT_VERSION,
        log_level: str = "INFO",
        log_file: str = "",
        enable_beta_features: bool = False,
        linux_install_path: os.PathLike | None = None,
    ) -> None:
        """Initialize server connections."""
        if not product_version:
            product_version = DEFAULT_PRODUCT_VERSION

        self._log = Additive._create_logger(log_file, log_level)
        self._log.debug("Logging set to %s", log_level)

        self._servers = Additive._connect_to_servers(
            server_connections, host, port, nservers, product_version, self._log, linux_install_path
        )
        self._nsims_per_server = nsims_per_server
        self._enable_beta_features = enable_beta_features

        self._progress_handler = None

        # Store any simulation inputs given to this class in case multiple asynchronous simulation calls
        # are made. The assumption is that all simulations handled by this class have a unique id.
        self._simulation_inputs = []

        # Setup data directory
        self._user_data_path = USER_DATA_PATH
        if not os.path.exists(self._user_data_path):  # pragma: no cover
            os.makedirs(self._user_data_path)
        LOG.info("user data path: " + self._user_data_path)

    @staticmethod
    def _create_logger(log_file, log_level) -> logging.Logger:
        """Instantiate the logger."""
        format = "%(asctime)s %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError("Invalid log level: %s" % log_level)
        logging.basicConfig(
            level=numeric_level,
            format=format,
            datefmt=datefmt,
        )
        log = logging.getLogger(__name__)
        if log_file:
            file_handler = logging.FileHandler(str(log_file))
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(logging.Formatter(format))
            log.file_handler = file_handler
            log.addHandler(file_handler)
        return log

    @staticmethod
    def _connect_to_servers(
        server_connections: list[str | grpc.Channel] = None,
        host: str | None = None,
        port: int = DEFAULT_ADDITIVE_SERVICE_PORT,
        nservers: int = 1,
        product_version: str = DEFAULT_PRODUCT_VERSION,
        log: logging.Logger = None,
        linux_install_path: os.PathLike | None = None,
    ) -> list[ServerConnection]:
        """Connect to Additive servers.

        Start them if necessary.
        """
        connections = []
        if server_connections:
            for target in server_connections:
                if isinstance(target, grpc.Channel):
                    connections.append(ServerConnection(channel=target, log=log))
                else:
                    connections.append(ServerConnection(addr=target, log=log))
        elif host:
            connections.append(ServerConnection(addr=f"{host}:{port}", log=log))
        elif os.getenv("ANSYS_ADDITIVE_ADDRESS"):
            connections.append(ServerConnection(addr=os.getenv("ANSYS_ADDITIVE_ADDRESS"), log=log))
        else:
            for _ in range(nservers):
                connections.append(
                    ServerConnection(
                        product_version=product_version,
                        log=log,
                        linux_install_path=linux_install_path,
                    )
                )

        return connections

    @property
    def nsims_per_server(self) -> int:
        """Number of simultaneous simulations to run on each server."""
        return self._nsims_per_server

    @nsims_per_server.setter
    def nsims_per_server(self, value: int) -> None:
        """Set the number of simultaneous simulations to run on each server."""
        if value < 1:
            raise ValueError("Number of simulations per server must be greater than zero.")
        self._nsims_per_server = value

    @property
    def enable_beta_features(self) -> bool:
        """Flag indicating if beta features are enabled."""
        return self._enable_beta_features

    @enable_beta_features.setter
    def enable_beta_features(self, value: bool) -> None:
        """Set the flag indicating if beta features are enabled."""
        self._enable_beta_features = value

    def about(self) -> None:
        """Print information about the client and server."""
        print(f"Client {__version__}, API version: {api_version}")
        if self._servers is None:
            print("Client is not connected to a server.")
            return
        else:
            for server in self._servers:
                print(server.status())

    def simulate(
        self,
        inputs: (
            SingleBeadInput
            | PorosityInput
            | MicrostructureInput
            | ThermalHistoryInput
            | Microstructure3DInput
            | list
        ),
        progress_handler: IProgressHandler | None = None,
    ) -> (
        SingleBeadSummary
        | PorositySummary
        | MicrostructureSummary
        | ThermalHistorySummary
        | Microstructure3DSummary
        | SimulationError
        | list
    ):
        """Execute additive simulations.

        Parameters
        ----------
        inputs: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput,
        Microstructure3DInput, list
            Parameters to use for simulations. A list of inputs may be provided to run multiple
            simulations.
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, and ``inputs`` contains a single
            simulation input, a default progress handler will be assigned.
        """
        task = self.simulate_async(inputs, progress_handler)
        task.wait_all()

        summaries = []

        errors = task.collect_errors()
        if errors:
            if isinstance(errors, list):
                summaries += errors
                for e in errors:
                    LOG.error(f"\nError: {e.message}")
            else:
                # Single error
                summaries.append(errors)
                LOG.error(f"\nError: {errors.message}")

        results = task.collect_results()
        if results:
            if isinstance(results, list):
                summaries += results
            else:
                # single result
                summaries.append(results)

        return summaries

    def simulate_async(
        self,
        inputs: (
            SingleBeadInput
            | PorosityInput
            | MicrostructureInput
            | ThermalHistoryInput
            | Microstructure3DInput
            | list
        ),
        progress_handler: IProgressHandler | None = None,
    ):
        """Execute additive simulations asynchronously. This method does not block while the
        simulations are running on the server. This class stores handles of type
        google.longrunning.Operation to the remote tasks that can be used to communicate with
        the server for status updates.

        Parameters
        ----------
        inputs: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput,
        Microstructure3DInput, list
            Parameters to use for simulations. A list of inputs may be provided to run multiple
            simulations.
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, and ``inputs`` contains a single
            simulation input, a default progress handler will be assigned.
        """
        self._check_for_duplicate_id(inputs)

        simulation_task = SimulationTask(self._servers, self._user_data_path, progress_handler)

        self._progress_handler = progress_handler

        if not isinstance(inputs, list):
            if not progress_handler:
                self._progress_handler = DefaultSingleSimulationProgressHandler()
            server = self._servers[0]
            operation = self._simulate(inputs, server)
            simulation_task.add_simulation(server.channel_str, operation, inputs)
            return simulation_task

        if len(inputs) == 0:
            raise ValueError("No simulation inputs provided")

        LOG.info(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Starting {len(inputs)} simulations",
            end="",
        )
        for i, sim_input in enumerate(inputs):
            server_id = i % len(self._servers)
            server = self._servers[server_id]
            operation = self._simulate(sim_input, server)
            simulation_task.add_simulation(server.channel_str, operation, sim_input)

        return simulation_task

    def _simulate(
        self,
        simulation_input: (
            SingleBeadInput
            | PorosityInput
            | MicrostructureInput
            | ThermalHistoryInput
            | Microstructure3DInput
        ),
        server: ServerConnection,
    ) -> Operation:
        """Execute a single simulation.

        Parameters
        ----------
        simulation_input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput,
        Microstructure3DInput
            Parameters to use for simulation.

        server: ServerConnection
            Server to use for the simulation.

        Returns
        -------
        A long running operation
        """
        if simulation_input.material == AdditiveMaterial():
            raise ValueError("A material is not assigned to the simulation input")

        if (
            isinstance(simulation_input, Microstructure3DInput)
            and self.enable_beta_features is False
        ):
            raise BetaFeatureNotEnabledError(
                "3D microstructure simulations require beta features to be enabled.\n"
                + "Set enable_beta_features=True when creating the Additive client."
            )

        try:
            if isinstance(simulation_input, ThermalHistoryInput):
                request = self._setup_thermal_history(simulation_input, server)
            else:
                request = simulation_input._to_simulation_request()
            long_running_op = server.simulation_stub.Simulate(request)
            return long_running_op

        except Exception as e:
            metadata = OperationMetadata(simulation_id=simulation_input.id, message=str(e))
            errored_op = Operation(name=simulation_input.id, done=True)
            errored_op.metadata.Pack(metadata)
            return errored_op

    def materials_list(self) -> list[str]:
        """Get a list of material names used in additive simulations.

        Returns
        -------
        list[str]
            Names of available additive materials.
        """
        response = self._servers[0].materials_stub.GetMaterialsList(Empty())
        return [n for n in response.names]

    def material(self, name: str) -> AdditiveMaterial:
        """Get a material for use in an additive simulation.

        Parameters
        ----------

        name: str
            Name of material.

        Returns
        -------
        AdditiveMaterial
        """
        request = GetMaterialRequest(name=name)
        result = self._servers[0].materials_stub.GetMaterial(request)
        return AdditiveMaterial._from_material_message(result)

    @staticmethod
    def load_material(
        parameters_file: str, thermal_lookup_file: str, characteristic_width_lookup_file: str
    ) -> AdditiveMaterial:
        """Load a user-provided material definition.

        Parameters
        ----------
        parameters_file: str
            Name of the JSON file containing material parameters. For more information, see
            `Create Material Configuration File (.json)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_tool_create_tables.html>`_
            in the *Additive Manufacturing Beta Features* documentation.
        thermal_lookup_file: str
            Name of the CSV file containing the lookup table for thermal dependent properties.
            For more information, see `Create Material Lookup File (.csv)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_create_mat_lookup.html>`_
            in the *Additive Manufacturing Beta Features* documentation.
        characteristic_width_lookup_file: str
            Name of the CSV file containing the lookup table for characteristic melt pool width. For
            more information, see
            `Find Characteristic Width Values and Generate Characteristic Width File (.csv)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_tool_find_cw.html>`_
            in the *Additive Manufacturing Beta Features* documentation.
        """
        material = AdditiveMaterial()
        material._load_parameters(parameters_file)
        material._load_thermal_properties(thermal_lookup_file)
        material._load_characteristic_width(characteristic_width_lookup_file)
        return material

    def tune_material(
        self,
        input: MaterialTuningInput,
        out_dir: str = USER_DATA_PATH,
        progress_handler: IProgressHandler = None,
    ) -> MaterialTuningSummary:
        """Tune a custom material for use with additive simulations.

        This method performs the same function as the Material Tuning Tool
        described in
        `Find Simulation Parameters to Match Simulation to Experiments
        <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_tool_match_sim_to_exp.html>`_.
        It is used for one step in the material tuning process. The other steps
        are described in
        `Chapter 2: Material Tuning Tool (Beta) to Create User Defined Materials
        <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_science_BETA_material_tuning_tool.html>`_.

        Parameters
        ----------
        input: MaterialTuningInput
            Input parameters for material tuning.
        out_dir: str, default: USER_DATA_PATH
            Folder path for output files.
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.

        Returns
        -------
        MaterialTuningSummary
            Summary of material tuning.
        """  # noqa: E501
        if input.id == "":
            input.id = misc.short_uuid()
        if out_dir == USER_DATA_PATH:
            out_dir = os.path.join(out_dir, input.id)

        if os.path.exists(out_dir):
            raise ValueError(
                f"Directory {out_dir} already exists. Delete or choose a different output directory."
            )

        request = input._to_request()

        operation = self._servers[0].materials_stub.TuneMaterial(request)

        task = SimulationTask([self._servers[0]], out_dir, progress_handler)
        task.add_simulation(self._servers[0].channel_str, operation, input)
        task.wait_all()

        operation = task.get_operation(input.id)
        response = TuneMaterialResponse()
        operation.response.Unpack(response)
        if not response.HasField("result"):
            raise Exception("Material tuning result not found")

        return MaterialTuningSummary(input, response.result, out_dir)

    def __file_upload_reader(
        self, file_name: str, chunk_size=2 * 1024**2
    ) -> Iterator[UploadFileRequest]:
        """Read a file and return an iterator of UploadFileRequests."""
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

    def _setup_thermal_history(self, input: ThermalHistoryInput, server: ServerConnection):
        """Setup a thermal history simulation.

        Parameters
        ----------
        input: ThermalHistoryInput
            Simulation input parameters.
        server: ServerConnection
            Server to use for the simulation.

        Returns
        -------
        :class:`SimulationRequest`
        """
        if not input.geometry or not input.geometry.path:
            raise ValueError("The geometry path is not defined in the simulation input")

        remote_geometry_path = ""
        for response in server.simulation_stub.UploadFile(
            self.__file_upload_reader(input.geometry.path)
        ):
            remote_geometry_path = response.remote_file_name
            progress = Progress.from_proto_msg(input.id, response.progress)
            if self._progress_handler:
                self._progress_handler.update(progress)
            if progress.state == ProgressState.ERROR:
                raise Exception(progress.message)

        return input._to_simulation_request(remote_geometry_path=remote_geometry_path)

    def _check_for_duplicate_id(self, inputs):
        if not isinstance(inputs, list):
            # An individual input, not a list
            if inputs.id == "":
                inputs.id = misc.short_uuid()
            if any([x for x in self._simulation_inputs if x.id == inputs.id]):
                raise ValueError(f'Duplicate simulation ID "{i.id}" in input list')

            self._simulation_inputs.append(inputs)
            return

        # list of inputs
        ids = []
        for i in inputs:
            if not i.id:
                # give input an id if none given
                i.id = misc.short_uuid()
            if any([x for x in self._simulation_inputs if x.id == i.id]):
                # id given previously
                raise ValueError(
                    f'Duplicate simulation ID "{i.id}" given in previous simulation calls'
                )
            if any([x for x in ids if x == i.id]):
                raise ValueError(f'Duplicate simulation ID "{i.id}" in input list')
            ids.append(i.id)
