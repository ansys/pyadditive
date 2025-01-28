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
"""Provides common definitions and classes for simulations."""

from enum import Enum

from ansys.additive.core.misc import short_uuid


class SimulationType(str, Enum):
    """Provides simulation types."""

    SINGLE_BEAD = "SingleBead"
    """Single bead simulation."""
    POROSITY = "Porosity"
    """Porosity simulation."""
    MICROSTRUCTURE = "Microstructure"
    """Microstructure simulation."""


class SimulationStatus(str, Enum):
    """Provides simulation status values."""

    # NOTE: Values are listed in order of precedence when deduping.
    # For example, if duplicate COMPLETED and WARNING simulations are
    # found when removing duplicates, the COMPLETED simulation will be
    # kept.
    COMPLETED = "Completed"
    """Simulation completed successfully."""
    WARNING = "Warning"
    """Simulation completed with warnings."""
    ERROR = "Error"
    """Simulation errored before completion."""
    CANCELLED = "Cancelled"
    """Simulation was cancelled."""
    RUNNING = "Running"
    """Simulation is running."""
    PENDING = "Pending"
    """Simulation is queued and waiting to run."""
    NEW = "New"
    """Simulation is created but not yet queued to run."""
    SKIP = "Skip"
    """Do not run this simulation, only applies to parametric studies."""


class SimulationInputBase:
    """Provides a base class for simulation inputs."""

    def __init__(self) -> None:
        """Initialize the simulation input base class."""
        self._id: str = short_uuid()

    @property
    def id(self) -> str:
        """Return a unique identifier for this simulation."""
        return self._id


class SimulationSummaryBase:
    """Provides a base class for simulation summaries."""

    def __init__(self, logs: str, status: SimulationStatus = SimulationStatus.COMPLETED):
        """Initialize a ``SimulationSummaryBase`` object."""
        self._logs = logs
        self._status = status

    @property
    def logs(self) -> str:
        """Simulation logs."""
        return self._logs

    @property
    def status(self) -> SimulationStatus:
        """Simulation status."""
        return self._status
