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
from ansys.api.additive.v0.additive_domain_pb2 import MeltPool as MeltPoolMsg
from ansys.api.additive.v0.additive_domain_pb2 import Progress as ProgressMsg
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState as ProgressMsgState
from ansys.api.additive.v0.additive_domain_pb2 import ThermalHistoryResult
from ansys.api.additive.v0.additive_materials_pb2 import (
    GetMaterialRequest,
    GetMaterialsListResponse,
    TuneMaterialResponse,
)
from ansys.api.additive.v0.additive_simulation_pb2 import (
    SimulationResponse,
    UploadFileRequest,
    UploadFileResponse,
)
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
    SingleBeadInput,
    SingleBeadSummary,
    StlFile,
    ThermalHistoryInput,
    __version__,
)
import ansys.additive.core.additive
from ansys.additive.core.exceptions import BetaFeatureNotEnabledError
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.material_tuning import MaterialTuningInput
from ansys.additive.core.progress_handler import DefaultSingleSimulationProgressHandler
from ansys.additive.core.server_connection import DEFAULT_PRODUCT_VERSION, ServerConnection
import ansys.additive.core.server_connection.server_connection

from . import test_utils


@pytest.mark.parametrize(
    "in_prod_version, expected_prod_version",
    [
        (None, DEFAULT_PRODUCT_VERSION),
        ("123", "123"),
        ("", DEFAULT_PRODUCT_VERSION),
    ],
)
def test_Additive_init_calls_connect_to_servers_correctly(
    monkeypatch: pytest.MonkeyPatch, in_prod_version, expected_prod_version
):
    # arrange
    server_connections = ["connection1", "connection2"]
    host = "hostname"
    port = 12345
    nservers = 3

    mock_server_connections = [Mock(ServerConnection)]
    mock_connect = create_autospec(
        ansys.additive.core.additive.Additive._connect_to_servers,
        return_value=mock_server_connections,
    )
    monkeypatch.setattr(ansys.additive.core.additive.Additive, "_connect_to_servers", mock_connect)

    # act
    additive = Additive(
        server_connections,
        host,
        port,
        nservers=nservers,
        product_version=in_prod_version,
        linux_install_path=None,
    )

    # assert
    mock_connect.assert_called_with(
        server_connections, host, port, nservers, expected_prod_version, ANY, None
    )
    assert additive._servers == mock_server_connections
    assert isinstance(additive._log, logging.Logger)
    assert additive._user_data_path == USER_DATA_PATH


@patch("ansys.additive.core.additive.ServerConnection")
def test_Additive_init_assigns_nsims_per_servers(_):
    # arrange
    nsims_per_server = 99

    # act
    additive_default = Additive()
    additive = Additive(nsims_per_server=nsims_per_server)

    # assert
    assert additive_default.nsims_per_server == 1
    assert additive.nsims_per_server == nsims_per_server


@patch("ansys.additive.core.additive.ServerConnection")
def test_nsims_per_servers_setter_raises_exception_for_invalid_value(_):
    # arrange
    nsims_per_server = -1
    additive = Additive()

    # act, assert
    with pytest.raises(ValueError, match="must be greater than zero"):
        additive.nsims_per_server = nsims_per_server


@patch("ansys.additive.core.additive.ServerConnection")
def test_nsims_per_servers_setter_correctly_assigns_valid_value(_):
    # arrange
    nsims_per_server = 99
    additive = Additive()

    # act
    additive.nsims_per_server = nsims_per_server

    # assert
    assert additive._nsims_per_server == nsims_per_server


@patch("ansys.additive.core.additive.ServerConnection")
def test_connect_to_servers_with_server_connections_creates_server_connections(mock_connection):
    # arrange
    mock_connection.return_value = Mock(ServerConnection)
    host1 = "localhost:1234"
    host2 = "localhost:5678"
    channel = grpc.insecure_channel("target")
    connections = [host1, channel, host2]
    log = logging.Logger("testlogger")

    # act
    servers = Additive._connect_to_servers(
        server_connections=connections,
        host=host1,
        port=99999,
        nservers=92,
        log=log,
    )

    # assert
    assert len(servers) == len(connections)
    assert len(mock_connection.mock_calls) == 3
    mock_connection.assert_has_calls(
        [call(addr=host1, log=log), call(channel=channel, log=log), call(addr=host2, log=log)]
    )


