# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
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
"""Provides for interacting with the Additive service."""

from __future__ import annotations

from collections.abc import Iterator
import concurrent.futures
from datetime import datetime
import hashlib
import logging
import os
import zipfile

from ansys.api.additive import __version__ as api_version
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState
from ansys.api.additive.v0.additive_materials_pb2 import GetMaterialRequest
from ansys.api.additive.v0.additive_simulation_pb2 import UploadFileRequest
from google.protobuf.empty_pb2 import Empty
import grpc

from ansys.additive.core import USER_DATA_PATH, __version__
from ansys.additive.core.download import download_file
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.material_tuning import MaterialTuningInput, MaterialTuningSummary
from ansys.additive.core.microstructure import MicrostructureSummary
import ansys.additive.core.misc as misc
from ansys.additive.core.porosity import PorositySummary
from ansys.additive.core.progress_logger import ProgressLogger
from ansys.additive.core.server_connection import ServerConnection
from ansys.additive.core.simulation import SimulationError
from ansys.additive.core.single_bead import SingleBeadSummary
from ansys.additive.core.thermal_history import ThermalHistoryInput, ThermalHistorySummary


class Additive:
    """Provides the client interface to the Additive service.

    You can connect to the Additive server using one of the following
    methods. The methods are listed in order of precedence.
        1. If ``channel`` is provided, use it to connect to the server.
        2. If ``host``, and optionally ``port``, are provided, connect to the server at ``host:port``.
        3. If running in a :class:`PyPIM <ansys.platform.instancemanagement.pypim>`-
        enabled cloud environment, launch and connect to an ``additive`` service.
        4. Use the value of the ``ANSYS_ADDITIVE_ADDRESS`` environment variable if it is defined.
        The value uses the format ``host:port``.
        5. Attempt to start the server on localhost and connect to it. For this to work,
        the Additive portion of the Ansys Structures package from the Ansys unified installation
        must be installed.


    Parameters
    ----------
    server_connections: list[str, grpc.Channel], None
        List of connection definitions for servers. The list may be a combination of strings and
        connected ``grpc.Channel``s. Strings use the format ``host:port`` to specify
        the server IPv4 address.
    channel: grpc.Channel, None
        gRPC channel connection to use for communicating with the server. If None, a connection will be
        established using the host and port parameters. Ignored if ``server_channels``
        is not ``None``.
    host: str, None
        Host name or IPv4 address of the server. Ignored if ``server_channels`` or ``channel``
        is not ``None``.
    port: int
        Port number to use when connecting to the server. Defaults to 50052.
    nservers: int
        Number of Additive servers to start and connect to. If running in a
        :class:`PyPIM <ansys.platform.instancemanagement.pypim>` enabled environment,
        ``nservers`` ``additive`` services will be started. If running on localhost,
        ``nservers`` instances of Additive server will be started. For this to work,
        the Additive portion of the Ansys Structures package must be installed. Ignored if
        ``server_connections``, ``channel``, or ``host`` is not ``None``.
    log_level: str
        Minimum severity level of messages to log.
    log_file: str
        File name to write log messages to.
    """

    DEFAULT_ADDITIVE_SERVICE_PORT = 50052

    def __init__(
        self,
        server_connections: list[str | grpc.Channel] = None,
        channel: grpc.Channel | None = None,
        host: str | None = None,
        port: int = DEFAULT_ADDITIVE_SERVICE_PORT,
        nservers: int = 1,
        log_level: str = "INFO",
        log_file: str = "",
    ) -> None:
        """Initialize server connections."""
        self._log = Additive._create_logger(log_file, log_level)
        self._log.debug("Logging set to %s", log_level)

        self._servers = Additive._connect_to_servers(
            server_connections, channel, host, port, nservers, self._log
        )

        # Setup data directory
        self._user_data_path = USER_DATA_PATH
        if not os.path.exists(self._user_data_path):  # pragma: no cover
            os.makedirs(self._user_data_path)
        print("user data path: " + self._user_data_path)

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
        channel: grpc.Channel | None = None,
        host: str | None = None,
        port: int = DEFAULT_ADDITIVE_SERVICE_PORT,
        nservers: int = 1,
        log: logging.Logger = None,
    ) -> list[ServerConnection]:
        """Connect to Additive servers, starting them if necessary."""
        connections = []
        if server_connections:
            for target in server_connections:
                if isinstance(target, grpc.Channel):
                    connections.append(ServerConnection(channel=target, log=log))
                else:
                    connections.append(ServerConnection(addr=target, log=log))
        elif channel:
            connections.append(ServerConnection(channel=channel, log=log))
        elif host:
            connections.append(ServerConnection(addr=f"{host}:{port}", log=log))
        elif os.getenv("ANSYS_ADDITIVE_ADDRESS"):
            connections.append(ServerConnection(addr=os.getenv("ANSYS_ADDITIVE_ADDRESS"), log=log))
        else:
            for _ in range(nservers):
                connections.append(ServerConnection(log=log))

        return connections

    def about(self) -> None:
        """Print information about the client and server."""
        print(f"Client {__version__}, API version: {api_version}")
        if self._servers is None:
            print("Not connected to server")
            return
        else:
            print("_servers not None")
            for server in self._servers:
                print(server.status())

    def simulate(self, inputs):
        """Execute an additive simulation.

        Parameters
        ----------
        inputs: :class:`SingleBeadInput`, :class:`PorosityInput`,
        :class:`MicrostructureInput`, :class:`ThermalHistoryInput`
        or a list of these input types
            Parameters to use for simulations.

        Returns
        -------
        :class:`SingleBeadSummary`, :class:`PorositySummary`,
        :class:`MicrostructureSummary`, :class:`ThermalHistorySummary`,
        :class:`SimulationError`, or, if a list of inputs was provided,
        a list of these types.
        """
        if type(inputs) is not list:
            return self._simulate(inputs, self._servers[0], show_progress=True)
        else:
            self._validate_inputs(inputs)

        summaries = []
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Completed 0 of {len(inputs)} simulations",
            end="",
        )
        with concurrent.futures.ThreadPoolExecutor(len(self._servers)) as executor:
            futures = []
            for i, input in enumerate(inputs):
                server_id = i % len(self._servers)
                futures.append(
                    executor.submit(
                        self._simulate,
                        input=input,
                        server=self._servers[server_id],
                        show_progress=False,
                    )
                )
            for future in concurrent.futures.as_completed(futures):
                summary = future.result()
                if isinstance(summary, SimulationError):
                    print(f"\nError: {summary.message}")
                summaries.append(summary)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"\r{timestamp} Completed {len(summaries)} of {len(inputs)} simulations",
                    end="",
                )
        print("")
        return summaries

    def _simulate(self, input, server: ServerConnection, show_progress: bool = False):
        """Execute a single simulation.

        Parameters
        ----------
        input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput
            Parameters to use for simulation.

        server: ServerConnection
            Server to use for the simulation.

        show_progress: bool, False
            Whether to send progress updates to the user interface.

        Returns
        -------
        One of the follow summary objects:
        :class:`SingleBeadSummary`, :class:`PorositySummary`,
        :class:`MicrostructureSummary`, :class:`ThermalHistorySummary`,
        :class:`SimulationError`
        """
        logger = None
        if show_progress:
            logger = ProgressLogger("Simulation")

        if input.material == AdditiveMaterial():
            raise ValueError("A material is not assigned to the simulation input")

        try:
            request = None
            if isinstance(input, ThermalHistoryInput):
                return self._simulate_thermal_history(input, USER_DATA_PATH, server, logger)
            else:
                request = input._to_simulation_request()

            for response in server.simulation_stub.Simulate(request):
                if response.HasField("progress"):
                    if logger:
                        logger.log_progress(response.progress)
                    if response.progress.state == ProgressState.PROGRESS_STATE_ERROR:
                        raise Exception(response.progress.message)
                if response.HasField("melt_pool"):
                    return SingleBeadSummary(input, response.melt_pool)
                if response.HasField("porosity_result"):
                    return PorositySummary(input, response.porosity_result)
                if response.HasField("microstructure_result"):
                    return MicrostructureSummary(
                        input, response.microstructure_result, self._user_data_path
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
            `Create Material Parameters File (.json)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_tool_create_tables.html>`_
            in the *Additiivate Manufacturing Beta Features* documentation.
        thermal_lookup_file: str
            Name of the CSV file containing the lookup table for thermal dependent properties.
            For more information, see `Create Material Lookup File (.csv)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_create_mat_lookup.html>`_
            in the *Additiivate Manufacturing Beta Features* documentation.
        characteristic_width_lookup_file: str
            Name of the CSV file containing the lookup table for characteristic melt pool width. For
            more information, see
            `Find Characteristic Width Values and Generate Characteristic Width File (.csv)
            <https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_print_udm_tool_find_cw.html>`_
            in the *Additiivate Manufacturing Beta Features* documentation.
        """
        material = AdditiveMaterial()
        material._load_parameters(parameters_file)
        material._load_thermal_properties(thermal_lookup_file)
        material._load_characteristic_width(characteristic_width_lookup_file)
        return material

    def tune_material(
        self, input: MaterialTuningInput, out_dir: str = USER_DATA_PATH
    ) -> MaterialTuningSummary:
        """Tune a custom material for use with additive simulations.

        Parameters
        ----------
        input: MaterialTuningInput
            Input parameters for material tuning.

        Returns
        -------
        MaterialTuningSummary
            Summary of material tuning.
        """
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
                if response.progress.state == ProgressState.PROGRESS_STATE_ERROR:
                    raise Exception(response.progress.message)
                else:
                    for m in response.progress.message.splitlines():
                        if (
                            "License successfully" in m
                            or "Starting ThermalSolver" in m
                            or "threads for solver" in m
                        ):
                            continue
                        print(m)
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
        logger: ProgressLogger | None = None,
    ) -> ThermalHistorySummary:
        """Execute a thermal history simulation.

        Parameters
        ----------
        input: ThermalHistoryInput
            Simulation input parameters.
        out_dir: str
            Folder path for output files.
        server: ServerConnection
            Server to use for the simulation.
        logger: ProgressLogger
            Log message handler.

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
            if logger:
                logger.log_progress(response.progress)
            if response.progress.state == ProgressState.PROGRESS_STATE_ERROR:
                raise Exception(response.progress.message)

        request = input._to_simulation_request(remote_geometry_path=remote_geometry_path)
        for response in server.simulation_stub.Simulate(request):
            if response.HasField("progress"):
                if logger:
                    logger.log_progress(response.progress)
                if (
                    response.progress.state == ProgressState.PROGRESS_STATE_ERROR
                    and "WARN" not in response.progress.message
                ):
                    raise Exception(response.progress.message)
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

    def _validate_inputs(self, inputs):
        ids = []
        for input in inputs:
            if input.id == "":
                input.id = misc.short_uuid()
            if input.id in ids:
                raise ValueError(f'Duplicate simulation ID "{input.id}" in input list')
            ids.append(input.id)
