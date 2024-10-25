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

from unittest.mock import ANY, Mock, create_autospec

import grpc
import pytest
from google.protobuf.empty_pb2 import Empty

import ansys.additive.core.server_connection.local_server
import ansys.additive.core.server_connection.server_connection
import ansys.api.additive.v0.about_pb2_grpc
import ansys.platform.instancemanagement as pypim
from ansys.additive.core.server_connection.constants import (
    LOCALHOST,
    PYPIM_PRODUCT_NAME,
)
from ansys.additive.core.server_connection.server_connection import (
    ServerConnection,
    ServerConnectionStatus,
)
from ansys.api.additive.v0.about_pb2 import AboutResponse
from ansys.api.additive.v0.about_pb2_grpc import AboutServiceStub
from ansys.api.additive.v0.additive_materials_pb2_grpc import MaterialsServiceStub
from ansys.api.additive.v0.additive_simulation_pb2_grpc import SimulationServiceStub


def test_init_raises_exception_if_channel_and_addr_provided():
    # arrange
    channel = grpc.insecure_channel("target")
    addr = "server.address"

    # act, assert
    with pytest.raises(ValueError) as exc:
        ServerConnection(channel, addr)
    assert "Both 'channel' and 'addr' cannot both be specified" in str(exc.value)


def test_init_connects_with_channel(monkeypatch):
    # arrange
    channel = grpc.insecure_channel("target")

    mock_ready = create_autospec(
        ansys.additive.core.server_connection.server_connection.ServerConnection.ready,
        return_value=True,
    )
    monkeypatch.setattr(
        ansys.additive.core.server_connection.server_connection.ServerConnection,
        "ready",
        mock_ready,
    )

    # act
    server = ServerConnection(channel=channel)

    # assert
    assert server._channel == channel
    assert hasattr(server, "_server_instance") == False
    assert isinstance(server.materials_stub, MaterialsServiceStub)
    assert isinstance(server.simulation_stub, SimulationServiceStub)
    assert isinstance(server._about_stub, AboutServiceStub)
    assert server.channel_str == "target"


def test_init_connects_with_addr(monkeypatch):
    # arrange
    addr = "1.2.3.4:1234"
    mock_ready = create_autospec(
        ansys.additive.core.server_connection.server_connection.ServerConnection.ready,
        return_value=True,
    )
    monkeypatch.setattr(
        ansys.additive.core.server_connection.server_connection.ServerConnection,
        "ready",
        mock_ready,
    )

    # act
    server = ServerConnection(addr=addr)

    # assert
    assert server.channel_str == addr
    assert hasattr(server, "_server_instance") == False
    assert isinstance(server.materials_stub, MaterialsServiceStub)
    assert isinstance(server.simulation_stub, SimulationServiceStub)
    assert isinstance(server._about_stub, AboutServiceStub)


def test_init_connects_with_pypim(monkeypatch):
    # arrange
    target = "localhost:1234"
    mock_ready = create_autospec(
        ansys.additive.core.server_connection.server_connection.ServerConnection.ready,
        return_value=True,
    )
    monkeypatch.setattr(
        ansys.additive.core.server_connection.server_connection.ServerConnection,
        "ready",
        mock_ready,
    )
    mock_instance = pypim.Instance(
        definition_name="definition",
        name="name",
        ready=True,
        status_message=None,
        services={"grpc": pypim.Service(uri=f"dns:{target}", headers={})},
    )

    mock_client = pypim.Client(channel=grpc.insecure_channel("ignored"))
    mock_client.create_instance = create_autospec(
        mock_client.create_instance, return_value=mock_instance
    )
    mock_instance.wait_for_ready = create_autospec(mock_instance.wait_for_ready)
    mock_instance.delete = create_autospec(mock_instance.delete)
    mock_connect = create_autospec(pypim.connect, return_value=mock_client)
    mock_is_configured = create_autospec(pypim.is_configured, return_value=True)
    monkeypatch.setattr(pypim, "connect", mock_connect)
    monkeypatch.setattr(pypim, "is_configured", mock_is_configured)

    # act
    server = ServerConnection(product_version="123")

    # assert
    assert server.channel_str == target
    assert hasattr(server, "_server_instance") == True
    assert isinstance(server.materials_stub, MaterialsServiceStub)
    assert isinstance(server.simulation_stub, SimulationServiceStub)
    assert isinstance(server._about_stub, AboutServiceStub)
    mock_client.create_instance.assert_called_with(
        product_name=PYPIM_PRODUCT_NAME, product_version="123"
    )


