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

import base64
import io
import os
import pathlib
import shutil
import tempfile
from unittest.mock import Mock, patch
import zipfile

import pytest
from google.longrunning.operations_pb2 import ListOperationsResponse, Operation
from google.protobuf.any_pb2 import Any
from google.rpc.code_pb2 import Code
from google.rpc.status_pb2 import Status
from google.rpc.error_details_pb2 import ErrorInfo

from ansys.additive.core import (
    Microstructure3DInput,
    Microstructure3DSummary,
    MicrostructureInput,
    MicrostructureSummary,
    PorosityInput,
    PorositySummary,
    SimulationTask,
    SingleBeadInput,
    SingleBeadSummary,
    StlFile,
    ThermalHistoryInput,
    ThermalHistorySummary,
)
from ansys.additive.core.material_tuning import (
    MaterialTuningInput,
    MaterialTuningSummary,
)
from ansys.additive.core.progress_handler import IProgressHandler, Progress
from ansys.additive.core.simulation import SimulationStatus
from ansys.additive.core.simulation_error import SimulationError
from ansys.api.additive.v0.additive_domain_pb2 import (
    MaterialTuningResult,
    Microstructure3DResult,
    MicrostructureResult,
    PorosityResult,
    ThermalHistoryResult,
)
from ansys.api.additive.v0.additive_domain_pb2 import MeltPool as MeltPoolMsg
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState as ProgressMsgState
from ansys.api.additive.v0.additive_operations_pb2 import OperationMetadata
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationResponse

from . import test_utils


class DummyProgressHandler(IProgressHandler):
    def __init__(self):
        self.sim_id = ""
        self.percent_complete = -1
        self.message = ""
        self.progress_state = ProgressMsgState.PROGRESS_STATE_UNSPECIFIED

    def update(self, progress: Progress):
        self.sim_id = progress.sim_id
        self.percent_complete = progress.percent_complete
        self.message = progress.message
        self.progress_state = progress.state


@patch("ansys.additive.core.additive.ServerConnection")
def test_convert_metadata_to_progress(server, tmp_path: pathlib.Path):
    # arrange
    operation = Operation()
    metadata = OperationMetadata(
        simulation_id="id",
        percent_complete=50.0,
        message="executing",
        state=ProgressMsgState.PROGRESS_STATE_EXECUTING,
    )
    operation.metadata.Pack(metadata)

    task = SimulationTask(server, operation, SingleBeadInput(), tmp_path)

    # act
    progress = task._convert_metadata_to_progress(operation.metadata)

    # assert
    assert progress.percent_complete == int(metadata.percent_complete)
    assert progress.message == metadata.message
    assert progress.sim_id == metadata.simulation_id
    assert progress.state == ProgressMsgState.PROGRESS_STATE_EXECUTING


