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
"""Provides input and result summary containers for microstructure 3D simulations."""
import math
import os

from ansys.api.additive.v0.additive_domain_pb2 import (
    Microstructure3DInput as Microstructure3DInputMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import Microstructure3DResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.core import misc
from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.microstructure import Microstructure2DResult


class Microstructure3DInput:
    """Provides input parameters for 3D microstructure simulation.

    Units are SI (m, kg, s, K) unless otherwise noted.

    .. warning::
        Beta Features Disclaimer

        * 3D microstructure simulation is a beta feature and requires ``enable_beta_features=True``
          when creating the :class:`Additive` client.
        * Beta features are considered unreleased and have not been fully tested nor
          fully validated. The results are not guaranteed by Ansys, Inc. (Ansys) to be
          correct. You assume the risk of using beta features.
        * At its discretion, Ansys may release, change, or withdraw beta features
          in future revisions.
        * Beta features are not subject to the Ansys Class 3 error reporting system.
          Ansys makes no commitment to resolve defects reported against beta features;
          however, your feedback will help us improve the quality of the product.
        * Ansys does not guarantee that database and/or input files used with beta
          features will run successfully from version to version of the software, nor
          with the final released version of the features. You may need to modify the
          database and/or input files before running them on other versions.
        * Documentation for beta features is called beta documentation, and it may
          not be written to the same standard as documentation for released features.
          Beta documentation may not be complete at the time of product release.
          At its discretion, Ansys may add, change, or delete beta documentation
          at any time.
    """

    DEFAULT_POSITION_COORDINATE = 0
    """Default X, Y, Z, position coordinate (m)."""
    MIN_POSITION_COORDINATE = 0
    """Minimum X, Y, Z, position coordinate (m)."""
    MAX_POSITION_COORDINATE = 10
    """Maximum X, Y, Z, position coordinate (m)."""
    DEFAULT_SAMPLE_SIZE = 0.1e-3
    """Default sample size in each dimension (m)."""
    MIN_SAMPLE_SIZE = 15e-6
    """Minimum sample size in each dimension (m)."""
    MAX_SAMPLE_SIZE = 0.5e-3
    """Maximum sample size in each dimension (m)."""
    DEFAULT_RUN_INITIAL_MICROSTRUCTURE = True
    """Default flag value indicating whether to run the initial microstructure conditions solver."""
    DEFAULT_USE_TRANSIENT_BULK_NUCLEATION = True
    """Default flag value indicating whether to use transient bulk nucleation rather than initial microstructure conditions."""  # noqa: E501
    DEFAULT_NUMBER_OF_RANDOM_NUCLEI = 8000
    """Default number of random nuclei to use in the initial microstructure conditions solver."""
    DEFAULT_MAX_NUCLEATION_DENSITY_BULK = int(20e12)
    """Default maximum nucleation density in the bulk (grains/m^3)."""

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
        calculate_initial_microstructure: bool = DEFAULT_RUN_INITIAL_MICROSTRUCTURE,
        use_transient_bulk_nucleation: bool = DEFAULT_USE_TRANSIENT_BULK_NUCLEATION,
        max_bulk_nucleation_density: int = DEFAULT_MAX_NUCLEATION_DENSITY_BULK,
        num_initial_random_nuclei: int = DEFAULT_NUMBER_OF_RANDOM_NUCLEI,
        machine: AdditiveMachine = AdditiveMachine(),
        material: AdditiveMaterial = AdditiveMaterial(),
    ):
        """Initialize a ``Microstructure3DInput`` object."""

        self.id = id
        self.sample_min_x = sample_min_x
        self.sample_min_y = sample_min_y
        self.sample_min_z = sample_min_z
        self.sample_size_x = sample_size_x
        self.sample_size_y = sample_size_y
        self.sample_size_z = sample_size_z
        self.calculate_initial_microstructure = calculate_initial_microstructure
        self.use_transient_bulk_nucleation = use_transient_bulk_nucleation
        self.max_bulk_nucleation_density = max_bulk_nucleation_density
        self.num_initial_random_nuclei = num_initial_random_nuclei
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
        if not isinstance(__o, Microstructure3DInput):
            return False
        return (
            self.id == __o.id
            and self.sample_min_x == __o.sample_min_x
            and self.sample_min_y == __o.sample_min_y
            and self.sample_min_z == __o.sample_min_z
            and self.sample_size_x == __o.sample_size_x
            and self.sample_size_y == __o.sample_size_y
            and self.sample_size_z == __o.sample_size_z
            and self.calculate_initial_microstructure == __o.calculate_initial_microstructure
            and self.use_transient_bulk_nucleation == __o.use_transient_bulk_nucleation
            and self.max_bulk_nucleation_density == __o.max_bulk_nucleation_density
            and self.num_initial_random_nuclei == __o.num_initial_random_nuclei
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
    def __validate_greater_than_zero(value, name):
        if math.isnan(value):
            raise ValueError("{} must be a number.".format(name))
        if value <= 0:
            raise ValueError("{} must be greater than zero.".format(name))

    @property
    def id(self) -> str:
        """User-provided ID for the simulation."""
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
        """
        return self._sample_size_x

    @sample_size_x.setter
    def sample_size_x(self, value: float):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "sample_size_x")
        self._sample_size_x = value

    @property
    def sample_size_y(self) -> float:
        """Size of the geometry sample in the y direction (m).

        Valid values are from the :obj:`MIN_SAMPLE_SIZE` value to the
        :obj:`MAX_SAMPLE_SIZE` value.
        """
        return self._sample_size_y

    @sample_size_y.setter
    def sample_size_y(self, value: float):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "sample_size_y")
        self._sample_size_y = value

    @property
    def sample_size_z(self) -> float:
        """Size of the geometry sample in the z direction (m).

        Valid values are from the :obj:`MIN_SAMPLE_SIZE` value to the
        :obj:`MAX_SAMPLE_SIZE` value.
        """
        return self._sample_size_z

    @sample_size_z.setter
    def sample_size_z(self, value: float):
        self.__validate_range(value, self.MIN_SAMPLE_SIZE, self.MAX_SAMPLE_SIZE, "sample_size_z")
        self._sample_size_z = value

    @property
    def calculate_initial_microstructure(self) -> bool:
        """Flag indicating if the initial microstructure conditions solver is to run.

        If ``True``, initial condition grain identifiers and Euler angles are calculated.
        If ``False``, the initial microstructure conditions solver is not be run.
        """
        return self._calculate_initial_microstructure

    @calculate_initial_microstructure.setter
    def calculate_initial_microstructure(self, value: bool):
        self._calculate_initial_microstructure = value

    @property
    def use_transient_bulk_nucleation(self) -> bool:
        """Flag indicating if nucleation is allowed in the bulk region of the meltpool.

        Nucleation rate is controlled by bulk nucleation density.
        If ``True``, bulk nucleation is enabled. if ``False``, bulk
        nucleation is disabled.
        """
        return self._use_transient_bulk_nucleation

    @use_transient_bulk_nucleation.setter
    def use_transient_bulk_nucleation(self, value: bool):
        self._use_transient_bulk_nucleation = value

    @property
    def max_bulk_nucleation_density(self) -> int:
        """Maximum nucleation density in the bulk (grains/m^3).

        If ``use_transient_bulk_nucleation=False``, this value is ignored.
        """
        return self._max_bulk_nucleation_density

    @max_bulk_nucleation_density.setter
    def max_bulk_nucleation_density(self, value: int):
        self.__validate_greater_than_zero(value, "max_bulk_nucleation_density")
        self._max_bulk_nucleation_density = value

    @property
    def num_initial_random_nuclei(self) -> int:
        """Number of random nuclei to use for the microstructure initial conditions.

        This value is used by the initial microstructure conditions solver.
        If ``use_transient_bulk_nucleation=True``, this value is ignored.
        """
        return self._num_initial_random_nuclei

    @num_initial_random_nuclei.setter
    def num_initial_random_nuclei(self, value: int):
        self.__validate_greater_than_zero(value, "num_initial_random_nuclei")
        self._num_initial_random_nuclei = value

    def _to_simulation_request(self) -> SimulationRequest:
        """Convert this object into a simulation request message."""
        input = Microstructure3DInputMessage(
            machine=self.machine._to_machine_message(),
            material=self.material._to_material_message(),
            x_origin=self.sample_min_x,
            y_origin=self.sample_min_y,
            z_origin=self.sample_min_z,
            x_length=self.sample_size_x,
            y_length=self.sample_size_y,
            z_length=self.sample_size_z,
            use_transient_bulk_nucleation=self.use_transient_bulk_nucleation,
            max_bulk_nucleation_density=float(self.max_bulk_nucleation_density),
            num_random_nuclei=self.num_initial_random_nuclei,
            run_initial_microstructure=self.calculate_initial_microstructure,
            # TODO: Add support for user provided initial microstructure data
            use_provided_initial_microstructure_data=False,
            # TODO: Add support for user provided thermal data
        )
        return SimulationRequest(id=self.id, microstructure_3d_input=input)


class Microstructure3DSummary:
    """Provides the summary of a 3D microstructure simulation."""

    _3D_GRAIN_VTK_NAME = "3d_grain_structure.vtk"

    def __init__(
        self, input: Microstructure3DInput, result: Microstructure3DResult, user_data_path: str
    ) -> None:
        """Initialize a ``Microstructure3DSummary`` object."""
        if not isinstance(input, Microstructure3DInput):
            raise ValueError("Invalid input type, " + self.__class__.__name__)
        if not isinstance(result, Microstructure3DResult):
            raise ValueError("Invalid result type, " + self.__class__.__name__)
        if not user_data_path or (user_data_path == ""):
            raise ValueError("Invalid user data path, " + self.__class__.__name__)
        self._input = input
        id = input.id if input.id else misc.short_uuid()
        outpath = os.path.join(user_data_path, id)
        os.makedirs(outpath, exist_ok=True)
        self._grain_3d_vtk = os.path.join(outpath, self._3D_GRAIN_VTK_NAME)
        with open(self._grain_3d_vtk, "wb") as f:
            f.write(result.three_d_vtk)
        self._2d_result = Microstructure2DResult(result.two_d_result, outpath)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in [x for x in self.__dict__ if x != "_2d_result"]:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        repr += f"xy_average_grain_size: {self.xy_average_grain_size}\n"
        repr += f"xz_average_grain_size: {self.xz_average_grain_size}\n"
        repr += f"yz_average_grain_size: {self.yz_average_grain_size}\n"
        return repr

    @property
    def input(self):
        """Simulation input.

        For more information, see the :class:`Microstructure3DInput` class.
        """
        return self._input

    @property
    def grain_3d_vtk(self) -> str:
        """Path to the VTK file containing the 3D grain structure data.

        The VTK file contains these scalar data sets" ``GrainNumber``, ``Phi0_(deg)``,
        ``Phi1_(deg)``, ``Phi2_(deg)``, and ``Temperatures``.
        """
        return self._grain_3d_vtk

    @property
    def xy_average_grain_size(self) -> float:
        """Average grain size (µm) for the XY plane."""
        return self._2d_result._xy_average_grain_size

    @property
    def xz_average_grain_size(self) -> float:
        """Average grain size (µm) for the XZ plane."""
        return self._2d_result._xz_average_grain_size

    @property
    def yz_average_grain_size(self) -> float:
        """Average grain size (µm) for the YZ plane."""
        return self._2d_result._yz_average_grain_size
