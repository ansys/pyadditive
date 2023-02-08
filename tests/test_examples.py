# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import os
import shutil

from ansys.additive import EXAMPLES_PATH
import ansys.additive.examples as examples


def _clean_examples_path():
    shutil.rmtree(EXAMPLES_PATH)
    os.makedirs(EXAMPLES_PATH)


def test_download_10mm_cube_retrieves_file():
    # arrange
    _clean_examples_path()

    # act
    filename = examples.download_10mm_cube()

    # assert
    assert os.path.isfile(filename)
    assert os.path.basename(filename) == "10mm_cube.stl"


def test_download_small_wedge_slm_build_file_retrieves_file():
    # arrange
    _clean_examples_path()

    # act
    filename = examples.download_small_wedge_slm_build_file()
    examples.decompress(filename)

    # assert
    assert os.path.isfile(filename)
    assert os.path.basename(filename) == "small-wedge-slm.zip"
    assert os.path.isfile(os.path.join(EXAMPLES_PATH, "small-wedge.slm"))
    assert os.path.isfile(os.path.join(EXAMPLES_PATH, "small-wedge.stl"))


def test_delete_downloads_removes_all_files():
    # arrange
    examples.download_10mm_cube()
    examples.download_small_wedge_slm_build_file()

    # act
    examples.delete_downloads()

    # assert
    assert len(os.listdir(EXAMPLES_PATH)) == 0


def test_download_material_tuning_input_retrieves_files():
    # arrange
    _clean_examples_path()

    # act
    inputs = examples.download_material_tuning_input()

    # assert
    assert os.path.isfile(inputs.experiment_data_file)
    assert os.path.isfile(inputs.material_parameters_file)
    assert os.path.isfile(inputs.thermal_properties_lookup_file)
    assert os.path.isfile(inputs.characteristic_width_lookup_file)


def test_get_ext_returns_expected_extension():
    # arrange
    filename = "test.stl"

    # act
    ext = examples.get_ext(filename)

    # assert
    assert ext == ".stl"
