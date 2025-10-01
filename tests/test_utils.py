# Copyright (C) 2022 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
from pathlib import Path

from ansys.additive.core.material import (
    AdditiveMaterial,
    CharacteristicWidthDataPoint,
    ThermalPropertiesDataPoint,
)
from ansys.additive.core.material_tuning import MaterialTuningInput
from ansys.additive.core.single_bead import (
    MeltPoolMessage,
    SingleBeadInput,
    SingleBeadSummary,
)
from ansys.api.additive.v0.additive_domain_pb2 import MeltPoolTimeStep


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
                laser_power=134,
                scan_speed=135,
            )
        ],
        thermal_properties_data=[
            ThermalPropertiesDataPoint(
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
        ],
        thermal_history_vtk_zip=str(),
    )


def get_test_melt_pool_message_with_thermal_history() -> MeltPoolMessage:
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
        ],
        thermal_history_vtk_zip=get_test_file_path("gridfullthermal.zip"),
    )


def get_test_SingleBeadSummary(input: SingleBeadInput = None) -> SingleBeadSummary:
    melt_pool_msg = get_test_melt_pool_message()
    if input is None:
        input = SingleBeadInput(
            material=get_test_material(),
        )

    return SingleBeadSummary(input, melt_pool_msg, "logs", None)


def get_test_file_path(name: str | Path) -> str:
    """Retrieve the absolute path to a test file in the data folder."""
    dir_name = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir_name, "data", name)


def get_test_material_tuning_input() -> MaterialTuningInput:
    file_name = get_test_file_path("slm_build_file.zip")
    return MaterialTuningInput(
        experiment_data_file=file_name,
        material_configuration_file=file_name,
        thermal_properties_lookup_file=file_name,
    )

def get_default_machine_repr() -> str:
        return ("machine: AdditiveMachine\n"
        + "laser_power: 195.0 W\n"
        + "scan_speed: 1.0 m/s\n"
        + "heater_temperature: 80.0 °C\n"
        + "layer_thickness: 5e-05 m\n"
        + "beam_diameter: 0.0001 m\n"
        + "starting_layer_angle: 57 °\n"
        + "layer_rotation_angle: 67 °\n"
        + "hatch_spacing: 0.0001 m\n"
        + "slicing_stripe_width: 0.01 m\n"
        + "heat_source_model: gaussian\n"
        + "ring_mode_index: 0\n")
