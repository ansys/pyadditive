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
"""Set up methods for grpc simulation requests."""

from collections.abc import Iterator
import hashlib
import os

from ansys.api.additive.v0.additive_simulation_pb2 import SimulationRequest, UploadFileRequest

from ansys.additive.core.microstructure import MicrostructureInput
from ansys.additive.core.microstructure_3d import Microstructure3DInput
from ansys.additive.core.porosity import PorosityInput
from ansys.additive.core.progress_handler import IProgressHandler, Progress, ProgressState
from ansys.additive.core.server_connection import ServerConnection
from ansys.additive.core.single_bead import SingleBeadInput
from ansys.additive.core.thermal_history import ThermalHistoryInput


def __file_upload_reader(file_name: str, chunk_size=2 * 1024**2) -> Iterator[UploadFileRequest]:
    """Read a file and return an iterator of UploadFileRequests."""
    file_size = os.path.getsize(file_name)
    short_name = os.path.basename(file_name)
    with open(file_name, mode="rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield UploadFileRequest(
                name=short_name,
                total_size=file_size,
                content=chunk,
                content_md5=hashlib.md5(chunk).hexdigest(),
            )


def _setup_thermal_history(
    input: ThermalHistoryInput,
    server: ServerConnection,
    progress_handler: IProgressHandler | None = None,
) -> SimulationRequest:
    """Setup a thermal history simulation.

    Parameters
    ----------
    input: ThermalHistoryInput
        Simulation input parameters.
    server: ServerConnection
        Server to use for the simulation.
    progress_handler: IProgressHandler, None, default: None
        Handler for progress updates. If ``None``, no progress updates are provided.

    Returns
    -------
    :class:`SimulationRequest`
    """
    if not input.geometry or not input.geometry.path:
        raise ValueError("The geometry path is not defined in the simulation input")

    remote_geometry_path = ""
    for response in server.simulation_stub.UploadFile(__file_upload_reader(input.geometry.path)):
        remote_geometry_path = response.remote_file_name
        progress = Progress.from_proto_msg(input.id, response.progress)
        if progress_handler:
            progress_handler.update(progress)
        if progress.state == ProgressState.ERROR:
            raise Exception(progress.message)

    return input._to_simulation_request(remote_geometry_path=remote_geometry_path)


def _create_request(
    simulation_input: (
        SingleBeadInput
        | PorosityInput
        | MicrostructureInput
        | ThermalHistoryInput
        | Microstructure3DInput
    ),
    server: ServerConnection,
    progress_handler: IProgressHandler | None = None,
) -> SimulationRequest:
    """Create a simulation request and set up any pre-requisites on a server, such as an STL file for a
    thermal history simulation.

    Parameters
    ----------
    simulation_input: SingleBeadInput, PorosityInput, MicrostructureInput, ThermalHistoryInput,
    Microstructure3DInput
        Parameters to use for simulation.
    server: ServerConnection
        Server to use for the simulation.
    progress_handler: IProgressHandler, None, default: None
        Handler for progress updates. If ``None``, no progress updates are provided.

    Returns
    -------
    A SimulationRequest
    """
    if isinstance(simulation_input, ThermalHistoryInput):
        request = _setup_thermal_history(simulation_input, server, progress_handler)
    else:
        request = simulation_input._to_simulation_request()

    return request
