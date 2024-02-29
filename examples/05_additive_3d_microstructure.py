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
3D Microstructure analysis
###########################

This example shows how to use PyAdditive to determine
the three-dimensional microstructure for a sample coupon
with given material and machine parameters.

Units are SI (m, kg, s, K) unless otherwise noted.
"""
###############################################################################
# Perform required import and connect
# -----------------------------------
# Perform the required import and connect to the Additive service.

import pyvista as pv

from ansys.additive.core import Additive, AdditiveMachine, Microstructure3DInput, SimulationError

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

material = additive.material("17-4PH")

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

machine.scan_speed = 1  # m/s
machine.laser_power = 500  # W

###############################################################################
# Specify inputs for 3D microstructure simulation
# ------------------------------------------------
# Specify microstructure inputs.
input = Microstructure3DInput(
    machine=machine,
    material=material,
    id="micro-3d",
    sample_size_x=0.0001,  # in meters (.1 mm)
    sample_size_y=0.0001,
    sample_size_z=0.0001,
)

###############################################################################
# Run simulation
# --------------
# Use the :meth:`~Additive.simulate` method of the ``additive`` object to run the simulation.
# The returned object is either a :class:`Microstructure3DSummary` object or a
# :class:`SimulationError` object.

summary = additive.simulate(input)
if isinstance(summary, SimulationError):
    raise Exception(summary.message)


###############################################################################
# Plot 3D grain visualization
# ---------------------------
# The ``summary``` object includes a VTK file describing the 3D grain structure.
# The VTK file contains scalar data sets ``GrainNumber``, ``Phi0``,
# ``Phi1``, ``Phi2`` and ``Temperatures``.

# Plot the Phi0 data of the 3D grain structure
cmap = "coolwarm"
ms3d = pv.read(summary.grain_3d_vtk)
ms3d.plot(scalars="Phi0", cmap=cmap)

# Add a cut plane to the plot
plotter = pv.Plotter()
plotter.add_mesh_clip_plane(ms3d, scalars="Phi0", cmap=cmap)
plotter.show()

###############################################################################
# Print average grain sizes
# -------------------------
# The ``summary``` object includes the average grain sizes in the XY, XZ, and YZ
# planes.

print("Average grain size in XY plane: {} µm".format(summary.xy_average_grain_size))
print("Average grain size in XZ plane: {} µm".format(summary.xz_average_grain_size))
print("Average grain size in YZ plane: {} µm".format(summary.yz_average_grain_size))
