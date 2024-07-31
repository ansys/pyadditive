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
"""Manages running and waiting simulations."""

from __future__ import annotations

import os
import zipfile

from ansys.api.additive.v0.additive_domain_pb2 import ProgressState
from ansys.api.additive.v0.additive_operations_pb2 import OperationMetadata
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationResponse
from google.longrunning.operations_pb2 import (
    GetOperationRequest,
    ListOperationsRequest,
    Operation,
    WaitOperationRequest,
)
from google.protobuf.any_pb2 import Any
from google.protobuf.duration_pb2 import Duration

from ansys.additive.core.download import download_file
from ansys.additive.core.microstructure import MicrostructureInput, MicrostructureSummary
from ansys.additive.core.microstructure_3d import Microstructure3DInput, Microstructure3DSummary
from ansys.additive.core.porosity import PorosityInput, PorositySummary
from ansys.additive.core.progress_handler import (
    IProgressHandler,
    Progress,
    ProgressState,
)
from ansys.additive.core.server_connection import ServerConnection
from ansys.additive.core.simulation import SimulationError
from ansys.additive.core.single_bead import SingleBeadInput, SingleBeadSummary
from ansys.additive.core.thermal_history import ThermalHistoryInput, ThermalHistorySummary

from ansys.additive.core.simulation_requests import _create_request


