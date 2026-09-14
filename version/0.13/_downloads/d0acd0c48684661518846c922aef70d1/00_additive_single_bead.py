"""
Single Bead Analysis
====================

This tutorial shows how you can use PyAdditive to determine
meltpool characteristics for given material and machine
parameter combinations.

Units are SI (m, kg, s, K) unless otherwise noted.

First, connect to the Additive service.
"""
import ansys.additive as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Select Material
# ---------------
# The next step is a to choose a material. A list of available materials can
# be obtained using the
# :meth:`get_materials_list() <ansys.additive.additive.Additive.get_materials_list>`
# command.

print(additive.get_materials_list())

###############################################################################
# Obtain the parameters for a single material by passing one of the names
# from the materials list to
# :meth:`get_material() <ansys.additive.additive.Additive.get_material>`.
material = additive.get_material("17-4PH")

###############################################################################
# Set Machine Parameters
# ----------------------
# Specify machine parameters by first creating an
# :class:`AdditiveMachine <ansys.additive.machine.AdditiveMachine>` object
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
# Create a :class:`SingleBeadInput <ansys.additive.single_bead.SingleBeadInput>`
# object containing the desired simulation parameters.

input = pyadditive.SingleBeadInput(
    machine=machine, material=material, id="single-bead-example", bead_length=0.0012  # meters
)

###############################################################################
# Run Simulation
# --------------
# Use the :meth:`simulate() <ansys.additive.additive.Additive.simulate>`
# method of the ``additive`` object to run the simulation. The returned object is a
# :class:`SingleBeadSummary <ansys.additive.single_bead.SingleBeadSummary>`
# containing the input and a
# :class:`MeltPool <ansys.additive.single_bead.MeltPool>` object.

summary = additive.simulate(input)

###############################################################################
# Plot Melt Pool Statistics
# -------------------------
# A :class:`Pandas DataFrame <pandas.DataFrame>` containing the melt pool
# statistics can be obtained using the
# :meth:`data_frame() <ansys.additive.single_bead.MeltPool.data_frame>` property
# of the ``melt_pool`` attribute of the ``summary`` object. The
# :meth:`plot() <pandas.DataFrame.plot>` method can be used to plot the melt
# pool dimensions as a function of bead length.

df = summary.melt_pool.data_frame.multiply(1e6)  # convert from meters to microns
df.index *= 1e3  # convert bead length from meters to millimeters

df.plot(
    y=["length", "width", "depth", "reference_width", "reference_depth"],
    ylabel="Melt Pool Dimensions (µm)",
    xlabel="Bead Length (mm)",
    title="Melt Pool Dimensions vs Bead Length",
)


###############################################################################
# List Melt Pool Statistics
# -------------------------
# A table of the melt pool statistics can be obtained using a
# `Pandas Styler <https://pandas.pydata.org/docs/user_guide/style.html>`_.
# Here we show only the first few rows using ``head()`` for brevity.

df.head().style.format("{:.2f}").format_index("{:.2f}")

###############################################################################
# Save Melt Pool Statistics
# -------------------------
# The melt pool statistics can be saved to a CSV file using the
# :meth:`to_csv() <pandas.DataFrame.to_csv>` method.

df.to_csv("melt_pool.csv")
