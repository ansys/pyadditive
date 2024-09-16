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
"""
Parametric study
================

This example shows how to use PyAdditive to perform a parametric study.
You perform a parametric study if you want to optimize additive machine parameters
to achieve a specific result. Here, the :class:`ParametricStudy` class is used to
conduct a parametric study. While not essential, the :class:`ParametricStudy`
class provides data management features that make the work easier. Also, the
``ansys.additive.widgets`` package can be used to create interactive visualizations
for of parametric study results. An example is available at
`Parametric Study Example
<https://widgets.additive.docs.pyansys.com/version/stable/examples/gallery_examples>`_.


Units are SI (m, kg, s, K) unless otherwise noted.
"""

###############################################################################
# Perform required imports and create a study
# -------------------------------------------
# Perform the required import and create a :class:`ParametricStudy` instance.
import numpy as np
import pandas as pd

from ansys.additive.core import Additive, SimulationStatus, SimulationType
from ansys.additive.core.parametric_study import ColumnNames, ParametricStudy

###############################################################################
# Select a material for the study
# -------------------------------
# Select a material to use in the study. The material name must be known by
# the Additive service. You can connect to the Additive service
# and print a list of available materials prior to selecting one.

additive = Additive()
print("Available material names: {}".format(additive.materials_list()))
material = "IN718"

###############################################################################
# Create the study
# ----------------
# Create the parametric study with a name and the selected material.

study = ParametricStudy("demo-study", material)

###############################################################################
# Get the study file name
# -----------------------
# The current state of the parametric study is saved to a file upon each
# update. You can retrieve the name of the file as shown below. This file
# uses a binary format and is not human readable.

print(study.file_name)


###############################################################################
# Create a single bead evaluation
# -------------------------------
# Parametric studies often start with single bead simulations in order to
# determine melt pool statistics. Here, the
# :meth:`~ParametricStudy.generate_single_bead_permutations` method is used to
# generate single bead simulation permutations. The parameters
# for the :meth:`~ParametricStudy.generate_single_bead_permutations` method allow you to
# specify a range of machine parameters and filter them by energy density. Not all
# the parameters shown are required. Optional parameters that are not specified
# use default values defined in the :class:`MachineConstants` class.

# Specify a range of laser powers. Valid values are 50 to 700 W.
initial_powers = np.linspace(50, 700, 7)
# Specify a range of laser scan speeds. Valid values are 0.35 to 2.5 m/s.
initial_scan_speeds = np.linspace(0.35, 2.5, 5)
# Specify powder layer thicknesses. Valid values are 10e-6 to 100e-6 m.
initial_layer_thicknesses = [40e-6, 50e-6]
# Specify laser beam diameters. Valid values are 20e-6 to 140e-6 m.
initial_beam_diameters = [80e-6]
# Specify heater temperatures. Valid values are 20 - 500 C.
initial_heater_temps = [80]
# Restrict the permutations within a range of energy densities
# For single bead, the energy density is laser power / (laser scan speed *  100 µm).
# The units are J/m^3.
min_energy_density = 2e10
max_energy_density = 8e10
# Specify a bead length in meters.
bead_length = 0.001

study.generate_single_bead_permutations(
    bead_length=bead_length,
    laser_powers=initial_powers,
    scan_speeds=initial_scan_speeds,
    layer_thicknesses=initial_layer_thicknesses,
    beam_diameters=initial_beam_diameters,
    heater_temperatures=initial_heater_temps,
    min_energy_density=min_energy_density,
    max_energy_density=max_energy_density,
)

###############################################################################
# Show the simulations as a table
# -------------------------------
# The :meth:`~ParametricStudy.data_frame` method returns a :class:`~pandas.DataFrame`
# object that can be used to display the simulations as a table. Here, the
# :meth:`~pandas.DataFrame.head` method is used to display all the rows of the table.

df = study.data_frame()
pd.set_option("display.max_columns", None)  # show all columns
df.head(len(df))

###############################################################################
# Skip some simulations
# ---------------------
# If you are working with a large parametric study, you may want to skip some
# simulations to reduce processing time. To do so, set the simulation status
# to :obj:`SimulationStatus.SKIP` which is defined in the :class:`SimulationStatus`
# class. Here, a :class:`~pandas.DataFrame` object is obtained, a filter is
# applied to get a list of simulation IDs, and then the status is updated on the
# simulations with those IDs.

