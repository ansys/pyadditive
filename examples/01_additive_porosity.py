# Copyright (C) 2022 - 2025 ANSYS, Inc. and/or its affiliates.
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
Porosity analysis
=================

This example shows how to use PyAdditive to determine
porosity for a given material and machine parameter combinations.

Units are SI (m, kg, s, K) unless otherwise noted.
"""
###############################################################################
# Perform required import and connect
# -----------------------------------
# Perform the required import and connect to the Additive service.

from ansys.additive.core import (
    Additive,
    AdditiveMachine,
    PorosityInput,
    SimulationError,
)

additive = Additive()

###############################################################################
# Select material
# ---------------
# Select a material. You can use the :meth:`~Additive.materials_list` method to
# obtain a list of available materials.

print("Available material names: {}".format(additive.materials_list()))

###############################################################################
# You can obtain the parameters for a single material by passing a name
# from the materials list to the :meth:`~Additive.material` method.

material = additive.material("316L")

###############################################################################
# Specify machine parameters
# --------------------------
# Specify machine parameters by first creating an :class:`AdditiveMachine` object
# and then assigning the desired values. All values are in SI units (m, kg, s, K)
# unless otherwise noted.

machine = AdditiveMachine()

# Show available parameters
print(machine)

###############################################################################
# Set laser power and scan speed
# ------------------------------
# Set the laser power and scan speed.

machine.scan_speed = 1.2  # m/s
machine.laser_power = 250  # W

###############################################################################
# Specify inputs for porosity simulation
# --------------------------------------
# Create a :class:`PorosityInput` object containing the desired simulation parameters.

input = PorosityInput(
    machine=machine,
    material=material,
    size_x=0.001,  # meters
    size_y=0.001,
    size_z=0.001,
)

###############################################################################
# Run simulation
# --------------
# Use the :meth:`~Additive.simulate` method of the ``additive`` object to run the simulation.
# The returned object is either a :class:`PorositySummary` object
# containing the input and the relative density of the simulated sample or a
# :class:`SimulationError` object.

summary = additive.simulate(input)
if isinstance(summary, SimulationError):
    raise Exception(summary.message)

###############################################################################
# Print relative density
# ----------------------

print(f"For {summary.input.material.name} with \n", summary.input.machine)
print(f"\n    relative density = {round(summary.relative_density, 5)}")

###############################################################################
# Print the simulation logs
# -------------------------
# To print the simulation logs, use the :meth:`~PorositySummary.logs` property.

print(summary.logs)
