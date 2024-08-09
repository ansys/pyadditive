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
"""Provides input and result summary containers for porosity simulations."""
import math

from ansys.api.additive.v0.additive_domain_pb2 import PorosityInput as PorosityInputMessage
from ansys.api.additive.v0.additive_domain_pb2 import PorosityResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.simulation_input_base import SimulationInputBase


class PorosityInput(SimulationInputBase):
    """Provides input parameters for porosity simulation."""

    DEFAULT_SAMPLE_SIZE = 3e-3
    """Default sample size in each dimension (m)."""
    MIN_SAMPLE_SIZE = 1e-3
    """Minimum sample size in each dimension (m)."""
    MAX_SAMPLE_SIZE = 1e-2
    """Maximum sample size in each dimension (m)."""

    def __init__(
        self,
        *,
        size_x: float = DEFAULT_SAMPLE_SIZE,
        size_y: float = DEFAULT_SAMPLE_SIZE,
        size_z: float = DEFAULT_SAMPLE_SIZE,
        machine: AdditiveMachine = AdditiveMachine(),
        material: AdditiveMaterial = AdditiveMaterial(),
    ):
        """Initialize a ``PorosityInput`` object."""
        super().__init__()
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
        if math.isnan(value):
            raise ValueError("{} must be a number.".format(name))
        if value < min or value > max:
            raise ValueError("{} must be between {} and {}.".format(name, min, max))

    @property
    def machine(self) -> AdditiveMachine:
        """Machine-related parameters."""
        return self._machine

    @machine.setter
    def machine(self, value):
        self._machine = value

    @property
    def material(self) -> AdditiveMaterial:
        """Material used during the simulation."""
        return self._material

    @material.setter
    def material(self, value):
        self._material = value

    @property
    def size_x(self) -> float:
        """Size (m) of the simulated sample in the x dimension.

        Valid values are from the :obj:`MIN_SAMPLE_SIZE` value to the
        :obj:`MAX_SAMPLE_SIZE` value.
        """
        return self._size_x

    @size_x.setter
    def size_x(self, value):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "size_x")
        self._size_x = value

    @property
    def size_y(self) -> float:
        """Size (m) of the simulated sample in the y dimension.

        Valid values are from the :obj:`MIN_SAMPLE_SIZE` value to the
        :obj:`MAX_SAMPLE_SIZE` value.
        """
        return self._size_y

    @size_y.setter
    def size_y(self, value):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "size_y")
        self._size_y = value

    @property
    def size_z(self) -> float:
        """Size (m) of the simulated sample in the z dimension.

        Valid values are from the :obj:`MIN_SAMPLE_SIZE` value to the
        :obj:`MAX_SAMPLE_SIZE` value.
        """
        return self._size_z

    @size_z.setter
    def size_z(self, value):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "size_z")
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
    """Provides a summary of a porosity simulation."""

    def __init__(
        self,
        input: PorosityInput,
        result: PorosityResult,
    ):
        """Initialize a ``PorositySummary`` object."""
        if not isinstance(input, PorosityInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        if not isinstance(result, PorosityResult):
            raise ValueError("Invalid result type passed to init, " + self.__class__.__name__)
        self._input = input
        self._relative_density = result.solid_ratio

    @property
    def input(self) -> PorosityInput:
        """Simulation input."""
        return self._input

    @property
    def relative_density(self) -> float:
        """Ratio of the density of the simulated sample to a completely solid sample."""
        return self._relative_density

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
