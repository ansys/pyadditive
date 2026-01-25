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
from pathlib import Path
import platform
import shutil
from unittest.mock import create_autospec, patch

import grpc
import pytest

from ansys.additive.core.server_connection.constants import TransportMode
from ansys.additive.core.server_connection.network_utils import (
    MAX_RCV_MSG_LEN,
    check_valid_ip,
    check_valid_port,
    create_channel,
)


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


def test_create_channel_returns_expected_insecure_channel():
    # arrange
    target = "1.2.3.4:1234"

    # act
    channel, _ = create_channel(
        target=target,
        transport_mode="insecure",
        certs_dir=None,
        uds_dir=None,
        uds_id=None,
        allow_remote_host=True,
    )

    # assert
    assert channel is not None
    assert channel._channel.target().decode().removeprefix("dns:///") == target


def test_create_channel_requires_allow_remote_host_for_non_loopback_insecure_channel():
    # arrange
    target = "1.2.3.4:1234"

    # act
    with pytest.raises(ValueError) as exc_info:
        create_channel(
            target=target, transport_mode="insecure", certs_dir=None, uds_dir=None, uds_id=None
        )

    # assert
    assert "Connections to remote hosts are not allowed" in str(exc_info.value)


@pytest.mark.skipif(platform.system() == "Windows", reason="Test only valid on Linux.")
def test_create_channel_returns_expected_uds_channel():
    # arrange
    target = "127.0.0.1:1234"
    uds_dir = Path("test_uds_channel")

    # act
    with patch(
        "ansys.additive.core.server_connection.network_utils.verify_uds_socket", return_value=True
    ):
        channel, uds_file = create_channel(
            target=target, transport_mode="uds", certs_dir=None, uds_dir=uds_dir, uds_id="111111"
        )

    # assert
    assert channel is not None
    assert isinstance(channel, grpc.Channel)
    assert uds_file == Path(uds_dir) / "additive-111111.sock"

    # cleanup
    shutil.rmtree(uds_dir, ignore_errors=True)


@pytest.mark.skipif(platform.system() == "Windows", reason="Test only valid on Linux.")
def test_create_channel_raises_exception_for_missing_uds_dir(monkeypatch):
    # arrange
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=None)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)
    target = "127.0.0.1:1234"
    uds_dir = "test_uds_channel_missing"

    # act and assert
    with pytest.raises(ConnectionError):
        create_channel(
            target=target, transport_mode="uds", certs_dir=None, uds_dir=uds_dir, uds_id="111111"
        )

    # cleanup
    shutil.rmtree(uds_dir, ignore_errors=True)


def test_create_channel_returns_expected_secure_channel(monkeypatch):
    # arrange
    mock_channel_credentials = create_autospec(grpc.ChannelCredentials, return_value=None)
    monkeypatch.setattr(grpc, "ChannelCredentials", mock_channel_credentials)
    mock_secure_channel = create_autospec(grpc.secure_channel, return_value=None)
    monkeypatch.setattr(grpc, "secure_channel", mock_secure_channel)
    target = "127.0.0.1:1234"
    certs_dir = Path("test_secure_channel")
    certs_dir.mkdir(parents=True, exist_ok=True)
    (certs_dir / "client.crt").write_text("test")
    (certs_dir / "client.key").write_text("test")
    (certs_dir / "ca.crt").write_text("test")

    # act
    create_channel(
        target=target,
        transport_mode=TransportMode.MTLS,
        certs_dir=certs_dir,
        uds_dir=None,
        uds_id=None,
    )

    # assert
    mock_secure_channel.assert_called_with(
        target, None, options=[("grpc.max_receive_message_length", MAX_RCV_MSG_LEN)]
    )

    # cleanup
    shutil.rmtree(certs_dir, ignore_errors=True)


def test_create_channel_raises_exception_for_missing_certs():
    # arrange
    target = "1.2.3.4:1234"

    # act, assert
    with pytest.raises(FileNotFoundError):
        create_channel(
            target=target,
            transport_mode=TransportMode.MTLS,
            certs_dir=None,
            uds_dir=None,
            uds_id=None,
        )


def test_create_channel_raises_exception_for_invalid_transport_mode():
    # arrange
    target = "1.2.3.4:1234"

    # act, assert
    with pytest.raises(ValueError):
        create_channel(
            target=target, transport_mode="invalid", certs_dir=None, uds_dir=None, uds_id=None
        )


def test_create_channel_raises_exception_for_missing_ip():
    # arrange
    target = ":1234"

    # act, assert
    with pytest.raises(ValueError):
        create_channel(target, transport_mode="insecure", certs_dir=None, uds_dir=None, uds_id=None)


def test_create_channel_raises_exception_for_bad_port():
    # arrange
    target = "1.2.3.4:123"

    # act, assert
    with pytest.raises(ValueError):
        create_channel(target, transport_mode="insecure", certs_dir=None, uds_dir=None, uds_id=None)


def test_create_channel_sets_max_rcv_msg_len(monkeypatch):
    # arrange
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=None)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)
    msg_len = 8 * 1024**2
    target = "1.2.3.4:1234"

    # act
    create_channel(
        target,
        transport_mode="insecure",
        certs_dir=None,
        uds_dir=None,
        uds_id=None,
        allow_remote_host=True,
        max_rcv_msg_len=msg_len,
    )

    # assert
    mock_insecure_channel.assert_called_with(
        target, options=[("grpc.max_receive_message_length", msg_len)]
    )
