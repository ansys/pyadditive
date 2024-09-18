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
"""Provides constant values related to parametric studies."""


class ColumnNames:
    """Provides column names for the parametric study data frame.

    Values are stored internally as a :class:`Pandas DataFrame <pandas.DataFrame>`.
    Column name definitions follow.
    """

    ITERATION = "Iteration"
    """Optional iteration number, useful for tracking the sequence of
    simulation groups."""
    PRIORITY = "Priority"
    """Priority value used to determine execution order."""
    TYPE = "Type"
    """Type of simulation."""
    ID = "ID"
    """Unique identifier for the simulation."""
    STATUS = "Status"
    """Status of the simulation."""
    MATERIAL = "Material"
    """Name of material used during simulation."""
    HEATER_TEMPERATURE = "Heater Temp (C)"
    """Heater temperature (C)."""
    LAYER_THICKNESS = "Layer Thickness (m)"
    """Powder deposition layer thickness (m)."""
    BEAM_DIAMETER = "Beam Diameter (m)"
    """Laser beam diameter (m)."""
    LASER_POWER = "Laser Power (W)"
    """Laser power (W)."""
    SCAN_SPEED = "Scan Speed (m/s)"
    """Laser scan speed (m/s)."""
    PV_RATIO = "Laser Power/Scan Speed (J/m)"
    """Ratio of laser power to scan speed (J/m)."""
    START_ANGLE = "Start Angle (degrees)"
    """Hatch scan angle for first layer (degrees)."""
    ROTATION_ANGLE = "Rotation Angle (degrees)"
    """Hatch rotation angle for subsequent layers (degrees)."""
    HATCH_SPACING = "Hatch Spacing (m)"
    """Hatch spacing (m)."""
    STRIPE_WIDTH = "Stripe Width (m)"
    """Stripe width (m)."""
    ENERGY_DENSITY = "Energy Density (J/m^3)"
    """Laser power divided by build rate (J/m^3)."""
    SINGLE_BEAD_LENGTH = "Single Bead Length (m)"
    """Length of single bead to simulate (m)."""
    BUILD_RATE = "Build Rate (m^3/s)"
    """Layer thickness * scan speed * hatch spacing (m^3/s)."""
    MELT_POOL_WIDTH = "Melt Pool Width (m)"
    """Median melt pool width measured at the top of the powder layer (m)."""
    MELT_POOL_DEPTH = "Melt Pool Depth (m)"
    """Median melt pool depth measured from the top of the powder layer (m)."""
    MELT_POOL_LENGTH = "Melt Pool Length (m)"
    """Median melt pool length measured at the top of the powder layer (m)."""
    MELT_POOL_LENGTH_OVER_WIDTH = "Melt Pool Length/Width"
    """Ratio of MELT_POOL_LENGTH to MELT_POOL_WIDTH."""
    MELT_POOL_REFERENCE_WIDTH = "Melt Pool Ref Width (m)"
    """Median melt pool width measured at the top of the base plate (m)."""
    MELT_POOL_REFERENCE_DEPTH = "Melt Pool Ref Depth (m)"
    """Median melt pool depth measured from the top of the base plate (m)."""
    MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH = "Melt Pool Ref Depth/Width"
    """Ratio of MELT_POOL_REFERENCE_DEPTH to MELT_POOL_REFERENCE_WIDTH."""
    POROSITY_SIZE_X = "Porosity Size X (m)"
    """X dimension size of porosity sample to simulate (m)."""
    POROSITY_SIZE_Y = "Porosity Size Y (m)"
    """Y dimension size of Porosity sample to simulate (m)."""
    POROSITY_SIZE_Z = "Porosity Size Z (m)"
    """Z dimension size of Porosity sample to simulate (m)."""
    RELATIVE_DENSITY = "Relative Density"
    """Relative density of simulated porosity sample."""
    MICRO_MIN_X = "Micro Min X (m)"
    """Minimum X dimension position of microstructure sample (m)."""
    MICRO_MIN_Y = "Micro Min Y (m)"
    """Minimum Y dimension position of microstructure sample (m)."""
    MICRO_MIN_Z = "Micro Min Z (m)"
    """Minimum Z dimension position of microstructure sample (m)."""
    MICRO_SIZE_X = "Micro Size X (m)"
    """X dimension size of microstructure sample to simulate (m)."""
    MICRO_SIZE_Y = "Micro Size Y (m)"
    """Y dimension size of microstructure sample to simulate (m)."""
    MICRO_SIZE_Z = "Micro Size Z (m)"
    """Z dimension size of microstructure sample to simulate (m)."""
    MICRO_SENSOR_DIM = "Micro Sensor Dim (m)"
    """Sensor dimension used in microstructure simulations (m)."""
    COOLING_RATE = "Cooling Rate (K/s)"
    """User-provided cooling rate used in microstructure simulations (K/s)."""
    THERMAL_GRADIENT = "Thermal Gradient (K/m)"
    """User-provided thermal gradient used in microstructure simulations (K/m)."""
    MICRO_MELT_POOL_WIDTH = "Micro Melt Pool Width (m)"
    """User-provided melt pool width used in microstructure simulation (m)."""
    MICRO_MELT_POOL_DEPTH = "Micro Melt Pool Depth (m)"
    """User-provided melt pool depth used in microstructure simulation (m)."""
    RANDOM_SEED = "Random Seed"
    """User-provided random seed used in microstructure simulation."""
    XY_AVERAGE_GRAIN_SIZE = "XY Average Grain Size (microns)"
    """Average microstructure grain size in the XY plane (microns)."""
    XZ_AVERAGE_GRAIN_SIZE = "XZ Average Grain Size (microns)"
    """Average microstructure grain size in the XZ plane (microns)."""
    YZ_AVERAGE_GRAIN_SIZE = "YZ Average Grain Size (microns)"
    """Average microstructure grain size in the YZ plane (microns)."""
    ERROR_MESSAGE = "Error Message"
    """Error message if simulation failed."""


DEFAULT_ITERATION = 0
"""Default iteration assigned to new simulations."""
DEFAULT_PRIORITY = 1
"""Default priority assigned to new simulations."""
FORMAT_VERSION = 3
"""Parametric study file format version."""
