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
"""Manages simulation tasks."""

from __future__ import annotations

from ansys.additive.core.progress_handler import IProgressHandler, Progress
from ansys.additive.core.simulation_task import SimulationTask


class SimulationTaskManager:
    """Provides a manager for simulation tasks."""

    def __init__(self):
        """Initialize the simulation task manager."""
        self._tasks: list[SimulationTask] = []

    def add_task(self, task: SimulationTask):
        """Add a task to this manager.

        Parameters
        ----------
        task: SimulationTask
            The simulation task holding the long running operation and corresponding server.
        """
        self._tasks.append(task)

    def status(
        self, progress_handler: IProgressHandler | None = None
    ) -> list[tuple[str, Progress]]:
        """Get status of each operation stored in this manager.

        Parameters
        ----------
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.

        Returns
        -------
        List of tuples with each tuple containing the operation name and an instance of Progress
        """
        status_all = list[tuple[str, Progress]]

        for t in self._tasks:
            progress = t.status(progress_handler)
            status_all.append((t._long_running_op.name, progress))

        return status_all

    def wait_all(self, progress_handler: IProgressHandler | None = None) -> None:
        """Wait for all simulations to finish. A simple loop that waits for each task will wait for the
        simulation that takes the longest. This works because wait returns immediately if operation is done.

        Parameters
        ----------
        progress_handler: IProgressHandler, None, default: None
            Handler for progress updates. If ``None``, no progress updates are provided.
        """
        for t in self._tasks:
            t.wait(progress_handler=progress_handler)

    def summaries(self):
        """Get a list of the summaries of completed simulations only."""
        return [t.summary for t in self._tasks if t.summary]