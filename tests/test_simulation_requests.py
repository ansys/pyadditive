# Copyright (C) 2022 - 2026 ANSYS, Inc. and/or its affiliates.
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
import os
from unittest.mock import Mock, patch

import pytest

from ansys.additive.core import (
    Microstructure3DInput,
    MicrostructureInput,
    PorosityInput,
    SingleBeadInput,
    StlFile,
    ThermalHistoryInput,
)
from ansys.additive.core.simulation_requests import (
    __file_upload_reader,
    create_request,
    _setup_thermal_history,
)
from ansys.api.additive.v0.additive_domain_pb2 import Progress as ProgressMsg
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState as ProgressMsgState
from ansys.api.additive.v0.additive_simulation_pb2 import (
    UploadFileRequest,
    UploadFileResponse,
)

from . import test_utils


@pytest.mark.parametrize(
    "sim_input",
    [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
        ThermalHistoryInput(geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))),
        Microstructure3DInput(),
    ],
)
def testcreate_request_returns_correct_request(sim_input):
    # arrange
    sim_input._id = "id"

    remote_file_name = "remote/file/name"
    upload_response = UploadFileResponse(
        remote_file_name=remote_file_name,
        progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_COMPLETED, message="done"),
    )
    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.UploadFile.return_value = [upload_response]

    # act
    request = create_request(sim_input, mock_connection_with_stub)

    # assert
    assert request.id == sim_input.id
    if isinstance(sim_input, SingleBeadInput):
        assert not mock_connection_with_stub.simulation_stub.UploadFile.called
        assert request.HasField("single_bead_input")
    if isinstance(sim_input, PorosityInput):
        assert not mock_connection_with_stub.simulation_stub.UploadFile.called
        assert request.HasField("porosity_input")
    if isinstance(sim_input, MicrostructureInput):
        assert not mock_connection_with_stub.simulation_stub.UploadFile.called
        assert request.HasField("microstructure_input")
    if isinstance(sim_input, Microstructure3DInput):
        assert not mock_connection_with_stub.simulation_stub.UploadFile.called
        assert request.HasField("microstructure_3d_input")
    if isinstance(sim_input, ThermalHistoryInput):
        mock_connection_with_stub.simulation_stub.UploadFile.assert_called_once()
        assert request.HasField("thermal_history_input")


@patch("ansys.additive.core.additive.ServerConnection")
def test_setup_thermal_history_without_geometry_raises_exception(
    server,
):
    # arrange
    input = ThermalHistoryInput()

    # act, assert
    with pytest.raises(
        ValueError, match="The geometry path is not defined in the simulation input"
    ):
        _setup_thermal_history(input, server)


def test_setup_thermal_history_with_progress_error_during_upload_raises_exception():
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

    # act, assert
    with pytest.raises(Exception, match=message):
        _setup_thermal_history(input, mock_connection_with_stub)
    mock_connection_with_stub.simulation_stub.UploadFile.assert_called_once()


def test_setup_thermal_history_returns_expected_request():
    id = "thermal-history-test"
    sim_input = ThermalHistoryInput(
        geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))
    )
    remote_file_name = "remote/file/name"
    upload_response = UploadFileResponse(
        remote_file_name=remote_file_name,
        progress=ProgressMsg(state=ProgressMsgState.PROGRESS_STATE_COMPLETED, message="done"),
    )
    simulation_request = sim_input._to_simulation_request(remote_geometry_path=remote_file_name)

    mock_connection_with_stub = Mock()
    mock_connection_with_stub.simulation_stub.UploadFile.return_value = [upload_response]

    # act
    request = _setup_thermal_history(sim_input, mock_connection_with_stub)

    # assert
    mock_connection_with_stub.simulation_stub.UploadFile.assert_called_once()
    assert request == simulation_request


def test_file_upload_reader_returns_expected_number_of_requests():
    # arrange
    file_size = os.path.getsize(__file__)
    expected_iterations = 10
    chunk_size = int(file_size / expected_iterations)
    if file_size % expected_iterations > 0:
        expected_iterations += 1
    short_name = os.path.basename(__file__)

    # act
    for n, request in enumerate(__file_upload_reader(os.path.abspath(__file__), chunk_size)):
        assert isinstance(request, UploadFileRequest)
        assert request.name == short_name
        assert request.total_size == file_size
        assert len(request.content) <= chunk_size
        assert request.content_md5 == hashlib.md5(request.content).hexdigest()
    assert n + 1 == expected_iterations
