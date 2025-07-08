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

import pytest

from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.porosity import PorosityInput, PorositySummary
from ansys.api.additive.v0.additive_domain_pb2 import PorosityResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.core.simulation import SimulationStatus

from . import test_utils


def test_PorosityInput_init_creates_default_object():
    # arrange, act
    machine = AdditiveMachine()
    material = AdditiveMaterial()
    input = PorosityInput()

    # assert
    assert input.id
    assert input.size_x == 3e-3
    assert input.size_y == 3e-3
    assert input.size_z == 3e-3
    assert machine == input.machine
    assert material == input.material


def test_PorosityInput_init_creates_expected_object():
    # arrange, act
    machine = AdditiveMachine(laser_power=100)
    material = test_utils.get_test_material()
    input = PorosityInput(
        size_x=1e-3,
        size_y=2e-3,
        size_z=3e-3,
        machine=machine,
        material=material,
    )

    # assert
    assert input.id
    assert input.size_x == 1e-3
    assert input.size_y == 2e-3
    assert input.size_z == 3e-3
    assert machine == input.machine
    assert material == input.material


def test_PorositySummary_init_creates_expected_object():
    # arrange
    logs = "simulation succeeded"
    input = PorosityInput(
        size_x=1e-3,
        size_y=2e-3,
        size_z=3e-3,
        machine=AdditiveMachine(),
        material=test_utils.get_test_material(),
    )

    result = PorosityResult(
        void_ratio=10,
        powder_ratio=11,
        solid_ratio=12,
    )

    # act
    summary = PorositySummary(input, result, logs)

    # assert
    assert input == summary.input
    assert summary.relative_density == 12
    assert summary.logs == logs
    assert summary.status == SimulationStatus.COMPLETED


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        PorosityResult(),
    ],
)
def test_PorositySummary_init_raises_exception_for_invalid_input_type(invalid_obj):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid input type"):
        PorositySummary(invalid_obj, PorosityResult(), "logs")


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        PorosityInput(),
    ],
)
def test_PorositySummary_init_raises_exception_for_invalid_result_type(invalid_obj):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid result type") as exc_info:
        PorositySummary(PorosityInput(), invalid_obj, "logs")


def test_PorositySummary_init_raises_exception_for_invalid_logs_type():
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid logs type") as exc_info:
        PorositySummary(PorosityInput(), PorosityResult(), b"logs")


def test_PorosityInput__to_simulation_request_assigns_values():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")
    input = PorosityInput(
        machine=machine, material=material, size_x=1e-3, size_y=2e-3, size_z=3e-3
    )

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == input.id
    p_input = request.porosity_input
    assert p_input.machine.laser_power == 99
    assert p_input.material.name == "vibranium"
    assert p_input.size_x == 1e-3
    assert p_input.size_y == 2e-3
    assert p_input.size_z == 3e-3


def test_PorosityInput_setters_raise_expected_errors():
    # arrange
    input = PorosityInput()

    # act, assert
    with pytest.raises(ValueError):
        input.size_x = 0.9e-3
    with pytest.raises(ValueError):
        input.size_x = 1.1e-2
    with pytest.raises(ValueError):
        input.size_y = 0.9e-3
    with pytest.raises(ValueError):
        input.size_y = 1.1e-2
    with pytest.raises(ValueError):
        input.size_z = 0.9e-3
    with pytest.raises(ValueError):
        input.size_z = 1.1e-2


@pytest.mark.parametrize("field", ["size_x", "size_y", "size_z"])
def test_PorosityInput_setters_raise_expected_error_for_nan_values(field):
    # arrange
    input = PorosityInput()

    # act & assert
    with pytest.raises(ValueError, match=field + " must be a number"):
        setattr(input, field, float("nan"))


def test_PorosityInput_repr_returns_expected_string():
    # arrange
    input = PorosityInput()

    # act, assert
    assert repr(input) == (
        "PorosityInput\n"
        + f"id: {input.id}\n"
        + "size_x: 0.003\n"
        + "size_y: 0.003\n"
        + "size_z: 0.003\n"
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
    )


def test_PorositySummary_repr_retuns_expected_string():
    # arrange
    input = PorosityInput()
    result = PorosityResult()
    summary = PorositySummary(input, result, "logs")

    # act, assert
    assert repr(summary) == (
        "PorositySummary\n"
        + "logs: logs\n"
        + "status: SimulationStatus.COMPLETED\n"
        + "input: PorosityInput\n"
        + f"id: {input.id}\n"
        + "size_x: 0.003\n"
        + "size_y: 0.003\n"
        + "size_z: 0.003\n"
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
        + "\n"
        + "relative_density: 0.0\n"
    )
