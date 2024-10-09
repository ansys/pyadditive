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
"""Provides a general framework for logging in PyAdditive.

Logger usage
------------

Global logger
~~~~~~~~~~~~~
There is a global logger named ``PyAdditive_global`` that is created when
``ansys.additive.core.__init__`` is called. If you want to use this global
logger, you must call it at the top of your module:

.. code:: python

   from ansys.additive.core import LOG

You can rename this logger to avoid conflicts with other loggers (if any):

.. code:: python

   from ansys.additive.core import LOG as logger

The default logging level of ``LOG`` is ``WARNING``.
You can change this level and output lower-level messages with
this code:

.. code:: python

   LOG.logger.setLevel("DEBUG")
   LOG.file_handler.setLevel("DEBUG")  # If present.
   LOG.stdout_handler.setLevel("DEBUG")  # If present.

Alternatively, you can ensure that all the handlers are set to the input log
level with this code:

.. code:: python

   LOG.setLevel("DEBUG")

This logger does not log to a file by default. If you want, you can
add a file handler with this code:

.. code:: python

   import os

   file_path = os.path.join(os.getcwd(), "pyadditive.log")
   LOG.log_to_file(file_path)
"""

import logging
import sys

from IPython import get_ipython

# Default logging configuration
LOG_LEVEL = logging.DEBUG
FILE_NAME = "pyadditive.log"

# Formatting
STDOUT_MSG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
FILE_MSG_FORMAT = STDOUT_MSG_FORMAT
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def is_notebook() -> bool:
    """Check if the code is running in a Jupyter notebook.

    Returns:
        bool: True if running in a Jupyter notebook, False otherwise.

    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True
        elif shell == "TerminalInteractiveShell":
            return False
        else:
            return False
    except NameError:
        return False


class PyAdditivePercentStyle(logging.PercentStyle):
    """Provides a common messaging style for the ``PyAdditiveFormatter`` class."""

    def __init__(self, fmt, *, defaults=None):
        """Initialize ``PyAdditivePercentStyle`` class."""
        self._fmt = fmt or self.default_format
        self._defaults = defaults

    def _format(self, record):
        """Append specifiers to the log message format."""
        defaults = self._defaults
        values = defaults | record.__dict__ if defaults else record.__dict__

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
        """Initialize the ``PyAdditiveFormatter`` class."""
        super().__init__(fmt, datefmt, style, validate)
        self._style = PyAdditivePercentStyle(fmt, defaults=defaults)  # overwriting


class Logger:
    """Provides the logger used for each PyAdditive session.

    This class allows you to add handlers to the logger to output messages
    to a file or to the standard output (stdout).

    Parameters
    ----------
    level : default : DEBUG
        Logging level to filter the message severity allowed in the logger.
    to_file : bool, default: False
        Whether to write log messages to a file.
    to_stdout : bool, default: True
        Whether to write log messages to the standard output.
    filename : str, default: obj:`FILE_NAME`
        Name of the file to write log log messages to.

    """

    file_handler = None
    stdout_handler = None
    _level = logging.DEBUG
    _instances = {}

    def __init__(
        self, level=logging.DEBUG, to_file=False, to_stdout=True, filename=FILE_NAME
    ) -> None:
        """Initialize a ``Logger`` object."""

        if is_notebook():
            level = logging.INFO

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
        filename : str, default: obj:`FILE_NAME`
            Name of the file to write log messages to.
        level : default : DEBUG
            Logging level to filter the message severity allowed in the logger.

        """

        self = addfile_handler(self, filename=filename, level=level)

    def log_to_stdout(self, level=LOG_LEVEL):
        """Add the standard output handler to the logger.

        Parameters
        ----------
        level : default : DEBUG
            Logging level to filter the message severity allowed in the logger.

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

    def setLevel(self, level: str | int) -> None:
        """Set the logging level for the logger.

        Parameters
        ----------
        level : str or int
            Logging level to filter the message severity allowed in the logger.
            If int, it must be one of the levels defined in the :obj:`~logging` module.
            Valid string values are ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``,
            and ``"CRITICAL"``.

        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)


def addfile_handler(logger, filename=FILE_NAME, level=LOG_LEVEL):
    """Add a file handler to the input.

    Parameters
    ----------
    logger : logging.Logger
        Logger to add the file handler to.
    filename : str, default: obj:`FILE_NAME`
        Name of the output file.
    level : default : DEBUG
        Logging level to filter the message severity allowed in the logger.

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
    level : default : DEBUG
        Logging level to filter the message severity allowed in the logger.

    Returns
    -------
    Logger
        :class:`Logger` or :class:`logging.Logger` object.

    """
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(PyAdditiveFormatter(STDOUT_MSG_FORMAT, DATE_FORMAT))

    if isinstance(logger, Logger):
        logger.stdout_handler = stdout_handler
        logger.logger.addHandler(stdout_handler)

    elif isinstance(logger, logging.Logger):
        logger.addHandler(stdout_handler)

    return logger


# ===============================================================
# Finally define logger
# ===============================================================

LOG = Logger(level=logging.WARNING, to_file=False, to_stdout=True)