@patch("ansys.additive.core.additive.ServerConnection")
def test_connect_to_servers_with_host_creates_server_connection(mock_connection):
    # arrange
    mock_connection.return_value = Mock(ServerConnection)
    host = "127.0.0.1"
    port = 9999
    log = logging.Logger("testlogger")

    # act
    servers = Additive._connect_to_servers(
        server_connections=None, host=host, port=port, nservers=99, log=log
    )

    # assert
    assert len(servers) == 1
    mock_connection.assert_called_once_with(addr=f"{host}:{port}", log=log)


@patch("ansys.additive.core.additive.ServerConnection")
def test_connect_to_servers_with_env_var_creates_server_connection(
    mock_connection, monkeypatch: pytest.MonkeyPatch
):
    # arrange
    addr = "localhost:1234"
    monkeypatch.setenv("ANSYS_ADDITIVE_ADDRESS", addr)
    mock_connection.return_value = Mock(ServerConnection)
    log = logging.Logger("testlogger")

    # act
    servers = Additive._connect_to_servers(server_connections=None, host=None, nservers=99, log=log)

    # assert
    assert len(servers) == 1
    mock_connection.assert_called_once_with(addr=addr, log=log)


@patch("ansys.additive.core.additive.ServerConnection")
def test_connect_to_servers_with_nservers_creates_server_connections(mock_connection):
    # arrange
    nservers = 99
    product_version = "123"
    mock_connection.return_value = Mock(ServerConnection)
    log = logging.Logger("testlogger")

    # act
    servers = Additive._connect_to_servers(
        server_connections=None,
        host=None,
        nservers=nservers,
        product_version=product_version,
        log=log,
    )

    # assert
    assert len(servers) == nservers
    mock_connection.assert_called_with(
        product_version=product_version, log=log, linux_install_path=None
    )


def test_create_logger_raises_exception_for_invalid_log_level():
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid log level"):
        Additive._create_logger(None, "Tragic")


def test_create_logger_creates_expected_logger(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture
):
    # arrange
    log_file = tmp_path / "test.log"
    message = "log message"

    # act
    log = Additive._create_logger(log_file, "INFO")
    with caplog.at_level(logging.INFO, logger="ansys.additive.core.additive"):
        log.info(message)
    # assert
    assert isinstance(log, logging.Logger)
    assert message in caplog.text
    assert hasattr(log, "file_handler")
    assert log_file.exists()
    with open(log_file, "r") as fid:
        text = "".join(fid.readlines())
    assert message in text


def test_about_prints_not_connected_message(capsys: pytest.CaptureFixture[str]):
    # arrange
    mock_additive = MagicMock()
    mock_additive.about = Additive.about
    mock_additive._servers = None

    # act
    mock_additive.about(mock_additive)

    # assert
    out_str = capsys.readouterr().out
    assert f"Client {__version__}, API version: {api_version}" in out_str
    assert "Client is not connected to a server." in out_str


def test_about_prints_server_status_messages(capsys: pytest.CaptureFixture[str]):
    # arrange
    mock_additive = MagicMock()
    mock_additive.about = Additive.about
    servers = []
    for i in range(5):
        servers.append(Mock(ServerConnection))
        servers[i].status.return_value = f"server {i} running"
    mock_additive._servers = servers

    # act
    mock_additive.about(mock_additive)

    # assert
    out_str = capsys.readouterr().out
    assert f"Client {__version__}, API version: {api_version}" in out_str
    for i in range(len(servers)):
        assert f"server {i} running" in out_str


