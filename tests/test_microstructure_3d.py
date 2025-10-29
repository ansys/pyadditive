# Copyright (C) 2022 - 2025 ANSYS, Inc. and/or its affiliates.
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
import shutil
import tempfile

import pytest

from ansys.additive.core.machine import AdditiveMachine
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.microstructure_3d import (
    Microstructure3DInput,
    Microstructure3DSummary,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    GrainStatistics,
    Microstructure3DResult,
    MicrostructureResult,
)
from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest

from ansys.additive.core.simulation import SimulationStatus

from . import test_utils

def test_Microstructure3DSummary_init_returns_expected_value():
    # arrange
    user_data_path = os.path.join(
        tempfile.gettempdir(), "microstructure_3d_summary_init"
    )
    os.makedirs(user_data_path, exist_ok=True)
    input = Microstructure3DInput()
    xy_vtk_bytes = bytes(range(3))
    xz_vtk_bytes = bytes(range(4, 6))
    yz_vtk_bytes = bytes(range(7, 9))
    grain_3d_bytes = bytes(range(10, 12))
    xy_stats = GrainStatistics(
        grain_number=1, area_fraction=2, diameter_um=3, orientation_angle=4
    )
    xz_stats = GrainStatistics(
        grain_number=5, area_fraction=6, diameter_um=7, orientation_angle=8
    )
    yz_stats = GrainStatistics(
        grain_number=9, area_fraction=10, diameter_um=11, orientation_angle=12
    )
    result = MicrostructureResult(
        xy_vtk=xy_vtk_bytes, xz_vtk=xz_vtk_bytes, yz_vtk=yz_vtk_bytes
    )
    result.xy_circle_equivalence.append(xy_stats)
    result.xz_circle_equivalence.append(xz_stats)
    result.yz_circle_equivalence.append(yz_stats)
    result_3d = Microstructure3DResult(three_d_vtk=grain_3d_bytes, two_d_result=result)

    # act
    summary = Microstructure3DSummary(input, result_3d, "logs", user_data_path)

    # assert
    assert isinstance(summary, Microstructure3DSummary)
    assert input == summary.input
    assert summary.grain_3d_vtk == os.path.join(
        user_data_path, input.id, summary._3D_GRAIN_VTK_NAME
    )
    assert summary.xy_average_grain_size == 6
    assert summary.xz_average_grain_size == 42
    assert summary.yz_average_grain_size == 110
    assert summary.logs == "logs"
    assert summary.status == SimulationStatus.COMPLETED
    # TODO: uncomment when the following properties are implemented
    # assert summary.xy_vtk == os.path.join(user_data_path, "id", "xy.vtk")
    # assert os.path.exists(summary.xy_vtk)
    # assert summary.xz_vtk == os.path.join(user_data_path, "id", "xz.vtk")
    # assert os.path.exists(summary.xz_vtk)
    # assert summary.yz_vtk == os.path.join(user_data_path, "id", "yz.vtk")
    # assert os.path.exists(summary.yz_vtk)
    # assert summary.xy_circle_equivalence["grain_number"][0] == 1
    # assert summary.xy_circle_equivalence["area_fraction"][0] == 2
    # assert summary.xy_circle_equivalence["diameter_um"][0] == 3
    # assert summary.xy_circle_equivalence["orientation_angle"][0] == math.degrees(4)
    # assert summary.xz_circle_equivalence["grain_number"][0] == 5
    # assert summary.xz_circle_equivalence["area_fraction"][0] == 6
    # assert summary.xz_circle_equivalence["diameter_um"][0] == 7
    # assert summary.xz_circle_equivalence["orientation_angle"][0] == math.degrees(8)
    # assert summary.yz_circle_equivalence["grain_number"][0] == 9
    # assert summary.yz_circle_equivalence["area_fraction"][0] == 10
    # assert summary.yz_circle_equivalence["diameter_um"][0] == 11
    # assert summary.yz_circle_equivalence["orientation_angle"][0] == math.degrees(12)

    # clean up
    shutil.rmtree(user_data_path)


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        Microstructure3DResult(),
    ],
)
def test_Microstructure3DSummary_init_raises_exception_for_invalid_input_type(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid input type"):
        Microstructure3DSummary(invalid_obj, Microstructure3DResult(), "logs", ".")


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        Microstructure3DInput(),
    ],
)
def test_Microstructure3DSummary_init_raises_exception_for_invalid_result_type(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid result type"):
        Microstructure3DSummary(Microstructure3DInput(), invalid_obj, "logs", ".")


@pytest.mark.parametrize(
    "invalid_path",
    [
        "",
        None,
    ],
)
def test_Microstructure3DSummary_init_raises_exception_for_invalid_path(
    invalid_path,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid user data path"):
        Microstructure3DSummary(
            Microstructure3DInput(), Microstructure3DResult(), "logs", invalid_path
        )


def test_Microstructure3DSummary_init_raises_exception_for_invalid_logs_type():
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid logs type"):
        Microstructure3DSummary(
            Microstructure3DInput(), Microstructure3DResult(), b"logs", "."
        )


def test_Microstructure3DSummary_repr_returns_expected_string():
    # arrange
    user_data_path = os.path.join(
        tempfile.gettempdir(), "microstructure_3d_summary_init"
    )
    os.makedirs(user_data_path, exist_ok=True)
    input = Microstructure3DInput()
    xy_vtk_bytes = bytes(range(3))
    xz_vtk_bytes = bytes(range(4, 6))
    yz_vtk_bytes = bytes(range(7, 9))
    grain_3d_bytes = bytes(range(10, 12))
    xy_stats = GrainStatistics(
        grain_number=1, area_fraction=2, diameter_um=3, orientation_angle=4
    )
    xz_stats = GrainStatistics(
        grain_number=5, area_fraction=6, diameter_um=7, orientation_angle=8
    )
    yz_stats = GrainStatistics(
        grain_number=9, area_fraction=10, diameter_um=11, orientation_angle=12
    )
    result = MicrostructureResult(
        xy_vtk=xy_vtk_bytes, xz_vtk=xz_vtk_bytes, yz_vtk=yz_vtk_bytes
    )
    result.xy_circle_equivalence.append(xy_stats)
    result.xz_circle_equivalence.append(xz_stats)
    result.yz_circle_equivalence.append(yz_stats)
    result_3d = Microstructure3DResult(three_d_vtk=grain_3d_bytes, two_d_result=result)
    summary = Microstructure3DSummary(
        input=input, result=result_3d, logs="logs", user_data_path=user_data_path
    )
    expected_output_dir = os.path.join(user_data_path, input.id)

    # act, assert
    assert repr(summary) == (
        "Microstructure3DSummary\n"
        + "logs: logs\n"
        + "status: SimulationStatus.COMPLETED\n"
        + "input: Microstructure3DInput\n"
        + f"id: {input.id}\n"
        + "sample_min_x: 0\n"
        + "sample_min_y: 0\n"
        + "sample_min_z: 0\n"
        + "sample_size_x: 0.0001\n"
        + "sample_size_y: 0.0001\n"
        + "sample_size_z: 0.0001\n"
        + "calculate_initial_microstructure: True\n"
        + "use_transient_bulk_nucleation: True\n"
        + "max_bulk_nucleation_density: 20000000000000\n"
        + "num_initial_random_nuclei: 8000\n"
        + "\n"
        + test_utils.get_default_machine_repr()
        + "\n"
        + test_utils.get_default_material_repr()
        + "\n"
        + "grain_3d_vtk: "
        + os.path.join(expected_output_dir, "3d_grain_structure.vtk")
        + "\n"
        + "xy_average_grain_size: 6.0\n"
        + "xz_average_grain_size: 42.0\n"
        + "yz_average_grain_size: 110.0\n"
        # TODO: uncomment when the following properties are implemented
        # + "xy_vtk: "
        # + os.path.join(expected_output_dir, "xy.vtk")
        # + "\n"
        # + "xz_vtk: "
        # + os.path.join(expected_output_dir, "xz.vtk")
        # + "\n"
        # + "yz_vtk: "
        # + os.path.join(expected_output_dir, "yz.vtk")
        # + "\n"
        # + "xy_circle_equivalence:    grain_number  area_fraction  diameter_um  orientation_angle\n"
        # + "0             1            2.0          3.0         229.183118\n"
        # + "xz_circle_equivalence:    grain_number  area_fraction  diameter_um  orientation_angle\n"
        # + "0             5            6.0          7.0         458.366236\n"
        # + "yz_circle_equivalence:    grain_number  area_fraction  diameter_um  orientation_angle\n"
        # + "0             9           10.0         11.0         687.549354\n"
    )

    # cleanup
    shutil.rmtree(user_data_path)


def test_Microstructure3DInput_init_creates_default_object():
    # arrange, act
    input = Microstructure3DInput()

    # assert
    assert input.id != ""
    assert input.machine.laser_power == 195
    assert input.material.name == ""
    assert input.sample_min_x == 0
    assert input.sample_min_y == 0
    assert input.sample_min_z == 0
    assert input.sample_size_x == 0.1e-3
    assert input.sample_size_y == 0.1e-3
    assert input.sample_size_z == 0.1e-3
    assert input.calculate_initial_microstructure is True
    assert input.use_transient_bulk_nucleation is True
    assert input.max_bulk_nucleation_density == 20e12
    assert input.num_initial_random_nuclei == 8000


def test_Microstructure3DInput_init_with_parameters_creates_expected_object():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")

    # act
    input = Microstructure3DInput(
        machine=machine,
        material=material,
        sample_min_x=1,
        sample_min_y=2,
        sample_min_z=3,
        sample_size_x=0.0001,
        sample_size_y=0.0002,
        sample_size_z=0.0003,
        use_transient_bulk_nucleation=True,
        max_bulk_nucleation_density=8e6,
        num_initial_random_nuclei=101,
    )

    # assert
    assert len(input.id) > 0
    assert input.machine.laser_power == 99
    assert input.material.name == "vibranium"
    assert input.sample_min_x == 1
    assert input.sample_min_y == 2
    assert input.sample_min_z == 3
    assert input.sample_size_x == 0.0001
    assert input.sample_size_y == 0.0002
    assert input.sample_size_z == 0.0003
    assert input.use_transient_bulk_nucleation is True
    assert input.max_bulk_nucleation_density == 8e6
    assert input.num_initial_random_nuclei == 101


def test_Microstructure3DInput_to_simulation_request_returns_expected_object():
    # arrange
    input = Microstructure3DInput()

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == input.id
    ms_input = request.microstructure_3d_input
    assert ms_input.x_origin == 0
    assert ms_input.y_origin == 0
    assert ms_input.z_origin == 0
    assert ms_input.x_length == 0.1e-3
    assert ms_input.y_length == 0.1e-3
    assert ms_input.z_length == 0.1e-3
    assert ms_input.first_deposit_layer == 0
    assert ms_input.run_initial_microstructure is True
    assert ms_input.num_random_nuclei == 8000
    assert ms_input.use_transient_bulk_nucleation is True
    assert ms_input.max_bulk_nucleation_density == 20e12


def test_Microstructure3DInput_to_simulation_request_assigns_values():
    # arrange
    machine = AdditiveMachine()
    machine.laser_power = 99
    material = AdditiveMaterial(name="vibranium")
    input = Microstructure3DInput(
        machine=machine,
        material=material,
        sample_min_x=1,
        sample_min_y=2,
        sample_min_z=3,
        sample_size_x=0.0001,
        sample_size_y=0.0002,
        sample_size_z=0.0003,
        calculate_initial_microstructure=False,
        num_initial_random_nuclei=99,
        use_transient_bulk_nucleation=False,
        max_bulk_nucleation_density=999,
    )

    # act
    request = input._to_simulation_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == input.id
    ms_input = request.microstructure_3d_input
    assert ms_input.machine.laser_power == 99
    assert ms_input.material.name == "vibranium"
    assert ms_input.x_origin == 1
    assert ms_input.y_origin == 2
    assert ms_input.z_origin == 3
    assert ms_input.x_length == 0.1e-3
    assert ms_input.y_length == 0.2e-3
    assert ms_input.z_length == 0.3e-3
    assert ms_input.first_deposit_layer == 0
    assert ms_input.run_initial_microstructure is False
    assert ms_input.num_random_nuclei == 99
    assert ms_input.use_transient_bulk_nucleation is False
    assert ms_input.max_bulk_nucleation_density == 999


def test_Microstructure3DInput_setters_raise_ValueError_for_values_out_of_range():
    # arrange
    input = Microstructure3DInput()

    # act & assert
    with pytest.raises(ValueError):
        input.sample_min_x = -1
    with pytest.raises(ValueError):
        input.sample_min_x = 11
    with pytest.raises(ValueError):
        input.sample_min_y = -1
    with pytest.raises(ValueError):
        input.sample_min_y = 11
    with pytest.raises(ValueError):
        input.sample_min_z = -1
    with pytest.raises(ValueError):
        input.sample_min_z = 11
    with pytest.raises(ValueError):
        input.sample_size_x = 14e-6
    with pytest.raises(ValueError):
        input.sample_size_x = 6e-4
    with pytest.raises(ValueError):
        input.sample_size_y = 14e-6
    with pytest.raises(ValueError):
        input.sample_size_y = 6e-4
    with pytest.raises(ValueError):
        input.sample_size_z = 14e-6
    with pytest.raises(ValueError):
        input.sample_size_z = 6e-4
    with pytest.raises(ValueError):
        input.max_bulk_nucleation_density = -1
    with pytest.raises(ValueError):
        input.num_initial_random_nuclei = -1


@pytest.mark.parametrize(
    "field",
    [
        "sample_min_x",
        "sample_min_y",
        "sample_min_z",
        "sample_size_x",
        "sample_size_y",
        "sample_size_z",
        "max_bulk_nucleation_density",
        "num_initial_random_nuclei",
    ],
)
def test_Microstructure3DInput_setters_raise_ValueError_for_nan_values(field):
    # arrange
    input = Microstructure3DInput()

    # act & assert
    with pytest.raises(ValueError, match=field + " must be a number"):
        setattr(input, field, float("nan"))


def test_Microstructure3DInput_repr_returns_expected_string():
    # arrange
    input = Microstructure3DInput()

    # act, assert
    assert repr(input) == (
        "Microstructure3DInput\n"
        + f"id: {input.id}\n"
        + "sample_min_x: 0\n"
        + "sample_min_y: 0\n"
        + "sample_min_z: 0\n"
        + "sample_size_x: 0.0001\n"
        + "sample_size_y: 0.0001\n"
        + "sample_size_z: 0.0001\n"
        + "calculate_initial_microstructure: True\n"
        + "use_transient_bulk_nucleation: True\n"
        + "max_bulk_nucleation_density: 20000000000000\n"
        + "num_initial_random_nuclei: 8000\n"
        + "\n"
        + test_utils.get_default_machine_repr()
        + "\n"
        + test_utils.get_default_material_repr()
    )
