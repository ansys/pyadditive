# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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
"""Provides a container for material parameters."""
import collections
import csv
import json
import re

from ansys.api.additive.v0.additive_domain_pb2 import (
    CharacteristicWidthDataPoint as CharacteristicWidthDataPointMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    ThermalPropertiesDataPoint as ThermalPropertiesDataPointMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import AdditiveMaterial as MaterialMessage

RESERVED_MATERIAL_NAMES = ["17-4PH", "316L", "Al357", "AlSi10Mg", "CoCr", "IN625", "IN718", "Ti64"]


class CharacteristicWidthDataPoint:
    """Provides the container for a characteristic width data point.

    Additive material definitions include a file containing a characteristic width
    lookup table, allowing a given laser speed and power to be correlated to a
    characteristic melt pool width. This class represents a single row in the lookup
    table.
    """

    def __init__(
        self, *, laser_power: float = 0, scan_speed: float = 0, characteristic_width: float = 0
    ):
        """Initialize a characteristic width data point."""
        self._laser_power = laser_power
        self._scan_speed = scan_speed
        self._characteristic_width = characteristic_width

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CharacteristicWidthDataPoint):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True

    @property
    def characteristic_width(self) -> float:
        """Characteristic melt pool width for a given laser power and scan
        speed (m)."""
        return self._characteristic_width

    @characteristic_width.setter
    def characteristic_width(self, value: float):
        """Set characteristic width value."""
        if value < 0:
            raise ValueError("Characteristic width must not be negative.")
        self._characteristic_width = value

    @property
    def laser_power(self) -> float:
        """Laser power (W)."""
        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: float):
        """Set power value."""
        if value < 0:
            raise ValueError("Power must not be negative.")
        self._laser_power = value

    @property
    def scan_speed(self) -> float:
        """Laser scan speed (m/s)."""
        return self._scan_speed

    @scan_speed.setter
    def scan_speed(self, value: float):
        """Set speed value."""
        if value < 0:
            raise ValueError("Speed must not be negative.")
        self._scan_speed = value

    @staticmethod
    def _from_characteristic_width_data_point_message(msg: CharacteristicWidthDataPointMessage):
        """Create a characteristic width data point`` from a characteristic
        data point message received from the Additive service."""
        if not isinstance(msg, CharacteristicWidthDataPointMessage):
            raise ValueError(
                "Invalid message object passed to from_characteristic_width_data_point_message()"
            )
        point = CharacteristicWidthDataPoint()
        for p in point.__dict__:
            setattr(point, p, getattr(msg, p.replace("_", "", 1)))
        return point

    def _to_characteristic_width_data_point_message(
        self,
    ) -> CharacteristicWidthDataPointMessage:
        """Create a characteristic width data point message from this
        characteristic width data point to send to the Additive service."""
        msg = CharacteristicWidthDataPointMessage()
        for p in self.__dict__:
            setattr(msg, p.replace("_", "", 1), getattr(self, p))
        return msg