@pytest.mark.parametrize(
    "input",
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
def test_simulate_with_single_input_calls_internal_simulate_once(_, input):
    # arrange
    input.material = test_utils.get_test_material()
    expected_summary = test_utils.get_test_SingleBeadSummary()
    with patch("ansys.additive.core.additive.Additive._simulate") as _simulate_patch:
        _simulate_patch.return_value = expected_summary
    additive = Additive(enable_beta_features=True)
    additive._simulate = _simulate_patch

    # act
    summary = additive.simulate(input)

    # assert
    assert isinstance(summary, SingleBeadSummary)
    assert summary == expected_summary
    _simulate_patch.assert_called_once_with(input, ANY, ANY)
    assert isinstance(_simulate_patch.call_args[0][2], DefaultSingleSimulationProgressHandler)


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
def test_simulate_prints_error_message_when_SimulationError_returned(_, caplog):
    # arrange
    input = SingleBeadInput(material=test_utils.get_test_material())
    error_msg = "error message"
    simulation_error = SimulationError(input, error_msg)
    with patch("ansys.additive.core.additive.Additive._simulate") as _simulate_patch:
        _simulate_patch.return_value = simulation_error
    additive = Additive()
    additive._simulate = _simulate_patch
    caplog.set_level(logging.ERROR, "PyAdditive_global")

    # act
    summaries = additive.simulate([input])

    # assert
    assert isinstance(summaries[0], SimulationError)
    assert error_msg in caplog.text
    _simulate_patch.assert_called_once_with(input=input, server=ANY, progress_handler=None)


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_with_input_list_calls_internal_simulate_n_times(_):
    # arrange
    with patch("ansys.additive.core.additive.Additive._simulate") as _simulate_patch:
        _simulate_patch.return_value = None
    additive = Additive(enable_beta_features=True)
    additive._simulate = _simulate_patch
    inputs = [
        SingleBeadInput(id="id1"),
        PorosityInput(id="id2"),
        MicrostructureInput(id="id3"),
        ThermalHistoryInput(id="id4"),
        Microstructure3DInput(id="id5"),
    ]
    # act
    additive.simulate(inputs)

    # assert
    assert _simulate_patch.call_count == len(inputs)
    print(_simulate_patch.call_args_list)
    calls = [call(input=i, server=ANY, progress_handler=None) for i in inputs]
    _simulate_patch.assert_has_calls(calls, any_order=True)


@pytest.mark.parametrize(
    "inputs, nservers, nsims_per_server, expected_n_threads",
    [
        (
            [
                SingleBeadInput(id="id1"),
                PorosityInput(id="id2"),
                MicrostructureInput(id="id3"),
                ThermalHistoryInput(id="id4"),
                SingleBeadInput(id="id5"),
            ],
            2,
            2,
            4,
        ),
        (
            [
                SingleBeadInput(id="id1"),
                PorosityInput(id="id2"),
                MicrostructureInput(id="id3"),
                ThermalHistoryInput(id="id4"),
            ],
            3,
            2,
            4,
        ),
    ],
)
@patch("ansys.additive.core.additive.ServerConnection")
@patch("concurrent.futures.ThreadPoolExecutor")
def test_simulate_with_n_servers_m_sims_per_server_uses_n_x_m_threads(
    mock_executor, mock_connection, inputs, nservers, nsims_per_server, expected_n_threads
):
    # arrange
    mock_connection.return_value = Mock(ServerConnection)

    def raise_exception(_):
        raise Exception("exception")

    # mock_executor.return_value = concurrent.futures.ThreadPoolExecutor()
    mock_executor.side_effect = raise_exception
    additive = Additive(nservers=nservers, nsims_per_server=nsims_per_server)

    # act
    try:
        additive.simulate(inputs)
    except Exception:
        pass

    # assert
    assert mock_connection.call_count == nservers
    mock_executor.assert_called_once_with(expected_n_threads)


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_with_duplicate_simulation_ids_raises_exception(_):
    # arrange
    with patch("ansys.additive.core.additive.Additive._simulate") as _simulate_patch:
        _simulate_patch.return_value = None
    additive = Additive()
    additive._simulate = _simulate_patch
    inputs = [
        x
        for x in [
            SingleBeadInput(id="id"),
            PorosityInput(id="id"),
        ]
    ]
    # act, assert
    with pytest.raises(ValueError, match="Duplicate simulation ID"):
        additive.simulate(inputs)


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_internal_simulate_with_thermal_history_without_geometry_returns_SimulationError(
    _,
):
    # arrange
    input = ThermalHistoryInput()
    input.material = test_utils.get_test_material()
    additive = Additive()

    # act
    result = additive._simulate(input, None)

    # assert
    assert isinstance(result, SimulationError)
    assert "The geometry path is not defined in the simulation input" in result.message


@pytest.mark.parametrize(
    "input,result,summary_type",
    [
        (SingleBeadInput(), MeltPoolMsg(), SingleBeadSummary),
        (PorosityInput(), PorosityResult(), PorositySummary),
        (MicrostructureInput(), MicrostructureResult(), MicrostructureSummary),
        (Microstructure3DInput(), Microstructure3DResult(), Microstructure3DSummary),
    ],
)  # patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_internal_simulate_returns_correct_summary(
    _,
    input,
    result,
    summary_type,
):
    # arrange
    input.material = test_utils.get_test_material()
    progress_msg = ProgressMsg(
        state=ProgressMsgState.PROGRESS_STATE_COMPLETED,
        percent_complete=100,
        message="running",
        context="simulation",
    )
    if isinstance(result, MeltPoolMsg):
        sim_response = SimulationResponse(id="id", progress=progress_msg, melt_pool=result)
    elif isinstance(result, PorosityResult):
        sim_response = SimulationResponse(id="id", progress=progress_msg, porosity_result=result)
    elif isinstance(result, MicrostructureResult):
        sim_response = SimulationResponse(
            id="id", progress=progress_msg, microstructure_result=result
        )
    elif isinstance(result, Microstructure3DResult):
        sim_response = SimulationResponse(
            id="id", progress=progress_msg, microstructure_3d_result=result
        )
    else:
        assert False, "Invalid result type"

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.Simulate.return_value = [sim_response]
    additive = Additive(enable_beta_features=True)

    # act
    summary = additive._simulate(input, mock_connection_with_stub)

    # assert
    assert isinstance(summary, summary_type)


