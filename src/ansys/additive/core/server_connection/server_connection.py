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
"""Provides definitions and untilities for connecting to the Additive server."""

from dataclasses import dataclass
import logging
import os
import time

from ansys.api.additive.v0.about_pb2_grpc import AboutServiceStub
from ansys.api.additive.v0.additive_materials_pb2_grpc import MaterialsServiceStub
from ansys.api.additive.v0.additive_settings_pb2_grpc import SettingsServiceStub
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub
import ansys.platform.instancemanagement as pypim
from google.longrunning.operations_pb2_grpc import OperationsStub
from google.protobuf.empty_pb2 import Empty
import grpc

from ansys.additive.core.server_connection.constants import (
    DEFAULT_PRODUCT_VERSION,
    LOCALHOST,
    PYPIM_PRODUCT_NAME,
)
from ansys.additive.core.server_connection.local_server import LocalServer
from ansys.additive.core.server_connection.network_utils import create_channel


@dataclass(frozen=True)
class ServerConnectionStatus:
    """Provides status information about a server.

    Parameters
    ----------
    connected: bool
        True if server is connected.
    channel_str: string, None
        Hostname and port of server connection in the form ``host:port``.
    metadata: dict, None
        Server metadata.
    """

    connected: bool
    """True if server is connected."""
    channel_str: str = None
    """Hostname and port of server connection in the form ``host:port``."""
    metadata: dict = None
    """Server metadata."""


class ServerConnection:
    """Provides connection to Additive server.

    If neither ``channel`` nor ``addr`` are provided, an attempt is
    made to start an Additive server and connect to it. Starting a server
    in a cloud environment requires
    `PyPIM <https://pypim.docs.pyansys.com/version/stable/index.html>`_ to be available.
    To start a server when running on localhost, the Additive option of the
    Structures package of the Ansys unified installation must be installed.

    Parameters
    ----------
    channel: grpc.Channel, None
        gRPC channel connected to server.
    addr: str, None
        IPv4 address of server of the form ``host:port``.
    product_version: str
        Version of the Ansys product installation in the form ``"YYR"``, where ``YY``
        is the two-digit year and ``R`` is the release number. For example, the release
        2024 R1 would be specified as ``241``. This parameter is only applicable in
        `PyPIM <https://pypim.docs.pyansys.com/version/stable/index.html>`_-enabled
        cloud environments and on localhost.
    log: logging.Logger, None
        Log to write connection messages to.
    linux_install_path: os.PathLike, None default: None
        Path to the Ansys installation directory on Linux. This parameter is only
        required when Ansys has not been installed in the default location. Example:
        ``/usr/shared/ansys_inc``. Note that the path should not include the product
        version.
    """

    def __init__(
        self,
        channel: grpc.Channel | None = None,
        addr: str | None = None,
        product_version: str = DEFAULT_PRODUCT_VERSION,
        log: logging.Logger = None,
        linux_install_path: os.PathLike | None = None,
    ) -> None:
        """Initialize a server connection."""

        if channel and addr:
            raise ValueError("Both 'channel' and 'addr' cannot both be specified.")

        self._log = log if log else logging.getLogger(__name__)

        if channel:
            self._channel = channel
        else:
            if addr:
                target = addr
            elif pypim.is_configured():
                pim = pypim.connect()
                self._server_instance = pim.create_instance(
                    product_name=PYPIM_PRODUCT_NAME, product_version=product_version
                )
                self._log.info("Waiting for server to initialize")
                self._server_instance.wait_for_ready()
                (_, target) = self._server_instance.services["grpc"].uri.split(":", 1)
            else:
                port = LocalServer.find_open_port()
                self._server_process = LocalServer.launch(
                    port, product_version=product_version, linux_install_path=linux_install_path
                )
                target = f"{LOCALHOST}:{port}"
            self._channel = create_channel(target)

        # assign service stubs
        self._materials_stub = MaterialsServiceStub(self._channel)
        self._simulation_stub = SimulationServiceStub(self._channel)
        self._about_stub = AboutServiceStub(self._channel)
        self._operations_stub = OperationsStub(self._channel)
        self._settings_stub = SettingsServiceStub(self._channel)

        if not self.ready():
            raise RuntimeError(f"Unable to connect to server {self.channel_str}")

        self._log.info("Connected to %s", self.channel_str)

    def __del__(self):
        """Destructor for cleaning up server connection."""
        if hasattr(self, "_server_instance") and self._server_instance:
            self._server_instance.delete()
        if hasattr(self, "_server_process") and self._server_process:
            self._server_process.kill()

    @property
    def channel_str(self) -> str:
        """GRPC channel target.

        The form is generally ``"ip:port"``. For example, ``"127.0.0.1:50052"``.
        """
        if self._channel is not None:
            return self._channel._channel.target().decode().removeprefix("dns:///")
        return ""

    @property
    def materials_stub(self) -> MaterialsServiceStub:
        """Materials service stub."""
        return self._materials_stub

    @property
    def simulation_stub(self) -> SimulationServiceStub:
        """Simulation service stub."""
        return self._simulation_stub

    @property
    def operations_stub(self) -> OperationsStub:
        """Operations service stub."""
        return self._operations_stub

    @property
    def settings_stub(self) -> SettingsServiceStub:
        """Settings service stub."""
        return self._settings_stub

    def status(self) -> ServerConnectionStatus:
        """Return the server connection status."""
        if not hasattr(self, "_channel") or self._channel is None:
            return ServerConnectionStatus(False)
        try:
            response = self._about_stub.About(Empty())
        except grpc.RpcError:
            return ServerConnectionStatus(False, self.channel_str)
        metadata = {}
        for key in response.metadata:
            metadata[key] = response.metadata[key]
        return ServerConnectionStatus(True, self.channel_str, metadata)

    def ready(self, retries: int = 5) -> bool:
        """Return whether the server is ready.

        Parameters
        ----------
        retries: int
            Number of times to retry before giving up. An linearly increasing delay
            is used between each retry.

        Returns
        -------
        bool:
            True means server is ready. False means the number of retries was exceeded
            without receiving a response from the server.
        """
        ready = False
        for i in range(retries + 1):
            try:
                self._about_stub.About(Empty())
                ready = True
                break
            except grpc.RpcError:
                time.sleep(i + 1)

        return ready
