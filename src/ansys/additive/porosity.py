from ansys.api.additive.v0.additive_domain_pb2 import PorosityInput as PorosityInputMessage
from ansys.api.additive.v0.additive_domain_pb2 import PorosityResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial


class PorosityInput:
    """Input parameters for porosity simulation

    ``id: string``
        User provided identifier for this simulation
    ``size_x: float``
        Size of simulated sample in x dimension (m), valid values: 0.001 to 0.01
    ``size_y: float``
        Size of simulated sample in y dimension (m), valid values: 0.001 to 0.01
    ``size_z: float``
        Size of simulated sample in z dimension (m), valid values: 0.001 to 0.01
    ``machine: AdditiveMachine``
        Machine related parameters
    ``material: AdditiveMaterial``
        Material used during simulation

    """

    def __init__(self, **kwargs):
        self.id = ""
        self.size_x = 1e-3
        self.size_y = 1e-3
        self.size_z = 1e-3
        self.machine = AdditiveMachine()
        self.material = AdditiveMaterial()
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            if k == "machine" or k == "material":
                repr += "\n" + k + ": " + str(getattr(self, k))
            else:
                repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def _to_simulation_request(self) -> SimulationRequest:
        """Convert this object into a simulation request message"""
        input = PorosityInputMessage(
            machine=self.machine.to_machine_message(),
            material=self.material._to_material_message(),
            size_x=self.size_x,
            size_y=self.size_y,
            size_z=self.size_z,
        )
        return SimulationRequest(id=self.id, porosity_input=input)


class PorositySummary:
    """Summary of a porosity simulation.

    Units are SI unless otherwise noted.

    """

    def __init__(
        self,
        input: PorosityInput,
        result: PorosityResult,
    ):
        if not isinstance(input, PorosityInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        if not isinstance(result, PorosityResult):
            raise ValueError("Invalid result type passed to init, " + self.__class__.__name__)
        self._input = input
        self._void_ratio = result.void_ratio
        self._powder_ratio = result.powder_ratio
        self._solid_ratio = result.solid_ratio

    @property
    def input(self) -> PorosityInput:
        """Simulation input."""
        return self._input

    @property
    def void_ratio(self) -> float:
        """Ratio of void to total volume of simulated sample."""
        return self._void_ratio

    @property
    def powder_ratio(self) -> float:
        """Ratio of powder to total volume of simulated sample."""
        return self._powder_ratio

    @property
    def solid_ratio(self) -> float:
        """Ratio of solid to total volume of simulated sample."""
        return self._solid_ratio

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
