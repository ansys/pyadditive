# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import math
import os

from ansys.api.additive.v0.additive_domain_pb2 import (
    MicrostructureInput as MicrostructureInputMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import GrainStatistics
from ansys.api.additive.v0.additive_domain_pb2 import MicrostructureResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
import numpy as np

from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial


class MicrostructureInput:
    """Input parameters for microstructure simulation.

    id: string
        Simulation identifier.
    machine: AdditiveMachine
        Machine related parameters.
    material: AdditiveMaterial
        Material used during simulation.
    cube_min_x: float
        Sample minimum x coordinate value (m), default 0.
    cube_min_y: float
        Sample minimum y coordinate value (m), default 0.
    cube_min_z: float
        Sample minimum z coordinate value (m), default 0.
    cube_size_x: float
        Sample size in x dimension (m), valid values: 0.001 to 0.01, default 0.0015.
    cube_size_y: float
        Sample size in y dimension (m), valid values: 0.001 to 0.01, default 0.0015.
    cube_size_z: float
        Sample size in z dimension (m), valid values: 0.001 to 0.01, default 0.0015.
    sensor_dimension: float
        Sensor dimension (m), valid values: 0.0001 to 0.001, default 0.0005.
    use_provided_thermal_parameters: bool
        Indicates that cooling_rate, thermal_gradient, melt_pool* have been provided by user,
        default False, meaning values will be calculated.
    cooling_rate: float, optional
        Cooling rate (°K/s), valid values: 1e5 to 1e7, default 1e6.
    thermal_gradient: float, optional
        Thermal gradient (°K/m), valid values: 1e5 to 1e8, default 1e7.
    melt_pool_width: float, optional
        Width of melt pool for a single bead scan, valid values: 7.5e-5 to 8e-4, default 1.5e-4.
    melt_pool_depth: float, optional
        Depth of melt pool for a single bead scan, valid values: 1.5e-5 to 8e-4, default 1e-4.
    random_seed: int, optional
        Seed used for nucleation calculations, default None.

    """

    def __init__(self, **kwargs):
        self.id = ""
        self.cube_min_x = 0
        self.cube_min_y = 0
        self.cube_min_z = 0
        self.cube_size_x = 1.5e-3
        self.cube_size_y = 1.5e-3
        self.cube_size_z = 1.5e-3
        self.sensor_dimension = 5e-4
        self.use_provided_thermal_parameters = False
        self.cooling_rate = 1e6
        self.thermal_gradient = 1e7
        self.melt_pool_width = 1.5e-4
        self.melt_pool_depth = 1e-4
        self.random_seed = None
        self.machine = AdditiveMachine()
        self.material = AdditiveMaterial()
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            if k == "machine" or k == "material":
                repr += "\n" + k + ": " + str(getattr(self, k))
            else:
                repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def _to_simulation_request(self) -> SimulationRequest:
        """Convert this object into a simulation request message"""
        input = MicrostructureInputMessage(
            machine=self.machine._to_machine_message(),
            material=self.material._to_material_message(),
            cube_min_x=self.cube_min_x,
            cube_min_y=self.cube_min_y,
            cube_min_z=self.cube_min_z,
            cube_size_x=self.cube_size_x,
            cube_size_y=self.cube_size_y,
            cube_size_z=self.cube_size_z,
            sensor_dimension=self.sensor_dimension,
            use_provided_thermal_parameters=self.use_provided_thermal_parameters,
            cooling_rate=self.cooling_rate,
            thermal_gradient=self.thermal_gradient,
            melt_pool_width=self.melt_pool_width,
            melt_pool_depth=self.melt_pool_depth,
            use_random_seed=(self.random_seed != None),
            random_seed=self.random_seed,
        )
        return SimulationRequest(id=self.id, microstructure_input=input)


class MicrostructureSummary:
    """Summary of a microstructure simulation.

    Units are typically SI (m, kg, s, K), however, some of the values listed
    below do not use SI units. See descriptions for details.

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
        if not os.path.exists(self._output_path):  # pragma: no cover
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

        self._xy_circle_equivalence = MicrostructureSummary._get_equivalence_dict(
            result.xy_circle_equivalence
        )
        self._xz_circle_equivalence = MicrostructureSummary._get_equivalence_dict(
            result.xz_circle_equivalence
        )
        self._yz_circle_equivalence = MicrostructureSummary._get_equivalence_dict(
            result.yz_circle_equivalence
        )

    @property
    def input(self):
        """Simulation input, see :class:`MicrostructureInput`."""
        return self._input

    @property
    def xy_vtk(self) -> str:
        """Path to VTK file containing 2-D grain structure data in XY plane."""
        return self._xy_vtk

    @property
    def xz_vtk(self) -> str:
        """Path to VTK file containing 2-D grain structure data in XZ plane."""
        return self._xz_vtk

    @property
    def yz_vtk(self) -> str:
        """Path to VTK file containing 2-D grain structure data in YZ plane."""
        return self._yz_vtk

    @property
    def xy_circle_equivalence(self) -> dict[str, np.array(float)]:
        """
        Circle equivalence data for XY plane.

        Dictionary keys include ``grain_number``, ``area_fraction``, ``diameter_um``
        and ``orientation_angle``. The ``diameter_um`` values are in microns and
        ``orientation_angle`` values are in degrees.

        """
        return self._xy_circle_equivalence

    @property
    def xz_circle_equivalence(self) -> dict[str, np.array(float)]:
        """
        Circle equivalence data for XZ plane.

        Dictionary keys include ``grain_number``, ``area_fraction``, ``diameter_um``
        and ``orientation_angle``. The ``diameter_um`` values are in microns and
        ``orientation_angle`` values are in degrees.

        """
        return self._xz_circle_equivalence

    @property
    def yz_circle_equivalence(self) -> dict[str, np.array(float)]:
        """
        Circle equivalence data for YZ plane.

        Dictionary keys include ``grain_number``, ``area_fraction``, ``diameter_um``
        and ``orientation_angle``. The ``diameter_um`` values are in microns and
        ``orientation_angle`` values are in degrees.

        """
        return self._yz_circle_equivalence

    @staticmethod
    def _get_equivalence_dict(src: list[GrainStatistics]) -> dict:
        d = {}
        d["grain_number"] = np.asarray([x.grain_number for x in src])
        d["area_fraction"] = np.asarray([x.area_fraction for x in src])
        d["diameter_um"] = np.asarray([x.diameter_um for x in src])
        d["orientation_angle"] = np.asarray([math.degrees(x.orientation_angle) for x in src])
        return d

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
