# Copyright (C) 2024 ANSYS, Inc. and/or its affiliates.
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

import datetime
import logging as deflogging  # Default logging

import pytest

from ansys.additive.core import LOG  # Global logger
import ansys.additive.core.progress_logger as logger

LOG_LEVELS = {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10}


def test_global_logger_exist():
    """Test for checking the accurate naming of the general Logger instance."""

    assert isinstance(LOG.logger, deflogging.Logger)
    assert LOG.logger.name == "PyAdditive_global"


def test_global_logger_has_handlers():
    """Test for checking that the general Logger has file_handlers and sdtout
    file_handlers implemented."""

    assert hasattr(LOG, "file_handler")
    assert hasattr(LOG, "std_out_handler")
    assert LOG.logger.hasHandlers
    assert LOG.file_handler or LOG.std_out_handler


def test_global_logger_logging(caplog: pytest.LogCaptureFixture):
    """Testing the global PyAdditive logger capabilities. Forcing minimum logging level to
    Debug, adding a message with different logging levels, checking the output and
    restoring to original level.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        Fixture for capturing logs.
    """
    LOG.logger.setLevel("DEBUG")
    LOG.std_out_handler.setLevel("DEBUG")
    for each_log_name, each_log_number in LOG_LEVELS.items():
        msg = f"This is an {each_log_name} message."
        LOG.logger.log(each_log_number, msg)
        # Make sure we are using the right logger, the right level and message.
        assert caplog.record_tuples[-1] == ("PyAdditive_global", each_log_number, msg)

    #  Set back to default level == ERROR
    LOG.logger.setLevel("ERROR")
    LOG.std_out_handler.setLevel("ERROR")


def test_global_logger_level_mode():
    """Checking that the Logger levels are stored as integer values and that the default
    value (unless changed) is ERROR."""
    assert isinstance(LOG.logger.level, int)
    assert LOG.logger.level == logger.logging.ERROR


def test_global_methods_with_log_level_debug(caplog: pytest.LogCaptureFixture):
    """Testing global logger methods for printing out different log messages, from DEBUG to
    CRITICAL.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        Fixture for capturing logs.
    """
    LOG.logger.setLevel("DEBUG")
    LOG.std_out_handler.setLevel("DEBUG")

    msg = f"This is a debug message"
    LOG.debug(msg)
    assert msg in caplog.text
    assert "DEBUG" in caplog.text

    msg = f"This is an info message"
    LOG.info(msg)
    assert msg in caplog.text
    assert "INFO" in caplog.text

    msg = f"This is a warning message"
    LOG.warning(msg)
    assert msg in caplog.text
    assert "WARNING" in caplog.text

    msg = f"This is an error message"
    LOG.error(msg)
    assert msg in caplog.text
    assert "ERROR" in caplog.text

    msg = f"This is a critical message"
    LOG.critical(msg)
    assert msg in caplog.text
    assert "CRITICAL" in caplog.text

    msg = f'This is a 30 message using "log"'
    LOG.log(30, msg)
    assert msg in caplog.text

    #  Set back to default level == ERROR
    LOG.logger.setLevel("ERROR")
    LOG.std_out_handler.setLevel("ERROR")


def test_global_methods_with_log_level_warning(caplog: pytest.LogCaptureFixture):
    """Testing global logger methods for printing out different log messages, from DEBUG to
    CRITICAL.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        Fixture for capturing logs.
    """
    LOG.logger.setLevel("WARNING")
    LOG.std_out_handler.setLevel("WARNING")

    msg = f"This is a debug message"
    LOG.debug(msg)
    assert msg not in caplog.text

    msg = f"This is an info message"
    LOG.info(msg)
    assert msg not in caplog.text

    msg = f"This is a warning message"
    LOG.warning(msg)
    assert msg in caplog.text

    msg = f"This is an error message"
    LOG.error(msg)
    assert msg in caplog.text

    msg = f"This is a critical message"
    LOG.critical(msg)
    assert msg in caplog.text

    msg = f'This is a 30 message using "log"'
    LOG.log(30, msg)
    assert msg in caplog.text

    #  Set back to default level == ERROR
    LOG.logger.setLevel("ERROR")
    LOG.std_out_handler.setLevel("ERROR")


def test_global_methods_with_log_level_critical(caplog: pytest.LogCaptureFixture):
    """Testing global logger methods for printing out different log messages, from DEBUG to
    CRITICAL.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        Fixture for capturing logs.
    """
    LOG.logger.setLevel("CRITICAL")
    LOG.std_out_handler.setLevel("CRITICAL")

    msg = f"This is a debug message"
    LOG.debug(msg)
    assert msg not in caplog.text

    msg = f"This is an info message"
    LOG.info(msg)
    assert msg not in caplog.text

    msg = f"This is a warning message"
    LOG.warning(msg)
    assert msg not in caplog.text

    msg = f"This is an error message"
    LOG.error(msg)
    assert msg not in caplog.text

    msg = f"This is a critical message"
    LOG.critical(msg)
    assert msg in caplog.text

    msg = f'This is a 30 message using "log"'
    LOG.log(30, msg)
    assert msg not in caplog.text

    #  Set back to default level == ERROR
    LOG.logger.setLevel("ERROR")
    LOG.std_out_handler.setLevel("ERROR")


def test_log_to_file(tmp_path_factory: pytest.TempPathFactory):
    """Testing writing to log file.

    Since the default loglevel of LOG is error, debug are not normally recorded to it.

    Parameters
    ----------
    tmp_path_factory  : pytest.TempdirFactory
        Fixture for accessing a temporal directory (erased after test execution).
    """
    file_path = tmp_path_factory.mktemp("log_files") / "instance.log"
    file_msg_error = "This is a error message"
    file_msg_debug = "This is a debug message"

    # The LOG loglevel is changed in previous test,
    # hence making sure now it is the "default" one.
    LOG.logger.setLevel("ERROR")
    LOG.std_out_handler.setLevel("ERROR")

    if not LOG.file_handler:
        LOG.log_to_file(file_path)

    LOG.error(file_msg_error)
    LOG.debug(file_msg_debug)

    with open(file_path, "r") as fid:
        text = "".join(fid.readlines())
    timestamp = text[0:23]

    assert file_msg_error in text
    assert file_msg_debug not in text
    assert "ERROR" in text
    assert "DEBUG" not in text
    format = "%Y-%m-%d %H:%M:%S,%f"
    assert datetime.datetime.strptime(timestamp, format)
