import os

from ansys.api.additive.v0.additive_domain_pb2 import BuildFile as BuildFileMessage
from ansys.api.additive.v0.additive_domain_pb2 import BuildFileMachineType
from ansys.api.additive.v0.additive_domain_pb2 import StlFile as StlFileMessage

from ansys.additive.core.geometry_file import BuildFile, MachineType, StlFile

from . import test_utils


def test_BuildFile_init_returns_expected_object():
    # arrange, act
    file_path = os.path.abspath(__file__)
    build_file = BuildFile(type=MachineType.SLM, path=file_path)

    # assert
    assert isinstance(build_file, BuildFile)
    assert build_file.type == MachineType.SLM
    assert build_file.path == file_path


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


def test_StlFile_init_with_args_returns_expected_object():
    # arrange, act
    file_path = os.path.abspath(__file__)
    stl_file = StlFile(path=file_path)

    # assert
    assert isinstance(stl_file, StlFile)
    assert stl_file.path == file_path


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
