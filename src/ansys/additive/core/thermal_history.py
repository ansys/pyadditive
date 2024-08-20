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
"""Provides input and result summary containers for thermal history simulations."""

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
from ansys.additive.core.simulation_input_base import SimulationInputBase


class Range:
    """Defines a range of values."""

    def __init__(self, min: float, max: float):
        """Initialize a ``Range`` object."""
        self._min = min
        self._max = max
        if self.min > self.max:
            raise ValueError("Attempted to initialize Range with min greater than max")

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Range):
            return False
        return self._min == other._min and self._max == other._max

    @property
    def min(self) -> float:
        """Minimum value of range."""
        return self._min

    @property
    def max(self) -> float:
        """Maximum value of range."""
        return self._max

    def _to_range_message(self) -> RangeMessage:
        """Transform this object into a ``RangeMessage`` object to send to the server."""
        return RangeMessage(min=self.min, max=self.max)


class CoaxialAverageSensorInputs:
    """Provides descriptions for coaxial average sensors."""

    MIN_SENSOR_RADIUS = 5e-5
    """Minimum radius for the circular field of view of the sensor (m)."""
    MAX_SENSOR_RADIUS = 1.5e-2
    """Maximum radius for the circular field of view of the sensor (m)."""

    def __init__(self, radius: float = MIN_SENSOR_RADIUS, z_heights: list[Range] = None):
        """Initialize a ``CoaxialAverageSensorInputs`` object."""
        self._radius = radius
        self._z_heights = z_heights if z_heights else []
        # use setter to validate radius
        self.radius = radius

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CoaxialAverageSensorInputs):
            return False
        return self._radius == other._radius and self._z_heights == other._z_heights

    @property
    def radius(self) -> float:
        """Radius of the circular field of the view of the sensor (m).

        Valid values are from the :obj:`MIN_SENSOR_RADIUS` value to the
        :obj:`MAX_SENSOR_RADIUS` value.
        """
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < self.MIN_SENSOR_RADIUS or value > self.MAX_SENSOR_RADIUS:
            raise ValueError(
                f"Radius values must be from {self.MIN_SENSOR_RADIUS} and {self.MAX_SENSOR_RADIUS}."
            )
        self._radius = value

    @property
    def z_heights(self) -> list[Range]:
        """Array of ranges along the z axis of the geometry (m).

        The simulated sensor follows the scan path for each deposit layer within each
        range.
        """
        return self._z_heights

    def _to_coaxial_average_sensor_inputs_message(self) -> CoaxialAverageSensorInputsMessage:
        """Create a coaxial average sensor input message to send to the server
        based upon this object."""
        msg = CoaxialAverageSensorInputsMessage(sensor_radius=self.radius)
        for z in self.z_heights:
            msg.z_heights.append(z._to_range_message())
        return msg


class ThermalHistoryInput(SimulationInputBase):
    """Provides input parameters for microstructure simulation."""

    def __init__(
        self,
        *,
        machine: AdditiveMachine = AdditiveMachine(),
        material: AdditiveMaterial = AdditiveMaterial(),
        geometry: StlFile | BuildFile = None,
        coax_ave_sensor_inputs: CoaxialAverageSensorInputs = CoaxialAverageSensorInputs(),
    ):
        """Initialize a ``ThermalHistoryInput`` object."""
        super().__init__()
        self._machine = machine
        self._material = material
        self._geometry = geometry
        self._coax_ave_sensor_inputs = coax_ave_sensor_inputs

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            if k == "_machine" or k == "_material":
                repr += "\n" + k.replace("_", "", 1) + ": " + str(getattr(self, k))
            else:
                repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ThermalHistoryInput):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True

    @property
    def machine(self) -> AdditiveMachine:
        """Machine parameters."""
        return self._machine

    @machine.setter
    def machine(self, value):
        self._machine = value

    @property
    def material(self) -> AdditiveMaterial:
        """Material parameters."""
        return self._material

    @material.setter
    def material(self, value):
        self._material = value

    @property
    def geometry(self) -> StlFile | BuildFile:
        """Part geometry."""
        return self._geometry

    @geometry.setter
    def geometry(self, value):
        """Set geometry."""
        if not isinstance(value, (StlFile, BuildFile)):
            raise TypeError("Geometry must be an StlFile or BuildFile.")
        self._geometry = value

    @property
    def coax_ave_sensor_inputs(self) -> CoaxialAverageSensorInputs:
        """Coaxial average sensor inputs."""
        return self._coax_ave_sensor_inputs

    @coax_ave_sensor_inputs.setter
    def coax_ave_sensor_inputs(self, value):
        if not isinstance(value, CoaxialAverageSensorInputs):
            raise TypeError(
                "Coaxial average sensor inputs must be a 'CoaxialAverageSensorInputs' object."
            )
        self._coax_ave_sensor_inputs = value

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
    def input(self) -> ThermalHistoryInput:
        """Simulation input.

        For more information, see the :class:`ThermalHistoryInput` class.
        """
        return self._input

    @property
    def coax_ave_output_folder(self) -> str:
        """Path to the folder containing the coaxial average sensor results.

        Results consist of VTK files, one per deposit layer, containing the thermal
        history of the scan pattern.
        """
        return self._coax_ave_output_folder
