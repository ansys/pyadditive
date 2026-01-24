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

import ipaddress
from pathlib import Path
import socket

from ansys.tools.common.cyberchannel import create_channel as create_cyber_channel
from ansys.tools.common.cyberchannel import verify_uds_socket

from .constants import UNIX_DOMAIN_SOCKET_SERVICE_NAME, TransportMode

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


def is_loopback(ip):
    """Check if the IP address is a loopback address."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_loopback
    except ValueError:
        return False  # Invalid IP address


def create_channel(
    target: str,
    transport_mode: TransportMode | str,
    certs_dir: Path | str | None,
    uds_dir: Path | str | None,
    uds_id: str | None,
    allow_remote_host: bool = False,
    max_rcv_msg_len: int = MAX_RCV_MSG_LEN,
):
    """Create a gRPC channel.

    Parameters
    ----------
    target: str
        IP address of the host to connect to, of the form ``host:port``.
    transport_mode : TransportMode | str
        The transport mode to use for the connection. Can be a member of the :class:`TransportMode
        <.constants.TransportMode>` enum or a string
        ('insecure', 'mtls', or 'uds').
    certs_dir : Path | str | None
        Directory containing certificates for mTLS connections. Required if `transport_mode` is 'mtls'.
    uds_dir : Path | str | None
        Directory containing Unix Domain Socket files. Required if `transport_mode` is 'uds'.
    uds_id : str | None
        Identifier for the Unix Domain Socket. Required if `transport_mode` is 'uds'.
    allow_remote_host: bool
        Whether to allow connections to remote hosts when using 'insecure' or 'mtls' transport modes.
    max_rcv_msg_len: int
        Size, in bytes, of the buffer used to receive messages. Default is :obj:`MAX_RCV_MSG_LEN`.
    Raises
    ------
    ValueError
        If the target string is improperly formed, the transport mode is invalid, or an unsupported
        transport mode is specified.
    ConnectionError
        If unable to connect to the Unix Domain Socket when using 'uds' transport mode.
    Returns
    -------
    channel: grpc.Channel
        Insecure or secure gRPC channel, depending on the transport mode.
    uds_file: Path | None
        Path to the Unix Domain Socket file if using 'uds' transport mode, otherwise None.
    """

    (host, port_str) = target.split(":")
    if not host:
        raise ValueError(
            f"Improperly formed target string {target}, it should be of the form 'host:port'"
        )
    ip = socket.gethostbyname(host)
    check_valid_ip(ip)
    check_valid_port(int(port_str))

    if isinstance(transport_mode, str):
        try:
            transport_mode = TransportMode[transport_mode.upper()]
        except KeyError as exc:
            raise ValueError(f"Invalid transport mode string: {transport_mode}") from exc

    match transport_mode:
        case TransportMode.INSECURE:
            if not allow_remote_host and not is_loopback(ip):
                raise ValueError(
                    "Connections to remote hosts are not allowed. Set 'allow_remote_host=True' to override."
                )
            return (
                create_cyber_channel(
                    transport_mode="insecure",
                    host=host,
                    port=port_str,
                    grpc_options=[("grpc.max_receive_message_length", max_rcv_msg_len)],
                ),
                None,
            )

        case TransportMode.MTLS:
            return (
                create_cyber_channel(
                    transport_mode="mtls",
                    host=host,
                    port=port_str,
                    certs_dir=certs_dir,
                    grpc_options=[("grpc.max_receive_message_length", max_rcv_msg_len)],
                ),
                None,
            )

        case TransportMode.UDS:
            uds_service = UNIX_DOMAIN_SOCKET_SERVICE_NAME
            uds_channel = create_cyber_channel(
                transport_mode="uds",
                uds_service=uds_service,
                uds_dir=uds_dir,
                uds_id=uds_id,
                grpc_options=[("grpc.max_receive_message_length", max_rcv_msg_len)],
            )
            # small bug in verify_uds_socket: needs Path or None, not str
            uds_folder = (
                uds_dir
                if isinstance(uds_dir, Path)
                else (Path(uds_dir) if isinstance(uds_dir, str) else None)
            )
            if not verify_uds_socket(uds_service, uds_folder, uds_id):
                raise ConnectionError(
                    f"Could not connect to UDS socket in {uds_folder or 'None'} with id "
                    f"{uds_id or 'None'}."
                )

            return uds_channel, Path(uds_channel._channel.target().decode().removeprefix("unix:"))
        case _:
            raise ValueError(f"Unsupported transport mode: {transport_mode}")
