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

from typing import Optional


def build_rate(
    scan_speed: float, layer_thickness: float, hatch_spacing: Optional[float] = None
) -> float:
    """Calculate the build rate.

    This is an approximate value useful for comparison but not for an accurate prediction
    of build time. The returned value is simply the product of the scan speed, layer thickness,
    and hatch spacing (if provided).

    Parameters
    ----------
    scan_speed : float
        Laser scan speed.
    layer_thickness : float
        Powder deposit layer thickness.
    hatch_spacing : float, None
        Distance between hatch scan lines.

    Returns
    -------
    float
        Volumetric build rate is returned if hatch spacing is provided.
        Otherwise, an area build rate is returned. If input units are m/s and m,
        the output units are m^3/s or m^2/s.
    """
    if hatch_spacing is None:
        return scan_speed * layer_thickness
    return scan_speed * layer_thickness * hatch_spacing


def energy_density(
    laser_power: float,
    scan_speed: float,
    layer_thickness: float,
    hatch_spacing: Optional[float] = None,
) -> float:
    """Calculate the energy density.

    This is an approximate value useful for comparison. The returned value is simply
    the laser power divided by the build rate. For more information, see the :meth:`build_rate`
    method.

    Parameters
    ----------
    laser_power : float
        Laser power.
    scan_speed : float
        Laser scan speed.
    layer_thickness : float
        Powder deposit layer thickness.
    hatch_spacing : float, None
        Distance between hatch scan lines.

    Returns
    -------
    float
        Volumetric energy density is returned i hatch spacing is provided.
        Otherwise an area energy density is returned. If input units are W, m/s, m, or m,
        the output units are J/m^3 or J/m^2.
    """
    br = build_rate(scan_speed, layer_thickness, hatch_spacing)
    return laser_power / br if br else float("nan")
