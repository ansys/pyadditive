# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Union

from ansys.additive.microstructure import MicrostructureInput
from ansys.additive.porosity import PorosityInput
from ansys.additive.single_bead import SingleBeadInput
from ansys.additive.thermal_history import ThermalHistoryInput


class SimulationType:
    """Provides simulation types."""

    #: Single bead simulation.
    SINGLE_BEAD = "SingleBead"
    #: Porosity simulation.
    POROSITY = "Porosity"
    #: Microstructure simulation.
    MICROSTRUCTURE = "Microstructure"


class SimulationStatus:
    """Simulation status values."""

    #: Simulation is awaiting execution.
    PENDING = "Pending"
    #: Simulation was executed.
    COMPLETED = "Completed"
    #: Simulation errored.
    ERROR = "Error"
    #: Do not execute this simulation. Only applies to parametric studies.
    SKIP = "Skip"


class SimulationError:
    """Provides simulation errors."""

    def __init__(
        self,
        input: Union[SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput],
        message: str,
    ):
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
