import math

import pytest

from ansys.additive.machine import AdditiveMachine, MachineMessage


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


def test_AdditiveMachine_init_raises_exception_for_arg():
    # arrange, act, assert
    with pytest.raises(AttributeError) as exc_info:
        AdditiveMachine(bogus="bummer")


def test_from_machine_message_returns_AdditiveMachine():
    # arrange
    msg = MachineMessage(
        laser_power=1,
        scan_speed=2,
        heater_temperature=3 + 273.15,
        layer_thickness=4,
        beam_diameter=5,
        starting_layer_angle=math.pi,
        layer_rotation_angle=2 * math.pi,
        hatch_spacing=8,
        slicing_stripe_width=9,
    )

    # act
    machine = AdditiveMachine.from_machine_message(msg)

    # assert
    abs_tol = 0.0001
    assert isinstance(machine, AdditiveMachine)
    assert machine.laser_power == 1
    assert machine.scan_speed == 2
    assert math.isclose(machine.heater_temperature, 3, abs_tol=abs_tol)
    assert machine.layer_thickness == 4
    assert machine.beam_diameter == 5
    assert machine.starting_layer_angle == 180
    assert machine.layer_rotation_angle == 360
    assert machine.hatch_spacing == 8
    assert machine.slicing_stripe_width == 9


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
    with pytest.raises(ValueError, match="Invalid message type passed to from_machine_message()"):
        AdditiveMachine.from_machine_message(invalid_obj)


def test_to_machine_message_returns_MachineMessage():
    # arrange
    machine = AdditiveMachine(
        laser_power=1,
        scan_speed=2,
        heater_temperature=3,
        layer_thickness=4,
        beam_diameter=5,
        starting_layer_angle=180,
        layer_rotation_angle=360,
        hatch_spacing=8,
        slicing_stripe_width=9,
    )

    # act
    msg = machine.to_machine_message()

    # assert
    abs_tol = 0.0001
    assert isinstance(msg, MachineMessage)
    assert msg.laser_power == 1
    assert msg.scan_speed == 2
    assert math.isclose(msg.heater_temperature, 3 + 273.15, abs_tol=abs_tol)
    assert msg.layer_thickness == 4
    assert msg.beam_diameter == 5
    assert math.isclose(msg.starting_layer_angle, math.pi, abs_tol=abs_tol)
    assert math.isclose(msg.layer_rotation_angle, 2 * math.pi, abs_tol=abs_tol)
    assert msg.hatch_spacing == 8
    assert msg.slicing_stripe_width == 9
