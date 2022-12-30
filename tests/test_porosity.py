from ansys.api.additive.v0.additive_domain_pb2 import PorosityResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
import pytest

from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial
from ansys.additive.porosity import PorosityInput, PorositySummary

from . import test_utils


def test_PorosityInput_init_creates_default_object():
    # arrange, act
    machine = AdditiveMachine()
    material = AdditiveMaterial()
    input = PorosityInput()

    # assert
    assert "" == input.id
    assert 1e-3 == input.size_x
    assert 1e-3 == input.size_y
    assert 1e-3 == input.size_z
    assert machine == input.machine
    assert material == input.material


def test_PorosityInput_init_creates_expected_object():
    # arrange, act
    machine = test_utils.get_test_machine()
    material = test_utils.get_test_material()
    input = PorosityInput(
        id="id",
        size_x=1,
        size_y=2,
        size_z=3,
        machine=machine,
        material=material,
    )

    # assert
    assert "id" == input.id
    assert 1 == input.size_x
    assert 2 == input.size_y
    assert 3 == input.size_z
    assert machine == input.machine
    assert material == input.material


def test_PorositySummary_init_creates_expected_object():
    # arrange
    input = PorosityInput(
        id="id",
        size_x=1,
        size_y=2,
        size_z=3,
        machine=test_utils.get_test_machine(),
        material=test_utils.get_test_material(),
    )

    result = PorosityResult(
        void_ratio=10,
        powder_ratio=11,
        solid_ratio=12,
    )

    # act
    summary = PorositySummary(input, result)

    # assert
    assert input == summary.input
    assert 10 == summary.void_ratio
    assert 11 == summary.powder_ratio
    assert 12 == summary.solid_ratio


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
    with pytest.raises(ValueError, match="Invalid input type") as exc_info:
        PorositySummary(invalid_obj, PorosityResult())


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
        PorositySummary(PorosityInput(), invalid_obj)


def test_PorosityInput__to_simulation_request_assigns_values():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")
    input = PorosityInput(
        id="myId", machine=machine, material=material, size_x=1, size_y=2, size_z=3
    )

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == "myId"
    p_input = request.porosity_input
    assert p_input.machine.laser_power == 99
    assert p_input.material.name == "vibranium"
    assert p_input.size_x == 1
    assert p_input.size_y == 2
    assert p_input.size_z == 3
