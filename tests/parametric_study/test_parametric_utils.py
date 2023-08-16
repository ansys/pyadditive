# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import math

from ansys.additive.parametric_study.parametric_utils import build_rate, energy_density


def test_build_rate_calculates_correctly():
    # arrange
    # act
    # assert
    assert build_rate(2, 3, 4) == 24
    assert build_rate(2, 3) == 6


def test_energy_density_calulcates_correctly():
    # arrange
    # act
    # assert
    assert energy_density(24, 2, 3, 4) == 1
    assert energy_density(6, 2, 3) == 1
    assert math.isnan(energy_density(6, 0, 3, 4))
