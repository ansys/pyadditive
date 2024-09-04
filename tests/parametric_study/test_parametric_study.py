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
import os
import pathlib
import platform
import shutil
import tempfile
from unittest.mock import Mock, PropertyMock, create_autospec, patch
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
from ansys.additive.core.parametric_study.constants import ColumnNames
from ansys.additive.core.parametric_study.parametric_study import FORMAT_VERSION, ParametricStudy
from ansys.additive.core.parametric_study.parametric_utils import build_rate
from tests import test_utils


def test_init_correctly_initializes_object(tmp_path: pytest.TempPathFactory):
    # arrange
    study_name = "test_study"
    expected_path = tmp_path / f"{study_name}.ps"
    study = ParametricStudy(tmp_path / study_name, "material")

    # assert
    assert study.file_name == expected_path.absolute()
    assert study.file_name.is_file()


def test_load_raises_exception_when_file_does_not_exist(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    filename = str(uuid.uuid4())
    # act, assert
    with pytest.raises(ValueError, match="is not a valid file"):
        ParametricStudy.load(filename)


def test_load_raises_exception_for_unpickled_file(tmp_path: pytest.TempPathFactory):
    # arrange
    filename = tmp_path / "unpickled_file.ps"
    with open(filename, "w") as f:
        f.write("test")
    # act, assert
    with pytest.raises(Exception, match="could not find MARK"):
        ParametricStudy.load(filename)


def test_load_raises_exception_when_file_not_parametric_study(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    filename = tmp_path / "nonstudy.ps"
    contents = [1, 2, 3, 4, 5]
    with open(filename, "wb") as f:
        dill.dump(contents, f)
    # act, assert
    with pytest.raises(ValueError, match="is not a parametric study"):
        ParametricStudy.load(filename)


def test_update_format_raises_exception_when_version_too_great(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    with patch(
        "ansys.additive.core.parametric_study.ParametricStudy.format_version",
        new_callable=PropertyMock,
    ) as mock_format_version:
        study = ParametricStudy(tmp_path / "test_study", "material")
        mock_format_version.return_value = FORMAT_VERSION + 1
        # act, assert
        with pytest.raises(ValueError, match="Unsupported version"):
            ParametricStudy.update_format(study)


# @pytest.mark.skipif(platform.system() != "Windows", reason="Test only valid on Windows.")
@pytest.mark.skip(reason="Invalid test data file.")
def test_load_reads_linux_file_on_windows(tmp_path: pytest.TempPathFactory):
    # arrange
    test_file = test_utils.get_test_file_path("linux.ps")
    temp_dir = tempfile.gettempdir()
    filename = os.path.join(temp_dir, "temp_file_name")
    shutil.copy2(test_file, filename)

    # act
    study = ParametricStudy.load(filename)

    # assert
    assert study is not None


@pytest.mark.skipif(platform.system() == "Windows", reason="Test only valid on Linux.")
def test_load_reads_windows_file_on_linux(tmp_path: pytest.TempPathFactory):
    # arrange
    filename = test_utils.get_test_file_path("windows.ps")

    # act
    study = ParametricStudy.load(filename)

    # assert
    assert study is not None


def test_save_and_load_returns_original_object(tmp_path: pytest.TempPathFactory):
    # arrange
    study_name = tmp_path / "test_study.ps"
    test_path = tmp_path / "parametric_save_and_load_test" / "study_copy.ps"
    study = ParametricStudy(study_name, "material")

    # act
    study.save(test_path)
    study2 = ParametricStudy.load(test_path)

    # assert
    assert study.data_frame().equals(study2.data_frame())
    assert study2.file_name == test_path
    assert study.file_name == study_name
    assert study2.material_name == study.material_name


def test_add_summaries_with_porosity_summary_adds_row(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    input = PorosityInput(
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
    assert row[ColumnNames.ITERATION] == 99
    assert row[ColumnNames.ID] == input.id
    assert row[ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert row[ColumnNames.MATERIAL] == material.name
    assert row[ColumnNames.HEATER_TEMPERATURE] == machine.heater_temperature
    assert row[ColumnNames.LAYER_THICKNESS] == machine.layer_thickness
    assert row[ColumnNames.BEAM_DIAMETER] == machine.beam_diameter
    assert row[ColumnNames.LASER_POWER] == machine.laser_power
    assert row[ColumnNames.SCAN_SPEED] == machine.scan_speed
    assert row[ColumnNames.HATCH_SPACING] == machine.hatch_spacing
    assert row[ColumnNames.START_ANGLE] == machine.starting_layer_angle
    assert row[ColumnNames.ROTATION_ANGLE] == machine.layer_rotation_angle
    assert row[ColumnNames.STRIPE_WIDTH] == machine.slicing_stripe_width
    assert row[ColumnNames.TYPE] == SimulationType.POROSITY
    assert row[ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ColumnNames.POROSITY_SIZE_X] == 1e-3
    assert row[ColumnNames.POROSITY_SIZE_Y] == 2e-3
    assert row[ColumnNames.POROSITY_SIZE_Z] == 3e-3
    assert row[ColumnNames.RELATIVE_DENSITY] == 12


def test_add_summaries_with_single_bead_summary_adds_row(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    melt_pool_msg = test_utils.get_test_melt_pool_message()
    input = SingleBeadInput(
        bead_length=0.01,
        machine=machine,
        material=material,
    )
    summary = SingleBeadSummary(input, melt_pool_msg, None)
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
    assert row[ColumnNames.ITERATION] == 98
    assert row[ColumnNames.ID] == input.id
    assert row[ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert row[ColumnNames.MATERIAL] == material.name
    assert row[ColumnNames.HEATER_TEMPERATURE] == machine.heater_temperature
    assert row[ColumnNames.LAYER_THICKNESS] == machine.layer_thickness
    assert row[ColumnNames.BEAM_DIAMETER] == machine.beam_diameter
    assert row[ColumnNames.LASER_POWER] == machine.laser_power
    assert row[ColumnNames.SCAN_SPEED] == machine.scan_speed
    assert row[ColumnNames.HATCH_SPACING] == machine.hatch_spacing
    assert row[ColumnNames.START_ANGLE] == machine.starting_layer_angle
    assert row[ColumnNames.ROTATION_ANGLE] == machine.layer_rotation_angle
    assert row[ColumnNames.STRIPE_WIDTH] == machine.slicing_stripe_width
    assert row[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD
    assert row[ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ColumnNames.SINGLE_BEAD_LENGTH] == 0.01
    assert row[ColumnNames.MELT_POOL_DEPTH] == median_mp[MeltPoolColumnNames.DEPTH]
    assert row[ColumnNames.MELT_POOL_WIDTH] == median_mp[MeltPoolColumnNames.WIDTH]
    assert row[ColumnNames.MELT_POOL_LENGTH] == median_mp[MeltPoolColumnNames.LENGTH]
    assert (
        row[ColumnNames.MELT_POOL_REFERENCE_DEPTH] == median_mp[MeltPoolColumnNames.REFERENCE_DEPTH]
    )
    assert (
        row[ColumnNames.MELT_POOL_REFERENCE_WIDTH] == median_mp[MeltPoolColumnNames.REFERENCE_WIDTH]
    )
    assert row[ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] == expected_dw
    assert row[ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH] == expected_lw


def test_add_summaries_with_microstructure_summary_adds_row(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    user_data_path = tmp_path / "microstructure_summary_init"
    input = MicrostructureInput(
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
    assert row[ColumnNames.ITERATION] == 99
    assert row[ColumnNames.ID] == input.id
    assert row[ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert row[ColumnNames.MATERIAL] == material.name
    assert row[ColumnNames.HEATER_TEMPERATURE] == machine.heater_temperature
    assert row[ColumnNames.LAYER_THICKNESS] == machine.layer_thickness
    assert row[ColumnNames.BEAM_DIAMETER] == machine.beam_diameter
    assert row[ColumnNames.LASER_POWER] == machine.laser_power
    assert row[ColumnNames.SCAN_SPEED] == machine.scan_speed
    assert row[ColumnNames.HATCH_SPACING] == machine.hatch_spacing
    assert row[ColumnNames.START_ANGLE] == machine.starting_layer_angle
    assert row[ColumnNames.ROTATION_ANGLE] == machine.layer_rotation_angle
    assert row[ColumnNames.STRIPE_WIDTH] == machine.slicing_stripe_width
    assert row[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE
    assert row[ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ColumnNames.MICRO_MIN_X] == input.sample_min_x
    assert row[ColumnNames.MICRO_MIN_Y] == input.sample_min_y
    assert row[ColumnNames.MICRO_MIN_Z] == input.sample_min_z
    assert row[ColumnNames.MICRO_SIZE_X] == input.sample_size_x
    assert row[ColumnNames.MICRO_SIZE_Y] == input.sample_size_y
    assert row[ColumnNames.MICRO_SIZE_Z] == input.sample_size_z
    assert row[ColumnNames.MICRO_SENSOR_DIM] == input.sensor_dimension
    assert row[ColumnNames.RANDOM_SEED] == 123
    assert row[ColumnNames.COOLING_RATE] == 1.2e6
    assert row[ColumnNames.THERMAL_GRADIENT] == 3.4e6
    assert row[ColumnNames.MICRO_MELT_POOL_WIDTH] == 0.5e-3
    assert row[ColumnNames.MICRO_MELT_POOL_DEPTH] == 0.6e-3
    assert row[ColumnNames.XY_AVERAGE_GRAIN_SIZE] == summary.xy_average_grain_size
    assert row[ColumnNames.XZ_AVERAGE_GRAIN_SIZE] == summary.xz_average_grain_size
    assert row[ColumnNames.YZ_AVERAGE_GRAIN_SIZE] == summary.yz_average_grain_size


def test_add_summaries_with_unknown_summaries_raises_error(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    unknown_summary = "unknown_summary"

    # act/assert
    with pytest.raises(TypeError):
        study.add_summaries([unknown_summary])


def test_add_summaries_returns_correct_number_of_added_summaries(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    input = PorosityInput(
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

    # act
    added = study.add_summaries([summary], iteration=99)
    re_added = study.add_summaries([summary], iteration=99)

    # assert
    assert added == 1
    assert re_added == 0


def test_add_summaries_removes_duplicate_entries(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    input = PorosityInput(
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

    # act
    study.add_summaries([summary], iteration=1)
    study.add_summaries([summary], iteration=2)

    # assert
    assert len(study.data_frame()) == 1


@pytest.mark.parametrize("input_status", [(SimulationStatus.NEW), (SimulationStatus.SKIP)])
def test_add_summaries_overwrites_duplicate_entries_with_simulation_status_completed(
    input_status,
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    material_name = "material"
    study = ParametricStudy(tmp_path / "test_study", material_name)
    machine = AdditiveMachine()
    material = AdditiveMaterial(name=material_name)
    input_sb_1 = SingleBeadInput(
        bead_length=0.01,
        machine=machine,
        material=material,
    )
    melt_pool_msg = test_utils.get_test_melt_pool_message()
    summary = SingleBeadSummary(input_sb_1, melt_pool_msg, None)
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
    study.add_inputs([input_sb_1], iteration=2, status=input_status)
    study.add_summaries([summary], iteration=1)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    row = study.data_frame().iloc[0]
    assert row[ColumnNames.ITERATION] == 1
    assert row[ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert row[ColumnNames.MATERIAL] == material.name
    assert row[ColumnNames.HEATER_TEMPERATURE] == machine.heater_temperature
    assert row[ColumnNames.LAYER_THICKNESS] == machine.layer_thickness
    assert row[ColumnNames.BEAM_DIAMETER] == machine.beam_diameter
    assert row[ColumnNames.LASER_POWER] == machine.laser_power
    assert row[ColumnNames.SCAN_SPEED] == machine.scan_speed
    assert row[ColumnNames.HATCH_SPACING] == machine.hatch_spacing
    assert row[ColumnNames.START_ANGLE] == machine.starting_layer_angle
    assert row[ColumnNames.ROTATION_ANGLE] == machine.layer_rotation_angle
    assert row[ColumnNames.STRIPE_WIDTH] == machine.slicing_stripe_width
    assert row[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD
    assert row[ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ColumnNames.SINGLE_BEAD_LENGTH] == 0.01
    assert row[ColumnNames.MELT_POOL_DEPTH] == median_mp[MeltPoolColumnNames.DEPTH]
    assert row[ColumnNames.MELT_POOL_WIDTH] == median_mp[MeltPoolColumnNames.WIDTH]
    assert row[ColumnNames.MELT_POOL_LENGTH] == median_mp[MeltPoolColumnNames.LENGTH]
    assert (
        row[ColumnNames.MELT_POOL_REFERENCE_DEPTH] == median_mp[MeltPoolColumnNames.REFERENCE_DEPTH]
    )
    assert (
        row[ColumnNames.MELT_POOL_REFERENCE_WIDTH] == median_mp[MeltPoolColumnNames.REFERENCE_WIDTH]
    )
    assert row[ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] == expected_dw
    assert row[ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH] == expected_lw


def test_add_summaries_overwrites_duplicate_completed_simulations_with_newer_entry(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    machine = AdditiveMachine()
    material = test_utils.get_test_material()
    input1 = PorosityInput(
        size_x=1e-3,
        size_y=2e-3,
        size_z=3e-3,
        machine=machine,
        material=material,
    )
    input2 = PorosityInput(
        size_x=1e-3,
        size_y=2e-3,
        size_z=3e-3,
        machine=machine,
        material=material,
    )
    result1 = PorosityResult(
        void_ratio=11,
        powder_ratio=12,
        solid_ratio=13,
    )
    result2 = PorosityResult(
        void_ratio=10,
        powder_ratio=11,
        solid_ratio=12,
    )
    expected_build_rate = build_rate(
        machine.scan_speed, machine.layer_thickness, machine.hatch_spacing
    )
    summary1 = PorositySummary(input1, result1)
    summary2 = PorositySummary(input2, result2)

    # act
    study.add_summaries([summary1], iteration=1)
    study.add_summaries([summary2], iteration=2)

    # assert
    assert len(study.data_frame()) == 1
    row = study.data_frame().iloc[0]
    assert row[ColumnNames.ITERATION] == 2
    assert row[ColumnNames.ID] == input2.id
    assert row[ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert row[ColumnNames.MATERIAL] == material.name
    assert row[ColumnNames.HEATER_TEMPERATURE] == machine.heater_temperature
    assert row[ColumnNames.LAYER_THICKNESS] == machine.layer_thickness
    assert row[ColumnNames.BEAM_DIAMETER] == machine.beam_diameter
    assert row[ColumnNames.LASER_POWER] == machine.laser_power
    assert row[ColumnNames.SCAN_SPEED] == machine.scan_speed
    assert row[ColumnNames.HATCH_SPACING] == machine.hatch_spacing
    assert row[ColumnNames.START_ANGLE] == machine.starting_layer_angle
    assert row[ColumnNames.ROTATION_ANGLE] == machine.layer_rotation_angle
    assert row[ColumnNames.STRIPE_WIDTH] == machine.slicing_stripe_width
    assert row[ColumnNames.TYPE] == SimulationType.POROSITY
    assert row[ColumnNames.BUILD_RATE] == expected_build_rate
    assert row[ColumnNames.ENERGY_DENSITY] == machine.laser_power / expected_build_rate
    assert row[ColumnNames.POROSITY_SIZE_X] == 1e-3
    assert row[ColumnNames.POROSITY_SIZE_Y] == 2e-3
    assert row[ColumnNames.POROSITY_SIZE_Z] == 3e-3
    assert row[ColumnNames.RELATIVE_DENSITY] == 12


def test_generate_single_bead_permutations_creates_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    bead_length = 0.005
    powers = [50, 250, 700]
    scan_speeds = [0.35, 1, 2.4]
    layer_thicknesses = [30e-6, 50e-6]
    heater_temperatures = [80, 100]
    beam_diameters = [2e-5]

    # act
    study.generate_single_bead_permutations(
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
                            (df[ColumnNames.ITERATION] == 0)
                            & (df[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD)
                            & (df[ColumnNames.STATUS] == SimulationStatus.NEW)
                            & (df[ColumnNames.MATERIAL] == "material")
                            & (df[ColumnNames.HEATER_TEMPERATURE] == t)
                            & (df[ColumnNames.LAYER_THICKNESS] == l)
                            & (df[ColumnNames.BEAM_DIAMETER] == d)
                            & (df[ColumnNames.LASER_POWER] == p)
                            & (df[ColumnNames.SCAN_SPEED] == v)
                            & (df[ColumnNames.START_ANGLE].isnull())
                            & (df[ColumnNames.ROTATION_ANGLE].isnull())
                            & (df[ColumnNames.HATCH_SPACING].isnull())
                            & (df[ColumnNames.STRIPE_WIDTH].isnull())
                            & (df[ColumnNames.ENERGY_DENSITY].notnull())
                            & (df[ColumnNames.BUILD_RATE].notnull())
                            & (df[ColumnNames.SINGLE_BEAD_LENGTH] == bead_length)
                        )


def test_generate_single_bead_permutations_filters_by_energy_density(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    powers = [50, 250, 700]
    scan_speeds = [1]
    layer_thicknesses = [50e-6]
    min_energy_density = 1.1e6
    max_energy_density = 5.1e6

    # act
    study.generate_single_bead_permutations(
        powers,
        scan_speeds,
        layer_thicknesses=layer_thicknesses,
        min_area_energy_density=min_energy_density,
        max_area_energy_density=max_energy_density,
    )

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ColumnNames.LASER_POWER] == 250


def test_generate_single_bead_permutations_only_adds_valid_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
    study.generate_single_bead_permutations(powers, scan_speeds)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ColumnNames.LASER_POWER] == MachineConstants.DEFAULT_LASER_POWER
    assert df.loc[0, ColumnNames.SCAN_SPEED] == MachineConstants.DEFAULT_SCAN_SPEED


def test_generate_single_bead_permuations_returns_correct_number_of_simulations_added(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    bead_length = 0.005
    powers = [50, 250, 700]
    scan_speeds = [0.35, 1, 2.4]
    layer_thicknesses = [30e-6, 50e-6]
    heater_temperatures = [80, 100]
    beam_diameters = [2e-5]

    # act
    initial_num_sim_added = study.generate_single_bead_permutations(
        powers,
        scan_speeds,
        bead_length=bead_length,
        layer_thicknesses=layer_thicknesses,
        heater_temperatures=heater_temperatures,
        beam_diameters=beam_diameters,
    )

    duplicate_num_sim_added = study.generate_single_bead_permutations(
        powers,
        scan_speeds,
        bead_length=bead_length,
        layer_thicknesses=layer_thicknesses,
        heater_temperatures=heater_temperatures,
        beam_diameters=beam_diameters,
    )

    # assert
    assert initial_num_sim_added == 36
    assert duplicate_num_sim_added == 0


def test_generate_porosity_permutations_creates_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
                                            (df[ColumnNames.ITERATION] == 0)
                                            & (df[ColumnNames.TYPE] == SimulationType.POROSITY)
                                            & (df[ColumnNames.STATUS] == SimulationStatus.NEW)
                                            & (df[ColumnNames.MATERIAL] == "material")
                                            & (df[ColumnNames.HEATER_TEMPERATURE] == t)
                                            & (df[ColumnNames.LAYER_THICKNESS] == l)
                                            & (df[ColumnNames.BEAM_DIAMETER] == d)
                                            & (df[ColumnNames.LASER_POWER] == p)
                                            & (df[ColumnNames.SCAN_SPEED] == v)
                                            & (df[ColumnNames.START_ANGLE] == a)
                                            & (df[ColumnNames.ROTATION_ANGLE] == r)
                                            & (df[ColumnNames.HATCH_SPACING] == h)
                                            & (df[ColumnNames.STRIPE_WIDTH] == w)
                                            & (df[ColumnNames.ENERGY_DENSITY].notnull())
                                            & (df[ColumnNames.BUILD_RATE].notnull())
                                            & (df[ColumnNames.POROSITY_SIZE_X] == size_x)
                                            & (df[ColumnNames.POROSITY_SIZE_Y] == size_y)
                                            & (df[ColumnNames.POROSITY_SIZE_Z] == size_z)
                                        )


def test_generate_porosity_permutations_filters_by_energy_density(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    powers = [50, 250, 700]
    scan_speeds = [1]
    layer_thicknesses = [50e-6]
    hatch_spacings = [1e-4]
    min_energy_density = 1.1e10
    max_energy_density = 5.1e10

    # act
    study.generate_porosity_permutations(
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
    assert df.loc[0, ColumnNames.LASER_POWER] == 250


def test_generate_porosity_permutations_filters_by_build_rate(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    powers = [50]
    scan_speeds = [1]
    layer_thicknesses = [30e-6, 50e-6, 90e-6]
    hatch_spacings = [1e-4]
    min_build_rate = 31e-10
    max_build_rate = 89e-10

    # act
    study.generate_porosity_permutations(
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
    assert df.loc[0, ColumnNames.LAYER_THICKNESS] == 50e-6


def test_generate_porosity_permutations_only_adds_valid_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
    study.generate_porosity_permutations(powers, scan_speeds)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ColumnNames.LASER_POWER] == MachineConstants.DEFAULT_LASER_POWER
    assert df.loc[0, ColumnNames.SCAN_SPEED] == MachineConstants.DEFAULT_SCAN_SPEED


def test_generate_porosity_permutations_returns_correct_number_of_simulations_added(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
    initial_num_sim_added = study.generate_porosity_permutations(
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

    duplicate_num_sim_added = study.generate_porosity_permutations(
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
    assert initial_num_sim_added == 72
    assert duplicate_num_sim_added == 0


def test_generate_microstructure_permutations_creates_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
                                            (df[ColumnNames.ITERATION] == 9)
                                            & (
                                                df[ColumnNames.TYPE]
                                                == SimulationType.MICROSTRUCTURE
                                            )
                                            & (df[ColumnNames.STATUS] == SimulationStatus.NEW)
                                            & (df[ColumnNames.MATERIAL] == "material")
                                            & (df[ColumnNames.HEATER_TEMPERATURE] == t)
                                            & (df[ColumnNames.LAYER_THICKNESS] == l)
                                            & (df[ColumnNames.BEAM_DIAMETER] == d)
                                            & (df[ColumnNames.LASER_POWER] == p)
                                            & (df[ColumnNames.SCAN_SPEED] == v)
                                            & (df[ColumnNames.START_ANGLE] == a)
                                            & (df[ColumnNames.ROTATION_ANGLE] == r)
                                            & (df[ColumnNames.HATCH_SPACING] == h)
                                            & (df[ColumnNames.STRIPE_WIDTH] == w)
                                            & (df[ColumnNames.ENERGY_DENSITY].notnull())
                                            & (df[ColumnNames.BUILD_RATE].notnull())
                                            & (df[ColumnNames.MICRO_MIN_X] == min_x)
                                            & (df[ColumnNames.MICRO_MIN_Y] == min_y)
                                            & (df[ColumnNames.MICRO_MIN_Z] == min_z)
                                            & (df[ColumnNames.MICRO_SIZE_X] == size_x)
                                            & (df[ColumnNames.MICRO_SIZE_Y] == size_y)
                                            & (df[ColumnNames.MICRO_SIZE_Z] == size_z)
                                            & (df[ColumnNames.COOLING_RATE] == cooling_rate)
                                            & (df[ColumnNames.THERMAL_GRADIENT] == thermal_gradient)
                                            & (
                                                df[ColumnNames.MICRO_MELT_POOL_WIDTH]
                                                == melt_pool_width
                                            )
                                            & (
                                                df[ColumnNames.MICRO_MELT_POOL_DEPTH]
                                                == melt_pool_depth
                                            )
                                            & (df[ColumnNames.RANDOM_SEED] == random_seed)
                                        )


@pytest.mark.parametrize("value", [None, np.nan])
def test_generate_microstructure_with_Nones_NANs_succeeds(value, tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    powers = [50]
    scan_speeds = [1]
    cooling_rate = value
    thermal_gradient = value
    melt_pool_width = value
    melt_pool_depth = value
    random_seed = value

    # act
    result = study.generate_microstructure_permutations(
        powers,
        scan_speeds,
        cooling_rate=cooling_rate,
        thermal_gradient=thermal_gradient,
        melt_pool_width=melt_pool_width,
        melt_pool_depth=melt_pool_depth,
        random_seed=random_seed,
    )

    # assert
    assert result == 1
    df = study.data_frame()
    assert len(df) == 1
    assert np.isnan(df.loc[0, ColumnNames.COOLING_RATE])
    assert np.isnan(df.loc[0, ColumnNames.THERMAL_GRADIENT])
    assert np.isnan(df.loc[0, ColumnNames.MICRO_MELT_POOL_WIDTH])
    assert np.isnan(df.loc[0, ColumnNames.MICRO_MELT_POOL_DEPTH])
    assert np.isnan(df.loc[0, ColumnNames.RANDOM_SEED])


@pytest.mark.parametrize("value", [None, np.nan])
def test_validate_microstructure_with_Nones_NANs_succeeds(value, tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    d = {
        ColumnNames.MICRO_MIN_X: 0,
        ColumnNames.MICRO_MIN_Y: 0,
        ColumnNames.MICRO_MIN_Z: 0,
        ColumnNames.MICRO_SIZE_X: 0.0015,
        ColumnNames.MICRO_SIZE_Y: 0.002,
        ColumnNames.MICRO_SIZE_Z: 0.003,
        ColumnNames.MICRO_SENSOR_DIM: 0.001,
        ColumnNames.COOLING_RATE: value,
        ColumnNames.THERMAL_GRADIENT: value,
        ColumnNames.MICRO_MELT_POOL_WIDTH: value,
        ColumnNames.MICRO_MELT_POOL_DEPTH: value,
        ColumnNames.RANDOM_SEED: value,
    }
    series = pd.Series(d)

    # act
    result = study._validate_microstructure_input(
        AdditiveMachine(),
        AdditiveMaterial(name="material"),
        series,
    )

    # assert
    assert result[0]
    assert not result[1]


def test_generate_microstructure_permutations_converts_Nones_to_NANs_in_dataframe(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    powers = [50]
    scan_speeds = [1]

    # act
    study.generate_microstructure_permutations(powers, scan_speeds)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert np.isnan(df.loc[0, ColumnNames.COOLING_RATE])
    assert np.isnan(df.loc[0, ColumnNames.THERMAL_GRADIENT])
    assert np.isnan(df.loc[0, ColumnNames.MICRO_MELT_POOL_WIDTH])
    assert np.isnan(df.loc[0, ColumnNames.MICRO_MELT_POOL_DEPTH])
    assert np.isnan(df.loc[0, ColumnNames.RANDOM_SEED])


def test_generate_microstructure_permutations_filters_by_energy_density(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    powers = [50, 250, 700]
    scan_speeds = [1]
    layer_thicknesses = [50e-6]
    hatch_spacings = [1e-4]
    min_energy_density = 1.1e10
    max_energy_density = 5.1e10

    # act
    study.generate_microstructure_permutations(
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
    assert df.loc[0, ColumnNames.LASER_POWER] == 250


def test_generate_microstructure_permutations_filters_by_build_rate(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    powers = [50]
    scan_speeds = [1]
    layer_thicknesses = [30e-6, 50e-6, 90e-6]
    hatch_spacings = [1e-4]
    min_build_rate = 31e-10
    max_build_rate = 89e-10

    # act
    study.generate_microstructure_permutations(
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
    assert df.loc[0, ColumnNames.LAYER_THICKNESS] == 50e-6


def test_generate_microstructure_permutations_only_adds_valid_permutations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
    study.generate_microstructure_permutations(powers, scan_speeds)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ColumnNames.LASER_POWER] == MachineConstants.DEFAULT_LASER_POWER
    assert df.loc[0, ColumnNames.SCAN_SPEED] == MachineConstants.DEFAULT_SCAN_SPEED


def test_generate_microstructure_permutations_returns_correct_number_of_simulations_added(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
    initial_num_sim_added = study.generate_microstructure_permutations(
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

    duplicate_num_sim_added = study.generate_microstructure_permutations(
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
    assert initial_num_sim_added == 72
    assert duplicate_num_sim_added == 0


def test_update_updates_error_status(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.generate_single_bead_permutations([50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ColumnNames.ID]
    input = SingleBeadInput()
    # overwrite the id to match the one in the study
    input._id = id
    error = SimulationError(input, "error message")

    # act
    study.update([error])

    # assert
    df2 = study.data_frame()
    assert len(df2) == len(df1) == 1
    assert df1.loc[0, ColumnNames.STATUS] == SimulationStatus.NEW
    assert df2.loc[0, ColumnNames.STATUS] == SimulationStatus.ERROR
    assert df2.loc[0, ColumnNames.ERROR_MESSAGE] == "error message"


def test_update_updates_single_bead_permutation(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.generate_single_bead_permutations([50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ColumnNames.ID]
    input = SingleBeadInput()
    # overwrite the id to match the one in the study
    input._id = id
    mp_msg = test_utils.get_test_melt_pool_message()
    mp_median = MeltPool(mp_msg, tmp_path).data_frame().median()
    summary = SingleBeadSummary(input, mp_msg, None)

    # act
    study.update([summary])

    # assert
    df2 = study.data_frame()
    assert len(df2) == len(df1) == 1
    assert df1.loc[0, ColumnNames.STATUS] == SimulationStatus.NEW
    assert df2.loc[0, ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert df2.loc[0, ColumnNames.MELT_POOL_WIDTH] == mp_median[MeltPoolColumnNames.WIDTH]
    assert df2.loc[0, ColumnNames.MELT_POOL_DEPTH] == mp_median[MeltPoolColumnNames.DEPTH]
    assert df2.loc[0, ColumnNames.MELT_POOL_LENGTH] == mp_median[MeltPoolColumnNames.LENGTH]
    assert df2.loc[0, ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH] == (
        mp_median[MeltPoolColumnNames.LENGTH] / mp_median[MeltPoolColumnNames.WIDTH]
    )
    assert (
        df2.loc[0, ColumnNames.MELT_POOL_REFERENCE_DEPTH]
        == mp_median[MeltPoolColumnNames.REFERENCE_DEPTH]
    )
    assert (
        df2.loc[0, ColumnNames.MELT_POOL_REFERENCE_WIDTH]
        == mp_median[MeltPoolColumnNames.REFERENCE_WIDTH]
    )
    assert df2.loc[0, ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] == (
        mp_median[MeltPoolColumnNames.REFERENCE_DEPTH]
        / mp_median[MeltPoolColumnNames.REFERENCE_WIDTH]
    )


def test_update_updates_porosity_permutation(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.generate_porosity_permutations([50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ColumnNames.ID]
    input = PorosityInput()
    # overwrite the id to match the one in the study
    input._id = id
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
    assert df1.loc[0, ColumnNames.STATUS] == SimulationStatus.NEW
    assert df2.loc[0, ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert df2.loc[0, ColumnNames.RELATIVE_DENSITY] == 12


def test_update_updates_microstructure_permutation(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.generate_microstructure_permutations([50], [1])
    df1 = study.data_frame()
    id = df1.loc[0, ColumnNames.ID]
    user_data_path = tmp_path / "ps_microstructure_update_test"
    input = MicrostructureInput()
    # overwrite the id to match the one in the study
    input._id = id
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
    assert df1.loc[0, ColumnNames.STATUS] == SimulationStatus.NEW
    assert df2.loc[0, ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert df2.loc[0, ColumnNames.XY_AVERAGE_GRAIN_SIZE] == 6
    assert df2.loc[0, ColumnNames.XZ_AVERAGE_GRAIN_SIZE] == 42
    assert df2.loc[0, ColumnNames.YZ_AVERAGE_GRAIN_SIZE] == 110


def test_update_raises_error_for_unknown_summary_type(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    summary = "invalid summary"

    # act
    with pytest.raises(TypeError):
        study.update([summary])


def test_add_inputs_creates_new_rows(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    inputs = [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
    ]

    # act
    study.add_inputs(inputs)

    # assert
    df = study.data_frame()
    assert len(df) == 3
    assert len(df[df[ColumnNames.STATUS] == SimulationStatus.NEW]) == 3


def test_add_inputs_raises_error_for_invalid_input(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    inputs = [
        "invalid input",
        "another one",
    ]

    # act, assert
    with pytest.raises(TypeError, match="Invalid simulation input type"):
        study.add_inputs(inputs, status=SimulationStatus.NEW)


def test_add_inputs_returns_correct_number_of_added_inputs(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    inputs = [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
    ]

    # act
    added = study.add_inputs(inputs)
    re_added = study.add_inputs(inputs)

    # assert
    assert added == 3
    assert re_added == 0


def test_add_inputs_assigns_common_params_correctly(tmp_path: pytest.TempPathFactory):
    # arrange
    material_name = "test_material"
    study = ParametricStudy(tmp_path / "test_study", material_name)
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
    material = AdditiveMaterial(name=material_name)
    input = SingleBeadInput(machine=machine, material=material)

    # act
    study.add_inputs([input], iteration=iteration, priority=priority, status=status)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ColumnNames.ITERATION] == iteration
    assert df.loc[0, ColumnNames.PRIORITY] == priority
    assert df.loc[0, ColumnNames.ID] == input.id
    assert df.loc[0, ColumnNames.STATUS] == status
    assert df.loc[0, ColumnNames.MATERIAL] == "test_material"
    assert df.loc[0, ColumnNames.LASER_POWER] == power
    assert df.loc[0, ColumnNames.SCAN_SPEED] == speed
    assert df.loc[0, ColumnNames.LAYER_THICKNESS] == layer_thickness
    assert df.loc[0, ColumnNames.BEAM_DIAMETER] == beam_diameter
    assert df.loc[0, ColumnNames.HEATER_TEMPERATURE] == heater_temperature
    assert df.loc[0, ColumnNames.START_ANGLE] == start_angle
    assert df.loc[0, ColumnNames.ROTATION_ANGLE] == rotation_angle
    assert df.loc[0, ColumnNames.HATCH_SPACING] == hatch_spacing
    assert df.loc[0, ColumnNames.STRIPE_WIDTH] == stripe_width


def test_add_inputs_assigns_porosity_params_correctly(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    size_x = 1.1e-3
    size_y = 1.2e-3
    size_z = 1.3e-3
    input = PorosityInput(size_x=size_x, size_y=size_y, size_z=size_z)

    # act
    study.add_inputs([input])

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ColumnNames.TYPE] == SimulationType.POROSITY
    assert df.loc[0, ColumnNames.POROSITY_SIZE_X] == size_x
    assert df.loc[0, ColumnNames.POROSITY_SIZE_Y] == size_y
    assert df.loc[0, ColumnNames.POROSITY_SIZE_Z] == size_z


def test_add_inputs_assigns_all_microstructure_params_correctly(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
    assert df.loc[0, ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE
    assert df.loc[0, ColumnNames.MICRO_MIN_X] == min_x
    assert df.loc[0, ColumnNames.MICRO_MIN_Y] == min_y
    assert df.loc[0, ColumnNames.MICRO_MIN_Z] == min_z
    assert df.loc[0, ColumnNames.MICRO_SIZE_X] == size_x
    assert df.loc[0, ColumnNames.MICRO_SIZE_Y] == size_y
    assert df.loc[0, ColumnNames.MICRO_SIZE_Z] == size_z
    assert df.loc[0, ColumnNames.MICRO_SENSOR_DIM] == sensor_dim
    assert df.loc[0, ColumnNames.COOLING_RATE] == cooling_rate
    assert df.loc[0, ColumnNames.THERMAL_GRADIENT] == thermal_gradient
    assert df.loc[0, ColumnNames.MICRO_MELT_POOL_WIDTH] == melt_pool_width
    assert df.loc[0, ColumnNames.MICRO_MELT_POOL_DEPTH] == melt_pool_depth
    assert df.loc[0, ColumnNames.RANDOM_SEED] == random_seed


def test_add_inputs_assigns_unspecified_microstructure_params_correctly(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
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
    assert df.loc[0, ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE
    assert df.loc[0, ColumnNames.MICRO_MIN_X] == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert df.loc[0, ColumnNames.MICRO_MIN_Y] == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert df.loc[0, ColumnNames.MICRO_MIN_Z] == MicrostructureInput.DEFAULT_POSITION_COORDINATE
    assert df.loc[0, ColumnNames.MICRO_SIZE_X] == size_x
    assert df.loc[0, ColumnNames.MICRO_SIZE_Y] == size_y
    assert df.loc[0, ColumnNames.MICRO_SIZE_Z] == size_z
    assert df.loc[0, ColumnNames.MICRO_SENSOR_DIM] == sensor_dim
    assert np.isnan(df.loc[0, ColumnNames.COOLING_RATE])
    assert np.isnan(df.loc[0, ColumnNames.THERMAL_GRADIENT])
    assert np.isnan(df.loc[0, ColumnNames.MICRO_MELT_POOL_WIDTH])
    assert np.isnan(df.loc[0, ColumnNames.MICRO_MELT_POOL_DEPTH])
    assert np.isnan(df.loc[0, ColumnNames.RANDOM_SEED])


@pytest.mark.parametrize(
    "input_status, expected_len",
    [
        (SimulationStatus.NEW, 3),
        (SimulationStatus.SKIP, 3),
    ],
)
def test_add_inputs_only_adds_entries_with_simulation_status_pending_or_skip(
    input_status, expected_len, tmp_path: pytest.TempPathFactory
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    inputs = [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
    ]

    # act
    study.add_inputs(inputs, status=input_status)

    # assert
    df = study.data_frame()
    assert len(df) == expected_len


@pytest.mark.parametrize(
    "input_status",
    [
        (SimulationStatus.COMPLETED),
        (SimulationStatus.ERROR),
    ],
)
def test_add_inputs_raises_error_with_simulation_status_completed_or_error(
    input_status, tmp_path: pytest.TempPathFactory
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    inputs = [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
    ]

    # act, assert
    with pytest.raises(ValueError, match="Simulation status must be"):
        study.add_inputs(inputs, status=input_status)


def test_add_inputs_returns_correct_number_of_simulations_added_to_the_study(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    inputs = [
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
        SingleBeadInput(),
        PorosityInput(),
        MicrostructureInput(),
    ]

    # act
    added = study.add_inputs(inputs, status=SimulationStatus.NEW)

    # assert
    assert added == 3


@pytest.mark.parametrize("input_status", [(SimulationStatus.NEW), (SimulationStatus.SKIP)])
def test_add_inputs_overwrites_duplicate_entries_by_keeping_earlier_entry(
    input_status, tmp_path: pytest.TempPathFactory
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    input_sb_1 = SingleBeadInput(bead_length=0.001)
    input_p_1 = PorosityInput(size_x=0.001, size_y=0.001, size_z=0.001)
    input_m_1 = MicrostructureInput(sample_size_x=0.001, sample_size_y=0.001, sample_size_z=0.002)
    input_sb_1_duplicate = SingleBeadInput(bead_length=0.001)
    input_p_1_duplicate = PorosityInput(size_x=0.001, size_y=0.001, size_z=0.001)
    input_m_1_duplicate = MicrostructureInput(
        sample_size_x=0.001, sample_size_y=0.001, sample_size_z=0.002
    )

    inputs = [
        input_sb_1,
        input_p_1,
        input_m_1,
        input_sb_1_duplicate,
        input_p_1_duplicate,
        input_m_1_duplicate,
    ]

    # act
    study.add_inputs(inputs, iteration=1, priority=1, status=input_status)

    # assert

    df = study.data_frame()
    assert len(df) == 3
    assert df.loc[0, ColumnNames.ID] == input_sb_1.id
    assert df.loc[1, ColumnNames.ID] == input_p_1.id
    assert df.loc[2, ColumnNames.ID] == input_m_1.id


@pytest.mark.parametrize("input_status", [(SimulationStatus.NEW), (SimulationStatus.SKIP)])
def test_add_inputs_overwrites_duplicate_entries_with_priority_to_simulation_status_new(
    input_status, tmp_path: pytest.TempPathFactory
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    sb1 = SingleBeadInput()
    sb2 = SingleBeadInput()

    # act
    study.add_inputs([sb1], status=SimulationStatus.NEW)
    study.add_inputs([sb2], status=input_status)

    # assert
    df = study.data_frame()
    assert len(df) == 1
    assert df.loc[0, ColumnNames.STATUS] == SimulationStatus.NEW
    assert df.loc[0, ColumnNames.ID] == sb1.id


@pytest.mark.parametrize("input_status", [(SimulationStatus.NEW), (SimulationStatus.SKIP)])
def test_add_inputs_does_not_overwrite_simulation_with_status_completed(
    input_status, tmp_path: pytest.TempPathFactory
):
    # arrange
    material_name = "test_material"
    study = ParametricStudy(tmp_path / "test_study", material_name)
    sb = SingleBeadInput(material=AdditiveMaterial(name=material_name))
    melt_pool_msg = test_utils.get_test_melt_pool_message()
    summary = SingleBeadSummary(sb, melt_pool_msg, None)

    # act
    study.add_summaries([summary], iteration=1)
    study.add_inputs([sb], iteration=1, status=input_status)

    # assert
    df = study.data_frame()

    assert len(df) == 1
    assert df.loc[0, ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert df.loc[0, ColumnNames.ID] == sb.id


def test_remove_deletes_multiple_rows_from_dataframe(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    for i in range(4):
        study.add_inputs([SingleBeadInput(bead_length=(i + 1) * 0.001)])
    df1 = study.data_frame()
    ids = [df1.iloc[0][ColumnNames.ID], df1.iloc[1][ColumnNames.ID]]

    # act
    study.remove(ids)

    # assert
    df2 = study.data_frame()
    assert len(df1) == 4
    assert len(df2) == 2
    assert len(df2[df2[ColumnNames.ID].isin(ids)]) == 0


def test_remove_deletes_single_row_from_dataframe(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    for i in range(4):
        study.add_inputs([SingleBeadInput(bead_length=(i + 1) * 0.001)])
    df1 = study.data_frame()
    id = df1.iloc[0][ColumnNames.ID]

    # act
    study.remove(id)

    # assert
    df2 = study.data_frame()
    assert len(df1) == 4
    assert len(df2) == 3
    assert len(df2[df2[ColumnNames.ID] == id]) == 0


def test_set_simulation_status_changes_status(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    for i in range(4):
        study.add_inputs([SingleBeadInput(bead_length=(i + 1) * 0.001)])
    status1 = study.data_frame()[ColumnNames.STATUS]
    df = study.data_frame()
    ids = [
        df.iloc[0][ColumnNames.ID],
        df.iloc[1][ColumnNames.ID],
    ]

    # act
    study.set_simulation_status(ids, SimulationStatus.SKIP)

    # assert
    status2 = study.data_frame()[ColumnNames.STATUS]
    for i in range(len(status1)):
        if i in [0, 1]:
            assert status2[i] == SimulationStatus.SKIP
            assert status1[i] != status2[i]
        else:
            assert status2[i] == status1[i]


def test_set_simulation_status_updates_error_message(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    for i in range(4):
        study.add_inputs([SingleBeadInput(bead_length=(i + 1) * 0.001)])
    df = study.data_frame()
    ids = [
        df.iloc[0][ColumnNames.ID],
        df.iloc[1][ColumnNames.ID],
    ]
    error_message = "error message"

    # act
    study.set_simulation_status(ids, SimulationStatus.ERROR, error_message)

    # assert
    status2 = study.data_frame()[ColumnNames.STATUS]
    df = study.data_frame()
    for i in range(len(df)):
        if i in [0, 1]:
            assert status2[i] == SimulationStatus.ERROR
            assert df.iloc[i][ColumnNames.ERROR_MESSAGE] == "error message"
        else:
            assert status2[i] == SimulationStatus.NEW
            assert pd.isna(df.iloc[i][ColumnNames.ERROR_MESSAGE])


def test_set_simulation_status_changes_status_for_single_id(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    for i in range(4):
        study.add_inputs([SingleBeadInput(bead_length=(i + 1) * 0.001)])
    status1 = study.data_frame()[ColumnNames.STATUS]
    id = study.data_frame().iloc[0][ColumnNames.ID]

    # act
    study.set_simulation_status(id, SimulationStatus.SKIP)

    # assert
    status2 = study.data_frame()[ColumnNames.STATUS]
    for i in range(len(status1)):
        if i == 0:
            assert status2[i] == SimulationStatus.SKIP
            assert status1[i] != status2[i]
        else:
            assert status2[i] == status1[i]


def test_create_unique_id_returns_unique_id(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")

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
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
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
    study = ParametricStudy(tmp_path / "test_study", "material")

    # act, assert
    assert study.format_version == FORMAT_VERSION


@pytest.mark.skipif(platform.system() != "Windows", reason="Test only valid on Windows.")
def test_update_format_updates_version_1_to_latest(tmp_path: pytest.TempPathFactory):
    # arrange
    v1_file = tmp_path / "version1.ps"
    shutil.copyfile(test_utils.get_test_file_path("v1.with-simulations.ps"), v1_file)
    with open(v1_file, "rb") as f:
        v1_study = dill.load(f)
    # Ensure our source study is version 1. If format_version is not present, assume version 1.
    assert "Heater Temp (°C)" in v1_study.data_frame().columns
    latest_file = tmp_path / "latest.ps"
    v1_study.file_name = latest_file

    # act
    latest_study = ParametricStudy.update_format(v1_study)

    # assert
    assert latest_study is not None
    assert os.path.isfile(latest_file)
    assert latest_study.format_version == FORMAT_VERSION
    columns = latest_study.data_frame().columns
    assert ColumnNames.HEATER_TEMPERATURE in columns
    assert ColumnNames.START_ANGLE in columns
    assert ColumnNames.ROTATION_ANGLE in columns
    assert ColumnNames.COOLING_RATE in columns
    assert ColumnNames.THERMAL_GRADIENT in columns
    assert ColumnNames.XY_AVERAGE_GRAIN_SIZE in columns
    assert ColumnNames.XZ_AVERAGE_GRAIN_SIZE in columns
    assert ColumnNames.YZ_AVERAGE_GRAIN_SIZE in columns
    assert ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH in columns
    assert ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH in columns
    assert latest_study.material_name == "test-material"


@pytest.mark.skipif(platform.system() != "Windows", reason="Test only valid on Windows.")
def test_update_format_raises_error_when_no_simulations_present(tmp_path: pytest.TempPathFactory):
    # arrange
    # load a version 1 study with no simulations
    v1_file = tmp_path / "version1.ps"
    shutil.copyfile(test_utils.get_test_file_path("v1.no-simulations.ps"), v1_file)
    with open(v1_file, "rb") as f:
        v1_study = dill.load(f)
    # Ensure our source study is version 1. If format_version is not present, assume version 1.
    assert "Heater Temp (°C)" in v1_study.data_frame().columns
    v1_study.file_name = v1_file

    # act, assert
    with pytest.raises(ValueError, match="Unable to determine material"):
        ParametricStudy.update_format(v1_study)


def test_reset_simulation_status_sets_status_to_new(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput(), PorosityInput()])
    ids = study.data_frame()[ColumnNames.ID].array
    study.set_simulation_status(ids[0], SimulationStatus.RUNNING)
    study.set_simulation_status(ids[1], SimulationStatus.PENDING)

    # act
    study.reset_simulation_status()

    # assert
    df = study.data_frame()
    assert len(df) == 2
    for _, row in df.iterrows():
        assert row[ColumnNames.STATUS] == SimulationStatus.NEW


def test_clear_errors_clears_all_error_messages(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput(), PorosityInput()])
    study._data_frame[ColumnNames.ERROR_MESSAGE] = "Error message"
    assert not study._data_frame[ColumnNames.ERROR_MESSAGE].isna().any()

    # act
    study.clear_errors()

    # assert
    assert study._data_frame[ColumnNames.ERROR_MESSAGE].isna().all()


def test_clear_errors_clears_some_error_messages(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput(), PorosityInput()])
    study._data_frame[ColumnNames.ERROR_MESSAGE] = "Error message"
    assert not study._data_frame[ColumnNames.ERROR_MESSAGE].isna().any()
    id = study._data_frame[ColumnNames.ID].values[0]

    # act
    study.clear_errors([id])

    # assert
    assert study._data_frame[ColumnNames.ERROR_MESSAGE].isna().values[0]
    assert not study._data_frame[ColumnNames.ERROR_MESSAGE].isna().values[1]


def test_set_priority_sets_priority(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    for i in range(4):
        study.add_inputs([SingleBeadInput(bead_length=(i + 1) * 0.001)])
    priority1 = study.data_frame()[ColumnNames.PRIORITY]
    ids = study.data_frame().iloc[0:2][ColumnNames.ID].array

    # act
    study.set_priority(ids, 5)

    # assert
    priority2 = study.data_frame()[ColumnNames.PRIORITY]
    for i in range(len(priority1)):
        if i in [0, 1]:
            assert priority2[i] == 5
            assert priority1[i] != priority2[i]
        else:
            assert priority2[i] == priority1[i]


def test_set_iteration_sets_iteration(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    for i in range(4):
        study.add_inputs([SingleBeadInput(bead_length=(i + 1) * 0.001)])
    iteration1 = study.data_frame()[ColumnNames.ITERATION]
    ids = study.data_frame().iloc[0:2][ColumnNames.ID].array

    # act
    study.set_iteration(ids, 5)

    # assert
    iteration2 = study.data_frame()[ColumnNames.ITERATION]
    for i in range(len(iteration1)):
        if i in [0, 1]:
            assert iteration2[i] == 5
            assert iteration1[i] != iteration2[i]
        else:
            assert iteration2[i] == iteration1[i]


def test_import_csv_study_raises_exception_when_file_does_not_exist(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    filename = tmp_path / study_name

    # act
    study = ParametricStudy(tmp_path / study_name, "material")

    # assert
    with pytest.raises(ValueError, match="does not exist"):
        study.import_csv_study(filename)


def test_import_csv_study_raises_exception_when_file_is_not_a_csv(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    filename = __file__

    # act
    study = ParametricStudy(tmp_path / study_name, "material")

    # assert
    with pytest.raises(ValueError, match="does not have the expected columns"):
        study.import_csv_study(filename)


def test_import_csv_study_raises_exception_when_file_does_not_have_correct_headers(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    incorrect_headers_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "incorrect-headers.csv"
    )

    # act
    study = ParametricStudy(tmp_path / study_name, "material")

    # assert
    with pytest.raises(ValueError, match="does not have the expected columns"):
        study.import_csv_study(incorrect_headers_file)


def test_import_csv_study_adds_simulations_to_new_study(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    single_bead_demo_csv_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "single-bead-test-study.csv"
    )
    # act
    study = ParametricStudy(tmp_path / study_name, "material")
    errors = study.import_csv_study(single_bead_demo_csv_file)

    # assert
    assert len(errors) == 0
    assert len(study.data_frame()) == 5
    assert len(study.data_frame()[ColumnNames.LASER_POWER].unique()) == 5


def test_import_csv_study_adds_simulations_of_multiple_input_types_to_new_study(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    single_bead_demo_csv_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "single-bead-test-study.csv"
    )
    porosity_demo_csv_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "porosity-test-study.csv"
    )
    microstructure_demo_csv_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "microstructure-test-study.csv"
    )

    # act
    study = ParametricStudy(tmp_path / study_name, "material")
    errors = study.import_csv_study(single_bead_demo_csv_file)
    errors += study.import_csv_study(porosity_demo_csv_file)
    errors += study.import_csv_study(microstructure_demo_csv_file)

    # assert
    assert len(errors) == 0
    assert len(study.data_frame()) == 15
    assert len(study.data_frame().index) == len(study.data_frame().index.unique())


def test_import_csv_study_adds_simulations_to_existing_study(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    single_bead_demo_csv_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "single-bead-test-study.csv"
    )
    study = ParametricStudy(tmp_path / study_name, "material")
    powers = [50, 250, 700]
    scan_speeds = [0.35]
    study.generate_porosity_permutations(
        laser_powers=powers,
        scan_speeds=scan_speeds,
    )

    # act
    study.import_csv_study(single_bead_demo_csv_file)

    # assert
    assert len(study.data_frame()) == 8


@pytest.mark.parametrize(
    "file_name, argument",
    [
        ("completed-test-study.csv", True),
        ("pending-test-study.csv", False),
        ("skip-test-study.csv", False),
        ("error-test-study.csv", False),
    ],
)
def test_import_csv_study_calls_remove_duplicates_entries_correctly(
    monkeypatch, file_name, argument, tmp_path: pytest.TempPathFactory
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    csv_file = test_utils.get_test_file_path(pathlib.Path("csv") / file_name)
    patched_simulate = create_autospec(ParametricStudy._remove_duplicate_entries, return_value=0)
    monkeypatch.setattr(ParametricStudy, "_remove_duplicate_entries", patched_simulate)

    # act
    study.import_csv_study(csv_file)

    # assert
    assert patched_simulate.call_args[1]["overwrite"] == argument


def test_import_csv_study_drops_duplicates_with_correct_simulation_status_heirarchy(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    duplicate_rows_file = test_utils.get_test_file_path(pathlib.Path("csv") / "duplicate-rows.csv")
    study = ParametricStudy(tmp_path / study_name, "material")

    # act
    errors = study.import_csv_study(duplicate_rows_file)

    # assert
    df = study.data_frame()
    assert len(df) == 5
    assert df.iloc[0][ColumnNames.STATUS] == SimulationStatus.COMPLETED
    assert df.iloc[0][ColumnNames.ID] == "sb_c_d"
    assert df.iloc[1][ColumnNames.STATUS] == SimulationStatus.WARNING
    assert df.iloc[1][ColumnNames.ID] == "sb_w"
    assert df.iloc[2][ColumnNames.STATUS] == SimulationStatus.ERROR
    assert df.iloc[2][ColumnNames.ID] == "sb_e"
    assert df.iloc[3][ColumnNames.STATUS] == SimulationStatus.NEW
    assert df.iloc[3][ColumnNames.ID] == "sb_n"
    assert df.iloc[4][ColumnNames.STATUS] == SimulationStatus.SKIP
    assert df.iloc[4][ColumnNames.ID] == "sb_s"
    assert len(errors) == 1
    assert "Removed 5 duplicate simulation(s)." in errors[0]


def test_import_csv_study_does_not_add_simulations_with_invalid_inputs_and_returns_expected_error(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    invalid_input_parameters_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "invalid-input-parameter.csv"
    )

    # act
    study = ParametricStudy(tmp_path / study_name, "material")
    error_list = study.import_csv_study(invalid_input_parameters_file)

    # assert
    assert len(error_list) == 25
    for error_message in error_list:
        assert "Invalid parameter combination" in error_message


@pytest.mark.parametrize(
    "file_name, len_error_list",
    [
        ("single-bead-nan-input-parameters.csv", 6),
        ("porosity-nan-input-parameters.csv", 7),
        ("microstructure-nan-input-parameters.csv", 7),
    ],
)
def test_import_csv_study_does_not_add_simulations_with_nan_inputs_and_returns_expected_error(
    file_name,
    len_error_list,
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    nan_input_parameters_file = test_utils.get_test_file_path(pathlib.Path("csv") / file_name)

    # act
    study = ParametricStudy(tmp_path / study_name, "material")
    error_list = study.import_csv_study(nan_input_parameters_file)

    # assert
    assert len(error_list) == len_error_list
    for error_message in error_list:
        assert "must be a number" in error_message
    assert len(study.data_frame()) == 0


def test_import_csv_adds_microstructure_simulations_with_nan_thermal_parameter_values(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    nan_thermal_parameters_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "microstructure-nan-input-thermal-parameters.csv"
    )

    # act
    study = ParametricStudy(tmp_path / study_name, "material")
    error_list = study.import_csv_study(nan_thermal_parameters_file)

    # assert
    assert len(error_list) == 0
    assert len(study.data_frame()) == 4


def test_import_csv_study_does_not_add_simulations_with_invalid_status_or_type_and_returns_expected_error(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study_name = "test_study"
    invalid_type_status_file = test_utils.get_test_file_path(
        pathlib.Path("csv") / "invalid-type-status.csv"
    )

    # act
    study = ParametricStudy(tmp_path / study_name, "material")
    error_list = study.import_csv_study(invalid_type_status_file)

    # assert
    assert len(error_list) == 2
    assert "Invalid simulation type" in error_list[0]
    assert "Invalid simulation status" in error_list[1]


@patch("ansys.additive.core.parametric_study.ParametricStudy.filter_data_frame")
def test_simulation_inputs_calls_filter_data_frame(
    mock_filter_data_frame,
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    mock_filter_data_frame.return_value = study._data_frame

    def mock_client_call(name: str):
        return AdditiveMaterial(name=name)

    # act
    study.simulation_inputs(mock_client_call)

    # assert
    mock_filter_data_frame.assert_called_once()


def test_simulation_inputs_calls_client_call_for_material(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    material_name = "material"
    study = ParametricStudy(tmp_path / "test_study", material_name)
    study.add_inputs([SingleBeadInput()])

    mock_client_call = Mock(return_value=AdditiveMaterial(name=material_name))

    # act
    study.simulation_inputs(mock_client_call)

    # assert
    mock_client_call.assert_called_once_with(material_name)


def test_simulation_inputs_logs_warning_when_no_simulations_meet_criteria(
    tmp_path: pytest.TempPathFactory,
    caplog,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    caplog.set_level(logging.WARNING, logger="PyAdditive_global")

    def mock_client_call(name: str):
        return AdditiveMaterial(name=name)

    # act
    study.simulation_inputs(mock_client_call, types=[SimulationType.POROSITY])

    # assert
    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.levelname == "WARNING"
        assert "No simulations meet the specified crtiteria." in record.message


def test_filter_data_frame_sorts_by_priority(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()], priority=3)
    study.add_inputs([PorosityInput()], priority=2)
    study.add_inputs([MicrostructureInput()], priority=1)

    # act
    df = study.filter_data_frame()

    # assert
    assert df.iloc[0][ColumnNames.PRIORITY] == 1
    assert df.iloc[1][ColumnNames.PRIORITY] == 2
    assert df.iloc[2][ColumnNames.PRIORITY] == 3


def test_filter_data_frame_filters_by_priority(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()], priority=3)
    study.add_inputs([PorosityInput()], priority=2)
    study.add_inputs([MicrostructureInput()], priority=1)

    # act
    df = study.filter_data_frame(priority=1)

    # assert
    assert len(df) == 1
    assert df.iloc[0][ColumnNames.PRIORITY] == 1


def test_filter_data_frame_filters_by_iteration(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()], iteration=1)
    study.add_inputs([PorosityInput()], iteration=2)
    study.add_inputs([MicrostructureInput()], iteration=3)

    # act
    df = study.filter_data_frame(iteration=2)

    # assert
    assert len(df) == 1
    assert df.iloc[0][ColumnNames.ITERATION] == 2


def test_filter_data_frame_filters_by_simulation_type(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    study.add_inputs([PorosityInput()])
    study.add_inputs([MicrostructureInput()])

    # act
    df = study.filter_data_frame(types=[SimulationType.POROSITY])

    # assert
    assert len(df) == 1
    assert df.iloc[0][ColumnNames.TYPE] == SimulationType.POROSITY


def test_filter_data_frame_filters_by_multiple_simulation_types(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    study.add_inputs([PorosityInput()])
    study.add_inputs([MicrostructureInput()])

    # act
    df = study.filter_data_frame(types=[SimulationType.POROSITY, SimulationType.SINGLE_BEAD])

    # assert
    assert len(df) == 2
    types = df[ColumnNames.TYPE].array
    assert SimulationType.POROSITY in types
    assert SimulationType.SINGLE_BEAD in types


def test_filter_data_frame_filters_by_simulation_ids(tmp_path: pytest.TempPathFactory):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    study.add_inputs([PorosityInput()])
    study.add_inputs([MicrostructureInput()])
    ids = study.data_frame()[ColumnNames.ID].array

    # act
    df = study.filter_data_frame(simulation_ids=[ids[0], ids[2], "bogus"])

    # assert
    assert len(df) == 2
    assert df.iloc[0][ColumnNames.ID] in ids
    assert df.iloc[1][ColumnNames.ID] in ids
    assert df.iloc[0][ColumnNames.ID] != df.iloc[1][ColumnNames.ID]


@pytest.mark.parametrize(
    "simulation_ids_input",
    [
        [],
        None,
    ],
)
def test_filter_data_frame_skips_filter_by_simulation_ids_if_the_list_is_empty_or_none(
    simulation_ids_input, tmp_path: pytest.TempPathFactory
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    study.add_inputs([PorosityInput()])
    study.add_inputs([MicrostructureInput()])

    # act
    df = study.filter_data_frame(simulation_ids=simulation_ids_input)

    # assert
    assert len(df) == 3


def test_filter_data_frame_logs_warnings_for_simulation_ids_not_found(
    tmp_path: pytest.TempPathFactory, caplog
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    study.add_inputs([PorosityInput()])
    study.add_inputs([MicrostructureInput()])
    caplog.set_level(logging.WARNING, logger="PyAdditive_global")

    # act
    df = study.filter_data_frame(simulation_ids=["bogus", "bogus2"])

    # assert
    assert len(df) == 0
    assert len(caplog.records) == 2
    assert "Simulation ID 'bogus' not found in the parametric study" in caplog.records[0].message
    assert "Simulation ID 'bogus2' not found in the parametric study" in caplog.records[1].message


def test_filter_data_frame_logs_debug_for_duplicate_simulation_id(
    tmp_path: pytest.TempPathFactory, caplog
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    id = study._data_frame.iloc[0][ColumnNames.ID]
    caplog.set_level(logging.DEBUG, logger="PyAdditive_global")

    # act
    df = study.filter_data_frame(simulation_ids=[id, id])

    # assert
    assert len(df) == 1
    assert len(caplog.records) == 1
    assert "has already been added" in caplog.records[0].message


def test_filter_data_frame_filters_by_simulation_id_and_sorts_by_priority(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()], priority=3)
    study.add_inputs([PorosityInput()], priority=2)
    study.add_inputs([MicrostructureInput()], priority=1)
    ids = [
        study.data_frame().iloc[0][ColumnNames.ID],
        study.data_frame().iloc[2][ColumnNames.ID],
    ]

    # act
    df = study.filter_data_frame(simulation_ids=ids)

    # assert
    assert len(df) == 2
    assert df.iloc[0][ColumnNames.PRIORITY] == 1
    assert df.iloc[1][ColumnNames.PRIORITY] == 3


def test_filter_data_frame_filters_by_simulation_id_and_iteration(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()], iteration=1)
    study.add_inputs([PorosityInput()], iteration=2)
    study.add_inputs([MicrostructureInput()], iteration=1)
    ids = study.data_frame()[ColumnNames.ID].array
    # act
    df = study.filter_data_frame(simulation_ids=ids, iteration=1)

    # assert
    assert len(df) == 2
    assert SimulationType.SINGLE_BEAD in df[ColumnNames.TYPE].array
    assert SimulationType.MICROSTRUCTURE in df[ColumnNames.TYPE].array


def test_filter_data_frame_filters_by_simulation_id_and_type(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()])
    study.add_inputs([PorosityInput()])
    study.add_inputs([MicrostructureInput()])
    ids = [
        study.data_frame().iloc[0][ColumnNames.ID],
        study.data_frame().iloc[1][ColumnNames.ID],
    ]

    # act
    df = study.filter_data_frame(simulation_ids=ids, types=[SimulationType.POROSITY])

    # assert
    assert len(df) == 1
    assert df.iloc[0][ColumnNames.TYPE] == SimulationType.POROSITY


def test_filter_data_frame_filters_by_simulation_id_and_priority(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    study.add_inputs([SingleBeadInput()], priority=3)
    study.add_inputs([PorosityInput()], priority=2)
    study.add_inputs([MicrostructureInput()], priority=1)
    ids = [
        study.data_frame().iloc[0][ColumnNames.ID],
        study.data_frame().iloc[2][ColumnNames.ID],
    ]

    # act
    df = study.filter_data_frame(simulation_ids=ids, priority=1)

    # assert
    assert len(df) == 1
    assert df.iloc[0][ColumnNames.PRIORITY] == 1


def test_filter_data_frame_with_simulation_ids_ignores_status(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    material = AdditiveMaterial(name="test_material")
    ids = []
    for i, s in enumerate(SimulationStatus):
        sb = SingleBeadInput(bead_length=(0.001 + (i * 0.0001)), material=material)
        ids.append(sb.id)
        study.add_inputs([sb])
        study._data_frame.iloc[i, study._data_frame.columns.get_loc(ColumnNames.STATUS)] = s

    # act
    df = study.filter_data_frame(
        simulation_ids=ids,
    )

    # assert
    assert len(df) == len(ids)


def test_filter_data_frame_without_simulations_ids_only_adds_new_simulations(
    tmp_path: pytest.TempPathFactory,
):
    # arrange
    study = ParametricStudy(tmp_path / "test_study", "material")
    material = AdditiveMaterial(name="test_material")
    ids = []
    for i, s in enumerate(SimulationStatus):
        sb = SingleBeadInput(bead_length=(0.001 + (i * 0.0001)), material=material)
        ids.append(sb.id)
        study.add_inputs([sb])
        study._data_frame.iloc[i, study._data_frame.columns.get_loc(ColumnNames.STATUS)] = s

    # act
    df = study.filter_data_frame()

    # assert
    assert len(df) == 1
    assert df.iloc[0][ColumnNames.STATUS] == SimulationStatus.NEW


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
    machine = ParametricStudy._create_machine(series)

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
    machine = ParametricStudy._create_machine(series)

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
    bead_length = 9.5e-3
    series = pd.Series(
        {
            ColumnNames.ID: "test_id",
            ColumnNames.SINGLE_BEAD_LENGTH: bead_length,
        }
    )
    machine = AdditiveMachine(laser_power=123)
    material = AdditiveMaterial(elastic_modulus=456)

    # act
    input = ParametricStudy._create_single_bead_input(series, material=material, machine=machine)

    # assert
    assert isinstance(input, SingleBeadInput)
    assert input.id == "test_id"
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
    input = ParametricStudy._create_porosity_input(series, material=material, machine=machine)

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
    input = ParametricStudy._create_microstructure_input(series, material=material, machine=machine)

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
    assert input.use_provided_thermal_parameters is True
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
    input = ParametricStudy._create_microstructure_input(series, material=material, machine=machine)

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
    assert input.use_provided_thermal_parameters is False
    assert input.cooling_rate == MicrostructureInput.DEFAULT_COOLING_RATE
    assert input.thermal_gradient == MicrostructureInput.DEFAULT_THERMAL_GRADIENT
    assert input.melt_pool_width == MicrostructureInput.DEFAULT_MELT_POOL_WIDTH
    assert input.melt_pool_depth == MicrostructureInput.DEFAULT_MELT_POOL_DEPTH
    assert input.random_seed == MicrostructureInput.DEFAULT_RANDOM_SEED
    assert input.machine == machine
    assert input.material == material
