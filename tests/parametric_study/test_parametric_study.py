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

import os
import platform
import shutil
from unittest.mock import PropertyMock, create_autospec, patch
import uuid

from ansys.api.additive.v0.additive_domain_pb2 import (
    GrainStatistics,
    MicrostructureResult,
    PorosityResult,
)
import dill
import numpy as np
import pandas as pd
import pytest

from ansys.additive.core import (
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
import ansys.additive.core.parametric_study as ps
from ansys.additive.core.parametric_study.parametric_runner import ParametricRunner
from ansys.additive.core.parametric_study.parametric_utils import build_rate
from tests import test_utils


def test_init_saves_study_to_file(tmp_path: pytest.TempPathFactory):
    # arrange
    study_name = "test_study"
    expected_path = tmp_path / f"{study_name}.ps"
    study = ps.ParametricStudy(tmp_path / study_name)

    # assert
    assert study.file_name == expected_path.absolute()
    assert study.file_name.is_file()


def test_load_raises_exception_when_file_does_not_exist(tmp_path: pytest.TempPathFactory):
    # arrange
    filename = str(uuid.uuid4())
    # act, assert
    with pytest.raises(ValueError, match="is not a valid file"):
        ps.ParametricStudy.load(filename)


def test_load_raises_exception_for_unpickled_file(tmp_path: pytest.TempPathFactory):
    # arrange
    filename = tmp_path / "unpickled_file.ps"
    with open(filename, "w") as f:
        f.write("test")
    # act, assert
    with pytest.raises(Exception, match="could not find MARK"):
        ps.ParametricStudy.load(filename)


def test_load_raises_exception_when_file_not_parametric_study(tmp_path: pytest.TempPathFactory):
    # arrange
    filename = tmp_path / "nonstudy.ps"
    contents = [1, 2, 3, 4, 5]
    with open(filename, "wb") as f:
        dill.dump(contents, f)
    # act, assert
    with pytest.raises(ValueError, match="is not a parametric study"):
        ps.ParametricStudy.load(filename)


def test_update_format_raises_exception_when_version_too_great(tmp_path: pytest.TempPathFactory):
    # arrange
    with patch(
        "ansys.additive.core.parametric_study.ParametricStudy.format_version",
        new_callable=PropertyMock,
    ) as mock_format_version:
        study = ps.ParametricStudy(tmp_path / "test_study")
        mock_format_version.return_value = ps.FORMAT_VERSION + 1
        filename = tmp_path / "invalid_format_version.ps"
        # act, assert
        with pytest.raises(ValueError, match="Unsupported version"):
            ps.ParametricStudy.update_format(study)


@pytest.mark.skipif(platform.system() != "Windows", reason="Test only valid on Windows.")
def test_load_reads_linux_file_on_windows(tmp_path: pytest.TempPathFactory):
    # arrange
    filename = test_utils.get_test_file_path("linux.ps")

    # act
    study = ps.ParametricStudy.load(filename)

    # assert
    assert study != None


@pytest.mark.skipif(platform.system() == "Windows", reason="Test only valid on Linux.")
def test_load_reads_windows_file_on_linux(tmp_path: pytest.TempPathFactory):
    # arrange
    filename = test_utils.get_test_file_path("windows.ps")

    # act
    study = ps.ParametricStudy.load(filename)

    # assert
    assert study != None


def test_save_and_load_returns_original_object(tmp_path: pytest.TempPathFactory):
    # arrange
    study_name = tmp_path / "test_study.ps"
    test_path = tmp_path / "parametric_save_and_load_test" / "study_copy.ps"
    study = ps.ParametricStudy(study_name)

    # act
    study.save(test_path)
    study2 = ps.ParametricStudy.load(test_path)

    # assert
    assert study.data_frame().equals(study2.data_frame())
    assert study2.file_name == test_path
    assert study.file_name == study_name


def test_add_summaries_with_porosity_summary_adds_row(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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
    expected_build_rate = build_rate(
        machine.scan_speed, machine.layer_thickness, machine.hatch_spacing
    )

    # act
    study.add_summaries([summary], iteration=99)

    # assert
    assert len(study.data_frame()) == 1
    row = study.data_frame().iloc[0]
    assert row[ps.ColumnNames.ITERATION] == 99
    assert row[ps.ColumnNames.ID] == "id"
    assert row[ps.ColumnNames.STATUS] == SimulationStatus.COMPLETED
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
    assert row[ps.ColumnNames.TYPE] == SimulationType.POROSITY
    assert row[ps.ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ps.ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ps.ColumnNames.POROSITY_SIZE_X] == 1e-3
    assert row[ps.ColumnNames.POROSITY_SIZE_Y] == 2e-3
    assert row[ps.ColumnNames.POROSITY_SIZE_Z] == 3e-3
    assert row[ps.ColumnNames.RELATIVE_DENSITY] == 12


def test_add_summaries_with_single_bead_summary_adds_row(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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
    expected_build_rate = build_rate(
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
    assert row[ps.ColumnNames.ITERATION] == 98
    assert row[ps.ColumnNames.ID] == "id"
    assert row[ps.ColumnNames.STATUS] == SimulationStatus.COMPLETED
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
    assert row[ps.ColumnNames.TYPE] == SimulationType.SINGLE_BEAD
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


def test_add_summaries_with_microstructure_summary_adds_row(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    user_data_path = tmp_path / "microstructure_summary_init"
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
    expected_build_rate = build_rate(
        machine.scan_speed, machine.layer_thickness, machine.hatch_spacing
    )

    # act
    study.add_summaries([summary], iteration=99)

    # assert
    assert len(study.data_frame()) == 1
    row = study.data_frame().iloc[0]
    assert row[ps.ColumnNames.ITERATION] == 99
    assert row[ps.ColumnNames.ID] == "id"
    assert row[ps.ColumnNames.STATUS] == SimulationStatus.COMPLETED
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
    assert row[ps.ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE
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


def test_add_summaries_with_unknown_summaries_raises_error(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    unknown_summary = "unknown_summary"

    # act/assert
    with pytest.raises(TypeError):
        study.add_summaries([unknown_summary])


def test_generate_single_bead_permutations_creates_permutations(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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
                            (df[ps.ColumnNames.ITERATION] == 0)
                            & (df[ps.ColumnNames.TYPE] == SimulationType.SINGLE_BEAD)
                            & (df[ps.ColumnNames.STATUS] == SimulationStatus.PENDING)
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


def test_generate_single_bead_permutations_filters_by_energy_density(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_generate_single_bead_permutations_only_adds_valid_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_generate_porosity_permutations_creates_permutations(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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
                                            (df[ps.ColumnNames.ITERATION] == 0)
                                            & (df[ps.ColumnNames.TYPE] == SimulationType.POROSITY)
                                            & (
                                                df[ps.ColumnNames.STATUS]
                                                == SimulationStatus.PENDING
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


def test_generate_porosity_permutations_filters_by_energy_density(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_generate_porosity_permutations_filters_by_build_rate(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_generate_porosity_permutations_only_adds_valid_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_generate_microstructure_permutations_creates_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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
                                            (df[ps.ColumnNames.ITERATION] == 9)
                                            & (
                                                df[ps.ColumnNames.TYPE]
                                                == SimulationType.MICROSTRUCTURE
                                            )
                                            & (
                                                df[ps.ColumnNames.STATUS]
                                                == SimulationStatus.PENDING
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


def test_generate_microstructure_permutations_converts_Nones_to_NANs_in_dataframe(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    powers = [50]
    scan_speeds = [1]

    # act
    study.generate_microstructure_permutations("material", powers, scan_speeds)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert np.isnan(df.loc[0, ps.ColumnNames.COOLING_RATE])
    assert np.isnan(df.loc[0, ps.ColumnNames.THERMAL_GRADIENT])
    assert np.isnan(df.loc[0, ps.ColumnNames.MICRO_MELT_POOL_WIDTH])
    assert np.isnan(df.loc[0, ps.ColumnNames.MICRO_MELT_POOL_DEPTH])
    assert np.isnan(df.loc[0, ps.ColumnNames.RANDOM_SEED])


def test_generate_microstructure_permutations_filters_by_energy_density(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_generate_microstructure_permutations_filters_by_build_rate(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_generate_microstructure_permutations_only_adds_valid_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_update_updates_error_status(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_update_updates_single_bead_permutation(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_update_updates_porosity_permutation(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_update_updates_microstructure_permutation(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    study.generate_microstructure_permutations("material", [50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ps.ColumnNames.ID]
    user_data_path = tmp_path / "ps_microstructure_update_test"
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


def test_update_raises_error_for_unknown_summary_type(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    summary = "invalid summary"

    # act
    with pytest.raises(TypeError):
        study.update([summary])


def test_add_inputs_creates_new_rows(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_add_inputs_does_not_create_new_rows_for_invalid_input(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    inputs = [
        "invalid input",
        "another one",
    ]

    # act
    study.add_inputs(inputs)

    # assert
    df = study.data_frame()
    assert len(df) == 0


def test_add_inputs_assigns_common_params_correctly(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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
    iteration = (7,)
    priority = (8,)
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


def test_add_inputs_assigns_porosity_params_correctly(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_add_inputs_assigns_all_microstructure_params_correctly(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_add_inputs_assigns_unspecified_microstructure_params_correctly(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
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


def test_run_simulations_calls_simulate_correctly(monkeypatch, tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    sb = SingleBeadInput()
    p = PorosityInput()
    ms = MicrostructureInput()
    study.add_inputs([sb, p, ms])
    mock_additive = create_autospec(Additive)
    # mock_additive.material.return_value = material
    patched_simulate = create_autospec(ParametricRunner.simulate, return_value=[])
    monkeypatch.setattr(ParametricRunner, "simulate", patched_simulate)

    # act
    study.run_simulations(mock_additive)

    # assert
    pd.testing.assert_frame_equal(patched_simulate.call_args[0][0], study.data_frame())
    assert patched_simulate.call_args[0][1] == mock_additive


def test_run_simulations_with_priority_calls_simulate_correctly(
    monkeypatch, tmp_path: pytest.TempPathFactory
):
    study = ps.ParametricStudy(tmp_path / "test_study")
    sb1 = SingleBeadInput(id="test_1")
    sb2 = SingleBeadInput(id="test_2")
    sb3 = SingleBeadInput(id="test_3")
    study.add_inputs([sb1], priority=1)
    study.add_inputs([sb2], priority=2)
    study.add_inputs([sb3], priority=3)
    mock_additive = create_autospec(Additive)
    # mock_additive.material.return_value = material
    patched_simulate = create_autospec(ParametricRunner.simulate, return_value=[])
    monkeypatch.setattr(ParametricRunner, "simulate", patched_simulate)

    # act
    study.run_simulations(mock_additive, priority=2)

    # assert
    assert patched_simulate.call_args[1]["priority"] == 2


def test_run_simulations_with_iteration_calls_simulate_correctly(
    monkeypatch, tmp_path: pytest.TempPathFactory
):
    study = ps.ParametricStudy(tmp_path / "test_study")
    sb1 = SingleBeadInput(id="test_1")
    sb2 = SingleBeadInput(id="test_2")
    sb3 = SingleBeadInput(id="test_3")
    study.add_inputs([sb1], iteration=1)
    study.add_inputs([sb2], iteration=2)
    study.add_inputs([sb3], iteration=3)
    mock_additive = create_autospec(Additive)
    # mock_additive.material.return_value = material
    patched_simulate = create_autospec(ParametricRunner.simulate, return_value=[])
    monkeypatch.setattr(ParametricRunner, "simulate", patched_simulate)

    # act
    study.run_simulations(mock_additive, iteration=2)

    # assert
    assert patched_simulate.call_args[1]["iteration"] == 2


def test_remove_deletes_multiple_rows_from_dataframe(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    for i in range(4):
        study.add_inputs([SingleBeadInput(id=f"test_id_{i}")])
    df1 = study.data_frame()
    ids = ["test_id_0", "test_id_1"]

    # act
    study.remove(ids)

    # assert
    df2 = study.data_frame()
    assert len(df1) == 4
    assert len(df2) == 2
    assert len(df2[df2[ps.ColumnNames.ID].isin(ids)]) == 0


def test_remove_deletes_single_row_from_dataframe(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    for i in range(4):
        study.add_inputs([SingleBeadInput(id=f"test_id_{i}")])
    df1 = study.data_frame()

    # act
    study.remove("test_id_0")

    # assert
    df2 = study.data_frame()
    assert len(df1) == 4
    assert len(df2) == 3
    assert len(df2[df2[ps.ColumnNames.ID] == "test_id_0"]) == 0


def test_set_status_changes_status(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    for i in range(4):
        study.add_inputs([SingleBeadInput(id=f"test_id_{i}")])
    status1 = study.data_frame()[ps.ColumnNames.STATUS]

    # act
    study.set_status(["test_id_0", "test_id_1"], SimulationStatus.SKIP)

    # assert
    status2 = study.data_frame()[ps.ColumnNames.STATUS]
    for i in range(len(status1)):
        if i in [0, 1]:
            assert status2[i] == SimulationStatus.SKIP
            assert status1[i] != status2[i]
        else:
            assert status2[i] == status1[i]


def test_set_status_changes_status_for_single_id(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    for i in range(4):
        study.add_inputs([SingleBeadInput(id=f"test_id_{i}")])
    status1 = study.data_frame()[ps.ColumnNames.STATUS]

    # act
    study.set_status("test_id_0", SimulationStatus.SKIP)

    # assert
    status2 = study.data_frame()[ps.ColumnNames.STATUS]
    for i in range(len(status1)):
        if i == 0:
            assert status2[i] == SimulationStatus.SKIP
            assert status1[i] != status2[i]
        else:
            assert status2[i] == status1[i]


def test_create_unique_id_returns_unique_id(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    study.add_inputs([SingleBeadInput(id="test_id_1")])

    # act
    id = study._create_unique_id(prefix="test_id_1")
    id2 = study._create_unique_id()

    # assert
    assert id.startswith("test_id_1")
    assert id != "test_id_1"
    assert id2.startswith("sim_")
    assert len(id2) > len("sim_")


def test_clear_removes_all_rows_but_not_columns(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    study.add_inputs([SingleBeadInput(id="test_id_1")])
    df1 = study.data_frame()

    # act
    study.clear()

    # assert
    df2 = study.data_frame()
    assert len(df1) == 1
    assert len(df2) == 0
    assert len(df1.columns) == len(df2.columns)
    assert len(df2.columns) > 0


def test_format_version_returns_proper_version(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")

    # act, assert
    assert study.format_version == ps.FORMAT_VERSION


@pytest.mark.skipif(platform.system() != "Windows", reason="Test only valid on Windows.")
def test_update_format_updates_version_1_to_latest(tmp_path: pytest.TempPathFactory):
    # arrange
    v1_file = tmp_path / "version1.ps"
    shutil.copyfile(test_utils.get_test_file_path("v1.ps"), v1_file)
    with open(v1_file, "rb") as f:
        v1_study = dill.load(f)
    # Ensure our source study is version 1. If format_version is not present, assume version 1.
    assert "Heater Temp (°C)" in v1_study.data_frame().columns
    latest_file = tmp_path / "latest.ps"
    v1_study.file_name = latest_file

    # act
    latest_study = ps.ParametricStudy.update_format(v1_study)

    # assert
    assert latest_study is not None
    assert os.path.isfile(latest_file)
    assert latest_study.format_version == ps.FORMAT_VERSION
    columns = latest_study.data_frame().columns
    assert ps.ColumnNames.HEATER_TEMPERATURE in columns
    assert ps.ColumnNames.START_ANGLE in columns
    assert ps.ColumnNames.ROTATION_ANGLE in columns
    assert ps.ColumnNames.COOLING_RATE in columns
    assert ps.ColumnNames.THERMAL_GRADIENT in columns
    assert ps.ColumnNames.XY_AVERAGE_GRAIN_SIZE in columns
    assert ps.ColumnNames.XZ_AVERAGE_GRAIN_SIZE in columns
    assert ps.ColumnNames.YZ_AVERAGE_GRAIN_SIZE in columns
    assert ps.ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH in columns
    assert ps.ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH in columns


def test_set_priority_sets_priority(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    for i in range(4):
        study.add_inputs([SingleBeadInput(id=f"test_id_{i}")])
    priority1 = study.data_frame()[ps.ColumnNames.PRIORITY]

    # act
    study.set_priority(["test_id_0", "test_id_1"], 5)

    # assert
    priority2 = study.data_frame()[ps.ColumnNames.PRIORITY]
    for i in range(len(priority1)):
        if i in [0, 1]:
            assert priority2[i] == 5
            assert priority1[i] != priority2[i]
        else:
            assert priority2[i] == priority1[i]


def test_set_iteration_sets_iteration(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ps.ParametricStudy(tmp_path / "test_study")
    for i in range(4):
        study.add_inputs([SingleBeadInput(id=f"test_id_{i}")])
    iteration1 = study.data_frame()[ps.ColumnNames.ITERATION]

    # act
    study.set_iteration(["test_id_0", "test_id_1"], 5)

    # assert
    iteration2 = study.data_frame()[ps.ColumnNames.ITERATION]
    for i in range(len(iteration1)):
        if i in [0, 1]:
            assert iteration2[i] == 5
            assert iteration1[i] != iteration2[i]
        else:
            assert iteration2[i] == iteration1[i]
