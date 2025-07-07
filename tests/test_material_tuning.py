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
import tempfile

import pytest

from ansys.additive.core.material_tuning import (
    MaterialTuningInput,
    MaterialTuningInputMessage,
    MaterialTuningResultMessage,
    MaterialTuningSummary,
)
from ansys.api.additive.v0.additive_simulation_pb2 import (
    SimulationRequest,
    SimulationResponse,
)

from . import test_utils


def test_MaterialTuningInput_init_assigns_defaults():
    # arrange
    # we need the files to exist, but we don't care about the contents
    file_path = test_utils.get_test_file_path("slm_build_file.zip")

    # act
    input = MaterialTuningInput(
        experiment_data_file=file_path,
        material_configuration_file=file_path,
        thermal_properties_lookup_file=file_path,
    )

    # assert
    assert input.id
    assert input.experiment_data_file == file_path
    assert input.material_configuration_file == file_path
    assert input.thermal_properties_lookup_file == file_path
    assert input.characteristic_width_lookup_file is None
    assert input.allowable_error == 0.05
    assert input.max_iterations == 15
    assert input.base_plate_temperature == 353.15


@pytest.mark.parametrize(
    "exp_file, mat_file, therm_file, cw_file",
    [
        (
            "exp_file",
            test_utils.get_test_file_path("slm_build_file.zip"),
            test_utils.get_test_file_path("slm_build_file.zip"),
            test_utils.get_test_file_path("slm_build_file.zip"),
        ),
        (
            test_utils.get_test_file_path("slm_build_file.zip"),
            "mat_file",
            test_utils.get_test_file_path("slm_build_file.zip"),
            test_utils.get_test_file_path("slm_build_file.zip"),
        ),
        (
            test_utils.get_test_file_path("slm_build_file.zip"),
            test_utils.get_test_file_path("slm_build_file.zip"),
            "therm_file",
            test_utils.get_test_file_path("slm_build_file.zip"),
        ),
        (
            test_utils.get_test_file_path("slm_build_file.zip"),
            test_utils.get_test_file_path("slm_build_file.zip"),
            test_utils.get_test_file_path("slm_build_file.zip"),
            "cw_file",
        ),
    ],
)
def test_MaterialTuningInput_init_raises_exception_for_missing_file(
    exp_file,
    mat_file,
    therm_file,
    cw_file,
):
    # arrange, act, assert
    with pytest.raises(FileNotFoundError) as exc_info:
        MaterialTuningInput(
            experiment_data_file=exp_file,
            material_configuration_file=mat_file,
            thermal_properties_lookup_file=therm_file,
            characteristic_width_lookup_file=cw_file,
        )


def test_MaterialTuningInput_str_returns_expected_string():
    # arrange
    # we need the files to exist, but we don't care about the contents
    file_path = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        experiment_data_file=file_path,
        material_configuration_file=file_path,
        thermal_properties_lookup_file=file_path,
    )

    # act
    result = str(input)

    # assert
    assert result == (
        "MaterialTuningInput\n"
        f"id: {input.id}\n"
        "allowable_error: 0.05\n"
        "max_iterations: 15\n"
        "experiment_data_file: {}\n"
        "material_configuration_file: {}\n"
        "thermal_properties_lookup_file: {}\n"
        "characteristic_width_lookup_file: None\n"
        "base_plate_temperature: 353.15\n".format(file_path, file_path, file_path)
    )


def test_to_request_creates_expected_SimulationRequest():
    # arrange
    # we need the files to exist, but we don't care about the contents
    file_path = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        experiment_data_file=file_path,
        material_configuration_file=file_path,
        thermal_properties_lookup_file=file_path,
        characteristic_width_lookup_file=file_path,
        allowable_error=1,
        max_iterations=2,
        base_plate_temperature=3,
    )
    expected_file_bytes = open(file_path, "rb").read()

    # act
    request = input._to_request()

    # assert
    assert isinstance(request, SimulationRequest)
    assert request.id == input.id
    assert request.material_tuning_input.allowable_error == 1
    assert request.material_tuning_input.max_iterations == 2
    assert request.material_tuning_input.base_plate_temperature == 3
    assert request.material_tuning_input.experiment_data == expected_file_bytes
    assert request.material_tuning_input.material_parameters == expected_file_bytes
    assert (
        request.material_tuning_input.thermal_properties_lookup == expected_file_bytes
    )
    assert (
        request.material_tuning_input.characteristic_width_lookup == expected_file_bytes
    )


def test_MaterialTuningInput_eq():
    # arrange
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        experiment_data_file=file_name,
        material_configuration_file=file_name,
        thermal_properties_lookup_file=file_name,
    )

    not_input = MaterialTuningInput(
        experiment_data_file=file_name,
        material_configuration_file=file_name,
        thermal_properties_lookup_file=file_name,
    )

    # act, assert
    assert input == input
    assert input != MaterialTuningInputMessage()
    assert input != not_input


