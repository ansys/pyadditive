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
"""Provides network connection utility functions."""

import socket

import grpc

MAX_RCV_MSG_LEN = 256 * 1024**2


def check_valid_ip(ip):
    """Check for valid IP address."""
    if ip.lower() != "localhost":
        ip = ip.replace('"', "").replace("'", "")
        socket.inet_aton(ip)


def check_valid_port(port, lower_bound=1024, high_bound=65535):
    """Check for valid port number."""
    _port = int(port)

    if lower_bound <= _port <= high_bound:
        return
    else:
        raise ValueError(f"'port' value outside of range {lower_bound} to {high_bound}.")


def create_channel(target: str, max_rcv_msg_len: int = MAX_RCV_MSG_LEN):
    """Create an insecure gRPC channel.

    Parameters
    ----------
    target: str
        IP address of the host to connect to, of the form ``host:port``.
    max_rcv_msg_len: int
        Size, in bytes, of the buffer used to receive messages. Default is
        :obj:`MAX_RCV_MSG_LEN`.

    Returns
    -------
    channel: grpc.Channel
        Insecure gRPC channel.

    """

    (host, port_str) = target.split(":")
    if not host:
        raise ValueError(
            f"Improperly formed target string {target}, it should be of the form 'host:port'"
        )
    ip = socket.gethostbyname(host)
    check_valid_ip(ip)
    check_valid_port(int(port_str))

    return grpc.insecure_channel(
        target, options=[("grpc.max_receive_message_length", max_rcv_msg_len)]
    )