class SimulationTask:
    def __init__(
        self,
        server_connections: list[ServerConnection],
        user_data_path: str,
        nsims_per_server: int
    ):
        self._servers = server_connections
        self._user_data_path = user_data_path
        self._nsims_per_server = nsims_per_server

        # TODO (deleon): Check if any existing long running operations already exist on the server. If so, cancel
        # and delete them as ListOperations() will pick them up.

        # dict to hold the server and any long running operations running on it.
        self._long_running_ops = {}
        # dict to hold the server and how many available simulation slots it has.
        self._available_sims_per_server = {}
        # list to hold waiting simulations, i.e. the inputs that can be formed into requests
        self._waiting_simulations = []
        # list to hold input objects
        self._simulation_inputs = []

        # Assuming multiple operations can be deployed on a single server, so initialize as a
        # dictionary of lists
        for server in self._servers:
            self._long_running_ops[server.channel_str] = []
            self._available_sims_per_server[server.channel_str] = self._nsims_per_server

        # dictionary to hold simulation result summaries or simulation errors upon completion,
        # keys are the simulation IDs
        self._summaries = {}

    def add_running_simulation(
        self,
        server_channel_str: str,
        long_running_op: Any,
        simlation_input: (
            SingleBeadInput
            | PorosityInput
            | MicrostructureInput
            | ThermalHistoryInput
            | Microstructure3DInput
        ),
    ) -> None:
        """Store a long-running operation that has been returned from the server along with the corresponding input.
        Also, update the current number of available job slots on the server.
        
        Parameters
        ----------
        server_channel_str: str
            The channel of the server that returned the long-running operation.
        long_running_op: Operation
            The long-running operation returned from the server or created on the client when an error occurred.
        simulation_input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput,
        Microstructure3DInput
            Parameters used for the simulation which will later be used to create a summary instance.
        """
        self._long_running_ops[server_channel_str].append(long_running_op)
        self._available_sims_per_server[server_channel_str] -= 1
        self._simulation_inputs.append(simlation_input)

    def add_waiting_simulation(
        self,
        simulation_input: (
            SingleBeadInput
            | PorosityInput
            | MicrostructureInput
            | ThermalHistoryInput
            | Microstructure3DInput
        ),
    ) -> None:
        """Store a simulation input if no servers available to run a simulation. This is intended
        to be used in conjunction with the client-side number-of-simulations-per-server restriction.
        
        Parameters
        ----------
        simulation_input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput,
        Microstructure3DInput
            Parameters to use for simulation.
        """
        self._waiting_simulations.append(simulation_input)
        self._simulation_inputs.append(simulation_input)

    def run_waiting_simulations(self, progress_handler: IProgressHandler | None = None) -> bool:
        """Attempt to run simulation inputs stored as waiting simulations.
        
        Parameters
        ----------
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates.

        Returns
        -------
        True if there are no more simulations waiting to be sent to server. Otherwise, False.
        """
        for channel, available_sims in self._available_sims_per_server:
            if not available_sims:
                # server has no open slots, try next one
                continue

            server = [x for x in self._servers if x.channel_str == channel][0]
            sim_input = self._waiting_simulations.pop()
            try:
                request = _create_request(sim_input, server, progress_handler)
                operation = server.simulation_stub.Simulate(request)
                self._long_running_ops[channel].append(operation)
                available_sims -= 1
            except Exception as e:
                metadata = OperationMetadata(simulation_id=sim_input.id, message=str(e))
                errored_op = Operation(name=sim_input.id, done=True)
                errored_op.metadata.Pack(metadata)
                self._long_running_ops[server.channel_str].append(errored_op)

        return not self._waiting_simulations

    def results(self):
        """Update the status of all Operations and get a list of simulation result summaries.

        If empty, no simulations have successfully finished. If only one simulation,
        returns a scalar not a list.
        """
        # Call status to get an update on operations
        self.status()

        results = [x for x in self._summaries.values() if not isinstance(x, SimulationError)]
        if len(results) == 1:
            return results[0]
        return results

    def errors(self):
        """Update the status of all Operations and get a list of simulation error summaries.

        If empty, no simulations have errored. If only one simulation, returns a scalar
        not a list.
        """

        # Call status to get an update on operations
        self.status()

        errors = [x for x in self._summaries.values() if isinstance(x, SimulationError)]
        if len(errors) == 1:
            return errors[0]
        return errors

    def get_operation(self, operation_name: str):
        """Get a specific operation from the server to update progress and results.

        Parameters
        ----------
        operation_name: str
            The name of the operation which should be the same as the simulation id
        """
        server = self._get_server_from_simulation_id(operation_name)
        get_request = GetOperationRequest(name=operation_name)
        operation = server.operations_stub.GetOperation(get_request)
        return operation

    def status(self, progress_handler: IProgressHandler | None = None):
        """Fetch status of all simulations from the server to update progress and results.
        
         Parameters
        ----------
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.

        Return
        ------
        A dictionary with simulation ids as keys and Progress instances as values
        """
        progress_updates = {}
        for server in self._servers:
            list_request = ListOperationsRequest()
            list_response = server.operations_stub.ListOperations(list_request)
            for op in list_response.operations:
                progress = self._update_operation_status(op)
                progress_updates[op.name] = progress
                if progress_handler:
                    progress_handler.update(progress)
        
        return progress_updates


    def wait_all(self,
                 progress_update_interval: int = 10,
                 progress_handler: IProgressHandler | None = None,
                 ) -> None:
        """Wait for all simulations to finish while updating progress.

        Loop over all operations across all servers and use WaitOperation() with a timeout
        inside a loop on each operation. WaitOperation() is blocking while the operation is
        running or the timeout hasn't been reached on the server. If the operation is already
        completed on the server or is completed while WaitOperation() is blocking, WaitOperation()
        returns immediately. A simple looping over all operations will block this function until
        the longest-running operation is completed. The timeout is provided to get progress updates
        as WaitOperation() returns an updated message about the operation.

        Parameters
        ----------
        progress_update_interval: int, 10
            A timeout value (in seconds) to give to the looped WaitOperation() calls to return an
            updated message for a progress update.
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.
        """
        for server in self._servers:
            list_request = ListOperationsRequest()
            list_response = server.operations_stub.ListOperations(list_request)

            for op in list_response.operations:
                while True:
                    timeout = Duration(seconds=progress_update_interval)
                    wait_request = WaitOperationRequest(name=op.name, timeout=timeout)
                    awaited_operation = server.operations_stub.WaitOperation(wait_request)
                    progress = self._update_operation_status(awaited_operation)
                    if progress_handler:
                        progress_handler.update(progress)
                    if awaited_operation.done:
                        break

        # Perform a call to status to ensure all messages from completed operations are recieved
        self.status(progress_handler)

    def _convert_metadata_to_progress(
        self,
        metadata_message: Any,
    ) -> Progress:
        """Update the progress handler with a metadata message.

        Parameters
        ----------
        metadata_message: [google.protobuf.Any]
            The metadata field of the Operation protobuf message prior to unpacking
            to an OperationMetadata class.

        Returns
        -------
        An instance of a Progress class
        """
        metadata = OperationMetadata()
        metadata_message.Unpack(metadata)
        return Progress.from_operation_metadata(metadata)

    def _unpack_summary(
        self, operation: Operation,
    ) -> tuple[(
        SingleBeadSummary
        | PorositySummary
        | MicrostructureSummary
        | ThermalHistorySummary
        | Microstructure3DSummary
        | SimulationError
    ), Progress]:
        """Update the simulation summaries. If an operation is completed, either the "error" field or
        the "response" field is available. Update the progress according to which field is available.

        Parameters
        ----------
        operation: [google.longrunning.Operation]
            The long-running operation
        """
        progress = self._convert_metadata_to_progress(operation.metadata)

        if progress.state == ProgressState.ERROR:
            sim_input = [x for x in self._simulation_inputs if x.id == operation.name][0]
            summary = SimulationError(sim_input, progress.message)
            return summary, progress

        if operation.HasField("response"):
            response = SimulationResponse()
            operation.response.Unpack(response)
            summary = self._get_results_from_response(response)
        # else:
            # TODO (deleon): Return a SimulationError if there is an rpc error
            # operation_error = RpcStatus()
            # operation.error.Unpack(operation_error)
            # summary = self._create_summary_of_operation_error(operation_error)

        return summary, progress

    def _update_operation_status(
            self,
            operation: Operation,
    ) -> Progress:
        """Update progress or summaries. If operation is done, update summaries and progress.
        Otherwise, update progress only.

        Parameters
        ----------
        operation: [google.longrunning.Operation]
            The long-running operation

        Returns
        -------
        Progress created from long-running operation metadata
        """
        if operation.done:
            # If operation is completed, get the summary and update progress. The server
            # should always mark the operation done on either a successful completion or
            # a simulation error.
            summary, progress = self._unpack_summary(operation)
            self._summaries[summary.input.id] = summary
        else:
            # Otherwise, just update progress
            progress = self._convert_metadata_to_progress(operation.metadata)

        return progress

    def _get_results_from_response(
        self, response: SimulationResponse
    ) -> (
        SingleBeadSummary
        | PorositySummary
        | MicrostructureSummary
        | ThermalHistorySummary
        | Microstructure3DSummary
    ):
        server = self._get_server_from_simulation_id(response.id)

        if not isinstance(self._simulation_inputs, list):
            simulation_input = self._simulation_inputs
        else:
            simulation_input = [x for x in self._simulation_inputs if x.id == response.id][0]

        if response.HasField("melt_pool"):
            thermal_history_output = None
            if self._check_if_thermal_history_is_present(response):
                thermal_history_output = os.path.join(
                    self._user_data_path, simulation_input.id, "thermal_history"
                )
                download_file(
                    server.simulation_stub,
                    response.melt_pool.thermal_history_vtk_zip,
                    thermal_history_output,
                )
            return SingleBeadSummary(simulation_input, response.melt_pool, thermal_history_output)
        if response.HasField("porosity_result"):
            return PorositySummary(simulation_input, response.porosity_result)
        if response.HasField("microstructure_result"):
            return MicrostructureSummary(
                simulation_input, response.microstructure_result, self._user_data_path
            )
        if response.HasField("microstructure_3d_result"):
            return Microstructure3DSummary(
                simulation_input, response.microstructure_3d_result, self._user_data_path
            )
        if response.HasField("thermal_history_result"):
            path = os.path.join(self._user_data_path, simulation_input.id, "coax_ave_output")
            local_zip = download_file(
                server.simulation_stub,
                response.thermal_history_result.coax_ave_zip_file,
                path,
            )
            with zipfile.ZipFile(local_zip, "r") as zip:
                zip.extractall(path)
            os.remove(local_zip)
            return ThermalHistorySummary(simulation_input, path)

    def _check_if_thermal_history_is_present(self, response) -> bool:
        """Check if thermal history output is present in the response."""
        return response.melt_pool.thermal_history_vtk_zip != str()

    def _get_server_from_simulation_id(self, id: str) -> ServerConnection:
        # Find list from dictionary values containing the particular simulation id
        target_server_list = [
            x for x in list(self._long_running_ops.values()) for y in x if y.name == id
        ]
        if not target_server_list:
            raise ValueError("Unable to find simulation id in existing long running operations. Id: " + id)
        # Convert list comprehension result to scalar
        target_server_list = target_server_list[0]
        # Get the dictionary key (server_channel string) corresponding to the value (target_server_list)
        server_channel = list(self._long_running_ops.keys())[
            list(self._long_running_ops.values()).index(target_server_list)
        ]
        # Find the actual server
        server = [x for x in self._servers if x.channel_str == server_channel]
        if not server:
            raise ValueError("Server not found for simulation id: " + id + " and channel: " + server_channel)
        
        # Convert list comprehension result to scalar
        return server[0]