def test_MaterialTuningSummary_init_with_all_fields_creates_expected_object():
    # arrange
    tmp = tempfile.TemporaryDirectory()
    msg = MaterialTuningResultMessage(
        optimized_parameters=b"optimized_parameters",
        characteristic_width_lookup=b"characteristic_width_lookup",
        coefficients=b"coefficients",
        material_parameters=b"material_parameters",
        log=b"log",
    )
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        experiment_data_file=file_name,
        material_configuration_file=file_name,
        thermal_properties_lookup_file=file_name,
    )

    # act
    summary = MaterialTuningSummary(input, msg, tmp.name)

    # assert
    assert isinstance(summary, MaterialTuningSummary)
    assert summary.input == input
    assert os.path.isfile(summary.optimized_parameters_file)
    with open(summary.optimized_parameters_file, "rb") as f:
        assert f.read() == b"optimized_parameters"
    assert os.path.isfile(summary.characteristic_width_file)
    with open(summary.characteristic_width_file, "rb") as f:
        assert f.read() == b"characteristic_width_lookup"
    assert os.path.isfile(summary.log_file)
    with open(summary.log_file, "rb") as f:
        assert f.read() == b"log"
    assert os.path.isfile(summary.coefficients_file)
    with open(summary.coefficients_file, "rb") as f:
        assert f.read() == b"coefficients"
    assert os.path.isfile(summary.material_configuration_file)
    with open(summary.material_configuration_file, "rb") as f:
        assert f.read() == b"material_parameters"


def test_MaterialTuningSummary_init_with_minimum_fields_creates_expected_object():
    # arrange
    tmp = tempfile.TemporaryDirectory()
    msg = MaterialTuningResultMessage(
        optimized_parameters=b"optimized_parameters",
        characteristic_width_lookup=b"",
        coefficients=b"",
        material_parameters=b"",
        log=b"",
    )
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        experiment_data_file=file_name,
        material_configuration_file=file_name,
        thermal_properties_lookup_file=file_name,
    )

    # act
    summary = MaterialTuningSummary(input, msg, tmp.name)

    # assert
    assert isinstance(summary, MaterialTuningSummary)
    assert summary.input == input
    assert os.path.isfile(summary.optimized_parameters_file)
    with open(summary.optimized_parameters_file, "rb") as f:
        assert f.read() == b"optimized_parameters"
    assert summary.characteristic_width_file is None
    assert summary.log_file is None
    assert summary.coefficients_file is None
    assert summary.material_configuration_file is None


@pytest.mark.parametrize(
    "invalid_obj",
    [int(1), None, "string", MaterialTuningInputMessage(), SimulationResponse()],
)
def test_MaterialTuningSummary_init_raises_type_error_for_invalid_input(invalid_obj):
    # arrange, act, assert
    with pytest.raises(
        TypeError, match="Parameter 'input' is not a 'MaterialTuningInput' object"
    ):
        MaterialTuningSummary(invalid_obj, MaterialTuningResultMessage(), "output_dir")


@pytest.mark.parametrize(
    "invalid_obj",
    [int(1), None, "string", MaterialTuningInputMessage(), SimulationResponse()],
)
def test_MaterialTuningSummary_init_raises_type_error_for_invalid_message(invalid_obj):
    # arrange
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    valid_input = MaterialTuningInput(
        experiment_data_file=file_name,
        material_configuration_file=file_name,
        thermal_properties_lookup_file=file_name,
    )

    # act, assert
    with pytest.raises(
        TypeError, match="Parameter 'msg' is not a 'MaterialTuningResultMessage' object"
    ):
        MaterialTuningSummary(valid_input, invalid_obj, "output_dir")


def test_MaterialTuningSummary_str_returns_expected_string():
    # arrange
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        experiment_data_file=file_name,
        material_configuration_file=file_name,
        thermal_properties_lookup_file=file_name,
    )
    tmp = tempfile.TemporaryDirectory()
    msg = MaterialTuningResultMessage(
        optimized_parameters=b"optimized_parameters",
        characteristic_width_lookup=b"characteristic_width_lookup",
        coefficients=b"coefficients",
        material_parameters=b"material_parameters",
        log=b"log",
    )
    result = MaterialTuningSummary(input, msg, tmp.name)

    # act
    result_str = str(result)

    # assert
    assert result_str == (
        "MaterialTuningSummary\n"
        "input: MaterialTuningInput\n"
        f"id: {input.id}\n"
        "allowable_error: 0.05\n"
        "max_iterations: 15\n"
        "experiment_data_file: {}\n"
        "material_configuration_file: {}\n"
        "thermal_properties_lookup_file: {}\n"
        "characteristic_width_lookup_file: None\n"
        "base_plate_temperature: 353.15\n\n"
        "optimized_parameters_file: {}\n"
        "coefficients_file: {}\n"
        "material_configuration_file: {}\n"
        "characteristic_width_file: {}\n"
        "log_file: {}\n".format(
            file_name,
            file_name,
            file_name,
            os.path.join(tmp.name, "optimized_parameters.csv"),
            os.path.join(tmp.name, "coefficients.csv"),
            os.path.join(tmp.name, "material_configuration.json"),
            os.path.join(tmp.name, "characteristic_width_lookup.csv"),
            os.path.join(tmp.name, "log.txt"),
        )
    )
