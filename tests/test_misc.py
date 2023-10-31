# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
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

import pytest

from ansys.additive.core import misc


def test_valid_ip_returns_without_error_for_valid_values():
    # arrange, act, assert
    misc.check_valid_ip("1.2.3.4")
    misc.check_valid_ip("127.0.0.1")
    misc.check_valid_ip("8.8.8.8")
    misc.check_valid_ip("localhost")


def test_valid_ip_raises_error_for_invalid_values():
    # arrange, act, assert
    with pytest.raises(OSError):
        misc.check_valid_ip("google.com")
    with pytest.raises(OSError):
        misc.check_valid_ip("")


def test_check_valid_port_returns_without_error_for_valid_values():
    # arrange, act, assert
    misc.check_valid_port(1001)
    misc.check_valid_port(59999)
    misc.check_valid_port("1001")
    misc.check_valid_port("1", 0, 2)


def test_check_valid_port_raises_error_for_invalid_values():
    # arrange, act, assert
    with pytest.raises(ValueError):
        misc.check_valid_port(1000)
    with pytest.raises(ValueError):
        misc.check_valid_port(60000)
    with pytest.raises(ValueError):
        misc.check_valid_port("1000")
    with pytest.raises(ValueError):
        misc.check_valid_port("0", 0, 2)


def test_short_uuid_returns_string_of_expected_length():
    # arrange, act
    result = misc.short_uuid()

    # assert
    assert isinstance(result, str)
    assert len(result) == 8
