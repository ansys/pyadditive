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

from unittest.mock import patch

from ansys.api.additive.v0.additive_domain_pb2 import Progress as ProgressMsg
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState as ProgressMsgState

from ansys.additive.core.progress_handler import (
    DefaultSingleSimulationProgressHandler,
    IProgressHandler,
    Progress,
    ProgressState,
)


def test_progress_prints_correctly():
    # arrange
    progress = Progress(
        sim_id="sim_id",
        state=ProgressState.RUNNING,
        percent_complete=50,
        message="message",
        context="context",
    )

    # act
    progress_str = str(progress)

    # assert
    assert "sim_id: RUNNING - 50% - context - message" == progress_str


def test_from_proto_msg_returns_correct_object():
    # arrange
    msg = ProgressMsg(
        state=ProgressMsgState.PROGRESS_STATE_EXECUTING,
        percent_complete=50,
        message="message",
        context="context",
    )

    # act
    progress = Progress.from_proto_msg("sim_id", msg)

    # assert
    assert "sim_id" == progress.sim_id
    assert ProgressState.RUNNING == progress.state
    assert 50 == progress.percent_complete
    assert "message" == progress.message
    assert "context" == progress.context


def test_default_single_simulation_progress_handler_is_instance_of_IProgressHandler():
    # act
    handler = DefaultSingleSimulationProgressHandler()

    # assert
    assert isinstance(handler, IProgressHandler)
    assert not hasattr(handler, "_pbar")
    assert handler._last_context == "Initializing"
    assert handler._last_percent_complete == 0


@patch("ansys.additive.core.progress_handler.tqdm.reset")
@patch("ansys.additive.core.progress_handler.tqdm.set_description")
@patch("ansys.additive.core.progress_handler.tqdm.update")
def test_default_single_simulation_progress_handler_update_updates_percent_complete(
    mock_update, mock_set_description, mock_reset
):
    # arrange
    handler = DefaultSingleSimulationProgressHandler()
    progress = Progress(
        sim_id="sim_id",
        state=ProgressState.RUNNING,
        percent_complete=50,
        message="message",
        context="context",
    )

    updated_progress = Progress(
        sim_id="sim_id",
        state=ProgressState.RUNNING,
        percent_complete=90,
        message="message",
        context="context",
    )

    # act
    handler.update(progress)
    handler.update(updated_progress)

    # assert
    assert handler._pbar is not None
    assert handler._last_context == updated_progress.context
    assert handler._last_percent_complete == updated_progress.percent_complete
    mock_update.assert_called_with(updated_progress.percent_complete - progress.percent_complete)
    mock_set_description.assert_called_once_with(progress.context)
    mock_reset.assert_called_once_with(total=100)


def test_default_single_simulation_progress_handler_skips_solver_info_updates():
    # arrange
    handler = DefaultSingleSimulationProgressHandler()
    progress = Progress(
        sim_id="sim_id",
        state=ProgressState.RUNNING,
        percent_complete=50,
        message="SOLVERINFO",
        context="context",
    )

    # act
    handler.update(progress)

    # assert
    assert not hasattr(handler, "_pbar")
    assert handler._last_context == "Initializing"
    assert handler._last_percent_complete == 0


@patch("ansys.additive.core.progress_handler.tqdm.write")
def test_default_single_simulation_progress_handler_calls_write_on_error(mock_write):
    # arrange
    handler = DefaultSingleSimulationProgressHandler()
    progress = Progress(
        sim_id="sim_id",
        state=ProgressState.ERROR,
        percent_complete=50,
        message="error message",
        context="context",
    )

    # act
    handler.update(progress)

    # assert
    mock_write.assert_called_once_with(progress.message)


@patch("ansys.additive.core.progress_handler.tqdm.reset")
@patch("ansys.additive.core.progress_handler.tqdm.set_description")
def test_default_single_simulation_progress_handler_does_not_reset_for_layer_change(
    mock_set_description, mock_reset
):
    # arrange
    handler = DefaultSingleSimulationProgressHandler()
    handler.update(
        Progress(
            sim_id="sim_id",
            state=ProgressState.RUNNING,
            percent_complete=50,
            message="initial context change",
            context="Solving Layer 1",
        )
    )
    mock_reset.reset_mock()
    mock_set_description.reset_mock()
    update = Progress(
        sim_id="sim_id",
        state=ProgressState.RUNNING,
        percent_complete=60,
        message="context change",
        context="Solving Layer 2",
    )

    # act
    handler.update(update)

    # assert
    mock_reset.assert_not_called()
    mock_set_description.assert_called_once_with(update.context, refresh=False)
