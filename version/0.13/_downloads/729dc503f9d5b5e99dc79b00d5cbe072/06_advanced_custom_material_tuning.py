"""
Custom Material Tuning
======================

This tutorial shows how you can tune a custom material for use with PyAdditive.
Background information and file formats can be found in `the Additive documentation
<https://ansysproducthelpqa.win.ansys.com/account/secured?returnurl=/Views/Secured/corp/v232/en/add_beta/add_science_BETA_material_tuning_tool.html>`_.
To prevent wasted time, the steps described in the Additive documentation should be
reviewed carefully before executing the tuning process below.

Units are SI (m, kg, s, K) unless otherwise noted.

"""
import ansys.additive as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Specify the Tuning Inputs
# -------------------------
# The ``MaterialTuningInput`` object contains the paths to the files needed to
# tune a material. The ``experiment_data_file`` is a CSV file containing the
# results of single bead experiments. The ``material_parameters_file`` is a JSON
# file containing the material parameters. The ``thermal_properties_lookup_file``
# is a CSV file containing the temperature dependent properties of the material.
# The ``characteristic_width_lookup_file`` is an optional CSV file containing
# the melt pool characteristic width at various laser powers and scan speeds.
# If the characteristic width lookup file is not specified, it will be generated
# during the tuning process.
#
# Example input files can be downloaded as shown below.

import ansys.additive.examples as examples

input_files = examples.download_material_tuning_input()

# Below we include the characteristic width lookup file in order to reduce
# processing time. If a characteristic width lookup file is not available,
# the field can be omitted when creating the ``MaterialTuningInput`` object.
input = pyadditive.MaterialTuningInput(
    id="custom-material-tuning",
    experiment_data_file=input_files.experiment_data_file,
    material_parameters_file=input_files.material_parameters_file,
    thermal_properties_lookup_file=input_files.thermal_properties_lookup_file,
    characteristic_width_lookup_file=input_files.characteristic_width_lookup_file,
    allowable_error=0.05,  # allowable difference, as a ratio, between experimental and simulated results
    max_iterations=10,  # maximum number of simulation iterations to perform
    base_plate_temperature=353.15,  # only used when calculating the characteristic width
)

###############################################################################
# Perform the Material Tuning
# ---------------------------
# Material tuning is performed using the ``tune_material`` method.

summary = additive.tune_material(input)

###############################################################################
# Review the Results
# ------------------
# The ``MaterialTuningSummary`` object contains the results of the material
# tuning process. These results are used in follow-on steps to calculate the
# material parameters needed by PyAdditive. See the Additive documentation
# referred to above for details.

print(summary)
