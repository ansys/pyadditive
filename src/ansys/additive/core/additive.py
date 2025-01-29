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

import logging
import os
import time

import grpc
from google.longrunning.operations_pb2 import Operation
from google.protobuf.empty_pb2 import Empty

import ansys.additive.core.misc as misc
from ansys.additive.core import USER_DATA_PATH, __version__
from ansys.additive.core.download import download_logs
from ansys.additive.core.exceptions import BetaFeatureNotEnabledError
from ansys.additive.core.logger import LOG
from ansys.additive.core.material import RESERVED_MATERIAL_NAMES, AdditiveMaterial
from ansys.additive.core.material_tuning import (
    MaterialTuningInput,
    MaterialTuningSummary,
)
from ansys.additive.core.microstructure import (
    MicrostructureInput,
    MicrostructureSummary,
)
from ansys.additive.core.microstructure_3d import (
    Microstructure3DInput,
    Microstructure3DSummary,
)
from ansys.additive.core.parametric_study import ParametricStudy
from ansys.additive.core.parametric_study.parametric_study_progress_handler import (
    ParametricStudyProgressHandler,
)
from ansys.additive.core.porosity import PorosityInput, PorositySummary
from ansys.additive.core.progress_handler import (
    DefaultSingleSimulationProgressHandler,
    IProgressHandler,
)
from ansys.additive.core.server_connection import (
    DEFAULT_PRODUCT_VERSION,
    ServerConnection,
)
from ansys.additive.core.simulation import (
    SimulationStatus,
    SimulationType,
)
from ansys.additive.core.simulation_error import SimulationError
from ansys.additive.core.simulation_requests import create_request
from ansys.additive.core.simulation_task import SimulationTask
from ansys.additive.core.simulation_task_manager import SimulationTaskManager
from ansys.additive.core.single_bead import SingleBeadInput, SingleBeadSummary
from ansys.additive.core.thermal_history import (
    ThermalHistoryInput,
    ThermalHistorySummary,
)
from ansys.api.additive import __version__ as api_version
from ansys.api.additive.v0.additive_materials_pb2 import (
    AddMaterialRequest,
    GetMaterialRequest,
    RemoveMaterialRequest,
)
from ansys.api.additive.v0.additive_operations_pb2 import OperationMetadata
from ansys.api.additive.v0.additive_settings_pb2 import SettingsRequest


