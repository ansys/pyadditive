# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
Using a custom material
=======================

This example shows how you can use a custom material in PyAdditive simulations.
For background information and file formats, see
`Material Tuning Tool (Beta) to Create User Defined Materials
<https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_science_BETA_material_tuning_tool.html?q=material%20tuning%20tool>`_
in the *Additive Manufacturing Beta Features* documentation.
To prevent wasted time, before executing this example, carefully review
the steps described in this PyAdditive documentation.

Units are SI (m, kg, s, K) unless otherwise noted.
"""
###############################################################################
# Perform required import and connect
# -----------------------------------
# Perform the required import and connect to the Additive service.

import ansys.additive as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Download custom material
# ------------------------
# Download an example of a custom material. Typically, you would have the
# files defining your custom material stored locally.

import ansys.additive.examples as examples

material_files = examples.download_custom_material()

###############################################################################
# Load custom material files
# --------------------------
# Use the ``load_material`` method on the ``additive`` object to load the files
# defining a custom material.

custom_material = additive.load_material(
    parameters_file=material_files.material_parameters_file,
    thermal_lookup_file=material_files.thermal_properties_lookup_file,
    characteristic_width_lookup_file=material_files.characteristic_width_lookup_file,
)

###############################################################################
# Use the custom material in a simulation
# ---------------------------------------
# Once the custom material has been loaded, you can assign it to a simulation input
# object.

input = pyadditive.SingleBeadInput(
    machine=pyadditive.AdditiveMachine(),
    material=custom_material,
    id="single-bead-simulation",
    bead_length=0.001,  # meters
)

# Remove '#' to run the simulation
# additive.simulate(input)
