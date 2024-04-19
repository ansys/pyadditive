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

from ansys.api.additive.v0.additive_domain_pb2 import MeltPoolTimeStep
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
import pytest

from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.single_bead import (
    MeltPool,
    MeltPoolMessage,
    SingleBeadInput,
    SingleBeadSummary,
)

from . import test_utils


def test_MeltPool_init_converts_MeltPoolMessage():
    # arrange, act
    melt_pool = MeltPool(test_utils.get_test_melt_pool_message())

    # assert
    df = melt_pool.data_frame()
    assert df is not None
    assert len(df.index) == 1
    assert df.index[0] == 1
    assert df.iloc[0]["length"] == 3
    assert df.iloc[0]["width"] == 4
    assert df.iloc[0]["reference_width"] == 5
    assert df.iloc[0]["depth"] == 6
    assert df.iloc[0]["reference_depth"] == 7


def test_SingleBeadSummary_init_returns_valid_result():
    # arrange
    melt_pool_msg = test_utils.get_test_melt_pool_message()
    expected_melt_pool = MeltPool(melt_pool_msg)
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    input = SingleBeadInput(
        id="id",
        bead_length=0.001,
        machine=machine,
        material=material,
    )

    # act
    summary = SingleBeadSummary(input, melt_pool_msg)

    # assert
    assert input == summary.input
    assert expected_melt_pool == summary.melt_pool


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        SingleBeadInput(),
    ],
)
def test_SingleBeadSummary_init_raises_exception_for_invalid_melt_pool_message(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid message type") as exc_info:
        SingleBeadSummary(SingleBeadInput(), invalid_obj)


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        MeltPoolMessage(),
    ],
)
def test_SingleBeadSummary_init_raises_exception_for_invalid_single_bead_input(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid input type") as exc_info:
        SingleBeadSummary(invalid_obj, MeltPoolMessage())


def test_SingleBeadInput_to_simulation_request_assigns_values():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")
    input = SingleBeadInput(
        id="myId",
        machine=machine,
        material=material,
        bead_length=0.01,
    )

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == "myId"
    sb_input = request.single_bead_input
    assert sb_input.machine.laser_power == 99
    assert sb_input.material.name == "vibranium"
    assert sb_input.bead_length == 0.01


def test_SingleBeadInput_repr_creates_expected_string():
    # arrange
    input = SingleBeadInput(id="myId")

    # act
    assert (
        input.__repr__()
        == "SingleBeadInput\n"
        + "id: myId\n"
        + "bead_length: 0.003\n"
        + "\n"
        + "machine: AdditiveMachine\n"
        + "laser_power: 195 W\n"
        + "scan_speed: 1.0 m/s\n"
        + "heater_temperature: 80 °C\n"
        + "layer_thickness: 5e-05 m\n"
        + "beam_diameter: 0.0001 m\n"
        + "starting_layer_angle: 57 °\n"
        + "layer_rotation_angle: 67 °\n"
        + "hatch_spacing: 0.0001 m\n"
        + "slicing_stripe_width: 0.01 m\n"
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
        + "output_thermal_history: False\n"
        + "thermal_history_interval: 1\n"
    )


def test_MeltPool_eq_returns_expected_value():
    # arrange
    mp_msg = MeltPoolMessage()
    mp1 = MeltPool(mp_msg)
    mp2 = MeltPool(mp_msg)
    mp_msg.time_steps.append(
        MeltPoolTimeStep(
            laser_x=1,
            laser_y=2,
            length=3,
            width=4,
            depth=5,
            reference_width=6,
            reference_depth=7,
        )
    )
    mp3 = MeltPool(mp_msg)

    # act, assert
    assert mp1 == mp2
    assert mp1 != mp3
    assert mp1 != MeltPoolMessage()


def test_MeltPool_repr_returns_expected_string():
    # arrange
    mp_msg = MeltPoolMessage()
    mp_msg.time_steps.append(
        MeltPoolTimeStep(
            laser_x=1,
            laser_y=2,
            length=3,
            width=4,
            depth=5,
            reference_width=6,
            reference_depth=7,
        )
    )
    mp = MeltPool(mp_msg)

    # act, assert
    assert mp.__repr__() == (
        "MeltPool\n"
        "             length  width  depth  reference_width  reference_depth\n"
        "bead_length                                                        \n"
        "1.0             3.0    4.0    5.0              6.0              7.0"
    )


def test_SingleBeadSummary_repr_returns_expected_string():
    # arrange
    msg = MeltPoolMessage()
    input = SingleBeadInput(id="myId")
    summary = SingleBeadSummary(input, msg)

    # act, assert
    assert (
        summary.__repr__()
        == "SingleBeadSummary\n"
        + "input: SingleBeadInput\n"
        + "id: myId\n"
        + "bead_length: 0.003\n"
        + "\n"
        + "machine: AdditiveMachine\n"
        + "laser_power: 195 W\n"
        + "scan_speed: 1.0 m/s\n"
        + "heater_temperature: 80 °C\n"
        + "layer_thickness: 5e-05 m\n"
        + "beam_diameter: 0.0001 m\n"
        + "starting_layer_angle: 57 °\n"
        + "layer_rotation_angle: 67 °\n"
        + "hatch_spacing: 0.0001 m\n"
        + "slicing_stripe_width: 0.01 m\n"
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
        + "output_thermal_history: False\n"
        + "thermal_history_interval: 1\n"
        + "\n"
        + "melt_pool: MeltPool\n"
        + "Empty DataFrame\nColumns: [length, width, depth, reference_width, reference_depth]\nIndex: []"
        + "\n"
    )


def test_SingleBeadInput_setters_raise_expected_errors():
    # arrange
    input = SingleBeadInput()

    # act, assert
    with pytest.raises(ValueError):
        input.bead_length = 0.5e-3
    with pytest.raises(ValueError):
        input.bead_length = 1.1e-2
    with pytest.raises(ValueError, match="bead_length must be a number"):
        input.bead_length = float("nan")
