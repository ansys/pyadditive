"""Functions to download sample datasets from the pyansys data repository.
"""
from http.client import HTTPMessage
import os
import shutil
import urllib.request
import zipfile

import ansys.additive as pyadditive

EXAMPLES_URI = "https://github.com/pyansys/example-data/raw/master"
PARTS_FOLDER = "pyadditive/part-only"
BUILD_FILES_FOLDER = "pyadditive/buildfiles"


def get_ext(filename):
    """Extract the extension of the filename"""
    ext = os.path.splitext(filename)[1].lower()
    return ext


def delete_downloads():
    """Delete all downloaded examples to free space or update the files"""
    shutil.rmtree(pyadditive.EXAMPLES_PATH)
    os.makedirs(pyadditive.EXAMPLES_PATH)
    return True


def decompress(filename):
    zip_ref = zipfile.ZipFile(filename, "r")
    zip_ref.extractall(pyadditive.EXAMPLES_PATH)
    return zip_ref.close()


def _get_file_url(filename, directory=None):
    if directory:
        return f"{EXAMPLES_URI}/{directory}/{filename}"
    return f"{EXAMPLES_URI}/{filename}"


def _retrieve_file(url, filename) -> tuple[str, HTTPMessage]:
    """
    Retrieve an example data file either from local storage or
    from the given url.

    Returns
    -------
    str: local file path
    HttpMessage: http status message if any

    """
    # First check if file has already been downloaded
    local_path = os.path.join(pyadditive.EXAMPLES_PATH, os.path.basename(filename))
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
    """Download an STL file describing a 10 millimeter cube."""
    return _download_file("10mm_cube.stl", PARTS_FOLDER)[0]


def download_small_wedge_slm_build_file():
    """Download an SLM build file for a small wedge part."""
    return _download_file("small-wedge-slm.zip", BUILD_FILES_FOLDER)[0]
