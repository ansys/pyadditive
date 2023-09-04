# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Tuple

import numpy as np
import pandas as pd
import panel as pn
import plotly.graph_objects as go

from ansys.additive.core import SimulationStatus, SimulationType
from ansys.additive.core.parametric_study import ColumnNames, ParametricStudy

from ._common_controls import _common_controls

pn.extension("plotly")


def porosity_contour_plot(ps: ParametricStudy):
    """Provides a contour plot of build rate and relative density.

    Parameters
    ----------
    ps : :class:`ParametricStudy <from ansys.additive.core.parametric_study.ParametricStudy>`
        Parametric study to be plotted.

    Returns
    -------
    :class: `panel.Row <panel.Row>`
        A ``Panel Row`` object containing the plot and controls.
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
        show_scatter_cb,
        show_contours_cb,
    ) = __init_controls(df)
    row1 = pn.Column(
        show_scatter_cb,
        show_contours_cb,
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
        show_scatter_cb,
        show_contours_cb,
    )
    plot = pn.Row(
        row1,
        pn.pane.Plotly(plot_view, sizing_mode="stretch_both", min_height=600),
        sizing_mode="stretch_both",
    ).servable()
    return plot


def __data_frame(ps: ParametricStudy) -> pd.DataFrame:
    df = ps.data_frame()
    df = df[
        (df[ColumnNames.TYPE] == SimulationType.POROSITY)
        & (df[ColumnNames.STATUS] == SimulationStatus.COMPLETED)
    ]
    # convert build rate from m^3/s to mm^3/s
    df.loc[:, ColumnNames.BUILD_RATE] *= 1e9
    return df


def __init_controls(df: pd.DataFrame):
    (
        ht_select,
        lt_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
    ) = _common_controls(df)
    show_scatter_cb = pn.widgets.Checkbox(
        name="Relative Density Points", sizing_mode="stretch_width"
    ).servable()
    show_scatter_cb.value = True
    show_contours_cb = pn.widgets.Checkbox(
        name="Relative Density Contours", sizing_mode="stretch_width"
    ).servable()
    show_contours_cb.value = True
    return (
        ht_select,
        lt_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
        show_scatter_cb,
        show_contours_cb,
    )


def __update_plot(
    df: pd.DataFrame,
    ht: float,
    lt: float,
    bd: float,
    sa: float,
    ra: float,
    hs: float,
    sw: float,
    show_scatter: bool,
    show_contours: bool,
) -> dict:
    fig = go.Figure()

    x, y, br, rd = __contour_data(df, ht, lt, bd, sa, ra, hs, sw)
    br_contour = go.Contour(
        x=x,
        y=y,
        z=br,
        contours=dict(showlabels=True, labelfont=dict(size=12, color="black")),
        contours_coloring="lines",
        line=dict(dash="dot", width=2),
        colorscale="Phase",
        colorbar=dict(
            title="Build Rate (mm^3/s)",
            titlefont=dict(size=12),
            titleside="right",
            tickfont=dict(size=12),
            thickness=20,
            len=0.25,
            lenmode="fraction",
            y=0.2,
        ),
        connectgaps=True,
    )
    fig.add_trace(br_contour)

    rd_contour = go.Contour(
        x=x,
        y=y,
        z=rd,
        contours=dict(showlabels=True, labelfont=dict(size=12, color="black")),
        contours_coloring="lines",
        line=dict(dash="solid", width=2),
        colorscale="Rainbow",
        colorbar=dict(
            title="Relative Density",
            titlefont=dict(size=12),
            titleside="right",
            thickness=20,
            tickfont=dict(size=12),
            len=0.25,
            lenmode="fraction",
            y=0.6,
        ),
        connectgaps=True,
        visible=show_contours,
    )
    fig.add_trace(rd_contour)

    scatter_x, scatter_y, rd_scatter = __scatter_data(df, ht, lt, bd, sa, ra, hs, sw)
    scatter = go.Scatter(
        x=scatter_x,
        y=scatter_y,
        mode="markers+text",
        text=[f"{z:.4f}" for z in rd_scatter],
        textposition="top center",
        visible=show_scatter,
        marker=dict(color="slategrey", size=5),
    )
    fig.add_trace(scatter)
    fig.update_layout(
        title=dict(
            text="Relative Density and Build Rate"
        )  # , xanchor="center", yanchor="top", x=0.5, y=0.9)
    )
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


def __contour_data(
    df: pd.DataFrame, ht: float, lt: float, bd: float, sa: float, ra: float, hs: float, sw: float
) -> Tuple[list, list, list, list]:
    """Returns lists of scan speed, laser power, build rate, and relative
    density values."""

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
            ColumnNames.BUILD_RATE,
            ColumnNames.RELATIVE_DENSITY,
        ],
    ]
    df.sort_values(
        by=[ColumnNames.LASER_POWER, ColumnNames.SCAN_SPEED],
        inplace=True,
    )
    speeds = df[ColumnNames.SCAN_SPEED].unique()
    powers = df[ColumnNames.LASER_POWER].unique()
    build_rate_z = []
    relative_density_z = []
    for p in powers:
        br_row = []
        rd_row = []
        for v in speeds:
            if (
                len(
                    df.loc[
                        (df[ColumnNames.LASER_POWER] == p) & (df[ColumnNames.SCAN_SPEED] == v),
                        ColumnNames.BUILD_RATE,
                    ].values
                )
                > 0
            ):
                br_row.append(
                    df.loc[
                        (df[ColumnNames.LASER_POWER] == p) & (df[ColumnNames.SCAN_SPEED] == v),
                        ColumnNames.BUILD_RATE,
                    ].values[0]
                )
            else:
                br_row.append(np.nan)
            if (
                len(
                    df.loc[
                        (df[ColumnNames.LASER_POWER] == p) & (df[ColumnNames.SCAN_SPEED] == v),
                        ColumnNames.RELATIVE_DENSITY,
                    ].values
                )
                > 0
            ):
                rd_row.append(
                    df.loc[
                        (df[ColumnNames.LASER_POWER] == p) & (df[ColumnNames.SCAN_SPEED] == v),
                        ColumnNames.RELATIVE_DENSITY,
                    ].values[0]
                )
            else:
                rd_row.append(np.nan)
        build_rate_z.append(br_row)
        relative_density_z.append(rd_row)
    return (speeds, powers, build_rate_z, relative_density_z)


def __scatter_data(
    df: pd.DataFrame, ht: float, lt: float, bd: float, sa: float, ra: float, hs: float, sw: float
) -> Tuple[list, list, list]:
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
            ColumnNames.BUILD_RATE,
            ColumnNames.RELATIVE_DENSITY,
        ],
    ]
    df.sort_values(
        by=[ColumnNames.LASER_POWER, ColumnNames.SCAN_SPEED],
        inplace=True,
    )
    return (
        df[ColumnNames.SCAN_SPEED].tolist(),
        df[ColumnNames.LASER_POWER].tolist(),
        df[ColumnNames.RELATIVE_DENSITY].tolist(),
    )
