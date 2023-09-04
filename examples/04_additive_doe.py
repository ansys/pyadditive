# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
Design of experiments
=====================

This example shows how you can use PyAdditive to run a design of experiments (DOE).
For this DOE, laser power and scan speed are varied over multiple single bead
simulations and results are plotted.

Units are SI (m, kg, s, K) unless otherwise noted.
"""
###############################################################################
# Perform required import and connect
# -----------------------------------
# Perform the required import and connect to the Additive service.

# from matplotlib.colors import LinearSegmentedColormap as colorMap
# import matplotlib.pyplot as plt
# import numpy as np

# import ansys.additive.core as pyadditive

# additive = pyadditive.Additive()

###############################################################################
# Specify parameters
# -------------------
# Create a list of ``SingleBeadInput`` objects with various laser power
# and scan speed combinations.

# bead_length = 0.001
# material = additive.get_material("17-4PH")
# initial_powers = [50, 350, 700]
# initial_scan_speeds = [0.35, 1.25, 2.5]
# # Use a comprehension to create a list of 9 machines
# machines = [
#     pyadditive.AdditiveMachine(laser_power=p, scan_speed=s)
#     for p in initial_powers
#     for s in initial_scan_speeds
# ]
# inputs = []
# for count, machine in enumerate(machines):
#     inputs.append(
#         pyadditive.SingleBeadInput(
#             id=f"single-bead-doe-{count}",
#             material=material,
#             machine=machine,
#             bead_length=bead_length,
#         )
#     )

# ###############################################################################
# Run simulation
# --------------
# Use the ``simulate`` method of the ``additive`` object to run the simulation.
# The list of summaries returned here are of the :class:`SingleBeadSummary` type.

# summaries = additive.simulate(inputs)

###############################################################################
# Plot melt pool statistics
# -------------------------
# Plot the indidivual melt pool statistics.

# import plotly.graph_objects as go
# summaries.sort(key=lambda s: (s.input.machine.laser_power, s.input.machine.scan_speed))

# traces = []
# buttons = [
#     dict(
#         label="All",
#         method="restyle",
#         args=[{"visible": True}],
#         args2=[{"visible": False}]),
# ]
# for summary in sb_summaries:
#     meltpool = summary.melt_pool
#     title = (
# f"{summary.input.machine.laser_power} W, {summary.input.machine.scan_speed} m/s,
# {summary.input.machine.layer_thickness * 1e6} um"
# )
#     # xaxis labelalias for hover text?
#     traces.append(go.Scatter(x=meltpool.laser_x, y=meltpool.width, name=f"{title} width", visible=False))
#     traces.append(go.Scatter(x=meltpool.laser_x, y=meltpool.depth, name=f"{title} depth", visible=False))
#     traces.append(go.Scatter(x=meltpool.laser_x, y=meltpool.length, name=f"{title} length", visible=False))
#     traces.append(go.Scatter(x=meltpool.laser_x,
# y=meltpool.reference_width, name=f"{title} ref width", visible=False))
#     traces.append(go.Scatter(x=meltpool.laser_x,
# y=meltpool.reference_depth, name=f"{title} ref depth", visible=False))
#     buttons.append(
#         dict(
#             label=title,
#             method="restyle",
#             args=[{"visible": True}, [i for i, x in enumerate(traces) if title in x.name]],
#             args2=[{"visible": False}, [i for i, x in enumerate(traces) if title in x.name]],
#         )
#     )


# layout = go.Layout(
#     updatemenus=[
#         dict(
#             buttons = buttons,
#             type = "buttons",
#             direction = "down",
#             x = 0,
#             y = 1.1,
#             xanchor = "right",
#             yanchor = "top",
#             pad=dict(r=100, t=40),
#             showactive = True,
#         )
#     ],
#     title="Melt Pool Dimensions (toggle buttons to view individual melt pool dimensions)",

#     showlegend=True,
#     xaxis=dict(
#         title="meters",
#         range=[0, max(sb_summaries[0].melt_pool.laser_x)]
#     ),
#     yaxis=dict(
#         title="meters",
#         range=[0, sb_summaries[0].input.bead_length*1.05],
#     ),
#     margin=dict(l=200, r=20, t=20, b=20),
# )

# fig = go.Figure(data=traces, layout=layout)
# fig.update_layout(hovermode="x")
# #fig.data[0].name
# fig.show()


# ###############################################################################
# Plot melt pool average depth over width verses laser power and scan speed
# -------------------------------------------------------------------------
# Create a "watermelon" plot to visualize the optimal laser power
# and scan speed combinations.

# # Gather plot values
# powers = []
# scan_speeds = []
# depth_over_width = []

# for s in summaries:
#     mp = s.melt_pool
#     ave_width = np.average(mp.width)
#     ave_depth = np.average(mp.depth)
#     powers.append(s.input.machine.laser_power)
#     scan_speeds.append(s.input.machine.scan_speed)
#     depth_over_width.append(ave_depth / ave_width if ave_width else 0)

# # Create plot, adjust dwMin and dwMax for desired acceptable range.
# dwMin = 0.37
# dwMax = 0.6
# contour_gradient = []
# marker_colors = []
# fig, ax = plt.subplots(figsize=(20, 10))
# for i in range(len(depth_over_width)):
#     if dwMin < depth_over_width[i] < dwMax:
#         contour_gradient.append(0)
#         marker_colors.append("blue")
#     else:
#         contour_gradient.append(abs(((dwMax + dwMin) / 2) - depth_over_width[i]))
#         marker_colors.append("black")
#     txt = "{}".format(round(depth_over_width[i], 2))
#     ax.annotate(
#         str(txt),
#         (scan_speeds[i], powers[i] + 25),
#         verticalalignment="top",
#         horizontalalignment="center",
#     )

# colMap = colorMap.from_list("", ["green", "yellow", "red", "red"])
# ax.tricontourf(scan_speeds, powers, contour_gradient, cmap=colMap, levels=255)
# ax.scatter(scan_speeds, powers, c=marker_colors, marker="d", s=100, facecolor="none")
# ax.use_sticky_edges = False
# ax.margins(0.075)
# ax.set_title("Melt Pool Depth/Width")
# ax.set_xlabel(f"Laser Scan Speed (m/s)")
# ax.set_ylabel(f"Laser Power (W)")