@pytest.mark.parametrize(
    "input",
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
def test_internal_simulate_without_material_raises_exception(_, input):
    # arrange
    additive = Additive(enable_beta_features=True)

    # act, assert
    with pytest.raises(ValueError, match="A material is not assigned to the simulation input"):
        additive._simulate(input, None)


@pytest.mark.parametrize(
    "input",
    [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
        Microstructure3DInput(),
    ],
)
# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_exception_during_interal_simulation_returns_SimulationError(_, input):
    # arrange
    error_msg = "simulation error"
    progress_msg = ProgressMsg(
        state=ProgressMsgState.PROGRESS_STATE_EXECUTING,
        percent_complete=50,
        message="running",
        context="simulation",
    )
    sim_response = SimulationResponse(id="id", progress=progress_msg)

    def iterable_with_exception(_):
        yield sim_response
        raise Exception(error_msg)

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.Simulate.side_effect = iterable_with_exception
    input.material = test_utils.get_test_material()
    additive = Additive(enable_beta_features=True)

    # act
    result = additive._simulate(input, mock_connection_with_stub)

    # assert
    assert isinstance(result, SimulationError)
    assert error_msg in result.message


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_server_error_during_interal_simulation_returns_SimulationError(_):
    # arrange
    error_msg = "simulation error"
    progress_msg = ProgressMsg(
        state=ProgressMsgState.PROGRESS_STATE_ERROR,
        percent_complete=50,
        message=error_msg,
        context="simulation",
    )
    sim_response = SimulationResponse(id="id", progress=progress_msg)
    input = SingleBeadInput(material=test_utils.get_test_material())

    def iterable_response(_):
        yield sim_response

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.Simulate.side_effect = iterable_response
    additive = Additive()

    # act
    result = additive._simulate(input, mock_connection_with_stub)

    # assert
    assert isinstance(result, SimulationError)
    assert error_msg in result.message


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
    assert material.poisson_ratio == 23
    assert len(material.characteristic_width_data) == 64
    assert len(material.thermal_properties_data) == 7500


@patch("ansys.additive.core.additive.ServerConnection")
def test_tune_material_raises_exception_if_output_path_exists(_, tmp_path: pathlib.Path):
    # arrange
    input = MaterialTuningInput(
        id="id",
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
        additive.tune_material(input, out_dir=tmp_path)


@patch("ansys.additive.core.additive.ServerConnection")
def test_tune_material_raises_exception_for_progress_error(mock_connection, tmp_path: pathlib.Path):
    # arrange
    input = MaterialTuningInput(
        id="id",
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
    message = "error message"
    response = TuneMaterialResponse(
        id="id", progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_ERROR, message=message)
    )

    def iterable_response(_):
        yield response

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.TuneMaterial.side_effect = iterable_response
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act, assert
    with pytest.raises(Exception, match=message):
        additive.tune_material(input, out_dir=tmp_path / "progress_error")


@pytest.mark.parametrize(
    "text, expected",
    [
        ("License successfully, should not be printed", False),
        ("Starting ThermalSolver, should not be printed", False),
        ("threads for solver, should not be printed", False),
        ("this should be logged", True),
    ],
)
@patch("ansys.additive.core.additive.ServerConnection")
def test_tune_material_filters_progress_messages(
    mock_connection,
    caplog,
    tmp_path: pathlib.Path,
    text: str,
    expected: bool,
):
    # arrange
    input = MaterialTuningInput(
        id="id",
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
    response = TuneMaterialResponse(
        id="id", progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_EXECUTING, message=text)
    )

    caplog.set_level(logging.INFO, logger="PyAdditive_global")

    def iterable_response(_):
        yield response

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.TuneMaterial.side_effect = iterable_response
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act
    additive.tune_material(input, out_dir=tmp_path / "progress_error")

    # assert
    assert (text in caplog.text) == expected


@patch("ansys.additive.core.additive.ServerConnection")
def test_tune_material_returns_expected_result(
    mock_connection,
    tmp_path: pathlib.Path,
):
    # arrange
    input = MaterialTuningInput(
        id="id",
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
    log_bytes = b"log_bytes"
    optimized_parameters_bytes = b"optimized_parameters"
    cw_lookup_bytes = b"characteristic width lookup"
    response = TuneMaterialResponse(
        id="id",
        result=MaterialTuningResult(
            log=log_bytes,
            optimized_parameters=optimized_parameters_bytes,
            characteristic_width_lookup=cw_lookup_bytes,
        ),
    )

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.materials_stub.TuneMaterial.return_value = [response]
    mock_connection.return_value = mock_connection_with_stub
    additive = Additive()

    # act
    summary = additive.tune_material(input, out_dir=tmp_path / "nominal_path")

    # assert
    assert summary.input == input
    with open(summary.log_file, "r") as f:
        assert log_bytes.decode() in f.read()
    with open(summary.optimized_parameters_file, "r") as f:
        assert optimized_parameters_bytes.decode() in f.read()
    with open(summary.characteristic_width_file, "r") as f:
        assert cw_lookup_bytes.decode() in f.read()


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_file_upload_reader_returns_expected_number_of_requests(_):
    # arrange
    file_size = os.path.getsize(__file__)
    expected_iterations = 10
    chunk_size = int(file_size / expected_iterations)
    if file_size % expected_iterations > 0:
        expected_iterations += 1
    short_name = os.path.basename(__file__)
    additive = Additive()

    # act
    for n, request in enumerate(
        additive._Additive__file_upload_reader(os.path.abspath(__file__), chunk_size)
    ):
        assert isinstance(request, UploadFileRequest)
        assert request.name == short_name
        assert request.total_size == file_size
        assert len(request.content) <= chunk_size
        assert request.content_md5 == hashlib.md5(request.content).hexdigest()
    assert n + 1 == expected_iterations


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_thermal_history_without_geometry_raises_exception(
    _,
):
    # arrange
    input = ThermalHistoryInput()
    additive = Additive()

    # act, assert
    with pytest.raises(
        ValueError, match="The geometry path is not defined in the simulation input"
    ):
        additive._simulate_thermal_history(input, None, None)


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_thermal_history_with_progress_error_during_upload_raises_exception(
    _,
):
    # arrange
    input = ThermalHistoryInput(
        geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))
    )
    message = "error message"
    response = UploadFileResponse(
        remote_file_name="remote/file/name",
        progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_ERROR, message=message),
    )

    def iterable_response(_):
        yield response

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.UploadFile.side_effect = iterable_response
    additive = Additive()

    # act, assert
    with pytest.raises(Exception, match=message):
        additive._simulate_thermal_history(input, None, mock_connection_with_stub)
    mock_connection_with_stub.simulation_stub.UploadFile.assert_called_once()


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
def test_simulate_thermal_history_with_progress_error_during_simulation_raises_exception(
    _,
):
    # arrange
    input = ThermalHistoryInput(
        geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))
    )
    message = "error message"
    remote_file_name = "remote/file/name"
    upload_response = UploadFileResponse(
        remote_file_name=remote_file_name,
        progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_COMPLETED, message="done"),
    )
    simulation_request = input._to_simulation_request(remote_geometry_path=remote_file_name)
    error_response_with_warn = SimulationResponse(
        id="ignored-warning",
        progress=ProgressMsg(
            state=ProgressMsgState.PROGRESS_STATE_ERROR, message="WARN warning message"
        ),
    )
    error_response = SimulationResponse(
        id="id",
        progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_ERROR, message=message),
    )

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.UploadFile.return_value = [upload_response]
    # The iterable returned from Simulate first generates a warning then an error
    mock_connection_with_stub.simulation_stub.Simulate.return_value = [
        error_response_with_warn,
        error_response,
    ]
    additive = Additive()

    # act, assert
    with pytest.raises(Exception, match=message):
        additive._simulate_thermal_history(input, None, mock_connection_with_stub)
    mock_connection_with_stub.simulation_stub.UploadFile.assert_called_once()
    # The Simulate method is called once and returns an iterator for the two responses above
    mock_connection_with_stub.simulation_stub.Simulate.assert_called_once_with(simulation_request)