@pytest.mark.parametrize(
    "sim_input,result,expected_summary_type",
    [
        (SingleBeadInput(), MeltPoolMsg(), SingleBeadSummary),
        (PorosityInput(), PorosityResult(), PorositySummary),
        (MicrostructureInput(), MicrostructureResult(), MicrostructureSummary),
        (Microstructure3DInput(), Microstructure3DResult(), Microstructure3DSummary),
        (
            ThermalHistoryInput(
                geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))
            ),
            ThermalHistoryResult(),
            ThermalHistorySummary,
        ),
        (
            MaterialTuningInput(
                experiment_data_file=test_utils.get_test_file_path(
                    pathlib.Path("Material") / "experimental_data.csv"
                ),
                material_configuration_file=test_utils.get_test_file_path(
                    pathlib.Path("Material") / "material-data.json"
                ),
                thermal_properties_lookup_file=test_utils.get_test_file_path(
                    pathlib.Path("Material") / "Test_Lookup.csv"
                ),
            ),
            MaterialTuningResult(
                optimized_parameters=b"optimized_parameters",
                characteristic_width_lookup=b"characteristic_width_lookup",
                coefficients=b"coefficients",
                material_parameters=b"material_parameters",
                log=b"log",
            ),
            MaterialTuningSummary,
        ),
    ],
)
@patch("ansys.additive.core.simulation_task.download_file")
def test_unpack_summary_returns_correct_summary(
    mock_download_file, sim_input, result, expected_summary_type, tmp_path: pathlib.Path
):
    # arrange
    if isinstance(result, MeltPoolMsg):
        sim_response = SimulationResponse(id=sim_input.id, melt_pool=result)
    elif isinstance(result, PorosityResult):
        sim_response = SimulationResponse(id=sim_input.id, porosity_result=result)
    elif isinstance(result, MicrostructureResult):
        sim_response = SimulationResponse(id=sim_input.id, microstructure_result=result)
    elif isinstance(result, Microstructure3DResult):
        sim_response = SimulationResponse(
            id=sim_input.id, microstructure_3d_result=result
        )
    elif isinstance(result, ThermalHistoryResult):
        # arrange
        results_file = tmp_path / "results.zip"
        shutil.copyfile(
            test_utils.get_test_file_path("thermal_history_results.zip"),
            str(results_file),
        )
        mock_download_file.return_value = str(results_file)
        sim_response = SimulationResponse(
            id=sim_input.id,
            thermal_history_result=ThermalHistoryResult(coax_ave_zip_file="zip-file"),
        )
    elif isinstance(result, MaterialTuningResult):
        sim_response = SimulationResponse(
            id=sim_input.id, material_tuning_result=result
        )
    else:
        assert False, "Invalid result type"

    server_channel_str = "1.1.1.1"
    mock_server = Mock()
    mock_server.channel_str = server_channel_str
    mock_server.simulation_stub = None

    metadata = OperationMetadata(
        simulation_id=sim_input.id,
        percent_complete=100.0,
        message="Done!",
        state=ProgressMsgState.PROGRESS_STATE_COMPLETED,
    )

    operation = Operation(name=sim_input.id, done=True)
    operation.response.Pack(sim_response)
    operation.metadata.Pack(metadata)
    task = SimulationTask(mock_server, operation, sim_input, tmp_path)

    # act
    progress = task._unpack_summary(operation)

    # assert
    assert isinstance(task.summary, expected_summary_type)
    assert progress.sim_id == sim_input.id
    assert progress.state == ProgressMsgState.PROGRESS_STATE_COMPLETED
    assert progress.percent_complete == 100.0
    assert progress.message == "Done!"


def test_unpack_summary_with_error(tmp_path: pathlib.Path):
    # arrange
    input = SingleBeadInput()
    mock_server = Mock()
    mock_server.channel_str = "1.1.1.1"
    mock_server.simulation_stub = None

    plain_text_logs = "Log file content"
    log_file_name = "log.txt"
    byte_stream = io.BytesIO()
    with zipfile.ZipFile(byte_stream, "w") as zip_ref:
        zip_ref.writestr(log_file_name, plain_text_logs)
    byte_stream.seek(0)
    zipped_logs = byte_stream.read()
    error_info = ErrorInfo()
    error_info.reason = "InternalError"
    error_info.domain = "additiveserver"
    error_info.metadata["mimetype"] = "application/zip"
    error_info.metadata["logs"] = base64.b64encode(zipped_logs).decode("ASCII")
    error_msg = "Error occurred"
    metadata = OperationMetadata(
        simulation_id=input.id,
        percent_complete=52,
        message=error_msg,
        state=ProgressMsgState.PROGRESS_STATE_ERROR,
    )
    status = Status()
    status.code = Code.INTERNAL
    status.message = error_msg
    error_info_any = Any()
    error_info_any.Pack(error_info)
    status.details.append(error_info_any)

    operation = Operation(name=input.id, done=True, error=status)
    operation.metadata.Pack(metadata)
    task = SimulationTask(mock_server, operation, SingleBeadInput(), tmp_path)

    # act
    progress = task._unpack_summary(operation)

    # assert
    assert isinstance(task.summary, SimulationError)
    assert progress.state == ProgressMsgState.PROGRESS_STATE_ERROR
    assert task.summary.logs == f"File: {log_file_name}\n{plain_text_logs}\n"


