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
"""Provides logging and progress."""

import logging
from os import getenv
import sys

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


# Default logging configuration
LOG_LEVEL = logging.DEBUG
FILE_NAME = "pyadditive.log"

# Formatting
STDOUT_MSG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
FILE_MSG_FORMAT = STDOUT_MSG_FORMAT


class PyAdditivePercentStyle(logging.PercentStyle):
    """Provides a common messaging style for the ``PyAdditiveFormatter`` class."""

    def __init__(self, fmt, *, defaults=None):
        """Initialize ``PyGeometryPercentStyle`` class."""
        self._fmt = fmt or self.default_format
        self._defaults = defaults

    def _format(self, record):
        """Format properly the message styles."""
        defaults = self._defaults
        if defaults:
            values = defaults | record.__dict__
        else:
            values = record.__dict__

        # We can make any changes that we want in the record here. For example,
        # adding a key.

        # We could create an ``if`` here if we want conditional formatting, and even
        # change the record.__dict__.
        # Because we don't want to create conditional fields now, it is fine to keep
        # the same MSG_FORMAT for all of them.

        # For the case of logging exceptions to the logger.
        values.setdefault("instance_name", "")

        return STDOUT_MSG_FORMAT % values


class PyAdditiveFormatter(logging.Formatter):
    """Provides a ``Formatter`` class for overwriting default format styles."""

    def __init__(
        self,
        fmt=STDOUT_MSG_FORMAT,
        datefmt=None,
        style="%",
        validate=True,
        defaults=None,
    ):
        """Initialize the ``PyGeometryFormatter`` class."""
        super().__init__(fmt, datefmt, style, validate)
        self._style = PyAdditivePercentStyle(fmt, defaults=defaults)  # overwriting


class Logger:
    """Provides the logger used for each PyAdditive session.

    This class allows you to add handlers to the logger to output messages
    to a file or to the standard output (stdout).

    Parameters
    ----------
    level : int, default: 10
        Logging level to filter the message severity allowed in the logger.
        The default is ``10``, in which case the ``logging.DEBUG`` level
        is used.
    to_file : bool, default: False
        Whether to write log messages to a file.
    to_stdout : bool, default: True
        Whether to write log messages to the standard output.
    filename : str, default: "pyansys-geometry.log"
        Name of the file to write log log messages to.
    """

    file_handler = None
    std_out_handler = None
    _level = logging.DEBUG
    _instances = {}

    def __init__(
        self, level=logging.DEBUG, to_file=False, to_stdout=True, filename=FILE_NAME
    ) -> None:
        """Initialize a ``Logger`` object.

        Parameters
        ----------
        name: str
            Name of the logger.
        """
        # create default main logger
        self.logger = logging.getLogger("PyAdditive_global")
        self.logger.setLevel(level)
        self.logger.propagate = True

        # Writing logging methods.
        self.debug = self.logger.debug
        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.critical = self.logger.critical
        self.log = self.logger.log

        # Using logger to record unhandled exceptions
        self.add_handling_uncaught_expections(self.logger)

        if to_file or filename != FILE_NAME:
            # We record to file
            self.log_to_file(filename=filename, level=level)

        if to_stdout:
            self.log_to_stdout(level=level)

    def log_to_file(self, filename=FILE_NAME, level=LOG_LEVEL):
        """Add a file handler to the logger.

        Parameters
        ----------
        progress: Progress
            Latest progress.
        """

        self = addfile_handler(self, filename=filename, level=level)

    def log_to_stdout(self, level=LOG_LEVEL):
        """Add the standard output handler to the logger.

        Parameters
        ----------
        progress: Progress
            Latest progress.
        """

        self = add_stdout_handler(self, level=level)

    def add_handling_uncaught_expections(self, logger):
        """Redirect the output of an exception to a logger.

        Parameters
        ----------
        logger : str
            Name of the logger.
        """

        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

        sys.excepthook = handle_exception


def addfile_handler(logger, filename=FILE_NAME, level=LOG_LEVEL, write_headers=False):
    """Add a file handler to the input.

    Parameters
    ----------
    logger : logging.Logger
        Logger to add the file handler to.
    filename : str, default: "pyansys-geometry.log"
        Name of the output file.
    level : int, default: 10
        Level of logging. The default is ``10``, in which case the
        ``logging.DEBUG`` level is used.
    write_headers : bool, default: False
        Whether to write the headers to the file.

    Returns
    -------
    Logger
        :class:`Logger` or :class:`logging.Logger` object.
    """
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(FILE_MSG_FORMAT))

    if isinstance(logger, Logger):
        logger.file_handler = file_handler
        logger.logger.addHandler(file_handler)

    elif isinstance(logger, logging.Logger):
        logger.file_handler = file_handler
        logger.addHandler(file_handler)

    return logger


def add_stdout_handler(logger, level=LOG_LEVEL):
    """Add a standout handler to the logger.

    Parameters
    ----------
    logger : logging.Logger
        Logger to add the file handler to.
    level : int, default: 10
        Level of logging. The default is ``10``, in which case the
        ``logging.DEBUG`` level is used.
    write_headers : bool, default: False
        Whether to write headers to the file.

    Returns
    -------
    Logger
        :class:`Logger` or :class:`logging.Logger` object.
    """
    std_out_handler = logging.StreamHandler()
    std_out_handler.setLevel(level)
    std_out_handler.setFormatter(PyAdditiveFormatter(STDOUT_MSG_FORMAT))

    if isinstance(logger, Logger):
        logger.std_out_handler = std_out_handler
        logger.logger.addHandler(std_out_handler)

    elif isinstance(logger, logging.Logger):
        logger.addHandler(std_out_handler)

    return logger


# ===============================================================
# Finally define logger
# ===============================================================

LOG = Logger(level=logging.ERROR, to_file=False, to_stdout=True)
LOG.debug("Loaded logging module as LOG")
