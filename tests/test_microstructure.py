# Copyright (C) 2022 - 2025 ANSYS, Inc. and/or its affiliates.
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

import math
import os
import shutil
import tempfile

import pytest

from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.microstructure import (
    MicrostructureInput,
    MicrostructureSummary,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    GrainStatistics,
    MicrostructureResult,
)
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.core.simulation import SimulationStatus

from . import test_utils


def test_MicrostructureSummary_init_returns_expected_value():
    # arrange
    logs = "log messages"
    user_data_path = os.path.join(tempfile.gettempdir(), "microstructure_summary_init")
    if not os.path.exists(user_data_path):
        os.makedirs(user_data_path)
    input = MicrostructureInput()
    xy_vtk_bytes = bytes(range(3))
    xz_vtk_bytes = bytes(range(4, 6))
    yz_vtk_bytes = bytes(range(7, 9))
    xy_stats = GrainStatistics(
        grain_number=1, area_fraction=2, diameter_um=3, orientation_angle=4
    )
    xz_stats = GrainStatistics(
        grain_number=5, area_fraction=6, diameter_um=7, orientation_angle=8
    )
    yz_stats = GrainStatistics(
        grain_number=9, area_fraction=10, diameter_um=11, orientation_angle=12
    )
    result = MicrostructureResult(
        xy_vtk=xy_vtk_bytes, xz_vtk=xz_vtk_bytes, yz_vtk=yz_vtk_bytes
    )
    result.xy_circle_equivalence.append(xy_stats)
    result.xz_circle_equivalence.append(xz_stats)
    result.yz_circle_equivalence.append(yz_stats)

    # act
    summary = MicrostructureSummary(input, result, logs, user_data_path)

    # assert
    assert isinstance(summary, MicrostructureSummary)
    assert input == summary.input
    assert summary.xy_vtk == os.path.join(user_data_path, input.id, "xy.vtk")
    assert os.path.exists(summary.xy_vtk)
    assert summary.xz_vtk == os.path.join(user_data_path, input.id, "xz.vtk")
    assert os.path.exists(summary.xz_vtk)
    assert summary.yz_vtk == os.path.join(user_data_path, input.id, "yz.vtk")
    assert os.path.exists(summary.yz_vtk)
    assert summary.xy_circle_equivalence["grain_number"][0] == 1
    assert summary.xy_circle_equivalence["area_fraction"][0] == 2
    assert summary.xy_circle_equivalence["diameter_um"][0] == 3
    assert summary.xy_circle_equivalence["orientation_angle"][0] == math.degrees(4)
    assert summary.xz_circle_equivalence["grain_number"][0] == 5
    assert summary.xz_circle_equivalence["area_fraction"][0] == 6
    assert summary.xz_circle_equivalence["diameter_um"][0] == 7
    assert summary.xz_circle_equivalence["orientation_angle"][0] == math.degrees(8)
    assert summary.yz_circle_equivalence["grain_number"][0] == 9
    assert summary.yz_circle_equivalence["area_fraction"][0] == 10
    assert summary.yz_circle_equivalence["diameter_um"][0] == 11
    assert summary.yz_circle_equivalence["orientation_angle"][0] == math.degrees(12)
    assert summary.xy_average_grain_size == 6
    assert summary.xz_average_grain_size == 42
    assert summary.yz_average_grain_size == 110
    assert summary.logs == logs
    assert summary.status == SimulationStatus.COMPLETED

    # clean up
    shutil.rmtree(user_data_path)


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        MicrostructureResult(),
    ],
)
def test_MicrostructureSummary_init_raises_exception_for_invalid_input_type(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid input type"):
        MicrostructureSummary(invalid_obj, MicrostructureResult(), "logs", ".")


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        MicrostructureInput(),
    ],
)
def test_MicrostructureSummary_init_raises_exception_for_invalid_result_type(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid result type"):
        MicrostructureSummary(MicrostructureInput(), invalid_obj, "logs", ".")


@pytest.mark.parametrize(
    "invalid_path",
    [
        "",
        None,
    ],
)
def test_MicrostructureSummary_init_raises_exception_for_invalid_path(
    invalid_path,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid user data path"):
        MicrostructureSummary(
            MicrostructureInput(), MicrostructureResult(), "logs", invalid_path
        )


def test_MicrostructureSummary_init_raises_exception_for_invalid_logs_type():
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid logs type"):
        MicrostructureSummary(
            MicrostructureInput(), MicrostructureResult(), b"logs", "."
        )


def test_MicrostructureInput_init_creates_default_object():
    # arrange, act
    input = MicrostructureInput()

    # assert
    assert input.id
    assert input.machine.laser_power == 195
    assert input.material.name == ""
    assert input.sample_min_x == 0
    assert input.sample_min_y == 0
    assert input.sample_min_z == 0
    assert input.sample_size_x == 0.0015
    assert input.sample_size_y == 0.0015
    assert input.sample_size_z == 0.0015
    assert input.sensor_dimension == 0.0005
    assert input.use_provided_thermal_parameters is False
    assert input.cooling_rate == 1e6
    assert input.thermal_gradient == 1e7
    assert input.melt_pool_width == 1.5e-4
    assert input.melt_pool_depth == 1e-4
    assert input.random_seed == 0


def test_MicrostructureInput_init_with_parameters_creates_expected_object():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")

    # act
    input = MicrostructureInput(
        machine=machine,
        material=material,
        sample_min_x=1,
        sample_min_y=2,
        sample_min_z=3,
        sample_size_x=0.001,
        sample_size_y=0.002,
        sample_size_z=0.003,
        sensor_dimension=1e-4,
        use_provided_thermal_parameters=True,
        cooling_rate=8e6,
        thermal_gradient=9e6,
        melt_pool_width=10e-5,
        melt_pool_depth=11e-5,
        random_seed=12,
    )

    # assert
    assert input.id
    assert input.machine.laser_power == 99
    assert input.material.name == "vibranium"
    assert input.sample_min_x == 1
    assert input.sample_min_y == 2
    assert input.sample_min_z == 3
    assert input.sample_size_x == 0.001
    assert input.sample_size_y == 0.002
    assert input.sample_size_z == 0.003
    assert input.sensor_dimension == 1e-4
    assert input.use_provided_thermal_parameters
    assert input.cooling_rate == 8e6
    assert input.thermal_gradient == 9e6
    assert input.melt_pool_width == 10e-5
    assert input.melt_pool_depth == 11e-5
    assert input.random_seed == 12


def test_MicrostructureInput_to_simulation_request_returns_expected_object():
    # arrange
    input = MicrostructureInput()

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == input.id
    ms_input = request.microstructure_input
    assert ms_input.cube_min_x == 0
    assert ms_input.cube_min_y == 0
    assert ms_input.cube_min_z == 0
    assert ms_input.cube_size_x == 0.0015
    assert ms_input.cube_size_y == 0.0015
    assert ms_input.cube_size_z == 0.0015
    assert ms_input.sensor_dimension == 0.0005
    assert ms_input.use_provided_thermal_parameters is False
    assert ms_input.cooling_rate == 1e6
    assert ms_input.thermal_gradient == 1e7
    assert ms_input.melt_pool_width == 1.5e-4
    assert ms_input.melt_pool_depth == 1e-4
    assert ms_input.use_random_seed is False
    assert ms_input.random_seed == 0


def test_MicrostructureInput_to_simulation_request_assigns_values():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")
    input = MicrostructureInput(
        machine=machine,
        material=material,
        sample_min_x=1,
        sample_min_y=2,
        sample_min_z=3,
        sample_size_x=0.001,
        sample_size_y=0.002,
        sample_size_z=0.003,
        sensor_dimension=1e-4,
        use_provided_thermal_parameters=True,
        cooling_rate=8e6,
        thermal_gradient=9e6,
        melt_pool_width=10e-5,
        melt_pool_depth=11e-5,
        random_seed=12,
    )

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == input.id
    ms_input = request.microstructure_input
    assert ms_input.machine.laser_power == 99
    assert ms_input.material.name == "vibranium"
    assert ms_input.cube_min_x == 1
    assert ms_input.cube_min_y == 2
    assert ms_input.cube_min_z == 3
    assert ms_input.cube_size_x == 0.001
    assert ms_input.cube_size_y == 0.002
    assert ms_input.cube_size_z == 0.003
    assert ms_input.sensor_dimension == 1e-4
    assert ms_input.use_provided_thermal_parameters
    assert ms_input.cooling_rate == 8e6
    assert ms_input.thermal_gradient == 9e6
    assert ms_input.melt_pool_width == 10e-5
    assert ms_input.melt_pool_depth == 11e-5
    assert ms_input.use_random_seed
    assert ms_input.random_seed == 12


def test_MicrostructureInput_setters_raise_ValueError_for_values_out_of_range():
    # arrange
    input = MicrostructureInput()

    # act & assert
    with pytest.raises(ValueError):
        input.sample_min_x = -1
    with pytest.raises(ValueError):
        input.sample_min_x = 11
    with pytest.raises(ValueError):
        input.sample_min_y = -1
    with pytest.raises(ValueError):
        input.sample_min_y = 11
    with pytest.raises(ValueError):
        input.sample_min_z = -1
    with pytest.raises(ValueError):
        input.sample_min_z = 11
    with pytest.raises(ValueError):
        input.sensor_dimension = 0.9e-4
    with pytest.raises(ValueError):
        input.sensor_dimension = 1.1e-3
    with pytest.raises(ValueError):
        input.sample_size_x = 0.0009
    with pytest.raises(ValueError):
        input.sample_size_x = 0.011
    with pytest.raises(ValueError):
        input.sample_size_y = 0.0009
    with pytest.raises(ValueError):
        input.sample_size_y = 0.011
    with pytest.raises(ValueError):
        input.sample_size_z = 0.0009
    with pytest.raises(ValueError):
        input.sample_size_z = 0.011
    with pytest.raises(ValueError):
        input.cooling_rate = 0.9e5
    with pytest.raises(ValueError):
        input.cooling_rate = 1.1e7
    with pytest.raises(ValueError):
        input.thermal_gradient = 0.9e5
    with pytest.raises(ValueError):
        input.thermal_gradient = 1.1e8
    with pytest.raises(ValueError):
        input.melt_pool_width = 7.4e-5
    with pytest.raises(ValueError):
        input.melt_pool_width = 8.1e-4
    with pytest.raises(ValueError):
        input.melt_pool_depth = 1.49e-5
    with pytest.raises(ValueError):
        input.melt_pool_depth = 8.1e-4
    with pytest.raises(ValueError):
        input.random_seed = 0
    with pytest.raises(ValueError):
        input.random_seed = 2**32


@pytest.mark.parametrize(
    "field",
    [
        "sample_min_x",
        "sample_min_y",
        "sample_min_z",
        "sample_size_x",
        "sample_size_y",
        "sample_size_z",
        "sensor_dimension",
        "cooling_rate",
        "thermal_gradient",
        "melt_pool_width",
        "melt_pool_depth",
        "random_seed",
    ],
)
def test_MicrostructureInput_setters_raise_ValueError_for_nan_values(field):
    # arrange
    input = MicrostructureInput()

    # act & assert
    with pytest.raises(ValueError, match=field + " must be a number"):
        setattr(input, field, float("nan"))


def test_MicrostructureInput_size_validation_raises_ValueError_for_values_out_of_range():
    # arrange
    input = MicrostructureInput(
        sensor_dimension=6e-4,
        sample_size_x=0.01,
        sample_size_y=0.01,
        sample_size_z=0.01,
    )

    # act & assert
    with pytest.raises(ValueError):
        input.sample_size_x = 1e-3
    with pytest.raises(ValueError):
        input.sample_size_y = 1e-3
    with pytest.raises(ValueError):
        input.sample_size_z = 1.5e-3
    input.sample_size_x = 1.1e-3
    with pytest.raises(ValueError):
        input.sensor_dimension = 7e-4
    input.sample_size_x = 0.01
    input.sample_size_y = 1.1e-3
    with pytest.raises(ValueError):
        input.sensor_dimension = 7e-4
    input.sample_size_y = 0.01
    input.sample_size_z = 1.6e-3
    with pytest.raises(ValueError):
        input.sensor_dimension = 7e-4
    input.sensor_dimension = 5e-4
    assert input.sensor_dimension == 5e-4


def test_MicrostructureInput_repr_returns_expected_string():
    # arrange
    input = MicrostructureInput()

    # act, assert
    assert repr(input) == (
        "MicrostructureInput\n"
        + f"id: {input.id}\n"
        + "sensor_dimension: 0.0005\n"
        + "sample_size_x: 0.0015\n"
        + "sample_size_y: 0.0015\n"
        + "sample_size_z: 0.0015\n"
        + "sample_min_x: 0\n"
        + "sample_min_y: 0\n"
        + "sample_min_z: 0\n"
        + "use_provided_thermal_parameters: False\n"
        + "cooling_rate: 1000000.0\n"
        + "thermal_gradient: 10000000.0\n"
        + "melt_pool_width: 0.00015\n"
        + "melt_pool_depth: 0.0001\n"
        + "\n"
        + test_utils.get_default_machine_repr()
        + "\n"
        + "material: AdditiveMaterial\n"
        + "absorptivity_maximum: 0\n"
        + "absorptivity_minimum: 0\n"
        + "absorptivity_powder_coefficient_a: 0\n"
        + "absorptivity_powder_coefficient_b: 0\n"
        + "absorptivity_solid_coefficient_a: 0\n"
        + "absorptivity_solid_coefficient_b: 0\n"
        + "anisotropic_strain_coefficient_parallel: 0\n"
        + "anisotropic_strain_coefficient_perpendicular: 0\n"
        + "anisotropic_strain_coefficient_z: 0\n"
        + "cooling_rate_sim_coeff_a: 0\n"
        + "cooling_rate_sim_coeff_b: 0\n"
        + "description: \n"
        + "elastic_modulus: 0\n"
        + "hardening_factor: 0\n"
        + "liquidus_temperature: 0\n"
        + "material_yield_strength: 0\n"
        + "name: \n"
        + "nucleation_constant_bulk: 0\n"
        + "nucleation_constant_interface: 0\n"
        + "penetration_depth_maximum: 0\n"
        + "penetration_depth_minimum: 0\n"
        + "penetration_depth_powder_coefficient_a: 0\n"
        + "penetration_depth_powder_coefficient_b: 0\n"
        + "penetration_depth_solid_coefficient_a: 0\n"
        + "penetration_depth_solid_coefficient_b: 0\n"
        + "poisson_ratio: 0\n"
        + "powder_packing_density: 0\n"
        + "purging_gas_convection_coefficient: 0\n"
        + "solid_density_at_room_temperature: 0\n"
        + "solid_specific_heat_at_room_temperature: 0\n"
        + "solid_thermal_conductivity_at_room_temperature: 0\n"
        + "solidus_temperature: 0\n"
        + "strain_scaling_factor: 0\n"
        + "support_yield_strength_ratio: 0\n"
        + "thermal_expansion_coefficient: 0\n"
        + "vaporization_temperature: 0\n"
        + "characteristic_width_data: CharacteristicWidthDataPoint[]\n"
        + "thermal_properties_data: ThermalPropertiesDataPoint[]\n"
        + "random_seed: 0\n"
    )


def test_MicrostructureSummary_repr_returns_expected_string():
    # arrange
    input = MicrostructureInput()
    user_data_path = os.path.join(tempfile.gettempdir(), "microstructure_summary_repr")
    if not os.path.exists(user_data_path):
        os.makedirs(user_data_path)
    xy_vtk_bytes = bytes(range(3))
    xz_vtk_bytes = bytes(range(4, 6))
    yz_vtk_bytes = bytes(range(7, 9))
    xy_stats = GrainStatistics(
        grain_number=1, area_fraction=2, diameter_um=3, orientation_angle=4
    )
    xz_stats = GrainStatistics(
        grain_number=5, area_fraction=6, diameter_um=7, orientation_angle=8
    )
    yz_stats = GrainStatistics(
        grain_number=9, area_fraction=10, diameter_um=11, orientation_angle=12
    )
    result = MicrostructureResult(
        xy_vtk=xy_vtk_bytes, xz_vtk=xz_vtk_bytes, yz_vtk=yz_vtk_bytes
    )
    result.xy_circle_equivalence.append(xy_stats)
    result.xz_circle_equivalence.append(xz_stats)
    result.yz_circle_equivalence.append(yz_stats)
    summary = MicrostructureSummary(
        input=input, result=result, logs="logs", user_data_path=user_data_path
    )
    expected_output_dir = os.path.join(user_data_path, input.id)

    # act, assert
    assert repr(summary) == (
        "MicrostructureSummary\n"
        + "logs: logs\n"
        + "status: SimulationStatus.COMPLETED\n"
        + "input: MicrostructureInput\n"
        + f"id: {input.id}\n"
        + "sensor_dimension: 0.0005\n"
        + "sample_size_x: 0.0015\n"
        + "sample_size_y: 0.0015\n"
        + "sample_size_z: 0.0015\n"
        + "sample_min_x: 0\n"
        + "sample_min_y: 0\n"
        + "sample_min_z: 0\n"
        + "use_provided_thermal_parameters: False\n"
        + "cooling_rate: 1000000.0\n"
        + "thermal_gradient: 10000000.0\n"
        + "melt_pool_width: 0.00015\n"
        + "melt_pool_depth: 0.0001\n"
        + "\n"
        + test_utils.get_default_machine_repr()
        + "\n"
        + "material: AdditiveMaterial\n"
        + "absorptivity_maximum: 0\n"
        + "absorptivity_minimum: 0\n"
        + "absorptivity_powder_coefficient_a: 0\n"
        + "absorptivity_powder_coefficient_b: 0\n"
        + "absorptivity_solid_coefficient_a: 0\n"
        + "absorptivity_solid_coefficient_b: 0\n"
        + "anisotropic_strain_coefficient_parallel: 0\n"
        + "anisotropic_strain_coefficient_perpendicular: 0\n"
        + "anisotropic_strain_coefficient_z: 0\n"
        + "cooling_rate_sim_coeff_a: 0\n"
        + "cooling_rate_sim_coeff_b: 0\n"
        + "description: \n"
        + "elastic_modulus: 0\n"
        + "hardening_factor: 0\n"
        + "liquidus_temperature: 0\n"
        + "material_yield_strength: 0\n"
        + "name: \n"
        + "nucleation_constant_bulk: 0\n"
        + "nucleation_constant_interface: 0\n"
        + "penetration_depth_maximum: 0\n"
        + "penetration_depth_minimum: 0\n"
        + "penetration_depth_powder_coefficient_a: 0\n"
        + "penetration_depth_powder_coefficient_b: 0\n"
        + "penetration_depth_solid_coefficient_a: 0\n"
        + "penetration_depth_solid_coefficient_b: 0\n"
        + "poisson_ratio: 0\n"
        + "powder_packing_density: 0\n"
        + "purging_gas_convection_coefficient: 0\n"
        + "solid_density_at_room_temperature: 0\n"
        + "solid_specific_heat_at_room_temperature: 0\n"
        + "solid_thermal_conductivity_at_room_temperature: 0\n"
        + "solidus_temperature: 0\n"
        + "strain_scaling_factor: 0\n"
        + "support_yield_strength_ratio: 0\n"
        + "thermal_expansion_coefficient: 0\n"
        + "vaporization_temperature: 0\n"
        + "characteristic_width_data: CharacteristicWidthDataPoint[]\n"
        + "thermal_properties_data: ThermalPropertiesDataPoint[]\n"
        + "random_seed: 0\n"
        + "\n"
        + "xy_vtk: "
        + os.path.join(expected_output_dir, "xy.vtk")
        + "\n"
        + "xz_vtk: "
        + os.path.join(expected_output_dir, "xz.vtk")
        + "\n"
        + "yz_vtk: "
        + os.path.join(expected_output_dir, "yz.vtk")
        + "\n"
        + "xy_circle_equivalence:    grain_number  area_fraction  diameter_um  orientation_angle\n"
        + "0             1            2.0          3.0         229.183118\n"
        + "xz_circle_equivalence:    grain_number  area_fraction  diameter_um  orientation_angle\n"
        + "0             5            6.0          7.0         458.366236\n"
        + "yz_circle_equivalence:    grain_number  area_fraction  diameter_um  orientation_angle\n"
        + "0             9           10.0         11.0         687.549354\n"
        + "xy_average_grain_size: 6.0\n"
        + "xz_average_grain_size: 42.0\n"
        + "yz_average_grain_size: 110.0\n"
    )

    # cleanup
    shutil.rmtree(user_data_path)
