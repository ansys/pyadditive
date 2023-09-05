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
"""Provides functions for downloading sample datasets from the PyAdditive
repository."""
from http.client import HTTPMessage
import os
import shutil
import urllib.request
import zipfile

from ansys.additive.core import EXAMPLES_PATH

EXAMPLES_URI = "https://github.com/ansys/example-data/raw/master"
PARTS_FOLDER = "pyadditive/part-only"
BUILD_FILES_FOLDER = "pyadditive/buildfiles"
MATERIAL_TUNING_FOLDER = "pyadditive/material_tuning_input"
CUSTOM_MATERIAL_FOLDER = "pyadditive/custom_material_data"


def get_ext(filename):
    """Extract the extension of the filename."""
    ext = os.path.splitext(filename)[1].lower()
    return ext


def delete_downloads():
    """Delete all downloaded examples to free space or update the files."""
    shutil.rmtree(EXAMPLES_PATH)
    os.makedirs(EXAMPLES_PATH)
    return True


def decompress(filename, subdir=None) -> str:
    """Decompress a ZIP file to the ``examples`` directory.

    Parameters
    ----------
    filename : str
        Name of the file.
    subdir : str, None
        Name of the subdirectory of the ``examples`` directory
        to extract the ZIP file contents to. The default is ``None``.

    Returns
    -------
    str
       Path to the decompressed contents of the ZIP file.
    """
    outdir = EXAMPLES_PATH
    zip_ref = zipfile.ZipFile(filename, "r")
    if subdir:
        outdir = os.path.join(outdir, subdir)
        os.makedirs(outdir, exist_ok=True)
    zip_ref.extractall(outdir)
    zip_ref.close()
    return outdir


def _get_file_url(filename, directory=None):
    if directory:
        return f"{EXAMPLES_URI}/{directory}/{filename}"
    return f"{EXAMPLES_URI}/{filename}"


def _retrieve_file(url, filename) -> tuple[str, HTTPMessage]:
    """Retrieve an example data file from either a URL or local storage.

    Parameters
    ----------
    url : str
       URL for the example data file.
    filename : str
       Name for the example data file.

    Returns
    -------
    str: Local path file was downloaded to.
    HttpMessage: HTTP status message, if any.
    """
    # First check if file has already been downloaded
    local_path = os.path.join(EXAMPLES_PATH, os.path.basename(filename))
    if os.path.isfile(local_path) or os.path.isdir(local_path):
        return local_path, None

    # grab the correct url retriever
    urlretrieve = urllib.request.urlretrieve

    # Perform download
    saved_file, resp = urlretrieve(url)
    shutil.move(saved_file, local_path)
    return local_path, resp


def _download_file(filename, directory=None) -> tuple[str, HTTPMessage]:
    url = _get_file_url(filename, directory)
    return _retrieve_file(url, filename)


def download_10mm_cube():
    """Download an STL file describing a 10-millimeter cube."""
    return _download_file("10mm_cube.stl", PARTS_FOLDER)[0]


def download_small_wedge_slm_build_file():
    """Download an SLM build file for a small wedge part."""
    return _download_file("small-wedge-slm.zip", BUILD_FILES_FOLDER)[0]


class MaterialTuningExampleInputFiles:
    """Holds the example inputs for the material tuning process."""

    def __init__(
        self,
        experiment_data_file: str,
        material_parameters_file: str,
        thermal_properties_lookup_file: str,
        characteristic_width_lookup_file: str,
    ):
        """Initialize the ``MaterialTuningInputs`` class.

        Parameters
        ----------
        experiment_data_file : str
            Path to the experiment data file.
        material_parameters_file : str
            Path to the material parameters file.
        thermal_properties_lookup_file : str
            Path to the thermal properties lookup file.
        characteristic_width_lookup_file : str
            Path to the characteristic width lookup file.
        """
        self._experiment_data_file = experiment_data_file
        self._material_parameters_file = material_parameters_file
        self._thermal_properties_lookup_file = thermal_properties_lookup_file
        self._characteristic_width_lookup_file = characteristic_width_lookup_file

    @property
    def experiment_data_file(self):
        return self._experiment_data_file

    @property
    def material_parameters_file(self):
        return self._material_parameters_file

    @property
    def thermal_properties_lookup_file(self):
        return self._thermal_properties_lookup_file

    @property
    def characteristic_width_lookup_file(self):
        return self._characteristic_width_lookup_file


