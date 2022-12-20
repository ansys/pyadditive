from enum import IntEnum

from ansys.api.additive.v0.additive_domain_pb2 import BuildFileMachineType


class MachineType(IntEnum):
    NONE = BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_NONE
    ADDITIVE_INDUSTRIES = BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_AI
    SLM = BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_SLM
    RENISHAW = BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_RENISHAW
    EOS = BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_EOS
    TRUMPF = BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_TRUMPF
    HB3D = BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_HB3D
    SISMA = BuildFileMachineType.BUILD_FILE_MACHINE_TYPE_SISMA


class BuildFile:
    """Build file description

    Properties
    ----------

    type: MachineType
        Additive manufacturing machine type used with this file
    path: string
        Path of zip archive containing build instruction file, geometry stl file and
        optional support stl files.
    """

    def __init__(self, **kwargs):
        self.type = MachineType.NONE
        self.path = ""
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BuildFile):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True


class StlFile:
    """Container for stl file definition.

    Properties
    ----------

    path: str
        Path to stl file on local client

    """

    def __init__(self, **kwargs):
        self.path = None
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StlFile):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True