class Additive:
    """Provides the client interface to one or more Additive services.

    Parameters
    ----------
    channel: grpc.Channel, default: None
        Server connection. If provided, it is assumed that the
        :class:`grpc.Channel <grpc.Channel>` object is connected to the server.
        Also, if provided, the ``host`` and ``port`` parameters are ignored.
    host: str, default: None
        Host name or IPv4 address of the server. This parameter is ignored if the
        ``server_channels`` or ``channel`` parameters is other than ``None``.
    port: int, default: 50052
        Port number to use when connecting to the server.
    nsims_per_server: int, default: 1
        Number of simultaneous simulations to run on the server. Each simulation
        requires a license checkout. If a license is not available, the simulation
        fails.
    product_version: str
        Version of the Ansys product installation in the form ``"YYR"``, where ``YY``
        is the two-digit year and ``R`` is the release number. For example, the release
        2024 R1 would be specified as ``241``. This parameter is only applicable in
        `PyPIM`_-enabled cloud environments and on localhost. Using an empty string
        or ``None`` uses the default product version.
    log_level: str, default: ""
        Minimum severity level of messages to log. Valid values are "DEBUG", "INFO",
        "WARNING", "ERROR", and "CRITICAL". The default value equates to "WARNING".
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

    Start and connect to a server on localhost or in a
    `PyPIM`_-enabled cloud environment. Allow two simultaneous
    simulations on the server.

    >>> additive = Additive(nsims_per_server=2)

    Start a single server on localhost or in a `PyPIM`_-enabled cloud environment.
    Use version 2024 R1 of the Ansys product installation.

    >>> additive = Additive(product_version="241")

    .. _PyPIM: https://pypim.docs.pyansys.com/version/stable/index.html

    """

    DEFAULT_ADDITIVE_SERVICE_PORT = 50052

    def __init__(
        self,
        channel: grpc.Channel | None = None,
        host: str | None = None,
        port: int = DEFAULT_ADDITIVE_SERVICE_PORT,
        nsims_per_server: int = 1,
        product_version: str = DEFAULT_PRODUCT_VERSION,
        log_level: str = "",
        log_file: str = "",
        enable_beta_features: bool = False,
        linux_install_path: os.PathLike | None = None,
    ) -> None:
        """Initialize server connections."""
        if not product_version:
            product_version = DEFAULT_PRODUCT_VERSION

        if log_level:
            LOG.setLevel(log_level)
        if log_file:
            LOG.log_to_file(filename=log_file, level=log_level)

        self._server = Additive._connect_to_server(
            channel,
            host,
            port,
            product_version,
            LOG,
            linux_install_path,
        )

        # HACK: Set the number of concurrent simulations per server
        # when generating documentation to reduce time.
        if os.getenv("GENERATING_DOCS", None):
            nsims_per_server = 8
        initial_settings = {"NumConcurrentSims": str(nsims_per_server)}
        LOG.info(self.apply_server_settings(initial_settings))

        self._enable_beta_features = enable_beta_features

        # Setup data directory
        self._user_data_path = USER_DATA_PATH
        if not os.path.exists(self._user_data_path):  # pragma: no cover
            os.makedirs(self._user_data_path)
        LOG.info("user data path: " + self._user_data_path)

    @staticmethod
    def _connect_to_server(
        channel: grpc.Channel | None = None,
        host: str | None = None,
        port: int = DEFAULT_ADDITIVE_SERVICE_PORT,
        product_version: str = DEFAULT_PRODUCT_VERSION,
        log: logging.Logger = None,
        linux_install_path: os.PathLike | None = None,
    ) -> ServerConnection:
        """Connect to an Additive server, starting it if necessary.

        Parameters
        ----------
        channel: grpc.Channel, default: None
            Server connection. If provided, it is assumed to be connected
            and the ``host`` and ``port`` parameters are ignored.
        host: str, default: None
            Host name or IPv4 address of the server. This parameter is ignored if
            the ``channel`` parameter is other than ``None``.
        port: int, default: 50052
            Port number to use when connecting to the server.
        product_version: str
            Version of the Ansys product installation in the form ``"YYR"``, where ``YY``
            is the two-digit year and ``R`` is the release number. For example, "251".
            This parameter is only applicable in `PyPIM`_-enabled cloud environments and
            on localhost. Using an empty string or ``None`` uses the default product version.
        log: logging.Logger, default: None
            Logger to use for logging messages.
        linux_install_path: os.PathLike, None, default: None
            Path to the Ansys installation directory on Linux. This parameter is only
            required when Ansys has not been installed in the default location. Example:
            ``/usr/shared/ansys_inc``. Note that the path should not include the product
            version.

        Returns
        -------
        ServerConnection
            Connection to the server.

        NOTE: If ``channel`` and ``host`` are not provided and the environment variable
        ``ANSYS_ADDITIVE_ADDRESS`` is set, the client will connect to the server at the
        address specified by the environment variable. The value of the environment variable
        should be in the form ``host:port``.

        """
        if channel:
            if not isinstance(channel, grpc.Channel):
                raise ValueError("channel must be a grpc.Channel object")
            return ServerConnection(channel=channel, log=log)
        elif host:
            return ServerConnection(addr=f"{host}:{port}", log=log)
        elif os.getenv("ANSYS_ADDITIVE_ADDRESS"):
            return ServerConnection(addr=os.getenv("ANSYS_ADDITIVE_ADDRESS"), log=log)
        else:
            return ServerConnection(
                product_version=product_version,
                log=log,
                linux_install_path=linux_install_path,
            )

    @property
    def enable_beta_features(self) -> bool:
        """Flag indicating if beta features are enabled."""
        return self._enable_beta_features

    @enable_beta_features.setter
    def enable_beta_features(self, value: bool) -> None:
        """Set the flag indicating if beta features are enabled."""
        self._enable_beta_features = value

    @property
    def connected(self) -> bool:
        """Return True if the client is connected to a server."""
        if self._server is None:
            return False
        return self._server.status().connected

    def about(self) -> str:
        """Return information about the client and server.

        Returns
        -------
        str
            Information about the client and server.

        """
        about = (
            f"ansys.additive.core version {__version__}\nClient side API version: {api_version}\n"
        )
        if self._server is None:
            about += "Client is not connected to a server.\n"
        else:
            about += str(self._server.status()) + "\n"
        return about

    def apply_server_settings(self, settings: dict[str, str]) -> list[str]:
        """Apply settings to each server.

        Current settings include:
        - ``NumConcurrentSims``: number of concurrent simulations per server.

        Parameters
        ----------
        settings: dict[str, str]
            Dictionary of settings to apply to the server.

        Returns
        -------
        list[str]
            List of messages from the server.

        """
        request = SettingsRequest()
        for setting_key, setting_value in settings.items():
            setting = request.settings.add()
            setting.key = setting_key
            setting.value = setting_value

        response = self._server.settings_stub.ApplySettings(request)

        return response.messages

    def list_server_settings(self) -> dict[str, str]:
        """Get a dictionary of settings for the server."""
        response = self._server.settings_stub.ListSettings(Empty())
        settings = {}
        for setting in response.settings:
            settings[setting.key] = setting.value
        return settings

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
        inputs: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput, Microstructure3DInput, list
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

        """  # noqa: E501
        summaries = []
        task_mgr = self.simulate_async(inputs, progress_handler)
        task_mgr.wait_all(progress_handler=progress_handler)
        summaries = task_mgr.summaries()

        for summ in summaries:
            if isinstance(summ, SimulationError):
                LOG.error(f"\nError: {summ.message}")

        return summaries if isinstance(inputs, list) else summaries[0]

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
    ) -> SimulationTaskManager:
        """Execute additive simulations asynchronously. This method does not block while the
        simulations are running on the server. This class stores handles of type
        google.longrunning.Operation to the remote tasks that can be used to communicate with
        the server for status updates.

        Parameters
        ----------
        inputs: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput, Microstructure3DInput, list
            Parameters to use for simulations. A list of inputs may be provided to run multiple
            simulations.
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, and ``inputs`` contains a single
            simulation input, a default progress handler will be assigned.

        Returns
        -------
        SimulationTaskManager
            A SimulationTaskManager to handle all tasks sent to the server by this function call.

        """  # noqa: E501
        self._check_for_duplicate_id(inputs)

        task_manager = SimulationTaskManager()
        if not isinstance(inputs, list):
            if not progress_handler:
                progress_handler = DefaultSingleSimulationProgressHandler()
            simulation_task = self._simulate(inputs, self._server, progress_handler)
            task_manager.add_task(simulation_task)
            return task_manager

        if len(inputs) == 0:
            raise ValueError("No simulation inputs provided")

        LOG.info(f"Starting {len(inputs)} simulations")
        for sim_input in inputs:
            task = self._simulate(sim_input, self._server, progress_handler)
            task_manager.add_task(task)

        return task_manager

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
        progress_handler: IProgressHandler | None = None,
    ) -> SimulationTask:
        """Execute a single simulation.

        Parameters
        ----------
        simulation_input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput, Microstructure3DInput
            Parameters to use for simulation.
        server: ServerConnection
            Server to use for the simulation.
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.

        Returns
        -------
        SimulationTask
            A task that can be used to monitor the simulation progress.

        """  # noqa: E501

        if simulation_input.material == AdditiveMaterial():
            raise ValueError("A material is not assigned to the simulation input")

        if (
            isinstance(simulation_input, (Microstructure3DInput, ThermalHistoryInput))
            and self.enable_beta_features is False
        ):
            raise BetaFeatureNotEnabledError(
                "This simulation requires beta features to be enabled.\n"
                "Set enable_beta_features=True when creating the Additive client."
            )

        try:
            request = create_request(simulation_input, server, progress_handler)
            long_running_op = server.simulation_stub.Simulate(request)
            simulation_task = SimulationTask(
                server, long_running_op, simulation_input, self._user_data_path
            )
            LOG.debug(f"Simulation task created for {simulation_input.id}")

        except Exception as e:
            metadata = OperationMetadata(simulation_id=simulation_input.id, message=str(e))
            errored_op = Operation(name=simulation_input.id, done=True)
            errored_op.metadata.Pack(metadata)
            simulation_task = SimulationTask(
                server, errored_op, simulation_input, self._user_data_path
            )

        if progress_handler:
            time.sleep(0.1)  # Allow time for the server to start the simulation
            progress_handler.update(simulation_task.status())

        return simulation_task

    def materials_list(self) -> list[str]:
        """Get a list of material names used in additive simulations.

        Returns
        -------
        list[str]
            Names of available additive materials.

        """
        response = self._server.materials_stub.GetMaterialsList(Empty())
        return response.names

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
        result = self._server.materials_stub.GetMaterial(request)
        return AdditiveMaterial._from_material_message(result)

    @staticmethod
    def load_material(
        parameters_file: str,
        thermal_lookup_file: str,
        characteristic_width_lookup_file: str,
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
        self,
        parameters_file: str,
        thermal_lookup_file: str,
        characteristic_width_lookup_file: str,
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
        LOG.info(f"Adding material {request.material.name}")
        response = self._server.materials_stub.AddMaterial(request)

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

        self._server.materials_stub.RemoveMaterial(RemoveMaterialRequest(name=name))

    def tune_material(
        self,
        input: MaterialTuningInput,
        out_dir: str = USER_DATA_PATH,
        progress_handler: IProgressHandler = None,
    ) -> MaterialTuningSummary | None:
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
        MaterialTuningSummary, None
            Summary of material tuning or ``None`` if the tuning failed.

        """  # noqa: E501

        task = self.tune_material_async(input, out_dir)
        task.wait(progress_handler=progress_handler)
        return task.summary

    def tune_material_async(
        self,
        input: MaterialTuningInput,
        out_dir: str = USER_DATA_PATH,
    ) -> SimulationTask:
        """Tune a custom material for use with additive simulations asynchronously.

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

        Returns
        -------
        SimulationTask
            An asynchronous simulation task.

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
        operation = self._server.simulation_stub.Simulate(request)
        LOG.debug(f"Material tuning operation created for {input.id}")
        return SimulationTask(self._server, operation, input, out_dir)

    def simulate_study(
        self,
        study: ParametricStudy,
        simulation_ids: list[str] | None = None,
        types: list[SimulationType] | None = None,
        priority: int | None = None,
        iteration: int = None,
    ):
        """Run the simulations in a parametric study.

        Parameters
        ----------
        study : ParametricStudy
            Parametric study to run.
        simulation_ids : list[str], default: None
            List of simulation IDs to run. If this value is ``None``,
            all simulations with a status of ``Pending`` are run.
        types : list[SimulationType], default: None
            Type of simulations to run. If this value is ``None``,
            all simulation types are run.
        priority : int, default: None
            Priority of simulations to run. If this value is ``None``,
            all priorities are run.
        iteration : int, default: None
            Iteration number of simulations to run. The default is ``None``,
            all iterations are run.
        progress_handler : IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, a :class:`ParametricStudyProcessHandler` will be used.

        """
        SLEEP_INTERVAL = 2
        progress_handler = ParametricStudyProgressHandler(study)
        summaries = []

        try:
            task_mgr = self.simulate_study_async(
                study, simulation_ids, types, priority, iteration, progress_handler
            )
            # Allow time for the server to start the simulations
            time.sleep(SLEEP_INTERVAL)
            while not task_mgr.done:
                task_mgr.status(progress_handler)
                current_summaries = task_mgr.summaries()
                new_summaries = [s for s in current_summaries if s not in summaries]
                if new_summaries:
                    study.update(new_summaries)
                    summaries = current_summaries
                time.sleep(SLEEP_INTERVAL)

        except Exception as e:
            LOG.error(f"Error running study: {e}")
            study.reset_simulation_status()
            raise RuntimeError from e

    def simulate_study_async(
        self,
        study: ParametricStudy,
        simulation_ids: list[str] | None = None,
        types: list[SimulationType] | None = None,
        priority: int | None = None,
        iteration: int = None,
        progress_handler: IProgressHandler = None,
    ) -> SimulationTaskManager:
        """Run the simulations in a parametric study asynchronously.

        Notes
        -----
            The caller of this method is responsible for updating the study with the results of the simulations.
            See :meth:`SimulationTaskManager.summaries` and :meth:`ParametricStudy.update`.

        Parameters
        ----------
        study : ParametricStudy
            Parametric study to run.
        simulation_ids : list[str], default: None
            List of simulation IDs to run. If this value is ``None``,
            all simulations with a status of ``Pending`` are run.
        types : list[SimulationType], default: None
            Type of simulations to run. If this value is ``None``,
            all simulation types are run.
        priority : int, default: None
            Priority of simulations to run. If this value is ``None``,
            all priorities are run.
        iteration : int, default: None
            Iteration number of simulations to run. The default is ``None``,
            all iterations are run.
        progress_handler : IProgressHandler, None, default: None
            Handler for progress updates.

        """
        inputs = study.simulation_inputs(self.material, simulation_ids, types, priority, iteration)
        if not inputs:
            # no simulations met the provided criteria, return an empty task manager
            return SimulationTaskManager()
        ids = [i.id for i in inputs]
        study.set_simulation_status(ids, SimulationStatus.PENDING)
        study.clear_errors(ids)
        return self.simulate_async(inputs, progress_handler)

    def _check_for_duplicate_id(self, inputs):
        """Check for duplicate simulation IDs in a list of inputs.

        If an input does not have an ID, one will be assigned.

        Parameters
        ----------
        inputs : SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput, Microstructure3DInput, list
            A simulation input or a list of simulation inputs.

        Raises
        ------
        ValueError
            If a duplicate ID is found in the list of inputs.

        """  # noqa: E501
        if not isinstance(inputs, list):
            # An individual input, not a list
            if inputs.id == "":
                inputs.id = misc.short_uuid()
            return
        ids = []
        for i in inputs:
            if not i.id:
                # give input an id if none provided
                i.id = misc.short_uuid()
            if any(id == i.id for id in ids):
                raise ValueError(f'Duplicate simulation ID "{i.id}" in input list')
            ids.append(i.id)

    def download_server_logs(self, log_dir: str | os.PathLike) -> str:
        """Download server logs to a specified directory.

        Parameters
        ----------
        log_dir : str
            Directory to save the logs to.

        Returns
        -------
        str
            Path to the downloaded logs.

        """
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return download_logs(self._server.simulation_stub, log_dir)
