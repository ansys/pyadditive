# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Callable, Optional, Union

from bokeh.models import Select

from ansys.additive.parametric_study import ColumnNames, ParametricStudy


class CommonSelections:
    """Defines common selection dropdowns for plots used with a parametric study."""

    def __init__(
        self,
        ps: ParametricStudy,
        heater_temp_cb: Union[Callable, None],
        layer_thickness_cb: Union[Callable, None],
        beam_diameter_cb: Union[Callable, None],
        start_angle_cb: Optional[Callable] = None,
        rotation_angle_cb: Optional[Callable] = None,
        hatch_spacing_cb: Optional[Callable] = None,
        stripe_width_cb: Optional[Callable] = None,
    ):
        df = ps.data_frame()

        if heater_temp_cb:
            ht_options = [
                (str(t), f"{t:.0f} °C") for t in df[ColumnNames.HEATER_TEMPERATURE].unique()
            ]
            self._ht_select = Select(
                options=ht_options, value=ht_options[0][0], title="Heater Temperature"
            )
            self._ht_select.on_change("value", heater_temp_cb)
        else:
            self._ht_select = None

        if layer_thickness_cb:
            lt_options = [
                (str(t), f"{t*1e6:.0f} µm") for t in df[ColumnNames.LAYER_THICKNESS].unique()
            ]
            self._lt_select = Select(
                options=lt_options, value=lt_options[0][0], title="Layer Thickness"
            )
            self._lt_select.on_change("value", layer_thickness_cb)
        else:
            self._lt_select = None

        if beam_diameter_cb:
            bd_options = [
                (str(t), f"{t*1e6:.0f} µm") for t in df[ColumnNames.BEAM_DIAMETER].unique()
            ]
            self._bd_select = Select(
                options=bd_options, value=bd_options[0][0], title="Beam Diameter"
            )
            self._bd_select.on_change("value", beam_diameter_cb)
        else:
            self._bd_select = None

        if start_angle_cb:
            sa_options = [(str(t), f"{t:.0f} °") for t in df[ColumnNames.START_ANGLE].unique()]
            self._sa_select = Select(
                options=sa_options, value=sa_options[0][0], title="Start Angle"
            )
            self._sa_select.on_change("value", start_angle_cb)
        else:
            self._sa_select = None

        if rotation_angle_cb:
            ra_options = [(str(t), f"{t:.0f} °") for t in df[ColumnNames.ROTATION_ANGLE].unique()]
            self._ra_select = Select(
                options=ra_options, value=ra_options[0][0], title="Rotation Angle"
            )
            self._ra_select.on_change("value", rotation_angle_cb)
        else:
            self._ra_select = None

        if hatch_spacing_cb:
            hs_options = [
                (str(t), f"{t*1e6:.0f} µm") for t in df[ColumnNames.HATCH_SPACING].unique()
            ]
            self._hs_select = Select(
                options=hs_options, value=hs_options[0][0], title="Hatch Spacing"
            )
            self._hs_select.on_change("value", hatch_spacing_cb)
        else:
            self._hs_select = None

        if stripe_width_cb:
            sw_options = [
                (str(t), f"{t*1e3:.0f} mm") for t in df[ColumnNames.STRIPE_WIDTH].unique()
            ]
            self._sw_select = Select(
                options=sw_options, value=sw_options[0][0], title="Stripe Width"
            )
            self._sw_select.on_change("value", stripe_width_cb)
        else:
            self._sw_select = None

    @property
    def layer_thickness(self) -> float:
        return float(self._lt_select.value) if self._lt_select else float("nan")

    @property
    def layer_thickness_select(self) -> Select:
        return self._lt_select

    @property
    def heater_temperature(self) -> float:
        return float(self._ht_select.value) if self._ht_select else float("nan")

    @property
    def heater_temperature_select(self) -> Select:
        return self._ht_select

    @property
    def beam_diameter(self) -> float:
        return float(self._bd_select.value) if self._bd_select else float("nan")

    @property
    def beam_diameter_select(self) -> Select:
        return self._bd_select

    @property
    def start_angle(self) -> float:
        return float(self._sa_select.value) if self._sa_select else float("nan")

    @property
    def start_angle_select(self) -> Select:
        return self._sa_select

    @property
    def rotation_angle(self) -> float:
        return float(self._ra_select.value) if self._ra_select else float("nan")

    @property
    def rotation_angle_select(self) -> Select:
        return self._ra_select

    @property
    def hatch_spacing(self) -> float:
        return float(self._hs_select.value) if self._hs_select else float("nan")

    @property
    def hatch_spacing_select(self) -> Select:
        return self._hs_select

    @property
    def stripe_width(self) -> float:
        return float(self._sw_select.value) if self._sw_select else float("nan")

    @property
    def stripe_width_select(self) -> Select:
        return self._sw_select
