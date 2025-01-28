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
"""Container for a simulation task."""

import base64
import io
import os
import zipfile

from google.longrunning.operations_pb2 import (
    CancelOperationRequest,
    GetOperationRequest,
    Operation,
    WaitOperationRequest,
)
from google.protobuf.any_pb2 import Any
from google.protobuf.duration_pb2 import Duration
from google.rpc.code_pb2 import Code
from google.rpc.error_details_pb2 import ErrorInfo

from ansys.additive.core.download import download_file
from ansys.additive.core.logger import LOG
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
from ansys.additive.core.porosity import PorosityInput, PorositySummary
from ansys.additive.core.progress_handler import (
    IProgressHandler,
    Progress,
    ProgressState,
)
from ansys.additive.core.server_connection import ServerConnection
from ansys.additive.core.simulation import SimulationStatus
from ansys.additive.core.simulation_error import SimulationError
from ansys.additive.core.single_bead import SingleBeadInput, SingleBeadSummary
from ansys.additive.core.thermal_history import (
    ThermalHistoryInput,
    ThermalHistorySummary,
)
from ansys.api.additive.v0.additive_operations_pb2 import OperationMetadata
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationResponse


class SimulationTask:
    """Provides a simulation task.

    Parameters
    ----------
    server_connection: ServerConnection
        The client connection to the Additive server.
    long_running_operation: Operation
        The long-running operation representing the simulation on the server.
    simulation_input: SingleBeadInput | PorosityInput | MicrostructureInput | ThermalHistoryInput | Microstructure3DInput | MaterialTuningInput
        The simulation input.
    user_data_path: str
        The path to the user data directory.

    """  # noqa: E501

    def __init__(
        self,
        server_connection: ServerConnection,
        long_running_operation: Operation,
        simulation_input: (
            SingleBeadInput
            | PorosityInput
            | MicrostructureInput
            | ThermalHistoryInput
            | Microstructure3DInput
            | MaterialTuningInput
        ),
        user_data_path: str,
    ):
        """Initialize the simulation task."""
        self._server = server_connection
        self._user_data_path = user_data_path
        self._long_running_op = long_running_operation
        self._simulation_input = simulation_input
        self._summary = None

    @property
    def simulation_id(self) -> str:
        """Get the simulation id associated with this task."""
        return self._simulation_input.id

    @property
    def summary(
        self,
    ) -> (
        SingleBeadSummary
        | PorositySummary
        | MicrostructureSummary
        | Microstructure3DSummary
        | ThermalHistorySummary
        | MaterialTuningSummary
        | SimulationError
        | None
    ):
        """The summary of the completed simulation.

        None if simulation is not completed.
        """
        return self._summary

    def status(self) -> Progress:
        """Fetch status from the server to update progress and results.

        Parameters
        ----------
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.

        Return
        ------
        Progress
            The progress of the operation.

        """
        get_request = GetOperationRequest(name=self._long_running_op.name)
        self._long_running_op = self._server.operations_stub.GetOperation(get_request)
        progress = self._update_operation_status(self._long_running_op)
        return progress

    def wait(
        self,
        *,
        progress_update_interval: int = 5,
        progress_handler: IProgressHandler | None = None,
    ) -> None:
        """Wait for simulation to finish while updating progress.

        Parameters
        ----------
        progress_update_interval: int, default: 5
            A timeout value (in seconds) to give to the looped WaitOperation() calls to return an
            updated message for a progress update.
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.

        """
        LOG.debug(f"Waiting for {self._long_running_op.name} to complete")
        try:
            while True:
                timeout = Duration(seconds=progress_update_interval)
                wait_request = WaitOperationRequest(
                    name=self._long_running_op.name, timeout=timeout
                )
                awaited_operation = self._server.operations_stub.WaitOperation(wait_request)
                progress = self._update_operation_status(awaited_operation)
                if progress_handler:
                    progress_handler.update(progress)
                if awaited_operation.done:
                    break
        except Exception as e:
            LOG.error(f"Error while awaiting operation: {e}")

        # Perform a call to status to ensure all messages are received and summary is updated
        progress = self.status()
        if progress_handler:
            progress_handler.update(progress)

    def cancel(self) -> None:
        """Cancel a running simulation."""
        LOG.debug(f"Cancelling {self._long_running_op.name}")
        request = CancelOperationRequest(name=self._long_running_op.name)
        self._server.operations_stub.CancelOperation(request)

    @property
    def done(self) -> bool:
        """Check if the task is completed."""
        return self._long_running_op.done

    @staticmethod
    def _convert_metadata_to_progress(
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
        self,
        operation: Operation,
    ) -> Progress:
        """Update the simulation summaries.

        If an operation is completed, either the "error" field or
        the "response" field is available. Update the progress according to which
        field is available.

        Parameters
        ----------
        operation: [google.longrunning.Operation]
            The long-running operation.

        Return
        ------
        Progress
            The progress of the operation.

        """
        progress = self._convert_metadata_to_progress(operation.metadata)

        if operation.HasField("response"):
            response = SimulationResponse()
            operation.response.Unpack(response)
            self._summary = self._create_summary(response, progress)
        elif operation.HasField("error") and operation.error.code not in [
            Code.CANCELLED,
            Code.OK,
        ]:
            logs = ""
            if operation.error.details:
                info = ErrorInfo()
                operation.error.details[0].Unpack(info)
                if info.metadata["mimetype"] != "application/zip":
                    logs = base64.b64decode(info.metadata["logs"]).decode("utf-8")
                else:
                    logs = self._extract_logs(base64.b64decode(info.metadata["logs"]))

            self._summary = SimulationError(self._simulation_input, operation.error.message, logs)

            # ensure returned progress has an error state
            progress.state = ProgressState.ERROR

        return progress

    def _update_operation_status(
        self,
        operation: Operation,
    ) -> Progress:
        """Update progress or summary.

        If operation is done, update summary and progress.
        Otherwise, update progress only.

        Parameters
        ----------
        operation: [google.longrunning.Operation]
            The long-running operation.

        Returns
        -------
        Progress
            Progress created from long-running operation metadata.

        """
        if operation.done:
            # If operation is completed, get the summary and update progress. The server
            # should always mark the operation done on either a successful completion or
            # a simulation error.
            progress = self._unpack_summary(operation)
        else:
            # Otherwise, just update progress
            progress = self._convert_metadata_to_progress(operation.metadata)

        return progress

    def _create_summary(
        self, response: SimulationResponse, progress: Progress
    ) -> (
        SingleBeadSummary
        | PorositySummary
        | MicrostructureSummary
        | ThermalHistorySummary
        | Microstructure3DSummary
        | MaterialTuningSummary
    ):
        progress_state_to_simulation_status = {
            ProgressState.ERROR: SimulationStatus.ERROR,
            ProgressState.WARNING: SimulationStatus.WARNING,
            ProgressState.COMPLETED: SimulationStatus.COMPLETED,
        }
        simulation_status = progress_state_to_simulation_status[progress.state]
        if response.HasField("material_tuning_result"):
            return MaterialTuningSummary(
                self._simulation_input,
                response.material_tuning_result,
                self._user_data_path,
            )
        logs = ""
        if response.logs:
            logs = self._extract_logs(response.logs)
        if response.HasField("melt_pool"):
            thermal_history_output = None
            if self._check_if_thermal_history_is_present(response):
                thermal_history_output = os.path.join(
                    self._user_data_path, self._simulation_input.id, "thermal_history"
                )
                download_file(
                    self._server.simulation_stub,
                    response.melt_pool.thermal_history_vtk_zip,
                    thermal_history_output,
                )
            return SingleBeadSummary(
                self._simulation_input,
                response.melt_pool,
                logs,
                thermal_history_output,
                simulation_status,
            )
        if response.HasField("porosity_result"):
            return PorositySummary(
                self._simulation_input,
                response.porosity_result,
                logs,
                simulation_status,
            )
        if response.HasField("microstructure_result"):
            return MicrostructureSummary(
                self._simulation_input,
                response.microstructure_result,
                logs,
                self._user_data_path,
                simulation_status,
            )
        if response.HasField("microstructure_3d_result"):
            return Microstructure3DSummary(
                self._simulation_input,
                response.microstructure_3d_result,
                logs,
                self._user_data_path,
                simulation_status,
            )
        if response.HasField("thermal_history_result"):
            path = os.path.join(self._user_data_path, self._simulation_input.id, "coax_ave_output")
            local_zip = download_file(
                self._server.simulation_stub,
                response.thermal_history_result.coax_ave_zip_file,
                path,
            )
            with zipfile.ZipFile(local_zip, "r") as zip:
                zip.extractall(path)
            os.remove(local_zip)
            return ThermalHistorySummary(self._simulation_input, path, logs, simulation_status)

    def _check_if_thermal_history_is_present(self, response) -> bool:
        """Check if thermal history output is present in the response."""
        return response.melt_pool.thermal_history_vtk_zip != str()

    def _extract_logs(self, log_bytes: bytes) -> str:
        """
        Extract log files from an array of bytes.


        Parameters
        ----------
        log_bytes : bytes
            An array of bytes containing the one or more log files.
            The bytes are assumed to be zip encoded.

        Returns
        -------
        str
            A string containing the concatenated log file contents.
            The name of each log file will precede its contents.

        """
        if not log_bytes:
            return ""

        # Create a BytesIO object from log_bytes
        byte_stream_io = io.BytesIO(log_bytes)

        # Open the ZIP file from the byte stream
        with zipfile.ZipFile(byte_stream_io, "r") as zip_ref:
            # Initialize an empty string to store the concatenated content
            concatenated_content = ""

            # Iterate through the files in the ZIP archive
            for file_name in zip_ref.namelist():
                # Read the content of the file
                with zip_ref.open(file_name) as file:
                    file_content = file.read().decode("utf-8")

                # Concatenate the file name and its content
                concatenated_content += f"File: {file_name}\n{file_content}\n"

        return concatenated_content
