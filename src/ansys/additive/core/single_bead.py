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
"""Provides input and result summary containers for single bead simulations."""

import math
import os
import zipfile

from ansys.api.additive.v0.additive_domain_pb2 import MeltPool as MeltPoolMessage
from ansys.api.additive.v0.additive_domain_pb2 import SingleBeadInput as SingleBeadInputMessage
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
import numpy as np
from pandas import DataFrame

from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.simulation_input_base import SimulationInputBase


class SingleBeadInput(SimulationInputBase):
    """Provides input parameters for a single bead simulation."""

    DEFAULT_BEAD_LENGTH = 3e-3
    """Default bead length (m)."""
    MIN_BEAD_LENGTH = 1e-3
    """Minimum bead length (m)."""
    MAX_BEAD_LENGTH = 1e-2
    """Maximum bead length (m)."""
    DEFAULT_OUTPUT_THERMAL_HISTORY = False
    """Default output thermal history flag."""
    DEFAULT_THERMAL_HISTORY_INTERVAL = 1
    """Default thermal history interval."""
    MIN_THERMAL_HISTORY_INTERVAL = 1
    """Minimum thermal history interval."""
    MAX_THERMAL_HISTORY_INTERVAL = 10000
    """Maximum thermal history interval."""

    def __init__(
        self,
        *,
        bead_length: float = DEFAULT_BEAD_LENGTH,
        machine: AdditiveMachine = AdditiveMachine(),
        material: AdditiveMaterial = AdditiveMaterial(),
        output_thermal_history: bool = DEFAULT_OUTPUT_THERMAL_HISTORY,
        thermal_history_interval: int = DEFAULT_THERMAL_HISTORY_INTERVAL,
    ):
        """Initialize a ``SingleBeadInput`` object."""
        super().__init__()
        self.bead_length = bead_length
        self.machine = machine
        self.material = material
        self.output_thermal_history = output_thermal_history
        self.thermal_history_interval = thermal_history_interval

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            if k == "_machine" or k == "_material":
                repr += "\n" + k.replace("_", "", 1) + ": " + str(getattr(self, k))
            else:
                repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, SingleBeadInput):
            return False
        return (
            self.id == __o.id
            and self.bead_length == __o.bead_length
            and self.machine == __o.machine
            and self.material == __o.material
            and self.output_thermal_history == __o.output_thermal_history
            and self.thermal_history_interval == __o.thermal_history_interval
        )

    def __validate_range(self, value, min, max, name):
        if math.isnan(value):
            raise ValueError("{} must be a number.".format(name))
        if value < min or value > max:
            raise ValueError("{} must be between {} and {}.".format(name, min, max))

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
    def bead_length(self) -> float:
        """Length (m) of bead to simulate.

        Valid values are from the :obj:`MIN_BEAD_LENGTH` value to the
        :obj:`MAX_BEAD_LENGTH` value.
        """
        return self._bead_length

    @bead_length.setter
    def bead_length(self, value):
        self.__validate_range(value, self.MIN_BEAD_LENGTH, self.MAX_BEAD_LENGTH, "bead_length")
        self._bead_length = value

    @property
    def output_thermal_history(self) -> bool:
        """Flag indicating whether to output the thermal history of the simulation."""
        return self._output_thermal_history

    @output_thermal_history.setter
    def output_thermal_history(self, value: bool):
        self._output_thermal_history = value

    @property
    def thermal_history_interval(self) -> int:
        """Interval, in simulation steps, between thermal history results.

        Use ``1`` to create thermal history results for every simulation step,
        ``2`` for every other step, and so on.
        """
        return self._thermal_history_interval

    @thermal_history_interval.setter
    def thermal_history_interval(self, value: int):
        self.__validate_range(
            value,
            self.MIN_THERMAL_HISTORY_INTERVAL,
            self.MAX_THERMAL_HISTORY_INTERVAL,
            "thermal_history_interval",
        )
        self._thermal_history_interval = value

    def _to_simulation_request(self) -> SimulationRequest:
        """Convert this object into a simulation request message."""
        input = SingleBeadInputMessage(
            machine=self.machine._to_machine_message(),
            material=self.material._to_material_message(),
            bead_length=self.bead_length,
            output_thermal_history=self.output_thermal_history,
            thermal_history_interval=self.thermal_history_interval,
        )
        return SimulationRequest(id=self.id, single_bead_input=input)


class MeltPoolColumnNames:
    """Provides column names for the melt pool data frame."""

    WIDTH = "width"
    """Width of melt pool (m)."""
    DEPTH = "depth"
    """Depth of melt pool (m)."""
    LENGTH = "length"
    """Length of melt pool (m)."""
    REFERENCE_WIDTH = "reference_width"
    """Width of melt pool at the surface of the base plate (m)."""
    REFERENCE_DEPTH = "reference_depth"
    """Depth of melt pool measured from the surface of the base plate (m)."""


