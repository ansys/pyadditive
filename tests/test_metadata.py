# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from ansys.additive import __version__


def test_pkg_version():
    assert __version__ == "0.3.7"
