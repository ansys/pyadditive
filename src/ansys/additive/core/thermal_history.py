# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
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

from ansys.api.additive.v0.additive_domain_pb2 import (
    CoaxialAverageSensorInputs as CoaxialAverageSensorInputsMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    ThermalHistoryInput as ThermalHistoryInputMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import BuildFile as BuildFileMessage
from ansys.api.additive.v0.additive_domain_pb2 import Range as RangeMessage
from ansys.api.additive.v0.additive_domain_pb2 import StlFile as StlFileMessage
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.core.geometry_file import BuildFile, StlFile
from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial


class Range:
    """Defines a parameter that spans a range of values.

    min: float
        Minimum value.
    max: float
        Maximum value.
    """

    def __init__(self, **kwargs):
        """Initialize a ``Range`` object."""
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

    def _to_range_message(self) -> RangeMessage:
        """Create a ``RangeMessage`` to send to the server based upon this
        object."""
        return RangeMessage(min=self.min, max=self.max)


class CoaxialAverageSensorInputs:
    """Provides descriptions for coaxial average sensors.

    radius: float
        Radius in meters for the circular field of the view of sensor. Valid values
        are from 5e-5 to 1.5e-2 m (0.05 - 15 mm).
    z_heights: Range[]
        Array of ranges in meters along the z axis of the geometry. The simulated
        sensor follows the scan path for each deposit layer within each range.
    """

    def __init__(self, **kwargs):
        """Initialize a ``CoaxialAverageSensorInputs`` object."""
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

    def _to_coaxial_average_sensor_inputs_message(self) -> CoaxialAverageSensorInputsMessage:
        """Create a coaxial average sensor input message to send to the server
        based upon this object."""
        msg = CoaxialAverageSensorInputsMessage(sensor_radius=self.radius)
        for z in self.z_heights:
            msg.z_heights.append(z._to_range_message())
        return msg


class ThermalHistoryInput:
    """Provides input parameters for microstructure simulation.

    id: string
        Simulation ID.
    machine: AdditiveMachine
        Machine-related parameters.
    material: AdditiveMaterial
        Material used during simulation.
    geometry: StlFile or BuildFile
        Geometry to use in the simulation.
    coax_ave_sensor_inputs: :class:`CoaxialAverageSensorInputs`
        Coaxial average sensor definition.
    """

    def __init__(self, **kwargs):
        """Initialize a ``ThermalHistoryInput`` object."""
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
        """Part geometry.

        For more information, see the :class:`StlFile`
        class or the :class:`BuildFile` class.
        """
        return self._geometry

    @geometry.setter
    def geometry(self, value):
        """Set geometry."""
        if not isinstance(value, (StlFile, BuildFile)):
            raise TypeError("ThermalHistoryInput.geometry must be an StlFile of BuildFile")
        self._geometry = value

    def _to_simulation_request(self, remote_geometry_path: str) -> SimulationRequest:
        """Convert this object into a simulation request message."""

        if not self.geometry:
            raise ValueError("Attempted to create simulation request without defining geometry")
        if not remote_geometry_path or (remote_geometry_path == ""):
            raise ValueError(
                "Attempted to create simulation request with empty remote_geometry_path"
            )

        input = ThermalHistoryInputMessage(
            machine=self.machine._to_machine_message(),
            material=self.material._to_material_message(),
            coax_ave_sensor_inputs=self.coax_ave_sensor_inputs._to_coaxial_average_sensor_inputs_message(),
        )

        if isinstance(self.geometry, StlFile):
            input.stl_file.CopyFrom(StlFileMessage(name=remote_geometry_path))
        else:
            input.build_file.CopyFrom(
                BuildFileMessage(type=self.geometry.type, name=remote_geometry_path)
            )

        return SimulationRequest(id=self.id, thermal_history_input=input)


class ThermalHistorySummary:
    """Summary of a thermal history simulation."""

    def __init__(self, input: ThermalHistoryInput, coax_ave_output_folder: str):
        """Initialize a ``ThermalHistorySummary`` object."""
        if not isinstance(input, ThermalHistoryInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        self._input = input
        self._coax_ave_output_folder = coax_ave_output_folder

    @property
    def input(self):
        """Simulation input.

        For more information, see the :class:`ThermalHistoryInput` class.
        """
        return self._input

    @property
    def coax_ave_output_folder(self):
        """Path to the folder containing the coaxial average sensor results."""
        return self._coax_ave_output_folder
