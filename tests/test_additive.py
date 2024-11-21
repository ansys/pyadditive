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

import logging
import pathlib
from unittest import mock
from unittest.mock import (
    ANY,
    MagicMock,
    Mock,
    PropertyMock,
    call,
    create_autospec,
    patch,
)

import grpc
import pytest
from google.longrunning.operations_pb2 import Operation

import ansys.additive.core.additive
import ansys.additive.core.server_connection.server_connection
import ansys.additive.core.simulation_task
import ansys.api.additive.v0.about_pb2_grpc
import ansys.api.additive.v0.additive_settings_pb2_grpc
from ansys.additive.core import (
    USER_DATA_PATH,
    Additive,
    Microstructure3DInput,
    MicrostructureInput,
    PorosityInput,
    SimulationError,
    SimulationTask,
    SingleBeadInput,
    StlFile,
    ThermalHistoryInput,
    __version__,
)
from ansys.additive.core.exceptions import BetaFeatureNotEnabledError
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.material_tuning import MaterialTuningInput
from ansys.additive.core.parametric_study.constants import ColumnNames
from ansys.additive.core.parametric_study.parametric_study import ParametricStudy
from ansys.additive.core.parametric_study.parametric_study_progress_handler import (
    ParametricStudyProgressHandler,
)
from ansys.additive.core.progress_handler import (
    IProgressHandler,
    Progress,
    ProgressState,
)
from ansys.additive.core.server_connection import (
    DEFAULT_PRODUCT_VERSION,
    ServerConnection,
)
from ansys.additive.core.simulation import SimulationStatus, SimulationType
from ansys.additive.core.simulation_task_manager import SimulationTaskManager
from ansys.additive.core.single_bead import SingleBeadSummary
from ansys.api.additive import __version__ as api_version
from ansys.api.additive.v0.additive_domain_pb2 import (
    MaterialTuningResult,
    Microstructure3DResult,
    MicrostructureResult,
    PorosityResult,
    ThermalHistoryResult,
)
from ansys.api.additive.v0.additive_domain_pb2 import MeltPool as MeltPoolMsg
from ansys.api.additive.v0.additive_domain_pb2 import Progress as ProgressMsg
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState as ProgressMsgState
from ansys.api.additive.v0.additive_materials_pb2 import (
    AddMaterialResponse,
    GetMaterialRequest,
    GetMaterialsListResponse,
    RemoveMaterialRequest,
    TuneMaterialResponse,
)
from ansys.api.additive.v0.additive_operations_pb2 import OperationMetadata
from ansys.api.additive.v0.additive_settings_pb2 import (
    ListSettingsResponse,
    SettingsRequest,
    SettingsResponse,
)
from ansys.api.additive.v0.additive_simulation_pb2 import (
    SimulationResponse,
    UploadFileResponse,
)

from . import test_utils


@pytest.mark.parametrize(
    "in_prod_version, expected_prod_version",
    [
        (None, DEFAULT_PRODUCT_VERSION),
        ("123", "123"),
        ("", DEFAULT_PRODUCT_VERSION),
    ],
)
def test_Additive_init_calls_connect_to_server_correctly(
    monkeypatch: pytest.MonkeyPatch, in_prod_version, expected_prod_version
):
    # arrange
    server_connections = ["connection1", "connection2"]
    host = "hostname"
    port = 12345

    mock_server_connection = Mock(ServerConnection)
    mock_connect = create_autospec(
        ansys.additive.core.additive.Additive._connect_to_server,
        return_value=mock_server_connection,
    )
    monkeypatch.setattr(ansys.additive.core.additive.Additive, "_connect_to_server", mock_connect)

    # act
    additive = Additive(
        server_connections,
        host,
        port,
        product_version=in_prod_version,
        linux_install_path=None,
    )

    # assert
    mock_connect.assert_called_with(
        server_connections, host, port, expected_prod_version, ANY, None
    )
    assert additive._server == mock_server_connection
    assert additive._user_data_path == USER_DATA_PATH


@patch("ansys.additive.core.additive.ServerConnection")
def test_Additive_init_assigns_nsims_per_server(server):
    # arrange
    nsims_per_server = 99

    # Mock makes SettingsServiceStub unable to use assert_called_once (somehow it's considered
    # a NonCallable mock). So we manually create the mock and test the calls manually.
    mock_connection_with_stub = Mock(ServerConnection)
    mock_connection_with_stub.settings_stub.ApplySettings.return_value = SettingsResponse(
        messages="applied"
    )
    server.return_value = mock_connection_with_stub
    expected_request = SettingsRequest()
    setting = expected_request.settings.add()
    setting.key = "NumConcurrentSims"
    setting.value = str(nsims_per_server)

    # act
    Additive(nsims_per_server=nsims_per_server)

    # assert
    assert mock_connection_with_stub.settings_stub.ApplySettings.call_count == 1
    assert mock_connection_with_stub.settings_stub.ApplySettings.call_args[0][0] == expected_request


