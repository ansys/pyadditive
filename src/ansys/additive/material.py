# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import collections

from ansys.api.additive.v0.additive_domain_pb2 import (
    CharacteristicWidthDataPoint as CharacteristicWidthDataPointMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    ThermalPropertiesDataPoint as ThermalPropertiesDataPointMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import AdditiveMaterial as MaterialMessage


class CharacteristicWidthDataPoint:
    """Container for a characteristic width data point.

    Additive material definitions include a file containing a characteristic width
    lookup table which allows a given laser speed and power to be correlated to a
    characteristic melt pool width. This class represents a single row in the
    lookup table.

    Units are SI (m, kg, s, K) unless otherwise noted.

    """

    def __init__(
        self, *, laser_power: float = 0, scan_speed: float = 0, characteristic_width: float = 0
    ):
        """Create a ``CharacteristicWidthDataPoint``."""
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
        """Characteristic melt pool width for a given laser power and speed (m)."""
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
        """Create a ``CharacteristicWidthDataPoint`` from a characteristic data point message
        received from Additive service"""
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
        ``CharacteristicWidthDataPoint`` to send to the Additive service"""
        msg = CharacteristicWidthDataPointMessage()
        for p in self.__dict__:
            setattr(msg, p.replace("_", "", 1), getattr(self, p))
        return msg


class ThermalPropertiesDataPoint:
    """
    Container for a temperature dependent properties.

    Additive material definitions include a file containing a lookup table
    which describes the material's thermal properties at different temperatures.
    This class represents a single row in the lookup table.

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
        thermal_conductivity_ratio: float = 0
    ):
        """Create a ``ThermalPropertiesDataPoint``."""
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
        """Set density_ratio value."""
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
        """Create a ``ThermalPropertiesDataPoint`` from a thermal characteristic
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
        """Create a thermal characteristic data point message from this ``ThermalPropertiesDataPoint``
        object to send to the Additive service.

        :meta private:
        """
        msg = ThermalPropertiesDataPointMessage()
        for p in self.__dict__:
            setattr(msg, p.replace("_", "", 1), getattr(self, p))
        return msg


class AdditiveMaterial:
    """Container for material properties used during additive manufacturing simulation."""

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
        thermal_properties_data: list[ThermalPropertiesDataPoint] = None
    ):
        """Create an ``AdditiveMaterial``."""
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
        """Set absorptivity_maximum."""
        self._absorptivity_maximum = value

    @property
    def absorptivity_minimum(self) -> float:
        """Absorptivity minimum."""
        return self._absorptivity_minimum

    @absorptivity_minimum.setter
    def absorptivity_minimum(self, value: float):
        """Set absorptivity_minimum."""
        self._absorptivity_minimum = value

    @property
    def absorptivity_powder_coefficient_a(self) -> float:
        """Absorptivity powder coefficient a."""
        return self._absorptivity_powder_coefficient_a

    @absorptivity_powder_coefficient_a.setter
    def absorptivity_powder_coefficient_a(self, value: float):
        """Set absorptivity_powder_coefficient_a."""
        self._absorptivity_powder_coefficient_a = value

    @property
    def absorptivity_powder_coefficient_b(self) -> float:
        """Absorptivity powder coefficient b."""
        return self._absorptivity_powder_coefficient_b

    @absorptivity_powder_coefficient_b.setter
    def absorptivity_powder_coefficient_b(self, value: float):
        """Set absorptivity_powder_coefficient_b."""
        self._absorptivity_powder_coefficient_b = value

    @property
    def absorptivity_solid_coefficient_a(self) -> float:
        """Absorptivity solid coefficient a."""
        return self._absorptivity_solid_coefficient_a

    @absorptivity_solid_coefficient_a.setter
    def absorptivity_solid_coefficient_a(self, value: float):
        """Set absorptivity_solid_coefficient_a."""
        self._absorptivity_solid_coefficient_a = value

    @property
    def absorptivity_solid_coefficient_b(self) -> float:
        """Absorptivity solid coefficient b."""
        return self._absorptivity_solid_coefficient_b

    @absorptivity_solid_coefficient_b.setter
    def absorptivity_solid_coefficient_b(self, value: float):
        """Set absorptivity_solid_coefficient_b."""
        self._absorptivity_solid_coefficient_b = value

    @property
    def anisotropic_strain_coefficient_parallel(self) -> float:
        """Multiplier on the predicted strain in the direction that the laser
        is scanning for the major fill rasters."""
        return self._anisotropic_strain_coefficient_parallel

    @anisotropic_strain_coefficient_parallel.setter
    def anisotropic_strain_coefficient_parallel(self, value: float):
        """Set anisotropic_strain_coefficient_parallel."""
        self._anisotropic_strain_coefficient_parallel = value

    @property
    def anisotropic_strain_coefficient_perpendicular(self) -> float:
        """Multiplier on the predicted strain orthogonal to the direction that
        the laser is scanning for the major fill rasters and in the plane of
        the surface of the build plate."""
        return self._anisotropic_strain_coefficient_perpendicular

    @anisotropic_strain_coefficient_perpendicular.setter
    def anisotropic_strain_coefficient_perpendicular(self, value: float):
        """Set anisotropic_strain_coefficient_perpendicular."""
        self._anisotropic_strain_coefficient_perpendicular = value

    @property
    def anisotropic_strain_coefficient_z(self) -> float:
        """Multiplier on the predicted strain in the Z direction."""
        return self._anisotropic_strain_coefficient_z

    @anisotropic_strain_coefficient_z.setter
    def anisotropic_strain_coefficient_z(self, value: float):
        """Set anisotropic_strain_coefficient_z."""
        self._anisotropic_strain_coefficient_z = value

    @property
    def elastic_modulus(self) -> float:
        """Elastic modulus (Pa)."""
        return self._elastic_modulus

    @elastic_modulus.setter
    def elastic_modulus(self, value: float):
        """Set elastic_modulus."""
        self._elastic_modulus = value

    @property
    def hardening_factor(self) -> float:
        """Factor relating the elastic modulus to the tangent modulus for
        plasticity simulations (tangent modulus = elastic modulus * hardening factor )."""
        return self._hardening_factor

    @hardening_factor.setter
    def hardening_factor(self, value: float):
        """Set hardening_factor."""
        self._hardening_factor = value

    @property
    def liquidus_temperature(self) -> float:
        """Minimum temperature at which the material is completely liquid (K)."""
        return self._liquidus_temperature

    @liquidus_temperature.setter
    def liquidus_temperature(self, value: float):
        """Set liquidus_temperature."""
        self._liquidus_temperature = value

    @property
    def material_yield_strength(self) -> float:
        """Material yield strength (Pa)."""
        return self._material_yield_strength

    @material_yield_strength.setter
    def material_yield_strength(self, value: float):
        """Set material_yield_strength."""
        self._material_yield_strength = value

    @property
    def name(self) -> str:
        """Name of material."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set name."""
        self._name = value

    @property
    def nucleation_constant_bulk(self) -> float:
        """Controls the homogeneous nucleation rate (in bulk of the microstructure
        simulation domain) during solidification (1/m^2/K^2)."""
        return self._nucleation_constant_bulk

    @nucleation_constant_bulk.setter
    def nucleation_constant_bulk(self, value: float):
        """Set nucleation_constant_bulk."""
        self._nucleation_constant_bulk = value

    @property
    def nucleation_constant_interface(self) -> float:
        """Controls the heterogeneous nucleation rate (on existing solid interfaces)
        during solidification (1/m/K^2)."""
        return self._nucleation_constant_interface

    @nucleation_constant_interface.setter
    def nucleation_constant_interface(self, value: float):
        """Set nucleation_constant_interface."""
        self._nucleation_constant_interface = value

    @property
    def penetration_depth_maximum(self) -> float:
        """Penetration depth maximum."""
        return self._penetration_depth_maximum

    @penetration_depth_maximum.setter
    def penetration_depth_maximum(self, value: float):
        """Set penetration_depth_maximum."""
        self._penetration_depth_maximum = value

    @property
    def penetration_depth_minimum(self) -> float:
        """Penetration depth minimum."""
        return self._penetration_depth_minimum

    @penetration_depth_minimum.setter
    def penetration_depth_minimum(self, value: float):
        """Set penetration_depth_minimum."""
        self._penetration_depth_minimum = value

    @property
    def penetration_depth_powder_coefficient_a(self) -> float:
        """Penetration depth powder coefficient a."""
        return self._penetration_depth_powder_coefficient_a

    @penetration_depth_powder_coefficient_a.setter
    def penetration_depth_powder_coefficient_a(self, value: float):
        """Set penetration_depth_powder_coefficient_a."""
        self._penetration_depth_powder_coefficient_a = value

    @property
    def penetration_depth_powder_coefficient_b(self) -> float:
        """Penetration depth powder coefficient b."""
        return self._penetration_depth_powder_coefficient_b

    @penetration_depth_powder_coefficient_b.setter
    def penetration_depth_powder_coefficient_b(self, value: float):
        """Set penetration_depth_powder_coefficient_b."""
        self._penetration_depth_powder_coefficient_b = value

    @property
    def penetration_depth_solid_coefficient_a(self) -> float:
        """Penetration depth solid coefficient a."""
        return self._penetration_depth_solid_coefficient_a

    @penetration_depth_solid_coefficient_a.setter
    def penetration_depth_solid_coefficient_a(self, value: float):
        """Set penetration_depth_solid_coefficient_a."""
        self._penetration_depth_solid_coefficient_a = value

    @property
    def penetration_depth_solid_coefficient_b(self) -> float:
        """Penetration depth solid coefficient b."""
        return self._penetration_depth_solid_coefficient_b

    @penetration_depth_solid_coefficient_b.setter
    def penetration_depth_solid_coefficient_b(self, value: float):
        """Set penetration_depth_solid_coefficient_b."""
        self._penetration_depth_solid_coefficient_b = value

    @property
    def poisson_ratio(self) -> float:
        """Poisson ratio."""
        return self._poisson_ratio

    @poisson_ratio.setter
    def poisson_ratio(self, value: float):
        """Set poisson_ratio."""
        self._poisson_ratio = value

    @property
    def powder_packing_density(self) -> float:
        """Density of powder material relative to the solid."""
        return self._powder_packing_density

    @powder_packing_density.setter
    def powder_packing_density(self, value: float):
        """Set powder_packing_density."""
        self._powder_packing_density = value

    @property
    def purging_gas_convection_coefficient(self) -> float:
        """Convection coefficient between the solid and gas during processing."""
        return self._purging_gas_convection_coefficient

    @purging_gas_convection_coefficient.setter
    def purging_gas_convection_coefficient(self, value: float):
        """Set purging_gas_convection_coefficient."""
        self._purging_gas_convection_coefficient = value

    @property
    def solid_density_at_room_temperature(self) -> float:
        """Density of bulk material at room temperature, 298 K (kg/m^3)."""
        return self._solid_density_at_room_temperature

    @solid_density_at_room_temperature.setter
    def solid_density_at_room_temperature(self, value: float):
        """Set solid_density_at_room_temperature."""
        self._solid_density_at_room_temperature = value

    @property
    def solid_specific_heat_at_room_temperature(self) -> float:
        """Specific heat of bulk material at room temperature, 298 K (J/kg/K)."""
        return self._solid_specific_heat_at_room_temperature

    @solid_specific_heat_at_room_temperature.setter
    def solid_specific_heat_at_room_temperature(self, value: float):
        """Set solid_specific_heat_at_room_temperature."""
        self._solid_specific_heat_at_room_temperature = value

    @property
    def solid_thermal_conductivity_at_room_temperature(self) -> float:
        """Thermal conductivity of bulk material at room temperature, 298 K (W/m/K)."""
        return self._solid_thermal_conductivity_at_room_temperature

    @solid_thermal_conductivity_at_room_temperature.setter
    def solid_thermal_conductivity_at_room_temperature(self, value: float):
        """Set solid_thermal_conductivity_at_room_temperature."""
        self._solid_thermal_conductivity_at_room_temperature = value

    @property
    def solidus_temperature(self) -> float:
        """Maximum temperature at which the material is completely solid (K)."""
        return self._solidus_temperature

    @solidus_temperature.setter
    def solidus_temperature(self, value: float):
        """Set solidus_temperature."""
        self._solidus_temperature = value

    @property
    def strain_scaling_factor(self) -> float:
        """Strain scaling factor."""
        return self._strain_scaling_factor

    @strain_scaling_factor.setter
    def strain_scaling_factor(self, value: float):
        """Set strain_scaling_factor."""
        self._strain_scaling_factor = value

    @property
    def support_yield_strength_ratio(self) -> float:
        """Factor to reduce the yield strength and elastic modulus of support material."""
        return self._support_yield_strength_ratio

    @support_yield_strength_ratio.setter
    def support_yield_strength_ratio(self, value: float):
        """Set support_yield_strength_ratio."""
        self._support_yield_strength_ratio = value

    @property
    def thermal_expansion_coefficient(self) -> float:
        """Coefficient of thermal expansion (1/K)."""
        return self._thermal_expansion_coefficient

    @thermal_expansion_coefficient.setter
    def thermal_expansion_coefficient(self, value: float):
        """Set thermal_expansion_coefficient."""
        self._thermal_expansion_coefficient = value

    @property
    def vaporization_temperature(self) -> float:
        """Temperature at which material has completely changed from liquid to vapor (K)."""
        return self._vaporization_temperature

    @vaporization_temperature.setter
    def vaporization_temperature(self, value: float):
        """Set vaporization_temperature (K)."""
        self._vaporization_temperature = value

    @property
    def characteristic_width_data(self) -> list[CharacteristicWidthDataPoint]:
        """List of :class:`CharacteristicWidthDataPoint`."""
        return self._characteristic_width_data

    @characteristic_width_data.setter
    def characteristic_width_data(self, value: list[CharacteristicWidthDataPoint]):
        """Set characteristic_width_data."""
        if not isinstance(value, collections.abc.Sequence):
            raise ValueError(
                "Invalid object type, {}, passed to characteristic_width_data()".format(type(value))
            )
        self._characteristic_width_data = value

    @property
    def thermal_properties_data(self) -> list[ThermalPropertiesDataPoint]:
        """List of :class:`ThermalPropertiesDataPoint`."""
        return self._thermal_properties_data

    @thermal_properties_data.setter
    def thermal_properties_data(self, value: list[ThermalPropertiesDataPoint]):
        """Set thermal_properties_data."""
        if not isinstance(value, collections.abc.Sequence):
            raise ValueError(
                "Invalid object type, {}, passed to thermal_properties_data()".format(type(value))
            )
        self._thermal_properties_data = value

    @staticmethod
    def _from_material_message(msg: MaterialMessage):
        """Create an ``AdditiveMaterial`` object from a material message received from
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
        """Create a material message from this ``AdditiveMaterial`` to send to the Additive service."""
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
