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
"""Provides a class to update progress when running parametric study simulations."""

import tempfile
import threading

from ansys.api.additive.v0.additive_simulation_pb2 import SimulationResponse
from google.longrunning.operations_pb2 import GetOperationRequest

from ansys.additive.core import LOG, Additive
from ansys.additive.core.microstructure import Microstructure2DResult
from ansys.additive.core.parametric_study import ParametricStudy
from ansys.additive.core.progress_handler import IProgressHandler, Progress, ProgressState
from ansys.additive.core.simulation import SimulationStatus
from ansys.additive.core.single_bead import MeltPool


class ParametricStudyProgressHandler(IProgressHandler):
    """Provides methods to update parametric study simulation status.

    Parameters
    ----------
    study : ParametricStudy
        Parametric study to update.
    additive : Additive
        Additive service connection to use for updating progress.
    """

    def __init__(
        self,
        study: ParametricStudy,
        additive: Additive,
    ) -> None:
        """Initialize progress handler."""

        self._study_lock = threading.Lock()
        self._study = study
        self._additive = additive
        # Store the last state of each simulation to avoid
        # unnecessary disk writes when setting the simulation status
        # on the study.
        self._last_progress_states = {}

    def update(self, progress: Progress) -> None:
        """Update the progress of a simulation.

        Parameters
        ----------
        progress : Progress
            Progress information for the simulation.
        """
        if (
            progress.sim_id in self._last_progress_states
            and progress.state == self._last_progress_states[progress.sim_id]
        ):
            return

        LOG.debug(f"Updating progress for {progress.sim_id}")

        if progress.state == ProgressState.WAITING:
            self._update_simulation_status(progress.sim_id, SimulationStatus.PENDING)
        elif progress.state == ProgressState.CANCELLED:
            self._update_simulation_status(progress.sim_id, SimulationStatus.CANCELLED)
        elif progress.state == ProgressState.RUNNING:
            self._update_simulation_status(progress.sim_id, SimulationStatus.RUNNING)
        elif progress.state == ProgressState.WARNING:
            self._update_simulation_status(progress.sim_id, SimulationStatus.WARNING)
        elif progress.state == ProgressState.ERROR:
            self._update_simulation_status(
                progress.sim_id, SimulationStatus.ERROR, progress.message
            )
        elif progress.state == ProgressState.COMPLETED:
            self._update_simulation_results(progress.sim_id)
            self._update_simulation_status(progress.sim_id, SimulationStatus.COMPLETED)

        self._last_progress_states[progress.sim_id] = progress.state

    def _update_simulation_status(
        self, sim_id: str, status: SimulationStatus, message: str = None
    ) -> None:
        """Update the status of a simulation.

        Parameters
        ----------
        sim_id : str
            Simulation ID.
        status : SimulationStatus
            Simulation status.
        message : str, optional
            Status message.
        """

        with self._study_lock:
            self._study.set_simulation_status(sim_id, status, message)

    def _update_simulation_results(self, sim_id: str) -> None:
        """Update the results of a completed simulation.

        Parameters
        ----------
        sim_id : str
            Simulation ID.
        """

        get_request = GetOperationRequest(name=sim_id)
        op = None
        for server in self._additive._servers:
            try:
                op = server.operations_stub.GetOperation(get_request)
                if op:
                    break
            except Exception as e:
                LOG.debug(f"Failed to find {sim_id} on {server.channel_str}: {e}")
                continue

        if op and op.HasField("response"):
            warning = False
            response = SimulationResponse()
            op.response.Unpack(response)
            if response.HasField("melt_pool"):
                # convert melt pool message to MeltPool object
                melt_pool = MeltPool(response.melt_pool)
                self._study._update_single_bead(sim_id, melt_pool)
            elif response.HasField("porosity_result"):
                self._study._update_porosity(sim_id, response.porosity_result.solid_ratio)
            elif response.HasField("microstructure_result"):
                result = Microstructure2DResult(
                    response.microstructure_result, tempfile.TemporaryDirectory().name
                )
                self._study._update_microstructure(
                    sim_id,
                    result.xy_average_grain_size,
                    result.xz_average_grain_size,
                    result.yz_average_grain_size,
                )
            else:
                warning = True

            if warning:
                LOG.warning(f"Unknown results for {sim_id}")
            else:
                LOG.info(f"Updated results for {sim_id}")
        else:
            LOG.warning(f"Failed to find results for {sim_id}")