@patch("ansys.additive.core.additive.ServerConnection")
def test_apply_server_settings_returns_appropriate_responses(server):
    # arrange
    settings = {"key": "value"}
    # Mock makes SettingsServiceStub unable to use assert_called_once (somehow it's considered
    # a NonCallable mock). So we manually create the mock and test the calls manually.
    channel_str = "1.1.1.1"
    mock_connection_with_stub = Mock(ServerConnection)
    mock_connection_with_stub.channel_str = channel_str
    response = SettingsResponse()
    response.messages.append("applied")
    mock_connection_with_stub.settings_stub.ApplySettings = Mock(return_value=response)
    server.return_value = mock_connection_with_stub
    expected_request = SettingsRequest()
    setting = expected_request.settings.add()
    setting.key = "key"
    setting.value = "value"

    # ApplySettings is called once here
    additive = Additive()

    # act
    result = additive.apply_server_settings(settings)

    # assert
    assert mock_connection_with_stub.settings_stub.ApplySettings.call_count == 2
    assert mock_connection_with_stub.settings_stub.ApplySettings.call_args[0][0] == expected_request
    assert result == ["applied"]


@patch("ansys.additive.core.additive.ServerConnection")
def test_list_server_settings_returns_appropriate_responses(server):
    # arrange
    # Mock makes SettingsServiceStub unable to use assert_called_once (somehow it's considered
    # a NonCallable mock). So we manually create the mock and test the calls manually.
    channel_str = "1.1.1.1"
    mock_connection_with_stub = Mock(ServerConnection)
    response = ListSettingsResponse()
    setting = response.settings.add()
    setting.key = "key"
    setting.value = "value"
    mock_connection_with_stub.settings_stub.ListSettings.return_value = response
    server.return_value = mock_connection_with_stub

    # ApplySettings is called once here
    additive = Additive()

    # act
    result = additive.list_server_settings()

    # assert
    assert mock_connection_with_stub.settings_stub.ListSettings.call_count == 1
    assert result == {"key": "value"}


@patch("ansys.additive.core.additive.ServerConnection")
def test_connect_to_server_with_channel_creates_server_connection(
    mock_connection,
):
    # arrange
    mock_connection.return_value = Mock(ServerConnection)
    host1 = "localhost:1234"
    channel = grpc.insecure_channel("target")
    log = logging.Logger("testlogger")

    # act
    server = Additive._connect_to_server(
        channel=channel,
        host=host1,
        port=99999,
        log=log,
    )

    # assert
    assert server is not None
    mock_connection.assert_called_once_with(channel=channel, log=log)


@patch("ansys.additive.core.additive.ServerConnection")
def test_connect_to_server_with_host_creates_server_connection(mock_connection):
    # arrange
    mock_connection.return_value = Mock(ServerConnection)
    host = "127.0.0.1"
    port = 9999
    log = logging.Logger("testlogger")

    # act
    server = Additive._connect_to_server(channel=None, host=host, port=port, log=log)

    # assert
    assert server is not None
    mock_connection.assert_called_once_with(addr=f"{host}:{port}", log=log)


@patch("ansys.additive.core.additive.ServerConnection")
def test_connect_to_server_with_env_var_creates_server_connection(
    mock_connection, monkeypatch: pytest.MonkeyPatch
):
    # arrange
    addr = "localhost:1234"
    monkeypatch.setenv("ANSYS_ADDITIVE_ADDRESS", addr)
    mock_connection.return_value = Mock(ServerConnection)
    log = logging.Logger("testlogger")

    # act
    server = Additive._connect_to_server(log=log)

    # assert
    assert server is not None
    mock_connection.assert_called_once_with(addr=addr, log=log)


def test_about_prints_not_connected_message():
    # arrange
    mock_additive = MagicMock()
    mock_additive.about = Additive.about
    mock_additive._server = None

    # act
    about = mock_additive.about(mock_additive)

    # assert
    assert (
        f"ansys.additive.core version {__version__}\nClient side API version: {api_version}"
        in about
    )
    assert "Client is not connected to a server." in about


def test_about_prints_server_status_messages():
    # arrange
    mock_additive = MagicMock()
    mock_additive.about = Additive.about
    mockServer = Mock(ServerConnection)
    mockServer.status.return_value = f"server status"
    mock_additive._server = mockServer

    # act
    about = mock_additive.about(mock_additive)

    # assert
    assert (
        f"ansys.additive.core version {__version__}\nClient side API version: {api_version}"
        in about
    )
    assert f"server status" in about


@pytest.mark.parametrize(
    "sim_input",
    [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
        ThermalHistoryInput(),
        Microstructure3DInput(),
    ],
)
# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_async_with_single_input_calls_internal_simulate_once(_, sim_input):
    # arrange
    sim_input.material = test_utils.get_test_material()

    metadata = OperationMetadata(simulation_id=sim_input.id, message="Simulation Started")
    expected_operation = Operation(name=sim_input.id)
    expected_operation.metadata.Pack(metadata)
    with patch("ansys.additive.core.additive.Additive._simulate") as _simulate_patch:
        _simulate_patch.return_value = expected_operation
    additive = Additive(enable_beta_features=True)
    additive._simulate = _simulate_patch

    # act
    task_manager = additive.simulate_async(sim_input)

    # assert
    _simulate_patch.assert_called_once_with(sim_input, ANY, ANY)
    assert isinstance(task_manager, SimulationTaskManager)


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_with_empty_input_list_raises_exception(_):
    # arrange
    additive = Additive()

    # act, assert
    with pytest.raises(ValueError):
        additive.simulate([])


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_logs_error_message_when_SimulationError_returned(_, caplog):
    # arrange
    sim_input = SingleBeadInput(material=test_utils.get_test_material())
    error_msg = "error message"
    simulation_error = SimulationError(sim_input, error_msg)
    mock_task_mgr = Mock(SimulationTaskManager)
    mock_task_mgr.summaries.return_value = [simulation_error]
    with patch("ansys.additive.core.additive.Additive.simulate_async") as sim_async_patch:
        sim_async_patch.return_value = mock_task_mgr
    additive = Additive()
    additive.simulate_async = sim_async_patch
    caplog.set_level(logging.ERROR, "PyAdditive_global")

    # act
    summary = additive.simulate(sim_input)

    # assert
    assert isinstance(summary, SimulationError)
    assert error_msg in caplog.text
    sim_async_patch.assert_called_once_with(sim_input, None)


