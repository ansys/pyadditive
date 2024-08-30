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

import pathlib

import pytest

from ansys.additive.core.parametric_study import ParametricStudy
from ansys.additive.core.parametric_study.constants import ColumnNames
from ansys.additive.core.parametric_study.parametric_study_progress_handler import (
    ParametricStudyProgressHandler,
)
from ansys.additive.core.progress_handler import Progress, ProgressState
from ansys.additive.core.simulation import SimulationStatus
from ansys.additive.core.single_bead import SingleBeadInput


def test_init_correctly_initializes(tmp_path: pathlib.Path):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")

    # act
    handler = ParametricStudyProgressHandler(study)

    # assert
    assert handler._study == study
    assert handler._study_lock is not None
    assert handler._last_progress_states == {}


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
    study = ParametricStudy(tmp_path / "test_study", "material")
    sb = SingleBeadInput()
    study.add_inputs([sb])
    handler = ParametricStudyProgressHandler(study)
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
