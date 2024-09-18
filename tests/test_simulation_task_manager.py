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

from unittest.mock import Mock, PropertyMock

from ansys.additive.core.progress_handler import Progress, ProgressState
from ansys.additive.core.simulation_task_manager import SimulationTask, SimulationTaskManager


def test_add_task_stores_task():
    # arrange
    mock_task = Mock(SimulationTask)
    taskMgr = SimulationTaskManager()

    # act
    taskMgr.add_task(mock_task)

    # assert
    assert len(taskMgr._tasks) == 1


def test_status_return_list_of_tuples_of_id_and_Progress():
    # arrange
    progress1 = Progress(
        sim_id="id1",
        message="simulation completed",
        state=ProgressState.COMPLETED,
        percent_complete=100,
        context="context",
    )
    mock_task1 = Mock(SimulationTask)
    mock_task1.status.return_value = progress1

    progress2 = Progress(
        sim_id="id2",
        message="simulation canceled",
        state=ProgressState.CANCELLED,
        percent_complete=33,
        context="context",
    )
    mock_task2 = Mock(SimulationTask)
    mock_task2.status.return_value = progress2

    taskMgr = SimulationTaskManager()
    taskMgr.add_task(mock_task1)
    taskMgr.add_task(mock_task2)

    # act
    result = taskMgr.status()

    # arrange
    assert len(result) == 2
    assert result[0] == (progress1.sim_id, progress1)
    assert result[1] == (progress2.sim_id, progress2)


def test_wait_all_calls_each_task_wait():
    # arrange
    mock_task1 = Mock(SimulationTask)
    mock_task2 = Mock(SimulationTask)

    taskMgr = SimulationTaskManager()
    taskMgr.add_task(mock_task1)
    taskMgr.add_task(mock_task2)

    # act
    taskMgr.wait_all()

    # assert
    mock_task1.wait.assert_called_once()
    mock_task2.wait.assert_called_once()


def test_cancel_all_calls_each_task_cancel():
    # arrange
    mock_task1 = Mock(SimulationTask)
    mock_task2 = Mock(SimulationTask)

    taskMgr = SimulationTaskManager()
    taskMgr.add_task(mock_task1)
    taskMgr.add_task(mock_task2)

    # act
    taskMgr.cancel_all()

    # assert
    mock_task1.cancel.assert_called_once()
    mock_task2.cancel.assert_called_once()


def test_simulation_ids():
    # arrange
    mock_task1 = Mock(SimulationTask)
    mock_task2 = Mock(SimulationTask)
    type(mock_task1).simulation_id = PropertyMock(return_value="sim1")
    type(mock_task2).simulation_id = PropertyMock(return_value="sim2")

    taskMgr = SimulationTaskManager()
    taskMgr.add_task(mock_task1)
    taskMgr.add_task(mock_task2)

    # act
    sim_ids = taskMgr.simulation_ids

    # assert
    assert sim_ids == ["sim1", "sim2"]