df = study.data_frame()
# Get IDs for single bead simulations with laser power below 75 W.
ids = df.loc[
    (df[ColumnNames.LASER_POWER] < 75) & (df[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD),
    ColumnNames.ID,
].tolist()
study.set_simulation_status(ids, SimulationStatus.SKIP)
print(study.data_frame()[[ColumnNames.ID, ColumnNames.TYPE, ColumnNames.STATUS]])

###############################################################################
# Run single bead simulations
# ---------------------------
# Run the simulations using the :meth:`~Additive.simulate_study` method. All simulations
# with a :obj:`SimulationStatus.NEW` status are executed.

additive.simulate_study(study)

###############################################################################
# View single bead results
# ------------------------
# The single bead simulation results are shown in the ``Melt Pool Width (m)``, ``Melt Pool Depth (m)``,
# ``Melt Pool Length (m)``, ``Melt Pool Length/Width``, ``Melt Pool Ref Width (m)``,
# ``Melt Pool Ref Depth (m)``, and ``Melt Pool Ref Depth/Width`` columns of the data frame.
# For explanations of these columns, see :class:`ColumnNames`.

study.data_frame().head(len(study.data_frame()))

###############################################################################
# Save the study to a CSV file
# ----------------------------
# The parametric study is saved with each update in a binary format.
# For other formats, use the ``to_*`` methods provided by the :class:`~pandas.DataFrame` class.

study.data_frame().to_csv("demo-study.csv")

###############################################################################
# Import a study from a CSV file
# ------------------------------
# Import a study from a CSV file using the :meth:`ParametricStudy.import_csv_study` method.
# The CSV file must contain the same columns as the parametric study data frame.
# The :meth:`ParametricStudy.import_csv_study` method will return a list of errors for each
# simulation that failed to import and the number of duplicate simulations removed (if any).
# All other valid simulations will be added to the study.

study2 = ParametricStudy("demo-csv-study.ps", material)
errors = study2.import_csv_study("demo-study.csv")
study2.data_frame().head()

###############################################################################
# Load a previously saved study
# -----------------------------
# Load a previously saved study using the static
# :meth:`ParameticStudy.load() <ParametricStudy.load>` method.

study3 = ParametricStudy.load("demo-study.ps")
study3.data_frame().head()

###############################################################################
# Create a porosity evaluation
# ----------------------------
# You can use the insights gained from the single bead evaluation to
# generate parameters for a porosity evaluation. Alternatively, you can
# perform a porosity evaluation without a previous single bead evaluation.
# Here, the laser power and scan speeds are determined by filtering the
# single bead results where the ratio of the melt pool reference depth
# to reference width is within a specified range. Additionally, the simulations
# are restricted to a minimum build rate, which is calculated as
# scan speed * layer thickness * hatch spacing. The
# :meth:`~ParametricStudy.generate_porosity_permutations` method is used to add
# porosity simulations to the study.

df = study.data_frame()
df = df[
    (df[ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] >= 0.3)
    & (df[ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] <= 0.65)
]

study.generate_porosity_permutations(
    laser_powers=df[ColumnNames.LASER_POWER].unique(),
    scan_speeds=df[ColumnNames.SCAN_SPEED].unique(),
    size_x=1e-3,
    size_y=1e-3,
    size_z=1e-3,
    layer_thicknesses=[40e-6],
    heater_temperatures=[80],
    beam_diameters=[80e-6],
    start_angles=[45],
    rotation_angles=[67.5],
    hatch_spacings=[100e-6],
    min_build_rate=5e-9,
    iteration=1,
)

################################################################################
# Run porosity simulations
# ------------------------
# Run the simulations using the :meth:`~Additive.simulate_study` method.

additive.simulate_study(study)

###############################################################################
# View porosity results
# ---------------------
# Porosity simulation results are shown in the ``Relative Density`` column of
# the data frame.
df = study.data_frame()
df = df[df[ColumnNames.TYPE] == SimulationType.POROSITY]
df.head(len(df))


###############################################################################
# Create a microstructure evaluation
# ----------------------------------
# Here a set of microstructure simulations is generated using many of the same
# parameters used for the porosity simulations. The parameters ``cooling_rate``,
# ``thermal_gradient``, ``melt_pool_width``, and ``melt_pool_depth`` are not
# specified so they are calculated. The
# :meth:`~ParametricStudy.generate_microstructure_permutations` method is used to add
# microstructure simulations to the study.

df = study.data_frame()
df = df[df[ColumnNames.TYPE] == SimulationType.POROSITY]

study.generate_microstructure_permutations(
    laser_powers=df[ColumnNames.LASER_POWER].unique(),
    scan_speeds=df[ColumnNames.SCAN_SPEED].unique(),
    size_x=1e-3,
    size_y=1e-3,
    size_z=1.1e-3,
    sensor_dimension=1e-4,
    layer_thicknesses=df[ColumnNames.LAYER_THICKNESS].unique(),
    heater_temperatures=df[ColumnNames.HEATER_TEMPERATURE].unique(),
    beam_diameters=df[ColumnNames.BEAM_DIAMETER].unique(),
    start_angles=df[ColumnNames.START_ANGLE].unique(),
    rotation_angles=df[ColumnNames.ROTATION_ANGLE].unique(),
    hatch_spacings=df[ColumnNames.HATCH_SPACING].unique(),
    iteration=2,
)

###############################################################################
# Run microstructure simulations
# ------------------------------
# Run the simulations using the :meth:`~Additive.simulate_study` method.

additive.simulate_study(study)

###############################################################################
# View microstructure results
# ---------------------------
# Microstructure simulation results are shown in the ``XY Average Grain Size (microns)``,
# ``XZ Average Grain Size (microns)``, and ``YZ Average Grain Size (microns)`` columns of
# the data frame. For explanations of these columns, see :class:`ColumnNames`.

df = study.data_frame()
df = df[df[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE]
df.head(len(df))
