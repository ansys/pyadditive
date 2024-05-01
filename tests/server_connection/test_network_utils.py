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
from unittest.mock import create_autospec

import grpc
import pytest

from ansys.additive.core.server_connection.network_utils import (
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


def test_create_channel_returns_expected_channel():
    # arrange
    target = "1.2.3.4:1234"

    # act
    channel = create_channel(target=target)

    # assert
    assert channel is not None
    assert channel._channel.target().decode().removeprefix("dns:///") == target


def test_create_channel_raises_exception_for_missing_ip():
    # arrange
    target = ":1234"

    # act, assert
    with pytest.raises(ValueError):
        create_channel(target)


def test_create_channel_raises_exception_for_bad_port():
    # arrange
    target = "1.2.3.4:123"

    # act, assert
    with pytest.raises(ValueError):
        create_channel(target)


def test_create_channel_sets_max_rcv_msg_len(monkeypatch):
    # arrange
    mock_insecure_channel = create_autospec(grpc.insecure_channel, return_value=None)
    monkeypatch.setattr(grpc, "insecure_channel", mock_insecure_channel)
    msg_len = 8 * 1024**2
    target = "1.2.3.4:1234"

    # act
    create_channel(target, msg_len)

    # assert
    mock_insecure_channel.assert_called_with(
        target, options=[("grpc.max_receive_message_length", msg_len)]
    )
