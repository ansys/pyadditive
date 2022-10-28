import pytest

from ansys.additive.material import (
    AdditiveMaterial,
    CharacteristicWidthDataPoint,
    CharacteristicWidthDataPointMessage,
    MaterialMessage,
    ThermalCharacteristicDataPoint,
    ThermalCharacteristicDataPointMessage,
)


def test_CharacteristicWidthDataPoint_init_raises_exception_for_invalid_key_value():
    # arrange, act, assert
    with pytest.raises(AttributeError):
        CharacteristicWidthDataPoint(bogus=123)


def test_from_characteristic_width_data_point_message_creates_CharacteristicWidthDataPoint():
    # arrange
    msg = CharacteristicWidthDataPointMessage(
        characteristic_width=1,
        power=2,
        speed=3,
    )

    # act
    point = CharacteristicWidthDataPoint.from_characteristic_width_data_point_message(msg)

    # assert
    assert isinstance(point, CharacteristicWidthDataPoint)
    assert point.characteristic_width == 1
    assert point.power == 2
    assert point.speed == 3


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
    with pytest.raises(ValueError, match="Invalid object") as exc_info:
        CharacteristicWidthDataPoint.from_characteristic_width_data_point_message(invalid_obj)


def test_to_characteristic_width_data_point_message_returns_CharacteristicWidthDataPointMessage():
    # arrange
    point = CharacteristicWidthDataPoint(
        characteristic_width=1,
        power=2,
        speed=3,
    )

    # act
    msg = point.to_characteristic_width_data_point_message()

    # assert
    assert isinstance(msg, CharacteristicWidthDataPointMessage)
    assert msg.characteristic_width == 1
    assert msg.power == 2
    assert msg.speed == 3


def test_ThermalCharacteristicDataPoint_init_raises_exception_for_invalid_key_value():
    # arrange, act, assert
    with pytest.raises(AttributeError):
        ThermalCharacteristicDataPoint(bogus=123)


def test_from_thermal_characteristic_data_point_message_creates_ThermalCharacteristicDataPoint():
    # arrange
    msg = ThermalCharacteristicDataPointMessage(
        density=1,
        density_ratio=2,
        specific_heat=3,
        specific_heat_ratio=4,
        temperature=5,
        thermal_conductivity=6,
        thermal_conductivity_ratio=7,
    )

    # act
    point = ThermalCharacteristicDataPoint.from_thermal_characteristic_data_point_message(msg)

    # assert
    assert isinstance(point, ThermalCharacteristicDataPoint)
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
        ThermalCharacteristicDataPoint(),
    ],
)
def test_from_thermal_characteristic_data_point_message_raises_exception_for_invalid_type(
    invalid_obj,
):
    # arrange, act, assert
    with pytest.raises(ValueError, match="Invalid object") as exc_info:
        ThermalCharacteristicDataPoint.from_thermal_characteristic_data_point_message(invalid_obj)


def test_to_thermal_characteristic_data_point_message_returns_ThermalCharacteristicDataPointMessage():  # noqa: E501
    # arrange
    point = ThermalCharacteristicDataPoint(
        density=1,
        density_ratio=2,
        specific_heat=3,
        specific_heat_ratio=4,
        temperature=5,
        thermal_conductivity=6,
        thermal_conductivity_ratio=7,
    )

    # act
    msg = point.to_thermal_characteristic_data_point_message()

    # assert
    assert isinstance(msg, ThermalCharacteristicDataPointMessage)
    assert msg.density == 1
    assert msg.density_ratio == 2
    assert msg.specific_heat == 3
    assert msg.specific_heat_ratio == 4
    assert msg.temperature == 5
    assert msg.thermal_conductivity == 6
    assert msg.thermal_conductivity_ratio == 7


def test_AdditiveMaterial_init_raises_exception_for_invalid_key_value():
    # arrange, act, assert
    with pytest.raises(AttributeError):
        AdditiveMaterial(bogus=123)


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
    msg.characteristic_width_data_set.characteristic_width_data_points.append(
        CharacteristicWidthDataPointMessage(
            characteristic_width=1,
            power=2,
            speed=3,
        )
    )
    msg.thermal_characteristic_data_set.thermal_characteristic_data_points.append(
        ThermalCharacteristicDataPointMessage(
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
    am = AdditiveMaterial.from_material_message(msg)

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
    assert cw.power == 2
    assert cw.speed == 3
    assert len(am.thermal_characteristic_data) == 1
    tc = am.thermal_characteristic_data[0]
    assert tc.density == 1
    assert tc.density_ratio == 2
    assert tc.specific_heat == 3
    assert tc.specific_heat_ratio == 4
    assert tc.temperature == 5
    assert tc.thermal_conductivity == 6
    assert tc.thermal_conductivity_ratio == 7


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
    with pytest.raises(ValueError, match="Invalid object") as exc_info:
        AdditiveMaterial.from_material_message(invalid_obj)


def test_to_material_message_returns_material_message():
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
            power=2,
            speed=3,
        )
    )
    am.thermal_characteristic_data.append(
        ThermalCharacteristicDataPoint(
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
    msg = am.to_material_message()

    # assert
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
    assert len(msg.characteristic_width_data_set.characteristic_width_data_points) == 1
    cw = msg.characteristic_width_data_set.characteristic_width_data_points[0]
    assert cw.characteristic_width == 1
    assert cw.power == 2
    assert cw.speed == 3
    assert len(msg.thermal_characteristic_data_set.thermal_characteristic_data_points) == 1
    tc = msg.thermal_characteristic_data_set.thermal_characteristic_data_points[0]
    assert tc.density == 1
    assert tc.density_ratio == 2
    assert tc.specific_heat == 3
    assert tc.specific_heat_ratio == 4
    assert tc.temperature == 5
    assert tc.thermal_conductivity == 6
    assert tc.thermal_conductivity_ratio == 7
