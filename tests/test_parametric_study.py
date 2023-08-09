# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import os
import shutil
import tempfile

from ansys.api.additive.v0.additive_domain_pb2 import (
    GrainStatistics,
    MicrostructureResult,
    PorosityResult,
)
import numpy as np

from ansys.additive import (
    AdditiveMachine,
    MeltPoolColumnNames,
    MicrostructureInput,
    MicrostructureSummary,
    PorosityInput,
    PorositySummary,
    SingleBeadInput,
    SingleBeadSummary,
)
import ansys.additive.parametric_study as ps
from tests import test_utils


def test_init_assigns_name():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")

    # assert
    assert study.project_name == "test_study"


def test_save_and_load_returns_original_object():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")

    # act
    study.save("test_study.prm")
    study2 = ps.ParametricStudy.load("test_study.prm")

    # assert
    assert study == study2

    # cleanup
    os.remove("test_study.prm")


def test_eq_returns_false_for_different_names():
    # arrange, act
    study = ps.ParametricStudy(project_name="test_study")
    study2 = ps.ParametricStudy(project_name="test_study2")

    # assert
    assert study != study2


def test_eq_returns_false_for_different_data():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    study2 = ps.ParametricStudy(project_name="test_study")
    df = study.data_frame()

    # act
    # add a column to one of the dataframes
    df["test"] = 1

    # assert
    assert study != study2


def test_build_rate_calculates_correctly():
    # arrange
    # act
    # assert
    assert ps.ParametricStudy.build_rate(2, 3, 4) == 24
    assert ps.ParametricStudy.build_rate(2, 3) == 6


def test_add_results_with_porosity_summary_adds_row():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    input = PorosityInput(
        id="id",
        size_x=1e-3,
        size_y=2e-3,
        size_z=3e-3,
        machine=machine,
        material=material,
    )
    result = PorosityResult(
        void_ratio=10,
        powder_ratio=11,
        solid_ratio=12,
    )
    summary = PorositySummary(input, result)
    expected_build_rate = ps.ParametricStudy.build_rate(
        machine.scan_speed, machine.layer_thickness, machine.hatch_spacing
    )

    # act
    study.add_results([summary], iteration=99)

    # assert
    assert len(study.data_frame()) == 1
    row = study.data_frame().iloc[0]
    assert row[ps.ColumnNames.PROJECT] == "test_study"
    assert row[ps.ColumnNames.ITERATION] == 99
    assert row[ps.ColumnNames.ID] == "id"
    assert row[ps.ColumnNames.STATUS] == ps.SimulationStatus.COMPLETED
    assert row[ps.ColumnNames.MATERIAL] == material.name
    assert row[ps.ColumnNames.HEATER_TEMPERATURE] == machine.heater_temperature
    assert row[ps.ColumnNames.LAYER_THICKNESS] == machine.layer_thickness
    assert row[ps.ColumnNames.BEAM_DIAMETER] == machine.beam_diameter
    assert row[ps.ColumnNames.LASER_POWER] == machine.laser_power
    assert row[ps.ColumnNames.SCAN_SPEED] == machine.scan_speed
    assert row[ps.ColumnNames.HATCH_SPACING] == machine.hatch_spacing
    assert row[ps.ColumnNames.START_ANGLE] == machine.starting_layer_angle
    assert row[ps.ColumnNames.ROTATION_ANGLE] == machine.layer_rotation_angle
    assert row[ps.ColumnNames.STRIPE_WIDTH] == machine.slicing_stripe_width
    assert row[ps.ColumnNames.TYPE] == ps.SimulationType.POROSITY
    assert row[ps.ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ps.ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ps.ColumnNames.POROSITY_SIZE_X] == 1e-3
    assert row[ps.ColumnNames.POROSITY_SIZE_Y] == 2e-3
    assert row[ps.ColumnNames.POROSITY_SIZE_Z] == 3e-3
    assert row[ps.ColumnNames.RELATIVE_DENSITY] == 12


