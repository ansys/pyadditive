# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from unittest.mock import patch

import pytest

from ansys.additive.server_utils import launch_server


@patch("os.name", "unknown_os")
def test_launch_server_with_invalid_os_raises_exception():
    # arrange
    # act, assert
    with pytest.raises(OSError) as excinfo:
        launch_server(0)
    assert "Unsupported OS" in str(excinfo.value)


@patch("os.name", "nt")
def test_launch_server_with_windows_os_and_AWP_ROOT_not_defined_raises_exception():
    # arrange
    # act, assert
    with pytest.raises(Exception) as excinfo:
        launch_server(0)
    assert "Cannot find Ansys installation directory" in str(excinfo.value)
