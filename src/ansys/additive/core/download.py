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

import hashlib
import os

from ansys.api.additive.v0.additive_simulation_pb2 import DownloadFileRequest
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub

from ansys.additive.core.progress_logger import Progress, ProgressLogger, ProgressState


def download_file(
    stub: SimulationServiceStub,
    remote_file_name: str,
    local_folder: str,
    logger: ProgressLogger = None,
) -> str:
    """Download a file from the server to the localhost.

    Parameters
    ----------
    remote_file_name: str
        Path to file on the server.
    local_folder: str
        Folder on your localhost to write your file to.
    logger: ProgressLogger
        Log message handler.

    Returns
    -------
    str
        Local path of downloaded file.
    """

    if not os.path.isdir(local_folder):
        os.makedirs(local_folder)

    dest = os.path.join(local_folder, os.path.basename(remote_file_name))
    request = DownloadFileRequest(remote_file_name=remote_file_name)

    with open(dest, "wb") as f:
        for response in stub.DownloadFile(request):
            if logger:
                logger.log_progress(response.progress)  # pragma: no cover
            if len(response.content) > 0:
                md5 = hashlib.md5(response.content).hexdigest()
                if md5 != response.content_md5:
                    if logger:  # pragma: no cover
                        logger.log_progress(
                            Progress(
                                state=ProgressState.PROGRESS_STATE_ERROR,
                                message="Download error, MD5 sums did not match",
                            )
                        )
                    raise ValueError("Download error, MD5 sums did not match")
                f.write(response.content)
    return dest
