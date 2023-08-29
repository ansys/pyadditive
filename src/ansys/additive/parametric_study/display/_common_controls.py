# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.

import pandas as pd
import panel as pn

from ansys.additive.parametric_study import ColumnNames


def _common_controls(df: pd.DataFrame):
    ht_options = {
        k: v for (k, v) in [(f"{t:.2f} °C", t) for t in df[ColumnNames.HEATER_TEMPERATURE].unique()]
    }
    ht_select = pn.widgets.Select(
        name="Heater Temperature", options=ht_options, sizing_mode="stretch_width"
    ).servable()
    lt_options = {
        k: v
        for (k, v) in [(f"{t*1e6:.0f} µm", t) for t in df[ColumnNames.LAYER_THICKNESS].unique()]
    }
    lt_select = pn.widgets.Select(
        name="Layer Thickness", options=lt_options, sizing_mode="stretch_width"
    ).servable()
    bd_options = {
        k: v for (k, v) in [(f"{t*1e6:.0f} µm", t) for t in df[ColumnNames.BEAM_DIAMETER].unique()]
    }
    bd_select = pn.widgets.Select(
        name="Beam Diameter", options=bd_options, sizing_mode="stretch_width"
    ).servable()
    sa_options = {
        k: v for (k, v) in [(f"{t:.1f} °", t) for t in df[ColumnNames.START_ANGLE].unique()]
    }
    sa_select = pn.widgets.Select(
        name="Start Angle", options=sa_options, sizing_mode="stretch_width"
    ).servable()
    ra_options = {
        k: v for (k, v) in [(f"{t:.1f} °", t) for t in df[ColumnNames.ROTATION_ANGLE].unique()]
    }
    ra_select = pn.widgets.Select(
        name="Rotation Angle", options=ra_options, sizing_mode="stretch_width"
    ).servable()
    hs_options = {
        k: v for (k, v) in [(f"{t*1e6:.0f} µm", t) for t in df[ColumnNames.HATCH_SPACING].unique()]
    }
    hs_select = pn.widgets.Select(
        name="Hatch Spacing", options=hs_options, sizing_mode="stretch_width"
    ).servable()
    sw_options = {
        k: v for (k, v) in [(f"{t*1e3:.0f} mm", t) for t in df[ColumnNames.STRIPE_WIDTH].unique()]
    }
    sw_select = pn.widgets.Select(
        name="Stripe Width", options=sw_options, sizing_mode="stretch_width"
    ).servable()
    return (
        ht_select,
        lt_select,
        bd_select,
        sa_select,
        ra_select,
        hs_select,
        sw_select,
    )