@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_returns_single_summary_for_single_input(_):
    # arrange
    sim_input = SingleBeadInput(material=test_utils.get_test_material())
    summary = SingleBeadSummary(sim_input, test_utils.get_test_melt_pool_message())
    mock_task_mgr = Mock(SimulationTaskManager)
    mock_task_mgr.summaries.return_value = [summary]
    with patch("ansys.additive.core.additive.Additive.simulate_async") as sim_async_patch:
        sim_async_patch.return_value = mock_task_mgr
    additive = Additive()
    additive.simulate_async = sim_async_patch

    # act
    summary = additive.simulate(sim_input)

    # assert
    assert isinstance(summary, SingleBeadSummary)


@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_returns_list_of_summaries_for_list_of_inputs(_):
    # arrange
    sim_input = SingleBeadInput(material=test_utils.get_test_material())
    summary = SingleBeadSummary(sim_input, test_utils.get_test_melt_pool_message())
    mock_task_mgr = Mock(SimulationTaskManager)
    mock_task_mgr.summaries.return_value = [summary]
    with patch("ansys.additive.core.additive.Additive.simulate_async") as sim_async_patch:
        sim_async_patch.return_value = mock_task_mgr
    additive = Additive()
    additive.simulate_async = sim_async_patch

    # act
    summaries = additive.simulate([sim_input])

    # assert
    assert isinstance(summaries, list)
    assert len(summaries) == 1


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_async_with_input_list_calls_internal_simulate_n_times(connection):
    # arrange
    metadata = OperationMetadata()
    # Note this operation name doesn't match the input id but we're only testing number of calls
    expected_operation = Operation(name="sim_id")
    metadata.message = "running"
    metadata.context = "simulation"
    metadata.percent_complete = 50.0
    expected_operation.metadata.Pack(metadata)
    sim_task = SimulationTask(connection, expected_operation, SingleBeadInput(), "path")

    with patch("ansys.additive.core.additive.Additive._simulate") as _simulate_patch:
        _simulate_patch.return_value = sim_task
    additive = Additive(enable_beta_features=True)
    additive._simulate = _simulate_patch
    inputs = [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
        ThermalHistoryInput(),
        Microstructure3DInput(),
    ]

    # act
    task_manager = additive.simulate_async(inputs)

    # assert
    assert isinstance(task_manager, SimulationTaskManager)
    assert _simulate_patch.call_count == len(inputs)
    calls = [call(i, ANY, None) for i in inputs]
    _simulate_patch.assert_has_calls(calls, any_order=True)


@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_study_async_performs_expected_steps(tmp_path: pathlib.Path):
    # arrange
    additive = Additive()
    additive.simulate_async = MagicMock(return_value=SimulationTaskManager())
    material = AdditiveMaterial(name="material")
    additive.material = Mock(return_value=material)
    sb = SingleBeadInput(material=material)
    p = PorosityInput(material=material)
    inputs = [sb, p]
    study = ParametricStudy(tmp_path / "test-study", "material")
    study.add_inputs(inputs)
    study._data_frame[ColumnNames.ERROR_MESSAGE] = "error message"

    # act
    task_mgr = additive.simulate_study_async(study)

    # assert
    assert isinstance(task_mgr, SimulationTaskManager)
    assert all(s == SimulationStatus.PENDING for s in study.data_frame()[ColumnNames.STATUS].values)
    assert all(e is None for e in study.data_frame()[ColumnNames.ERROR_MESSAGE].values)
    additive.simulate_async.assert_called_once_with(inputs, None)


@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_study_async_passes_params_to_simulation_inputs(_, tmp_path: pathlib.Path):
    # arrange
    additive = Additive()
    additive.simulate_async = MagicMock(return_value=SimulationTaskManager())
    material = AdditiveMaterial(name="material")
    additive.material = Mock(return_value=material)
    sb = SingleBeadInput(material=material)
    p = PorosityInput(material=material)
    inputs = [sb, p]
    study = ParametricStudy(tmp_path / "test-study", "material")
    study.add_inputs(inputs)
    study._data_frame[ColumnNames.ERROR_MESSAGE] = "error message"
    study.simulation_inputs = Mock(return_value=inputs)
    # Since we're mocking simulation_inputs(), we need to mock the save method
    study.save = MagicMock()
    sim_ids = [sb.id, p.id]
    types = [SimulationType.SINGLE_BEAD, SimulationType.POROSITY]
    priority = 0
    iteration = 1

    # act
    additive.simulate_study_async(study, sim_ids, types, priority, iteration)

    # assert
    study.simulation_inputs.assert_called_once_with(
        additive.material, sim_ids, types, priority, iteration
    )


