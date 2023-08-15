# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import math
import os
import shutil
import tempfile
from unittest import TestCase
from unittest.mock import create_autospec

from ansys.api.additive.v0.additive_domain_pb2 import (
    GrainStatistics,
    MicrostructureResult,
    PorosityResult,
)
import pandas as pd
import numpy as np
import pytest

from ansys.additive import (
    Additive,
    AdditiveMachine,
    AdditiveMaterial,
    MachineConstants,
    MeltPool,
    MeltPoolColumnNames,
    MicrostructureInput,
    MicrostructureSummary,
    PorosityInput,
    PorositySummary,
    SimulationError,
    SimulationStatus,
    SimulationType,
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
    study2.generate_single_bead_permutations("material", [100], [1])

    # act, assert
    assert study != study2


def test_build_rate_calculates_correctly():
    # arrange
    # act
    # assert
    assert ps.ParametricStudy.build_rate(2, 3, 4) == 24
    assert ps.ParametricStudy.build_rate(2, 3) == 6


def test_energy_density_calulcates_correctly():
    # arrange
    # act
    # assert
    assert ps.ParametricStudy.energy_density(24, 2, 3, 4) == 1
    assert ps.ParametricStudy.energy_density(6, 2, 3) == 1
    assert math.isnan(ps.ParametricStudy.energy_density(6, 0, 3, 4))


def test_add_summaries_with_porosity_summary_adds_row():
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
    study.add_summaries([summary], iteration=99)

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


def test_add_summaries_with_single_bead_summary_adds_row():
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
    median_mp = summary.melt_pool.data_frame().median()
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
    study.add_summaries([summary], iteration=98)

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


def test_add_summaries_with_microstructure_summary_adds_row():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    user_data_path = os.path.join(tempfile.gettempdir(), "microstructure_summary_init")
    if not os.path.exists(user_data_path):
        os.makedirs(user_data_path)
    input = MicrostructureInput(
        id="id",
        machine=machine,
        material=material,
        random_seed=123,
        use_provided_thermal_parameters=True,
        cooling_rate=1.2e6,
        thermal_gradient=3.4e6,
        melt_pool_width=0.5e-3,
        melt_pool_depth=0.6e-3,
    )
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
    study.add_summaries([summary], iteration=99)

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
    assert row[ps.ColumnNames.COOLING_RATE] == 1.2e6
    assert row[ps.ColumnNames.THERMAL_GRADIENT] == 3.4e6
    assert row[ps.ColumnNames.MICRO_MELT_POOL_WIDTH] == 0.5e-3
    assert row[ps.ColumnNames.MICRO_MELT_POOL_DEPTH] == 0.6e-3
    assert row[ps.ColumnNames.XY_AVERAGE_GRAIN_SIZE] == summary.xy_average_grain_size
    assert row[ps.ColumnNames.XZ_AVERAGE_GRAIN_SIZE] == summary.xz_average_grain_size
    assert row[ps.ColumnNames.YZ_AVERAGE_GRAIN_SIZE] == summary.yz_average_grain_size

    # clean up
    shutil.rmtree(user_data_path)

def test_add_summaries_with_unknown_summaries_raises_error():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    unknown_summary = "unknown_summary"

    # act/assert
    with pytest.raises(TypeError):
        study.add_summaries([unknown_summary])

def test_add_summaries_with_unknown_summaries_raises_error():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    unknown_summary = "unknown_summary"

    # act/assert
    with pytest.raises(TypeError):
        study.add_summaries([unknown_summary])


def test_generate_single_bead_permutations_creates_permutations():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    bead_length = 0.005
    powers = [50, 250, 700]
    scan_speeds = [0.35, 1, 2.4]
    layer_thicknesses = [30e-6, 50e-6]
    heater_temperatures = [80, 100]
    beam_diameters = [2e-5]

    # act
    study.generate_single_bead_permutations(
        "material",
        powers,
        scan_speeds,
        bead_length=bead_length,
        layer_thicknesses=layer_thicknesses,
        heater_temperatures=heater_temperatures,
        beam_diameters=beam_diameters,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 36
    for p in powers:
        for v in scan_speeds:
            for l in layer_thicknesses:
                for t in heater_temperatures:
                    for d in beam_diameters:
                        assert any(
                            (df[ps.ColumnNames.PROJECT] == "test_study")
                            & (df[ps.ColumnNames.ITERATION] == 0)
                            & (df[ps.ColumnNames.TYPE] == ps.SimulationType.SINGLE_BEAD)
                            & (df[ps.ColumnNames.STATUS] == ps.SimulationStatus.PENDING)
                            & (df[ps.ColumnNames.MATERIAL] == "material")
                            & (df[ps.ColumnNames.HEATER_TEMPERATURE] == t)
                            & (df[ps.ColumnNames.LAYER_THICKNESS] == l)
                            & (df[ps.ColumnNames.BEAM_DIAMETER] == d)
                            & (df[ps.ColumnNames.LASER_POWER] == p)
                            & (df[ps.ColumnNames.SCAN_SPEED] == v)
                            & (df[ps.ColumnNames.START_ANGLE].isnull())
                            & (df[ps.ColumnNames.ROTATION_ANGLE].isnull())
                            & (df[ps.ColumnNames.HATCH_SPACING].isnull())
                            & (df[ps.ColumnNames.STRIPE_WIDTH].isnull())
                            & (df[ps.ColumnNames.ENERGY_DENSITY].notnull())
                            & (df[ps.ColumnNames.BUILD_RATE].notnull())
                            & (df[ps.ColumnNames.SINGLE_BEAD_LENGTH] == bead_length)
                        )


def test_generate_single_bead_permutations_filters_by_energy_density():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [50, 250, 700]
    scan_speeds = [1]
    layer_thicknesses = [50e-6]
    min_energy_density = 1.1e6
    max_energy_density = 5.1e6

    # act
    study.generate_single_bead_permutations(
        "material",
        powers,
        scan_speeds,
        layer_thicknesses=layer_thicknesses,
        min_area_energy_density=min_energy_density,
        max_area_energy_density=max_energy_density,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.LASER_POWER] == 250


def test_generate_single_bead_permutations_only_adds_valid_permutations():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [
        MachineConstants.MIN_LASER_POWER - 1,
        MachineConstants.DEFAULT_LASER_POWER,
        MachineConstants.MAX_LASER_POWER + 1,
    ]
    scan_speeds = [
        MachineConstants.MIN_SCAN_SPEED - 1,
        MachineConstants.DEFAULT_SCAN_SPEED,
        MachineConstants.MAX_SCAN_SPEED + 1,
    ]

    # act
    study.generate_single_bead_permutations("material", powers, scan_speeds)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.LASER_POWER] == MachineConstants.DEFAULT_LASER_POWER
    assert df.loc[0, ps.ColumnNames.SCAN_SPEED] == MachineConstants.DEFAULT_SCAN_SPEED


def test_generate_porosity_permutations_creates_permutations():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [50, 250, 700]
    scan_speeds = [0.35, 1, 2.4]
    layer_thicknesses = [30e-6, 50e-6]
    heater_temperatures = [80, 100]
    beam_diameters = [2e-5]
    start_angles = [22.5, 0]
    rotation_angles = [30]
    hatch_spacings = [1e-4]
    stripe_widths = [0.05]
    size_x = 0.001
    size_y = 0.002
    size_z = 0.003

    # act
    study.generate_porosity_permutations(
        "material",
        powers,
        scan_speeds,
        size_x=size_x,
        size_y=size_y,
        size_z=size_z,
        layer_thicknesses=layer_thicknesses,
        heater_temperatures=heater_temperatures,
        beam_diameters=beam_diameters,
        start_angles=start_angles,
        rotation_angles=rotation_angles,
        hatch_spacings=hatch_spacings,
        stripe_widths=stripe_widths,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 72
    for p in powers:
        for v in scan_speeds:
            for l in layer_thicknesses:
                for t in heater_temperatures:
                    for d in beam_diameters:
                        for a in start_angles:
                            for r in rotation_angles:
                                for h in hatch_spacings:
                                    for w in stripe_widths:
                                        assert any(
                                            (df[ps.ColumnNames.PROJECT] == "test_study")
                                            & (df[ps.ColumnNames.ITERATION] == 0)
                                            & (
                                                df[ps.ColumnNames.TYPE]
                                                == ps.SimulationType.POROSITY
                                            )
                                            & (
                                                df[ps.ColumnNames.STATUS]
                                                == ps.SimulationStatus.PENDING
                                            )
                                            & (df[ps.ColumnNames.MATERIAL] == "material")
                                            & (df[ps.ColumnNames.HEATER_TEMPERATURE] == t)
                                            & (df[ps.ColumnNames.LAYER_THICKNESS] == l)
                                            & (df[ps.ColumnNames.BEAM_DIAMETER] == d)
                                            & (df[ps.ColumnNames.LASER_POWER] == p)
                                            & (df[ps.ColumnNames.SCAN_SPEED] == v)
                                            & (df[ps.ColumnNames.START_ANGLE] == a)
                                            & (df[ps.ColumnNames.ROTATION_ANGLE] == r)
                                            & (df[ps.ColumnNames.HATCH_SPACING] == h)
                                            & (df[ps.ColumnNames.STRIPE_WIDTH] == w)
                                            & (df[ps.ColumnNames.ENERGY_DENSITY].notnull())
                                            & (df[ps.ColumnNames.BUILD_RATE].notnull())
                                            & (df[ps.ColumnNames.POROSITY_SIZE_X] == size_x)
                                            & (df[ps.ColumnNames.POROSITY_SIZE_Y] == size_y)
                                            & (df[ps.ColumnNames.POROSITY_SIZE_Z] == size_z)
                                        )


def test_generate_porosity_permutations_filters_by_energy_density():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [50, 250, 700]
    scan_speeds = [1]
    layer_thicknesses = [50e-6]
    hatch_spacings = [1e-4]
    min_energy_density = 1.1e10
    max_energy_density = 5.1e10

    # act
    study.generate_porosity_permutations(
        "material",
        powers,
        scan_speeds,
        layer_thicknesses=layer_thicknesses,
        hatch_spacings=hatch_spacings,
        min_energy_density=min_energy_density,
        max_energy_density=max_energy_density,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.LASER_POWER] == 250


def test_generate_porosity_permutations_filters_by_build_rate():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [50]
    scan_speeds = [1]
    layer_thicknesses = [30e-6, 50e-6, 90e-6]
    hatch_spacings = [1e-4]
    min_build_rate = 31e-10
    max_build_rate = 89e-10

    # act
    study.generate_porosity_permutations(
        "material",
        powers,
        scan_speeds,
        layer_thicknesses=layer_thicknesses,
        hatch_spacings=hatch_spacings,
        min_build_rate=min_build_rate,
        max_build_rate=max_build_rate,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.LAYER_THICKNESS] == 50e-6


def test_generate_porosity_permutations_only_adds_valid_permutations():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [
        MachineConstants.MIN_LASER_POWER - 1,
        MachineConstants.DEFAULT_LASER_POWER,
        MachineConstants.MAX_LASER_POWER + 1,
    ]
    scan_speeds = [
        MachineConstants.MIN_SCAN_SPEED - 1,
        MachineConstants.DEFAULT_SCAN_SPEED,
        MachineConstants.MAX_SCAN_SPEED + 1,
    ]

    # act
    study.generate_porosity_permutations("material", powers, scan_speeds)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.LASER_POWER] == MachineConstants.DEFAULT_LASER_POWER
    assert df.loc[0, ps.ColumnNames.SCAN_SPEED] == MachineConstants.DEFAULT_SCAN_SPEED


def test_generate_microstructure_permutations_creates_permutations():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [50, 250, 700]
    scan_speeds = [0.35, 1, 2.4]
    layer_thicknesses = [30e-6, 50e-6]
    heater_temperatures = [80, 100]
    beam_diameters = [2e-5]
    start_angles = [22.5, 0]
    rotation_angles = [30]
    hatch_spacings = [1e-4]
    stripe_widths = [0.05]
    min_x = 1
    min_y = 2
    min_z = 3
    size_x = 0.001
    size_y = 0.002
    size_z = 0.003
    cooling_rate = MicrostructureInput.DEFAULT_COOLING_RATE
    thermal_gradient = MicrostructureInput.DEFAULT_THERMAL_GRADIENT
    melt_pool_width = MicrostructureInput.DEFAULT_MELT_POOL_WIDTH
    melt_pool_depth = MicrostructureInput.DEFAULT_MELT_POOL_DEPTH
    random_seed = 1234

    # act
    study.generate_microstructure_permutations(
        "material",
        powers,
        scan_speeds,
        min_x=min_x,
        min_y=min_y,
        min_z=min_z,
        size_x=size_x,
        size_y=size_y,
        size_z=size_z,
        layer_thicknesses=layer_thicknesses,
        heater_temperatures=heater_temperatures,
        beam_diameters=beam_diameters,
        start_angles=start_angles,
        rotation_angles=rotation_angles,
        hatch_spacings=hatch_spacings,
        stripe_widths=stripe_widths,
        cooling_rate=cooling_rate,
        thermal_gradient=thermal_gradient,
        melt_pool_width=melt_pool_width,
        melt_pool_depth=melt_pool_depth,
        random_seed=random_seed,
        iteration=9,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 72
    for p in powers:
        for v in scan_speeds:
            for l in layer_thicknesses:
                for t in heater_temperatures:
                    for d in beam_diameters:
                        for a in start_angles:
                            for r in rotation_angles:
                                for h in hatch_spacings:
                                    for w in stripe_widths:
                                        assert any(
                                            (df[ps.ColumnNames.PROJECT] == "test_study")
                                            & (df[ps.ColumnNames.ITERATION] == 9)
                                            & (
                                                df[ps.ColumnNames.TYPE]
                                                == ps.SimulationType.MICROSTRUCTURE
                                            )
                                            & (
                                                df[ps.ColumnNames.STATUS]
                                                == ps.SimulationStatus.PENDING
                                            )
                                            & (df[ps.ColumnNames.MATERIAL] == "material")
                                            & (df[ps.ColumnNames.HEATER_TEMPERATURE] == t)
                                            & (df[ps.ColumnNames.LAYER_THICKNESS] == l)
                                            & (df[ps.ColumnNames.BEAM_DIAMETER] == d)
                                            & (df[ps.ColumnNames.LASER_POWER] == p)
                                            & (df[ps.ColumnNames.SCAN_SPEED] == v)
                                            & (df[ps.ColumnNames.START_ANGLE] == a)
                                            & (df[ps.ColumnNames.ROTATION_ANGLE] == r)
                                            & (df[ps.ColumnNames.HATCH_SPACING] == h)
                                            & (df[ps.ColumnNames.STRIPE_WIDTH] == w)
                                            & (df[ps.ColumnNames.ENERGY_DENSITY].notnull())
                                            & (df[ps.ColumnNames.BUILD_RATE].notnull())
                                            & (df[ps.ColumnNames.MICRO_MIN_X] == min_x)
                                            & (df[ps.ColumnNames.MICRO_MIN_Y] == min_y)
                                            & (df[ps.ColumnNames.MICRO_MIN_Z] == min_z)
                                            & (df[ps.ColumnNames.MICRO_SIZE_X] == size_x)
                                            & (df[ps.ColumnNames.MICRO_SIZE_Y] == size_y)
                                            & (df[ps.ColumnNames.MICRO_SIZE_Z] == size_z)
                                            & (df[ps.ColumnNames.COOLING_RATE] == cooling_rate)
                                            & (
                                                df[ps.ColumnNames.THERMAL_GRADIENT]
                                                == thermal_gradient
                                            )
                                            & (
                                                df[ps.ColumnNames.MICRO_MELT_POOL_WIDTH]
                                                == melt_pool_width
                                            )
                                            & (
                                                df[ps.ColumnNames.MICRO_MELT_POOL_DEPTH]
                                                == melt_pool_depth
                                            )
                                            & (df[ps.ColumnNames.RANDOM_SEED] == random_seed)
                                        )


def test_generate_microstructure_permutations_filters_by_energy_density():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [50, 250, 700]
    scan_speeds = [1]
    layer_thicknesses = [50e-6]
    hatch_spacings = [1e-4]
    min_energy_density = 1.1e10
    max_energy_density = 5.1e10

    # act
    study.generate_microstructure_permutations(
        "material",
        powers,
        scan_speeds,
        layer_thicknesses=layer_thicknesses,
        hatch_spacings=hatch_spacings,
        min_energy_density=min_energy_density,
        max_energy_density=max_energy_density,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.LASER_POWER] == 250


def test_generate_microstructure_permutations_filters_by_build_rate():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [50]
    scan_speeds = [1]
    layer_thicknesses = [30e-6, 50e-6, 90e-6]
    hatch_spacings = [1e-4]
    min_build_rate = 31e-10
    max_build_rate = 89e-10

    # act
    study.generate_microstructure_permutations(
        "material",
        powers,
        scan_speeds,
        layer_thicknesses=layer_thicknesses,
        hatch_spacings=hatch_spacings,
        min_build_rate=min_build_rate,
        max_build_rate=max_build_rate,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.LAYER_THICKNESS] == 50e-6


def test_generate_microstructure_permutations_only_adds_valid_permutations():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    powers = [
        MachineConstants.MIN_LASER_POWER - 1,
        MachineConstants.DEFAULT_LASER_POWER,
        MachineConstants.MAX_LASER_POWER + 1,
    ]
    scan_speeds = [
        MachineConstants.MIN_SCAN_SPEED - 1,
        MachineConstants.DEFAULT_SCAN_SPEED,
        MachineConstants.MAX_SCAN_SPEED + 1,
    ]

    # act
    study.generate_microstructure_permutations("material", powers, scan_speeds)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.LASER_POWER] == MachineConstants.DEFAULT_LASER_POWER
    assert df.loc[0, ps.ColumnNames.SCAN_SPEED] == MachineConstants.DEFAULT_SCAN_SPEED

def test_update_updates_error_status():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    study.generate_single_bead_permutations("material", [50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ps.ColumnNames.ID]
    input = SingleBeadInput(id=id)
    error = SimulationError(input, "error message")

    # act
    study.update([error])

    # assert
    df2 = study.data_frame()
    assert len(df2) == len(df1) == 1
    assert df1.loc[0, ps.ColumnNames.STATUS] == SimulationStatus.PENDING
    assert df2.loc[0, ps.ColumnNames.STATUS] == SimulationStatus.ERROR
    assert df2.loc[0, ps.ColumnNames.ERROR_MESSAGE] == "error message"

def test_update_updates_single_bead_permutation():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    study.generate_single_bead_permutations("material", [50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ps.ColumnNames.ID]
    input = SingleBeadInput(id=id)
    mp_msg = test_utils.get_test_melt_pool_message()
    mp_median = MeltPool(mp_msg).data_frame().median()
    summary = SingleBeadSummary(input, mp_msg)

    # act
    study.update([summary])

    # assert
    df2 = study.data_frame()
    assert len(df2) == len(df1) == 1
    assert df1.loc[0, ps.ColumnNames.STATUS] == SimulationStatus.PENDING
    assert df2.loc[0, ps.ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert df2.loc[0, ps.ColumnNames.MELT_POOL_WIDTH] == mp_median[MeltPoolColumnNames.WIDTH]
    assert df2.loc[0, ps.ColumnNames.MELT_POOL_DEPTH] == mp_median[MeltPoolColumnNames.DEPTH]
    assert df2.loc[0, ps.ColumnNames.MELT_POOL_LENGTH] == mp_median[MeltPoolColumnNames.LENGTH]
    assert df2.loc[0, ps.ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH] == (
        mp_median[MeltPoolColumnNames.LENGTH] / mp_median[MeltPoolColumnNames.WIDTH]
    )
    assert (
        df2.loc[0, ps.ColumnNames.MELT_POOL_REFERENCE_DEPTH]
        == mp_median[MeltPoolColumnNames.REFERENCE_DEPTH]
    )
    assert (
        df2.loc[0, ps.ColumnNames.MELT_POOL_REFERENCE_WIDTH]
        == mp_median[MeltPoolColumnNames.REFERENCE_WIDTH]
    )
    assert df2.loc[0, ps.ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] == (
        mp_median[MeltPoolColumnNames.REFERENCE_DEPTH]
        / mp_median[MeltPoolColumnNames.REFERENCE_WIDTH]
    )


def test_update_updates_porosity_permutation():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    study.generate_porosity_permutations("material", [50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ps.ColumnNames.ID]
    input = PorosityInput(id=id)
    result = PorosityResult(
        void_ratio=10,
        powder_ratio=11,
        solid_ratio=12,
    )
    summary = PorositySummary(input, result)

    # act
    study.update([summary])

    # assert
    df2 = study.data_frame()
    assert len(df2) == len(df1) == 1
    assert df1.loc[0, ps.ColumnNames.STATUS] == SimulationStatus.PENDING
    assert df2.loc[0, ps.ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert df2.loc[0, ps.ColumnNames.RELATIVE_DENSITY] == 12


def test_update_updates_microstructure_permutation():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    study.generate_microstructure_permutations("material", [50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ps.ColumnNames.ID]
    user_data_path = os.path.join(tempfile.gettempdir(), "ps_microstructure_update_test")
    if not os.path.exists(user_data_path):
        os.makedirs(user_data_path)
    input = MicrostructureInput(id=id)
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

    # act
    study.update([summary])

    # assert
    df2 = study.data_frame()
    assert len(df2) == len(df1) == 1
    assert df1.loc[0, ps.ColumnNames.STATUS] == SimulationStatus.PENDING
    assert df2.loc[0, ps.ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert df2.loc[0, ps.ColumnNames.XY_AVERAGE_GRAIN_SIZE] == 6
    assert df2.loc[0, ps.ColumnNames.XZ_AVERAGE_GRAIN_SIZE] == 42
    assert df2.loc[0, ps.ColumnNames.YZ_AVERAGE_GRAIN_SIZE] == 110

def test_update_raises_error_for_unknown_summary_type():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    summary = "invalid summary"

    # act
    with pytest.raises(TypeError):
        study.update([summary])

def test_create_machine_assigns_all_values():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    power = 50
    speed = 1.2
    layer_thickness = 40e-6
    beam_diameter = 75e-6
    heater_temperature = 120
    start_angle = 15
    rotation_angle = 22
    hatch_spacing = 110e-6
    stripe_width = 5e-3
    series = pd.Series({
        ps.ColumnNames.LASER_POWER: power,
        ps.ColumnNames.SCAN_SPEED: speed,
        ps.ColumnNames.LAYER_THICKNESS: layer_thickness,
        ps.ColumnNames.BEAM_DIAMETER: beam_diameter,
        ps.ColumnNames.HEATER_TEMPERATURE: heater_temperature,
        ps.ColumnNames.START_ANGLE: start_angle,
        ps.ColumnNames.ROTATION_ANGLE: rotation_angle,
        ps.ColumnNames.HATCH_SPACING: hatch_spacing,
        ps.ColumnNames.STRIPE_WIDTH: stripe_width,
    })

    # act
    machine = study._ParametricStudy__create_machine(series)

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
        study = ps.ParametricStudy(project_name="test_study")
        power = 50
        speed = 1.2
        layer_thickness = 40e-6
        beam_diameter = 75e-6
        heater_temperature = 120
        series = pd.Series({
            ps.ColumnNames.LASER_POWER: power,
            ps.ColumnNames.SCAN_SPEED: speed,
            ps.ColumnNames.LAYER_THICKNESS: layer_thickness,
            ps.ColumnNames.BEAM_DIAMETER: beam_diameter,
            ps.ColumnNames.HEATER_TEMPERATURE: heater_temperature,
            ps.ColumnNames.START_ANGLE: float("nan"),
            ps.ColumnNames.ROTATION_ANGLE: float("nan"),
            ps.ColumnNames.HATCH_SPACING: float("nan"),
            ps.ColumnNames.STRIPE_WIDTH: float("nan"),
        })

        # act
        machine = study._ParametricStudy__create_machine(series)

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
    study = ps.ParametricStudy(project_name="test_study")
    id = "test_id"
    bead_length = 9.5e-3
    series = pd.Series({
        ps.ColumnNames.ID: id,
        ps.ColumnNames.SINGLE_BEAD_LENGTH: bead_length,
    })
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = study._create_single_bead_input(series, material=material, machine=machine)

    # assert
    assert isinstance(input, SingleBeadInput)
    assert input.id == id
    assert input.bead_length == bead_length
    assert input.machine == machine
    assert input.material == material

def test_create_porosity_input():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    id = "test_id"
    size_x = 1e-3
    size_y = 2e-3
    size_z = 3e-3
    series = pd.Series({
        ps.ColumnNames.ID: id,
        ps.ColumnNames.POROSITY_SIZE_X: size_x,
        ps.ColumnNames.POROSITY_SIZE_Y: size_y,
        ps.ColumnNames.POROSITY_SIZE_Z: size_z,
    })
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = study._create_porosity_input(series, material=material, machine=machine)

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
    study = ps.ParametricStudy(project_name="test_study")
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
    series = pd.Series({
        ps.ColumnNames.ID: id,
        ps.ColumnNames.MICRO_MIN_X: min_x,
        ps.ColumnNames.MICRO_MIN_Y: min_y,
        ps.ColumnNames.MICRO_MIN_Z: min_z,
        ps.ColumnNames.MICRO_SIZE_X: size_x,
        ps.ColumnNames.MICRO_SIZE_Y: size_y,
        ps.ColumnNames.MICRO_SIZE_Z: size_z,
        ps.ColumnNames.MICRO_SENSOR_DIM: sensor_dim,
        ps.ColumnNames.COOLING_RATE: cooling_rate,
        ps.ColumnNames.THERMAL_GRADIENT: thermal_gradient,
        ps.ColumnNames.MICRO_MELT_POOL_WIDTH: melt_pool_width,
        ps.ColumnNames.MICRO_MELT_POOL_DEPTH: melt_pool_depth,
        ps.ColumnNames.RANDOM_SEED: random_seed,
    })
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = study._create_microstructure_input(series, material=material, machine=machine)

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
    study = ps.ParametricStudy(project_name="test_study")
    id = "test_id"
    size_x = 1.1e-3
    size_y = 1.2e-3
    size_z = 1.3e-3
    sensor_dim = 1.4e-4
    series = pd.Series({
        ps.ColumnNames.ID: id,
        ps.ColumnNames.MICRO_MIN_X: float("nan"),
        ps.ColumnNames.MICRO_MIN_Y: float("nan"),
        ps.ColumnNames.MICRO_MIN_Z: float("nan"),
        ps.ColumnNames.MICRO_SIZE_X: size_x,
        ps.ColumnNames.MICRO_SIZE_Y: size_y,
        ps.ColumnNames.MICRO_SIZE_Z: size_z,
        ps.ColumnNames.MICRO_SENSOR_DIM: sensor_dim,
        ps.ColumnNames.COOLING_RATE: float("nan"),
        ps.ColumnNames.THERMAL_GRADIENT: float("nan"),
        ps.ColumnNames.MICRO_MELT_POOL_WIDTH: float("nan"),
        ps.ColumnNames.MICRO_MELT_POOL_DEPTH: float("nan"),
        ps.ColumnNames.RANDOM_SEED: float("nan"),
    })
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = study._create_microstructure_input(series, material=material, machine=machine)

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


def test_add_inputs_creates_new_rows():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    inputs = [
        SingleBeadInput(id="test_id_1"),
        PorosityInput(id="test_id_2"),
        MicrostructureInput(id="test_id_3"),
    ]

    # act
    study.add_inputs(inputs)

    # assert
    df = study.data_frame()
    assert len(df) == 3

def test_add_inputs_assigns_common_params_correctly():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    power = 50
    speed = 1.2
    layer_thickness = 40e-6
    beam_diameter = 75e-6
    heater_temperature = 120
    start_angle = 15
    rotation_angle = 22
    hatch_spacing = 110e-6
    stripe_width = 5e-3
    status = SimulationStatus.SKIP
    iteration = 7,
    priority = 8,
    machine = AdditiveMachine(
        laser_power=power,
        scan_speed=speed,
        layer_thickness=layer_thickness,
        beam_diameter=beam_diameter,
        heater_temperature=heater_temperature,
        starting_layer_angle=start_angle,
        layer_rotation_angle=rotation_angle,
        hatch_spacing=hatch_spacing,
        slicing_stripe_width=stripe_width,
    )
    material = AdditiveMaterial(name="test_material")
    input = SingleBeadInput(id="test_input", machine=machine, material=material)

    # act
    study.add_inputs([input], iteration=iteration, priority=priority, status=status)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.PROJECT] == "test_study"
    assert df.loc[0, ps.ColumnNames.ITERATION] == iteration
    assert df.loc[0, ps.ColumnNames.PRIORITY] == priority
    assert df.loc[0, ps.ColumnNames.ID] == "test_input"
    assert df.loc[0, ps.ColumnNames.STATUS] == status
    assert df.loc[0, ps.ColumnNames.MATERIAL] == "test_material"
    assert df.loc[0, ps.ColumnNames.LASER_POWER] == power
    assert df.loc[0, ps.ColumnNames.SCAN_SPEED] == speed
    assert df.loc[0, ps.ColumnNames.LAYER_THICKNESS] == layer_thickness
    assert df.loc[0, ps.ColumnNames.BEAM_DIAMETER] == beam_diameter
    assert df.loc[0, ps.ColumnNames.HEATER_TEMPERATURE] == heater_temperature
    assert df.loc[0, ps.ColumnNames.START_ANGLE] == start_angle
    assert df.loc[0, ps.ColumnNames.ROTATION_ANGLE] == rotation_angle
    assert df.loc[0, ps.ColumnNames.HATCH_SPACING] == hatch_spacing
    assert df.loc[0, ps.ColumnNames.STRIPE_WIDTH] == stripe_width

def test_add_inputs_assigns_porosity_params_correctly():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    size_x = 1.1e-3
    size_y = 1.2e-3
    size_z = 1.3e-3
    input = PorosityInput(size_x=size_x, size_y=size_y, size_z=size_z)

    # act
    study.add_inputs([input])

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.TYPE] == SimulationType.POROSITY
    assert df.loc[0, ps.ColumnNames.POROSITY_SIZE_X] == size_x
    assert df.loc[0, ps.ColumnNames.POROSITY_SIZE_Y] == size_y
    assert df.loc[0, ps.ColumnNames.POROSITY_SIZE_Z] == size_z


def test_add_inputs_assigns_all_microstructure_params_correctly():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    size_x = 1.1e-3
    size_y = 1.2e-3
    size_z = 1.3e-3
    min_x = 1
    min_y = 2
    min_z = 3
    sensor_dim = 1.4e-4
    cooling_rate = 1.5e6
    thermal_gradient = 1.6e6
    melt_pool_width = 1.7e-4
    melt_pool_depth = 1.8e-4
    random_seed = 1234
    input = MicrostructureInput(
        sample_min_x=min_x,
        sample_min_y=min_y,
        sample_min_z=min_z,
        sample_size_x=size_x,
        sample_size_y=size_y,
        sample_size_z=size_z,
        sensor_dimension=sensor_dim,
        use_provided_thermal_parameters=True,
        cooling_rate=cooling_rate,
        thermal_gradient=thermal_gradient,
        melt_pool_width=melt_pool_width,
        melt_pool_depth=melt_pool_depth,
        random_seed=random_seed,
    )

    # act
    study.add_inputs([input])

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE
    assert df.loc[0, ps.ColumnNames.MICRO_MIN_X] == min_x
    assert df.loc[0, ps.ColumnNames.MICRO_MIN_Y] == min_y
    assert df.loc[0, ps.ColumnNames.MICRO_MIN_Z] == min_z
    assert df.loc[0, ps.ColumnNames.MICRO_SIZE_X] == size_x
    assert df.loc[0, ps.ColumnNames.MICRO_SIZE_Y] == size_y
    assert df.loc[0, ps.ColumnNames.MICRO_SIZE_Z] == size_z
    assert df.loc[0, ps.ColumnNames.MICRO_SENSOR_DIM] == sensor_dim
    assert df.loc[0, ps.ColumnNames.COOLING_RATE] == cooling_rate
    assert df.loc[0, ps.ColumnNames.THERMAL_GRADIENT] == thermal_gradient
    assert df.loc[0, ps.ColumnNames.MICRO_MELT_POOL_WIDTH] == melt_pool_width
    assert df.loc[0, ps.ColumnNames.MICRO_MELT_POOL_DEPTH] == melt_pool_depth
    assert df.loc[0, ps.ColumnNames.RANDOM_SEED] == random_seed

def test_add_inputs_assigns_unspecified_microstructure_params_correctly():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    size_x = 1.1e-3
    size_y = 1.2e-3
    size_z = 1.3e-3
    sensor_dim = 1.4e-4
    input = MicrostructureInput(
        sample_size_x=size_x,
        sample_size_y=size_y,
        sample_size_z=size_z,
        sensor_dimension=sensor_dim,
    )

    # act
    study.add_inputs([input])

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ps.ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE
    assert df.loc[0, ps.ColumnNames.MICRO_MIN_X] == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert df.loc[0, ps.ColumnNames.MICRO_MIN_Y] == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert df.loc[0, ps.ColumnNames.MICRO_MIN_Z] == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert df.loc[0, ps.ColumnNames.MICRO_SIZE_X] == size_x
    assert df.loc[0, ps.ColumnNames.MICRO_SIZE_Y] == size_y
    assert df.loc[0, ps.ColumnNames.MICRO_SIZE_Z] == size_z
    assert df.loc[0, ps.ColumnNames.MICRO_SENSOR_DIM] == sensor_dim
    assert np.isnan(df.loc[0, ps.ColumnNames.COOLING_RATE])
    assert np.isnan(df.loc[0, ps.ColumnNames.THERMAL_GRADIENT])
    assert np.isnan(df.loc[0, ps.ColumnNames.MICRO_MELT_POOL_WIDTH])
    assert np.isnan(df.loc[0, ps.ColumnNames.MICRO_MELT_POOL_DEPTH])
    assert np.isnan(df.loc[0, ps.ColumnNames.RANDOM_SEED])


def test_run_simulations_calls_simulate_correctly():
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
    study.run_simulations(mock_additive)

    # assert
    mock_additive.simulate.assert_called_once_with(inputs)

def test_run_simulations_skips_simulations_with_missing_materials():
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
    study.run_simulations(mock_additive)

    # assert
    mock_additive.simulate.assert_called_once_with([sb, ms])

def test_remove_deletes_rows_from_dataframe():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    study.generate_single_bead_permutations("material", [50, 100], [1, 1.25])
    df1 = study.data_frame()

    # act
    study.remove([0, 1])

    # assert
    df2 = study.data_frame()
    assert len(df1) == 4
    assert len(df2) == 2

def test_set_status_changes_status():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    study.generate_single_bead_permutations("material", [50, 100], [1, 1.25])
    status1 = study.data_frame()[ps.ColumnNames.STATUS]

    # act
    study.set_status([0, 1], SimulationStatus.SKIP)

    # assert
    status2 = study.data_frame()[ps.ColumnNames.STATUS]
    for i in range(len(status1)):
        if i in [0, 1]:
            assert status2[i] == SimulationStatus.SKIP
            assert status1[i] != status2[i]
        else:
            assert status2[i] == status1[i]

def test_create_unique_id_returns_unique_id():
    # arrange
    study = ps.ParametricStudy(project_name="test_study")
    study.add_inputs([SingleBeadInput(id="test_id_1")])

    # act
    id = study._ParametricStudy__create_unique_id(prefix="test_id_1")
    id2 = study._ParametricStudy__create_unique_id()

    # assert
    assert id.startswith("test_id_1")
    assert id != "test_id_1"
    assert id2.startswith("sim_")
    assert len(id2) > len("sim_")