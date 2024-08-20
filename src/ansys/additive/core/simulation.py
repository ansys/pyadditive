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
from typing import Union

from ansys.additive.core.microstructure import MicrostructureInput
from ansys.additive.core.porosity import PorosityInput
from ansys.additive.core.single_bead import SingleBeadInput
from ansys.additive.core.thermal_history import ThermalHistoryInput


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


class SimulationError:
    """Provides simulation errors."""

    def __init__(
        self,
        input: Union[SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput],
        message: str,
    ):
        """Initialize a ``SimulationError`` object."""
        self._input = input
        self._message = message

    @property
    def input(
        self,
    ) -> Union[SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput]:
        """Simulation input."""
        return self._input

    @property
    def message(self) -> str:
        """Provides simulation error message."""
        return self._message