@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_study_performs_expected_steps(_, tmp_path: pathlib.Path):
    # arrange
    additive = Additive()
    mock_task_mgr = Mock(SimulationTaskManager)
    mock_done = PropertyMock(side_effect=[False, True])
    type(mock_task_mgr).done = mock_done
    mock_summaries_list = [test_utils.get_test_SingleBeadSummary()]
    mock_task_mgr.summaries.return_value = mock_summaries_list
    mock_task_mgr.status = Mock(SimulationTaskManager.status)
    additive.simulate_study_async = MagicMock(return_value=mock_task_mgr)
    sb = SingleBeadInput()
    p = PorosityInput()
    inputs = [sb, p]
    study = ParametricStudy(tmp_path / "test-study", "material")
    study.add_inputs(inputs)
    study.update = MagicMock()
    simIds = [sb.id, p.id]
    types = [SimulationType.SINGLE_BEAD, SimulationType.POROSITY]
    priority = 0
    iteration = 1

    # act
    additive.simulate_study(study, simIds, types, priority, iteration)

    # assert
    additive.simulate_study_async.assert_called_once_with(
        study, simIds, types, priority, iteration, mock.ANY
    )
    assert isinstance(additive.simulate_study_async.call_args[0][5], ParametricStudyProgressHandler)
    mock_task_mgr.status.assert_called_once()
    assert isinstance(mock_task_mgr.status.call_args[0][0], ParametricStudyProgressHandler)


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_with_duplicate_simulation_ids_raises_exception(_):
    # arrange
    with patch("ansys.additive.core.additive.Additive._simulate") as _simulate_patch:
        _simulate_patch.return_value = None
    additive = Additive()
    additive._simulate = _simulate_patch
    inputs = [SingleBeadInput(), PorosityInput()]
    # overwrite the second input's ID with the first input's ID
    inputs[1]._id = inputs[0].id

    # act, assert
    with pytest.raises(ValueError, match="Duplicate simulation ID"):
        additive.simulate(inputs)


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_async_with_duplicate_simulation_ids_raises_exception(_):
    # arrange
    with patch("ansys.additive.core.additive.Additive._simulate") as _simulate_patch:
        _simulate_patch.return_value = None
    additive = Additive()
    additive._simulate = _simulate_patch
    inputs = [SingleBeadInput(), PorosityInput()]
    # overwrite the second input's ID with the first input's ID
    inputs[1]._id = inputs[0].id

    # act, assert
    with pytest.raises(ValueError, match="Duplicate simulation ID"):
        additive.simulate_async(inputs)


@pytest.mark.parametrize(
    "sim_input,result",
    [
        (SingleBeadInput(), MeltPoolMsg()),
        (PorosityInput(), PorosityResult()),
        (MicrostructureInput(), MicrostructureResult()),
        (Microstructure3DInput(), Microstructure3DResult()),
        (
            ThermalHistoryInput(
                geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))
            ),
            ThermalHistoryResult(),
        ),
    ],
)
@patch("ansys.additive.core.additive.ServerConnection")
def test_internal_simulate_called_with_single_input_updates_SimulationTask(
    mock_connection,
    monkeypatch: pytest.MonkeyPatch,
    sim_input,
    result,
):
    # arrange
    mock_status = create_autospec(
        ansys.additive.core.additive.SimulationTask.status,
        return_value=Progress(
            sim_id="id",
            state=ProgressState.COMPLETED,
            percent_complete=100,
            message="done",
            context="simulation",
        ),
    )
    monkeypatch.setattr(ansys.additive.core.additive.SimulationTask, "status", mock_status)
    sim_input.material = test_utils.get_test_material()

    if isinstance(result, MeltPoolMsg):
        sim_response = SimulationResponse(id="id", melt_pool=result)
    elif isinstance(result, PorosityResult):
        sim_response = SimulationResponse(id="id", porosity_result=result)
    elif isinstance(result, MicrostructureResult):
        sim_response = SimulationResponse(id="id", microstructure_result=result)
    elif isinstance(result, Microstructure3DResult):
        sim_response = SimulationResponse(id="id", microstructure_3d_result=result)
    elif isinstance(result, ThermalHistoryResult):
        sim_response = SimulationResponse(id="id", thermal_history_result=result)
    else:
        assert False, "Invalid result type"

    metadata = OperationMetadata(
        simulation_id="id",
        state=ProgressState.COMPLETED,
        percent_complete=100,
        message="done",
        context="simulation",
    )
    long_running_operation = Operation(name="id", done=True)
    long_running_operation.response.Pack(sim_response)
    long_running_operation.metadata.Pack(metadata)

    remote_file_name = "remote/file/name"
    upload_response = UploadFileResponse(
        remote_file_name=remote_file_name,
        progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_COMPLETED, message="done"),
    )

    server_channel_str = "1.1.1.1"
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.Simulate.return_value = long_running_operation
    mock_connection_with_stub.simulation_stub.UploadFile.return_value = [upload_response]
    mock_connection_with_stub.operations_stub.GetOperation.return_value = long_running_operation
    mock_connection_with_stub.channel_str = server_channel_str
    mock_connection.return_value = mock_connection_with_stub

    additive = Additive(
        enable_beta_features=True,
        nsims_per_server=2,
    )
    mock_progress_handler = Mock(IProgressHandler)

    # act
    task = additive._simulate(
        simulation_input=sim_input,
        server=mock_connection_with_stub,
        progress_handler=mock_progress_handler,
    )

    # assert
    operation = task._long_running_op
    assert operation.done
    response = SimulationResponse()
    operation.response.Unpack(response)
    if isinstance(result, MeltPoolMsg):
        assert response.HasField("melt_pool")
    elif isinstance(result, PorosityResult):
        assert response.HasField("porosity_result")
    elif isinstance(result, MicrostructureResult):
        assert response.HasField("microstructure_result")
    elif isinstance(result, Microstructure3DResult):
        assert response.HasField("microstructure_3d_result")
    elif isinstance(result, ThermalHistoryResult):
        assert response.HasField("thermal_history_result")
    else:
        assert False, "Invalid result type"
    if not isinstance(sim_input, ThermalHistoryInput):
        mock_progress_handler.update.assert_called_once()
    else:
        assert mock_progress_handler.update.call_count == 2