def test_add_results_with_single_bead_summary_adds_row():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    melt_pool_msg = test_utils.get_test_melt_pool_message()
    input = SingleBeadInput(
        id="id",
        bead_length=0.01,
        machine=machine,
        material=material,
    )
    summary = SingleBeadSummary(input, melt_pool_msg)
    expected_build_rate = ps.ParametricStudy.build_rate(
        machine.scan_speed,
        machine.layer_thickness,
    )
    median_mp = summary.melt_pool.data_frame.median()
    expected_dw = (
        median_mp[MeltPoolColumnNames.REFERENCE_DEPTH]
        / median_mp[MeltPoolColumnNames.REFERENCE_WIDTH]
        if median_mp[MeltPoolColumnNames.REFERENCE_WIDTH]
        else np.nan
    )
    expected_lw = (
        median_mp[MeltPoolColumnNames.LENGTH] / median_mp[MeltPoolColumnNames.WIDTH]
        if median_mp[MeltPoolColumnNames.WIDTH]
        else np.nan
    )

    # act
    study.add_results([summary], iteration=98)

    # assert
    assert len(study.data_frame()) == 1
    row = study.data_frame().iloc[0]
    assert row[ps.ColumnNames.PROJECT] == "test_study"
    assert row[ps.ColumnNames.ITERATION] == 98
    assert row[ps.ColumnNames.ID] == "id"
    assert row[ps.ColumnNames.STATUS] == ps.SimulationStatus.COMPLETED
    assert row[ps.ColumnNames.MATERIAL] == material.name
    assert row[ps.ColumnNames.HEATER_TEMPERATURE] == machine.heater_temperature
    assert row[ps.ColumnNames.LAYER_THICKNESS] == machine.layer_thickness
    assert row[ps.ColumnNames.BEAM_DIAMETER] == machine.beam_diameter
    assert row[ps.ColumnNames.LASER_POWER] == machine.laser_power
    assert row[ps.ColumnNames.SCAN_SPEED] == machine.scan_speed
    assert row[ps.ColumnNames.HATCH_SPACING] == machine.hatch_spacing
    assert row[ps.ColumnNames.START_ANGLE] == machine.starting_layer_angle
    assert row[ps.ColumnNames.ROTATION_ANGLE] == machine.layer_rotation_angle
    assert row[ps.ColumnNames.STRIPE_WIDTH] == machine.slicing_stripe_width
    assert row[ps.ColumnNames.TYPE] == ps.SimulationType.SINGLE_BEAD
    assert row[ps.ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ps.ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ps.ColumnNames.SINGLE_BEAD_LENGTH] == 0.01
    assert row[ps.ColumnNames.MELT_POOL_DEPTH] == median_mp[MeltPoolColumnNames.DEPTH]
    assert row[ps.ColumnNames.MELT_POOL_WIDTH] == median_mp[MeltPoolColumnNames.WIDTH]
    assert row[ps.ColumnNames.MELT_POOL_LENGTH] == median_mp[MeltPoolColumnNames.LENGTH]
    assert (
        row[ps.ColumnNames.MELT_POOL_REFERENCE_DEPTH]
        == median_mp[MeltPoolColumnNames.REFERENCE_DEPTH]
    )
    assert (
        row[ps.ColumnNames.MELT_POOL_REFERENCE_WIDTH]
        == median_mp[MeltPoolColumnNames.REFERENCE_WIDTH]
    )
    assert row[ps.ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] == expected_dw
    assert row[ps.ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH] == expected_lw


def test_add_results_with_microstructure_summary_adds_row():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    user_data_path = os.path.join(tempfile.gettempdir(), "microstructure_summary_init")
    if not os.path.exists(user_data_path):
        os.makedirs(user_data_path)
    input = MicrostructureInput(id="id", random_seed=123, machine=machine, material=material)
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
    summary = MicrostructureSummary(input, result, user_data_path)
    expected_build_rate = ps.ParametricStudy.build_rate(
        machine.scan_speed, machine.layer_thickness, machine.hatch_spacing
    )

    # act
    study.add_results([summary], iteration=99)

    # assert
    assert len(study.data_frame()) == 1
    row = study.data_frame().iloc[0]
    assert row[ps.ColumnNames.PROJECT] == "test_study"
    assert row[ps.ColumnNames.ITERATION] == 99
    assert row[ps.ColumnNames.ID] == "id"
    assert row[ps.ColumnNames.STATUS] == ps.SimulationStatus.COMPLETED
    assert row[ps.ColumnNames.MATERIAL] == material.name
    assert row[ps.ColumnNames.HEATER_TEMPERATURE] == machine.heater_temperature
    assert row[ps.ColumnNames.LAYER_THICKNESS] == machine.layer_thickness
    assert row[ps.ColumnNames.BEAM_DIAMETER] == machine.beam_diameter
    assert row[ps.ColumnNames.LASER_POWER] == machine.laser_power
    assert row[ps.ColumnNames.SCAN_SPEED] == machine.scan_speed
    assert row[ps.ColumnNames.HATCH_SPACING] == machine.hatch_spacing
    assert row[ps.ColumnNames.START_ANGLE] == machine.starting_layer_angle
    assert row[ps.ColumnNames.ROTATION_ANGLE] == machine.layer_rotation_angle
    assert row[ps.ColumnNames.STRIPE_WIDTH] == machine.slicing_stripe_width
    assert row[ps.ColumnNames.TYPE] == ps.SimulationType.MICROSTRUCTURE
    assert row[ps.ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ps.ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ps.ColumnNames.MICRO_MIN_X] == input.sample_min_x
    assert row[ps.ColumnNames.MICRO_MIN_Y] == input.sample_min_y
    assert row[ps.ColumnNames.MICRO_MIN_Z] == input.sample_min_z
    assert row[ps.ColumnNames.MICRO_SIZE_X] == input.sample_size_x
    assert row[ps.ColumnNames.MICRO_SIZE_Y] == input.sample_size_y
    assert row[ps.ColumnNames.MICRO_SIZE_Z] == input.sample_size_z
    assert row[ps.ColumnNames.MICRO_SENSOR_DIM] == input.sensor_dimension
    assert row[ps.ColumnNames.RANDOM_SEED] == 123
    assert row[ps.ColumnNames.XY_AVERAGE_GRAIN_SIZE] == summary.xy_average_grain_size
    assert row[ps.ColumnNames.XZ_AVERAGE_GRAIN_SIZE] == summary.xz_average_grain_size
    assert row[ps.ColumnNames.YZ_AVERAGE_GRAIN_SIZE] == summary.yz_average_grain_size

    # clean up
    shutil.rmtree(user_data_path)
