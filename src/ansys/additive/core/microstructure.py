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
"""Provides input and result summary containers for microstructure simulations."""
import math
import os

from ansys.api.additive.v0.additive_domain_pb2 import (
    MicrostructureInput as MicrostructureInputMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    MicrostructureResult as MicrostructureResultMessage,
)
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
from google.protobuf.internal.containers import RepeatedCompositeFieldContainer
import numpy as np
import pandas as pd

from ansys.additive.core import misc
from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.simulation_input_base import SimulationInputBase


class MicrostructureInput(SimulationInputBase):
    """Provides input parameters for microstructure simulation.

    Units are SI (m, kg, s, K) unless otherwise noted.
    """

    DEFAULT_POSITION_COORDINATE = 0
    """Default X, Y, Z, position coordinate (m)."""
    MIN_POSITION_COORDINATE = 0
    """Minimum X, Y, Z, position coordinate (m)."""
    MAX_POSITION_COORDINATE = 10
    """Maximum X, Y, Z, position coordinate (m)."""
    DEFAULT_SAMPLE_SIZE = 1.5e-3
    """Default sample size in each dimension (m)."""
    MIN_SAMPLE_SIZE = 0.001
    """Minimum sample size in each dimension (m)."""
    MAX_SAMPLE_SIZE = 0.01
    """Maximum sample size in each dimension (m)."""
    DEFAULT_SENSOR_DIMENSION = 5e-4
    """Default sensor dimension (m)."""
    MIN_SENSOR_DIMENSION = 1e-4
    """Minimum sensor dimension (m)."""
    MAX_SENSOR_DIMENSION = 1e-3
    """Maximum sensor dimension (m)."""
    MIN_XY_SIZE_CUSHION = 5e-4
    """Minimum cushion between sensor dimension and sample size in the X and Y dimensions (m)."""
    MIN_Z_SIZE_CUSHION = 1e-3
    """Minimum cushion between sensor dimension and sample size in the Z dimension (m)."""
    DEFAULT_USE_PROVIDED_THERMAL_PARAMETERS = False
    """Default flag value indicating whether to use user-provided thermal parameters."""
    DEFAULT_COOLING_RATE = 1e6
    """Default cooling rate (K/s)."""
    MIN_COOLING_RATE = 1e5
    """Minimum cooling rate (K/s)."""
    MAX_COOLING_RATE = 1e7
    """Maximum cooling rate (K/s)."""
    DEFAULT_THERMAL_GRADIENT = 1e7
    """Default thermal gradient (K/m)."""
    MIN_THERMAL_GRADIENT = 1e5
    """Minimum thermal gradient (K/m)."""
    MAX_THERMAL_GRADIENT = 1e8
    """Maximum thermal gradient (K/m)."""
    DEFAULT_MELT_POOL_WIDTH = 1.5e-4
    """Default melt pool width (m)."""
    MIN_MELT_POOL_WIDTH = 7.5e-5
    """Minimum melt pool width (m)."""
    MAX_MELT_POOL_WIDTH = 8e-4
    """Maximum melt pool width (m)."""
    DEFAULT_MELT_POOL_DEPTH = 1e-4
    """Default melt pool depth (m)."""
    MIN_MELT_POOL_DEPTH = 1.5e-5
    """Minimum melt pool depth (m)."""
    MAX_MELT_POOL_DEPTH = 8e-4
    """Maximum melt pool depth (m)."""
    DEFAULT_RANDOM_SEED = 0
    """The default random seed, which indicates that a random seed was not provided."""
    MIN_RANDOM_SEED = 1
    """Minimum random seed."""
    MAX_RANDOM_SEED = 2**32 - 1
    """Maximum random seed."""

    def __init__(
        self,
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
        """Initialize a ``MicrostructureInput`` object."""
        super().__init__()

        # we have a circular dependency here, so we validate sensor_dimension
        # and sample_size_* then assign them without calling the setters
        self.__validate_range(
            sensor_dimension,
            self.MIN_SENSOR_DIMENSION,
            self.MAX_SENSOR_DIMENSION,
            "sensor_dimension",
        )
        self.__validate_size(
            sample_size_x, sensor_dimension, self.MIN_XY_SIZE_CUSHION, "sample_size_x"
        )
        self.__validate_size(
            sample_size_y, sensor_dimension, self.MIN_XY_SIZE_CUSHION, "sample_size_y"
        )
        self.__validate_size(
            sample_size_z, sensor_dimension, self.MIN_Z_SIZE_CUSHION, "sample_size_z"
        )
        self._sensor_dimension = sensor_dimension
        self._sample_size_x = sample_size_x
        self._sample_size_y = sample_size_y
        self._sample_size_z = sample_size_z

        # use setters for remaining properties
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
        if math.isnan(value):
            raise ValueError("{} must be a number.".format(name))
        if value < min or value > max:
            raise ValueError("{} must be between {} and {}.".format(name, min, max))

    @staticmethod
    def __validate_size(size_value, sensor_value, cushion, name):
        if math.isnan(size_value):
            raise ValueError("{} must be a number.".format(name))
        if size_value - sensor_value < cushion:
            raise ValueError(
                "{} must be at least {} larger than sensor_dimension.".format(name, cushion)
            )

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
        """Minimum x coordinate of the geometry sample (m).

        Valid values are from the :obj:`MIN_POSITION_COORDINATE` value to
        the :obj:`MAX_POSITION_COORDINATE` value.
        """
        return self._sample_min_x

    @sample_min_x.setter
    def sample_min_x(self, value: float):
        self.__validate_range(
            value, self.MIN_POSITION_COORDINATE, self.MAX_POSITION_COORDINATE, "sample_min_x"
        )
        self._sample_min_x = value

    @property
    def sample_min_y(self) -> float:
        """Minimum y coordinate of the geometry sample (m).

        Valid values are from the :obj:`MIN_POSITION_COORDINATE` value to the
        :obj:`MAX_POSITION_COORDINATE` value.
        """
        return self._sample_min_y

    @sample_min_y.setter
    def sample_min_y(self, value: float):
        self.__validate_range(
            value, self.MIN_POSITION_COORDINATE, self.MAX_POSITION_COORDINATE, "sample_min_y"
        )
        self._sample_min_y = value

    @property
    def sample_min_z(self) -> float:
        """Minimum z coordinate of the geometry sample (m).

        Valid values are from the :obj:`MIN_POSITION_COORDINATE` value to the
        :obj:`MAX_POSITION_COORDINATE` value.
        """
        return self._sample_min_z

    @sample_min_z.setter
    def sample_min_z(self, value: float):
        self.__validate_range(
            value, self.MIN_POSITION_COORDINATE, self.MAX_POSITION_COORDINATE, "sample_min_z"
        )
        self._sample_min_z = value

    @property
    def sample_size_x(self) -> float:
        """Size of the geometry sample in the x direction (m).

        Valid values are from the :obj:`MIN_SAMPLE_SIZE` value to the
        :obj:`MAX_SAMPLE_SIZE` value.
        When setting the```sample_size_x`` parameter, the value must be greater than the
        ``sensor_dimension`` value plus the :obj:`MIN_XY_SIZE_CUSHION` value.
        """
        return self._sample_size_x

    @sample_size_x.setter
    def sample_size_x(self, value: float):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "sample_size_x")
        self.__validate_size(
            value, self.sensor_dimension, self.MIN_XY_SIZE_CUSHION, "sample_size_x"
        )
        self._sample_size_x = value

    @property
    def sample_size_y(self) -> float:
        """Size of the geometry sample in the y direction (m).

        Valid values are from the :obj:`MIN_SAMPLE_SIZE` value to the
        :obj:`MAX_SAMPLE_SIZE` value.
        When setting the ``sample_size_y`` parameter, the value must be greater than the
        ``sensor_dimension`` value plus the :obj:`MIN_XY_SIZE_CUSHION` value.
        """
        return self._sample_size_y

    @sample_size_y.setter
    def sample_size_y(self, value: float):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "sample_size_y")
        self.__validate_size(
            value, self.sensor_dimension, self.MIN_XY_SIZE_CUSHION, "sample_size_y"
        )
        self._sample_size_y = value

    @property
    def sample_size_z(self) -> float:
        """Size of the geometry sample in the z direction (m).

        Valid values are from the :obj:`MIN_SAMPLE_SIZE` value to the
        :obj:`MAX_SAMPLE_SIZE` value.
        When setting the ``sample_size_y`` parameter, the value must be greater than the
        ``sensor_dimension`` value plus the :obj:`MIN_XY_SIZE_CUSHION` value.
        """
        return self._sample_size_z

    @sample_size_z.setter
    def sample_size_z(self, value: float):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "sample_size_z")
        self.__validate_size(value, self.sensor_dimension, self.MIN_Z_SIZE_CUSHION, "sample_size_z")
        self._sample_size_z = value

    @property
    def sensor_dimension(self) -> float:
        """Dimension of the sensor (m).

        Valid values are from the :obj:`MIN_SENSOR_DIMENSION` value to the
        :obj:`MAX_SENSOR_DIMENSION` value.
        """
        return self._sensor_dimension

    @sensor_dimension.setter
    def sensor_dimension(self, value: float):
        self.__validate_range(
            value, self.MIN_SENSOR_DIMENSION, self.MAX_SENSOR_DIMENSION, "sensor_dimension"
        )
        size_errors = ""
        try:
            self.__validate_size(
                self.sample_size_x, value, self.MIN_XY_SIZE_CUSHION, "sample_size_x"
            )
        except ValueError as e:
            size_errors += str(e) + "\n"
        try:
            self.__validate_size(
                self.sample_size_y, value, self.MIN_XY_SIZE_CUSHION, "sample_size_y"
            )
        except ValueError as e:
            size_errors += str(e) + "\n"
        try:
            self.__validate_size(
                self.sample_size_z, value, self.MIN_Z_SIZE_CUSHION, "sample_size_z"
            )
        except ValueError as e:
            size_errors += str(e) + "\n"
        if size_errors:
            raise ValueError(size_errors)

        self._sensor_dimension = value

    @property
    def use_provided_thermal_parameters(self) -> bool:
        """Flag indicating if the ``cooling_rate``, ``thermal_gradient``, ``melt_pool_depth``, and ``melt_pool_width`` parameters have been provided by the user.

        If the value is ``False``, these values
        will be calculated. Default is ``False``.
        """  # noqa: E501
        return self._use_provided_thermal_parameters

    @use_provided_thermal_parameters.setter
    def use_provided_thermal_parameters(self, value: bool):
        self._use_provided_thermal_parameters = value

    @property
    def cooling_rate(self) -> float:
        """Material cooling rate (K/s).

        Valid values are from the :obj:`MIN_COOLING_RATE` value to the
        :obj:`MAX_COOLING_RATE` value.
        """
        return self._cooling_rate

    @cooling_rate.setter
    def cooling_rate(self, value: float):
        self.__validate_range(value, self.MIN_COOLING_RATE, self.MAX_COOLING_RATE, "cooling_rate")
        self._cooling_rate = value

    @property
    def thermal_gradient(self) -> float:
        """Material thermal gradient (K/m).

        Valid values are from the :obj:`MIN_THERMAL_GRADIENT` value to the
        :obj:`MAX_THERMAL_GRADIENT` value.
        """
        return self._thermal_gradient

    @thermal_gradient.setter
    def thermal_gradient(self, value: float):
        self.__validate_range(
            value, self.MIN_THERMAL_GRADIENT, self.MAX_THERMAL_GRADIENT, "thermal_gradient"
        )
        self._thermal_gradient = value

    @property
    def melt_pool_width(self) -> float:
        """Melt pool width (m).

        This is the width of the melt pool measured at the top of the powder layer.

        Valid values are from the :obj:`MIN_MELT_POOL_WIDTH` value to the
        :obj:`MAX_MELT_POOL_WIDTH` value.
        """
        return self._melt_pool_width

    @melt_pool_width.setter
    def melt_pool_width(self, value: float):
        self.__validate_range(
            value, self.MIN_MELT_POOL_WIDTH, self.MAX_MELT_POOL_WIDTH, "melt_pool_width"
        )
        self._melt_pool_width = value

    @property
    def melt_pool_depth(self) -> float:
        """Melt pool depth (m).

        This is the depth of the melt pool as measured from the top of the powder layer.

        Valid values are from the :obj:`MIN_MELT_POOL_DEPTH` value to the
        :obj:`MAX_MELT_POOL_DEPTH` value.
        """
        return self._melt_pool_depth

    @melt_pool_depth.setter
    def melt_pool_depth(self, value: float):
        self.__validate_range(
            value, self.MIN_MELT_POOL_DEPTH, self.MAX_MELT_POOL_DEPTH, "melt_pool_depth"
        )
        self._melt_pool_depth = value

    @property
    def random_seed(self) -> int:
        """Random seed for the simulation.

        Valid values are from the :obj:`MIN_RANDOM_SEED` value to the
        :obj:`MAX_RANDOM_SEED` value.
        """
        return self._random_seed

    @random_seed.setter
    def random_seed(self, value: int):
        self.__validate_range(value, self.MIN_RANDOM_SEED, self.MAX_RANDOM_SEED, "random_seed")
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

    GRAIN_NUMBER = "grain_number"
    """Grain number."""
    AREA_FRACTION = "area_fraction"
    """Area fraction for grain."""
    DIAMETER = "diameter_um"
    """Grain diameter (µm)."""
    ORIENTATION_ANGLE = "orientation_angle"
    """Orientation angle (degrees)."""


