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

from ansys.additive.core import (
    Additive,
    AdditiveMachine,
    BuildFile,
    CoaxialAverageSensorInputs,
    MachineType,
    Range,
    SimulationError,
    StlFile,
    ThermalHistoryInput,
)

additive = Additive()

###############################################################################
# Select model
# ------------
# Select the geometry model. Currently, PyAdditive supports
# two types of geometry specifications,
# :class:`STLFile <ansys.additive.core.geometry_file.StlFile>` and
# :class:`BuildFile <ansys.additive.core.geometry_file.BuildFile>`.
#
# You can download example build and STL files by importing the ``examples``
# module.

import ansys.additive.core.examples as examples

# Create an ``StlFile`` object.
stl_name = examples.download_10mm_cube()
stl_file = StlFile(stl_name)

# Or, create a ``BuildFile`` object.
build_file_name = examples.download_small_wedge_slm_build_file()
build_file = BuildFile(MachineType.SLM, build_file_name)

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
# Specify machine parameters by first creating an
# :class:`AdditiveMachine <from ansys.additive.core.machine.AdditiveMachine>`
# object then assigning the desired values.
# All values are in SI units (m, kg, s, K) unless otherwise noted.

machine = AdditiveMachine()

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
# Thermal history is simulated for the given geometry over a range of heights
# in the Z dimension. More than one range can be specified. Each range is specified
# with a :class:`Range <ansys.additive.core.thermal_history.Range>` object.
# The ranges are assigned to a
# :class:`CoaxialAverageSensorInputs <ansys.additive.core.thermal_history.CoaxialAverageSensorInputs>`
# object which also includes a sensor radius. The ``CoaxialAverageSensorInputs`` object
# is assigned to a
# :class:`ThermalHistoryInput <ansys.additive.core.thermal_history.ThermalHistoryInput>`
# object.

# Values are in meters
sensor_inputs = CoaxialAverageSensorInputs(
    radius=5e-4,
    z_heights=[Range(min=1e-3, max=1.1e-3), Range(min=6.5e-3, max=6.6e-3)],
)

input = ThermalHistoryInput(
    machine=machine,
    material=material,
    id="thermal-history-example",
    geometry=stl_file,
    coax_ave_sensor_inputs=sensor_inputs,
)

###############################################################################
# Run simulation
# --------------
# Use the :meth:`simulate() <ansys.additive.core.additive.Additive.simulate>`
# method of the ``additive`` object to run the simulation. The returned object is a
# either a
# :class:`ThermalHistorySummary <ansys.additive.core.thermal_history.ThemalHistorySummary>`
# object or a
# :class:`SimulationError <ansys.additive.core.simulation.SimulationError>.

summary = additive.simulate(input)
if isinstance(summary, SimulationError):
    raise Exception(summary.message)

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
