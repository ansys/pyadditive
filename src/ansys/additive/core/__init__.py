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
"""Python client for the Ansys Additive service."""

import os

import platformdirs

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:  # pragma: no cover
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

__APP_NAME = "pyadditive"
__COMPANY_NAME = "Ansys Inc"

# Setup data directory
USER_DATA_PATH = platformdirs.user_data_dir(__APP_NAME, __COMPANY_NAME)
"""Storage path for user data."""
if not os.path.exists(USER_DATA_PATH):  # pragma: no cover
    os.makedirs(USER_DATA_PATH)

EXAMPLES_PATH = os.path.join(USER_DATA_PATH, "examples")
"""Storage path for example data."""
if not os.path.exists(EXAMPLES_PATH):  # pragma: no cover
    os.makedirs(EXAMPLES_PATH)

from ansys.additive.core.additive import Additive  # noqa: F401, E402
from ansys.additive.core.exceptions import (  # noqa: F401, E402
    BetaFeatureNotEnabledError,
)
from ansys.additive.core.geometry_file import (  # noqa: F401, E402
    BuildFile,
    MachineType,
    StlFile,
)
from ansys.additive.core.logger import LOG  # noqa: F401, E402
from ansys.additive.core.machine import (  # noqa: F401, E402
    AdditiveMachine,
    MachineConstants,
)
from ansys.additive.core.material import (  # noqa: F401, E402
    AdditiveMaterial,
    CharacteristicWidthDataPoint,
    ThermalPropertiesDataPoint,
)
from ansys.additive.core.material_tuning import (  # noqa: F401, E402
    MaterialTuningInput,
    MaterialTuningSummary,
)
from ansys.additive.core.microstructure import (  # noqa: F401, E402
    CircleEquivalenceColumnNames,
    MicrostructureInput,
    MicrostructureSummary,
)
from ansys.additive.core.microstructure_3d import (  # noqa: F401, E402
    Microstructure3DInput,
    Microstructure3DSummary,
)
from ansys.additive.core.porosity import (  # noqa: F401, E402
    PorosityInput,
    PorositySummary,
)
from ansys.additive.core.simulation import (  # noqa: F401, E402
    SimulationStatus,
    SimulationType,
)
from ansys.additive.core.simulation_error import SimulationError  # noqa: F401, E402
from ansys.additive.core.simulation_task import SimulationTask  # noqa: F401, E402
from ansys.additive.core.simulation_task_manager import (  # noqa: F401, E402
    SimulationTaskManager,
)
from ansys.additive.core.single_bead import (  # noqa: F401, E402
    MeltPool,
    MeltPoolColumnNames,
    SingleBeadInput,
    SingleBeadSummary,
)
from ansys.additive.core.thermal_history import (  # noqa: F401, E402
    CoaxialAverageSensorInputs,
    Range,
    ThermalHistoryInput,
    ThermalHistorySummary,
)
