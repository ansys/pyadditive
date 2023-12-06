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
"""Provides interactive plot of porosity results."""

from __future__ import annotations

import math
import os

import numpy as np
import pandas as pd
import panel as pn
import plotly.graph_objects as go

from ansys.additive.core import SimulationStatus, SimulationType
from ansys.additive.core.misc import short_uuid
from ansys.additive.core.parametric_study import ColumnNames, ParametricStudy

from ._common_controls import _common_controls

# global variables
_range_slider = None

pn.extension("plotly")


def porosity_eval_plot(ps: ParametricStudy):
    """Generate a heat map plot of porosity results to determine parametric regions with desirable relative density statistics.

    Parameters
    ----------
    ps : ParametricStudy to plot.

    Returns
    -------
    :class: `panel.Row <panel.Row>`
        Interactive plot.
    """  # noqa
    df = __data_frame(ps)
    (
        ht_select,
        lt_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
        _range_slider,
    ) = __init_controls(df)
    side_bar = pn.Column(
        pn.Spacer(height=50),
        _range_slider,
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
        _range_slider,
    )
    plot = pn.Row(
        side_bar,
        pn.pane.Plotly(plot_view, sizing_mode="stretch_both", min_height=600),
        sizing_mode="stretch_both",
    ).servable()
    if os.getenv("GENERATING_DOCS"):
        name = porosity_eval_plot.__name__
        plot.save(f"{name}_{short_uuid()}.png")
        plot.__repr__ = lambda: name
    return plot


def __data_frame(ps: ParametricStudy) -> pd.DataFrame:
    df = ps.data_frame()
    df = df[
        (df[ColumnNames.TYPE] == SimulationType.POROSITY)
        & (df[ColumnNames.STATUS] == SimulationStatus.COMPLETED)
    ]
    df.update(
        df[
            [
                ColumnNames.RELATIVE_DENSITY,
            ]
        ].fillna(0)
    )
    return df


def __init_controls(df: pd.DataFrame):
    global _range_slider

    (
        ht_select,
        lt_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
    ) = _common_controls(df)
    range_end = 1.0
    _range_slider = pn.widgets.RangeSlider(
        name="Relative density",
        sizing_mode="stretch_width",
        start=0,
        end=range_end,
        value=(0.85 * range_end, 1.0 * range_end),
        step=0.01,
        bar_color="green",
    ).servable()
    return (
        ht_select,
        lt_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
        _range_slider,
    )


def __contour_colorscale() -> list:
    return [
        [0.0, "green"],
        [0.1, "green"],
        [0.15, "yellow"],
        [0.5, "firebrick"],
        [1.0, "firebrick"],
    ]


# @pn.cache
def __update_plot(
    df: pd.DataFrame,
    ht: float,
    lt: float,
    bd: float,
    sa: float,
    ra: float,
    hs: float,
    sw: float,
    range: tuple[float, float],
) -> go.Figure:
    fig = go.Figure()

    x, y, z = __contour_data(df, ht, lt, bd, sa, ra, hs, sw, range)
    contour = go.Heatmap(
        x=x,
        y=y,
        z=z,
        colorscale=__contour_colorscale(),
        showscale=False,
        connectgaps=True,
        hoverinfo="skip",
        zsmooth="best",
    )
    fig.add_trace(contour)

    scatter_x, scatter_y, z_scatter = __scatter_data(df, ht, lt, bd, sa, ra, hs, sw, range)
    scatter = go.Scatter(
        x=scatter_x,
        y=scatter_y,
        mode="markers+text",
        text=[f"<b>{z:.2f}</b>" for z in z_scatter],
        textposition="top center",
        marker=dict(color="black", size=5),
        cliponaxis=False,
    )
    fig.add_trace(scatter)
    title = "Porosity Relative density"
    fig.update_layout(title_text=title, plot_bgcolor="white")
    fig.update_xaxes(
        title_text="Scan Speed (m/s)",
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgray",
        title_font=dict(size=12),
        range=[min(x) - 0.1, max(x) + 0.2],
    )
    fig.update_yaxes(
        title_text="Laser Power (W)",
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgray",
        title_font=dict(size=12),
        range=[min(y) - 20, max(y) + 70],
    )

    return fig


def __contour_data(
    df: pd.DataFrame,
    ht: float,
    lt: float,
    bd: float,
    sa: float,
    ra: float,
    hs: float,
    sw: float,
    range: tuple[float, float],
) -> tuple[list, list, list]:
    """Get lists of scan speed, laser power, and relative density
    values."""

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
            ColumnNames.RELATIVE_DENSITY,
        ],
    ]
    df.sort_values(
        by=[ColumnNames.LASER_POWER, ColumnNames.SCAN_SPEED],
        inplace=True,
    )
    speeds = df[ColumnNames.SCAN_SPEED].unique()
    powers = df[ColumnNames.LASER_POWER].unique()
    z_vals = []
    z_max = df[ColumnNames.RELATIVE_DENSITY].max()
    if math.isclose(z_max, 0, abs_tol=1e-5):
        z_max = 1
    min_range = range[0]
    max_range = range[1]
    for p in powers:
        row = []
        for v in speeds:
            if (
                len(
                    df.loc[
                        (df[ColumnNames.LASER_POWER] == p) & (df[ColumnNames.SCAN_SPEED] == v),
                        ColumnNames.RELATIVE_DENSITY,
                    ].values
                )
                > 0
            ):
                z = df.loc[
                    (df[ColumnNames.LASER_POWER] == p) & (df[ColumnNames.SCAN_SPEED] == v),
                    ColumnNames.RELATIVE_DENSITY,
                ].values[0]
                z = round(z, 2)
                if z >= min_range and z <= max_range:
                    row.append(0.01)
                else:
                    row.append(0.1 + min(abs(max_range - z) / z_max, abs(min_range - z) / z_max))
            else:
                row.append(np.nan)
        z_vals.append(row)
    return (speeds, powers, z_vals)


def __scatter_data(
    df: pd.DataFrame,
    ht: float,
    lt: float,
    bd: float,
    sa: float,
    ra: float,
    hs: float,
    sw: float,
    float,
) -> tuple[list, list, list]:
    idx = df[
        (df[ColumnNames.LAYER_THICKNESS] == lt)
        & (df[ColumnNames.HEATER_TEMPERATURE] == ht)
        & (df[ColumnNames.BEAM_DIAMETER] == bd)
        & (df[ColumnNames.START_ANGLE] == sa)
        & (df[ColumnNames.ROTATION_ANGLE] == ra)
        & (df[ColumnNames.HATCH_SPACING] == hs)
        & (df[ColumnNames.STRIPE_WIDTH] == sw)
        & (~df[ColumnNames.RELATIVE_DENSITY].isna())
    ].index
    scatter_x = df.loc[idx, ColumnNames.SCAN_SPEED].tolist()
    scatter_y = df.loc[idx, ColumnNames.LASER_POWER].tolist()
    scatter_z = df.loc[idx, ColumnNames.RELATIVE_DENSITY].tolist()
    return (
        scatter_x,
        scatter_y,
        scatter_z,
    )
