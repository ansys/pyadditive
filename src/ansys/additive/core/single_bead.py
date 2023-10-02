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

from ansys.api.additive.v0.additive_domain_pb2 import MeltPool as MeltPoolMessage
from ansys.api.additive.v0.additive_domain_pb2 import SingleBeadInput as SingleBeadInputMessage
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
from pandas import DataFrame

from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial


class SingleBeadInput:
    """Provides input parameters for single bead simulation.

    Parameters
    ----------
    bead_length: float, optional, default: :obj:`DEFAULT_BEAD_LENGTH`
        Length (m) of bead to simulate, valid values are :obj:`MIN_BEAD_LENGTH` to :obj:`MAX_BEAD_LENGTH`.
    machine: :class:`AdditiveMachine <ansys.additive.core.machine.AdditiveMachine>`
        Machine parameters.
    material: :class:`AdditiveMaterial <ansys.additive.core.material.AdditiveMaterial>`
        Material parameters.
    """

    #: Default bead length (m).
    DEFAULT_BEAD_LENGTH = 3e-3
    #: Minimum bead length (m).
    MIN_BEAD_LENGTH = 1e-3
    #: Maximum bead length (m).
    MAX_BEAD_LENGTH = 1e-2

    def __init__(
        self,
        id: str = "",
        bead_length: float = DEFAULT_BEAD_LENGTH,
        machine: AdditiveMachine = AdditiveMachine(),
        material: AdditiveMaterial = AdditiveMaterial(),
    ):
        """Initialize a ``SingleBeadInput`` object.

        Parameters
        ----------
        bead_length: float, optional, default: :obj:`DEFAULT_BEAD_LENGTH`
            Length (m) of bead to simulate, valid values are :obj:`MIN_BEAD_LENGTH` to :obj:`MAX_BEAD_LENGTH`.
        machine: :class:`AdditiveMachine <ansys.additive.core.machine.AdditiveMachine>`
            Machine parameters.
        material: :class:`AdditiveMaterial <ansys.additive.core.material.AdditiveMaterial>`
            Material parameters.
        """
        self.id = id
        self.bead_length = bead_length
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
        if not isinstance(__o, SingleBeadInput):
            return False
        return (
            self.id == __o.id
            and self.bead_length == __o.bead_length
            and self.machine == __o.machine
            and self.material == __o.material
        )

    def __validate_range(self, value, min, max, name):
        if value < min or value > max:
            raise ValueError("{} must be between {} and {}.".format(name, min, max))

    @property
    def id(self) -> str:
        """User-provided ID for the simulation."""
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

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

        Valid values are from :obj:`MIN_BEAD_LENGTH` to :obj:`MAX_BEAD_LENGTH` m.
        """
        return self._bead_length

    @bead_length.setter
    def bead_length(self, value):
        self.__validate_range(value, self.MIN_BEAD_LENGTH, self.MAX_BEAD_LENGTH, "bead_length")
        self._bead_length = value

    def _to_simulation_request(self) -> SimulationRequest:
        """Convert this object into a simulation request message."""
        input = SingleBeadInputMessage(
            machine=self.machine._to_machine_message(),
            material=self.material._to_material_message(),
            bead_length=self.bead_length,
        )
        return SimulationRequest(id=self.id, single_bead_input=input)


class MeltPoolColumnNames:
    """Provides column names for the melt pool data frame."""

    #: Width of melt pool (m).
    WIDTH = "width"
    #: Depth of melt pool (m).
    DEPTH = "depth"
    #: Length of melt pool (m).
    LENGTH = "length"
    #: Width of melt pool at the surface of the base plate (m).
    REFERENCE_WIDTH = "reference_width"
    #: Depth of melt pool measured from the surface of the base plate (m).
    REFERENCE_DEPTH = "reference_depth"


class MeltPool:
    """Contains the melt pool size dimensions for each time step during a
    single bead simulation.

    Units are SI unless otherwise noted.

    Parameters
    ----------
    msg: ``MeltPoolMessage``
        Simulation result message describing the melt pool.
    """

    def __init__(self, msg: MeltPoolMessage):
        """Initialize a ``MeltPool`` object."""
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

    def data_frame(self) -> DataFrame:
        """Get the data frame containing the melt pool data.

        Values are in meters.

        Indices:
            - ``bead_length``: Length of the bead at each time step.

        Columns:
            - ``MeltPoolColumnNames.LENGTH``: Length of the melt pool.
            - ``MeltPoolColumnNames.WIDTH``: Width of the melt pool.
            - ``MeltPoolColumnNames.DEPTH``: Depth of the melt pool.
            - ``MeltPoolColumnNames.REFERENCE_WIDTH``: Reference width of the melt pool.
              Reference width is the melt pool width at the bottom of the powder layer
              or the width at the top of the substrate.
            - ``MeltPoolColumnNames.REFERENCE_DEPTH``: Reference depth of the melt pool.
              Reference depth is the depth of the entire melt pool minus the powder
              layer thickness or the depth of penetration into the substrate.
        """
        return self._df.copy()

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, MeltPool):
            return False
        return self._df.equals(__o._df)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        repr += self._df.to_string()
        return repr


class SingleBeadSummary:
    """Provides a summary of a single bead simulation.

    Parameters
    ----------
    input: :class:`SingleBeadInput`
        Input for single bead simulation.
    msg: ``MeltPoolMessage``
        Simulation result message describing the melt pool.
    """

    def __init__(
        self,
        input: SingleBeadInput,
        msg: MeltPoolMessage,
    ):
        """Initialize a ``SingleBeadSummary`` object.

        Parameters
        ----------
        input: :class:`SingleBeadInput`
            Input for the single bead simulation.
        msg: :class:`MeltPoolMessage`
            Message from the server describing the melt pool.
        """
        if not isinstance(input, SingleBeadInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        if not isinstance(msg, MeltPoolMessage):
            raise ValueError("Invalid message type passed to init, " + self.__class__.__name__)
        self._input = input
        self._melt_pool = MeltPool(msg)

    @property
    def input(self) -> SingleBeadInput:
        """Simulation input.

        For more information, see the :class:`SingleBeadInput` class.
        """
        return self._input

    @property
    def melt_pool(self) -> MeltPool:
        """Resulting melt pool.

        For more information, see the :class:`MeltPool` class.
        """
        return self._melt_pool

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
