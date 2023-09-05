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

class ColumnNames:
    """Provides column names for the parametric study data frame.

    Values are stored internally as a :class:`Pandas DataFrame
    <pandas.DataFrame>`. Column name definitions follow.
    """

    #: Name of the parametric summary project.
    PROJECT = "Project"
    #: Iteration number, which is useful for tracking the sequence of simulation groups.
    ITERATION = "Iteration"
    #: Priority value used to determine execution order.
    PRIORITY = "Priority"
    #: Type of simulation. For example, single bead, porosity, or microstructure.
    TYPE = "Type"
    #: Identifier for the simulation.
    #: NOTE: A unique ID for each permutation is enforced by the parametric study.
    ID = "ID"
    #: Status of the simulation. For example, pending, success, or failure.
    STATUS = "Status"
    #: Name of material used during simulation.
    #: See :class:`AdditiveMaterial <from ansys.additive.core.material.AdditiveMaterial>`.
    MATERIAL = "Material"
    #: Heater temperature (°C).
    HEATER_TEMPERATURE = "Heater Temp (°C)"
    #: Powder deposition layer thickness (m).
    LAYER_THICKNESS = "Layer Thickness (m)"
    #: Laser beam diameter (m).
    BEAM_DIAMETER = "Beam Diameter (m)"
    #: Laser power (W).
    LASER_POWER = "Laser Power (W)"
    #: Laser scan speed (m/s).
    SCAN_SPEED = "Scan Speed (m/s)"
    #: Hatch scan angle for first layer (°).
    START_ANGLE = "Start Angle (°)"
    #: Hatch rotation angle for subsequent layers (°).
    ROTATION_ANGLE = "Rotation Angle (°)"
    #: Hatch spacing (m).
    HATCH_SPACING = "Hatch Spacing (m)"
    #: Stripe width (m).
    STRIPE_WIDTH = "Stripe Width (m)"
    #: Energy density calculated as laser power divided by build rate (J/m^3).
    ENERGY_DENSITY = "Energy Density (J/m^3)"
    #: Build rate, calculated as layer thickness * scan speed * hatch spacing (m^3/s).
    #: For single bead simulations, hatch spacing is 1 m.
    BUILD_RATE = "Build Rate (m^3/s)"
    #: Length of single bead to simulate (m).
    SINGLE_BEAD_LENGTH = "Single Bead Length (m)"
    #: Median melt pool width measured at the top of the powder layer (m).
    MELT_POOL_WIDTH = "Melt Pool Width (m)"
    #: Median melt pool depth measured from the top of the powder layer (m).
    MELT_POOL_DEPTH = "Melt Pool Depth (m)"
    #: Median melt pool length measured at the top of the powder layer (m).
    MELT_POOL_LENGTH = "Melt Pool Length (m)"
    #: Ratio of MELT_POOL_LENGTH to the median melt pool width at the top of the powder layer.
    MELT_POOL_LENGTH_OVER_WIDTH = "Melt Pool Length/Width (m)"
    #: Median melt pool width measured at the top of the base plate (m).
    MELT_POOL_REFERENCE_WIDTH = "Melt Pool Ref Width (m)"
    #: Median melt pool depth measured from the top of the base plate (m).
    MELT_POOL_REFERENCE_DEPTH = "Melt Pool Ref Depth (m)"
    #: Ratio of MELT_POOL_REFERENCE_DEPTH to MELT_POOL_REFERENCE_WIDTH.
    MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH = "Melt Pool Ref Depth/Width (m)"
    #: X dimension size of porosity sample to simulate (m).
    POROSITY_SIZE_X = "Porosity Size X (m)"
    #: Y dimension size of Porosity sample to simulate (m).
    POROSITY_SIZE_Y = "Porosity Size Y (m)"
    #: Z dimension size of Porosity sample to simulate (m).
    POROSITY_SIZE_Z = "Porosity Size Z (m)"
    #: Relative density of simulated porosity sample.
    RELATIVE_DENSITY = "Relative Density"
    #: Minimum X dimension position of microstructure sample (m).
    MICRO_MIN_X = "Micro Min X (m)"
    #: Minimum Y dimension position of microstructure sample (m).
    MICRO_MIN_Y = "Micro Min Y (m)"
    #: Minimum Z dimension position of microstructure sample (m).
    MICRO_MIN_Z = "Micro Min Z (m)"
    #: X dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_X = "Micro Size X (m)"
    #: Y dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_Y = "Micro Size Y (m)"
    #: Z dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_Z = "Micro Size Z (m)"
    #: Sensor dimension used in microstructure simulations (m).
    MICRO_SENSOR_DIM = "Micro Sensor Dim (m)"
    #: User-provided cooling rate used in microstructure simulations (°K/s).
    COOLING_RATE = "Cooling Rate (°K/s)"
    #: User-provided thermal gradient used in microstructure simulations (°K/m).
    THERMAL_GRADIENT = "Thermal Gradient (°K/m)"
    #: User-provided melt pool width used in microstructure simulation (m).
    MICRO_MELT_POOL_WIDTH = "Micro Melt Pool Width (m)"
    #: User-provided melt pool depth used in microstructure simulation (m).
    MICRO_MELT_POOL_DEPTH = "Micro Melt Pool Depth (m)"
    #: User-provided random seed used in microstructure simulation.
    RANDOM_SEED = "Random Seed"
    #: Average microstructure grain size in the XY plane (µm).
    XY_AVERAGE_GRAIN_SIZE = "XY Average Grain Size (µm)"
    #: Average microstructure grain size in the XZ plane (µm).
    XZ_AVERAGE_GRAIN_SIZE = "XZ Average Grain Size (µm)"
    #: Average microstructure grain size in the YZ plane (µm).
    YZ_AVERAGE_GRAIN_SIZE = "YZ Average Grain Size (µm)"
    #: Error message if simulation failed.
    ERROR_MESSAGE = "Error Message"


DEFAULT_ITERATION = 0
DEFAULT_PRIORITY = 1
