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

import hashlib
import logging
import os
import pathlib
import shutil
from unittest.mock import ANY, MagicMock, Mock, call, create_autospec, patch

from ansys.api.additive import __version__ as api_version
import ansys.api.additive.v0.about_pb2_grpc
from ansys.api.additive.v0.additive_domain_pb2 import (
    Microstructure3DResult,
    MicrostructureResult,
    PorosityResult,
)
from ansys.api.additive.v0.additive_domain_pb2 import MaterialTuningResult
from ansys.api.additive.v0.additive_domain_pb2 import MeltPool as MeltPoolMessage
from ansys.api.additive.v0.additive_domain_pb2 import MeltPool as MeltPoolMsg
from ansys.api.additive.v0.additive_domain_pb2 import Progress as ProgressMsg
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState as ProgressMsgState
from ansys.api.additive.v0.additive_domain_pb2 import ThermalHistoryResult
from ansys.api.additive.v0.additive_materials_pb2 import (
    GetMaterialRequest,
    GetMaterialsListResponse,
    TuneMaterialResponse,
)
from ansys.api.additive.v0.additive_operations_pb2 import OperationMetadata
from ansys.api.additive.v0.additive_simulation_pb2 import (
    SimulationRequest,
    SimulationResponse,
    UploadFileRequest,
    UploadFileResponse,
)
from google.longrunning.operations_pb2 import ListOperationsResponse, Operation
import grpc
import pytest

from ansys.additive.core import (
    USER_DATA_PATH,
    Additive,
    Microstructure3DInput,
    Microstructure3DSummary,
    MicrostructureInput,
    MicrostructureSummary,
    PorosityInput,
    PorositySummary,
    SimulationError,
    SimulationTask,
    SingleBeadInput,
    SingleBeadSummary,
    StlFile,
    ThermalHistoryInput,
    ThermalHistorySummary,
    __version__,
)
import ansys.additive.core.additive
import ansys.additive.core.download
from ansys.additive.core.exceptions import BetaFeatureNotEnabledError
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.material_tuning import MaterialTuningInput
from ansys.additive.core.progress_handler import (
    DefaultSingleSimulationProgressHandler,
    IProgressHandler,
    Progress,
)
from ansys.additive.core.server_connection import DEFAULT_PRODUCT_VERSION, ServerConnection
import ansys.additive.core.server_connection.server_connection
import ansys.additive.core.simulation_task

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
def test_update_progress_handler_reports_progress_from_metadata(server):
    # arrange
    operation = Operation()
    metadata = OperationMetadata(simulation_id="id", percent_complete=50.0, message="executing")
    operation.metadata.Pack(metadata)

    progress_handler = DummyProgressHandler()

    task = SimulationTask([server], "user_path", progress_handler)

    # act
    task._update_progress(operation.metadata, ProgressMsgState.PROGRESS_STATE_EXECUTING)

    # assert
    assert task._progress_handler.percent_complete == int(metadata.percent_complete)
    assert task._progress_handler.message == metadata.message
    assert task._progress_handler.sim_id == metadata.simulation_id
    assert task._progress_handler.progress_state == ProgressMsgState.PROGRESS_STATE_EXECUTING


@pytest.mark.parametrize(
    "sim_input",
    [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
        Microstructure3DInput(),
        ThermalHistoryInput(),
    ],
)
def test_add_simulation(sim_input):
    # arrange
    server_channel_str = "1.1.1.1"
    mock_server = Mock()
    mock_server.channel_str = server_channel_str

    task = SimulationTask([mock_server], "user_path")
    operation = Operation(name="id")

    # act
    task.add_simulation(server_channel_str, operation, sim_input)

    # assert
    assert task._long_running_ops
    assert task._long_running_ops[server_channel_str][0].name == "id"
    assert task._simulation_inputs
    assert isinstance(task._simulation_inputs[0], type(sim_input))


def test_get_server_from_simulation_id():
    # arrange
    server_channel_str = "1.1.1.1"
    mock_server_1 = Mock()
    mock_server_1.channel_str = server_channel_str
    server_channel_str = "1.1.1.2"
    mock_server_2 = Mock()
    mock_server_2.channel_str = server_channel_str
    server_channel_str = "1.1.1.3"
    mock_server_3 = Mock()
    mock_server_3.channel_str = server_channel_str

    task = SimulationTask([mock_server_1, mock_server_2, mock_server_3], "user_path")
    task.add_simulation(mock_server_1.channel_str, Operation(name="001"), SingleBeadInput())
    task.add_simulation(mock_server_2.channel_str, Operation(name="002"), SingleBeadInput())
    task.add_simulation(mock_server_2.channel_str, Operation(name="003"), SingleBeadInput())
    task.add_simulation(mock_server_3.channel_str, Operation(name="004"), SingleBeadInput())
    task.add_simulation(mock_server_3.channel_str, Operation(name="005"), SingleBeadInput())
    task.add_simulation(mock_server_3.channel_str, Operation(name="006"), SingleBeadInput())

    # act & assert
    assert task._get_server_from_simulation_id("001") == mock_server_1
    assert task._get_server_from_simulation_id("002") == mock_server_2
    assert task._get_server_from_simulation_id("003") == mock_server_2
    assert task._get_server_from_simulation_id("004") == mock_server_3
    assert task._get_server_from_simulation_id("005") == mock_server_3
    assert task._get_server_from_simulation_id("006") == mock_server_3


