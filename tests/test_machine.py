# Copyright (C) 2022 - 2026 ANSYS, Inc. and/or its affiliates.
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

import pytest

from ansys.additive.core.machine import AdditiveMachine, MachineMessage, HeatSourceModelEnumMessage, RingModeIndexEnumMessage


def test_AdditiveMachine_init_returns_default():
    # arrange, act
    machine = AdditiveMachine()

    # assert
    assert isinstance(machine, AdditiveMachine)
    assert machine.laser_power == 195
    assert machine.scan_speed == 1.0
    assert machine.heater_temperature == 80.0
    assert machine.layer_thickness == 5e-5
    assert machine.beam_diameter == 1e-4
    assert machine.starting_layer_angle == 57
    assert machine.layer_rotation_angle == 67
    assert machine.hatch_spacing == 1e-4
    assert machine.slicing_stripe_width == 0.01
    assert machine.heat_source_model == "gaussian"
    assert machine.ring_mode_index == 0
    assert machine.defocus == 0.0


def test_from_machine_message_returns_AdditiveMachine():
    # arrange
    msg = MachineMessage(
        laser_power=100,
        scan_speed=2,
        heater_temperature=30 + 273.15,
        layer_thickness=4e-5,
        beam_diameter=5e-5,
        starting_layer_angle=60 * math.pi / 180,
        layer_rotation_angle=70 * math.pi / 180,
        hatch_spacing=8e-5,
        slicing_stripe_width=0.009,
        heat_source_model=HeatSourceModelEnumMessage.HEAT_SOURCE_MODEL_RING,
        ring_mode_index=RingModeIndexEnumMessage.RING_MODE_INDEX_05,
        defocus_distance=3.e-3,
    )

    # act
    machine = AdditiveMachine._from_machine_message(msg)

    # assert
    abs_tol = 0.0001
    assert isinstance(machine, AdditiveMachine)
    assert machine.laser_power == 100
    assert machine.scan_speed == 2
    assert math.isclose(machine.heater_temperature, 30, abs_tol=abs_tol)
    assert machine.layer_thickness == 4e-5
    assert machine.beam_diameter == 5e-5
    assert math.isclose(machine.starting_layer_angle, 60, abs_tol=abs_tol)
    assert math.isclose(machine.layer_rotation_angle, 70, abs_tol=abs_tol)
    assert machine.hatch_spacing == 8e-5
    assert machine.slicing_stripe_width == 0.009
    assert machine.heat_source_model == "ring"
    assert machine.ring_mode_index == 5
    assert machine.defocus == 0.003


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        AdditiveMachine(),
    ],
)
def test_from_machine_message_raises_exception_for_invalid_type(invalid_obj):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid message type passed to _from_machine_message()"):
        AdditiveMachine._from_machine_message(invalid_obj)


def test_to_machine_message_returns_MachineMessage():
    # arrange
    machine = AdditiveMachine(
        laser_power=100,
        scan_speed=2,
        heater_temperature=30,
        layer_thickness=4e-5,
        beam_diameter=5e-5,
        starting_layer_angle=60,
        layer_rotation_angle=70,
        hatch_spacing=8e-5,
        slicing_stripe_width=0.009,
        heat_source_model="ring",
        ring_mode_index=4,
        defocus=0.003,
    )

    # act
    msg = machine._to_machine_message()

    # assert
    abs_tol = 0.0001
    assert isinstance(msg, MachineMessage)
    assert msg.laser_power == 100
    assert msg.scan_speed == 2
    assert math.isclose(msg.heater_temperature, 30 + 273.15, abs_tol=abs_tol)
    assert msg.layer_thickness == 4e-5
    assert msg.beam_diameter == 5e-5
    assert math.isclose(msg.starting_layer_angle, 60 * math.pi / 180, abs_tol=abs_tol)
    assert math.isclose(msg.layer_rotation_angle, 70 * math.pi / 180, abs_tol=abs_tol)
    assert msg.hatch_spacing == 8e-5
    assert msg.slicing_stripe_width == 0.009
    assert msg.heat_source_model == HeatSourceModelEnumMessage.HEAT_SOURCE_MODEL_RING
    assert msg.ring_mode_index == RingModeIndexEnumMessage.RING_MODE_INDEX_04
    assert msg.defocus_distance == 0.003


def test_AdditiveMachine_eq_returns_expected_value():
    # arrange
    machine = AdditiveMachine()
    not_machine = AdditiveMachine(laser_power=100)

    # act, assert
    assert machine == AdditiveMachine()
    assert machine != MachineMessage()
    assert machine != not_machine


