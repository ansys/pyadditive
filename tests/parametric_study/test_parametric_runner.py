# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from unittest.mock import create_autospec

import pandas as pd

from ansys.additive import (
    AdditiveMachine,
    AdditiveMaterial,
    MachineConstants,
    MicrostructureInput,
    PorosityInput,
    SingleBeadInput,
)
from ansys.additive.additive import Additive
import ansys.additive.parametric_study as ps
from ansys.additive.parametric_study.constants import ColumnNames
from ansys.additive.parametric_study.parametric_runner import ParametricRunner as pr


def test_create_machine_assigns_all_values():
    # arrange
    power = 50
    speed = 1.2
    layer_thickness = 40e-6
    beam_diameter = 75e-6
    heater_temperature = 120
    start_angle = 15
    rotation_angle = 22
    hatch_spacing = 110e-6
    stripe_width = 5e-3
    series = pd.Series(
        {
            ColumnNames.LASER_POWER: power,
            ColumnNames.SCAN_SPEED: speed,
            ColumnNames.LAYER_THICKNESS: layer_thickness,
            ColumnNames.BEAM_DIAMETER: beam_diameter,
            ColumnNames.HEATER_TEMPERATURE: heater_temperature,
            ColumnNames.START_ANGLE: start_angle,
            ColumnNames.ROTATION_ANGLE: rotation_angle,
            ColumnNames.HATCH_SPACING: hatch_spacing,
            ColumnNames.STRIPE_WIDTH: stripe_width,
        }
    )

    # act
    machine = pr._create_machine(series)

    # assert
    assert isinstance(machine, AdditiveMachine)
    assert machine.laser_power == power
    assert machine.scan_speed == speed
    assert machine.layer_thickness == layer_thickness
    assert machine.beam_diameter == beam_diameter
    assert machine.heater_temperature == heater_temperature
    assert machine.starting_layer_angle == start_angle
    assert machine.layer_rotation_angle == rotation_angle
    assert machine.hatch_spacing == hatch_spacing
    assert machine.slicing_stripe_width == stripe_width


def test_create_machine_assigns_default_values():
    # arrange
    power = 50
    speed = 1.2
    layer_thickness = 40e-6
    beam_diameter = 75e-6
    heater_temperature = 120
    series = pd.Series(
        {
            ColumnNames.LASER_POWER: power,
            ColumnNames.SCAN_SPEED: speed,
            ColumnNames.LAYER_THICKNESS: layer_thickness,
            ColumnNames.BEAM_DIAMETER: beam_diameter,
            ColumnNames.HEATER_TEMPERATURE: heater_temperature,
            ColumnNames.START_ANGLE: float("nan"),
            ColumnNames.ROTATION_ANGLE: float("nan"),
            ColumnNames.HATCH_SPACING: float("nan"),
            ColumnNames.STRIPE_WIDTH: float("nan"),
        }
    )

    # act
    machine = pr._create_machine(series)

    # assert
    assert isinstance(machine, AdditiveMachine)
    assert machine.laser_power == power
    assert machine.scan_speed == speed
    assert machine.layer_thickness == layer_thickness
    assert machine.beam_diameter == beam_diameter
    assert machine.heater_temperature == heater_temperature
    assert machine.starting_layer_angle == MachineConstants.DEFAULT_STARTING_LAYER_ANGLE
    assert machine.layer_rotation_angle == MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE
    assert machine.hatch_spacing == MachineConstants.DEFAULT_HATCH_SPACING
    assert machine.slicing_stripe_width == MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH


def test_create_single_bead_input():
    # arrange
    id = "test_id"
    bead_length = 9.5e-3
    series = pd.Series(
        {
            ColumnNames.ID: id,
            ColumnNames.SINGLE_BEAD_LENGTH: bead_length,
        }
    )
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = pr._create_single_bead_input(series, material=material, machine=machine)

    # assert
    assert isinstance(input, SingleBeadInput)
    assert input.id == id
    assert input.bead_length == bead_length
    assert input.machine == machine
    assert input.material == material


def test_create_porosity_input():
    # arrange
    id = "test_id"
    size_x = 1e-3
    size_y = 2e-3
    size_z = 3e-3
    series = pd.Series(
        {
            ColumnNames.ID: id,
            ColumnNames.POROSITY_SIZE_X: size_x,
            ColumnNames.POROSITY_SIZE_Y: size_y,
            ColumnNames.POROSITY_SIZE_Z: size_z,
        }
    )
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = pr._create_porosity_input(series, material=material, machine=machine)

    # assert
    assert isinstance(input, PorosityInput)
    assert input.id == id
    assert input.size_x == size_x
    assert input.size_y == size_y
    assert input.size_z == size_z
    assert input.machine == machine
    assert input.material == material