@pytest.mark.parametrize(
    "sim_input",
    [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
        ThermalHistoryInput(),
        Microstructure3DInput(),
    ],
)
# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_internal_simulate_without_material_raises_exception(server, sim_input):
    # arrange
    additive = Additive(enable_beta_features=True)

    # act, assert
    with pytest.raises(ValueError, match="A material is not assigned to the simulation input"):
        additive._simulate(simulation_input=sim_input, server=server)


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
# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_exception_during_internal_simulate_returns_operation_with_error(_, sim_input):
    # arrange
    error_msg = "simulation error"

    def iterable_with_exception(_):
        raise Exception(error_msg)

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.Simulate.side_effect = iterable_with_exception
    mock_connection_with_stub.channel_str = "1.1.1.1"
    sim_input.material = test_utils.get_test_material()
    additive = Additive(enable_beta_features=True)

    # act
    task = additive._simulate(sim_input, mock_connection_with_stub)

    # assert
    result = task._long_running_op
    assert isinstance(result, Operation)
    assert result.done
    metadata = OperationMetadata()
    result.metadata.Unpack(metadata)
    if not isinstance(sim_input, ThermalHistoryInput):
        assert metadata.message == error_msg
    else:
        assert metadata.message


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_internal_simulate_returns_errored_operation_from_server(mock_server):
    # arrange
    error_msg = "simulation error"
    progress_msg = ProgressMsg(
        state=ProgressMsgState.PROGRESS_STATE_ERROR,
        percent_complete=50,
        message=error_msg,
        context="simulation",
    )
    sim_response = SimulationResponse(id="id", progress=progress_msg)

    # make metadata have different values than progress message to
    # allow testing of each field
    metadata = OperationMetadata(
        simulation_id="diff_id",
        context="server",
        message=error_msg,
        percent_complete=60,
        state=ProgressMsgState.PROGRESS_STATE_ERROR,
    )
    errored_operation = Operation(name="diff_id", done=True)
    errored_operation.metadata.Pack(metadata)
    errored_operation.response.Pack(sim_response)

    input = SingleBeadInput(material=test_utils.get_test_material())

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.Simulate.return_value = errored_operation
    mock_connection_with_stub.channel_str = "1.1.1.1"
    mock_server.return_value = mock_connection_with_stub
    additive = Additive(nsims_per_server=1)

    # act
    task = additive._simulate(input, mock_connection_with_stub)

    # assert
    result = task._long_running_op
    assert isinstance(result, Operation)
    assert result.name == "diff_id"

    result_metadata = OperationMetadata()
    result.metadata.Unpack(result_metadata)
    assert result_metadata.simulation_id == "diff_id"
    assert error_msg in result_metadata.message
    assert result_metadata.percent_complete == 60.0
    assert result_metadata.context == "server"
    assert result_metadata.state == ProgressMsgState.PROGRESS_STATE_ERROR

    assert result.HasField("response")
    result_response = SimulationResponse()
    result.response.Unpack(result_response)
    assert result_response.id == "id"
    assert result_response.progress.state == ProgressMsgState.PROGRESS_STATE_ERROR
    assert result_response.progress.context == "simulation"
    assert result_response.progress.percent_complete == 50.0


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_materials_list_returns_list_of_material_names(mock_connection):
    # arrange
    names = ["material1", "material2"]
    materials_list_response = GetMaterialsListResponse(names=names)
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.GetMaterialsList.return_value = materials_list_response
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act
    result = additive.materials_list()

    # assert
    assert result == names


@patch("ansys.additive.core.additive.ServerConnection")
def test_get_material_returns_material(mock_connection):
    # arrange
    material = test_utils.get_test_material()
    material_name = "vibranium"
    material.name = material_name
    material_msg = material._to_material_message()
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.GetMaterial.return_value = material_msg
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act
    result = additive.material(material_name)

    # assert
    assert result == material
    mock_connection_with_stub.materials_stub.GetMaterial.assert_called_once_with(
        GetMaterialRequest(name=material_name)
    )


