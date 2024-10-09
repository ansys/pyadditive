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
"""Provides startup utilities for a local Additive server."""

import os
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

from ansys.additive.core import USER_DATA_PATH
from ansys.additive.core.server_connection.constants import (
    ADDITIVE_SERVER_EXE_NAME,
    ADDITIVE_SERVER_SUBDIR,
    DEFAULT_PRODUCT_VERSION,
)


class LocalServer:
    """Provides startup utilities for a local Additive server."""

    @staticmethod
    def launch(
        port: int,
        cwd: str = USER_DATA_PATH,
        product_version: str = DEFAULT_PRODUCT_VERSION,
        linux_install_path: os.PathLike | None = None,
    ) -> subprocess.Popen:
        """Launch a local gRPC server for the Additive service.

        Parameters
        ----------
        port: int
            Port number to use for gRPC connections.
        cwd: str
            Current working directory to use for the server process.
        product_version: str
            Version of the Ansys installation to use, of the form ``"YYR"``, where
            ``YY`` is the two digit year and ``R`` is the release for
            that year. For example, Ansys 2024 R1 would be ``"241"``.
        linux_install_path: os.PathLike, None default: None
            Path to the Ansys installation directory on Linux. This parameter is only
            required when Ansys has not been installed in the default location. Example:
            ``/usr/shared/ansys_inc``. Note that the path does not include the product
            version.

        Returns
        -------
        process: subprocess.Popen
            Server process. To stop the server, call the ``kill()`` method on the returned object.

        """
        server_exe = ""
        if os.name == "nt":
            env_var = (
                f"AWP_ROOT{product_version}"
                if product_version
                else f"AWP_ROOT{DEFAULT_PRODUCT_VERSION}"
            )
            awp_root = os.environ.get(env_var)
            if not awp_root:
                raise FileNotFoundError("Cannot find Ansys installation directory")
            server_exe = Path(awp_root) / ADDITIVE_SERVER_SUBDIR / f"{ADDITIVE_SERVER_EXE_NAME}.exe"
        elif os.name == "posix":
            base_path = None
            if linux_install_path is not None:
                if not os.path.isdir(str(linux_install_path)):
                    raise FileNotFoundError(f"Cannot find {linux_install_path}")
                base_path = linux_install_path
            else:
                for path in ["/usr/ansys_inc", "/ansys_inc"]:
                    if os.path.isdir(path):
                        base_path = path
                        break
            if not base_path:
                raise FileNotFoundError("Cannot find Ansys installation directory")
            server_exe = (
                Path(base_path)
                / f"v{product_version}"
                / ADDITIVE_SERVER_SUBDIR
                / ADDITIVE_SERVER_EXE_NAME
            )
        else:
            raise OSError(f"Unsupported OS {os.name}")

        if not server_exe.exists():
            raise FileNotFoundError(f"Cannot find {server_exe}")

        Path(cwd).mkdir(parents=True, exist_ok=True)

        start_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        with open(os.path.join(cwd, f"additiveserver_{start_time}.log"), "w") as log_file:
            server_process = subprocess.Popen(  # noqa: S603
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

    @staticmethod
    def find_open_port() -> int:
        """Find an open port on the local host.

        Returns
        -------
        port: int
            Open port number.

        .. note::
            This port may be taken by the time you try to use it.

        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = s.getsockname()[1]
        s.close()
        return port