class MicrostructureSummary:
    """Provides the summary of a microstructure simulation."""

    def __init__(
        self, input: MicrostructureInput, result: MicrostructureResultMessage, user_data_path: str
    ) -> None:
        """Initialize a ``MicrostructureSummary`` object."""
        if not isinstance(input, MicrostructureInput):
            raise ValueError("Invalid input type passed to init, " + self.__class__.__name__)
        if not isinstance(result, MicrostructureResultMessage):
            raise ValueError("Invalid result type passed to init, " + self.__class__.__name__)
        if not user_data_path:
            raise ValueError("Invalid user data path, " + self.__class__.__name__)
        self._input = input
        id = input.id if input.id else misc.short_uuid()
        outpath = os.path.join(user_data_path, id)
        self._result = Microstructure2DResult(result, outpath)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in [x for x in self.__dict__ if x != "_result"]:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        repr += self._result.__repr__()
        return repr

    @property
    def input(self):
        """Simulation input.

        For more information, see the :class:`MicrostructureInput` class.
        """
        return self._input

    @property
    def xy_vtk(self) -> str:
        """Path to the VTK file containing the 2D grain structure data in the XY plane.

        The VTK file contains these scalar data sets: ``GrainBoundaries``, ``Orientation_(deg)``, and
        ``GrainNumber``.
        """
        return self._result._xy_vtk

    @property
    def xz_vtk(self) -> str:
        """Path to the VTK file containing the 2D grain structure data in the XZ plane.

        The VTK file contains these scalar data sets: ``GrainBoundaries``,
        ``Orientation_(deg)``, and ``GrainNumber``.
        """
        return self._result._xz_vtk

    @property
    def yz_vtk(self) -> str:
        """Path to the VTK file containing the 2D grain structure data in the YZ plane.

        The VTK file contains these scalar data sets: ``GrainBoundaries``,
        ``Orientation_(deg)``, and ``GrainNumber``.
        """
        return self._result._yz_vtk

    @property
    def xy_circle_equivalence(self) -> pd.DataFrame:
        """Circle equivalence data for the XY plane.

        For data frame column names, see the :class:`CircleEquivalenceColumnNames` class.
        """
        return self._result._xy_circle_equivalence

    @property
    def xz_circle_equivalence(self) -> pd.DataFrame:
        """Circle equivalence data for the XZ plane.

        For data frame column names, see the :class:`CircleEquivalenceColumnNames` class.
        """
        return self._result._xz_circle_equivalence

    @property
    def yz_circle_equivalence(self) -> pd.DataFrame:
        """Circle equivalence data for the YZ plane.

        For data frame column names, see the :class:`CircleEquivalenceColumnNames` class.
        """
        return self._result._yz_circle_equivalence

    @property
    def xy_average_grain_size(self) -> float:
        """Average grain size (µm) for the XY plane."""
        return self._result._xy_average_grain_size

    @property
    def xz_average_grain_size(self) -> float:
        """Average grain size (µm) for the XZ plane."""
        return self._result._xz_average_grain_size

    @property
    def yz_average_grain_size(self) -> float:
        """Average grain size (µm) for the YZ plane."""
        return self._result._yz_average_grain_size

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


