# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from ansys.api.additive.v0.additive_domain_pb2 import MeltPool as MeltPoolMessage
from ansys.api.additive.v0.additive_domain_pb2 import SingleBeadInput as SingleBeadInputMessage
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
from pandas import DataFrame

from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial


class SingleBeadInput:
    """Input parameters for single bead simulation."""

    #: Default bead length (m).
    DEFAULT_BEAD_LENGTH = 3e-3
    __MIN_BEAD_LENGTH = 1e-3
    __MAX_BEAD_LENGTH = 1e-2

    def __init__(
        self,
        id="",
        bead_length=DEFAULT_BEAD_LENGTH,
        machine=AdditiveMachine(),
        material=AdditiveMaterial(),
    ):
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
    def bead_length(self):
        """Length of bead to simulate (m).
        Valid values are from 1e-3 to 1e-2 m (1 to 10 mm)."""
        return self._bead_length

    @bead_length.setter
    def bead_length(self, value):
        self.__validate_range(value, self.__MIN_BEAD_LENGTH, self.__MAX_BEAD_LENGTH, "bead_length")
        self._bead_length = value

    def _to_simulation_request(self) -> SimulationRequest:
        """Convert this object into a simulation request message"""
        input = SingleBeadInputMessage(
            machine=self.machine._to_machine_message(),
            material=self.material._to_material_message(),
            bead_length=self.bead_length,
        )
        return SimulationRequest(id=self.id, single_bead_input=input)


class MeltPoolColumnNames:
    """Column names for melt pool data frame."""

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
    """Container for the melt pool evolution during a single bead simulation.

    Units are SI unless otherwise noted.

    """

    def __init__(self, msg: MeltPoolMessage):
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

    @property
    def data_frame(self) -> DataFrame:
        """:class:`Pandas DataFrame <pandas.DataFrame>` containing melt pool data.

        Values are in meters.

        Indices:
            - bead_length: Length of bead at each time step.

        Columns:
            - ``MeltPoolColumnNames.LENGTH``: length of melt pool at each time step.
            - ``MeltPoolColumnNames.WIDTH``: width of melt pool at each time step.
            - ``MeltPoolColumnNames.DEPTH``: depth of melt pool at each time step.
            - ``MeltPoolColumnNames.REFERENCE_WIDTH``: reference width of melt pool at each time step.
              Reference width is the melt pool width at the bottom of the powder layer,
              or, the width at the top of the substrate.
            - ``MeltPoolColumnNames.REFERENCE_DEPTH``: reference depth of melt pool at each time step.
              Reference depth is the depth of the entire melt pool minus the powder
              layer thickness, or, the depth of penetration into the substrate.
        """
        return self._df

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, MeltPool):
            return False
        return self._df.equals(__o._df)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        repr += self._df.to_string()
        return repr


class SingleBeadSummary:
    """Summary of a single bead simulation."""

    def __init__(
        self,
        input: SingleBeadInput,
        msg: MeltPoolMessage,
    ):
        if not isinstance(input, SingleBeadInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        if not isinstance(msg, MeltPoolMessage):
            raise ValueError("Invalid message type passed to init, " + self.__class__.__name__)
        self._input = input
        self._melt_pool = MeltPool(msg)

    @property
    def input(self) -> SingleBeadInput:
        """Simulation input, see :class:`SingleBeadInput`."""
        return self._input

    @property
    def melt_pool(self) -> MeltPool:
        """Resulting melt pool, see :class:`MeltPool`."""
        return self._melt_pool

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
