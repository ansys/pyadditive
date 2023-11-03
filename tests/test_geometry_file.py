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
import pathlib

from ansys.api.additive.v0.additive_domain_pb2 import BuildFile as BuildFileMessage
from ansys.api.additive.v0.additive_domain_pb2 import BuildFileMachineType
from ansys.api.additive.v0.additive_domain_pb2 import StlFile as StlFileMessage
import pytest

from ansys.additive.core.geometry_file import BuildFile, MachineType, StlFile

from . import test_utils


def test_BuildFile_init_returns_expected_object():
    # arrange
    file_path = os.path.abspath(__file__)

    # act
    build_file = BuildFile(type=MachineType.SLM, path=file_path)

    # assert
    assert isinstance(build_file, BuildFile)
    assert build_file.type == MachineType.SLM
    assert build_file.path == file_path


def test_BuildFile_init_with_invalid_machine_type_raises_exception():
    # arrange
    file_path = os.path.abspath(__file__)

    # act, assert
    with pytest.raises(ValueError, match="Invalid machine type"):
        BuildFile(type=999999, path=file_path)


def test_BuildFile_init_with_invalid_file_raises_exception(tmp_path: pathlib.Path):
    # arrange
    file_path = tmp_path / "bogus"

    # act, assert
    with pytest.raises(FileNotFoundError, match="File does not exist"):
        BuildFile(type=MachineType.TRUMPF, path=file_path)


def test_BuildFile_eq():
    # arrange
    bf = BuildFile(type=MachineType.EOS, path=os.path.abspath(__file__))
    not_bf = BuildFile(
        type=MachineType.EOS, path=test_utils.get_test_file_path("slm_build_file.zip")
    )

    # act, assert
    assert bf == BuildFile(type=bf.type, path=bf.path)
    assert bf != BuildFileMessage(
        type=BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_EOS, name=bf.path
    )
    assert bf != not_bf


def test_BuildFile_repr():
    # arrange
    file_path = os.path.abspath(__file__)
    bf = BuildFile(type=MachineType.EOS, path=file_path)

    # act, assert
    assert bf.__repr__() == f"BuildFile\ntype: EOS\npath: {file_path}\n"


def test_BuildFile_type_setter_raises_exception_for_invalid_type():
    # arrange
    bf = BuildFile(type=MachineType.HB3D, path=os.path.abspath(__file__))

    # act, assert
    with pytest.raises(ValueError, match="Attempted to assign type with invalid value"):
        bf.type = 99999


def test_BuildFile_type_setter_correctly_sets_value():
    # arrange
    bf = BuildFile(type=MachineType.HB3D, path=os.path.abspath(__file__))

    # act
    bf.type = MachineType.ADDITIVE_INDUSTRIES

    # assert
    assert bf._type == bf.type == MachineType.ADDITIVE_INDUSTRIES


def test_BuildFile_path_setter_raises_exception_for_invalid_type(tmp_path: pathlib.Path):
    # arrange
    bf = BuildFile(type=MachineType.HB3D, path=os.path.abspath(__file__))

    # act, assert
    with pytest.raises(FileNotFoundError, match="File does not exist"):
        bf.path = tmp_path / "bogus"


def test_BuildFile_path_setter_correctly_assigns_value(tmp_path: pathlib.Path):
    # arrange
    bf = BuildFile(type=MachineType.HB3D, path=os.path.abspath(__file__))
    new_path = tmp_path / "build-file.zip"
    new_path.touch()

    # act
    bf.path = new_path

    # assert
    assert bf._path == bf.path == new_path


def test_StlFile_init_with_args_returns_expected_object():
    # arrange, act
    file_path = os.path.abspath(__file__)
    stl_file = StlFile(path=file_path)

    # assert
    assert isinstance(stl_file, StlFile)
    assert stl_file.path == file_path


def test_StlFile_init_with_invalid_file_raises_exception(tmp_path: pathlib.Path):
    # arrange
    file_path = tmp_path / "bogus"

    # act, assert
    with pytest.raises(FileNotFoundError, match="File does not exist"):
        StlFile(path=file_path)


def test_StlFile_eq():
    # arrange
    stl = StlFile(path=os.path.abspath(__file__))
    not_stl = StlFile(path=test_utils.get_test_file_path("slm_build_file.zip"))

    # act, assert
    assert stl == StlFile(path=stl.path)
    assert stl != StlFileMessage(name=stl.path)
    assert stl != not_stl


def test_StlFile_repr():
    # arrange
    file_path = os.path.abspath(__file__)
    bf = StlFile(path=file_path)

    # act, assert
    assert bf.__repr__() == "StlFile\npath: {}\n".format(file_path)


def test_StlFile_path_setter_raises_exception_for_missing_path(tmp_path: pathlib.Path):
    # arrange
    sf = StlFile(os.path.abspath(__file__))

    # act, assert
    with pytest.raises(FileNotFoundError, match="File does not exist"):
        sf.path = tmp_path / "bogus"


def test_StlFile_path_setter_correctly_assigns_value(tmp_path: pathlib.Path):
    # arrange
    sf = StlFile(os.path.abspath(__file__))
    new_path = tmp_path / "new-file.stl"
    new_path.touch()

    # act
    sf.path = new_path

    # assert
    assert sf._path == sf.path == new_path
