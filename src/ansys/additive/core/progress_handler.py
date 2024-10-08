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
"""Provides progress updates."""

from abc import ABC, abstractmethod
from enum import IntEnum
from os import getenv

from pydantic import BaseModel
from tqdm import tqdm

from ansys.api.additive.v0.additive_domain_pb2 import Progress as ProgressMsg
from ansys.api.additive.v0.additive_domain_pb2 import ProgressState as ProgressMsgState
from ansys.api.additive.v0.additive_operations_pb2 import OperationMetadata


class ProgressState(IntEnum):
    """Simulation progress status."""

    NEW = ProgressMsgState.PROGRESS_STATE_NEW
    """Simulation created and not yet queued to run."""
    WAITING = ProgressMsgState.PROGRESS_STATE_WAITING
    """Simulation is queued and waiting to start."""
    RUNNING = ProgressMsgState.PROGRESS_STATE_EXECUTING
    """Simulation is running."""
    COMPLETED = ProgressMsgState.PROGRESS_STATE_COMPLETED
    """Simulation has completed."""
    ERROR = ProgressMsgState.PROGRESS_STATE_ERROR
    """Simulation has errored."""
    CANCELLED = ProgressMsgState.PROGRESS_STATE_CANCELLED
    """Simulation has been cancelled."""
    WARNING = ProgressMsgState.PROGRESS_STATE_WARNING
    """Simulation completed with warnings."""


class Progress(BaseModel):
    """Progress information."""

    sim_id: str
    state: ProgressState
    percent_complete: int
    message: str
    context: str

    @classmethod
    def from_proto_msg(cls, sim_id: str, progress: ProgressMsg):
        """Create a ``Progress`` object from a progress protobuf message."""
        return cls(
            sim_id=sim_id,
            state=ProgressState(progress.state),
            percent_complete=progress.percent_complete,
            message=progress.message,
            context=progress.context,
        )

    @classmethod
    def from_operation_metadata(cls, metadata: OperationMetadata):
        """Create a ``Progress`` object from an operation metadata (long-running operations) protobuf message."""  # noqa: E501
        return cls(
            sim_id=metadata.simulation_id,
            state=metadata.state,
            percent_complete=metadata.percent_complete,
            message=metadata.message,
            context=metadata.context,
        )

    def __str__(self):
        return f"{self.sim_id}: {self.state.name} - {self.percent_complete}% - {self.context} - {self.message}"  # noqa: E501


class IProgressHandler(ABC):
    """Interface for simulation progress updates."""

    @abstractmethod
    def update(self, progress: Progress):
        """Update progress.

        Parameters
        ----------
        progress : Progress
            Progress information.

        """
        raise NotImplementedError


class DefaultSingleSimulationProgressHandler(IProgressHandler):
    """Creates a progress bar for a single simulation.

    Parameters
    ----------
    sim_id : str
        Simulation ID.

    """

    def __init__(self):
        """Initialize progress handler."""
        self._last_percent_complete = 0
        self._last_context = "Initializing"

    def update(self, progress: Progress):
        """Update the progress bar.

        Parameters
        ----------
        progress: Progress
            Latest progress.

        """
        # Don't send  progress when generating docs
        if getenv("GENERATING_DOCS"):
            return

        # Skip SOLVERINFO messages
        if progress.message and "SOLVERINFO" in progress.message:
            return

        if not hasattr(self, "_pbar"):
            self._pbar = tqdm(
                total=100,
                colour="green",
                desc=self._last_context,
                dynamic_ncols=True,
            )

        if progress.state == ProgressState.ERROR:
            self._pbar.write(progress.message)
            return

        if progress.context and progress.context != self._last_context:
            if "Solving Layer" not in progress.context or progress.context == "Solving Layer 1":
                self._pbar.reset(total=100)
                self._pbar.set_description(progress.context)
                self._last_context = progress.context
                self._last_percent_complete = 0
            else:
                self._pbar.set_description(progress.context, refresh=False)

        if progress.percent_complete - self._last_percent_complete > 0:
            self._pbar.update(progress.percent_complete - self._last_percent_complete)
        self._last_percent_complete = progress.percent_complete

    def __del__(self):
        if hasattr(self, "_pbar"):
            self._pbar.close()
