# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import hashlib
import os
import tempfile
from unittest.mock import Mock

from ansys.api.additive.v0.additive_domain_pb2 import Progress, ProgressState
from ansys.api.additive.v0.additive_simulation_pb2 import DownloadFileRequest, DownloadFileResponse
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub
import pytest

from ansys.additive.download import download_file


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