def test_create_microstructure_input_assigns_all_values():
    # arrange
    id = "test_id"
    min_x = 1
    min_y = 2
    min_z = 3
    size_x = 1.1e-3
    size_y = 1.2e-3
    size_z = 1.3e-3
    sensor_dim = 1.4e-4
    cooling_rate = 1.5e6
    thermal_gradient = 1.6e6
    melt_pool_width = 1.7e-4
    melt_pool_depth = 1.8e-4
    random_seed = 1234
    series = pd.Series(
        {
            ColumnNames.ID: id,
            ColumnNames.MICRO_MIN_X: min_x,
            ColumnNames.MICRO_MIN_Y: min_y,
            ColumnNames.MICRO_MIN_Z: min_z,
            ColumnNames.MICRO_SIZE_X: size_x,
            ColumnNames.MICRO_SIZE_Y: size_y,
            ColumnNames.MICRO_SIZE_Z: size_z,
            ColumnNames.MICRO_SENSOR_DIM: sensor_dim,
            ColumnNames.COOLING_RATE: cooling_rate,
            ColumnNames.THERMAL_GRADIENT: thermal_gradient,
            ColumnNames.MICRO_MELT_POOL_WIDTH: melt_pool_width,
            ColumnNames.MICRO_MELT_POOL_DEPTH: melt_pool_depth,
            ColumnNames.RANDOM_SEED: random_seed,
        }
    )
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = pr._create_microstructure_input(series, material=material, machine=machine)

    # assert
    assert isinstance(input, MicrostructureInput)
    assert input.id == id
    assert input.sample_min_x == min_x
    assert input.sample_min_y == min_y
    assert input.sample_min_z == min_z
    assert input.sample_size_x == size_x
    assert input.sample_size_y == size_y
    assert input.sample_size_z == size_z
    assert input.sensor_dimension == sensor_dim
    assert input.use_provided_thermal_parameters == True
    assert input.cooling_rate == cooling_rate
    assert input.thermal_gradient == thermal_gradient
    assert input.melt_pool_width == melt_pool_width
    assert input.melt_pool_depth == melt_pool_depth
    assert input.random_seed == random_seed
    assert input.machine == machine
    assert input.material == material


def test_create_microstructure_input_assigns_defaults_for_nans():
    # arrange
    id = "test_id"
    size_x = 1.1e-3
    size_y = 1.2e-3
    size_z = 1.3e-3
    sensor_dim = 1.4e-4
    series = pd.Series(
        {
            ColumnNames.ID: id,
            ColumnNames.MICRO_MIN_X: float("nan"),
            ColumnNames.MICRO_MIN_Y: float("nan"),
            ColumnNames.MICRO_MIN_Z: float("nan"),
            ColumnNames.MICRO_SIZE_X: size_x,
            ColumnNames.MICRO_SIZE_Y: size_y,
            ColumnNames.MICRO_SIZE_Z: size_z,
            ColumnNames.MICRO_SENSOR_DIM: sensor_dim,
            ColumnNames.COOLING_RATE: float("nan"),
            ColumnNames.THERMAL_GRADIENT: float("nan"),
            ColumnNames.MICRO_MELT_POOL_WIDTH: float("nan"),
            ColumnNames.MICRO_MELT_POOL_DEPTH: float("nan"),
            ColumnNames.RANDOM_SEED: float("nan"),
        }
    )
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = pr._create_microstructure_input(series, material=material, machine=machine)

    # assert
    assert isinstance(input, MicrostructureInput)
    assert input.id == id
    assert input.sample_min_x == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert input.sample_min_y == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert input.sample_min_z == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert input.sample_size_x == size_x
    assert input.sample_size_y == size_y
    assert input.sample_size_z == size_z
    assert input.sensor_dimension == sensor_dim
    assert input.use_provided_thermal_parameters == False
    assert input.cooling_rate == MicrostructureInput.DEFAULT_COOLING_RATE
    assert input.thermal_gradient == MicrostructureInput.DEFAULT_THERMAL_GRADIENT
    assert input.melt_pool_width == MicrostructureInput.DEFAULT_MELT_POOL_WIDTH
    assert input.melt_pool_depth == MicrostructureInput.DEFAULT_MELT_POOL_DEPTH
    assert input.random_seed == MicrostructureInput.DEFAULT_RANDOM_SEED
    assert input.machine == machine
    assert input.material == material


def test_simulate_calls_additive_simulate_correctly():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [sb, p, ms]
    mock_additive = create_autospec(Additive)
    mock_additive.get_material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive)

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_skips_simulations_with_missing_materials():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [sb, p, ms]
    mock_additive = create_autospec(Additive)
    mock_additive.get_material.side_effect = [material, Exception(), material]

    # act
    pr.simulate(study.data_frame(), mock_additive)

    # assert
    mock_additive.simulate.assert_called_once_with([sb, ms])