def test_init_starts_local_server(monkeypatch):
    # arrange
    mock_ready = create_autospec(
        ansys.additive.core.server_connection.server_connection.ServerConnection.ready,
        return_value=True,
    )
    monkeypatch.setattr(
        ansys.additive.core.server_connection.server_connection.ServerConnection,
        "ready",
        mock_ready,
    )
    mock_launch = create_autospec(
        ansys.additive.core.server_connection.local_server.LocalServer.launch,
        return_value=None,
    )
    monkeypatch.setattr(
        ansys.additive.core.server_connection.local_server.LocalServer,
        "launch",
        mock_launch,
    )

    # act
    server = ServerConnection(product_version="123")

    # assert
    assert LOCALHOST in server.channel_str
    assert hasattr(server, "_server_instance") is False
    assert isinstance(server.materials_stub, MaterialsServiceStub)
    assert isinstance(server.simulation_stub, SimulationServiceStub)
    assert isinstance(server._about_stub, AboutServiceStub)
    mock_launch.assert_called_with(ANY, product_version="123", linux_install_path=None)


def test_ready_returns_true_when_about_succeeds():
    # assert
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.ready = ServerConnection.ready

    def mock_about_endpoint(request: Empty):
        response = AboutResponse()
        response.metadata["key1"] = "value1"
        response.metadata["key2"] = "value2"
        response.metadata["key3"] = "value3"
        return response

    mock_stub = Mock(AboutServiceStub)
    mock_stub.About = Mock(side_effect=mock_about_endpoint)
    mock_server_connection._about_stub = mock_stub

    # act
    ready = mock_server_connection.ready(mock_server_connection)

    # assert
    assert ready == True
    mock_stub.About.assert_called_once()


def test_ready_returns_false_when_about_fails():
    # assert
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.ready = ServerConnection.ready

    def mock_about_endpoint(request: Empty):
        raise grpc.RpcError

    mock_stub = Mock(AboutServiceStub)
    mock_stub.About = Mock(side_effect=mock_about_endpoint)
    mock_server_connection._about_stub = mock_stub

    # act
    ready = mock_server_connection.ready(mock_server_connection, 0)

    # assert
    assert ready == False
    mock_stub.About.assert_called_once()


def test_status_with_no_channel_returns_expected_status():
    # arrange
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.status = ServerConnection.status

    # act
    status = mock_server_connection.status(mock_server_connection)

    # assert
    assert isinstance(status, ServerConnectionStatus)
    assert status.connected == False
    assert status.channel_str is None
    assert status.metadata is None


def test_status_channel_none_returns_expected_status():
    # arrange
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.status = ServerConnection.status
    mock_server_connection._channel = None

    # act
    status = mock_server_connection.status(mock_server_connection)

    # assert
    assert isinstance(status, ServerConnectionStatus)
    assert status.connected == False
    assert status.channel_str is None
    assert status.metadata is None


def test_status_when_connected_returns_expected_status():
    # arrange
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.status = ServerConnection.status
    mock_server_connection._channel = "channel"
    mock_server_connection.channel_str = "channel_str"

    def mock_about_endpoint(request: Empty):
        response = AboutResponse()
        response.metadata["key1"] = "value1"
        response.metadata["key2"] = "value2"
        response.metadata["key3"] = "value3"
        return response

    mock_stub = Mock(AboutServiceStub)
    mock_stub.About = Mock(side_effect=mock_about_endpoint)
    mock_server_connection._about_stub = mock_stub

    # act
    status = mock_server_connection.status(mock_server_connection)

    # assert
    mock_stub.About.assert_called_once
    assert status.connected == True
    assert status.channel_str == "channel_str"
    assert status.metadata["key1"] == "value1"
    assert status.metadata["key2"] == "value2"
    assert status.metadata["key3"] == "value3"


def test_status_when_not_connected_returns_expected_status():
    # arrange
    mock_server_connection = Mock(ServerConnection)
    mock_server_connection.status = ServerConnection.status
    mock_server_connection._channel = "channel"
    mock_server_connection.channel_str = "channel_str"

    def mock_about_endpoint(request: Empty):
        raise grpc.RpcError

    mock_stub = Mock(AboutServiceStub)
    mock_stub.About = Mock(side_effect=mock_about_endpoint)
    mock_server_connection._about_stub = mock_stub

    # act
    status = mock_server_connection.status(mock_server_connection)

    # assert
    mock_stub.About.assert_called_once
    assert status.connected == False
    assert status.channel_str == "channel_str"
    assert status.metadata == None


def test_server_connection_status_str_not_connected():
    # arrange
    status = ServerConnectionStatus(connected=False, channel_str="localhost:50051")

    # act
    status_str = str(status)

    # assert
    assert status_str == "Server localhost:50051 is not connected."


def test_server_connection_status_str_connected_without_metadata():
    # arrange
    status = ServerConnectionStatus(connected=True, channel_str="localhost:50051")

    # act
    status_str = str(status)

    # assert
    assert status_str == "Server localhost:50051 is connected."


def test_server_connection_status_str_connected_with_metadata():
    # arrange
    metadata = {"version": "1.0", "status": "running"}
    status = ServerConnectionStatus(
        connected=True, channel_str="localhost:50051", metadata=metadata
    )

    # act
    status_str = str(status)

    # assert
    expected_str = "Server localhost:50051 is connected.\n  version: 1.0\n  status: running"
    assert status_str == expected_str
