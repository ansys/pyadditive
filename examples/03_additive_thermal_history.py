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
Thermal history analysis
========================

This example shows how you can use PyAdditive to determine
thermal history during a build using a simulated coaxial
average sensor.

Units are SI (m, kg, s, K) unless otherwise noted.
"""
###############################################################################
# Perform required import and connect
# -----------------------------------
# Perform the required import and connect to the Additive service.

import ansys.additive.core as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Select model
# ------------
# Select the geometry model. Currently, PyAdditive supports
# two types of geometry specifications, STL files and build files. In
# this context, a build file is a ZIP archive that contains an STL file describing the
# geometry, a machine instruction file, and zero or more STL files describing
# support structures. For more information on build files, see <TBD>.
#
# You can download example build and STL files by importing the ``examples``
# module.

import ansys.additive.core.examples as examples

# Create ``StlFile`` object
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Create an ``StlFile`` object.

stl_name = examples.download_10mm_cube()
stl_file = pyadditive.StlFile(stl_name)

# Create ``BuildFile`` object
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a ``BuildFile`` object.

build_file_name = examples.download_small_wedge_slm_build_file()
build_file = pyadditive.BuildFile(pyadditive.MachineType.SLM, build_file_name)

###############################################################################
# Select material
# ---------------
# Select a material. You can use the
# :meth:`get_materials_list() <ansys.additive.additive.Additive.get_materials_list>`
# method to obtain a list of available materials.

print(additive.get_materials_list())

###############################################################################
# You can obtain the parameters for a single material by passing a name
# from the materials list to the
# :meth:`get_material() <ansys.additive.additive.Additive.get_material>`
# method.

material = additive.get_material("17-4PH")

###############################################################################
# Specify machine parameters
# --------------------------
# Specify machine parameters by first creating an ``AdditiveMachine`` object
# and then assigning the desired values. All values are in SI units (m, kg, s, K)
# unless otherwise noted.

machine = pyadditive.AdditiveMachine()

# Show available parameters
print(machine)

###############################################################################
# Set laser power and scan speed
# ------------------------------
# Set the laser power and scan speed.

machine.scan_speed = 1  # m/s
machine.laser_power = 500  # W

###############################################################################
# Specify inputs for thermal history simulation
# ---------------------------------------------
# Create a ``ThermalHistoryInput`` object containing the desired simulation
# parameters. The ``ThermalHistoryInput`` object contains ``CoaxialAverageSensorInputs``.
# ``CoaxialAverageSensorInputs`` consist of a sensor radius and one or more ``Range``
# of z heights.

# Values are in meters
sensor_inputs = pyadditive.CoaxialAverageSensorInputs(
    radius=5e-4,
    z_heights=[pyadditive.Range(min=1e-3, max=1.1e-3), pyadditive.Range(min=6.5e-3, max=6.6e-3)],
)

input = pyadditive.ThermalHistoryInput(
    machine=machine,
    material=material,
    id="thermal-history-example",
    geometry=stl_file,
    coax_ave_sensor_inputs=sensor_inputs,
)

###############################################################################
# Run simulation
# --------------
# Use the ``simulate`` method of the ``additive`` object to run the simulation.

summary = additive.simulate(input)

###############################################################################
# Plot thermal history
# --------------------
# Plot the thermal history using PyVista.

import glob
import os

import pyvista as pv

vtk_files = glob.glob(os.path.join(summary.coax_ave_output_folder, "*.vtk"))
for file in vtk_files:
    plotter = pv.Plotter(window_size=[512, 512])
    plotter.add_mesh(pv.read(file))
    title = os.path.splitext(os.path.basename(file))[0]
    plotter.add_title(title, font_size=8)
    plotter.show()
