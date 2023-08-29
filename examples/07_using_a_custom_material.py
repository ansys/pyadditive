# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
Using A Custom Material
=======================

This tutorial shows how you can use a custom material in PyAdditive simulations.
Background information and file formats can be found in `the Additive documentation
<https://ansysproducthelpqa.win.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_science_BETA_material_tuning_tool.html>`_.

Units are SI (m, kg, s, K) unless otherwise noted.

"""
import ansys.additive as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Example Custom Material
# -----------------------
# Here we download an example custom material. Typically a user would have the
# files defining their custom material stored locally.
import ansys.additive.examples as examples

material_files = examples.download_custom_material()

###############################################################################
# Load the Custom Material Files
# ------------------------------
# The ``load_material`` method on the ``additive`` object loads the files defining a custom material.
custom_material = additive.load_material(
    parameters_file=material_files.material_parameters_file,
    thermal_lookup_file=material_files.thermal_properties_lookup_file,
    characteristic_width_lookup_file=material_files.characteristic_width_lookup_file,
)


###############################################################################
# Use the Custom Material in a Simulation
# ---------------------------------------
# Once the custom material has been loaded, it can be assigned to a simulation input
# object.

input = pyadditive.SingleBeadInput(
    machine=pyadditive.AdditiveMachine(),
    material=custom_material,
    id="single-bead-simulation",
    bead_length=0.001,  # meters
)

# Remove '#' to run the simulation
# additive.simulate(input)
