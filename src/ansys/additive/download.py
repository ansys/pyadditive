# (c) 2022 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.

import hashlib
import os

from ansys.api.additive.v0.additive_simulation_pb2 import DownloadFileRequest
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub

from ansys.additive.progress_logger import Progress, ProgressLogger, ProgressState


def download_file(
    stub: SimulationServiceStub,
    remote_file_name: str,
    local_folder: str,
    log_progress: bool = True,
):
    """Download a file from the server to the local host

    Parameters
    ----------

    remote_file_name: str
        Path to file on the server
    local_folder: str
        Folder on local host to write file to

    """

    logger = None
    if log_progress:
        logger = ProgressLogger("Download")

    if not os.path.isdir(local_folder):
        os.makedirs(local_folder)

    dest = os.path.join(local_folder, os.path.basename(remote_file_name))
    request = DownloadFileRequest(remote_file_name=remote_file_name)

    with open(dest, "wb") as f:
        for response in stub.DownloadFile(request):
            if logger:
                logger.log_progress(response.progress)
            if len(response.content) > 0:
                md5 = hashlib.md5(response.content).hexdigest()
                if md5 != response.content_md5:
                    if logger:
                        logger.log_progress(
                            Progress(
                                state=ProgressState.PROGRESS_STATE_ERROR,
                                message="Download error, MD5 sums did not match",
                            )
                        )
                    raise ValueError("Download error, MD5 sums did not match")
                f.write(response.content)
    return dest
