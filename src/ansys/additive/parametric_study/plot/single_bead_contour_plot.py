# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Tuple

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, LabelSet, LinearColorMapper, RangeSlider, Select
from bokeh.plotting import figure
from bokeh.plotting.contour import contour_data
import numpy as np
import panel as pn

from ansys.additive import MachineConstants, SimulationStatus, SimulationType
from ansys.additive.parametric_study import ColumnNames, ParametricStudy

from .common_selections import CommonSelections

__sb_df = None
__sb_widgets_range_slider = None
__sb_widgets_parameter_select = None
__sb_widgets_cmap = None
__sb_widgets_fig = None
__sb_widgets_contour_renderer = None
__sb_widgets_column_data_source = None
__common_selections = None


def single_bead_contour_plot(ps: ParametricStudy) -> pn.pane.Bokeh:
    """
    Provides a contour plot of a melt pool characteristic with controls to select
    layer thickness and the range of interest of the dependent variable.

    Parameters
    ----------
    ps : :class:`ParametricStudy <ansys.additive.parametric_study.ParametricStudy>`
        Parametric study to be plotted.

    Returns
    -------
    :class: `pn.pane.Bokeh <panel.pane.Bokeh>`
        A Panel pane object containing the plot and controls.
    """

    global __sb_df
    df = ps.data_frame()
    __sb_df = df[
        (df[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD)
        & (df[ColumnNames.STATUS] == SimulationStatus.COMPLETED)
    ]
    __init_controls(ps)
    return __init_plot()


def __get_levels() -> list[float]:
    return [0, 0.1, 0.25, 0.5, 0.75, 1]


def __init_controls(ps: ParametricStudy):
    global __sb_df
    global __sb_widgets_range_slider
    global __sb_widgets_cmap
    global __common_selections
    global __sb_widgets_parameter_select

    # Create parameter selector
    parameter_options = [
        (ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH, "Ref Depth/Ref Width"),
        (ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH, "Length/Width"),
    ]
    __sb_widgets_parameter_select = Select(
        options=parameter_options, value=parameter_options[0][0], title="Parameter of Interest"
    )
    __sb_widgets_parameter_select.on_change("value", __parameter_select_cb)
    # Create range slider
    range_end = 0.1 + __sb_df[__sb_widgets_parameter_select.value].max()
    __sb_widgets_range_slider = RangeSlider(
        title="Range",
        start=0,
        end=range_end,
        value=(0.375 * range_end, 0.75 * range_end),
        step=0.01,
        bar_color="green",
    )
    __sb_widgets_range_slider.on_change("value", __range_slider_cb)

    # Create layer thickness, heater temp, and beam diameter selectors
    __common_selections = CommonSelections(
        ps, __selection_changed_cb, __selection_changed_cb, __selection_changed_cb
    )


def __init_plot() -> pn.pane.Bokeh:
    global __sb_df
    global __sb_widgets_column_data_source
    global __sb_widgets_contour_renderer
    global __sb_widgets_cmap
    global __sb_widgets_fig
    global __sb_widgets_parameter_select

    x, y, z = __get_contour_data(
        __sb_widgets_range_slider.value[0],
        __sb_widgets_range_slider.value[1],
    )

    # Create color map
    palette = ("#1a9641", "#a6d96a", "#ffffbf", "#fdae61", "#d7191c")
    __sb_widgets_cmap = LinearColorMapper(palette=palette, low=0, high=1)

    param_of_interest = __sb_widgets_parameter_select.value
    title_suffix = (
        "ref depth/ref width"
        if param_of_interest == ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH
        else "length/width"
    )
    # Create figure
    __sb_widgets_fig = figure(
        width=600,
        height=600,
        title="Melt pool " + title_suffix,
        x_axis_label="Scan Speed (m/s)",
        y_axis_label="Laser Power (W)",
        x_range=(MachineConstants.MIN_SCAN_SPEED - 0.05, MachineConstants.MAX_SCAN_SPEED + 0.2),
        y_range=(MachineConstants.MIN_LASER_POWER - 20, MachineConstants.MAX_LASER_POWER + 50),
    )
    __sb_widgets_contour_renderer = __sb_widgets_fig.contour(
        x=x,
        y=y,
        z=z,
        levels=__get_levels(),
        fill_color=__sb_widgets_cmap.palette,
        line_color=None,
    )
    lt = __common_selections.layer_thickness
    ht = __common_selections.heater_temperature
    bd = __common_selections.beam_diameter
    idx = __sb_df[
        (__sb_df[ColumnNames.LAYER_THICKNESS] == lt)
        & (__sb_df[ColumnNames.HEATER_TEMPERATURE] == ht)
        & (__sb_df[ColumnNames.BEAM_DIAMETER] == bd)
        & (~__sb_df[param_of_interest].isna())
    ].index
    scatter_x = __sb_df.loc[idx, ColumnNames.SCAN_SPEED].tolist()
    scatter_y = __sb_df.loc[idx, ColumnNames.LASER_POWER].tolist()
    scatter_z = __sb_df.loc[idx, param_of_interest].tolist()
    __sb_widgets_column_data_source = ColumnDataSource(
        data=dict(x=scatter_x, y=scatter_y, z=[f"{z:.2f}" for z in scatter_z])
    )
    __sb_widgets_fig.scatter(
        x="x", y="y", source=__sb_widgets_column_data_source, color="black", size=5
    )
    labels = LabelSet(
        name="SingleBeadLabelSet",
        x="x",
        y="y",
        text="z",
        x_offset=0,
        y_offset=5,
        source=__sb_widgets_column_data_source,
        text_font_size="8pt",
        text_color="black",
    )
    __sb_widgets_fig.add_layout(labels)
    cb = __sb_widgets_contour_renderer.construct_color_bar(
        width=6, major_label_text_font_size="0pt", major_tick_line_color=None
    )
    __sb_widgets_fig.add_layout(cb, "right")

    row2 = row(
        __common_selections.layer_thickness_select,
        __common_selections.heater_temperature_select,
        __common_selections.beam_diameter_select,
    )
    row1 = row(
        __sb_widgets_parameter_select,
        __sb_widgets_range_slider,
    )
    return pn.pane.Bokeh(column(row1, row2, __sb_widgets_fig, sizing_mode="stretch_both"))


def __get_contour_data(min_range: float, max_range: float) -> Tuple[list, list, list]:
    global __common_selections
    global __sb_widgets_parameter_select

    param_of_interest = __sb_widgets_parameter_select.value
    lt = __common_selections.layer_thickness
    bd = __common_selections.beam_diameter
    ht = __common_selections.heater_temperature
    idx = __sb_df[
        (__sb_df[ColumnNames.LAYER_THICKNESS] == lt)
        & (__sb_df[ColumnNames.BEAM_DIAMETER] == bd)
        & (__sb_df[ColumnNames.HEATER_TEMPERATURE] == ht)
    ].index

    df = __sb_df.loc[
        idx,
        [
            ColumnNames.LASER_POWER,
            ColumnNames.SCAN_SPEED,
            param_of_interest,
        ],
    ]
    df.sort_values(
        by=[ColumnNames.LASER_POWER, ColumnNames.SCAN_SPEED],
        inplace=True,
    )
    z_vals = []
    z_max = df[param_of_interest].max()
    powers = df[ColumnNames.LASER_POWER].unique()
    speeds = df[ColumnNames.SCAN_SPEED].unique()
    for p in powers:
        row = []
        for v in speeds:
            if (
                len(
                    df.loc[
                        (df[ColumnNames.LASER_POWER] == p) & (df[ColumnNames.SCAN_SPEED] == v),
                        param_of_interest,
                    ].values
                )
                > 0
            ):
                z = df.loc[
                    (df[ColumnNames.LASER_POWER] == p) & (df[ColumnNames.SCAN_SPEED] == v),
                    param_of_interest,
                ].values[0]
                if z >= min_range and z <= max_range:
                    row.append(0.09)
                else:
                    row.append(0.09 + min(abs(max_range - z) / z_max, abs(min_range - z) / z_max))
            else:
                row.append(np.nan)
        z_vals.append(row)
    return (speeds, powers, z_vals)


def __parameter_select_cb(attrname, old, new):
    global __sb_df
    global __sb_widgets_parameter_select
    global __sb_widgets_range_slider

    range_end = 0.1 + __sb_df[__sb_widgets_parameter_select.value].max()
    __sb_widgets_range_slider.update(
        start=0,
        end=range_end,
        value=(0.375 * range_end, 0.75 * range_end),
    )
    __selection_changed_cb(None, None, None)
    title_suffix = (
        "ref depth/ref width"
        if __sb_widgets_parameter_select.value == ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH
        else "length/width"
    )
    __sb_widgets_fig.title.text = f"Melt pool {title_suffix}"


def __range_slider_cb(attrname, old, new):
    global __sb_widgets_range_slider
    global __sb_widgets_contour_renderer

    speeds, powers, z = __get_contour_data(
        __sb_widgets_range_slider.value[0],
        __sb_widgets_range_slider.value[1],
    )
    data = contour_data(speeds, powers, z, __get_levels())
    __sb_widgets_contour_renderer.set_data(data)
    __sb_widgets_contour_renderer.line_renderer.glyph.line_color = None


def __selection_changed_cb(attrname, old, event):
    __range_slider_cb(None, None, None)
    __update_column_data_source()


def __update_column_data_source():
    global __sb_df
    global __sb_widgets_column_data_source
    global __common_selections
    global __sb_widgets_parameter_select

    param_of_interest = __sb_widgets_parameter_select.value
    lt = __common_selections.layer_thickness
    ht = __common_selections.heater_temperature
    bd = __common_selections.beam_diameter

    idx = __sb_df[
        (__sb_df[ColumnNames.LAYER_THICKNESS] == lt)
        & (__sb_df[ColumnNames.HEATER_TEMPERATURE] == ht)
        & (__sb_df[ColumnNames.BEAM_DIAMETER] == bd)
        & (~__sb_df[param_of_interest].isna())
    ].index
    scatter_x = __sb_df.loc[idx, ColumnNames.SCAN_SPEED].tolist()
    scatter_y = __sb_df.loc[idx, ColumnNames.LASER_POWER].tolist()
    scatter_z = __sb_df.loc[idx, param_of_interest].tolist()
    __sb_widgets_column_data_source.data = dict(
        x=scatter_x,
        y=scatter_y,
        z=[f"{z:.2f}" for z in scatter_z],
    )
