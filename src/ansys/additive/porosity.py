# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from ansys.api.additive.v0.additive_domain_pb2 import PorosityInput as PorosityInputMessage
from ansys.api.additive.v0.additive_domain_pb2 import PorosityResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial


class PorosityInput:
    """Input parameters for porosity simulation.

    ``id: string``
        User provided identifier for this simulation.
    ``size_x: float``
        Size of simulated sample in x dimension (m), valid values: 0.001 to 0.01.
    ``size_y: float``
        Size of simulated sample in y dimension (m), valid values: 0.001 to 0.01.
    ``size_z: float``
        Size of simulated sample in z dimension (m), valid values: 0.001 to 0.01.
    ``machine: AdditiveMachine``
        Machine related parameters.
    ``material: AdditiveMaterial``
        Material used during simulation.
    """

    #: Default sample size (m) in each dimension.
    DEFAULT_SAMPLE_SIZE = 3e-3
    __MIN_SAMPLE_SIZE = 1e-3
    __MAX_SAMPLE_SIZE = 1e-2

    def __init__(
        self,
        id="",
        *,
        size_x=DEFAULT_SAMPLE_SIZE,
        size_y=DEFAULT_SAMPLE_SIZE,
        size_z=DEFAULT_SAMPLE_SIZE,
        machine=AdditiveMachine(),
        material=AdditiveMaterial(),
    ):
        self.id = id
        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z
        self.machine = machine
        self.material = material

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            if k == "_machine" or k == "_material":
                repr += "\n" + k.replace("_", "", 1) + ": " + str(getattr(self, k))
            else:
                repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, PorosityInput):
            return False
        return (
            self.id == __o.id
            and self.size_x == __o.size_x
            and self.size_y == __o.size_y
            and self.size_z == __o.size_z
            and self.machine == __o.machine
            and self.material == __o.material
        )

    def __validate_range(self, value, min, max, name):
        if value < min or value > max:
            raise ValueError("{} must be between {} and {}.".format(name, min, max))

    @property
    def id(self):
        """User provided identifier for this simulation."""
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def machine(self):
        """Machine related parameters."""
        return self._machine

    @machine.setter
    def machine(self, value):
        self._machine = value

    @property
    def material(self):
        """Material used during simulation."""
        return self._material

    @material.setter
    def material(self, value):
        self._material = value

    @property
    def size_x(self):
        """Size of simulated sample in x dimension (m).

        Valid values are from 1e-3 to 1e-2 m (1 to 10 mm).
        """
        return self._size_x

    @size_x.setter
    def size_x(self, value):
        self.__validate_range(value, self.__MIN_SAMPLE_SIZE, self.__MAX_SAMPLE_SIZE, "size_x")
        self._size_x = value

    @property
    def size_y(self):
        """Size of simulated sample in y dimension (m).

        Valid values are from 1e-3 to 1e-2 m (1 to 10 mm).
        """
        return self._size_y

    @size_y.setter
    def size_y(self, value):
        self.__validate_range(value, self.__MIN_SAMPLE_SIZE, self.__MAX_SAMPLE_SIZE, "size_y")
        self._size_y = value

    @property
    def size_z(self):
        """Size of simulated sample in z dimension (m).

        Valid values are from 1e-3 to 1e-2 m (1 to 10 mm).
        """
        return self._size_z

    @size_z.setter
    def size_z(self, value):
        self.__validate_range(value, self.__MIN_SAMPLE_SIZE, self.__MAX_SAMPLE_SIZE, "size_z")
        self._size_z = value

    def _to_simulation_request(self) -> SimulationRequest:
        """Convert this object into a simulation request message."""
        input = PorosityInputMessage(
            machine=self.machine._to_machine_message(),
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
        self._relative_density = result.solid_ratio

    @property
    def input(self) -> PorosityInput:
        """Simulation input, see :class:`PorosityInput`."""
        return self._input

    @property
    def relative_density(self) -> float:
        """Ratio of the density of the simulated sample to a completely solid
        sample."""
        return self._relative_density

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
