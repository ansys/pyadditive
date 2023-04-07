"""
Porosity Analysis
=================

This tutorial shows how you can use PyAdditive to determine
porosity for given material and machine parameter combinations.

Units are SI (m, kg, s, K) unless otherwise noted.

First, connect to the Additive service.
"""
import ansys.additive as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Material Selection
# ------------------
# The next step is a to choose a material. A list of available materials can
# be obtained using the ``get_materials_list`` command.

print(additive.get_materials_list())

###############################################################################
# Obtain the parameters for a single material using one of the names from the list.
material_name = "17-4PH"
material = additive.get_material(material_name)

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
machine.scan_speed = 1.2  # m/s
machine.laser_power = 250  # W

###############################################################################
# Specify Porosity Simulation Inputs
# ----------------------------------
# Create a ``PorosityInput`` object containing the desired simulation
# parameters.

input = pyadditive.PorosityInput(
    machine=machine,
    material=material,
    id="porosity-example",
    size_x=0.001,  # in meters (1 mm)
    size_y=0.001,
    size_z=0.001,
)

###############################################################################
# Run Simulation
# --------------
# Use the ``simulate`` method of the ``additive`` object to run the simulation.
# The ``simulate`` method returns a list of summary objects so we
# take the first element of the list.

summary = additive.simulate(input)[0]

###############################################################################
# Print Results
# -------------
# The result object has void_ratio, powder_ratio and solid_ratio properties.

print(
    f"For {material_name} with laser power of {summary.input.machine.laser_power} W"
    + f" and scan speed of {summary.input.machine.scan_speed} m/s:"
)
print(f"    solid ratio = {round(summary.solid_ratio, 5)}")
print(f"    powder ratio = {round(summary.powder_ratio, 5)}")
print(f"    void ratio = {round(summary.void_ratio, 5)}")
