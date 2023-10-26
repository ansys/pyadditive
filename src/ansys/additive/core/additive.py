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
import socket
import zipfile

from ansys.api.additive import __version__ as api_version
from ansys.api.additive.v0.about_pb2_grpc import AboutServiceStub
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState
from ansys.api.additive.v0.additive_materials_pb2 import GetMaterialRequest
from ansys.api.additive.v0.additive_materials_pb2_grpc import MaterialsServiceStub
from ansys.api.additive.v0.additive_simulation_pb2 import UploadFileRequest
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub
import ansys.platform.instancemanagement as pypim
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
from ansys.additive.core.server_utils import find_open_port, launch_server, server_ready
from ansys.additive.core.simulation import SimulationError
from ansys.additive.core.single_bead import SingleBeadSummary
from ansys.additive.core.thermal_history import ThermalHistoryInput, ThermalHistorySummary

MAX_MESSAGE_LENGTH = int(256 * 1024**2)
DEFAULT_ADDITIVE_SERVICE_PORT = 50052
LOCALHOST = "127.0.0.1"


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
    nproc: int
        Number of simulations to run in parallel. The number of available licenses must
        be greater than or equal to this number.
    host: str, None
        Host name or IPv4 address of the server. If ``None``, the client attempts
        to connect to a server using one of the methods described previously.
    port: int, None
        Port number to use when connecting to the server. If None, the default port will be used, 50052.
    loglevel: str
        Minimum severity level of messages to log.
    log_file: str
        File name to write log messages to.
    channel: grpc.Channel, None
        gRPC channel connection to use for communicating with the server. If None, a connection will be
        established using the host and port parameters.
    """

    def __init__(
        self,
        nproc: int = 4,
        host: str | None = None,
        port: int | None = None,
        loglevel: str = "INFO",
        log_file: str = "",
        channel: grpc.Channel | None = None,
    ) -> None:  # PEP 484
        """Initialize a connection to the server."""
        if channel is not None and (host is not None or port is not None):
            raise ValueError(
                "If 'channel' is specified, neither 'port' nor 'host' can be specified."
            )

        ip = socket.gethostbyname(host) if host != None else None

        self._nproc = nproc
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
        self._about_stub = AboutServiceStub(self._channel)

        if not server_ready(self._about_stub):
            raise RuntimeError("Unable to connect to server")

        # Setup data directory
        self._user_data_path = USER_DATA_PATH
        if not os.path.exists(self._user_data_path):  # pragma: no cover
            os.makedirs(self._user_data_path)
        print("user data path: " + self._user_data_path)

    def __del__(self):
        """Destructor for cleaning up the service connection."""
        if hasattr(self, "_server_instance") and self._server_instance:
            self._server_instance.delete()
        if hasattr(self, "_server_process") and self._server_process:
            self._server_process.kill()

    def _create_logger(self, log_file, loglevel) -> logging.Logger:
        """Instantiate the logger."""
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError("Invalid log level: %s" % loglevel)
        if log_file:
            if not isinstance(log_file, str):
                log_file = "instance.log"
            logging.basicConfig(filename=log_file, level=numeric_level)
        else:
            logging.basicConfig(
                level=numeric_level,
                format="%(asctime)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        return logging.getLogger(__name__)

    def _create_channel(
        self,
        ip: str | None = None,
        port: int | None = None,
        product_version: str | None = None,
    ):
        """Create an insecure gRPC channel.

        A channel connection is established using one of the following methods.
        The methods are listed in order of precedence.

        #. Use the user-provided IP address and port values, if any.
        #. Use PyPIM if the client is running in a PyPIM-enabled environment
           such as Ansys Lab.
        #. Use an IP address and port definition string defined by the
           ``ANSYS_ADDITIVE_ADDRESS`` environment variable.
        #. Use the default IP address and port, ``localhost:50052``.

        Parameters
        ----------
        ip: str, None
            IP address of the remote server host in IPv4 dotted-quad string format.
        port: int, None
            Port number on the server to connect to.
        product_version: str, None
            Product version of the Additive server. This parameter is only applicable
            in PyPIM environments.

        Returns
        -------
        channel: grpc.Channel
            Insecure gRPC channel.
        """
        if port:
            misc.check_valid_port(port)
        else:
            port = DEFAULT_ADDITIVE_SERVICE_PORT

        if ip:
            misc.check_valid_ip(ip)
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
            port = find_open_port()
            self._server_process = launch_server(port)
            return self.__open_insecure_channel(f"{LOCALHOST}:{port}")

    def __open_insecure_channel(self, target: str) -> grpc.Channel:
        """Open an insecure gRPC channel to a given target.

        Parameters
        ----------
        target : str
            Target for the insecure gRPC channel.
        """
        return grpc.insecure_channel(
            target, options=[("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH)]
        )

    @property
    def _channel_str(self):
        """Target string.

        The form is generally ``"ip:port"``. For example, ``"127.0.0.1:50052"``.
        """
        if self._channel is not None:
            return self._channel._channel.target().decode()
        return ""

    def about(self) -> None:
        """Print information about the client and server."""
        print("Client")
        print(f"    Version: {__version__}")
        print(f"    API version: {api_version}")
        if self._channel is None:
            print("Not connected to server")
            return
        try:
            response = self._about_stub.About(Empty())
        except grpc.RpcError as exc:
            raise Exception(f"Failed to connect to server: {self._channel_str}\n{exc}")
        print(f"Server {self._channel_str}")
        for key in response.metadata:
            value = response.metadata[key]
            print(f"    {key}: {value}")

    def simulate(self, inputs, nproc: int | None = None):
        """Execute an additive simulation.

        Parameters
        ----------
        inputs: :class:`SingleBeadInput`, :class:`PorosityInput`,
        :class:`MicrostructureInput`, :class:`ThermalHistoryInput`
        or a list of these input types
            Parameters to use for simulations.

        nproc: int, None
            Number of processors to use for simulation. This corresponds
            to the maximum number of licenses to check out at one time.
            If no value is specified, the value of the ``nproc`` parameter
            provided in the Additive service constructor is used.

        Returns
        -------
        :class:`SingleBeadSummary`, :class:`PorositySummary`,
        :class:`MicrostructureSummary`, :class:`ThermalHistorySummary`,
        :class:`SimulationError`, or, if a list of inputs was provided,
        a list of these types.
        """
        if type(inputs) is not list:
            result = self._simulate(inputs, show_progress=True)
            return result
        else:
            self._validate_inputs(inputs)

        summaries = []
        nthreads = self._nproc
        if nproc:
            nthreads = nproc
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Completed 0 of {len(inputs)} simulations",
            end="",
        )
        with concurrent.futures.ThreadPoolExecutor(nthreads) as executor:
            futures = []
            for input in inputs:
                futures.append(executor.submit(self._simulate, input=input, show_progress=False))
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

    def _simulate(self, input, show_progress: bool = False):
        """Execute a single simulation.

        Parameters
        ----------
        input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput
            Parameters to use for simulation.

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
            raise ValueError("Material must be specified")

        try:
            request = None
            if isinstance(input, ThermalHistoryInput):
                return self._simulate_thermal_history(input, USER_DATA_PATH, logger)
            else:
                request = input._to_simulation_request()

            for response in self._simulation_stub.Simulate(request):
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

    def get_materials_list(self) -> list[str]:
        """Get a list of material names used in additive simulations.

        Returns
        -------
        list[str]
            Names of available additive materials.
        """
        return self._materials_stub.GetMaterialsList(Empty())

    def get_material(self, name: str) -> AdditiveMaterial:
        """Get a material for use in an additive simulation.

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
            raise Exception(
                f"Directory {out_dir} already exists. Delete or choose a different output directory."
            )

        request = input._to_request()

        for response in self._materials_stub.TuneMaterial(request):
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
        self, file_name: str, chunk_size=2 * 1024 * 1024
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
        logger: ProgressLogger | None = None,
    ) -> ThermalHistorySummary:
        """Execute a thermal history simulation.

        Parameters
        ----------
        input: ThermalHistoryInput
            Simulation input parameters.
        out_dir: str
            Folder path for output files.
        logger: ProgressLogger
            Log message handler.

        Returns
        -------
        :class:`ThermalHistorySummary`
        """
        if input.geometry == None or input.geometry.path == "":
            raise ValueError("Geometry path not defined")

        remote_geometry_path = ""
        for response in self._simulation_stub.UploadFile(
            self.__file_upload_reader(input.geometry.path)
        ):
            remote_geometry_path = response.remote_file_name
            if logger:
                logger.log_progress(response.progress)
            if response.progress.state == ProgressState.PROGRESS_STATE_ERROR:
                raise Exception(response.progress.message)

        request = input._to_simulation_request(remote_geometry_path=remote_geometry_path)
        for response in self._simulation_stub.Simulate(request):
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
                    self._simulation_stub,
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
