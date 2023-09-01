# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from os import path

import pytest

from ansys.additive.core.material import (
    AdditiveMaterial,
    CharacteristicWidthDataPoint,
    CharacteristicWidthDataPointMessage,
    MaterialMessage,
    ThermalPropertiesDataPoint,
    ThermalPropertiesDataPointMessage,
)
from tests import test_utils


def test_CharacteristicWidthDataPoint_setters_raise_exception_for_invalid_value():
    # arrange
    props = ["characteristic_width", "laser_power", "scan_speed"]
    point = CharacteristicWidthDataPoint()

    # act, assert
    for p in props:
        with pytest.raises(ValueError, match=".* must not be negative"):
            setattr(point, p, -1)


def test_CharacteristicWidthDataPoint_repr_returns_expected_string():
    # arrange
    point = CharacteristicWidthDataPoint(laser_power=2, scan_speed=3, characteristic_width=1)
    expected_str = (
        "CharacteristicWidthDataPoint\nlaser_power: 2\nscan_speed: 3\ncharacteristic_width: 1\n"
    )

    # act, assert
    assert expected_str == point.__repr__()


def test_from_characteristic_width_data_point_message_creates_CharacteristicWidthDataPoint():
    # arrange
    msg = CharacteristicWidthDataPointMessage(
        characteristic_width=1,
        laser_power=2,
        scan_speed=3,
    )

    # act
    point = CharacteristicWidthDataPoint._from_characteristic_width_data_point_message(msg)

    # assert
    assert isinstance(point, CharacteristicWidthDataPoint)
    assert point.characteristic_width == 1
    assert point.laser_power == 2
    assert point.scan_speed == 3


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        CharacteristicWidthDataPoint(),
    ],
)
def test_from_characteristic_width_data_point_message_raises_exception_for_invalid_type(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(
        ValueError,
        match="Invalid message object passed to from_characteristic_width_data_point_message()",
    ):
        CharacteristicWidthDataPoint._from_characteristic_width_data_point_message(invalid_obj)


def test_to_characteristic_width_data_point_message_returns_CharacteristicWidthDataPointMessage():
    # arrange
    point = CharacteristicWidthDataPoint(
        characteristic_width=1,
        laser_power=2,
        scan_speed=3,
    )

    # act
    msg = point._to_characteristic_width_data_point_message()

    # assert
    assert isinstance(msg, CharacteristicWidthDataPointMessage)
    assert msg.characteristic_width == 1
    assert msg.laser_power == 2
    assert msg.scan_speed == 3


def test_CharacteristicWidthDataPoint_eq():
    # arrange
    point = CharacteristicWidthDataPoint()
    not_point = CharacteristicWidthDataPoint(laser_power=1, scan_speed=2, characteristic_width=3)

    # act, assert
    assert point == CharacteristicWidthDataPoint()
    assert point != CharacteristicWidthDataPointMessage()
    assert point != not_point


def test_CharacteristicWidthDataPoint_setters():
    # arrange
    point = CharacteristicWidthDataPoint()
    point.laser_power = 1
    point.scan_speed = 2
    point.characteristic_width = 3

    # act, assert
    assert point.laser_power == 1
    assert point.scan_speed == 2
    assert point.characteristic_width == 3


def test_ThermalPropertiesDataPoint_setters_raise_exception_for_invalid_value():
    # arrange
    props = ["density", "density_ratio", "temperature"]
    point = ThermalPropertiesDataPoint()

    # act, assert
    for p in props:
        with pytest.raises(ValueError, match=".* must not be negative"):
            setattr(point, p, -1)


def test_ThermalPropertiesDataPoint_repr_returns_expected_string():
    # arrange
    point = ThermalPropertiesDataPoint(
        density=1,
        density_ratio=2,
        specific_heat=3,
        specific_heat_ratio=4,
        temperature=5,
        thermal_conductivity=6,
        thermal_conductivity_ratio=7,
    )
    expected_str = (
        "ThermalPropertiesDataPoint\ndensity: 1\ndensity_ratio: 2\nspecific_heat: 3\n"
        "specific_heat_ratio: 4\ntemperature: 5\nthermal_conductivity: 6\nthermal_conductivity_ratio: 7\n"
    )

    # act, assert
    assert expected_str == point.__repr__()


def test_ThermalPropertiesDataPoint_eq():
    # arrange
    point = ThermalPropertiesDataPoint()
    not_point = ThermalPropertiesDataPoint(
        density=1,
        density_ratio=2,
        specific_heat=3,
        specific_heat_ratio=4,
        temperature=5,
        thermal_conductivity=6,
        thermal_conductivity_ratio=7,
    )

    # act, assert
    assert point == ThermalPropertiesDataPoint()
    assert point != ThermalPropertiesDataPointMessage()
    assert point != not_point


def test_ThermalPropertiesDataPoint_setters():
    # arrange
    point = ThermalPropertiesDataPoint()
    point.density = 1
    point.density_ratio = 2
    point.specific_heat = 3
    point.specific_heat_ratio = 4
    point.temperature = 5
    point.thermal_conductivity = 6
    point.thermal_conductivity_ratio = 7

    # act, assert
    assert point.density == 1
    assert point.density_ratio == 2
    assert point.specific_heat == 3
    assert point.specific_heat_ratio == 4
    assert point.temperature == 5
    assert point.thermal_conductivity == 6
    assert point.thermal_conductivity_ratio == 7


def test_from_thermal_properties_data_point_message_creates_ThermalPropertiesDataPoint():
    # arrange
    msg = ThermalPropertiesDataPointMessage(
        density=1,
        density_ratio=2,
        specific_heat=3,
        specific_heat_ratio=4,
        temperature=5,
        thermal_conductivity=6,
        thermal_conductivity_ratio=7,
    )

    # act
    point = ThermalPropertiesDataPoint._from_thermal_properties_data_point_message(msg)

    # assert
    assert isinstance(point, ThermalPropertiesDataPoint)
    assert point.density == 1
    assert point.density_ratio == 2
    assert point.specific_heat == 3
    assert point.specific_heat_ratio == 4
    assert point.temperature == 5
    assert point.thermal_conductivity == 6
    assert point.thermal_conductivity_ratio == 7


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        ThermalPropertiesDataPoint(),
    ],
)
def test_from_thermal_properties_data_point_message_raises_exception_for_invalid_type(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(
        ValueError,
        match="Invalid message object passed to from_thermal_properties_data_point_message()",
    ):
        ThermalPropertiesDataPoint._from_thermal_properties_data_point_message(invalid_obj)


def test_to_thermal_properties_data_point_message_returns_ThermalPropertiesDataPointMessage():  # noqa: E501
    # arrange
    point = ThermalPropertiesDataPoint(
        density=1,
        density_ratio=2,
        specific_heat=3,
        specific_heat_ratio=4,
        temperature=5,
        thermal_conductivity=6,
        thermal_conductivity_ratio=7,
    )

    # act
    msg = point._to_thermal_properties_data_point_message()

    # assert
    assert isinstance(msg, ThermalPropertiesDataPointMessage)
    assert msg.density == 1
    assert msg.density_ratio == 2
    assert msg.specific_heat == 3
    assert msg.specific_heat_ratio == 4
    assert msg.temperature == 5
    assert msg.thermal_conductivity == 6
    assert msg.thermal_conductivity_ratio == 7


@pytest.mark.parametrize(
    "invalid_obj",
    [
        int(1),
        None,
        AdditiveMaterial(),
    ],
)
def test_from_material_message_raises_exception_for_invalid_type(invalid_obj):
    # arrange, act, assert
    with pytest.raises(
        ValueError, match="Invalid message object passed to from_material_message()"
    ) as exc_info:
        AdditiveMaterial._from_material_message(invalid_obj)


def test_AdditiveMaterial_eq():
    # arrange
    material = AdditiveMaterial()
    not_material = AdditiveMaterial(
        absorptivity_maximum=1,
        absorptivity_minimum=2,
        absorptivity_powder_coefficient_a=3,
        absorptivity_powder_coefficient_b=4,
        absorptivity_solid_coefficient_a=5,
        absorptivity_solid_coefficient_b=6,
        anisotropic_strain_coefficient_parallel=7,
        anisotropic_strain_coefficient_perpendicular=8,
        anisotropic_strain_coefficient_z=9,
        elastic_modulus=10,
        hardening_factor=11,
        liquidus_temperature=12,
        material_yield_strength=13,
        name="test-material",
        nucleation_constant_bulk=14,
        nucleation_constant_interface=15,
        thermal_properties_data=[
            ThermalPropertiesDataPoint(
                density=1,
                density_ratio=2,
                specific_heat=3,
                specific_heat_ratio=4,
                temperature=5,
                thermal_conductivity=6,
                thermal_conductivity_ratio=7,
            )
        ],
    )

    # act, assert
    assert material == AdditiveMaterial()
    assert material != MaterialMessage()
    assert material != not_material


def test_characteristic_width_data_setter_raises_exception_for_nonsequence_type():
    # arrange
    material = AdditiveMaterial()

    # act, assert
    with pytest.raises(TypeError, match="Invalid object type") as exc_info:
        material.characteristic_width_data = CharacteristicWidthDataPoint()


def test_characteristic_width_data_setter_assigns_characteristic_width_data_points():
    # arrange
    material = AdditiveMaterial()
    data_points = [
        CharacteristicWidthDataPoint(
            laser_power=1,
            characteristic_width=2,
        ),
        CharacteristicWidthDataPoint(
            scan_speed=3,
            characteristic_width=4,
        ),
    ]

    # act
    material.characteristic_width_data = data_points

    # assert
    assert material.characteristic_width_data == data_points


def test_thermal_properties_data_setter_raises_exception_for_nonsequence_type():
    # arrange
    material = AdditiveMaterial()

    # act, assert
    with pytest.raises(TypeError, match="Invalid object type") as exc_info:
        material.thermal_properties_data = ThermalPropertiesDataPoint()


def test_thermal_properties_data_setter_assigns_thermal_properties_data_points():
    # arrange
    material = AdditiveMaterial()
    data_points = [
        ThermalPropertiesDataPoint(density=1, specific_heat=2),
        ThermalPropertiesDataPoint(density_ratio=3, thermal_conductivity=4),
    ]

    # act
    material.thermal_properties_data = data_points

    # assert
    assert material.thermal_properties_data == data_points


def test_from_material_message_creates_AdditiveMaterial():
    # arrange
    msg = MaterialMessage(
        absorptivity_maximum=1,
        absorptivity_minimum=2,
        absorptivity_powder_coefficient_a=3,
        absorptivity_powder_coefficient_b=4,
        absorptivity_solid_coefficient_a=5,
        absorptivity_solid_coefficient_b=6,
        anisotropic_strain_coefficient_parallel=7,
        anisotropic_strain_coefficient_perpendicular=8,
        anisotropic_strain_coefficient_z=9,
        elastic_modulus=10,
        hardening_factor=11,
        liquidus_temperature=12,
        material_yield_strength=13,
        name="test-material",
        nucleation_constant_bulk=14,
        nucleation_constant_interface=15,
        penetration_depth_maximum=16,
        penetration_depth_minimum=17,
        penetration_depth_powder_coefficient_a=18,
        penetration_depth_powder_coefficient_b=19,
        penetration_depth_solid_coefficient_a=20,
        penetration_depth_solid_coefficient_b=21,
        poisson_ratio=22,
        powder_packing_density=23,
        purging_gas_convection_coefficient=24,
        solid_density_at_room_temperature=25,
        solid_specific_heat_at_room_temperature=26,
        solid_thermal_conductivity_at_room_temperature=27,
        solidus_temperature=28,
        strain_scaling_factor=29,
        support_yield_strength_ratio=30,
        thermal_expansion_coefficient=31,
        vaporization_temperature=32,
    )
    msg.characteristic_width_data_points.append(
        CharacteristicWidthDataPointMessage(
            characteristic_width=1,
            laser_power=2,
            scan_speed=3,
        )
    )
    msg.thermal_properties_data_points.append(
        ThermalPropertiesDataPointMessage(
            density=1,
            density_ratio=2,
            specific_heat=3,
            specific_heat_ratio=4,
            temperature=5,
            thermal_conductivity=6,
            thermal_conductivity_ratio=7,
        )
    )

    # act
    am = AdditiveMaterial._from_material_message(msg)

    # assert
    assert isinstance(am, AdditiveMaterial)
    assert am.absorptivity_maximum == 1
    assert am.absorptivity_minimum == 2
    assert am.absorptivity_powder_coefficient_a == 3
    assert am.absorptivity_powder_coefficient_b == 4
    assert am.absorptivity_solid_coefficient_a == 5
    assert am.absorptivity_solid_coefficient_b == 6
    assert am.anisotropic_strain_coefficient_parallel == 7
    assert am.anisotropic_strain_coefficient_perpendicular == 8
    assert am.anisotropic_strain_coefficient_z == 9
    assert am.elastic_modulus == 10
    assert am.hardening_factor == 11
    assert am.liquidus_temperature == 12
    assert am.material_yield_strength == 13
    assert am.name == "test-material"
    assert am.nucleation_constant_bulk == 14
    assert am.nucleation_constant_interface == 15
    assert am.penetration_depth_maximum == 16
    assert am.penetration_depth_minimum == 17
    assert am.penetration_depth_powder_coefficient_a == 18
    assert am.penetration_depth_powder_coefficient_b == 19
    assert am.penetration_depth_solid_coefficient_a == 20
    assert am.penetration_depth_solid_coefficient_b == 21
    assert am.poisson_ratio == 22
    assert am.powder_packing_density == 23
    assert am.purging_gas_convection_coefficient == 24
    assert am.solid_density_at_room_temperature == 25
    assert am.solid_specific_heat_at_room_temperature == 26
    assert am.solid_thermal_conductivity_at_room_temperature == 27
    assert am.solidus_temperature == 28
    assert am.strain_scaling_factor == 29
    assert am.support_yield_strength_ratio == 30
    assert am.thermal_expansion_coefficient == 31
    assert am.vaporization_temperature == 32
    assert len(am.characteristic_width_data) == 1
    cw = am.characteristic_width_data[0]
    assert cw.characteristic_width == 1
    assert cw.laser_power == 2
    assert cw.scan_speed == 3
    assert len(am.thermal_properties_data) == 1
    tc = am.thermal_properties_data[0]
    assert tc.density == 1
    assert tc.density_ratio == 2
    assert tc.specific_heat == 3
    assert tc.specific_heat_ratio == 4
    assert tc.temperature == 5
    assert tc.thermal_conductivity == 6
    assert tc.thermal_conductivity_ratio == 7


def test_to_material_message_returns_MaterialMessage():
    # arrange
    am = AdditiveMaterial()
    am.absorptivity_maximum = 1
    am.absorptivity_minimum = 2
    am.absorptivity_powder_coefficient_a = 3
    am.absorptivity_powder_coefficient_b = 4
    am.absorptivity_solid_coefficient_a = 5
    am.absorptivity_solid_coefficient_b = 6
    am.anisotropic_strain_coefficient_parallel = 7
    am.anisotropic_strain_coefficient_perpendicular = 8
    am.anisotropic_strain_coefficient_z = 9
    am.elastic_modulus = 10
    am.hardening_factor = 11
    am.liquidus_temperature = 12
    am.material_yield_strength = 13
    am.name = "test-material"
    am.nucleation_constant_bulk = 14
    am.nucleation_constant_interface = 15
    am.penetration_depth_maximum = 16
    am.penetration_depth_minimum = 17
    am.penetration_depth_powder_coefficient_a = 18
    am.penetration_depth_powder_coefficient_b = 19
    am.penetration_depth_solid_coefficient_a = 20
    am.penetration_depth_solid_coefficient_b = 21
    am.poisson_ratio = 22
    am.powder_packing_density = 23
    am.purging_gas_convection_coefficient = 24
    am.solid_density_at_room_temperature = 25
    am.solid_specific_heat_at_room_temperature = 26
    am.solid_thermal_conductivity_at_room_temperature = 27
    am.solidus_temperature = 28
    am.strain_scaling_factor = 29
    am.support_yield_strength_ratio = 30
    am.thermal_expansion_coefficient = 31
    am.vaporization_temperature = 32
    am.characteristic_width_data.append(
        CharacteristicWidthDataPoint(
            characteristic_width=1,
            laser_power=2,
            scan_speed=3,
        )
    )
    am.thermal_properties_data.append(
        ThermalPropertiesDataPoint(
            density=1,
            density_ratio=2,
            specific_heat=3,
            specific_heat_ratio=4,
            temperature=5,
            thermal_conductivity=6,
            thermal_conductivity_ratio=7,
        )
    )

    # act
    msg = am._to_material_message()

    assert isinstance(msg, MaterialMessage)
    assert msg.absorptivity_maximum == 1
    assert msg.absorptivity_minimum == 2
    assert msg.absorptivity_powder_coefficient_a == 3
    assert msg.absorptivity_powder_coefficient_b == 4
    assert msg.absorptivity_solid_coefficient_a == 5
    assert msg.absorptivity_solid_coefficient_b == 6
    assert msg.anisotropic_strain_coefficient_parallel == 7
    assert msg.anisotropic_strain_coefficient_perpendicular == 8
    assert msg.anisotropic_strain_coefficient_z == 9
    assert msg.elastic_modulus == 10
    assert msg.hardening_factor == 11
    assert msg.liquidus_temperature == 12
    assert msg.material_yield_strength == 13
    assert msg.name == "test-material"
    assert msg.nucleation_constant_bulk == 14
    assert msg.nucleation_constant_interface == 15
    assert msg.penetration_depth_maximum == 16
    assert msg.penetration_depth_minimum == 17
    assert msg.penetration_depth_powder_coefficient_a == 18
    assert msg.penetration_depth_powder_coefficient_b == 19
    assert msg.penetration_depth_solid_coefficient_a == 20
    assert msg.penetration_depth_solid_coefficient_b == 21
    assert msg.poisson_ratio == 22
    assert msg.powder_packing_density == 23
    assert msg.purging_gas_convection_coefficient == 24
    assert msg.solid_density_at_room_temperature == 25
    assert msg.solid_specific_heat_at_room_temperature == 26
    assert msg.solid_thermal_conductivity_at_room_temperature == 27
    assert msg.solidus_temperature == 28
    assert msg.strain_scaling_factor == 29
    assert msg.support_yield_strength_ratio == 30
    assert msg.thermal_expansion_coefficient == 31
    assert msg.vaporization_temperature == 32
    assert len(msg.characteristic_width_data_points) == 1
    cw = msg.characteristic_width_data_points[0]
    assert cw.characteristic_width == 1
    assert cw.laser_power == 2
    assert cw.scan_speed == 3
    assert len(msg.thermal_properties_data_points) == 1
    tc = msg.thermal_properties_data_points[0]
    assert tc.density == 1
    assert tc.density_ratio == 2
    assert tc.specific_heat == 3
    assert tc.specific_heat_ratio == 4
    assert tc.temperature == 5
    assert tc.thermal_conductivity == 6
    assert tc.thermal_conductivity_ratio == 7


def test_load_thermal_properties_parses_lookup_file():
    # arrange
    csv_file = test_utils.get_test_file_path(path.join("Material", "Test_Lookup.csv"))
    material = AdditiveMaterial()
    # populate the array prior to loading the file, these should be cleared
    material.thermal_properties_data.append(ThermalPropertiesDataPoint())
    material.thermal_properties_data.append(ThermalPropertiesDataPoint())
    expected_first_point = ThermalPropertiesDataPoint(
        temperature=2,
        thermal_conductivity=8.3067794,
        specific_heat=260.25,
        density=8631.11931,
        thermal_conductivity_ratio=0.01,
        density_ratio=0.6,
        specific_heat_ratio=1,
    )
    expected_last_point = ThermalPropertiesDataPoint(
        temperature=15000,
        thermal_conductivity=40.5490107,
        specific_heat=759.56,
        density=6329.51763,
        thermal_conductivity_ratio=1,
        density_ratio=1,
        specific_heat_ratio=1,
    )

    # act
    material._load_thermal_properties(csv_file)

    # assert
    assert len(material.thermal_properties_data) == 7500
    assert material.thermal_properties_data[0] == expected_first_point
    assert material.thermal_properties_data[-1] == expected_last_point


def test_load_characteristic_width_parses_lookup_file():
    # arrange
    csv_file = test_utils.get_test_file_path(path.join("Material", "Test_CW_Lookup.csv"))
    material = AdditiveMaterial()
    # populate the array prior to loading the file, these should be cleared
    material.characteristic_width_data.append(CharacteristicWidthDataPoint())
    material.characteristic_width_data.append(CharacteristicWidthDataPoint())
    expected_first_point = CharacteristicWidthDataPoint(
        characteristic_width=0.000054939,
        laser_power=50,
        scan_speed=0.35,
    )
    expected_last_point = CharacteristicWidthDataPoint(
        characteristic_width=0.000076736,
        laser_power=700,
        scan_speed=2.5,
    )

    # act
    material._load_characteristic_width(csv_file)

    # assert
    assert len(material.characteristic_width_data) == 64
    assert material.characteristic_width_data[0] == expected_first_point
    assert material.characteristic_width_data[-1] == expected_last_point


def test_load_parameters_parses_parameter_file():
    # arrange
    json_file = test_utils.get_test_file_path(path.join("Material", "material-data.json"))
    material = AdditiveMaterial()

    # act
    material._load_parameters(json_file)

    # assert
    assert material.name == "TestMaterial"
    assert material.absorptivity_maximum == 1
    assert material.absorptivity_minimum == 2
    assert material.absorptivity_powder_coefficient_a == 3
    assert material.absorptivity_powder_coefficient_b == 4
    assert material.absorptivity_solid_coefficient_a == 5
    assert material.absorptivity_solid_coefficient_b == 6
    assert material.anisotropic_strain_coefficient_parallel == 7
    assert material.anisotropic_strain_coefficient_perpendicular == 8
    assert material.anisotropic_strain_coefficient_z == 9
    assert material.elastic_modulus == 10
    assert material.hardening_factor == 12
    assert material.liquidus_temperature == 13
    assert material.material_yield_strength == 14
    assert material.nucleation_constant_bulk == 15
    assert material.nucleation_constant_interface == 16
    assert material.penetration_depth_maximum == 17
    assert material.penetration_depth_minimum == 18
    assert material.penetration_depth_powder_coefficient_a == 19
    assert material.penetration_depth_powder_coefficient_b == 20
    assert material.penetration_depth_solid_coefficient_a == 21
    assert material.penetration_depth_solid_coefficient_b == 22
    assert material.poisson_ratio == 23
    assert material.powder_packing_density == 24
    assert material.purging_gas_convection_coefficient == 25
    assert material.solid_density_at_room_temperature == 26
    assert material.solid_specific_heat_at_room_temperature == 27
    assert material.solid_thermal_conductivity_at_room_temperature == 28
    assert material.solidus_temperature == 29
    assert material.strain_scaling_factor == 30
    assert material.support_yield_strength_ratio == 31
    assert material.thermal_expansion_coefficient == 32
    assert material.vaporization_temperature == 33
