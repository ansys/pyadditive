# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
.. _ref_example_thermal_history:

Thermal History Analysis
========================

This tutorial shows how you can use PyAdditive to determine
thermal history during a build using a simulated coaxial
average sensor.

Units are SI (m, kg, s, K) unless otherwise noted.

First, connect to the Additive service.
"""
import ansys.additive as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Model Selection
# ---------------
# The next step is a to specify a geometry model. Currently, PyAdditive supports
# two types of geometry specifications, STL files and build files. A build file
# in this context is a zip archive containing an STL file describing the
# geometry, a machine instruction file and zero or more STL files describing
# support structures. For details of the build file see <TBD>.
#
# Example build and STL files can be downloaded by importing the examples
# module as shown below.

import ansys.additive.examples as examples

# Creating an ``StlFile`` object
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

stl_name = examples.download_10mm_cube()
stl_file = pyadditive.StlFile(stl_name)

# Creating a ``BuildFile`` object
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

build_file_name = examples.download_small_wedge_slm_build_file()
build_file = pyadditive.BuildFile(pyadditive.MachineType.SLM, build_file_name)

###############################################################################
# Material Selection
# ------------------
# The next step is a to choose a material. A list of available materials can
# be obtained using the ``get_materials_list`` command.

print(additive.get_materials_list())

###############################################################################
# Obtain the parameters for a single material using one of the names from the list.
material = additive.get_material("17-4PH")

###############################################################################
# Machine Parameter Specification
# -------------------------------
# Specify machine parameters by first creating an ``AdditiveMachine`` object
# then assigning the desired values. All values are in SI units (m, kg, s, K)
# unless otherwise noted.

machine = pyadditive.AdditiveMachine()

# Show available parameters
print(machine)

###############################################################################
# Set laser power and scan speed
machine.scan_speed = 1  # m/s
machine.laser_power = 500  # W
machine.layer_thickness = 5e-5  # m (50 microns)

###############################################################################
# Specify Thermal History Simulation Inputs
# -----------------------------------------
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
# Run Simulation
# --------------
# Use the ``simulate`` method of the ``additive`` object to run the simulation.

# NOTE: Change the log_progress parameter to True or remove it altogether when
# using this example interactively.
summary = additive.simulate(input, log_progress=False)

###############################################################################
# Plot Thermal History
# --------------------
# You can plot the thermal history using pyvista as shown below.

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