# patch needed for Additive() call
@patch("ansys.additive.core.additive.ServerConnection")
@patch("ansys.additive.core.additive.download_file")
def test_simulate_thermal_history_returns_expected_summary(
    mock_download_file, _, tmp_path: pathlib.Path
):
    # arrange
    results_file = tmp_path / "results.zip"
    out_dir = tmp_path / "out_dir"
    shutil.copyfile(test_utils.get_test_file_path("thermal_history_results.zip"), str(results_file))
    mock_download_file.side_effect = lambda a, b, c: str(results_file)

    id = "thermal-history-test"
    input = ThermalHistoryInput(
        id=id, geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))
    )
    remote_file_name = "remote/file/name"
    upload_response = UploadFileResponse(
        remote_file_name=remote_file_name,
        progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_COMPLETED, message="done"),
    )
    simulation_request = input._to_simulation_request(remote_geometry_path=remote_file_name)
    simulation_response = SimulationResponse(
        id=id, thermal_history_result=ThermalHistoryResult(coax_ave_zip_file="zip-file")
    )

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.UploadFile.return_value = [upload_response]
    mock_connection_with_stub.simulation_stub.Simulate.return_value = [simulation_response]
    additive = Additive()

    # act
    summary = additive._simulate_thermal_history(input, str(out_dir), mock_connection_with_stub)

    # assert
    mock_connection_with_stub.simulation_stub.UploadFile.assert_called_once()
    mock_connection_with_stub.simulation_stub.Simulate.assert_called_once_with(simulation_request)
    assert summary.input == input
    assert summary.coax_ave_output_folder == str(out_dir / id / "coax_ave_output")
    assert len(list(pathlib.Path(summary.coax_ave_output_folder).glob("*.vtk"))) == 6


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
