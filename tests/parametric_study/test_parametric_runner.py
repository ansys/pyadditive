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

import logging
from unittest.mock import create_autospec

import pandas as pd
from pyadditive.tests import test_utils
import pytest

from ansys.additive.core import (
    AdditiveMachine,
    AdditiveMaterial,
    MachineConstants,
    MicrostructureInput,
    PorosityInput,
    SimulationType,
    SingleBeadInput,
)
from ansys.additive.core.additive import Additive
import ansys.additive.core.parametric_study as ps
from ansys.additive.core.parametric_study.constants import ColumnNames
from ansys.additive.core.parametric_study.parametric_runner import ParametricRunner as pr
from ansys.additive.core.single_bead import SingleBeadSummary


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


def test_simulate_sorts_by_priority(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [sb, p, ms]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive)

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_filters_by_priority(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [sb]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive, priority=1)

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_filters_by_iteration(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb1 = SingleBeadInput(id="iteration_1", material=material, bead_length=0.001)
    sb2 = SingleBeadInput(id="iteration_2", material=material, bead_length=0.002)
    sb3 = SingleBeadInput(id="iteration_3", material=material, bead_length=0.003)
    study.add_inputs([sb1], iteration=1)
    study.add_inputs([sb2], iteration=2)
    study.add_inputs([sb3], iteration=3)
    inputs = [sb2]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive, iteration=2)

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_filters_by_single_simulation_type(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [p]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive, type=SimulationType.POROSITY)

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_filters_by_simulation_type_list(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [p, ms]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(
        study.data_frame(),
        mock_additive,
        type=[SimulationType.POROSITY, SimulationType.MICROSTRUCTURE],
    )

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_skips_simulations_with_missing_materials(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    mock_additive = create_autospec(Additive)
    mock_additive.material.side_effect = [material, Exception(), material]

    # act
    pr.simulate(study.data_frame(), mock_additive)

    # assert
    mock_additive.simulate.assert_called_once_with([sb, ms])


def test_simulate_returns_empty_list_when_no_simulations_meet_criteria(
    tmp_path: pytest.TempPathFactory,
    caplog,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    study.add_inputs([sb], priority=1)
    mock_additive = create_autospec(Additive)
    caplog.set_level(logging.WARNING, logger="PyAdditive_global")

    # act
    result = pr.simulate(study.data_frame(), mock_additive, type=SimulationType.POROSITY)

    # assert
    assert result == []
    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.levelname == "WARNING"
        assert "None of the input simulations meet the criteria selected" in record.message


@pytest.mark.parametrize(
    "simulation_ids_input",
    [
        ["test_2"],
        ["test_0", "test_2"],
    ],
)
def test_simulate_filters_by_simulation_ids_if_the_list_has_atleast_one_valid_element(
    simulation_ids_input, tmp_path: pytest.TempPathFactory
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [p]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive, simulation_ids=simulation_ids_input)

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


@pytest.mark.parametrize(
    "simulation_ids_input",
    [
        [],
        None,
    ],
)
def test_simulate_skips_filter_by_simulation_ids_if_the_list_is_empty_or_none(
    simulation_ids_input, tmp_path: pytest.TempPathFactory
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [sb, p, ms]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive, simulation_ids=simulation_ids_input)

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_is_skipped_if_simulation_ids_list_has_invalid_elements(
    tmp_path: pytest.TempPathFactory, caplog
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    result = pr.simulate(study.data_frame(), mock_additive, simulation_ids=["test_0", "test_4"])

    # assert
    mock_additive.simulate.assert_not_called()
    assert result == []
    assert len(caplog.records) == 1
    assert "None of the input simulations meet the criteria selected" in caplog.records[0].message


def test_simulate_filters_by_simulation_ids_and_skips_duplicates(
    tmp_path: pytest.TempPathFactory, caplog
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [sb, p]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive, simulation_ids=["test_1", "test_2", "test_1"])

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_filters_by_simulation_ids_and_sorts_by_priority(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], priority=1)
    study.add_inputs([p], priority=2)
    study.add_inputs([ms], priority=3)
    inputs = [sb, ms]  # note that pr.simulate should reorder the inputs based on the priority
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(study.data_frame(), mock_additive, simulation_ids=["test_3", "test_1"])

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_filters_by_simulation_ids_and_iteration(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb = SingleBeadInput(id="test_1", material=material)
    p = PorosityInput(id="test_2", material=material)
    ms = MicrostructureInput(id="test_3", material=material)
    study.add_inputs([sb], iteration=1)
    study.add_inputs([p], iteration=2)
    study.add_inputs([ms], iteration=3)
    inputs = [sb]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(
        study.data_frame(),
        mock_additive,
        simulation_ids=["test_3", "test_2", "test_1"],
        iteration=1,
    )

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_filters_by_simulation_ids_and_type(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb_1 = SingleBeadInput(bead_length=0.001, id="test_1", material=material)
    sb_2 = SingleBeadInput(bead_length=0.002, id="test_2", material=material)
    sb_3 = SingleBeadInput(bead_length=0.003, id="test_3", material=material)
    sb_4 = SingleBeadInput(bead_length=0.004, id="test_4", material=material)
    p = PorosityInput(id="test_5", material=material)
    ms = MicrostructureInput(id="test_6", material=material)
    study.add_inputs([sb_1, sb_2, sb_3, sb_4], iteration=1)
    study.add_inputs([p], iteration=2)
    study.add_inputs([ms], iteration=3)
    inputs = [sb_1, sb_2]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(
        study.data_frame(),
        mock_additive,
        simulation_ids=["test_1", "test_2", "test_5", "test_6"],
        type=SimulationType.SINGLE_BEAD,
    )

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)


def test_simulate_filters_by_simulation_ids_only_takes_pending_simulations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    material = AdditiveMaterial(name="test_material")
    sb_1 = SingleBeadInput(bead_length=0.001, id="test_1", material=material)
    sb_2 = SingleBeadInput(bead_length=0.002, id="test_2", material=material)
    sb_3 = SingleBeadInput(bead_length=0.003, id="test_3", material=material)
    sb_4 = SingleBeadInput(bead_length=0.004, id="test_4", material=material)
    p = PorosityInput(id="test_5", material=material)
    ms = MicrostructureInput(id="test_6", material=material)
    melt_pool_msg = test_utils.get_test_melt_pool_message()
    summary_1 = SingleBeadSummary(sb_1, melt_pool_msg, None)
    summary_2 = SingleBeadSummary(sb_2, melt_pool_msg, None)
    study.add_summaries([summary_1, summary_2])
    study.add_inputs([sb_3, sb_4], iteration=1)
    study.add_inputs([p], iteration=2)
    study.add_inputs([ms], iteration=3)
    inputs = [sb_3, sb_4, p, ms]
    mock_additive = create_autospec(Additive)
    mock_additive.material.return_value = material

    # act
    pr.simulate(
        study.data_frame(),
        mock_additive,
        simulation_ids=["test_1", "test_2", "test_3", "test_4", "test_5", "test_6"],
    )

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)
