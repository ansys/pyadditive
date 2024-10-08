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
"""Unit conversion constants and functions."""

MM_TO_METER = 0.001
METER_TO_MM = 1000


def celsius_to_kelvin(celsius: float) -> float:
    """Convert celsius to kelvin.

    Parameters
    ----------
    celsius: float
        Degrees celsius.

    Returns
    -------
    float
        Equivalent degrees in kelvin.

    """
    return celsius + 273.15


def kelvin_to_celsius(kelvin):
    """Convert degrees kelvin to celsius.

    Parameters
    ----------
    kelvin: float
        Degrees kelvin.

    Returns
    -------
    float
        Equivalent degrees in celsius.

    """
    return kelvin - 273.15
