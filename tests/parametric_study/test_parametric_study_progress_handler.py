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

import math
import pathlib
from unittest.mock import Mock

from ansys.api.additive.v0.additive_domain_pb2 import (
    GrainStatistics,
    MicrostructureResult,
    PorosityResult,
)
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationResponse
from google.longrunning.operations_pb2 import Operation
import pytest

from ansys.additive.core import Additive
from ansys.additive.core.microstructure import MicrostructureInput
from ansys.additive.core.parametric_study import ParametricStudy
from ansys.additive.core.parametric_study.constants import ColumnNames
from ansys.additive.core.parametric_study.parametric_study_progress_handler import (
    ParametricStudyProgressHandler,
)
from ansys.additive.core.porosity import PorosityInput
from ansys.additive.core.progress_handler import Progress, ProgressState
from ansys.additive.core.server_connection.server_connection import ServerConnection
from ansys.additive.core.simulation import SimulationStatus
from ansys.additive.core.single_bead import SingleBeadInput
from tests import test_utils


def test_init_correctly_initializes(tmp_path: pathlib.Path):
    # arrange
    additive = Mock(Additive)
    study = ParametricStudy(tmp_path / "test_study")

    # act
    handler = ParametricStudyProgressHandler(study, additive)

    # assert
    handler._study == study
    handler._additive == additive
    handler._study_lock is not None
    handler._last_progress_states == {}


@pytest.mark.parametrize(
    "status",
    [
        ProgressState.WAITING,
        ProgressState.CANCELLED,
        ProgressState.RUNNING,
        ProgressState.WARNING,
    ],
)
def test_update_updates_simulation_status_correctly_when_not_completed(
    tmp_path: pathlib.Path, status: ProgressState
):
    # arrange
    additive = Mock(Additive)
    study = ParametricStudy(tmp_path / "test_study")
    sb = SingleBeadInput()
    study.add_inputs([sb])
    handler = ParametricStudyProgressHandler(study, additive)
    progress = Progress(
        sim_id=sb.id,
        state=status,
        percent_complete=50,
        message="test message",
        context="test context",
    )
    if status == ProgressState.WAITING:
        expectedStatus = SimulationStatus.PENDING
    elif status == ProgressState.CANCELLED:
        expectedStatus = SimulationStatus.CANCELLED
    elif status == ProgressState.RUNNING:
        expectedStatus = SimulationStatus.RUNNING
    elif status == ProgressState.WARNING:
        expectedStatus = SimulationStatus.WARNING
    elif status == ProgressState.ERROR:
        expectedStatus = SimulationStatus.ERROR

    # act
    handler.update(progress)

    # assert
    assert study.data_frame().iloc[0][ColumnNames.STATUS] == expectedStatus
    if status != ProgressState.ERROR:
        assert study.data_frame().isnull().iloc[0][ColumnNames.ERROR_MESSAGE]
    else:
        assert study.data_frame().iloc[0][ColumnNames.ERROR_MESSAGE] == "test message"


def test_update_updates_completed_single_bead_simulation(tmp_path: pathlib.Path):
    # arrange
    additive = Mock(Additive)
    study = ParametricStudy(tmp_path / "test_study")
    input = SingleBeadInput()
    study.add_inputs([input])
    handler = ParametricStudyProgressHandler(study, additive)
    progress = Progress(
        sim_id=input.id,
        state=ProgressState.COMPLETED,
        percent_complete=100,
        message="done",
        context="test context",
    )
    response = SimulationResponse(id=input.id, melt_pool=test_utils.get_test_melt_pool_message())
    operation = Operation(name=input.id, done=True)
    operation.response.Pack(response)
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.operations_stub.GetOperation.return_value = operation
    additive._servers = [mock_server_connection]

    # act
    handler.update(progress)

    # assert
    s = study.data_frame().iloc[0]
    assert s[ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert s[ColumnNames.MELT_POOL_LENGTH] == 3
    assert s[ColumnNames.MELT_POOL_WIDTH] == 4
    assert s[ColumnNames.MELT_POOL_DEPTH] == 6
    assert s[ColumnNames.MELT_POOL_REFERENCE_WIDTH] == 5
    assert s[ColumnNames.MELT_POOL_REFERENCE_DEPTH] == 7
    assert s[ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] == 7 / 5
    assert s[ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH] == 3 / 4


def test_update_updates_completed_porosity_simulation(tmp_path: pathlib.Path):
    # arrange
    additive = Mock(Additive)
    study = ParametricStudy(tmp_path / "test_study")
    input = PorosityInput()
    study.add_inputs([input])
    handler = ParametricStudyProgressHandler(study, additive)
    progress = Progress(
        sim_id=input.id,
        state=ProgressState.COMPLETED,
        percent_complete=100,
        message="done",
        context="test context",
    )
    response = SimulationResponse(
        id=input.id,
        porosity_result=PorosityResult(void_ratio=1, powder_ratio=2, solid_ratio=3),
    )
    operation = Operation(name=input.id, done=True)
    operation.response.Pack(response)
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.operations_stub.GetOperation.return_value = operation
    additive._servers = [mock_server_connection]

    # act
    handler.update(progress)

    # assert
    s = study.data_frame().iloc[0]
    assert s[ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert s[ColumnNames.RELATIVE_DENSITY] == 3


def test_update_updates_completed_microstructure_simulation(tmp_path: pathlib.Path):
    # arrange
    additive = Mock(Additive)
    study = ParametricStudy(tmp_path / "test_study")
    input = MicrostructureInput()
    study.add_inputs([input])
    handler = ParametricStudyProgressHandler(study, additive)
    progress = Progress(
        sim_id=input.id,
        state=ProgressState.COMPLETED,
        percent_complete=100,
        message="done",
        context="test context",
    )
    xy_vtk_bytes = bytes(range(3))
    xz_vtk_bytes = bytes(range(4, 6))
    yz_vtk_bytes = bytes(range(7, 9))
    xy_stats = GrainStatistics(grain_number=1, area_fraction=2, diameter_um=3, orientation_angle=4)
    xz_stats = GrainStatistics(grain_number=5, area_fraction=6, diameter_um=7, orientation_angle=8)
    yz_stats = GrainStatistics(
        grain_number=9, area_fraction=10, diameter_um=11, orientation_angle=12
    )
    result = MicrostructureResult(xy_vtk=xy_vtk_bytes, xz_vtk=xz_vtk_bytes, yz_vtk=yz_vtk_bytes)
    result.xy_circle_equivalence.append(xy_stats)
    result.xz_circle_equivalence.append(xz_stats)
    result.yz_circle_equivalence.append(yz_stats)
    response = SimulationResponse(id=input.id, microstructure_result=result)
    operation = Operation(name=input.id, done=True)
    operation.response.Pack(response)
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.operations_stub.GetOperation.return_value = operation
    additive._servers = [mock_server_connection]

    # act
    handler.update(progress)

    # assert
    s = study.data_frame().iloc[0]
    assert s[ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert not math.isnan(s[ColumnNames.XY_AVERAGE_GRAIN_SIZE])
    assert not math.isnan(s[ColumnNames.XZ_AVERAGE_GRAIN_SIZE])
    assert not math.isnan(s[ColumnNames.YZ_AVERAGE_GRAIN_SIZE])
