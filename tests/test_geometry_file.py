# (c) 2022 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from ansys.api.additive.v0.additive_domain_pb2 import BuildFile as BuildFileMessage
from ansys.api.additive.v0.additive_domain_pb2 import StlFile as StlFileMessage
import pytest

from ansys.additive.geometry_file import BuildFile, MachineType, StlFile


def test_BuildFile_init_returns_default():
    # arrange, act
    build_file = BuildFile()

    # assert
    assert isinstance(build_file, BuildFile)
    assert build_file.type == MachineType.NONE
    assert build_file.path == ""


def test_BuildFile_init_with_args_returns_expected_object():
    # arrange, act
    build_file = BuildFile(type=MachineType.SLM, path="mybuild.zip")

    # assert
    assert isinstance(build_file, BuildFile)
    assert build_file.type == MachineType.SLM
    assert build_file.path == "mybuild.zip"


def test_BuildFile_init_raises_exception_for_unkown_arg():
    # arrange, act, assert
    with pytest.raises(AttributeError) as exc_info:
        BuildFile(bogus="bummer")


def test_BuildFile_eq():
    # arrange
    bf = BuildFile(type=MachineType.EOS, path="part.zip")
    not_bf = BuildFile(type=MachineType.EOS, path="not.zip")

    # act, assert
    assert bf == BuildFile(type=bf.type, path=bf.path)
    assert bf != BuildFileMessage(type=bf.type, name=bf.path)
    assert bf != not_bf


def test_BuildFile_repr():
    # arrange
    bf = BuildFile(type=MachineType.EOS, path="part.zip")

    # act, assert
    assert bf.__repr__() == "BuildFile\ntype: MachineType.EOS\npath: part.zip\n"


def test_StlFile_init_returns_default():
    # arrange, act
    stl_file = StlFile()

    # assert
    assert isinstance(stl_file, StlFile)
    assert stl_file.path == None


def test_StlFile_init_with_args_returns_expected_object():
    # arrange, act
    stl_file = StlFile(path="mypart.stl")

    # assert
    assert isinstance(stl_file, StlFile)
    assert stl_file.path == "mypart.stl"


def test_StlFile_init_raises_exception_for_unkown_arg():
    # arrange, act, assert
    with pytest.raises(AttributeError) as exc_info:
        StlFile(bogus="bummer")


def test_StlFile_eq():
    # arrange
    stl = StlFile(path="part.stl")
    not_stl = StlFile(path="not.stl")

    # act, assert
    assert stl == StlFile(path=stl.path)
    assert stl != StlFileMessage(name=stl.path)
    assert stl != not_stl


def test_StlFile_repr():
    # arrange
    bf = StlFile(path="part.stl")

    # act, assert
    assert bf.__repr__() == "StlFile\npath: part.stl\n"
