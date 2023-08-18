# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from bokeh.models import Select
import numpy as np

from ansys.additive import MachineConstants
from ansys.additive.parametric_study import ParametricStudy
from ansys.additive.parametric_study.plot.common_selections import CommonSelections


def test_init_with_all_none_param_creates_expected_object():
    # arrange
    ps = ParametricStudy("test")

    # act
    cs = CommonSelections(ps, None, None, None)

    # assert
    assert cs.layer_thickness_select is None
    assert np.isnan(cs.layer_thickness)
    assert cs.heater_temperature_select is None
    assert np.isnan(cs.heater_temperature)
    assert cs.beam_diameter_select is None
    assert np.isnan(cs.beam_diameter)
    assert cs.start_angle_select is None
    assert np.isnan(cs.start_angle)
    assert cs.rotation_angle_select is None
    assert np.isnan(cs.rotation_angle)
    assert cs.hatch_spacing_select is None
    assert np.isnan(cs.hatch_spacing)
    assert cs.stripe_width_select is None
    assert np.isnan(cs.stripe_width)


def test_init_with_param_creates_expected_object():
    # arrange
    ps = ParametricStudy("test")
    ps.generate_porosity_permutations(material_name="material", laser_powers=[100], scan_speeds=[1])

    def callback(attr, old, new):
        pass

    # act
    cs = CommonSelections(
        ps,
        heater_temp_cb=callback,
        layer_thickness_cb=callback,
        beam_diameter_cb=callback,
        start_angle_cb=callback,
        rotation_angle_cb=callback,
        hatch_spacing_cb=callback,
        stripe_width_cb=callback,
    )

    # assert
    assert isinstance(cs.layer_thickness_select, Select)
    assert cs.layer_thickness == MachineConstants.DEFAULT_LAYER_THICKNESS
    assert isinstance(cs.heater_temperature_select, Select)
    assert cs.heater_temperature == MachineConstants.DEFAULT_HEATER_TEMP
    assert isinstance(cs.beam_diameter_select, Select)
    assert cs.beam_diameter == MachineConstants.DEFAULT_BEAM_DIAMETER
    assert isinstance(cs.start_angle_select, Select)
    assert cs.start_angle == MachineConstants.DEFAULT_STARTING_LAYER_ANGLE
    assert isinstance(cs.rotation_angle_select, Select)
    assert cs.rotation_angle == MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE
    assert isinstance(cs.hatch_spacing_select, Select)
    assert cs.hatch_spacing == MachineConstants.DEFAULT_HATCH_SPACING
    assert isinstance(cs.stripe_width_select, Select)
    assert cs.stripe_width == MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH
