# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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
Custom material tuning
======================

This example shows how to tune a custom material for use with PyAdditive.
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

from ansys.additive.core import Additive, MaterialTuningInput

additive = Additive()

###############################################################################
# Specify tuning inputs
# ---------------------
# The :class:`MaterialTuningInput` object contains the paths to the files needed to
# tune a material. The ``experiment_data_file`` file is a CSV file containing the
# results of single bead experiments. The ``material_configuration_file`` file is a JSON
# file containing the material parameters. The ``thermal_properties_lookup_file``
# file is a CSV file containing the temperature-dependent properties of the material.
# The ``characteristic_width_lookup_file`` file is an optional CSV file containing
# the melt pool characteristic width at various laser powers and scan speeds.
# If the characteristic width lookup file is not specified, it is generated
# during the tuning process.

# Download the example input files.

import ansys.additive.core.examples as examples

input_files = examples.download_material_tuning_input()

# This code includes the characteristic width lookup file to reduce
# processing time. If a characteristic width lookup file is not available,
# the field can be omitted when creating the MaterialTuningInput object.

input = MaterialTuningInput(
    id="custom-material-tuning",
    experiment_data_file=input_files.experiment_data_file,
    material_configuration_file=input_files.material_configuration_file,
    thermal_properties_lookup_file=input_files.thermal_properties_lookup_file,
    characteristic_width_lookup_file=input_files.characteristic_width_lookup_file,
    allowable_error=0.05,  # allowable difference, as a ratio, between experimental and simulated results
    max_iterations=10,  # maximum number of simulation iterations to perform
    base_plate_temperature=353.15,  # only used when calculating the characteristic width
)

###############################################################################
# Perform material tuning
# ------------------------
# Use the :meth:`~Additive.tune_material` method to perform material tuning.

summary = additive.tune_material(input)

###############################################################################
# Review results
# --------------
# The :class:`MaterialTuningSummary` object contains the results of the material
# tuning process. These results are used in follow-on steps to calculate the
# material parameters needed by PyAdditive. For more information, see the
# Additive documentation referred to earlier.

print(summary)
