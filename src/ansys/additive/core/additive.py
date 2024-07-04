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
import concurrent.futures
from datetime import datetime
import hashlib
import logging
import os
import zipfile

from ansys.api.additive import __version__ as api_version
from ansys.api.additive.v0.additive_materials_pb2 import (
    AddMaterialRequest,
    GetMaterialRequest,
    RemoveMaterialRequest,
)
from ansys.api.additive.v0.additive_simulation_pb2 import UploadFileRequest
from google.protobuf.empty_pb2 import Empty
import grpc

from ansys.additive.core import USER_DATA_PATH, __version__
from ansys.additive.core.download import download_file
from ansys.additive.core.exceptions import BetaFeatureNotEnabledError
from ansys.additive.core.logger import LOG
from ansys.additive.core.material import RESERVED_MATERIAL_NAMES, AdditiveMaterial
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
        if product_version is None or product_version == "":
            product_version = DEFAULT_PRODUCT_VERSION

        self._log = Additive._create_logger(log_file, log_level)
        self._log.debug("Logging set to %s", log_level)

        self._servers = Additive._connect_to_servers(
            server_connections, host, port, nservers, product_version, self._log, linux_install_path
        )
        self._nsims_per_server = nsims_per_server
        self._enable_beta_features = enable_beta_features

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

        Returns
        -------
        SingleBeadSummary, PorositySummary, MicrostructureSummary, ThermalHistorySummary,
        Microstructure3DSummary, SimulationError, list
            One or more summaries of simulation results. If a list of inputs is provided, a
            list is returned.
        """
        self._check_for_duplicate_id(inputs)

        if not isinstance(inputs, list):
            if not progress_handler:
                progress_handler = DefaultSingleSimulationProgressHandler()
            return self._simulate(inputs, self._servers[0], progress_handler)

        if len(inputs) == 0:
            raise ValueError("No simulation inputs provided")

        summaries = []
        LOG.info(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Starting {len(inputs)} simulations",
            end="",
        )
        threads = min(len(inputs), len(self._servers) * self._nsims_per_server)
        with concurrent.futures.ThreadPoolExecutor(threads) as executor:
            futures = []
            for i, input in enumerate(inputs):
                server_id = i % len(self._servers)
                futures.append(
                    executor.submit(
                        self._simulate,
                        input=input,
                        server=self._servers[server_id],
                        progress_handler=progress_handler,
                    )
                )
            for future in concurrent.futures.as_completed(futures):
                summary = future.result()
                if isinstance(summary, SimulationError):
                    LOG.error(f"\nError: {summary.message}")
                summaries.append(summary)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                LOG.info(
                    f"\r{timestamp} Completed {len(summaries)} of {len(inputs)} simulations",
                    end="",
                )
        return summaries

    def _simulate(
        self,
        input: (
            SingleBeadInput
            | PorosityInput
            | MicrostructureInput
            | ThermalHistoryInput
            | Microstructure3DInput
        ),
        server: ServerConnection,
        progress_handler: IProgressHandler | None = None,
    ) -> (
        SingleBeadSummary
        | PorositySummary
        | MicrostructureSummary
        | ThermalHistorySummary
        | Microstructure3DSummary
        | SimulationError
    ):
        """Execute a single simulation.

        Parameters
        ----------
        input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput,
        Microstructure3DInput
            Parameters to use for simulation.

        server: ServerConnection
            Server to use for the simulation.

        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.

        Returns
        -------
        SingleBeadSummary, PorositySummary, MicrostructureSummary, ThermalHistorySummary,
        Microstructure3DSummary, SimulationError
        """
        if input.material == AdditiveMaterial():
            raise ValueError("A material is not assigned to the simulation input")

        if isinstance(input, Microstructure3DInput) and self.enable_beta_features is False:
            raise BetaFeatureNotEnabledError(
                "3D microstructure simulations require beta features to be enabled.\n"
                + "Set enable_beta_features=True when creating the Additive client."
            )

        try:
            request = None
            if isinstance(input, ThermalHistoryInput):
                return self._simulate_thermal_history(
                    input, USER_DATA_PATH, server, progress_handler
                )
            else:
                request = input._to_simulation_request()

            for response in server.simulation_stub.Simulate(request):
                if response.HasField("progress"):
                    progress = Progress.from_proto_msg(input.id, response.progress)
                    if progress_handler:
                        progress_handler.update(progress)
                    if progress.state == ProgressState.ERROR:
                        raise Exception(progress.message)
                if response.HasField("melt_pool"):
                    thermal_history_output = None
                    if self._check_if_thermal_history_is_present(response):
                        thermal_history_output = os.path.join(
                            self._user_data_path, input.id, "thermal_history"
                        )
                        download_file(
                            self._servers[0].simulation_stub,
                            response.melt_pool.thermal_history_vtk_zip,
                            thermal_history_output,
                        )
                    return SingleBeadSummary(input, response.melt_pool, thermal_history_output)
                if response.HasField("porosity_result"):
                    return PorositySummary(input, response.porosity_result)
                if response.HasField("microstructure_result"):
                    return MicrostructureSummary(
                        input, response.microstructure_result, self._user_data_path
                    )
                if response.HasField("microstructure_3d_result"):
                    return Microstructure3DSummary(
                        input, response.microstructure_3d_result, self._user_data_path
                    )
        except Exception as e:
            return SimulationError(input, str(e))

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
            Requested material definition.
        """
        request = GetMaterialRequest(name=name)
        result = self._servers[0].materials_stub.GetMaterial(request)
        return AdditiveMaterial._from_material_message(result)

    @staticmethod
    def load_material(
        parameters_file: str, thermal_lookup_file: str, characteristic_width_lookup_file: str
    ) -> AdditiveMaterial:
        """Load a custom material definition for the current session. The resulting
        ``AdditiveMaterial`` object will not be saved to the library.

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

        Returns
        -------
        AdditiveMaterial
            A material definition for use in additive simulations.
        """
        material = AdditiveMaterial()
        material._load_parameters(parameters_file)
        material._load_thermal_properties(thermal_lookup_file)
        material._load_characteristic_width(characteristic_width_lookup_file)
        return material

    def add_material(
        self, parameters_file: str, thermal_lookup_file: str, characteristic_width_lookup_file: str
    ) -> AdditiveMaterial | None:
        """Add a custom material to the library for use in additive simulations.

        Parameters
        ----------
        parameters_file: str
            Name of the JSON file containing material parameters. For more information, see
            `Create Material Configuration File (.json)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_tool_create_tables.html>`_
            in the *Additive Manufacturing Beta Features* documentation.
        thermal_lookup_file: str
            Name of the CSV file containing the lookup table for temperature-dependent properties.
            For more information, see `Create Material Lookup File (.csv)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_create_mat_lookup.html>`_
            in the *Additive Manufacturing Beta Features* documentation.
        characteristic_width_lookup_file: str
            Name of the CSV file containing the lookup table for characteristic melt pool width. For
            more information, see
            `Find Characteristic Width Values and Generate Characteristic Width File (.csv)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_tool_find_cw.html>`_
            in the *Additive Manufacturing Beta Features* documentation.

        Returns
        -------
        AdditiveMaterial
            A definition of the material that was added to the library.
        """  # noqa: E501
        material = self.load_material(
            parameters_file, thermal_lookup_file, characteristic_width_lookup_file
        )

        names = self.materials_list()
        if material.name.lower() in (name.lower() for name in names):
            raise ValueError(f"Material {material.name} already exists. Unable to add material.")

        request = AddMaterialRequest(id=misc.short_uuid(), material=material._to_material_message())
        print(f"Adding material {request.material.description}")
        response = self._servers[0].materials_stub.AddMaterial(request)

        if response.HasField("error"):
            raise RuntimeError(response.error)

        return AdditiveMaterial._from_material_message(response.material)

    def remove_material(self, name: str):
        """Remove a material from the server.

        Parameters
        ----------
        name: str
            Name of the material to remove.
        """
        if name.lower() in (material.lower() for material in RESERVED_MATERIAL_NAMES):
            raise ValueError(f"Unable to remove Ansys-supplied material '{name}'.")

        self._servers[0].materials_stub.RemoveMaterial(RemoveMaterialRequest(name=name))

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

        for response in self._servers[0].materials_stub.TuneMaterial(request):
            if response.HasField("progress"):
                progress = Progress.from_proto_msg(input.id, response.progress)
                if progress.state == ProgressState.ERROR:
                    raise Exception(progress.message)
                else:
                    for m in progress.message.splitlines():
                        if (
                            "License successfully" in m
                            or "Starting ThermalSolver" in m
                            or "threads for solver" in m
                        ):
                            continue
                        LOG.info(m)
                        if progress_handler:
                            progress_handler.update(progress)
            if response.HasField("result"):
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

    def _simulate_thermal_history(
        self,
        input: ThermalHistoryInput,
        out_dir: str,
        server: ServerConnection,
        progress_handler: IProgressHandler | None = None,
    ) -> ThermalHistorySummary:
        """Run a thermal history simulation.

                Parameters
                ----------
                input: ThermalHistoryInput
                    Simulation input parameters.
                out_dir: str
                    Folder path for output files.
                server: ServerConnection
                    Server to use for the simulation.
                progress_handler: IPorgressHandler, None, default: None
                    Handler for progress updates. If ``None``, no progress updates are provided.
        .

                Returns
                -------
                :class:`ThermalHistorySummary`
        """
        if input.geometry is None or input.geometry.path == "":
            raise ValueError("The geometry path is not defined in the simulation input")

        remote_geometry_path = ""
        for response in server.simulation_stub.UploadFile(
            self.__file_upload_reader(input.geometry.path)
        ):
            remote_geometry_path = response.remote_file_name
            progress = Progress.from_proto_msg(input.id, response.progress)
            if progress_handler:
                progress_handler.update(progress)
            if progress.state == ProgressState.ERROR:
                raise Exception(progress.message)

        request = input._to_simulation_request(remote_geometry_path=remote_geometry_path)
        for response in server.simulation_stub.Simulate(request):
            if response.HasField("progress"):
                progress = Progress.from_proto_msg(input.id, response.progress)
                if progress_handler:
                    progress_handler.update(progress)
                if progress.state == ProgressState.ERROR and "WARN" not in progress.message:
                    raise Exception(progress.message)
            if response.HasField("thermal_history_result"):
                path = os.path.join(out_dir, input.id, "coax_ave_output")
                local_zip = download_file(
                    server.simulation_stub,
                    response.thermal_history_result.coax_ave_zip_file,
                    path,
                )
                with zipfile.ZipFile(local_zip, "r") as zip:
                    zip.extractall(path)
                os.remove(local_zip)
                return ThermalHistorySummary(input, path)

    def _check_for_duplicate_id(self, inputs):
        if not isinstance(inputs, list):
            return
        ids = []
        for input in inputs:
            if input.id == "":
                input.id = misc.short_uuid()
            if input.id in ids:
                raise ValueError(f'Duplicate simulation ID "{input.id}" in input list')
            ids.append(input.id)

    def _check_if_thermal_history_is_present(self, response) -> bool:
        """Check if thermal history output is present in the response."""
        return response.melt_pool.thermal_history_vtk_zip != str()
