# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
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
"""Provides logging and progress."""

import logging
from os import getenv

from ansys.api.additive.v0.additive_domain_pb2 import Progress, ProgressState
from tqdm import tqdm


class ProgressLogger:
    """Provides for logging and progress reporting."""

    def __init__(self, name: str = None) -> None:
        """Initialize a ``ProgressLogger`` object.

        Parameters
        ----------
        name: str
            Name of the logger.
        """
        self._log = logging.getLogger(name)
        self._last_percent_complete = 0
        self._last_context = "Initializing"

    def log_progress(self, progress: Progress):
        """Report progress and possibly emit a log message.

        Parameters
        ----------
        progress: Progress
            Latest progress.
        """
        if getenv("GENERATING_DOCS"):
            # Don't send  progress when generating docs
            return
        if not hasattr(self, "_pbar"):
            self._pbar = tqdm(total=100, colour="green", desc=self._last_context, mininterval=0.001)

        if progress.message and "SOLVERINFO" in progress.message:
            self._log.debug(progress.message)
            return

        if progress.state == ProgressState.PROGRESS_STATE_ERROR:
            self._pbar.write(progress.message)
            return

        if progress.context and progress.context != self._last_context:
            if "Solving Layer" not in progress.context or progress.context == "Solving Layer 1":
                self._pbar.reset(total=100)
                self._pbar.set_description(progress.context)
                self._last_context = progress.context
                self._last_percent_complete = 0
            else:
                self._pbar.set_description(progress.context, refresh=False)

        if progress.percent_complete - self._last_percent_complete > 0:
            self._pbar.update(progress.percent_complete - self._last_percent_complete)
        self._last_percent_complete = progress.percent_complete

    def __del__(self):
        if hasattr(self, "_pbar"):
            self._pbar.close()
