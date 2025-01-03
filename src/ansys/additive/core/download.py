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
"""Provides a function for downloading files from the server to the client."""

import datetime
import hashlib
import os

from ansys.additive.core.progress_handler import (
    IProgressHandler,
    Progress,
    ProgressState,
)
from ansys.api.additive.v0.additive_server_info_pb2_grpc import ServerInfoServiceStub
from ansys.api.additive.v0.additive_simulation_pb2 import DownloadFileRequest
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub


def download_file(
    stub: SimulationServiceStub,
    remote_file_name: str,
    local_folder: str,
    progress_handler: IProgressHandler = None,
) -> str:
    """Download a file from the server to the localhost.

    Parameters
    ----------
    stub: SimulationServiceStub
        gRPC stub for the simulation service.
    remote_file_name: str
        Path to file on the server.
    local_folder: str
        Folder on your localhost to write your file to.
    progress_handler: ProgressLogger, None, default: None
        Progress update handler. If ``None``, no progress will be provided.

    Returns
    -------
    str
        Local path of downloaded file.

    """

    if not os.path.isdir(local_folder):
        os.makedirs(local_folder)

    dest = os.path.join(local_folder, os.path.basename(remote_file_name))
    request = DownloadFileRequest(remote_file_name=remote_file_name)

    handle_download_file_response(dest, stub.DownloadFile(request), progress_handler)
    return dest


def download_logs(
    stub: ServerInfoServiceStub,
    local_folder: str,
    progress_handler: IProgressHandler = None,
) -> str:
    """Download logs from the server to the localhost.

    Parameters
    ----------
    stub: ServerInfoServiceStub
        gRPC stub for the server information service.
    local_folder: str
        Folder on your localhost to write the server logs to.
    progress_handler: ProgressLogger, None, default: None
        Progress update handler. If ``None``, no progress will be provided.

    Returns
    -------
    str
        Local path of downloaded file.

    """

    if not os.path.isdir(local_folder):
        os.makedirs(local_folder)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(local_folder, f"additive-server-logs-{timestamp}.zip")
    response = stub.ServerLogs()

    handle_download_file_response(dest, response, progress_handler)
    return dest


def handle_download_file_response(
    destination: str,
    download_file_response: any,
    progress_handler: IProgressHandler = None,
) -> None:
    """
    Handle server response.

    Parameters
    ----------
    destination: str
        Destination of the file.
    download_file_response: any
        Download file response.
    progress_handler: IProgressHandler, default: None
        Progress handler.

    """

    with open(destination, "wb") as f:
        for response in download_file_response:
            if progress_handler:
                progress_handler.update(
                    Progress.from_proto_msg(response.progress)
                )  # pragma: no cover
            if len(response.content) > 0:
                md5 = hashlib.md5(response.content).hexdigest()  # noqa: S324
                if md5 != response.content_md5:
                    msg = "Download error, MD5 sums did not match"
                    if progress_handler:  # pragma: no cover
                        progress_handler.update(
                            Progress(
                                state=ProgressState.ERROR,
                                message=msg,
                            )
                        )
                    raise ValueError(msg)
                f.write(response.content)