class MeltPool:
    """Contains the melt pool size dimensions for each time step during a single bead simulation."""

    def __init__(self, msg: MeltPoolMessage, thermal_history_output: str | None = None):
        """Initialize a ``MeltPool`` object.

        Parameters:
            msg: MeltPoolMessage
                The message containing the melt pool data.
            thermal_history_output: str | None
                Path to the thermal history output file.
        """
        bead_length = [ts.laser_x for ts in msg.time_steps]
        length = [ts.length for ts in msg.time_steps]
        width = [ts.width for ts in msg.time_steps]
        depth = [ts.depth for ts in msg.time_steps]
        reference_width = [ts.reference_width for ts in msg.time_steps]
        reference_depth = [ts.reference_depth for ts in msg.time_steps]
        self._df = DataFrame(
            index=bead_length,
            data={
                MeltPoolColumnNames.LENGTH: length,
                MeltPoolColumnNames.WIDTH: width,
                MeltPoolColumnNames.DEPTH: depth,
                MeltPoolColumnNames.REFERENCE_WIDTH: reference_width,
                MeltPoolColumnNames.REFERENCE_DEPTH: reference_depth,
            },
        )
        self._df.index.name = "bead_length"
        self._thermal_history_output = thermal_history_output

    def data_frame(self) -> DataFrame:
        """Get the data frame containing the melt pool data.

        Values are in meters.

        Indices:
            - ``bead_length``: Length of the bead at each time step.

        Columns:
            - :obj:`MeltPoolColumnNames.LENGTH`.
            - :obj:`MeltPoolColumnNames.WIDTH`.
            - :obj:`MeltPoolColumnNames.DEPTH`.
            - :obj:`MeltPoolColumnNames.REFERENCE_WIDTH`.
            - :obj:`MeltPoolColumnNames.REFERENCE_DEPTH`.
        """
        return self._df.copy()

    def depth_over_width(self) -> float:
        """Return the median reference depth over reference width."""
        depth = self.median_reference_depth()
        width = self.median_reference_width()
        return depth / width if width != 0 else np.nan

    def length_over_width(self) -> float:
        """Return the median length over width."""
        length = self.median_length()
        width = self.median_width()
        return length / width if width != 0 else np.nan

    def median_width(self) -> float:
        """Return the median width."""
        return self._df[MeltPoolColumnNames.WIDTH].median()

    def median_depth(self) -> float:
        """Return the median depth."""
        return self._df[MeltPoolColumnNames.DEPTH].median()

    def median_length(self) -> float:
        """Return the median length."""
        return self._df[MeltPoolColumnNames.LENGTH].median()

    def median_reference_width(self) -> float:
        """Return the median reference width."""
        return self._df[MeltPoolColumnNames.REFERENCE_WIDTH].median()

    def median_reference_depth(self) -> float:
        """Return the median reference depth."""
        return self._df[MeltPoolColumnNames.REFERENCE_DEPTH].median()

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, MeltPool):
            return False
        return self._df.equals(__o._df)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        repr += self._df.to_string()
        repr += (
            "\n" + "grid_full_thermal_sensor_file_output_path: " + str(self.thermal_history_output)
        )
        return repr

    @property
    def thermal_history_output(self) -> str | None:
        """Path to the thermal history output file."""
        return self._thermal_history_output


class SingleBeadSummary:
    """Provides a summary of a single bead simulation."""

    THERMAL_HISTORY_OUTPUT_ZIP = "gridfullthermal.zip"

    def __init__(
        self,
        input: SingleBeadInput,
        msg: MeltPoolMessage,
        thermal_history_output: str | None = None,
    ):
        """Initialize a ``SingleBeadSummary`` object."""
        if not isinstance(input, SingleBeadInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        if not isinstance(msg, MeltPoolMessage):
            raise ValueError("Invalid message type passed to init, " + self.__class__.__name__)
        self._input = input
        self._melt_pool = MeltPool(msg, thermal_history_output)
        if thermal_history_output is not None:
            self._extract_thermal_history(thermal_history_output)

    @property
    def input(self) -> SingleBeadInput:
        """Simulation input."""
        return self._input

    @property
    def melt_pool(self) -> MeltPool:
        """Resulting melt pool."""
        return self._melt_pool

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def _extract_thermal_history(self, thermal_history_output):
        """Extract the thermal history output."""
        zip_file = os.path.join(thermal_history_output, self.THERMAL_HISTORY_OUTPUT_ZIP)
        if not os.path.isfile(zip_file):
            raise FileNotFoundError("Thermal history files not found: " + zip_file)
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(thermal_history_output)
        try:
            os.remove(zip_file)
        except OSError:
            pass
