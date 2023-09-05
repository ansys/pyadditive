import os
import tempfile

from ansys.api.additive.v0.additive_materials_pb2 import TuneMaterialRequest, TuneMaterialResponse
import pytest

from ansys.additive.core.material_tuning import (
    MaterialTuningInput,
    MaterialTuningInputMessage,
    MaterialTuningResultMessage,
    MaterialTuningSummary,
)

from . import test_utils


def test_MaterialTuningInput_init_assigns_defaults():
    # arrange
    # we need the files to exist, but we don't care about the contents
    file_path = test_utils.get_test_file_path("slm_build_file.zip")

    # act
    input = MaterialTuningInput(
        id="id",
        experiment_data_file=file_path,
        material_parameters_file=file_path,
        thermal_properties_lookup_file=file_path,
    )

    # assert
    assert input.id == "id"
    assert input.experiment_data_file == file_path
    assert input.material_parameters_file == file_path
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
            id="id",
            experiment_data_file=exp_file,
            material_parameters_file=mat_file,
            thermal_properties_lookup_file=therm_file,
            characteristic_width_lookup_file=cw_file,
        )


def test_MaterialTuningInput_str_returns_expected_string():
    # arrange
    # we need the files to exist, but we don't care about the contents
    file_path = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        id="id",
        experiment_data_file=file_path,
        material_parameters_file=file_path,
        thermal_properties_lookup_file=file_path,
    )

    # act
    result = str(input)

    # assert
    assert result == (
        "MaterialTuningInput\n"
        "id: id\n"
        "allowable_error: 0.05\n"
        "max_iterations: 15\n"
        "experiment_data_file: {}\n"
        "material_parameters_file: {}\n"
        "thermal_properties_lookup_file: {}\n"
        "characteristic_width_lookup_file: None\n"
        "base_plate_temperature: 353.15\n".format(file_path, file_path, file_path)
    )


def test_to_request_creates_expected_TuneMaterialRequest():
    # arrange
    # we need the files to exist, but we don't care about the contents
    file_path = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        id="id",
        experiment_data_file=file_path,
        material_parameters_file=file_path,
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
    assert isinstance(request, TuneMaterialRequest)
    assert request.id == "id"
    assert request.input.allowable_error == 1
    assert request.input.max_iterations == 2
    assert request.input.base_plate_temperature == 3
    assert request.input.experiment_data == expected_file_bytes
    assert request.input.material_parameters == expected_file_bytes
    assert request.input.thermal_properties_lookup == expected_file_bytes
    assert request.input.characteristic_width_lookup == expected_file_bytes


def test_MaterialTuningInput_eq():
    # arrange
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        id="id",
        experiment_data_file=file_name,
        material_parameters_file=file_name,
        thermal_properties_lookup_file=file_name,
    )

    not_input = MaterialTuningInput(
        id="not_id",
        experiment_data_file=file_name,
        material_parameters_file=file_name,
        thermal_properties_lookup_file=file_name,
    )

    # act, assert
    assert input == MaterialTuningInput(
        id="id",
        experiment_data_file=file_name,
        material_parameters_file=file_name,
        thermal_properties_lookup_file=file_name,
    )
    assert input != MaterialTuningInputMessage()
    assert input != not_input


def test_MaterialTuningSummary_init_creates_expected_object():
    # arrange
    tmp = tempfile.TemporaryDirectory()
    msg = MaterialTuningResultMessage(
        optimized_parameters=b"optimized_parameters",
        characteristic_width_lookup=b"characteristic_width_lookup",
        log=b"log",
    )
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        id="id",
        experiment_data_file=file_name,
        material_parameters_file=file_name,
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


@pytest.mark.parametrize(
    "invalid_obj",
    [int(1), None, "string", MaterialTuningInputMessage(), TuneMaterialResponse()],
)
def test_MaterialTuningSummary_init_raises_type_error_for_invalid_input(invalid_obj):
    # arrange, act, assert
    with pytest.raises(TypeError, match="Parameter 'input' is not a 'MaterialTuningInput' object"):
        MaterialTuningSummary(invalid_obj, MaterialTuningResultMessage(), "output_dir")


@pytest.mark.parametrize(
    "invalid_obj",
    [int(1), None, "string", MaterialTuningInputMessage(), TuneMaterialResponse()],
)
def test_MaterialTuningSummary_init_raises_type_error_for_invalid_message(invalid_obj):
    # arrange
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    valid_input = MaterialTuningInput(
        id="id",
        experiment_data_file=file_name,
        material_parameters_file=file_name,
        thermal_properties_lookup_file=file_name,
    )
    # act, assert
    tmp = tempfile.TemporaryDirectory()
    with pytest.raises(
        TypeError, match="Parameter 'msg' is not a 'MaterialTuningResultMessage' object"
    ):
        MaterialTuningSummary(valid_input, invalid_obj, "output_dir")


def test_MaterialTuningSummary_str_returns_expected_string():
    # arrange
    file_name = test_utils.get_test_file_path("slm_build_file.zip")
    input = MaterialTuningInput(
        id="id",
        experiment_data_file=file_name,
        material_parameters_file=file_name,
        thermal_properties_lookup_file=file_name,
    )
    tmp = tempfile.TemporaryDirectory()
    msg = MaterialTuningResultMessage(
        optimized_parameters=b"optimized_parameters",
        characteristic_width_lookup=b"characteristic_width_lookup",
        log=b"log",
    )
    result = MaterialTuningSummary(input, msg, tmp.name)

    # act
    result_str = str(result)

    # assert
    assert result_str == (
        "MaterialTuningSummary\n"
        "input: MaterialTuningInput\n"
        "id: id\n"
        "allowable_error: 0.05\n"
        "max_iterations: 15\n"
        "experiment_data_file: {}\n"
        "material_parameters_file: {}\n"
        "thermal_properties_lookup_file: {}\n"
        "characteristic_width_lookup_file: None\n"
        "base_plate_temperature: 353.15\n\n"
        "optimized_parameters_file: {}\n"
        "characteristic_width_file: {}\n"
        "log_file: {}\n".format(
            file_name,
            file_name,
            file_name,
            os.path.join(tmp.name, "optimized_parameters.csv"),
            os.path.join(tmp.name, "characteristic_width_lookup.csv"),
            os.path.join(tmp.name, "log.txt"),
        )
    )
