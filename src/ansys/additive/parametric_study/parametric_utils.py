# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Optional


def build_rate(
    scan_speed: float, layer_thickness: float, hatch_spacing: Optional[float] = None
) -> float:
    """Calculate the build rate.

    This is an approximate value useful for comparison but not for an accurate prediction
    of build time. The returned value is simply the product of the scan speed, layer thickness,
    and hatch spacing (if provided).

    Parameters
    ----------
    scan_speed : float
        Laser scan speed.
    layer_thickness : float
        Powder deposit layer thickness.
    hatch_spacing : float, optional
        Distance between hatch scan lines.

    Returns
    -------
    float
        The volumetric build rate if hatch spacing is provided,
        otherwise an area build rate. If input units are m/s, m, m,
        the output units are m^3/s or m^2/s.

    """
    if hatch_spacing is None:
        return scan_speed * layer_thickness
    return scan_speed * layer_thickness * hatch_spacing


def energy_density(
    laser_power: float,
    scan_speed: float,
    layer_thickness: float,
    hatch_spacing: Optional[float] = None,
) -> float:
    """Calculate the energy density.

    This is an approximate value useful for comparison. The returned value is simply
    the laser power divided by the build rate. See :method:`build_rate`.

    Parameters
    ----------
    laser_power : float
        Laser power.
    scan_speed : float
        Laser scan speed.
    layer_thickness : float
        Powder deposit layer thickness.
    hatch_spacing : float, optional
        Distance between hatch scan lines.

    Returns
    -------
    float
        The volumetric energy density if hatch spacing is provided,
        otherwise an area energy density. If input units are W, m/s, m, m,
        the output units are J/m^3 or J/m^2.

    """
    br = build_rate(scan_speed, layer_thickness, hatch_spacing)
    return laser_power / br if br else float("nan")
