# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import math

from ansys.api.additive.v0.additive_domain_pb2 import GrainStatistics, MicrostructureResult
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest
import pytest

from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial
from ansys.additive.microstructure import MicrostructureInput, MicrostructureSummary


def test_MicrostructureSummary_init_returns_expected_value():
    # arrange
    input = MicrostructureInput()
    xy_vtk_bytes = bytes(range(3))
    xz_vtk_bytes = bytes(range(4, 6))
    yz_vtk_bytes = bytes(range(7, 9))
    xy_stats = GrainStatistics(grain_number=1, area_fraction=2, diameter_um=3, orientation_angle=4)
    xz_stats = GrainStatistics(grain_number=5, area_fraction=6, diameter_um=7, orientation_angle=8)
    yz_stats = GrainStatistics(
        grain_number=9, area_fraction=10, diameter_um=11, orientation_angle=12
    )
    result = MicrostructureResult(xy_vtk=xy_vtk_bytes, xz_vtk=xz_vtk_bytes, yz_vtk=yz_vtk_bytes)
    result.xy_circle_equivalence.append(xy_stats)
    result.xz_circle_equivalence.append(xz_stats)
    result.yz_circle_equivalence.append(yz_stats)

    # act
    summary = MicrostructureSummary(input, result)

    # assert
    assert isinstance(summary, MicrostructureSummary)
    assert input == summary.input
    assert summary.xy_vtk == xy_vtk_bytes
    assert summary.xz_vtk == xz_vtk_bytes
    assert summary.yz_vtk == yz_vtk_bytes
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
    with pytest.raises(ValueError, match="Invalid input type") as exc_info:
        MicrostructureSummary(invalid_obj, MicrostructureResult())


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
    with pytest.raises(ValueError, match="Invalid result type") as exc_info:
        MicrostructureSummary(MicrostructureInput(), invalid_obj)


def test_MicrostructureInput_init_creates_default_object():
    # arrange, act
    input = MicrostructureInput()

    # assert
    assert input.id == ""
    assert input.machine.laser_power == 195
    assert input.material.name == ""
    assert input.cube_min_x == 0
    assert input.cube_min_y == 0
    assert input.cube_min_z == 0
    assert input.cube_size_x == 0.0015
    assert input.cube_size_y == 0.0015
    assert input.cube_size_z == 0.0015
    assert input.sensor_dimension == 0.0005
    assert input.use_provided_thermal_parameters == False
    assert input.cooling_rate == 1e6
    assert input.thermal_gradient == 1e7
    assert input.melt_pool_width == 1.5e-4
    assert input.melt_pool_depth == 1e-4
    assert input.random_seed == None


def test_MicrostructureInput_init_with_parameters_creates_expected_object():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")

    # act
    input = MicrostructureInput(
        id="myId",
        machine=machine,
        material=material,
        cube_min_x=1,
        cube_min_y=2,
        cube_min_z=3,
        cube_size_x=4,
        cube_size_y=5,
        cube_size_z=6,
        sensor_dimension=7,
        use_provided_thermal_parameters=True,
        cooling_rate=8,
        thermal_gradient=9,
        melt_pool_width=10,
        melt_pool_depth=11,
        random_seed=12,
    )

    # assert
    assert "myId" == input.id
    assert input.machine.laser_power == 99
    assert input.material.name == "vibranium"
    assert input.cube_min_x == 1
    assert input.cube_min_y == 2
    assert input.cube_min_z == 3
    assert input.cube_size_x == 4
    assert input.cube_size_y == 5
    assert input.cube_size_z == 6
    assert input.sensor_dimension == 7
    assert input.use_provided_thermal_parameters == True
    assert input.cooling_rate == 8
    assert input.thermal_gradient == 9
    assert input.melt_pool_width == 10
    assert input.melt_pool_depth == 11
    assert input.random_seed == 12


def test_MicrostructureInput_init_raises_exception_for_invalid_input():
    # arrange, act, assert
    with pytest.raises(AttributeError):
        MicrostructureInput(bogus="invalid")


def test_MicrostructureInput__to_simulation_request_returns_expected_object():
    # arrange
    input = MicrostructureInput()

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == ""
    ms_input = request.microstructure_input
    assert ms_input.cube_min_x == 0
    assert ms_input.cube_min_y == 0
    assert ms_input.cube_min_z == 0
    assert ms_input.cube_size_x == 0.0015
    assert ms_input.cube_size_y == 0.0015
    assert ms_input.cube_size_z == 0.0015
    assert ms_input.sensor_dimension == 0.0005
    assert ms_input.use_provided_thermal_parameters == False
    assert ms_input.cooling_rate == 1e6
    assert ms_input.thermal_gradient == 1e7
    assert ms_input.melt_pool_width == 1.5e-4
    assert ms_input.melt_pool_depth == 1e-4
    assert ms_input.use_random_seed == False
    assert ms_input.random_seed == 0


def test_MicrostructureInput__to_simulation_request_assigns_values():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")
    input = MicrostructureInput(
        id="myId",
        machine=machine,
        material=material,
        cube_min_x=1,
        cube_min_y=2,
        cube_min_z=3,
        cube_size_x=4,
        cube_size_y=5,
        cube_size_z=6,
        sensor_dimension=7,
        use_provided_thermal_parameters=True,
        cooling_rate=8,
        thermal_gradient=9,
        melt_pool_width=10,
        melt_pool_depth=11,
        random_seed=12,
    )

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == "myId"
    ms_input = request.microstructure_input
    assert ms_input.machine.laser_power == 99
    assert ms_input.material.name == "vibranium"
    assert ms_input.cube_min_x == 1
    assert ms_input.cube_min_y == 2
    assert ms_input.cube_min_z == 3
    assert ms_input.cube_size_x == 4
    assert ms_input.cube_size_y == 5
    assert ms_input.cube_size_z == 6
    assert ms_input.sensor_dimension == 7
    assert ms_input.use_provided_thermal_parameters == True
    assert ms_input.cooling_rate == 8
    assert ms_input.thermal_gradient == 9
    assert ms_input.melt_pool_width == 10
    assert ms_input.melt_pool_depth == 11
    assert ms_input.use_random_seed == True
    assert ms_input.random_seed == 12