def test_range_check_raises_exception_for_invalid_value():
    # arrange, act, assert
    with pytest.raises(ValueError, match="laser_power"):
        AdditiveMachine(laser_power=49)
    with pytest.raises(ValueError, match="laser_power"):
        AdditiveMachine(laser_power=701)
    with pytest.raises(ValueError, match="scan_speed"):
        AdditiveMachine(scan_speed=0.34)
    with pytest.raises(ValueError, match="scan_speed"):
        AdditiveMachine(scan_speed=2.6)
    with pytest.raises(ValueError, match="heater_temperature"):
        AdditiveMachine(heater_temperature=19)
    with pytest.raises(ValueError, match="heater_temperature"):
        AdditiveMachine(heater_temperature=501)
    with pytest.raises(ValueError, match="layer_thickness"):
        AdditiveMachine(layer_thickness=0.9e-5)
    with pytest.raises(ValueError, match="layer_thickness"):
        AdditiveMachine(layer_thickness=1.1e-4)
    with pytest.raises(ValueError, match="beam_diameter"):
        AdditiveMachine(beam_diameter=1.9e-5)
    with pytest.raises(ValueError, match="beam_diameter"):
        AdditiveMachine(beam_diameter=1.41e-4)
    with pytest.raises(ValueError, match="starting_layer_angle"):
        AdditiveMachine(starting_layer_angle=-1)
    with pytest.raises(ValueError, match="starting_layer_angle"):
        AdditiveMachine(starting_layer_angle=181)
    with pytest.raises(ValueError, match="layer_rotation_angle"):
        AdditiveMachine(layer_rotation_angle=-1)
    with pytest.raises(ValueError, match="layer_rotation_angle"):
        AdditiveMachine(layer_rotation_angle=181)
    with pytest.raises(ValueError, match="hatch_spacing"):
        AdditiveMachine(hatch_spacing=5.9e-5)
    with pytest.raises(ValueError, match="hatch_spacing"):
        AdditiveMachine(hatch_spacing=2.1e-4)
    with pytest.raises(ValueError, match="slicing_stripe_width"):
        AdditiveMachine(slicing_stripe_width=0.0009)
    with pytest.raises(ValueError, match="slicing_stripe_width"):
        AdditiveMachine(slicing_stripe_width=0.11)
    with pytest.raises(ValueError, match="heat_source_model"):
        AdditiveMachine(heat_source_model="not_a_valid_model")
    with pytest.raises(ValueError, match="ring_mode_index"):
        AdditiveMachine(ring_mode_index=11)
    with pytest.raises(ValueError, match="ring_mode_index"):
        AdditiveMachine(ring_mode_index=-2)
    with pytest.raises(ValueError, match="defocus"):
        AdditiveMachine(defocus=1)
    with pytest.raises(ValueError, match="defocus"):
        AdditiveMachine(defocus=-1)


def test_range_check_raises_exception_for_nan_value():
    # arrange, act, assert
    with pytest.raises(ValueError, match="laser_power must be a number"):
        AdditiveMachine(laser_power=float("nan"))
    with pytest.raises(ValueError, match="scan_speed must be a number"):
        AdditiveMachine(scan_speed=float("nan"))
    with pytest.raises(ValueError, match="heater_temperature must be a number"):
        AdditiveMachine(heater_temperature=float("nan"))
    with pytest.raises(ValueError, match="layer_thickness must be a number"):
        AdditiveMachine(layer_thickness=float("nan"))
    with pytest.raises(ValueError, match="beam_diameter must be a number"):
        AdditiveMachine(beam_diameter=float("nan"))
    with pytest.raises(ValueError, match="starting_layer_angle must be a number"):
        AdditiveMachine(starting_layer_angle=float("nan"))
    with pytest.raises(ValueError, match="layer_rotation_angle must be a number"):
        AdditiveMachine(layer_rotation_angle=float("nan"))
    with pytest.raises(ValueError, match="hatch_spacing must be a number"):
        AdditiveMachine(hatch_spacing=float("nan"))
    with pytest.raises(ValueError, match="slicing_stripe_width must be a number"):
        AdditiveMachine(slicing_stripe_width=float("nan"))
    with pytest.raises(ValueError, match="ring_mode_index must be a number"):
        AdditiveMachine(ring_mode_index=float("nan")) # type: ignore
    with pytest.raises(ValueError, match="defocus must be a number"):
        AdditiveMachine(defocus=float("nan")) # type: ignore


def test_setters_set_correct_values():
    # arrange
    machine = AdditiveMachine()

    # act
    machine.laser_power = 50
    machine.scan_speed = 0.35
    machine.heater_temperature = 20
    machine.layer_thickness = 1e-5
    machine.beam_diameter = 2e-5
    machine.starting_layer_angle = 0
    machine.layer_rotation_angle = 90
    machine.hatch_spacing = 6e-5
    machine.slicing_stripe_width = 0.001
    machine.defocus = 0.003

    # assert
    assert machine.laser_power == 50
    assert machine.scan_speed == 0.35
    assert machine.heater_temperature == 20
    assert machine.layer_thickness == 1e-5
    assert machine.beam_diameter == 2e-5
    assert machine.starting_layer_angle == 0
    assert machine.layer_rotation_angle == 90
    assert machine.hatch_spacing == 6e-5
    assert machine.slicing_stripe_width == 0.001
    assert machine.defocus == 0.003


def test_default_heat_source_is_gaussian():
    # Other heat source models are marked as beta, the default should not be a beta feature

    # arrange, act
    machine = AdditiveMachine()

    # assert
    assert machine.heat_source_model == "gaussian"


def test_validate_range_accepts_valid_values():
    # arrange
    machine = AdditiveMachine()

    # act, assert - no exception should be raised
    machine._AdditiveMachine__validate_range(50, 0, 100, "test_value")
    machine._AdditiveMachine__validate_range(0, 0, 100, "test_value")
    machine._AdditiveMachine__validate_range(100, 0, 100, "test_value")


def test_validate_range_raises_exception_for_nan():
    # arrange
    machine = AdditiveMachine()

    # act, assert
    with pytest.raises(ValueError, match="test_value must be a number"):
        machine._AdditiveMachine__validate_range(float("nan"), 0, 100, "test_value")


def test_validate_range_raises_exception_for_value_below_min():
    # arrange
    machine = AdditiveMachine()

    # act, assert
    with pytest.raises(ValueError, match="test_value must be between 0 and 100"):
        machine._AdditiveMachine__validate_range(-1, 0, 100, "test_value")


def test_validate_range_raises_exception_for_value_above_max():
    # arrange
    machine = AdditiveMachine()

    # act, assert
    with pytest.raises(ValueError, match="test_value must be between 0 and 100"):
        machine._AdditiveMachine__validate_range(101, 0, 100, "test_value")