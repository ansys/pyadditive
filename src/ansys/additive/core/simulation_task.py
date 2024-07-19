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
"""Provides progress updates."""

from __future__ import annotations

import os
import zipfile

from ansys.api.additive.v0.additive_domain_pb2 import ProgressState as ProgressMsgState
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
    DefaultSingleSimulationProgressHandler,
    IProgressHandler,
    Progress,
    ProgressState,
)
from ansys.additive.core.server_connection import ServerConnection
from ansys.additive.core.simulation import SimulationError
from ansys.additive.core.single_bead import SingleBeadInput, SingleBeadSummary
from ansys.additive.core.thermal_history import ThermalHistoryInput, ThermalHistorySummary


class SimulationTask:
    def __init__(
        self,
        server_connections: list[ServerConnection],
        user_data_path: str,
        progress_handler: IProgressHandler | None = None,
    ):
        self._servers = server_connections
        self._progress_handler = progress_handler
        self._user_data_path = user_data_path

        # TODO (deleon): Check if any existing long running operations already exist on the server. If so, cancel
        # and delete them as ListOperations() will pick them up.

        # dict to hold the server and any long running operations deployed on it.
        self._long_running_ops = {}
        # list to hold input objects
        self._simulation_inputs = []

        # Assuming multiple operations can be deployed on a single server, so initialize as a
        # dictionary of lists
        for server in self._servers:
            self._long_running_ops[server.channel_str] = []

        # dictionary to hold simulation result summaries or simulation errors upon completion,
        # keys are the simulation IDs
        self._summaries = {}

    def add_simulation(
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
        self._long_running_ops[server_channel_str].append(long_running_op)
        self._simulation_inputs.append(simlation_input)

    def collect_results(self):
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

    def collect_errors(self):
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

    def status(self):
        """Fetch status of all simulations from the server to update progress and results."""
        for server in self._servers:
            list_request = ListOperationsRequest()
            list_response = server.operations_stub.ListOperations(list_request)
            for op in list_response.operations:
                self._update_operation_status(op)

    def wait_all(self, progress_update_interval: int = 10) -> None:
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
        """
        for server in self._servers:
            list_request = ListOperationsRequest()
            list_response = server.operations_stub.ListOperations(list_request)

            for op in list_response.operations:
                while True:
                    timeout = Duration(seconds=progress_update_interval)
                    wait_request = WaitOperationRequest(name=op.name, timeout=timeout)
                    awaited_operation = server.operations_stub.WaitOperation(wait_request)
                    self._update_operation_status(awaited_operation)
                    if awaited_operation.done:
                        break

        # Perform a call to status to ensure all messages from completed operations are recieved
        self.status()

    def _update_progress(
        self,
        metadata_message: Any,
        progress_state: ProgressState,
    ):
        """Update the progress handler with a metadata message.

        Parameters
        ----------
        metadata_message: [google.protobuf.Any]
            The metadata field of the Operation protobuf message prior to unpacking
            to an OperationMetadata class.
        progress_state: [ProgressState]
            The progress status of the simulation.
        """
        metadata = OperationMetadata()
        metadata_message.Unpack(metadata)
        progress = Progress.from_operation_metadata(progress_state, metadata)
        if self._progress_handler:
            self._progress_handler.update(progress)
        if progress.state == ProgressState.ERROR:
            raise Exception(progress.message)

    def _unpack_summary(
        self, operation: Operation
    ) -> (
        SingleBeadSummary
        | PorositySummary
        | MicrostructureSummary
        | ThermalHistorySummary
        | Microstructure3DSummary
    ):
        """Update the simulation summaries. If an operation is completed, either the "error" field or
        the "response" field is available. Update the progress according to which field is available.

        Parameters
        ----------
        operation: [google.longrunning.Operation]
            The long-running operation
        """
        if operation.HasField("response"):
            response = SimulationResponse()
            self._update_progress(operation.metadata, ProgressMsgState.PROGRESS_STATE_COMPLETED)
            operation.response.Unpack(response)
            summary = self._get_results_from_response(response)
        else:
            self._update_progress(operation.metadata, ProgressMsgState.PROGRESS_STATE_ERROR)
            # TODO (deleon): Return a SimulationError if there is an rpc error
            # operation_error = RpcStatus()
            # operation.error.Unpack(operation_error)
            # summary = self._create_summary_of_operation_error(operation_error)

        return summary

    def _update_operation_status(self, operation: Operation):
        """Update progress or summaries. If operation is done, update summaries and progress.
        Otherwise, update progress only.

        Parameters
        ----------
        operation: [google.longrunning.Operation]
            The long-running operation
        """
        if operation.done:
            # if operation is completed, get the summary and update progress
            summary = self._unpack_summary(operation)
            self._summaries[summary.input.id] = summary
        else:
            # otherwise, just update progress
            self._update_progress(operation.metadata, ProgressMsgState.PROGRESS_STATE_EXECUTING)

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
        target_server_list = [
            x for x in list(self._long_running_ops.values()) for y in x if y.name == id
        ][0]
        server_channel = list(self._long_running_ops.keys())[
            list(self._long_running_ops.values()).index(target_server_list)
        ]
        return [x for x in self._servers if x.channel_str == server_channel][0]