@pytest.mark.parametrize(
    "sim_input,result,expected_summary_type",
    [
        (SingleBeadInput(id="id"), MeltPoolMsg(), SingleBeadSummary),
        (PorosityInput(id="id"), PorosityResult(), PorositySummary),
        (MicrostructureInput(id="id"), MicrostructureResult(), MicrostructureSummary),
        (Microstructure3DInput(id="id"), Microstructure3DResult(), Microstructure3DSummary),
        (
            ThermalHistoryInput(
                id="id", geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))
            ),
            ThermalHistoryResult(),
            ThermalHistorySummary,
        ),
    ],
)
@patch("ansys.additive.core.simulation_task.download_file")
def test_unpack_summary_returns_correct_summary(
    mock_download_file, sim_input, result, expected_summary_type, tmp_path: pathlib.Path
):
    # arrange
    if isinstance(result, MeltPoolMsg):
        sim_response = SimulationResponse(id="id", melt_pool=result)
    elif isinstance(result, PorosityResult):
        sim_response = SimulationResponse(id="id", porosity_result=result)
    elif isinstance(result, MicrostructureResult):
        sim_response = SimulationResponse(id="id", microstructure_result=result)
    elif isinstance(result, Microstructure3DResult):
        sim_response = SimulationResponse(id="id", microstructure_3d_result=result)
    elif isinstance(result, ThermalHistoryResult):
        # arrange
        results_file = tmp_path / "results.zip"
        out_dir = tmp_path / "out_dir"
        shutil.copyfile(
            test_utils.get_test_file_path("thermal_history_results.zip"), str(results_file)
        )
        # mock_download_file.side_effect = lambda a, b, c: str(results_file)
        mock_download_file.return_value = str(results_file)
        sim_response = SimulationResponse(
            id="id", thermal_history_result=ThermalHistoryResult(coax_ave_zip_file="zip-file")
        )
    else:
        assert False, "Invalid result type"

    server_channel_str = "1.1.1.1"
    mock_server = Mock()
    mock_server.channel_str = server_channel_str
    mock_server.simulation_stub = None

    task = SimulationTask([mock_server], "user_path")
    task.add_simulation(server_channel_str, Operation(name="id"), sim_input)

    operation = Operation(name="id", done=True)
    operation.response.Pack(sim_response)

    # act
    summary = task._unpack_summary(operation)

    # assert
    assert isinstance(summary, expected_summary_type)


@patch("ansys.additive.core.additive.SimulationTask.status")
def test_collect_results_returns_only_summaries(_):
    # arrange
    mock_server = Mock()
    mock_server.channel_str = "1.1.1.1"
    summary = test_utils.get_test_SingleBeadSummary()
    error = SimulationError(SingleBeadInput(), "error")

    task = SimulationTask([mock_server], "user_path")
    task._summaries = {
        "sim1": summary,
        "sim2": summary,
        "sim3": summary,
        "sim4": error,
        "sim5": error,
    }

    # act
    results = task.collect_results()

    # assert
    assert len(results) == 3
    assert all(isinstance(x, SingleBeadSummary) for x in results)


@patch("ansys.additive.core.additive.SimulationTask.status")
def test_collect_errors_returns_only_SimulationError(_):
    # arrange
    mock_server = Mock()
    mock_server.channel_str = "1.1.1.1"
    summary = test_utils.get_test_SingleBeadSummary()
    error = SimulationError(SingleBeadInput(), "error")

    task = SimulationTask([mock_server], "user_path")
    task._summaries = {
        "sim1": summary,
        "sim2": summary,
        "sim3": summary,
        "sim4": error,
        "sim5": error,
    }

    # act
    results = task.collect_errors()

    # assert
    assert len(results) == 2
    assert all(isinstance(x, SimulationError) for x in results)


@patch("ansys.additive.core.simulation_task.SimulationTask._update_operation_status")
def test_status_calls_update_progress(update_mock):
    # arrange
    op_list = [Operation(name="op1"), Operation(name="op2"), Operation(name="op3")]
    response = ListOperationsResponse(operations=op_list)

    mock_server = Mock()
    mock_server.channel_str = "1.1.1.1"
    mock_server.operations_stub.ListOperations.return_value = response

    task = SimulationTask([mock_server], "user_path")

    # act
    task.status()

    # assert
    assert update_mock.call_count == len(op_list)


@patch("ansys.additive.core.simulation_task.SimulationTask._update_operation_status")
def test_wait_calls_update_progress_and_break_with_completed_operations(update_mock):
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

    task = SimulationTask([mock_server], "user_path")

    # act
    task.wait_all()

    # assert
    # Note the times 2 is because status() is called at end of wait_all()
    assert update_mock.call_count == 2 * len(op_list)
