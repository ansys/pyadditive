# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Union

from ansys.additive.microstructure import MicrostructureInput
from ansys.additive.porosity import PorosityInput
from ansys.additive.single_bead import SingleBeadInput
from ansys.additive.thermal_history import ThermalHistoryInput

class SimulationType:
    """Simulation types for a parametric study."""

    #: Single bead simulation.
    SINGLE_BEAD = "single_bead"
    #: Porosity simulation.
    POROSITY = "porosity"
    #: Microstructure simulation.
    MICROSTRUCTURE = "microstructure"


class SimulationStatus:
    """Simulation status values."""

    #: Simulation is awaiting execution.
    PENDING = "pending"
    #: Simulation was executed.
    COMPLETED = "completed"
    #: Simulation errored.
    ERROR = "error"
    #: Do not execute this simulation. Only applies to parametric studies.
    SKIP = "skip"


class SimulationError:
    """Container for simulation errors."""

    def __init__(self, input: Union[SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput], message: str):
        self._input = input
        self._message = message

    @property
    def input(self) -> Union[SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput]:
        """Simulation input."""
        return self._input

    @property
    def message(self) -> str:
        """Simulation error message."""
        return self._message
