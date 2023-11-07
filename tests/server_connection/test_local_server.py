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

import glob
import os
import pathlib
import subprocess
from unittest.mock import ANY, Mock, patch

import pytest

from ansys.additive.core.server_connection.constants import DEFAULT_ANSYS_VERSION
from ansys.additive.core.server_connection.local_server import LocalServer

TEST_VALID_PORT = 1024


@patch("os.name", "unknown_os")
def test_launch_with_invalid_os_raises_exception():
    # arrange
    # act, assert
    with pytest.raises(OSError) as excinfo:
        LocalServer.launch(TEST_VALID_PORT)
    assert "Unsupported OS" in str(excinfo.value)


@patch("os.name", "nt")
def test_launch_with_windows_os_and_AWP_ROOT_not_defined_raises_exception():
    # arrange
    orig_ansys_ver = None
    if f"AWP_ROOT{DEFAULT_ANSYS_VERSION}" in os.environ:
        orig_ansys_ver = os.environ[f"AWP_ROOT{DEFAULT_ANSYS_VERSION}"]
        del os.environ[f"AWP_ROOT{DEFAULT_ANSYS_VERSION}"]
    # act, assert
    with pytest.raises(Exception) as excinfo:
        LocalServer.launch(TEST_VALID_PORT)
    assert "Cannot find Ansys installation directory" in str(excinfo.value)

    # cleanup
    if orig_ansys_ver:
        os.environ[f"AWP_ROOT{DEFAULT_ANSYS_VERSION}"] = orig_ansys_ver


@patch("os.name", "posix")
@patch("os.path.isdir")
def test_launch_with_linux_os_and_no_install_dir_raises_exception(mock_isdir):
    # arrange
    mock_isdir.return_value = False

    # act, assert
    with pytest.raises(FileNotFoundError) as excinfo:
        LocalServer.launch(TEST_VALID_PORT)
    assert "Cannot find Ansys installation directory" in str(excinfo.value)


@pytest.mark.skipif(os.name == "nt", reason="Test only valid on linux")
@patch("os.path.isdir")
def test_launch_with_linux_installation_but_invalid_ansys_version_raises_exception(mock_isdir):
    # arrange
    mock_isdir.return_value = True

    # act, assert
    with pytest.raises(FileNotFoundError) as excinfo:
        LocalServer.launch(TEST_VALID_PORT, product_version="bogus")
    assert "Cannot find " in str(excinfo.value)


@pytest.mark.skipif(os.name != "nt", reason="Test only valid on Windows")
def test_launch_when_exe_not_found_raises_exception_win():
    # arrange
    os.environ["AWP_ROOT241"] = "Bogus"

    # act, assert
    with pytest.raises(FileNotFoundError) as excinfo:
        LocalServer.launch(TEST_VALID_PORT)
    assert "Cannot find " in str(excinfo.value)


@pytest.mark.skipif(os.name != "nt", reason="Test only valid on Windows")
def test_launch_when_product_version_invalid_raises_exception_win(tmp_path: pathlib.Path):
    # arrange
    exe_name = tmp_path / "server.exe"
    exe_name.touch()
    os.environ["AWP_ROOT241"] = str(exe_name)

    # act, assert
    with pytest.raises(FileNotFoundError) as excinfo:
        LocalServer.launch(TEST_VALID_PORT, tmp_path, "233")
    assert "Cannot find Ansys installation directory" in str(excinfo.value)


@pytest.mark.skipif(os.name != "nt", reason="Test only valid on Windows")
def test_launch_when_product_version_invalid_raises_exception_win(tmp_path: pathlib.Path):
    # arrange
    exe_name = tmp_path / "server.exe"
    exe_name.touch()
    os.environ["AWP_ROOT241"] = str(exe_name)

    # act, assert
    with pytest.raises(Exception) as excinfo:
        LocalServer.launch(TEST_VALID_PORT, tmp_path, "242")
    assert "Cannot find Ansys installation directory" in str(excinfo.value)