class ThermalPropertiesDataPoint:
    """Provides the container for temperature-dependent properties.

    Additive material definitions include a file containing a lookup table describing
    the material's thermal properties at different temperatures. This class represents a
    single row in the lookup table.

    Units are SI (m, kg, s, K) unless otherwise noted.
    """

    def __init__(
        self,
        *,
        density: float = 0,
        density_ratio: float = 0,
        specific_heat: float = 0,
        specific_heat_ratio: float = 0,
        temperature: float = 0,
        thermal_conductivity: float = 0,
        thermal_conductivity_ratio: float = 0,
    ):
        """Create a thermal properties data point."""
        self._density = density
        self._density_ratio = density_ratio
        self._specific_heat = specific_heat
        self._specific_heat_ratio = specific_heat_ratio
        self._temperature = temperature
        self._thermal_conductivity = thermal_conductivity
        self._thermal_conductivity_ratio = thermal_conductivity_ratio

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ThermalPropertiesDataPoint):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True

    @property
    def density(self) -> float:
        """Density (kg/m^3)."""
        return self._density

    @density.setter
    def density(self, value: float):
        """Set density value."""
        if value < 0:
            raise ValueError("Density must not be negative.")
        self._density = value

    @property
    def density_ratio(self) -> float:
        """Density ratio."""
        return self._density_ratio

    @density_ratio.setter
    def density_ratio(self, value: float):
        """Set density ratio value."""
        if value < 0:
            raise ValueError("Density ratio must not be negative.")
        self._density_ratio = value

    @property
    def specific_heat(self) -> float:
        """Specific heat (J/kg/K)."""
        return self._specific_heat

    @specific_heat.setter
    def specific_heat(self, value: float):
        """Set specific heat."""
        self._specific_heat = value

    @property
    def specific_heat_ratio(self) -> float:
        """Specific heat ratio."""
        return self._specific_heat_ratio

    @specific_heat_ratio.setter
    def specific_heat_ratio(self, value: float):
        """Set specific heat ratio."""
        self._specific_heat_ratio = value

    @property
    def temperature(self) -> float:
        """Temperature (K)."""
        return self._temperature

    @temperature.setter
    def temperature(self, value: float):
        """Set temperature."""
        if value < 0:
            raise ValueError("Temperature must not be negative.")
        self._temperature = value

    @property
    def thermal_conductivity(self) -> float:
        """Thermal conductivity (W/m/K)."""
        return self._thermal_conductivity

    @thermal_conductivity.setter
    def thermal_conductivity(self, value: float):
        """Set thermal conductivity."""
        self._thermal_conductivity = value

    @property
    def thermal_conductivity_ratio(self) -> float:
        """Thermal conductivity ratio."""
        return self._thermal_conductivity_ratio

    @thermal_conductivity_ratio.setter
    def thermal_conductivity_ratio(self, value: float):
        """Set thermal conductivity ratio."""
        self._thermal_conductivity_ratio = value

    @staticmethod
    def _from_thermal_properties_data_point_message(msg: ThermalPropertiesDataPointMessage):
        """Create a thermal properties data point from a thermal characteristic
        data point message received from the Additive service.

        :meta private:
        """
        if not isinstance(msg, ThermalPropertiesDataPointMessage):
            raise ValueError(
                "Invalid message object passed to from_thermal_properties_data_point_message()"
            )
        point = ThermalPropertiesDataPoint()
        for p in point.__dict__:
            setattr(point, p, getattr(msg, p.replace("_", "", 1)))
        return point

    def _to_thermal_properties_data_point_message(
        self,
    ) -> ThermalPropertiesDataPointMessage:
        """Create a thermal characteristic data point message from this thermal
        properties data point to send to the Additive service.

        :meta private:
        """
        msg = ThermalPropertiesDataPointMessage()
        for p in self.__dict__:
            setattr(msg, p.replace("_", "", 1), getattr(self, p))
        return msg