def test_load_material_returns_material():
    # arrange
    parameters_file = test_utils.get_test_file_path(pathlib.Path("Material") / "material-data.json")
    thermal_lookup_file = test_utils.get_test_file_path(
        pathlib.Path("Material") / "Test_Lookup.csv"
    )
    characteristic_width_lookup_file = test_utils.get_test_file_path(
        pathlib.Path("Material") / "Test_CW_Lookup.csv"
    )

    # act
    material = Additive.load_material(
        parameters_file, thermal_lookup_file, characteristic_width_lookup_file
    )

    # assert
    assert isinstance(material, AdditiveMaterial)
    assert material.name == "TestMaterial"
    assert material.description == "Test material description"
    assert material.absorptivity_maximum == 1
    assert material.absorptivity_minimum == 2
    assert material.absorptivity_powder_coefficient_a == 3
    assert material.absorptivity_powder_coefficient_b == 4
    assert material.absorptivity_solid_coefficient_a == 5
    assert material.absorptivity_solid_coefficient_b == 6
    assert material.anisotropic_strain_coefficient_parallel == 7
    assert material.anisotropic_strain_coefficient_perpendicular == 8
    assert material.anisotropic_strain_coefficient_z == 9
    assert material.elastic_modulus == 10
    assert material.hardening_factor == 12
    assert material.liquidus_temperature == 13
    assert material.material_yield_strength == 14
    assert material.nucleation_constant_bulk == 15
    assert material.nucleation_constant_interface == 16
    assert material.penetration_depth_maximum == 17
    assert material.penetration_depth_minimum == 18
    assert material.penetration_depth_powder_coefficient_a == 19
    assert material.penetration_depth_powder_coefficient_b == 20
    assert material.penetration_depth_solid_coefficient_a == 21
    assert material.penetration_depth_solid_coefficient_b == 22
    assert material.poisson_ratio == 23
    assert material.powder_packing_density == 24
    assert material.purging_gas_convection_coefficient == 25
    assert material.solid_density_at_room_temperature == 26
    assert material.solid_specific_heat_at_room_temperature == 27
    assert material.solid_thermal_conductivity_at_room_temperature == 28
    assert material.solidus_temperature == 29
    assert material.strain_scaling_factor == 30
    assert material.support_yield_strength_ratio == 31
    assert material.thermal_expansion_coefficient == 32
    assert material.vaporization_temperature == 33
    assert len(material.characteristic_width_data) == 64
    assert material.characteristic_width_data[0].scan_speed == 0.35
    assert material.characteristic_width_data[0].laser_power == 50
    assert material.characteristic_width_data[0].characteristic_width == 0.000054939
    assert len(material.thermal_properties_data) == 7500
    row = material.thermal_properties_data[0]
    assert row.temperature == 2
    assert row.thermal_conductivity == 8.3067794
    assert row.specific_heat == 260.25
    assert row.density == 8631.11931
    assert row.thermal_conductivity_ratio == 0.01
    assert row.density_ratio == 0.6
    assert row.specific_heat_ratio == 1


@patch("ansys.additive.core.additive.ServerConnection")
def test_add_material_calls_material_service_add_material(mock_connection):
    # arrange
    parameters_file = test_utils.get_test_file_path(pathlib.Path("Material") / "material-data.json")
    thermal_lookup_file = test_utils.get_test_file_path(
        pathlib.Path("Material") / "Test_Lookup.csv"
    )
    characteristic_width_lookup_file = test_utils.get_test_file_path(
        pathlib.Path("Material") / "Test_CW_Lookup.csv"
    )
    loaded_material = Additive.load_material(
        parameters_file, thermal_lookup_file, characteristic_width_lookup_file
    )
    added_material = AdditiveMaterial()
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.AddMaterial.return_value = AddMaterialResponse(
        id="id", material=added_material._to_material_message()
    )
    mock_connection_with_stub.materials_stub.GetMaterialsList.return_value = (
        GetMaterialsListResponse(names=[])
    )
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act
    result = additive.add_material(
        parameters_file, thermal_lookup_file, characteristic_width_lookup_file
    )

    # assert
    assert result == added_material
    mock_connection_with_stub.materials_stub.AddMaterial.assert_called_once()
    assert len(mock_connection_with_stub.materials_stub.AddMaterial.call_args[0][0].id) > 0
    assert (
        mock_connection_with_stub.materials_stub.AddMaterial.call_args[0][0].material
        == loaded_material._to_material_message()
    )


@patch("ansys.additive.core.additive.ServerConnection")
def test_add_material_raises_ValueError_when_adding_existing_material(mock_connection):
    # arrange
    parameters_file = test_utils.get_test_file_path(pathlib.Path("Material") / "material-data.json")
    thermal_lookup_file = test_utils.get_test_file_path(
        pathlib.Path("Material") / "Test_Lookup.csv"
    )
    characteristic_width_lookup_file = test_utils.get_test_file_path(
        pathlib.Path("Material") / "Test_CW_Lookup.csv"
    )
    loaded_material = Additive.load_material(
        parameters_file, thermal_lookup_file, characteristic_width_lookup_file
    )
    added_material = AdditiveMaterial()
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.AddMaterial.return_value = AddMaterialResponse(
        id="id", material=added_material._to_material_message()
    )
    mock_connection_with_stub.materials_stub.GetMaterialsList.return_value = (
        GetMaterialsListResponse(names=[loaded_material.name])
    )
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act, assert
    with pytest.raises(ValueError, match="already exists"):
        additive.add_material(
            parameters_file, thermal_lookup_file, characteristic_width_lookup_file
        )


