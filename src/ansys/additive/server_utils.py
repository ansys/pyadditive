# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from datetime import datetime
import os
import subprocess
import time

from ansys.additive import USER_DATA_PATH

DEFAULT_ANSYS_VERSION = "241"
ADDITIVE_SERVER_EXE_NAME = "Additive.Grpc"


def launch_server(port: int, cwd: str = USER_DATA_PATH) -> subprocess.Popen:
    """Launch a local gRPC server for the Additive service.

    Parameters
    ----------

    port: int
        Port number to use for gRPC connections.

    cwd: str
        Current working directory to use for the server process.

    Returns
    -------
    process: subprocess.Popen
        Server process. To stop the server, call ``kill()`` on the returned object.

    """
    ver = DEFAULT_ANSYS_VERSION
    server_exe = ""
    if os.name == "nt":
        awp_root = os.environ.get(f"AWP_ROOT{ver}")
        if not awp_root:
            raise Exception("Cannot find Ansys installation directory")
        server_exe = os.path.join(
            awp_root, "Additive", "additive_grpc", f"{ADDITIVE_SERVER_EXE_NAME}.exe"
        )
    elif os.name == "posix":
        base_path = None
        for path in ["/usr/ansys_inc", "/ansys_inc"]:
            if os.path.isdir(path):
                base_path = path  # pragma: no cover
                break
        if not base_path:
            raise Exception("Cannot find Ansys installation directory")
        server_exe = os.path.join(
            base_path, f"v{ver}", "Additive", "additive_grpc", ADDITIVE_SERVER_EXE_NAME
        )
    else:
        raise OSError(f"Unsupported OS {os.name}")

    if not os.path.exists(server_exe):
        raise FileNotFoundError(f"Cannot find {server_exe}")

    if not os.path.exists(cwd):
        os.makedirs(cwd)  # pragma: no cover

    start_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(os.path.join(cwd, f"additive_server_{start_time}.log"), "w") as log_file:
        server_process = subprocess.Popen(
            f'"{server_exe}" --port {port}',
            shell=os.name != "nt",  # use shell on Linux
            cwd=cwd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        time.sleep(2)  # wait for server to start
        if server_process.poll():
            raise Exception(f"Server exited with code {server_process.returncode}")

    return server_process


def find_open_port() -> int:
    """Find an open port on the local host.

    Returns
    -------
    port: int
        Open port number. *Note:* this port may be taken by the time you try to use it.

    """
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = s.getsockname()[1]
    s.close()
    return port
