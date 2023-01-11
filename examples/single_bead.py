# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
.. _ref_example_single_bead:

Single Bead Analysis
--------------------

This tutorial shows how you can use PyAdditive to determine
meltpool characteristics for given material and machine
parameter combinations.

First, connect to the Additive service.
"""
import matplotlib.pyplot as plt

import ansys.additive.additive as pyadditive
from ansys.additive.machine import AdditiveMachine
from ansys.additive.single_bead import BeadType, SingleBeadInput

additive = pyadditive.Additive()

###############################################################################
# Material Selection
# ~~~~~~~~~~~~~~~~~~
# The next step is a to choose a material. A list of available materials can
# be obtained using the following command.

material_list = additive.get_materials_list()
print(material_list)

# Obtain the parameters for a single material using one of the names in the list.
material = additive.get_material("17-4PH")

###############################################################################
# Machine Parameter Specification
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Specify machine parameters by first creating an ``AdditiveMachine`` object
# then assigning the desired values. All values are in SI units (m, kg, s, K)
# unless otherwise noted.

machine = AdditiveMachine()

# See available parameters
print(machine)

# Set laser power and scan speed
machine.scan_speed = 1  # m/s
machine.laser_power = 500  # W

###############################################################################
# Specify Single Bead Simulation Inputs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a ``SingleBeadInput`` object containing the desired simulation
# parameters.

input = SingleBeadInput(
    machine=machine,
    material=material,
    id="single-bead-example",
    bead_length=0.001,  # meters (1 mm)
    bead_type=BeadType.BEAD_ON_POWDER,  # See :class:`BeadType`
)

###############################################################################
# Run Simulation
# ~~~~~~~~~~~~~~
# Use the ``simulate`` method of the ``additive`` object to run the simulation.

# NOTE: Change the log_progress parameter to True or remove it altogether when
# using this example interactively.
result = additive.simulate(input, log_progress=False)

###############################################################################
# Plot Melt Pool Statistics
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# You can plot the melt pool statistics using matplotlib.

_, ax = plt.subplots()
mp = result.melt_pool
ax.plot(mp.laser_x, mp.length, label="length")
ax.plot(mp.laser_x, mp.width, label="width")
ax.plot(mp.laser_x, mp.depth, label="depth")
ax.plot(mp.laser_x, mp.reference_width, label="reference_width")
ax.plot(mp.laser_x, mp.reference_depth, label="reference_depth")
ax.legend()
ax.set_title("Melt Pool Statistics")

plt.show()