def test_unpack_summary_with_error_and_plain_text_logs(tmp_path: pathlib.Path):
    # arrange
    input = SingleBeadInput()
    mock_server = Mock()
    mock_server.channel_str = "1.1.1.1"
    mock_server.simulation_stub = None

    logs = "Log file content"
    error_info = ErrorInfo()
    error_info.reason = "InternalError"
    error_info.domain = "additiveserver"
    error_info.metadata["mimetype"] = "text/plain"
    error_info.metadata["logs"] = base64.b64encode(str.encode(logs))
    error_msg = "Error occurred"
    metadata = OperationMetadata(
        simulation_id=input.id,
        percent_complete=52,
        message=error_msg,
        state=ProgressMsgState.PROGRESS_STATE_ERROR,
    )
    status = Status()
    status.code = Code.INTERNAL
    status.message = error_msg
    error_info_any = Any()
    error_info_any.Pack(error_info)
    status.details.append(error_info_any)

    operation = Operation(name=input.id, done=True, error=status)
    operation.metadata.Pack(metadata)
    task = SimulationTask(mock_server, operation, SingleBeadInput(), tmp_path)

    # act
    progress = task._unpack_summary(operation)

    # assert
    assert isinstance(task.summary, SimulationError)
    assert progress.state == ProgressMsgState.PROGRESS_STATE_ERROR
    assert task.summary.logs == logs


@patch("ansys.additive.core.simulation_task.SimulationTask._update_operation_status")
def test_status_calls_update_progress(update_mock, tmp_path: pathlib.Path):
    # arrange
    op_list = [Operation(name="op1"), Operation(name="op2"), Operation(name="op3")]
    response = ListOperationsResponse(operations=op_list)

    mock_server = Mock()
    mock_server.channel_str = "1.1.1.1"
    mock_server.operations_stub.ListOperations.return_value = response

    task = SimulationTask(
        mock_server, Operation(name="op1"), SingleBeadInput(), tmp_path
    )

    # act
    task.status()

    # assert
    assert update_mock.call_count == 1


@patch("ansys.additive.core.simulation_task.SimulationTask._update_operation_status")
def test_wait_calls_update_progress_and_break_with_completed_operations(
    update_mock, tmp_path: pathlib.Path
):
    # arrange
    op_list = [
        Operation(name="op1", done=True),
        Operation(name="op2", done=True),
        Operation(name="op3", done=True),
    ]
    response = ListOperationsResponse(operations=op_list)

    mock_server = Mock()
    mock_server.channel_str = "1.1.1.1"
    mock_server.operations_stub.ListOperations.return_value = response

    task = SimulationTask(
        mock_server, Operation(name="op1"), SingleBeadInput(), tmp_path
    )

    # act
    task.wait()

    # assert
    # Note: status is updated twice within wait().
    assert update_mock.call_count == 2


@patch("ansys.additive.core.additive.ServerConnection")
def test_simulation_id_property_returns_id_from_input(
    mock_server, tmp_path: pathlib.Path
):
    # arrange
    sim_input = SingleBeadInput()

    task = SimulationTask(
        mock_server, Operation(name="some_other_name"), sim_input, tmp_path
    )

    # act & assert
    assert task.simulation_id == sim_input.id


def test_unpack_summary_with_cancelled_error(tmp_path: pathlib.Path):
    # arrange
    sim_input = SingleBeadInput()
    server_channel_str = "1.1.1.1"
    mock_server = Mock()
    mock_server.channel_str = server_channel_str
    mock_server.simulation_stub = None

    metadata = OperationMetadata(
        simulation_id=sim_input.id,
        percent_complete=50.0,
        message="Cancelled",
        state=ProgressMsgState.PROGRESS_STATE_CANCELLED,
    )

    operation = Operation(name=sim_input.id, done=True)
    operation.error.code = Code.CANCELLED
    operation.error.message = "Operation was cancelled"
    operation.metadata.Pack(metadata)
    task = SimulationTask(mock_server, operation, sim_input, tmp_path)

    # act
    progress = task._unpack_summary(operation)

    # assert
    assert task.summary is None
    assert progress.sim_id == sim_input.id
    assert progress.state == ProgressMsgState.PROGRESS_STATE_CANCELLED
    assert progress.percent_complete == 50.0
    assert progress.message == "Cancelled"


