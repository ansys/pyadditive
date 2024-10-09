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
"""Provides a class to update progress when running parametric study simulations."""

import threading

from ansys.additive.core.logger import LOG
from ansys.additive.core.parametric_study import ParametricStudy
from ansys.additive.core.progress_handler import (
    IProgressHandler,
    Progress,
    ProgressState,
)
from ansys.additive.core.simulation import SimulationStatus


class ParametricStudyProgressHandler(IProgressHandler):
    """Provides methods to update parametric study simulation status.

    Parameters
    ----------
    study : ParametricStudy
        Parametric study to update.

    """

    def __init__(
        self,
        study: ParametricStudy,
    ) -> None:
        """Initialize progress handler."""

        self._study_lock = threading.Lock()
        self._study = study
        # Store the last state of each simulation to avoid
        # unnecessary disk writes when setting the simulation status
        # on the study.
        self._last_progress_states = {}

    def update(self, progress: Progress) -> None:
        """Update the progress of a simulation.

        Parameters
        ----------
        progress : Progress
            Progress information for the simulation.

        """
        if (
            progress.sim_id in self._last_progress_states
            and progress.state == self._last_progress_states[progress.sim_id]
        ):
            return

        LOG.debug(f"Updating progress for {progress.sim_id}")

        if progress.state == ProgressState.WAITING:
            self._update_simulation_status(progress.sim_id, SimulationStatus.PENDING)
        elif progress.state == ProgressState.CANCELLED:
            self._update_simulation_status(progress.sim_id, SimulationStatus.CANCELLED)
        elif progress.state == ProgressState.RUNNING:
            self._update_simulation_status(progress.sim_id, SimulationStatus.RUNNING)
        elif progress.state == ProgressState.WARNING:
            self._update_simulation_status(progress.sim_id, SimulationStatus.WARNING)
        elif progress.state == ProgressState.COMPLETED:
            self._update_simulation_status(progress.sim_id, SimulationStatus.COMPLETED)
        elif progress.state == ProgressState.ERROR:
            self._update_simulation_status(
                progress.sim_id, SimulationStatus.ERROR, progress.message
            )

        self._last_progress_states[progress.sim_id] = progress.state

    def _update_simulation_status(
        self, sim_id: str, status: SimulationStatus, message: str = None
    ) -> None:
        """Update the status of a simulation.

        Parameters
        ----------
        sim_id : str
            Simulation ID.
        status : SimulationStatus
            Simulation status.
        message : str, optional
            Status message.

        """

        with self._study_lock:
            self._study.set_simulation_status(sim_id, status, message)
