# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Tuple

import numpy as np
import pandas as pd
import panel as pn
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ansys.additive import SimulationStatus, SimulationType
from ansys.additive.parametric_study import ColumnNames, ParametricStudy

from ._common_controls import _common_controls

pn.extension("plotly")


def ave_grain_size_plot(ps: ParametricStudy):
    """Generates a contour plot of build rate and relative density.

    Parameters
    ----------
    ps : :class:`ParametricStudy <ansys.additive.parametric_study.ParametricStudy>`
        Parametric study to plot.

    Returns
    -------
    :class: `panel.Row <panel.Row>`
        Panel row containing the plot and controls.
    """
    df = __data_frame(ps)
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
        max_width=200,
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
) -> dict:
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
    np_xy = np.array(xy)
    xy_norm = np_xy / np.linalg.norm(np_xy)
    xy_scatter = go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        text=[f"{z:.2f}" for z in xy],
        textposition="top center",
        marker=dict(color="darkred", size=__normalize(xy)),
        cliponaxis=False,
    )
    xz_scatter = go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        text=[f"{z:.2f}" for z in xz],
        textposition="top center",
        marker=dict(color="darkorchid", size=__normalize(xz)),
        cliponaxis=False,
    )
    yz_scatter = go.Scatter(
        x=x,
        y=y,
        mode="markers+text",
        text=[f"{z:.2f}" for z in yz],
        textposition="top center",
        marker=dict(color="steelblue", size=__normalize(yz)),
        cliponaxis=False,
    )
    fig.add_trace(xy_scatter, row=1, col=1)
    fig.add_trace(xz_scatter, row=1, col=2)
    fig.add_trace(yz_scatter, row=1, col=3)
    fig.update_layout(showlegend=False, title_text="Average Grain Size (µm)")
    fig.update_xaxes(
        title_text="Scan Speed (m/s)",
        showgrid=True,
        gridwidth=1,
        gridcolor="white",
        title_font=dict(size=12),
        range=[min(x) - 0.1, max(x) + 0.1],
    )
    fig.update_yaxes(
        title_text="Laser Power (W)",
        showgrid=True,
        gridwidth=1,
        gridcolor="white",
        title_font=dict(size=12),
        range=[min(y) - 20, max(y) + 70],
    )

    return fig


def __normalize(x: list, t_min: float = 5, t_max: float = 18) -> list:
    norm_arr = []
    diff = t_max - t_min
    diff_arr = max(x) - min(x)
    for i in x:
        temp = (((i - min(x)) * diff) / diff_arr) + t_min
        norm_arr.append(temp)
    return norm_arr


def __scatter_data(
    df: pd.DataFrame, ht: float, lt: float, bd: float, sa: float, ra: float, hs: float, sw: float
) -> Tuple[list, list, list, list, list]:
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
