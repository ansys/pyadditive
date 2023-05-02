from datetime import datetime
import os
import subprocess
import time

from ansys.additive import USER_DATA_PATH

DEFAULT_ANSYS_VERSION = "241"
ADDITIVE_SERVER_EXE_NAME = "Additive.Grpc"


def launch_server(port: int):
    """Launch a local gRPC server for the Additive service.

    Parameters
    ----------

    port: int
        Port number to use for gRPC connections.
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
                base_path = path
        if not base_path:
            raise Exception("Cannot find Ansys installation directory")
        server_exe = os.path.join(
            base_path, f"v{ver}", "Additive", "additive_grpc", ADDITIVE_SERVER_EXE_NAME
        )
    else:
        raise OSError(f"Unsupported OS {os.name}")

    working_dir = os.path.join(USER_DATA_PATH, "additive_server")
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = open(os.path.join(working_dir, f"additive_server_{start_time}.log"), "w")

    cmd = f'"{server_exe}" --port {port}'
    server_process = subprocess.Popen(
        cmd,
        shell=os.name != "nt",  # use shell on Linux
        cwd=working_dir,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    time.sleep(2)  # wait for server to start
    if server_process.poll():
        raise Exception(f"Server exited with code {server_process.returncode}")

    return server_process
