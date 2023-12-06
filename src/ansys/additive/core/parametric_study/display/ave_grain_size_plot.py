# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
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
"""Provides a plot for average grain size."""

from __future__ import annotations

import os

import pandas as pd
import panel as pn
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ansys.additive.core import MachineConstants, SimulationStatus, SimulationType
from ansys.additive.core.misc import short_uuid
from ansys.additive.core.parametric_study import ColumnNames, ParametricStudy

from ._common_controls import _common_controls

# Initialize panel for plotly.
pn.extension("plotly")

# Min/Max average grain size
min_ags = None
max_ags = None


def ave_grain_size_plot(ps: ParametricStudy):
    """Plot average grain size for laser power versus scan speed.

    Parameters
    ----------
    ps : ParametricStudy
        Parametric study to plot.

    Returns
    -------
    panel.Row
        Interactive plot.
    """
    global min_ags, max_ags
    df = __data_frame(ps)
    min_ags, max_ags = __min_max_ave_grain_size(df)

    (
        ht_select,
        lt_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
    ) = _common_controls(df)
    col1 = pn.Column(
        lt_select,
        ht_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
        width=200,
    )
    plot_view = pn.bind(
        __update_plot,
        df,
        ht_select,
        lt_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
    )
    plot = pn.Row(
        col1,
        pn.pane.Plotly(plot_view, sizing_mode="stretch_both", min_height=600),
        sizing_mode="stretch_both",
    ).servable()
    if os.getenv("GENERATING_DOCS"):
        name = ave_grain_size_plot.__name__
        plot.save(f"{name}_{short_uuid()}.png")
        plot.__repr__ = lambda: name
    return plot


def __data_frame(ps: ParametricStudy) -> pd.DataFrame:
    df = ps.data_frame()
    df = df[
        (df[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE)
        & (df[ColumnNames.STATUS] == SimulationStatus.COMPLETED)
    ]
    # convert build rate from m^3/s to mm^3/s
    df.loc[:, ColumnNames.BUILD_RATE] *= 1e9
    return df


def __update_plot(
    df: pd.DataFrame,
    ht: float,
    lt: float,
    bd: float,
    sa: float,
    ra: float,
    hs: float,
    sw: float,
) -> dict:
    global min_ags, max_ags

    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=(
            "XY",
            "XZ",
            "YZ",
        ),
        vertical_spacing=0.11,
    )

    x, y, xy, xz, yz = __scatter_data(df, ht, lt, bd, sa, ra, hs, sw)

    xy_scatter = go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        text=[f"{z:.2f}" for z in xy],
        textposition="top center",
        marker=dict(color="darkred", size=__normalized_markers(xy, min_ags, max_ags)),
        cliponaxis=False,
    )
    xz_scatter = go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        text=[f"{z:.2f}" for z in xz],
        textposition="top center",
        marker=dict(color="darkorchid", size=__normalized_markers(xz, min_ags, max_ags)),
        cliponaxis=False,
    )
    yz_scatter = go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        text=[f"{z:.2f}" for z in yz],
        textposition="top center",
        marker=dict(color="steelblue", size=__normalized_markers(yz, min_ags, max_ags)),
        cliponaxis=False,
    )
    fig.add_trace(xy_scatter, row=1, col=1)
    fig.add_trace(xz_scatter, row=1, col=2)
    fig.add_trace(yz_scatter, row=1, col=3)
    fig.update_layout(showlegend=False, title_text="Average Grain Size (µm)")
    min_x = MachineConstants.MIN_SCAN_SPEED if len(x) == 0 else min(x) - 0.1
    max_x = MachineConstants.MAX_SCAN_SPEED if len(x) == 0 else max(x) + 0.1
    fig.update_xaxes(
        title_text="Scan Speed (m/s)",
        showgrid=True,
        gridwidth=1,
        gridcolor="white",
        title_font=dict(size=12),
        range=[min_x, max_x],
    )
    min_y = MachineConstants.MIN_LASER_POWER if len(y) == 0 else min(y) - 20
    max_y = MachineConstants.MAX_LASER_POWER if len(y) == 0 else max(y) + 70
    fig.update_yaxes(
        title_text="Laser Power (W)",
        showgrid=True,
        gridwidth=1,
        gridcolor="white",
        title_font=dict(size=12),
        range=[min_y, max_y],
    )

    return fig


def __normalized_markers(
    x: list[float], v_min: float, v_max: float, m_min: float = 5, m_max: float = 18
) -> list:
    """Normalize a list of values and map them to a range of marker values.

    Parameters
    ----------
    x: list[float]
        Values to normalize.
    v_min: float
        Minimum input value which will map to minimum output value.
    v_max: float
        Maximum input value which will map to maximum output value.
    m_min: float
        Minimum output value.
    m_max: float
        Maximum output value.

    Returns
    -------
    list[float]
        Normalized values.
    """
    if not x:
        return []
    range = v_max - v_min
    if range == 0:
        return [m_max for _ in x]
    scale_factor = m_max - m_min
    normalized = []
    for i in x:
        temp = (((i - v_min) * scale_factor) / range) + m_min
        normalized.append(temp)
    return normalized


def __scatter_data(
    df: pd.DataFrame, ht: float, lt: float, bd: float, sa: float, ra: float, hs: float, sw: float
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    idx = df[
        (df[ColumnNames.LAYER_THICKNESS] == lt)
        & (df[ColumnNames.BEAM_DIAMETER] == bd)
        & (df[ColumnNames.HEATER_TEMPERATURE] == ht)
        & (df[ColumnNames.START_ANGLE] == sa)
        & (df[ColumnNames.ROTATION_ANGLE] == ra)
        & (df[ColumnNames.HATCH_SPACING] == hs)
        & (df[ColumnNames.STRIPE_WIDTH] == sw)
    ].index

    df = df.loc[
        idx,
        [
            ColumnNames.LASER_POWER,
            ColumnNames.SCAN_SPEED,
            ColumnNames.XY_AVERAGE_GRAIN_SIZE,
            ColumnNames.XZ_AVERAGE_GRAIN_SIZE,
            ColumnNames.YZ_AVERAGE_GRAIN_SIZE,
        ],
    ]
    df.sort_values(
        by=[ColumnNames.LASER_POWER, ColumnNames.SCAN_SPEED],
        inplace=True,
    )
    return (
        df[ColumnNames.SCAN_SPEED].tolist(),
        df[ColumnNames.LASER_POWER].tolist(),
        df[ColumnNames.XY_AVERAGE_GRAIN_SIZE].tolist(),
        df[ColumnNames.XZ_AVERAGE_GRAIN_SIZE].tolist(),
        df[ColumnNames.YZ_AVERAGE_GRAIN_SIZE].tolist(),
    )


def __min_max_ave_grain_size(df: pd.DataFrame) -> tuple[float | None, float | None]:
    xy = df[ColumnNames.XY_AVERAGE_GRAIN_SIZE].to_list()
    xz = df[ColumnNames.XZ_AVERAGE_GRAIN_SIZE].to_list()
    yz = df[ColumnNames.YZ_AVERAGE_GRAIN_SIZE].to_list()
    all = xy + xz + yz
    min_ags = min(all) if len(all) > 0 else None
    max_ags = max(all) if len(all) > 0 else None
    return (min_ags, max_ags)
