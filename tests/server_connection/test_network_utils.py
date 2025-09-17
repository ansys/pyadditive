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
import os
from pathlib import Path
from unittest.mock import create_autospec

import grpc
import pytest

from ansys.additive.core.server_connection.network_utils import (
    MAX_RCV_MSG_LEN,
    check_grpc_version,
    check_valid_ip,
    check_valid_port,
    create_channel,
    is_uds_supported,
    version_tuple,
)
from ansys.additive.core.server_connection.server_connection import TransportMode


@pytest.mark.parametrize(
    "ip",
    [
        "1.2.3.4",
        "127.0.0.1",
        "8.8.8.8",
        "localhost",
    ],
)
def test_valid_ip_returns_without_error_for_valid_values(ip: str):
    # arrange, act, assert
    check_valid_ip(ip)


def test_valid_ip_raises_error_for_invalid_values():
    # arrange, act, assert
    with pytest.raises(Exception):
        check_valid_ip("google.com")
    with pytest.raises(Exception):
        check_valid_ip("1.2.3.")


def test_check_valid_port_returns_without_error_for_valid_values():
    # arrange
    ports = [1024, 65535, "1024"]
    # act, assert
    [check_valid_port(port) for port in ports]
    check_valid_port("1", 0, 2)


def test_check_valid_port_raises_error_for_invalid_values():
    # arrange
    ports = [1023, 65536, "1023"]
    # act, assert
    for port in ports:
        with pytest.raises(ValueError):
            check_valid_port(port)


def test_create_channel_returns_expected_channel():
    # arrange
    target = "1.2.3.4:1234"

    # act
    channel = create_channel(target=target, transport_mode=TransportMode.INSECURE)

    # assert
    assert channel is not None
    assert channel._channel.target().decode().removeprefix("dns:///") == target  # type: ignore


def test_create_channel_raises_exception_for_missing_ip():
    # arrange
    target = ":1234"

    # act, assert
    with pytest.raises(ValueError):
        create_channel(target=target, transport_mode=TransportMode.INSECURE)


def test_create_channel_raises_exception_for_bad_port():
    # arrange
    target = "1.2.3.4:123"

    # act, assert
    with pytest.raises(ValueError):
        create_channel(target=target, transport_mode=TransportMode.INSECURE)


def test_create_channel_sets_max_rcv_msg_len(monkeypatch):
    # arrange
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=None)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)
    msg_len = 8 * 1024**2
    target = "1.2.3.4:1234"

    # act
    create_channel(target=target, transport_mode=TransportMode.INSECURE, max_rcv_msg_len=msg_len)

    # assert
    mock_insecure_channel.assert_called_with(
        target, options=[("grpc.max_receive_message_length", msg_len)]
    )


def test_create_channel_uses_custom_uds_path_and_id(monkeypatch):
    # arrange
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=None)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)
    target = "127.0.0.1:1234"
    monkeypatch.setattr(
        "ansys.additive.core.server_connection.network_utils.is_uds_supported",
        lambda: True,
    )
    custom_uds_dir = Path("custom")

    # act
    create_channel(
        target=target, transport_mode=TransportMode.UDS, uds_dir=custom_uds_dir, uds_id="myid"
    )

    # assert
    if os.name == "nt":
        expected_uds_path = custom_uds_dir / "additiveserver-myid.sock"
        expected_target = f"unix:{expected_uds_path}"
        mock_insecure_channel.assert_called_with(
            expected_target,
            options=(
                ("grpc.default_authority", "localhost"),
                ("grpc.max_receive_message_length", MAX_RCV_MSG_LEN),
            ),
        )
    else:
        expected_target = f"unix:{custom_uds_dir}/additiveserver-myid.sock"
        mock_insecure_channel.assert_called_with(
            expected_target,
            options=(
                ("grpc.default_authority", "localhost"),
                ("grpc.max_receive_message_length", MAX_RCV_MSG_LEN),
            ),
        )


def test_create_channel_uds_raises_for_non_localhost(monkeypatch):
    # arrange
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=None)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)
    monkeypatch.setattr(
        "ansys.additive.core.server_connection.network_utils.is_uds_supported",
        lambda: True,
    )
    target = "1.1.1.1:1234"

    # act, assert
    with pytest.raises(ValueError, match="UDS transport only supports localhost connections."):
        create_channel(target=target, transport_mode=TransportMode.UDS)


def test_create_channel_uds_raises_for_uds_not_supported(monkeypatch):
    # arrange
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=None)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)
    monkeypatch.setattr(
        "ansys.additive.core.server_connection.network_utils.is_uds_supported",
        lambda: False,
    )
    target = "localhost:1234"

    # act, assert
    with pytest.raises(
        RuntimeError,
        match="Unix Domain Sockets are not supported on this platform or gRPC version.",
    ):
        create_channel(target=target, transport_mode=TransportMode.UDS)


def test_is_uds_supported_returns_expected_value(monkeypatch):
    # arrange
    mock_check_grpc_version = create_autospec(check_grpc_version, return_value=True)
    monkeypatch.setattr(
        "ansys.additive.core.server_connection.network_utils.check_grpc_version",
        mock_check_grpc_version,
    )

    # act
    result = is_uds_supported()

    # assert
    if os.name == "nt":
        mock_check_grpc_version.assert_called()
        assert result is True
    else:
        assert result is True
        mock_check_grpc_version.assert_not_called()


@pytest.mark.parametrize(
    "version_str, expected_tuple",
    [
        ("1.2.3", (1, 2, 3)),
        ("10.20.30", (10, 20, 30)),
        ("0.0.0", (0, 0, 0)),
    ],
)
def test_version_tuple(version_str, expected_tuple):
    # act
    result = version_tuple(version_str)

    # assert
    assert result == expected_tuple


def test_check_grpc_version_returns_expected_value(monkeypatch):
    # arrange
    monkeypatch.setattr(
        "ansys.additive.core.server_connection.network_utils.grpc.__version__",
        "1.63.0",
    )

    # act
    result = check_grpc_version()

    # assert
    assert result is True


def test_check_grpc_version_handles_invalid_version(monkeypatch):
    # arrange
    monkeypatch.setattr(
        "ansys.additive.core.server_connection.network_utils.grpc.__version__",
        "invalid.version.string",
    )

    # act
    result = check_grpc_version()

    # assert
    assert result is False


def test_check_grpc_version_handles_old_version(monkeypatch):
    # arrange
    mock_grpc_version = create_autospec(grpc.__version__, return_value="1.60.0")
    monkeypatch.setattr(
        "ansys.additive.core.server_connection.network_utils.grpc.__version__",
        mock_grpc_version,
    )

    # act
    result = check_grpc_version()

    # assert
    assert result is False