@patch("ansys.additive.core.additive.ServerConnection")
def test_add_material_raises_RuntimeError_when_server_errors(mock_connection):
    # arrange
    parameters_file = test_utils.get_test_file_path(pathlib.Path("Material") / "material-data.json")
    thermal_lookup_file = test_utils.get_test_file_path(
        pathlib.Path("Material") / "Test_Lookup.csv"
    )
    characteristic_width_lookup_file = test_utils.get_test_file_path(
        pathlib.Path("Material") / "Test_CW_Lookup.csv"
    )
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.AddMaterial.return_value = AddMaterialResponse(
        id="id", error="error"
    )
    mock_connection_with_stub.materials_stub.GetMaterialsList.return_value = (
        GetMaterialsListResponse(names=[])
    )
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act, assert
    with pytest.raises(RuntimeError, match="error"):
        additive.add_material(
            parameters_file, thermal_lookup_file, characteristic_width_lookup_file
        )


@patch("ansys.additive.core.additive.ServerConnection")
def test_remove_material_calls_material_service_remove_material(mock_connection):
    # arrange
    material_name = "vibranium"
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.RemoveMaterial.return_value = None
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act
    additive.remove_material(material_name)

    # assert
    mock_connection_with_stub.materials_stub.RemoveMaterial.assert_called_once_with(
        RemoveMaterialRequest(name=material_name)
    )


@patch("ansys.additive.core.additive.ServerConnection")
def test_remove_material_raises_ValueError_when_removing_reserved_material(
    mock_connection,
):
    material_name = "ALSI10MG"
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.RemoveMaterial.return_value = None
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act, assert
    with pytest.raises(ValueError, match="Unable to remove Ansys-supplied material"):
        additive.remove_material(material_name)


@patch("ansys.additive.core.additive.ServerConnection")
def test_tune_material_async_raises_exception_if_output_path_exists(_, tmp_path: pathlib.Path):
    # arrange
    input = MaterialTuningInput(
        experiment_data_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "experimental_data.csv"
        ),
        material_configuration_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "material-data.json"
        ),
        thermal_properties_lookup_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "Test_Lookup.csv"
        ),
    )
    additive = Additive()

    # act, assert
    with pytest.raises(ValueError, match="already exists"):
        additive.tune_material_async(input, out_dir=tmp_path)


@patch("ansys.additive.core.additive.ServerConnection")
def test_tune_material_async_calls_material_service_tune_material(
    mock_connection, tmp_path: pathlib.Path
):
    # assemble
    input = MaterialTuningInput(
        experiment_data_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "experimental_data.csv"
        ),
        material_configuration_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "material-data.json"
        ),
        thermal_properties_lookup_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "Test_Lookup.csv"
        ),
    )

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.TuneMaterial.return_value = Operation(name="id")
    mock_connection.return_value = mock_connection_with_stub

    # act
    additive = Additive()
    task = additive.tune_material_async(input, out_dir=tmp_path / "tune_material")

    # assert
    assert isinstance(task, SimulationTask)
    assert task._long_running_op.name == "id"
    assert task._long_running_op.done == False
    mock_connection_with_stub.materials_stub.TuneMaterial.assert_called_once()


# TODO (deleon): Add exceptions to material tuning
# @patch("ansys.additive.core.additive.ServerConnection")
# def test_tune_material_raises_exception_for_progress_error(mock_connection, tmp_path: pathlib.Path):
#     # arrange
#     input = MaterialTuningInput(
#         id="id",
#         experiment_data_file=test_utils.get_test_file_path(
#             pathlib.Path("Material") / "experimental_data.csv"
#         ),
#         material_configuration_file=test_utils.get_test_file_path(
#             pathlib.Path("Material") / "material-data.json"
#         ),
#         thermal_properties_lookup_file=test_utils.get_test_file_path(
#             pathlib.Path("Material") / "Test_Lookup.csv"
#         ),
#     )
#     message = "error message"
#     response = TuneMaterialResponse(
#         id="id", progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_ERROR, message=message)
#     )

#     def iterable_response(_):
#         yield response

#     mock_connection_with_stub = Mock()
#     mock_connection_with_stub.materials_stub.TuneMaterial.side_effect = iterable_response
#     mock_connection.return_value = mock_connection_with_stub
#     additive = Additive()

#     # act, assert
#     with pytest.raises(Exception, match=message):
#         additive.tune_material(input, out_dir=tmp_path / "progress_error")

# TODO (deleon): Add progress filtering to material tuning
# @pytest.mark.parametrize(
#     "text, expected",
#     [
#         ("License successfully, should not be printed", False),
#         ("Starting ThermalSolver, should not be printed", False),
#         ("threads for solver, should not be printed", False),
#         ("this should be logged", True),
#     ],
# )
# @patch("ansys.additive.core.additive.ServerConnection")
# def test_tune_material_filters_progress_messages(
#     mock_connection,
#     caplog,
#     tmp_path: pathlib.Path,
#     text: str,
#     expected: bool,
# ):
#     # arrange
#     input = MaterialTuningInput(
#         id="id",
#         experiment_data_file=test_utils.get_test_file_path(
#             pathlib.Path("Material") / "experimental_data.csv"
#         ),
#         material_configuration_file=test_utils.get_test_file_path(
#             pathlib.Path("Material") / "material-data.json"
#         ),
#         thermal_properties_lookup_file=test_utils.get_test_file_path(
#             pathlib.Path("Material") / "Test_Lookup.csv"
#         ),
#     )
#     response = TuneMaterialResponse(
#         id="id", progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_EXECUTING, message=text)
#     )

#     caplog.set_level(logging.INFO, logger="PyAdditive_global")

#     def iterable_response(_):
#         yield response

