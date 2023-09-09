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

"""
Parametric study
================

This example shows how you can use PyAdditive to perform a parametric study.
The intended audience is a user who desires to optimize additive machine parameters
to achieve a specific result. Here, the
:class:`ParametricStudy <ansys.additive.core.parametric_study.ParametricStudy>`
class is used to conduct a parametric study. This is not required but
``ParametricStudy`` provides data management and visualization features which ease the task.

Units are SI (m, kg, s, K) unless otherwise noted.
"""
###############################################################################
# Perform required imports and create a study
# ------------------------------------------
# Perform the required import and create a ``ParametricStudy``.
import numpy as np

from ansys.additive.core import Additive, SimulationStatus, SimulationType
from ansys.additive.core.parametric_study import ColumnNames, ParametricStudy
import ansys.additive.core.parametric_study.display as display

study = ParametricStudy("demo-study")

###############################################################################
# Get study file name
# -------------------
# The current state of the parametric study is saved to a file upon each
# update. You can retrieve the name of the file as shown below. This file
# uses a binary format and is not human readable.

print(study.file_name)

###############################################################################
# Select a material for the study
# -------------------------------
# Select a material to use in the study. The material name must be known by
# the Additive service. You can connect to the Additive service
# and print a list of available materials prior to selecting one.

additive = Additive()
print(additive.get_materials_list())
material = "IN718"

###############################################################################
# Create a single bead evaluation
# -------------------------------
# Parametric studies often start with single bead simulations in order to
# determine melt pool statistics. Here, the
# :meth:`generate_single_bead_permutations <ParametricStudy.generate_single_bead_permutations`
# method is used to generate single bead simulation permutations. The parameters
# for ``generate_single_bead_permutations`` allow you to specify a range of
# machine parameters and filter them by energy density. Not all the parameters
# shown are required. Optional parameters that are not specified will use default
# values defined in the :class:`MachineConstants <ansys.additive.core.machine.MachineConstants>`
# class.

# Specify a range of laser powers. Valid values are 50 to 700 W.
initial_powers = np.linspace(50, 700, 3)
# Specify a range of laser scan speeds. Valid values are 0.35 to 2.5 m/s.
initial_scan_speeds = np.linspace(0.35, 2.5, 3)
# Specify powder layer thicknesses. Valid values are 10e-6 to 100e-6 m.
initial_layer_thicknesses = [40e-6, 50e-6]
# Specify laser beam diameters. Valid values are 20e-6 to 140e-6 m.
initial_beam_diameters = [80e-6, 120e-6]
# Specify heater temperatures. Valid values are 20 - 500 C.
initial_heater_temps = [80, 120]
# Restrict the permutations within a range of energy densities
# For single bead, the energy density is laser power / (laser scan speed * layer thickness).
min_energy_density = 2e6
max_energy_density = 8e6
# Specify a bead length in meters.
bead_length = 0.001

study.generate_single_bead_permutations(
    material_name=material,
    bead_length=bead_length,
    laser_powers=initial_powers,
    scan_speeds=initial_scan_speeds,
    layer_thicknesses=initial_layer_thicknesses,
    beam_diameters=initial_beam_diameters,
    heater_temperatures=initial_heater_temps,
    min_area_energy_density=min_energy_density,
    max_area_energy_density=max_energy_density,
)

###############################################################################
# Show the simulations as a table
# -------------------------------
# You can use the ``display`` module of ``ParametricStudy`` to list the simulations
# as a table.

display.show_table(study)

###############################################################################
# Skip some simulations
# ---------------------
# If you a working with a large parametric study, you may want to skip some
# simulations to reduce processing time. To do so, set the simulation status
# to ``SimulationStatus.SKIP``. See
# :class:`SimulationStatus <ansys.additive.core.simulation.SimulationStatus>`
# class. Here, a :class:`DataFrame <pandas.DataFrame>` is obtained, a filter is
# applied to get a list of simulation IDs, then the status is updated on the
# simulations with those IDs.

df = study.data_frame()
# Get IDs for single bead simulations with laser power below 75 W.
ids = df.loc[
    (df[ColumnNames.LASER_POWER] < 75) & (df[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD),
    ColumnNames.ID,
].tolist()
study.set_status(ids, SimulationStatus.SKIP)
display.show_table(study)

# ###############################################################################
# Run single bead simulations
# ---------------------------
# Run the simulations using :meth:`run_simulations <ParametricStudy.run_simulations>`.
# All simulations with status ``SimulationStatus.PENDING`` will be executed.

study.run_simulations(additive)

# ###############################################################################
# Save the study to CSV file
# --------------------------
# The parametric study is saved with each update in a binary format.
# For other formats, use the ``to_*`` methods provided by
# :class:`DataFrame <pandas.DataFrame>`.

study.data_frame().to_csv("demo-study.csv")

# ###############################################################################
# Load a previously saved study
# -----------------------------
# Load a previously saved study using the :meth:`ParameticStudy.load <ParametricStudy.load>`
# method.

study2 = ParametricStudy.load("demo-study.ps")
display.show_table(study2)

###############################################################################
# Plot single bead results
# ------------------------
# Plot the single bead results.

display.single_bead_eval_plot(study)

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
# scan speed * layer thickness * hatch spacing.

df = study.data_frame()
df = df[
    (df[ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] >= 0.15)
    & (df[ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] <= 0.75)
]

study.generate_porosity_permutations(
    material_name=material,
    laser_powers=df[ColumnNames.LASER_POWER].unique(),
    scan_speeds=df[ColumnNames.SCAN_SPEED].unique(),
    size_x=1e-3,
    size_y=1e-3,
    size_z=1e-3,
    layer_thicknesses=[40e-6],
    heater_temperatures=[80],
    beam_diameters=[80e-6],
    start_angles=[0, 45],
    rotation_angles=[67.5, 23.75],
    hatch_spacings=[100e-6, 200e-6],
    min_build_rate=1e-8,
    iteration=1,
)

# ###############################################################################
# Run porosity simulations
# ------------------------
# Run the simulations using :meth:`run_simulations <ParametricStudy.run_simulations>`.

study.run_simulations(additive)

# ###############################################################################
# Plot porosity results
# ---------------------
# Plot the porosity simulation results.

display.porosity_contour_plot(study)

###############################################################################
# Create a microstructure evaluation
# ----------------------------------
# Here a set of microstructure simulations is generated using many of the same
# parameters used for the porosity simulations. The parameters ``cooling_rate``,
# ``thermal_gradient``, ``melt_pool_width``, and ``melt_pool_depth`` are not
# specified so they will be calculated.

df = study.data_frame()
df = df[(df[ColumnNames.TYPE] == SimulationType.POROSITY)]

study.generate_microstructure_permutations(
    material_name=material,
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

# ###############################################################################
# Run microstructure simulations
# ------------------------
# Run the simulations using :meth:`run_simulations <ParametricStudy.run_simulations>`.

study.run_simulations(additive)

# ###############################################################################
# Plot microstructure results
# ---------------------------
# Plot the average grain size from the microstructure simulation results.

display.ave_grain_size_plot(study)
