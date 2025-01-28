# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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
"""Provides simulation error information."""

from ansys.additive.core.material_tuning import MaterialTuningInput
from ansys.additive.core.microstructure import MicrostructureInput
from ansys.additive.core.microstructure_3d import Microstructure3DInput
from ansys.additive.core.porosity import PorosityInput
from ansys.additive.core.single_bead import SingleBeadInput
from ansys.additive.core.thermal_history import ThermalHistoryInput


class SimulationError:
    """Provides simulation error information."""

    def __init__(
        self,
        input: (
            SingleBeadInput
            | PorosityInput
            | MicrostructureInput
            | Microstructure3DInput
            | ThermalHistoryInput
            | MaterialTuningInput
        ),
        message: str,
        logs: str,
    ):
        """Initialize a ``SimulationError`` object."""
        self._input = input
        self._message = message
        self._logs = logs

    @property
    def input(
        self,
    ) -> (
        SingleBeadInput
        | PorosityInput
        | MicrostructureInput
        | Microstructure3DInput
        | ThermalHistoryInput
        | MaterialTuningInput
    ):
        """Simulation input."""
        return self._input

    @property
    def message(self) -> str:
        """Provides simulation error message."""
        return self._message

    @property
    def logs(self) -> str:
        """Provides simulation logs."""
        return self._logs
