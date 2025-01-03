# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
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

import hashlib
import os
import tempfile
from unittest.mock import Mock

import pytest

from ansys.additive.core.download import download_file
from ansys.api.additive.v0.additive_domain_pb2 import (
    DownloadFileResponse,
    Progress,
    ProgressState,
)
from ansys.api.additive.v0.additive_simulation_pb2 import DownloadFileRequest
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub


def test_download_file_calls_service_with_expected_params():
    # arrange
    remote_file_name = os.path.join("remote", "myfile.txt")
    expected_request = DownloadFileRequest(remote_file_name=remote_file_name)

    def mock_download_endpoint(request: DownloadFileRequest):
        content = bytes(range(255))
        md5 = hashlib.md5(content).hexdigest()
        progress = Progress(
            state=ProgressState.PROGRESS_STATE_EXECUTING,
            percent_complete=100,
            message="done",
            context="download",
        )
        yield DownloadFileResponse(
            file_name="ignored",
            total_size=len(content),
            content=content,
            content_md5=md5,
            progress=progress,
        )

    mock_stub = Mock(SimulationServiceStub)
    mock_stub.DownloadFile = Mock(side_effect=mock_download_endpoint)
    tmp_dir = tempfile.TemporaryDirectory().name

    # act
    local_file = download_file(mock_stub, remote_file_name, tmp_dir)

    # assert
    mock_stub.DownloadFile.assert_called_once_with(expected_request)
    assert local_file == os.path.join(tmp_dir, "myfile.txt")


def test_download_raises_exception_if_md5_check_fails():
    # arrange
    remote_file_name = os.path.join("remote", "myfile.txt")
    expected_request = DownloadFileRequest(remote_file_name=remote_file_name)

    def mock_download_endpoint(request: DownloadFileRequest):
        content = bytes(range(255))
        md5 = "invalid md5"
        progress = Progress(
            state=ProgressState.PROGRESS_STATE_EXECUTING,
            percent_complete=100,
            message="done",
            context="download",
        )
        yield DownloadFileResponse(
            file_name="ignored",
            total_size=len(content),
            content=content,
            content_md5=md5,
            progress=progress,
        )

    mock_stub = Mock(SimulationServiceStub)
    mock_stub.DownloadFile = Mock(side_effect=mock_download_endpoint)
    tmp_dir = tempfile.TemporaryDirectory().name

    # act
    with pytest.raises(ValueError, match="Download error, MD5 sums did not match"):
        local_file = download_file(mock_stub, remote_file_name, tmp_dir)

    # assert
    mock_stub.DownloadFile.assert_called_once_with(expected_request)
