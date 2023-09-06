# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
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

from ansys.additive.core import EXAMPLES_PATH
import ansys.additive.core.examples as examples


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


def test_download_custom_material_retrieves_files():
    # arrange
    _clean_examples_path()

    # act
    material = examples.download_custom_material()

    # assert
    assert os.path.isfile(material.material_parameters_file)
    assert os.path.isfile(material.thermal_properties_lookup_file)
    assert os.path.isfile(material.characteristic_width_lookup_file)


def test_get_ext_returns_expected_extension():
    # arrange
    filename = "test.stl"

    # act
    ext = examples.get_ext(filename)

    # assert
    assert ext == ".stl"
