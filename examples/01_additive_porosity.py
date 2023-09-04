# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
Porosity Analysis
=================

This tutorial shows how you can use PyAdditive to determine
porosity for given material and machine parameter combinations.

Units are SI (m, kg, s, K) unless otherwise noted.

First, connect to the Additive service.
"""
import ansys.additive.core as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Select Material
# ---------------
# The next step is a to choose a material. A list of available materials can
# be obtained using the
# :meth:`get_materials_list() <ansys.additive.core.additive.Additive.get_materials_list>`
# command.

print(additive.get_materials_list())

###############################################################################
# Obtain the parameters for a single material by passing one of the names
# from the materials list to
# :meth:`get_material() <ansys.additive.core.additive.Additive.get_material>`.
material = additive.get_material("316L")

###############################################################################
# Set Machine Parameters
# ----------------------
# Specify machine parameters by first creating an
# :class:`AdditiveMachine <from ansys.additive.core.machine.AdditiveMachine>` object
# then assigning the desired values. All values are in SI units (m, kg, s, K)
# unless otherwise noted.
machine = pyadditive.AdditiveMachine()

# Show available parameters
print(machine)

###############################################################################
# Set laser power and scan speed
machine.scan_speed = 1.2  # m/s
machine.laser_power = 250  # W

###############################################################################
# Specify Porosity Simulation Inputs
# ----------------------------------
# Create a :class:`PorosityInput <ansys.additive.core.porosity.PorosityInput>` object
# containing the desired simulation parameters.

input = pyadditive.PorosityInput(
    machine=machine,
    material=material,
    id="porosity-example",
    size_x=0.001,  # meters
    size_y=0.001,
    size_z=0.001,
)

###############################################################################
# Run Simulation
# --------------
# Use the :meth:`simulate() <ansys.additive.core.additive.Additive.simulate>` method
# on the ``additive`` object to run the simulation. The returned object is a
# :class:`PorositySummary <ansys.additive.core.porosity.PorositySummary>` object
# containing the input and the relative density of the simulated sample.

summary = additive.simulate(input)

###############################################################################
# Print Results
# -------------

print(f"For {summary.input.material.name} with \n", summary.input.machine)
print(f"\n    relative density = {round(summary.relative_density, 5)}")
