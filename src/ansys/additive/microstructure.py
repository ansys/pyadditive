# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import math
import os

from ansys.api.additive.v0.additive_domain_pb2 import (
    MicrostructureInput as MicrostructureInputMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import MicrostructureResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
from google.protobuf.internal.containers import RepeatedCompositeFieldContainer
import numpy as np
import pandas as pd

from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial


class MicrostructureInput:
    """Provides input parameters for microstructure simulation.

    Units are SI (m, kg, s, K) unless otherwise noted.
    """

    #: Default minimum x, y, z, position coordinate (m).
    DEFAULT_POSITION_COORDINATE = 0
    __MIN_POSITION_COORDINATE = 0
    __MAX_POSITION_COORDINATE = 10
    #: Default sample size (m) in each dimension.
    DEFAULT_SAMPLE_SIZE = 1.5e-3
    __MIN_SAMPLE_SIZE = 0.001
    __MAX_SAMPLE_SIZE = 0.01
    #: Default sensor dimension (m).
    DEFAULT_SENSOR_DIMENSION = 5e-4
    __MIN_SENSOR_DIMENSION = 1e-4
    __MAX_SENSOR_DIMENSION = 1e-3
    __MIN_XY_SIZE_CUSHION = 5e-4
    __MIN_Z_SIZE_CUSHION = 1e-3
    #: Default flag value indicating whether to use user provided thermal parameters.
    DEFAULT_USE_PROVIDED_THERMAL_PARAMETERS = False
    #: Default cooling rate (K/s).
    DEFAULT_COOLING_RATE = 1e6
    __MIN_COOLING_RATE = 1e5
    __MAX_COOLING_RATE = 1e7
    #: Default thermal gradient (K/m).
    DEFAULT_THERMAL_GRADIENT = 1e7
    __MIN_THERMAL_GRADIENT = 1e5
    __MAX_THERMAL_GRADIENT = 1e8
    #: Default melt pool width (m).
    DEFAULT_MELT_POOL_WIDTH = 1.5e-4
    __MIN_MELT_POOL_WIDTH = 7.5e-5
    __MAX_MELT_POOL_WIDTH = 8e-4
    #: Default melt pool depth (m).
    DEFAULT_MELT_POOL_DEPTH = 1e-4
    __MIN_MELT_POOL_DEPTH = 1.5e-5
    __MAX_MELT_POOL_DEPTH = 8e-4
    #: The default random seed is outside the range of valid seeds.
    #: It indicates that the user did not provide a seed.
    DEFAULT_RANDOM_SEED = 0
    __MIN_RANDOM_SEED = 1
    __MAX_RANDOM_SEED = 2**31 - 1

    def __init__(
        self,
        id: str = "",
        *,
        sample_min_x: float = DEFAULT_POSITION_COORDINATE,
        sample_min_y: float = DEFAULT_POSITION_COORDINATE,
        sample_min_z: float = DEFAULT_POSITION_COORDINATE,
        sample_size_x: float = DEFAULT_SAMPLE_SIZE,
        sample_size_y: float = DEFAULT_SAMPLE_SIZE,
        sample_size_z: float = DEFAULT_SAMPLE_SIZE,
        sensor_dimension: float = DEFAULT_SENSOR_DIMENSION,
        use_provided_thermal_parameters: bool = DEFAULT_USE_PROVIDED_THERMAL_PARAMETERS,
        cooling_rate: float = DEFAULT_COOLING_RATE,
        thermal_gradient: float = DEFAULT_THERMAL_GRADIENT,
        melt_pool_width: float = DEFAULT_MELT_POOL_WIDTH,
        melt_pool_depth: float = DEFAULT_MELT_POOL_DEPTH,
        random_seed: int = DEFAULT_RANDOM_SEED,
        machine: AdditiveMachine = AdditiveMachine(),
        material: AdditiveMaterial = AdditiveMaterial(),
    ):
        # we have a circular dependency here, so we validate sensor_dimension
        # and sample_size_* then assign them without calling the setters
        self.__validate_range(
            sensor_dimension,
            self.__MIN_SENSOR_DIMENSION,
            self.__MAX_SENSOR_DIMENSION,
            "sensor_dimension",
        )
        self.__validate_size(
            sample_size_x, sensor_dimension, self.__MIN_XY_SIZE_CUSHION, "sample_size_x"
        )
        self.__validate_size(
            sample_size_y, sensor_dimension, self.__MIN_XY_SIZE_CUSHION, "sample_size_y"
        )
        self.__validate_size(
            sample_size_z, sensor_dimension, self.__MIN_Z_SIZE_CUSHION, "sample_size_z"
        )
        self._sensor_dimension = sensor_dimension
        self._sample_size_x = sample_size_x
        self._sample_size_y = sample_size_y
        self._sample_size_z = sample_size_z

        # use setters for remaining properties
        self.id = id
        self.sample_min_x = sample_min_x
        self.sample_min_y = sample_min_y
        self.sample_min_z = sample_min_z
        self.use_provided_thermal_parameters = use_provided_thermal_parameters
        self.cooling_rate = cooling_rate
        self.thermal_gradient = thermal_gradient
        self.melt_pool_width = melt_pool_width
        self.melt_pool_depth = melt_pool_depth
        self.machine = machine
        self.material = material
        if random_seed != self.DEFAULT_RANDOM_SEED:
            self.random_seed = random_seed
        else:
            self._random_seed = random_seed

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            if k == "_machine" or k == "_material":
                repr += "\n" + k.replace("_", "", 1) + ": " + str(getattr(self, k))
            else:
                repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, MicrostructureInput):
            return False
        return (
            self.id == __o.id
            and self.sample_min_x == __o.sample_min_x
            and self.sample_min_y == __o.sample_min_y
            and self.sample_min_z == __o.sample_min_z
            and self.sample_size_x == __o.sample_size_x
            and self.sample_size_y == __o.sample_size_y
            and self.sample_size_z == __o.sample_size_z
            and self.sensor_dimension == __o.sensor_dimension
            and self.use_provided_thermal_parameters == __o.use_provided_thermal_parameters
            and self.cooling_rate == __o.cooling_rate
            and self.thermal_gradient == __o.thermal_gradient
            and self.melt_pool_width == __o.melt_pool_width
            and self.melt_pool_depth == __o.melt_pool_depth
            and self.random_seed == __o.random_seed
            and self.machine == __o.machine
            and self.material == __o.material
        )

    @staticmethod
    def __validate_range(value, min, max, name):
        if value < min or value > max:
            raise ValueError("{} must be between {} and {}.".format(name, min, max))

    @staticmethod
    def __validate_size(size_value, sensor_value, cushion, name):
        if size_value - sensor_value < cushion:
            raise ValueError(
                "{} must be at least {} larger than sensor_dimension.".format(name, cushion)
            )

    @property
    def id(self) -> str:
        """User-provided ID for this simulation."""
        return self._id

    @id.setter
    def id(self, value: str):
        self._id = value

    @property
    def machine(self):
        """Machine-related parameters."""
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
    def sample_min_x(self) -> float:
        """Minimum x coordinate (m) of the geometry sample."""
        return self._sample_min_x

    @sample_min_x.setter
    def sample_min_x(self, value: float):
        self.__validate_range(
            value, self.__MIN_POSITION_COORDINATE, self.__MAX_POSITION_COORDINATE, "sample_min_x"
        )
        self._sample_min_x = value

    @property
    def sample_min_y(self) -> float:
        """Minimum y coordinate (m) of the geometry sample."""
        return self._sample_min_y

    @sample_min_y.setter
    def sample_min_y(self, value: float):
        self.__validate_range(
            value, self.__MIN_POSITION_COORDINATE, self.__MAX_POSITION_COORDINATE, "sample_min_y"
        )
        self._sample_min_y = value

    @property
    def sample_min_z(self) -> float:
        """Minimum z coordinate (m) of the geometry sample."""
        return self._sample_min_z

    @sample_min_z.setter
    def sample_min_z(self, value: float):
        self.__validate_range(
            value, self.__MIN_POSITION_COORDINATE, self.__MAX_POSITION_COORDINATE, "sample_min_z"
        )
        self._sample_min_z = value

    @property
    def sample_size_x(self) -> float:
        """Size of the geometry sample in the x direction (m).

        Valid values are from 0.001 to 0.01.
        """
        return self._sample_size_x

    @sample_size_x.setter
    def sample_size_x(self, value: float):
        self.__validate_range(
            value, self.__MIN_SAMPLE_SIZE, self.__MAX_SAMPLE_SIZE, "sample_size_x"
        )
        self.__validate_size(
            value, self.sensor_dimension, self.__MIN_XY_SIZE_CUSHION, "sample_size_x"
        )
        self._sample_size_x = value

    @property
    def sample_size_y(self) -> float:
        """Size of the geometry sample in the y direction (m).

        Valid values are from 0.001 to 0.01.
        """
        return self._sample_size_y

    @sample_size_y.setter
    def sample_size_y(self, value: float):
        self.__validate_range(
            value, self.__MIN_SAMPLE_SIZE, self.__MAX_SAMPLE_SIZE, "sample_size_y"
        )
        self.__validate_size(
            value, self.sensor_dimension, self.__MIN_XY_SIZE_CUSHION, "sample_size_y"
        )
        self._sample_size_y = value

    @property
    def sample_size_z(self) -> float:
        """Size of the geometry sample in the z direction (m).

        Valid values are from 0.001 to 0.01.
        """
        return self._sample_size_z

    @sample_size_z.setter
    def sample_size_z(self, value: float):
        self.__validate_range(
            value, self.__MIN_SAMPLE_SIZE, self.__MAX_SAMPLE_SIZE, "sample_size_z"
        )
        self.__validate_size(
            value, self.sensor_dimension, self.__MIN_Z_SIZE_CUSHION, "sample_size_z"
        )
        self._sample_size_z = value

    @property
    def sensor_dimension(self) -> float:
        """Dimension of the sensor (m).

        Valid values are from 0.0001 to 0.001.
        """
        return self._sensor_dimension

    @sensor_dimension.setter
    def sensor_dimension(self, value: float):
        self.__validate_range(
            value, self.__MIN_SENSOR_DIMENSION, self.__MAX_SENSOR_DIMENSION, "sensor_dimension"
        )
        size_errors = ""
        try:
            self.__validate_size(
                self.sample_size_x, value, self.__MIN_XY_SIZE_CUSHION, "sample_size_x"
            )
        except ValueError as e:
            size_errors += str(e) + "\n"
        try:
            self.__validate_size(
                self.sample_size_y, value, self.__MIN_XY_SIZE_CUSHION, "sample_size_y"
            )
        except ValueError as e:
            size_errors += str(e) + "\n"
        try:
            self.__validate_size(
                self.sample_size_z, value, self.__MIN_Z_SIZE_CUSHION, "sample_size_z"
            )
        except ValueError as e:
            size_errors += str(e) + "\n"
        if size_errors:
            raise ValueError(size_errors)

        self._sensor_dimension = value

    @property
    def use_provided_thermal_parameters(self) -> bool:
        """Check to see if the ``cooling_rate``, ``thermal_gradient``,
        ``melt_pool_depth``, and ``melt_pool_width`` parameters have been
        provided by the user."""
        return self._use_provided_thermal_parameters

    @use_provided_thermal_parameters.setter
    def use_provided_thermal_parameters(self, value: bool):
        self._use_provided_thermal_parameters = value

    @property
    def cooling_rate(self) -> float:
        """Material cooling rate (K/s).

        Valid values are from 1e5 to 1e7.
        """
        return self._cooling_rate

    @cooling_rate.setter
    def cooling_rate(self, value: float):
        self.__validate_range(
            value, self.__MIN_COOLING_RATE, self.__MAX_COOLING_RATE, "cooling_rate"
        )
        self._cooling_rate = value

    @property
    def thermal_gradient(self) -> float:
        """Material thermal gradient (K/m).

        Valid values are from 1e5 to 1e8.
        """
        return self._thermal_gradient

    @thermal_gradient.setter
    def thermal_gradient(self, value: float):
        self.__validate_range(
            value, self.__MIN_THERMAL_GRADIENT, self.__MAX_THERMAL_GRADIENT, "thermal_gradient"
        )
        self._thermal_gradient = value

    @property
    def melt_pool_width(self) -> float:
        """Melt pool width (m).

        This is the width of the melt pool measured at the top of the powder layer,
        which corresponds to the ``WIDTH`` value in
        :class:`MeltPoolColumnNames <ansys.additive.single_bead.MeltPoolColumnNames>`
        class.

        Valid values are from 7.5e-5 to 8e-4.
        """
        return self._melt_pool_width

    @melt_pool_width.setter
    def melt_pool_width(self, value: float):
        self.__validate_range(
            value, self.__MIN_MELT_POOL_WIDTH, self.__MAX_MELT_POOL_WIDTH, "melt_pool_width"
        )
        self._melt_pool_width = value

    @property
    def melt_pool_depth(self) -> float:
        """Melt pool depth (m).

        This is the depth of the melt pool as measured from the top of the powder layer,
        which corresponds to the ``DEPTH``value in the
        :class:`MeltPoolColumnNames <ansys.additive.single_bead.MeltPoolColumnNames>`
        class.

        Valid values are from 1.5e-5 to 8e-4.
        """
        return self._melt_pool_depth

    @melt_pool_depth.setter
    def melt_pool_depth(self, value: float):
        self.__validate_range(
            value, self.__MIN_MELT_POOL_DEPTH, self.__MAX_MELT_POOL_DEPTH, "melt_pool_depth"
        )
        self._melt_pool_depth = value

    @property
    def random_seed(self) -> int:
        """Random seed for the simulation.

        Valid values are from 1 to 4294967295.
        """
        return self._random_seed

    @random_seed.setter
    def random_seed(self, value: int):
        self.__validate_range(value, self.__MIN_RANDOM_SEED, self.__MAX_RANDOM_SEED, "random_seed")
        self._random_seed = value

    def _to_simulation_request(self) -> SimulationRequest:
        """Convert this object into a simulation request message."""
        input = MicrostructureInputMessage(
            machine=self.machine._to_machine_message(),
            material=self.material._to_material_message(),
            cube_min_x=self.sample_min_x,
            cube_min_y=self.sample_min_y,
            cube_min_z=self.sample_min_z,
            cube_size_x=self.sample_size_x,
            cube_size_y=self.sample_size_y,
            cube_size_z=self.sample_size_z,
            sensor_dimension=self.sensor_dimension,
            use_provided_thermal_parameters=self.use_provided_thermal_parameters,
            cooling_rate=self.cooling_rate,
            thermal_gradient=self.thermal_gradient,
            melt_pool_width=self.melt_pool_width,
            melt_pool_depth=self.melt_pool_depth,
            use_random_seed=(self.random_seed != self.DEFAULT_RANDOM_SEED),
            random_seed=self.random_seed,
        )
        return SimulationRequest(id=self.id, microstructure_input=input)


