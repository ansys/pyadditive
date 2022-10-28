from ansys.api.additive.v0.additive_domain_pb2 import (
    CharacteristicWidthDataPoint,
    MeltPoolTimeStep,
    ThermalCharacteristicDataPoint,
)

from ansys.additive.machine import AdditiveMachine
from ansys.additive.material import AdditiveMaterial
from ansys.additive.single_bead import MeltPoolMessage


def get_test_machine() -> AdditiveMachine:
    return AdditiveMachine(
        laser_power=10,
        scan_speed=11,
        heater_temperature=12,
        layer_thickness=13,
        beam_diameter=14,
        starting_layer_angle=15,
        layer_rotation_angle=16,
        hatch_spacing=17,
        slicing_stripe_width=18,
    )


def get_test_material() -> AdditiveMaterial:

    return AdditiveMaterial(
        absorptivity_maximum=101,
        absorptivity_minimum=102,
        absorptivity_powder_coefficient_a=103,
        absorptivity_powder_coefficient_b=104,
        absorptivity_solid_coefficient_a=105,
        absorptivity_solid_coefficient_b=106,
        anisotropic_strain_coefficient_parallel=107,
        anisotropic_strain_coefficient_perpendicular=108,
        anisotropic_strain_coefficient_z=109,
        elastic_modulus=110,
        hardening_factor=111,
        liquidus_temperature=112,
        material_yield_strength=113,
        name="test-material",
        nucleation_constant_bulk=114,
        nucleation_constant_interface=115,
        penetration_depth_maximum=116,
        penetration_depth_minimum=117,
        penetration_depth_powder_coefficient_a=118,
        penetration_depth_powder_coefficient_b=119,
        penetration_depth_solid_coefficient_a=120,
        penetration_depth_solid_coefficient_b=121,
        poisson_ratio=122,
        powder_packing_density=123,
        purging_gas_convection_coefficient=124,
        solid_density_at_room_temperature=125,
        solid_specific_heat_at_room_temperature=126,
        solid_thermal_conductivity_at_room_temperature=127,
        solidus_temperature=128,
        strain_scaling_factor=129,
        support_yield_strength_ratio=130,
        thermal_expansion_coefficient=131,
        vaporization_temperature=132,
        characteristic_width_data=[
            CharacteristicWidthDataPoint(
                characteristic_width=133,
                power=134,
                speed=135,
            )
        ],
        thermal_characteristic_data=[
            ThermalCharacteristicDataPoint(
                density=136,
                density_ratio=137,
                specific_heat=138,
                specific_heat_ratio=139,
                temperature=140,
                thermal_conductivity=141,
                thermal_conductivity_ratio=142,
            )
        ],
    )


def get_test_melt_pool_message() -> MeltPoolMessage:
    return MeltPoolMessage(
        time_steps=[
            MeltPoolTimeStep(
                laser_x=1,
                laser_y=2,
                length=3,
                width=4,
                reference_width=5,
                depth=6,
                reference_depth=7,
            )
        ]
    )