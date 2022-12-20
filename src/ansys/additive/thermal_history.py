# (c) 2022 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.

from ansys.api.additive.v0.additive_domain_pb2 import (
    CoaxialAverageSensorInputs as CoaxialAverageSensorInputsMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    ThermalHistoryInput as ThermalHistoryInputMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import BuildFile as BuildFileMessage
from ansys.api.additive.v0.additive_domain_pb2 import Range as RangeMessage
from ansys.api.additive.v0.additive_domain_pb2 import StlFile as StlFileMessage
from ansys.api.additive.v0.additive_domain_pb2 import ThermalHistoryResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.geometry_file import BuildFile, StlFile
from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial


class Range:
    """Defines a parameter that spans a range of values

    Properties
    ----------
    min: float
        Minimum value
    max: float
        Maximum value

    """

    def __init__(self, **kwargs):
        self.min = 0
        self.max = 0
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)
        if self.min > self.max:
            raise ValueError("Attempted to initialize Range with min greater than max")

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Range):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True

    def to_range_message(self) -> RangeMessage:
        return RangeMessage(min=self.min, max=self.max)


class CoaxialAverageSensorInputs:
    """Coaxial average sensor descriptions

    Properties
    ----------

    radius: float (meters)
        Radius for circular field of view of sensor. Validated values
        are 5e-5 to 1.5e-2 (0.05 - 15 mm).
    z_heights: Range[] (meters)
        Array of ranges along the z axis of the geometry. The simulated sensor will
        follow the scan path for each deposit layer within each range.

    """

    def __init__(self, **kwargs):
        self.radius = 0
        self.z_heights = []
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)
        if self.radius < 0:
            raise ValueError(
                "Attempted to initialize CoaxialAverageSensorInputs with negative sensor radius"
            )

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CoaxialAverageSensorInputs):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True

    def to_coaxial_average_sensor_inputs_message(self) -> CoaxialAverageSensorInputsMessage:
        msg = CoaxialAverageSensorInputsMessage(sensor_radius=self.radius)
        for z in self.z_heights:
            msg.z_heights.append(z.to_range_message())
        return msg


class ThermalHistoryInput:
    """Input parameters for microstructure simulation

    Properties
    ----------

    id: string
        Simulation identifier
    machine: AdditiveMachine
        Machine related parameters
    material: AdditiveMaterial
        Material used during simulation
    geometry: StlFile or BuildFile
        Geometry to use in simulation
    coax_ave_sensor_inputs: CoaxialAverageSensorInputs
        Coaxial average sensor definition

    """

    def __init__(self, **kwargs):
        self.id = ""
        self._geometry = None
        self.coax_ave_sensor_inputs = CoaxialAverageSensorInputs()
        self.machine = AdditiveMachine()
        self.material = AdditiveMaterial()
        for key, value in kwargs.items():
            if key == "geometry":
                self.geometry = value  # call setter
            else:
                getattr(self, key)  # raises AttributeError if key not found
                setattr(self, key, value)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            if k == "machine" or k == "material":
                repr += "\n" + k + ": " + str(getattr(self, k))
            elif k == "_geometry":
                repr += "geometry: " + str(getattr(self, k)) + "\n"
            else:
                repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ThermalHistoryInput):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True

    @property
    def geometry(self):
        return self._geometry

    @geometry.setter
    def geometry(self, value):
        if not isinstance(value, (StlFile, BuildFile)):
            raise TypeError("ThermalHistoryInput.geometry must be an StlFile of BuildFile")
        self._geometry = value

    def to_simulation_request(self, remote_geometry_path: str) -> SimulationRequest:
        """Convert this object into a simulation request message"""

        if not self.geometry:
            raise ValueError("Attempted to create simulation request without defining geometry")
        if not remote_geometry_path or (remote_geometry_path == ""):
            raise ValueError(
                "Attempted to create simulation request with empty remote_geometry_path"
            )

        input = ThermalHistoryInputMessage(
            machine=self.machine.to_machine_message(),
            material=self.material.to_material_message(),
            coax_ave_sensor_inputs=self.coax_ave_sensor_inputs.to_coaxial_average_sensor_inputs_message(),
        )

        if isinstance(self.geometry, StlFile):
            input.stl_file.CopyFrom(StlFileMessage(name=remote_geometry_path))
        else:
            input.build_file.CopyFrom(
                BuildFileMessage(type=self.geometry.type, name=remote_geometry_path)
            )

        return SimulationRequest(id=self.id, thermal_history_input=input)


class ThermalHistorySummary:
    """Summary of a thermal history simulation

    Properties
    ----------

    input: ThermalHistoryInput
        Simulation input parameters
    remote_coax_ave_zip_file: str
        Identifier used by the server for the coaxial average sensor results zip archive.
        Use the download service endpoint to retrieve the archive from the server.

    """

    def __init__(self, input: ThermalHistoryInput, result: ThermalHistoryResult):
        if not isinstance(input, ThermalHistoryInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        if not isinstance(result, ThermalHistoryResult):
            raise ValueError("Invalid result type passed to init, " + self.__class__.__name__)
        self._input = input
        self._remote_coax_ave_zip_file = result.coax_ave_zip_file

    @property
    def input(self):
        return self._input

    @property
    def remote_coax_ave_zip_file(self):
        return self._remote_coax_ave_zip_file