class CircleEquivalenceColumnNames:
    """Provides column names for the circle equivalence data frame."""

    #: Grain number
    GRAIN_NUMBER = "grain_number"
    #: Area fraction for grain
    AREA_FRACTION = "area_fraction"
    #: Grain diameter (µm)
    DIAMETER = "diameter_um"
    #: Orientation angle (degrees)
    ORIENTATION_ANGLE = "orientation_angle"


class MicrostructureSummary:
    """Provides the summary of a microstructure simulation.

    Units are typically SI (m, kg, s, K). However, some of the following
    values do not use SI units. For more information, see the
    descriptions.
    """

    def __init__(
        self, input: MicrostructureInput, result: MicrostructureResult, user_data_path: str
    ) -> None:
        if not isinstance(input, MicrostructureInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        if not isinstance(result, MicrostructureResult):
            raise ValueError("Invalid result type passed to init, " + self.__class__.__name__)
        if not user_data_path or (user_data_path == ""):
            raise ValueError("Invalid user data path passed to init, " + self.__class__.__name__)
        self._input = input
        self._output_path = os.path.join(user_data_path, input.id)
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)
        self._xy_vtk = os.path.join(self._output_path, "xy.vtk")
        with open(self._xy_vtk, "wb") as xy_vtk:
            xy_vtk.write(result.xy_vtk)
        self._xz_vtk = os.path.join(self._output_path, "xz.vtk")
        with open(self._xz_vtk, "wb") as xz_vtk:
            xz_vtk.write(result.xz_vtk)
        self._yz_vtk = os.path.join(self._output_path, "yz.vtk")
        with open(self._yz_vtk, "wb") as yz_vtk:
            yz_vtk.write(result.yz_vtk)

        self._xy_circle_equivalence = MicrostructureSummary._circle_equivalence_frame(
            result.xy_circle_equivalence
        )
        self._xz_circle_equivalence = MicrostructureSummary._circle_equivalence_frame(
            result.xz_circle_equivalence
        )
        self._yz_circle_equivalence = MicrostructureSummary._circle_equivalence_frame(
            result.yz_circle_equivalence
        )
        self._xy_average_grain_size = MicrostructureSummary._average_grain_size(
            self._xy_circle_equivalence
        )
        self._xz_average_grain_size = MicrostructureSummary._average_grain_size(
            self._xz_circle_equivalence
        )
        self._yz_average_grain_size = MicrostructureSummary._average_grain_size(
            self._yz_circle_equivalence
        )

    @property
    def input(self):
        """Simulation input.

        For more information, see the :class:`MicrostructureInput` class.
        """
        return self._input

    @property
    def xy_vtk(self) -> str:
        """Path to the VTK file containing the 2-D grain structure data in the
        XY plane."""
        return self._xy_vtk

    @property
    def xz_vtk(self) -> str:
        """Path to the VTK file containing the 2-D grain structure data in the
        XZ plane."""
        return self._xz_vtk

    @property
    def yz_vtk(self) -> str:
        """Path to the VTK file containing the 2-D grain structure data in the
        YZ plane."""
        return self._yz_vtk

    @property
    def xy_circle_equivalence(self) -> pd.DataFrame:
        """Circle equivalence data for the XY plane.

        For data frame column names, see the :class:`CircleEquivalenceColumnNames` class.
        """
        return self._xy_circle_equivalence

    @property
    def xz_circle_equivalence(self) -> pd.DataFrame:
        """Circle equivalence data forthe  XZ plane.

        For data frame column names, see the :class:`CircleEquivalenceColumnNames` class.
        """
        return self._xz_circle_equivalence

    @property
    def yz_circle_equivalence(self) -> pd.DataFrame:
        """Circle equivalence data for the YZ plane.

        For data frame column names, see the :class:`CircleEquivalenceColumnNames` class.
        """
        return self._yz_circle_equivalence

    @property
    def xy_average_grain_size(self) -> float:
        """Average grain size (µm) for the XY plane."""
        return self._xy_average_grain_size

    @property
    def xz_average_grain_size(self) -> float:
        """Average grain size (µm) for the XZ plane."""
        return self._xz_average_grain_size

    @property
    def yz_average_grain_size(self) -> float:
        """Average grain size (µm) for the YZ plane."""
        return self._yz_average_grain_size

    @staticmethod
    def _circle_equivalence_frame(src: RepeatedCompositeFieldContainer) -> pd.DataFrame:
        d = {}
        d[CircleEquivalenceColumnNames.GRAIN_NUMBER] = np.asarray([x.grain_number for x in src])
        d[CircleEquivalenceColumnNames.AREA_FRACTION] = np.asarray([x.area_fraction for x in src])
        d[CircleEquivalenceColumnNames.DIAMETER] = np.asarray([x.diameter_um for x in src])
        d[CircleEquivalenceColumnNames.ORIENTATION_ANGLE] = np.asarray(
            [math.degrees(x.orientation_angle) for x in src]
        )
        return pd.DataFrame(d)

    @staticmethod
    def _average_grain_size(df: pd.DataFrame) -> float:
        """Calculate the average grain size (µm) for a given plane.

        Parameters
        ----------
        df : pd.DataFrame
            Data frame containing circle equivalence data for a given plane.

        Returns
        -------
        float
            Average grain size (µm).
        """

        return (
            df[CircleEquivalenceColumnNames.DIAMETER]
            * df[CircleEquivalenceColumnNames.AREA_FRACTION]
        ).sum()

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
