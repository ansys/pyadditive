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

from __future__ import annotations

import os
from pathlib import Path
import socket

import grpc

from .constants import (
    DEFAULT_UNIX_DOMAIN_SOCKET_LINUX,
    DEFAULT_UNIX_DOMAIN_SOCKET_WINDOWS,
    UNIX_DOMAIN_SOCKET_PREFIX,
    TransportMode,
)

MAX_RCV_MSG_LEN = 256 * 1024**2
_IS_WINDOWS = os.name == "nt"


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


def version_tuple(version_str):
    """Convert a version string into a tuple of integers for comparison."""
    return tuple(int(x) for x in version_str.split("."))


# IMPORTANT: UDS support on Windows requires gRPC version 1.63.0 or higher
def check_grpc_version():
    """Check if the installed gRPC version meets the minimum requirement."""
    min_version = "1.63.0"
    current_version = grpc.__version__

    try:
        return version_tuple(current_version) >= version_tuple(min_version)
    except ValueError:
        print("Warning: Unable to parse gRPC version.")
        return False


def is_uds_supported():
    """Check if Unix Domain Sockets (UDS) are supported on the current platform."""
    is_grpc_version_ok = check_grpc_version()
    return (not _IS_WINDOWS) or (_IS_WINDOWS and is_grpc_version_ok)


def create_channel(
    target: str,
    transport_mode: TransportMode,
    uds_dir: Path | None = None,
    uds_id: str | None = None,
    max_rcv_msg_len: int = MAX_RCV_MSG_LEN,
):
    """Create a gRPC channel with the chosen transport mode.

    Parameters
    ----------
    target: str
        IP address of the host to connect to, of the form ``host:port``.
    transport_mode: TransportMode
        Transport mode to use. Options are given in :class:`TransportMode`.
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

    match transport_mode:
        case TransportMode.INSECURE:
            ip = socket.gethostbyname(host)
            check_valid_ip(ip)
            check_valid_port(int(port_str))
            return grpc.insecure_channel(
                target, options=[("grpc.max_receive_message_length", max_rcv_msg_len)]
            )
        case TransportMode.UDS:
            if not is_uds_supported():
                raise RuntimeError(
                    "Unix Domain Sockets are not supported on this platform or gRPC version."
                )
            if host not in ["localhost", "127.0.0.1"]:
                raise ValueError("UDS transport only supports localhost connections.")
            # Generate socket filename with optional ID
            socket_filename = (
                f"{UNIX_DOMAIN_SOCKET_PREFIX}-{uds_id}.sock"
                if uds_id
                else f"{UNIX_DOMAIN_SOCKET_PREFIX}.sock"
            )
            # Determine UDS directory
            if uds_dir is None:
                uds_dir = (
                    DEFAULT_UNIX_DOMAIN_SOCKET_WINDOWS
                    if _IS_WINDOWS
                    else DEFAULT_UNIX_DOMAIN_SOCKET_LINUX
                )
            uds_target = f"unix:{uds_dir / socket_filename}"

            # If using UDS transport, set default authority to localhost
            # see https://github.com/grpc/grpc/issues/34305
            #
            # This is specially critical when running against a C# server
            options = (
                ("grpc.default_authority", "localhost"),
                ("grpc.max_receive_message_length", max_rcv_msg_len),
            )
            return grpc.insecure_channel(uds_target, options=options)
        case _:
            raise RuntimeError(f"Unsupported transport mode: {transport_mode}")
