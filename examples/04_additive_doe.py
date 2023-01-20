# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
.. _ref_example_doe:

Design Of Experiments
=====================

This tutorial shows how you can use PyAdditive to run a design of experiments (DOE).
For this DOE we will vary laser power and scan speed over multiple single bead
simulations and plot the results.

Units are SI (m, kg, s, K) unless otherwise noted.

First, connect to the Additive service.
"""
import concurrent.futures

from matplotlib.colors import LinearSegmentedColormap as colorMap
import matplotlib.pyplot as plt
import numpy as np

import ansys.additive as pyadditive

additive = pyadditive.Additive()

###############################################################################
# Specify Parameters
# ---------------------------------
# Here we create a list of ``SingleBeadInput`` objects with various laser power
# and scan speed combinations.

bead_length = 0.001
bead_type = pyadditive.BeadType.BEAD_ON_POWDER
material = additive.get_material("17-4PH")
powers = [50, 350, 700]
scan_speeds = [0.35, 1.25, 2.5]
# Use a comprehension to create a list of 9 machines
machines = [
    pyadditive.AdditiveMachine(laser_power=p, scan_speed=s) for p in powers for s in scan_speeds
]
inputs = []
for count, machine in enumerate(machines):
    inputs.append(
        pyadditive.SingleBeadInput(
            id=f"single-bead-doe-{count}",
            material=material,
            machine=machine,
            bead_length=bead_length,
            bead_type=bead_type,
        )
    )

###############################################################################
# Run Simulations
# ---------------
# We run the simulations in parallel and store the summaries as each simulation
# completes.
# *NOTE: At present it is not recommended to run more than 10 concurrent simulations.*
summaries = []
completed = 0
total_simulations = len(inputs)
print(f"Running {total_simulations} simulations")
with concurrent.futures.ThreadPoolExecutor(10) as executor:
    futures = []
    for input in inputs:
        futures.append(executor.submit(additive.simulate, input=input, log_progress=False))
    for future in concurrent.futures.as_completed(futures):
        summaries.append(future.result())
        completed += 1
        print(f"Completed {completed} of {total_simulations} simulations")


###############################################################################
# Plot Individual Meltpool Statistics
# -----------------------------------
summaries.sort(key=lambda s: (s.input.machine.laser_power, s.input.machine.scan_speed))
nrows = 3
ncols = 3
fig, axs = plt.subplots(nrows, ncols, figsize=(15, 15), layout="constrained")
for r in range(nrows):
    for c in range(ncols):
        i = r * nrows + c
        mp = summaries[i].melt_pool
        axs[r][c].plot(mp.laser_x, mp.width, label="width")
        axs[r][c].plot(mp.laser_x, mp.reference_width, label="ref width")
        axs[r][c].plot(mp.laser_x, mp.depth, label="depth")
        axs[r][c].plot(mp.laser_x, mp.reference_depth, label="ref depth")
        axs[r][c].plot(mp.laser_x, mp.length, label="length")
        axs[r][c].legend()
        axs[r][c].set_xlabel(f"Bead Length (m)")  # Add an x-label to the axes.
        axs[r][c].set_ylabel(f"(m)")  # Add a y-label to the axes.
        title = (
            "Power "
            + str(summaries[i].input.machine.laser_power)
            + "W, Scan Speed "
            + str(summaries[i].input.machine.scan_speed)
            + "m/s"
        )
        axs[r][c].set_title(title)  # Add a title to the axes.


###############################################################################
# Plot Meltpool Average Depth Over Width Verses Laser Power And Scan Speed
# ------------------------------------------------------------------------
# Here we create a "watermelon" plot to visualize the optimal laser power
# and scan speed combinations.

# Gather plot values
powers = []
scan_speeds = []
depth_over_width = []

for s in summaries:
    mp = s.melt_pool
    ave_width = np.average(mp.width)
    ave_depth = np.average(mp.depth)
    powers.append(s.input.machine.laser_power)
    scan_speeds.append(s.input.machine.scan_speed)
    depth_over_width.append(ave_depth / ave_width if ave_width else 0)

# Create plot, adjust dwMin and dwMax for desired acceptable range.
dwMin = 0.37
dwMax = 0.6
contour_gradient = []
marker_colors = []
fig, ax = plt.subplots(figsize=(20, 10))
for i in range(len(depth_over_width)):
    if dwMin < depth_over_width[i] < dwMax:
        contour_gradient.append(0)
        marker_colors.append("blue")
    else:
        contour_gradient.append(abs(((dwMax + dwMin) / 2) - depth_over_width[i]))
        marker_colors.append("black")
    txt = "{}".format(round(depth_over_width[i], 2))
    ax.annotate(
        str(txt),
        (scan_speeds[i], powers[i] + 25),
        verticalalignment="top",
        horizontalalignment="center",
    )

colMap = colorMap.from_list("", ["green", "yellow", "red", "red"])
ax.tricontourf(scan_speeds, powers, contour_gradient, cmap=colMap, levels=255)
ax.scatter(scan_speeds, powers, c=marker_colors, marker="d", s=100, facecolor="none")
ax.use_sticky_edges = False
ax.margins(0.075)
ax.set_title("Melt Pool Depth/Width")
ax.set_xlabel(f"Laser Scan Speed (m/s)")
ax.set_ylabel(f"Laser Power (W)")
