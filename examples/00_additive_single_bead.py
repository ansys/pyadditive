"""
Single Bead Analysis
====================

This tutorial shows how you can use PyAdditive to determine
meltpool characteristics for given material and machine
parameter combinations.

Units are SI (m, kg, s, K) unless otherwise noted.

First, connect to the Additive service.
"""
import matplotlib.pyplot as plt

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
machine.laser_power = 300  # W

###############################################################################
# Specify Single Bead Simulation Inputs
# -------------------------------------
# Create a ``SingleBeadInput`` object containing the desired simulation
# parameters.

input = pyadditive.SingleBeadInput(
    machine=machine, material=material, id="single-bead-example", bead_length=0.0012  # meters
)

###############################################################################
# Run Simulation
# --------------
# Use the ``simulate`` method of the ``additive`` object to run the simulation.
# The ``simulate`` method returns a list of summary objects so we
# take the first element of the list.

summary = additive.simulate(input)[0]

###############################################################################
# Plot Melt Pool Statistics
# -------------------------
# You can plot the melt pool statistics using matplotlib.

_, ax = plt.subplots()
mp = summary.melt_pool
ax.plot(mp.laser_x, mp.length, label="length")
ax.plot(mp.laser_x, mp.width, label="width")
ax.plot(mp.laser_x, mp.depth, label="depth")
ax.plot(mp.laser_x, mp.reference_width, label="reference_width")
ax.plot(mp.laser_x, mp.reference_depth, label="reference_depth")
ax.legend()
ax.set_xlabel("Bead Length (m)")
ax.set_ylabel("Melt Pool (m)")
ax.set_title("Melt Pool Statistics")

plt.show()