@pytest.mark.skipif(os.name != "nt", reason="Test only valid on Windows")
@patch("subprocess.Popen")
def test_launch_calls_popen_as_expected_win(mock_popen, tmp_path: pathlib.Path):
    # arrange
    mock_process = Mock()
    product_version = "myversion"
    attrs = {"poll.return_value": None}
    mock_process.configure_mock(**attrs)
    mock_popen.return_value = mock_process
    os.environ[f"AWP_ROOT{product_version}"] = str(tmp_path)
    exe_path = tmp_path / "Additive" / "additiveserver" / "additiveserver.exe"
    exe_path.mkdir(parents=True, exist_ok=True)
    exe_path.touch(mode=0o777, exist_ok=True)

    # act
    LocalServer.launch(TEST_VALID_PORT, tmp_path, product_version)

    # assert
    mock_popen.assert_called_once_with(
        f'"{exe_path}" --port {TEST_VALID_PORT}',
        shell=False,
        cwd=tmp_path,
        stdout=ANY,
        stderr=subprocess.STDOUT,
    )
    assert len(glob.glob(str(tmp_path / "additiveserver_*.log"))) == 1


@pytest.mark.skipif(os.name == "nt", reason="Test only valid on linux")
@patch("os.path.exists")
@patch("os.path.isdir")
@patch("subprocess.Popen")
@patch("pathlib.Path.exists")
def test_launch_calls_popen_as_expected_linux(
    mock_pathlib_exists, mock_popen, mock_isdir, mock_os_exists, tmp_path: pathlib.Path
):
    # arrange
    mock_process = Mock()
    product_version = 123
    attrs = {"poll.return_value": None}
    mock_process.configure_mock(**attrs)
    mock_popen.return_value = mock_process
    mock_pathlib_exists.return_value = True
    mock_isdir.return_value = True
    mock_os_exists.return_value = True
    exe_path = f"/usr/ansys_inc/v{product_version}/Additive/additiveserver/additiveserver"

    # act
    LocalServer.launch(TEST_VALID_PORT, tmp_path, product_version)

    # assert
    mock_popen.assert_called_once_with(
        f'"{exe_path}" --port {TEST_VALID_PORT}',
        shell=True,
        cwd=tmp_path,
        stdout=ANY,
        stderr=subprocess.STDOUT,
    )
    assert len(glob.glob(str(tmp_path / "additiveserver_*.log"))) == 1


@pytest.mark.skipif(os.name == "posix", reason="Test only valid on Windows")
@patch("subprocess.Popen")
def test_launch_raises_exception_if_process_fails_to_start_win(mock_popen, tmp_path: pathlib.Path):
    # arrange
    os.environ["AWP_ROOT241"] = str(tmp_path)
    mock_process = Mock()
    attrs = {"poll.return_value": 1}
    mock_process.configure_mock(**attrs)
    mock_popen.return_value = mock_process
    exe_path = tmp_path / "Additive" / "additiveserver" / "additiveserver.exe"
    exe_path.mkdir(parents=True, exist_ok=True)
    exe_path.touch(mode=0o777, exist_ok=True)

    # act, assert
    with pytest.raises(Exception) as excinfo:
        LocalServer.launch(TEST_VALID_PORT, tmp_path)
    assert "Server exited with code" in str(excinfo.value)


@pytest.mark.skipif(os.name == "nt", reason="Test only valid on linux")
@patch("os.path.exists")
@patch("os.path.isdir")
@patch("subprocess.Popen")
@patch("pathlib.Path.exists")
def test_launch_raises_exception_if_process_fails_to_start_linux(
    mock_pathlib_exists, mock_popen, mock_isdir, mock_os_exists, tmp_path: pathlib.Path
):
    # arrange
    mock_process = Mock()
    attrs = {"poll.return_value": 1}
    mock_process.configure_mock(**attrs)
    mock_popen.return_value = mock_process
    mock_pathlib_exists.return_value = True
    mock_isdir.return_value = True
    mock_os_exists.return_value = True

    # act, assert
    with pytest.raises(Exception) as excinfo:
        LocalServer.launch(0, tmp_path)
    assert "Server exited with code" in str(excinfo.value)


def test_find_open_port_returns_valid_port():
    # act
    port = LocalServer.find_open_port()

    # assert
    assert port >= 1024 and port <= 65535