def download_material_tuning_input() -> MaterialTuningExampleInputFiles:
    """Download the input files for the material tuning example."""
    zip_file = _download_file("material_tuning_input.zip", MATERIAL_TUNING_FOLDER)[0]
    extract_dir = decompress(zip_file, "material_tuning_input")
    experiment_data_file = os.path.join(extract_dir, "experiment_data.csv")
    if not os.path.isfile(experiment_data_file):
        raise FileNotFoundError("Failed to download experiment data file")
    material_parameters_file = os.path.join(extract_dir, "material_parameters.json")
    if not os.path.isfile(material_parameters_file):
        raise FileNotFoundError("Failed to download material parameters file")
    thermal_lookup_file = os.path.join(extract_dir, "thermal_lookup.csv")
    if not os.path.isfile(thermal_lookup_file):
        raise FileNotFoundError("Failed to download thermal lookup file")
    characteristic_width_lookup_file = os.path.join(extract_dir, "characteristic_width_lookup.csv")
    if not os.path.isfile(characteristic_width_lookup_file):
        raise FileNotFoundError("Failed to download characteristic width lookup file")
    return MaterialTuningExampleInputFiles(
        experiment_data_file,
        material_parameters_file,
        thermal_lookup_file,
        characteristic_width_lookup_file,
    )


class CustomMaterialExampleFiles:
    """Holds the files associated with a custom material definition."""

    def __init__(
        self,
        material_parameters_file: str,
        thermal_properties_lookup_file: str,
        characteristic_width_lookup_file: str,
    ):
        """Initialize the ``CustomMaterialExampleFiles`` class.

        Parameters
        ----------
        material_parameters_file : str
            Path to the material parameters file.
        thermal_properties_lookup_file : str
            Path to the thermal properties lookup file.
        characteristic_width_lookup_file : str
            Path to the characteristic width lookup file.
        """
        self._material_parameters_file = material_parameters_file
        self._thermal_properties_lookup_file = thermal_properties_lookup_file
        self._characteristic_width_lookup_file = characteristic_width_lookup_file

    @property
    def material_parameters_file(self):
        """Path to the material parameters file."""
        return self._material_parameters_file

    @property
    def thermal_properties_lookup_file(self):
        """Path to the thermal properties lookup file."""
        return self._thermal_properties_lookup_file

    @property
    def characteristic_width_lookup_file(self):
        """Path to the characteristic width lookup file."""
        return self._characteristic_width_lookup_file


def download_custom_material() -> CustomMaterialExampleFiles:
    """Download the files describing a custom material."""
    zip_file = _download_file("custom_material_data.zip", CUSTOM_MATERIAL_FOLDER)[0]
    extract_dir = decompress(zip_file, "custom_material_data")
    material_parameters_file = os.path.join(extract_dir, "material_parameters.json")
    if not os.path.isfile(material_parameters_file):
        raise FileNotFoundError("Failed to download material parameters file")
    thermal_lookup_file = os.path.join(extract_dir, "thermal_lookup.csv")
    if not os.path.isfile(thermal_lookup_file):
        raise FileNotFoundError("Failed to download thermal lookup file")
    characteristic_width_lookup_file = os.path.join(extract_dir, "characteristic_width_lookup.csv")
    if not os.path.isfile(characteristic_width_lookup_file):
        raise FileNotFoundError("Failed to download characteristic width lookup file")
    return CustomMaterialExampleFiles(
        material_parameters_file,
        thermal_lookup_file,
        characteristic_width_lookup_file,
    )