class AdditiveMaterial:
    """Provides the container for material properties used during additive manufacturing simulations."""

    def __init__(
        self,
        *,
        absorptivity_maximum: float = 0,
        absorptivity_minimum: float = 0,
        absorptivity_powder_coefficient_a: float = 0,
        absorptivity_powder_coefficient_b: float = 0,
        absorptivity_solid_coefficient_a: float = 0,
        absorptivity_solid_coefficient_b: float = 0,
        anisotropic_strain_coefficient_parallel: float = 0,
        anisotropic_strain_coefficient_perpendicular: float = 0,
        anisotropic_strain_coefficient_z: float = 0,
        description: str = "",
        elastic_modulus: float = 0,
        hardening_factor: float = 0,
        liquidus_temperature: float = 0,
        material_yield_strength: float = 0,
        name: str = "",
        nucleation_constant_bulk: float = 0,
        nucleation_constant_interface: float = 0,
        penetration_depth_maximum: float = 0,
        penetration_depth_minimum: float = 0,
        penetration_depth_powder_coefficient_a: float = 0,
        penetration_depth_powder_coefficient_b: float = 0,
        penetration_depth_solid_coefficient_a: float = 0,
        penetration_depth_solid_coefficient_b: float = 0,
        poisson_ratio: float = 0,
        powder_packing_density: float = 0,
        purging_gas_convection_coefficient: float = 0,
        solid_density_at_room_temperature: float = 0,
        solid_specific_heat_at_room_temperature: float = 0,
        solid_thermal_conductivity_at_room_temperature: float = 0,
        solidus_temperature: float = 0,
        strain_scaling_factor: float = 0,
        support_yield_strength_ratio: float = 0,
        thermal_expansion_coefficient: float = 0,
        vaporization_temperature: float = 0,
        characteristic_width_data: list[CharacteristicWidthDataPoint] = None,
        thermal_properties_data: list[ThermalPropertiesDataPoint] = None,
    ):
        """Create an additive material."""
        self._absorptivity_maximum = absorptivity_maximum
        self._absorptivity_minimum = absorptivity_minimum
        self._absorptivity_powder_coefficient_a = absorptivity_powder_coefficient_a
        self._absorptivity_powder_coefficient_b = absorptivity_powder_coefficient_b
        self._absorptivity_solid_coefficient_a = absorptivity_solid_coefficient_a
        self._absorptivity_solid_coefficient_b = absorptivity_solid_coefficient_b
        self._anisotropic_strain_coefficient_parallel = anisotropic_strain_coefficient_parallel
        self._anisotropic_strain_coefficient_perpendicular = (
            anisotropic_strain_coefficient_perpendicular
        )
        self._anisotropic_strain_coefficient_z = anisotropic_strain_coefficient_z
        self._description = description
        self._elastic_modulus = elastic_modulus
        self._hardening_factor = hardening_factor
        self._liquidus_temperature = liquidus_temperature
        self._material_yield_strength = material_yield_strength
        self._name = name
        self._nucleation_constant_bulk = nucleation_constant_bulk
        self._nucleation_constant_interface = nucleation_constant_interface
        self._penetration_depth_maximum = penetration_depth_maximum
        self._penetration_depth_minimum = penetration_depth_minimum
        self._penetration_depth_powder_coefficient_a = penetration_depth_powder_coefficient_a
        self._penetration_depth_powder_coefficient_b = penetration_depth_powder_coefficient_b
        self._penetration_depth_solid_coefficient_a = penetration_depth_solid_coefficient_a
        self._penetration_depth_solid_coefficient_b = penetration_depth_solid_coefficient_b
        self._poisson_ratio = poisson_ratio
        self._powder_packing_density = powder_packing_density
        self._purging_gas_convection_coefficient = purging_gas_convection_coefficient
        self._solid_density_at_room_temperature = solid_density_at_room_temperature
        self._solid_specific_heat_at_room_temperature = solid_specific_heat_at_room_temperature
        self._solid_thermal_conductivity_at_room_temperature = (
            solid_thermal_conductivity_at_room_temperature
        )
        self._solidus_temperature = solidus_temperature
        self._strain_scaling_factor = strain_scaling_factor
        self._support_yield_strength_ratio = support_yield_strength_ratio
        self._thermal_expansion_coefficient = thermal_expansion_coefficient
        self._vaporization_temperature = vaporization_temperature
        if characteristic_width_data:
            self._characteristic_width_data = characteristic_width_data
        else:
            self._characteristic_width_data = []
        if thermal_properties_data:
            self._thermal_properties_data = thermal_properties_data
        else:
            self._thermal_properties_data = []

    def __repr__(self) -> str:
        repr = self.__class__.__name__ + "\n"
        for p in self.__dict__:
            if p != "_characteristic_width_data" and p != "_thermal_properties_data":
                repr = repr + "{}: {}\n".format(p.replace("_", "", 1), getattr(self, p))
        repr = (
            repr
            + "characteristic_width_data: CharacteristicWidthDataPoint[]\n"
            + "thermal_properties_data: ThermalPropertiesDataPoint[]\n"
        )
        return repr

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, AdditiveMaterial):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(__o, k):
                return False
        return True

    @property
    def absorptivity_maximum(self) -> float:
        """Absorptivity maximum."""
        return self._absorptivity_maximum

    @absorptivity_maximum.setter
    def absorptivity_maximum(self, value: float):
        """Set absorptivity maximum."""
        self._absorptivity_maximum = value

    @property
    def absorptivity_minimum(self) -> float:
        """Absorptivity minimum."""
        return self._absorptivity_minimum

    @absorptivity_minimum.setter
    def absorptivity_minimum(self, value: float):
        """Set absorptivity minimum."""
        self._absorptivity_minimum = value

    @property
    def absorptivity_powder_coefficient_a(self) -> float:
        """Absorptivity powder coefficient a."""
        return self._absorptivity_powder_coefficient_a

    @absorptivity_powder_coefficient_a.setter
    def absorptivity_powder_coefficient_a(self, value: float):
        """Set absorptivity powder coefficient a."""
        self._absorptivity_powder_coefficient_a = value

    @property
    def absorptivity_powder_coefficient_b(self) -> float:
        """Absorptivity powder coefficient b."""
        return self._absorptivity_powder_coefficient_b

    @absorptivity_powder_coefficient_b.setter
    def absorptivity_powder_coefficient_b(self, value: float):
        """Set absorptivity powder coefficient b."""
        self._absorptivity_powder_coefficient_b = value

    @property
    def absorptivity_solid_coefficient_a(self) -> float:
        """Absorptivity solid coefficient a."""
        return self._absorptivity_solid_coefficient_a

    @absorptivity_solid_coefficient_a.setter
    def absorptivity_solid_coefficient_a(self, value: float):
        """Set absorptivity solid coefficient a."""
        self._absorptivity_solid_coefficient_a = value

    @property
    def absorptivity_solid_coefficient_b(self) -> float:
        """Absorptivity solid coefficient b."""
        return self._absorptivity_solid_coefficient_b

    @absorptivity_solid_coefficient_b.setter
    def absorptivity_solid_coefficient_b(self, value: float):
        """Set absorptivity solid coefficient b."""
        self._absorptivity_solid_coefficient_b = value

    @property
    def anisotropic_strain_coefficient_parallel(self) -> float:
        """Multiplier on the predicted strain in the direction that the laser is scanning for the major fill rasters."""  # noqa: E501
        return self._anisotropic_strain_coefficient_parallel

    @anisotropic_strain_coefficient_parallel.setter
    def anisotropic_strain_coefficient_parallel(self, value: float):
        """Set anisotropic strain coefficient parallel."""
        self._anisotropic_strain_coefficient_parallel = value

    @property
    def anisotropic_strain_coefficient_perpendicular(self) -> float:
        """Multiplier on the predicted strain orthogonal to the direction that the laser is scanning for the major fill rasters and in the plane of the surface of the build plate."""  # noqa: E501
        return self._anisotropic_strain_coefficient_perpendicular

    @anisotropic_strain_coefficient_perpendicular.setter
    def anisotropic_strain_coefficient_perpendicular(self, value: float):
        """Set anisotropic strain coefficient perpendicular."""
        self._anisotropic_strain_coefficient_perpendicular = value

    @property
    def anisotropic_strain_coefficient_z(self) -> float:
        """Multiplier on the predicted strain in the Z direction."""
        return self._anisotropic_strain_coefficient_z

    @anisotropic_strain_coefficient_z.setter
    def anisotropic_strain_coefficient_z(self, value: float):
        """Set anisotropic strain coefficient z."""
        self._anisotropic_strain_coefficient_z = value

    @property
    def description(self) -> str:
        """Description of the material."""
        return self._description

    @description.setter
    def description(self, value: str):
        """Set description."""
        self._description = value

    @property
    def elastic_modulus(self) -> float:
        """Elastic modulus (Pa)."""
        return self._elastic_modulus

    @elastic_modulus.setter
    def elastic_modulus(self, value: float):
        """Set elastic modulus."""
        self._elastic_modulus = value

    @property
    def hardening_factor(self) -> float:
        """Factor relating the elastic modulus to the tangent modulus for plasticity simulations (tangent modulus = elastic modulus * hardening factor)."""  # noqa: E501
        return self._hardening_factor

    @hardening_factor.setter
    def hardening_factor(self, value: float):
        """Set hardening factor."""
        self._hardening_factor = value

    @property
    def liquidus_temperature(self) -> float:
        """Minimum temperature (K) at which the material is completely liquid."""
        return self._liquidus_temperature

    @liquidus_temperature.setter
    def liquidus_temperature(self, value: float):
        """Set liquidus temperature."""
        self._liquidus_temperature = value

    @property
    def material_yield_strength(self) -> float:
        """Material yield strength (Pa)."""
        return self._material_yield_strength

    @material_yield_strength.setter
    def material_yield_strength(self, value: float):
        """Set material yield strength."""
        self._material_yield_strength = value

    @property
    def name(self) -> str:
        """Name of the material."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set name."""
        self._name = value

    @property
    def nucleation_constant_bulk(self) -> float:
        """Controls the homogeneous nucleation rate (in bulk of the microstructure simulation domain) during solidification (1/m^2/K^2)."""  # noqa: E501
        return self._nucleation_constant_bulk

    @nucleation_constant_bulk.setter
    def nucleation_constant_bulk(self, value: float):
        """Set nucleation constant bulk."""
        self._nucleation_constant_bulk = value

    @property
    def nucleation_constant_interface(self) -> float:
        """Heterogeneous nucleation rate (on existing solid interfaces) during solidification (1/m/K^2)."""  # noqa: E501
        return self._nucleation_constant_interface

    @nucleation_constant_interface.setter
    def nucleation_constant_interface(self, value: float):
        """Set nucleation constant interface."""
        self._nucleation_constant_interface = value

    @property
    def penetration_depth_maximum(self) -> float:
        """Penetration depth maximum."""
        return self._penetration_depth_maximum

    @penetration_depth_maximum.setter
    def penetration_depth_maximum(self, value: float):
        """Set penetration depth maximum."""
        self._penetration_depth_maximum = value

    @property
    def penetration_depth_minimum(self) -> float:
        """Penetration depth minimum."""
        return self._penetration_depth_minimum

    @penetration_depth_minimum.setter
    def penetration_depth_minimum(self, value: float):
        """Set penetration depth minimum."""
        self._penetration_depth_minimum = value

    @property
    def penetration_depth_powder_coefficient_a(self) -> float:
        """Penetration depth powder coefficient a."""
        return self._penetration_depth_powder_coefficient_a

    @penetration_depth_powder_coefficient_a.setter
    def penetration_depth_powder_coefficient_a(self, value: float):
        """Set penetration depth powder coefficient a."""
        self._penetration_depth_powder_coefficient_a = value

    @property
    def penetration_depth_powder_coefficient_b(self) -> float:
        """Penetration depth powder coefficient b."""
        return self._penetration_depth_powder_coefficient_b

    @penetration_depth_powder_coefficient_b.setter
    def penetration_depth_powder_coefficient_b(self, value: float):
        """Set penetration depth powder coefficient b."""
        self._penetration_depth_powder_coefficient_b = value

    @property
    def penetration_depth_solid_coefficient_a(self) -> float:
        """Penetration depth solid coefficient a."""
        return self._penetration_depth_solid_coefficient_a

    @penetration_depth_solid_coefficient_a.setter
    def penetration_depth_solid_coefficient_a(self, value: float):
        """Set penetration depth solid coefficient a."""
        self._penetration_depth_solid_coefficient_a = value

    @property
    def penetration_depth_solid_coefficient_b(self) -> float:
        """Penetration depth solid coefficient b."""
        return self._penetration_depth_solid_coefficient_b

    @penetration_depth_solid_coefficient_b.setter
    def penetration_depth_solid_coefficient_b(self, value: float):
        """Set penetration_depth solid coefficient b."""
        self._penetration_depth_solid_coefficient_b = value

    @property
    def poisson_ratio(self) -> float:
        """Poisson ratio."""
        return self._poisson_ratio

    @poisson_ratio.setter
    def poisson_ratio(self, value: float):
        """Set Poisson ratio."""
        self._poisson_ratio = value

    @property
    def powder_packing_density(self) -> float:
        """Density of powder material relative to the solid."""
        return self._powder_packing_density

    @powder_packing_density.setter
    def powder_packing_density(self, value: float):
        """Set powder packing density."""
        self._powder_packing_density = value

    @property
    def purging_gas_convection_coefficient(self) -> float:
        """Convection coefficient between the solid and gas during build."""
        return self._purging_gas_convection_coefficient

    @purging_gas_convection_coefficient.setter
    def purging_gas_convection_coefficient(self, value: float):
        """Set purging gas convection coefficient."""
        self._purging_gas_convection_coefficient = value

    @property
    def solid_density_at_room_temperature(self) -> float:
        """Density of bulk material at room temperature, 298 K (kg/m^3)."""
        return self._solid_density_at_room_temperature

    @solid_density_at_room_temperature.setter
    def solid_density_at_room_temperature(self, value: float):
        """Set solid density at room temperature."""
        self._solid_density_at_room_temperature = value

    @property
    def solid_specific_heat_at_room_temperature(self) -> float:
        """Specific heat of bulk material at room temperature, 298 K (J/kg/K)."""
        return self._solid_specific_heat_at_room_temperature

    @solid_specific_heat_at_room_temperature.setter
    def solid_specific_heat_at_room_temperature(self, value: float):
        """Set solid specific heat at room temperature."""
        self._solid_specific_heat_at_room_temperature = value

    @property
    def solid_thermal_conductivity_at_room_temperature(self) -> float:
        """Thermal conductivity of bulk material at room temperature, 298 K (W/m/K)."""
        return self._solid_thermal_conductivity_at_room_temperature

    @solid_thermal_conductivity_at_room_temperature.setter
    def solid_thermal_conductivity_at_room_temperature(self, value: float):
        """Set solid thermal conductivity at_room temperature."""
        self._solid_thermal_conductivity_at_room_temperature = value

    @property
    def solidus_temperature(self) -> float:
        """Maximum temperature (K) at which the material is completely solid."""
        return self._solidus_temperature

    @solidus_temperature.setter
    def solidus_temperature(self, value: float):
        """Set solidus temperature."""
        self._solidus_temperature = value

    @property
    def strain_scaling_factor(self) -> float:
        """Strain scaling factor."""
        return self._strain_scaling_factor

    @strain_scaling_factor.setter
    def strain_scaling_factor(self, value: float):
        """Set strain scaling factor."""
        self._strain_scaling_factor = value

    @property
    def support_yield_strength_ratio(self) -> float:
        """Knockdown factor that is used to adjust the strength of the support material in comparison to the solid material.

        The factor is multiplied by the support material's yield
        strength and elastic modulus. A value of 1.0, for example,
        results in support strength equal to the solid material, whereas
        0.5 is half the strength of the solid material.
        """  # noqa: E501
        return self._support_yield_strength_ratio

    @support_yield_strength_ratio.setter
    def support_yield_strength_ratio(self, value: float):
        """Set support yield strength ratio."""
        self._support_yield_strength_ratio = value

    @property
    def thermal_expansion_coefficient(self) -> float:
        """Coefficient of thermal expansion (1/K)."""
        return self._thermal_expansion_coefficient

    @thermal_expansion_coefficient.setter
    def thermal_expansion_coefficient(self, value: float):
        """Set thermal expansion coefficient."""
        self._thermal_expansion_coefficient = value

    @property
    def vaporization_temperature(self) -> float:
        """Temperature (K) at which the material has completely changed from liquid to vapor."""
        return self._vaporization_temperature

    @vaporization_temperature.setter
    def vaporization_temperature(self, value: float):
        """Set vaporization temperature (K)."""
        self._vaporization_temperature = value

    @property
    def characteristic_width_data(self) -> list[CharacteristicWidthDataPoint]:
        """List of characteristic width data points."""
        return self._characteristic_width_data

    @characteristic_width_data.setter
    def characteristic_width_data(self, value: list[CharacteristicWidthDataPoint]):
        """Set characteristic width data."""
        if not isinstance(value, collections.abc.Sequence):
            raise TypeError(
                "Invalid object type, {}, passed to characteristic_width_data()".format(type(value))
            )
        self._characteristic_width_data = value

    @property
    def thermal_properties_data(self) -> list[ThermalPropertiesDataPoint]:
        """List of thermal properties data points."""
        return self._thermal_properties_data

    @thermal_properties_data.setter
    def thermal_properties_data(self, value: list[ThermalPropertiesDataPoint]):
        """Set thermal properties data."""
        if not isinstance(value, collections.abc.Sequence):
            raise TypeError(
                "Invalid object type, {}, passed to thermal_properties_data()".format(type(value))
            )
        self._thermal_properties_data = value

    @staticmethod
    def _from_material_message(msg: MaterialMessage):
        """Create an additive material from a material message received from
        the Additive service."""
        if not isinstance(msg, MaterialMessage):
            raise ValueError("Invalid message object passed to from_material_message()")
        material = AdditiveMaterial()
        for p in material.__dict__:
            if p != "_characteristic_width_data" and p != "_thermal_properties_data":
                setattr(material, p, getattr(msg, p.replace("_", "", 1)))
        for c in msg.characteristic_width_data_points:
            material.characteristic_width_data.append(
                CharacteristicWidthDataPoint._from_characteristic_width_data_point_message(c)
            )
        for t in msg.thermal_properties_data_points:
            material.thermal_properties_data.append(
                ThermalPropertiesDataPoint._from_thermal_properties_data_point_message(t)
            )
        return material

    def _to_material_message(self) -> MaterialMessage:
        """Create a material message from the additive material to send to the
        Additive service."""
        msg = MaterialMessage()
        for p in self.__dict__:
            if p != "_characteristic_width_data" and p != "_thermal_properties_data":
                setattr(msg, p.replace("_", "", 1), getattr(self, p))
        for c in self.characteristic_width_data:
            msg.characteristic_width_data_points.append(
                c._to_characteristic_width_data_point_message()
            )
        for t in self.thermal_properties_data:
            msg.thermal_properties_data_points.append(t._to_thermal_properties_data_point_message())
        return msg

    def _load_parameters(self, parameters_file: str):
        """Load material parameters from a JSON file."""
        with open(parameters_file, "r") as f:
            data = json.load(f)
        self.name = data["name"]
        self.description = data["description"]
        parameters = data["configuration"]
        # Convert camelCase to snake_case
        pattern = re.compile(r"(?<!^)(?=[A-Z])")
        for p in parameters:
            if p != "materialName" and p != "elasticModulusOfBase":
                name = pattern.sub("_", p).lower()
                name = name.replace("_coeff_", "_coefficient_")
                setattr(self, name, parameters[p])

    def _load_thermal_properties(self, thermal_lookup_file: str):
        """Load thermal properties from a CSV file."""
        with open(thermal_lookup_file, "r") as f:
            reader = csv.reader(f)
            self.thermal_properties_data.clear()
            next(reader)  # skip header
            for row in reader:
                self.thermal_properties_data.append(
                    ThermalPropertiesDataPoint(
                        temperature=float(row[0]),
                        thermal_conductivity=float(row[1]),
                        specific_heat=float(row[2]),
                        density=float(row[3]),
                        thermal_conductivity_ratio=float(row[4]),
                        density_ratio=float(row[5]),
                        specific_heat_ratio=float(row[6]),
                    )
                )

    def _load_characteristic_width(self, cw_lookup_file: str):
        """Load characteristic width values from a CSV file."""
        with open(cw_lookup_file, "r") as f:
            reader = csv.reader(f)
            self.characteristic_width_data.clear()
            next(reader)
            for row in reader:
                self.characteristic_width_data.append(
                    CharacteristicWidthDataPoint(
                        scan_speed=float(row[0]),
                        laser_power=float(row[1]),
                        characteristic_width=float(row[2]),
                    )
                )