#     mock_connection_with_stub = Mock()
#     mock_connection_with_stub.materials_stub.TuneMaterial.side_effect = iterable_response
#     mock_connection.return_value = mock_connection_with_stub
#     additive = Additive()

#     # act
#     additive.tune_material(input, out_dir=tmp_path / "progress_error")

#     # assert
#     assert (text in caplog.text) == expected


@patch("ansys.additive.core.simulation_task.SimulationTask._update_operation_status")
@patch("ansys.additive.core.additive.Additive.tune_material_async")
@patch("ansys.additive.core.additive.ServerConnection")
def test_tune_material_calls_tune_material_async(
    mock_connection, mock_tune_material_async, _, tmp_path: pathlib.Path
):
    # assemble
    input = MaterialTuningInput(
        experiment_data_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "experimental_data.csv"
        ),
        material_configuration_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "material-data.json"
        ),
        thermal_properties_lookup_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "Test_Lookup.csv"
        ),
    )
    out_dir = tmp_path / "tune_material"
    operation = Operation(done=True)
    metadata = OperationMetadata(
        simulation_id="id",
        percent_complete=50.0,
        message="executing",
        state=ProgressMsgState.PROGRESS_STATE_EXECUTING,
    )
    operation.metadata.Pack(metadata)
    task = SimulationTask(mock_connection, operation, input, out_dir)
    mock_tune_material_async.return_value = task
    additive = Additive()

    # act
    additive.tune_material(input, out_dir=out_dir)

    # assert
    mock_tune_material_async.assert_called_once_with(input, out_dir)


@patch("ansys.additive.core.additive.Additive.tune_material_async")
@patch("ansys.additive.core.additive.ServerConnection")
def test_tune_material_returns_expected_result(
    mock_connection,
    mock_tune_material_async,
    tmp_path: pathlib.Path,
):
    # arrange
    input = MaterialTuningInput(
        experiment_data_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "experimental_data.csv"
        ),
        material_configuration_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "material-data.json"
        ),
        thermal_properties_lookup_file=test_utils.get_test_file_path(
            pathlib.Path("Material") / "Test_Lookup.csv"
        ),
    )
    out_dir = tmp_path / "tune_material"
    log_bytes = b"log_bytes"
    optimized_parameters_bytes = b"optimized_parameters"
    cw_lookup_bytes = b"characteristic width lookup"

    operation_completed = Operation(name="id", done=True)
    metadata = OperationMetadata(
        simulation_id=input.id,
        percent_complete=100.0,
        message="done",
        state=ProgressMsgState.PROGRESS_STATE_COMPLETED,
    )
    operation_completed.metadata.Pack(metadata)
    response = TuneMaterialResponse(
        id=input.id,
        result=MaterialTuningResult(
            log=log_bytes,
            optimized_parameters=optimized_parameters_bytes,
            characteristic_width_lookup=cw_lookup_bytes,
        ),
    )
    operation_completed.response.Pack(response)
    task = SimulationTask(mock_connection, operation_completed, input, out_dir)
    mock_tune_material_async.return_value = task
    mock_connection.operations_stub.WaitOperation.return_value = operation_completed
    mock_connection.operations_stub.GetOperation.return_value = operation_completed
    additive = Additive()

    # act
    summary = additive.tune_material(input, out_dir=out_dir)

    # assert
    assert summary.input == input
    with open(summary.log_file, "r") as f:
        assert log_bytes.decode() in f.read()
    with open(summary.optimized_parameters_file, "r") as f:
        assert optimized_parameters_bytes.decode() in f.read()
    with open(summary.characteristic_width_file, "r") as f:
        assert cw_lookup_bytes.decode() in f.read()


@patch("ansys.additive.core.additive.ServerConnection")
def test_Additive_init_assigns_enable_beta_features(_):
    # arrange
    # act
    additive_default = Additive()
    additive = Additive(enable_beta_features=True)

    # assert
    assert additive_default.enable_beta_features is False
    assert additive.enable_beta_features is True


@patch("ansys.additive.core.additive.ServerConnection")
def test_enable_beta_features_setter_assigns_value(_):
    # arrange
    additive = Additive()
    assert additive.enable_beta_features is False

    # act
    additive.enable_beta_features = True

    # assert
    assert additive.enable_beta_features is True


@patch("ansys.additive.core.additive.ServerConnection")
def test_3d_microstructure_without_beta_enabled_raises_exception(_):
    # arrange
    additive = Additive()
    input = Microstructure3DInput(material=AdditiveMaterial(name="my_material"))

    # act, assert
    with pytest.raises(BetaFeatureNotEnabledError):
        additive.simulate(input)


@patch("ansys.additive.core.additive.download_logs")
@patch("ansys.additive.core.additive.ServerConnection")
def test_download_server_logs_calls_download_logs(
    mock_connection, mock_download_logs, tmp_path: pathlib.Path
):
    # arrange
    mock_server = Mock(ServerConnection)
    mock_server.channel_str = "1.1.1.1:50052"
    mock_connection.return_value = mock_server
    mock_download_logs.return_value = "additive-server-logs.zip"
    additive = Additive()
    out_dir = tmp_path / "logs"

    # act
    log_file = additive.download_server_logs(out_dir)

    # assert
    mock_download_logs.assert_called_once_with(mock_server.simulation_stub, out_dir)
    assert log_file == "additive-server-logs.zip"