class Microstructure2DResult:
    """Provides the results of a 2D microstructure simulation."""

    def __init__(self, msg: MicrostructureResultMessage, output_data_path: str) -> None:
        """Initialize a ``Microstructure2DResult`` object."""
        if not isinstance(msg, MicrostructureResultMessage):
            raise ValueError("Invalid msg parameter, " + self.__class__.__name__)
        if not output_data_path:
            raise ValueError("Invalid output data path, " + self.__class__.__name__)

        if not os.path.exists(output_data_path):
            os.makedirs(output_data_path)
        self._xy_vtk = os.path.join(output_data_path, "xy.vtk")
        with open(self._xy_vtk, "wb") as xy_vtk:
            xy_vtk.write(msg.xy_vtk)
        self._xz_vtk = os.path.join(output_data_path, "xz.vtk")
        with open(self._xz_vtk, "wb") as xz_vtk:
            xz_vtk.write(msg.xz_vtk)
        self._yz_vtk = os.path.join(output_data_path, "yz.vtk")
        with open(self._yz_vtk, "wb") as yz_vtk:
            yz_vtk.write(msg.yz_vtk)

        self._xy_circle_equivalence = MicrostructureSummary._circle_equivalence_frame(
            msg.xy_circle_equivalence
        )
        self._xz_circle_equivalence = MicrostructureSummary._circle_equivalence_frame(
            msg.xz_circle_equivalence
        )
        self._yz_circle_equivalence = MicrostructureSummary._circle_equivalence_frame(
            msg.yz_circle_equivalence
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

    def __repr__(self):
        repr = ""
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
