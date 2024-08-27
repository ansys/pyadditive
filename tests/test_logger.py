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

import datetime
import logging as deflogging  # Default logging

import pytest

from ansys.additive.core import LOG  # Global logger

LOG_LEVELS = {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10}


@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    # setup code
    default_level = LOG.logger.level
    yield
    # teardown code
    LOG.logger.setLevel(default_level)
    for handler in LOG.logger.handlers:
        handler.setLevel(default_level)


def test_global_logger_exists():
    assert isinstance(LOG.logger, deflogging.Logger)
    assert LOG.logger.name == "PyAdditive_global"


def test_global_logger_has_only_stdout_handler_enabled_by_default():
    assert hasattr(LOG, "file_handler")
    assert hasattr(LOG, "stdout_handler")
    assert LOG.logger.hasHandlers
    assert not LOG.file_handler
    assert LOG.stdout_handler


def test_global_logger_logging_with_level_debug(caplog: pytest.LogCaptureFixture):
    LOG.logger.setLevel("DEBUG")
    LOG.stdout_handler.setLevel("DEBUG")
    for each_log_name, each_log_number in LOG_LEVELS.items():
        msg = f"This is an {each_log_name} message."
        LOG.logger.log(each_log_number, msg)
        # Make sure we are using the right logger, the right level and message.
        assert caplog.record_tuples[-1] == ("PyAdditive_global", each_log_number, msg)


def test_global_logger_level_mode():
    """Checking that the Logger levels are stored as integer values and that the default
    value is WARNING.

    Update test if default value is changed.
    """
    assert isinstance(LOG.logger.level, int)
    assert LOG.logger.level == LOG_LEVELS["WARNING"]


@pytest.mark.parametrize(
    "level",
    [
        deflogging.DEBUG,
        deflogging.INFO,
        deflogging.WARN,
        deflogging.ERROR,
        deflogging.CRITICAL,
    ],
)
def test_global_logger_debug_levels(level: int, caplog: pytest.LogCaptureFixture):
    with caplog.at_level(level, LOG.logger.name):  # changing root logger level:
        for each_log_name, each_log_number in LOG_LEVELS.items():
            msg = f"This is a message of type {each_log_name}."
            LOG.logger.log(each_log_number, msg)
            # Make sure we are using the right logger, the right level and message.
            if each_log_number >= level:
                assert caplog.record_tuples[-1] == (
                    "PyAdditive_global",
                    each_log_number,
                    msg,
                )
            else:
                assert caplog.record_tuples[-1] != (
                    "PyAdditive_global",
                    each_log_number,
                    msg,
                )


@pytest.mark.parametrize(
    "level",
    [
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ],
)
def test_setLevel_sets_log_level(level: str):
    assert LOG.logger.level == LOG_LEVELS["WARNING"]

    # act
    LOG.setLevel(level)

    # assert
    assert LOG.logger.level == LOG_LEVELS[level]
    for handler in LOG.logger.handlers:
        assert handler.level == LOG_LEVELS[level]


def test_global_logger_log_to_file(tmp_path_factory: pytest.TempPathFactory):
    file_path = tmp_path_factory.mktemp("log_files") / "instance.log"
    file_msg_error = "This is a error message"
    file_msg_debug = "This is a debug message"

    # The LOG loglevel is changed in previous test,
    # hence making sure now it is the "default" one.
    LOG.logger.setLevel("ERROR")
    LOG.stdout_handler.setLevel("ERROR")

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