def test_extract_logs():
    # arrange
    plain_text_logs = "Log file content"
    log_file_name = "log.txt"
    expected_logs = f"File: {log_file_name}\n{plain_text_logs}\n"
    byte_stream = io.BytesIO()
    with zipfile.ZipFile(byte_stream, "w") as zip_ref:
        zip_ref.writestr(log_file_name, plain_text_logs)
    byte_stream.seek(0)
    zipped_logs = byte_stream.read()

    task = SimulationTask(Mock(), Operation(), SingleBeadInput(), pathlib.Path())

    # act
    logs = task._extract_logs(zipped_logs)

    # assert
    assert logs == expected_logs


def test_extract_logs_with_empty_logs():
    # arrange
    task = SimulationTask(Mock(), Operation(), SingleBeadInput(), pathlib.Path())

    # act
    logs = task._extract_logs(b"")

    # assert
    assert logs == ""


def test_extract_logs_with_invalid_zip_encoding():
    # arrange
    task = SimulationTask(Mock(), Operation(), SingleBeadInput(), pathlib.Path())

    # act & assert
    with pytest.raises(zipfile.BadZipFile):
        task._extract_logs(b"logs")


@pytest.mark.parametrize(
    "sim_input, response, expected_summary_type",
    [
        (
            test_utils.get_test_material_tuning_input(),
            SimulationResponse(material_tuning_result=MaterialTuningResult()),
            MaterialTuningSummary,
        ),
        (
            SingleBeadInput(),
            SimulationResponse(melt_pool=MeltPoolMsg()),
            SingleBeadSummary,
        ),
        (
            PorosityInput(),
            SimulationResponse(porosity_result=PorosityResult()),
            PorositySummary,
        ),
        (
            MicrostructureInput(),
            SimulationResponse(microstructure_result=MicrostructureResult()),
            MicrostructureSummary,
        ),
        (
            Microstructure3DInput(),
            SimulationResponse(microstructure_3d_result=Microstructure3DResult()),
            Microstructure3DSummary,
        ),
        (
            ThermalHistoryInput(),
            SimulationResponse(
                thermal_history_result=ThermalHistoryResult(
                    coax_ave_zip_file="zip-file"
                )
            ),
            ThermalHistorySummary,
        ),
    ],
)
@patch("ansys.additive.core.simulation_task.download_file")
def test_create_summary(
    mock_download_file,
    sim_input,
    response,
    expected_summary_type,
    tmp_path: pathlib.Path,
):
    # arrange
    mock_server = Mock()
    mock_server.simulation_stub = Mock()
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_zip_file = os.path.join(tmp_dir.name, "results.zip")
    shutil.copy(
        test_utils.get_test_file_path("thermal_history_results.zip"),
        tmp_zip_file,
    )
    mock_download_file.return_value = tmp_zip_file
    task = SimulationTask(mock_server, Operation(), sim_input, tmp_path)
    metadata = OperationMetadata(
        simulation_id="id",
        percent_complete=50.0,
        message="executing",
        state=ProgressMsgState.PROGRESS_STATE_WARNING,
    )
    progress = Progress.from_operation_metadata(metadata)

    # act
    summary = task._create_summary(response, progress)

    # assert
    assert isinstance(summary, expected_summary_type)
    if not isinstance(summary, MaterialTuningSummary):
        assert summary.status == SimulationStatus.WARNING


def test_create_summary_with_logs_calls_extract_logs(
    tmp_path: pathlib.Path,
):
    # arrange
    sim_input = SingleBeadInput()
    mock_server = Mock()
    mock_server.simulation_stub = Mock()
    response = SimulationResponse(melt_pool=MeltPoolMsg(), logs=b"logs")
    task = SimulationTask(mock_server, Operation(), sim_input, tmp_path)
    task._extract_logs = Mock()
    task._extract_logs.return_value = "logs"
    metadata = OperationMetadata(
        simulation_id="id",
        percent_complete=50.0,
        message="executing",
        state=ProgressMsgState.PROGRESS_STATE_WARNING,
    )
    progress = Progress.from_operation_metadata(metadata)

    # act
    summary = task._create_summary(response, progress)

    # assert
    task._extract_logs.assert_called_once_with(response.logs)
    assert summary.logs == "logs"
