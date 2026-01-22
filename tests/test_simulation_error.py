# Copyright (C) 2022 - 2026 ANSYS, Inc. and/or its affiliates.
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

import hashlib
import os
from unittest.mock import Mock, patch

import pytest

from ansys.additive.core.geometry_file import StlFile
from ansys.additive.core.microstructure import MicrostructureInput
from ansys.additive.core.microstructure_3d import Microstructure3DInput
from ansys.additive.core.porosity import PorosityInput
from ansys.additive.core.simulation_error import SimulationError
from ansys.additive.core.single_bead import SingleBeadInput
from ansys.additive.core.thermal_history import ThermalHistoryInput
from tests import test_utils


@pytest.mark.parametrize(
    "input, expectedInputType",
    [
        (SingleBeadInput(), SingleBeadInput),
        (PorosityInput(), PorosityInput),
        (MicrostructureInput(), MicrostructureInput),
        (Microstructure3DInput(), Microstructure3DInput),
        (
            ThermalHistoryInput(
                geometry=StlFile(test_utils.get_test_file_path("5x5x1_0x_0y_0z.stl"))
            ),
            ThermalHistoryInput,
        ),
        (Microstructure3DInput(), Microstructure3DInput),
    ],
)
def test_simulation_error(input, expectedInputType):
    # arrange
    message = "message"
    logs = "logs"

    # act
    simulation_error = SimulationError(input, message, logs)

    # assert
    assert simulation_error.input == input
    assert simulation_error.message == message
    assert simulation_error.logs == logs
    assert isinstance(simulation_error.input, expectedInputType)
