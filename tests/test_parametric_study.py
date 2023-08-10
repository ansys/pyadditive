# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import math
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
    MachineConstants,
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


def test_energy_density_calulcates_correctly():
    # arrange
    # act
    # assert
    assert ps.ParametricStudy.energy_density(24, 2, 3, 4) == 1
    assert ps.ParametricStudy.energy_density(6, 2, 3) == 1
    assert math.isnan(ps.ParametricStudy.energy_density(6, 0, 3, 4))


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
    assert row[ps.ColumnNames.COOLING_RATE] == 1.2e6
    assert row[ps.ColumnNames.THERMAL_GRADIENT] == 3.4e6
    assert row[ps.ColumnNames.MICRO_MELT_POOL_WIDTH] == 0.5e-3
    assert row[ps.ColumnNames.MICRO_MELT_POOL_DEPTH] == 0.6e-3
    assert row[ps.ColumnNames.XY_AVERAGE_GRAIN_SIZE] == summary.xy_average_grain_size
    assert row[ps.ColumnNames.XZ_AVERAGE_GRAIN_SIZE] == summary.xz_average_grain_size
    assert row[ps.ColumnNames.YZ_AVERAGE_GRAIN_SIZE] == summary.yz_average_grain_size

    # clean up
    shutil.rmtree(user_data_path)


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
