from ansys.api.additive.v0.additive_domain_pb2 import (
    CharacteristicWidthDataPoint as CharacteristicWidthDataPointMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    ThermalCharacteristicDataPoint as ThermalCharacteristicDataPointMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import AdditiveMaterial as MaterialMessage


class AdditiveMaterial:
    """Material parameters related to additive manufacturing

    Properties
    ----------

    absorptivity_maximum : float
    absorptivity_minimum : float
    absorptivity_powder_coefficient_a : float
    absorptivity_powder_coefficient_b : float
    absorptivity_solid_coefficient_a : float
    absorptivity_solid_coefficient_b : float
    anisotropic_strain_coefficient_parallel : float
    anisotropic_strain_coefficient_perpendicular : float
    anisotropic_strain_coefficient_z : float
    elastic_modulus : float
    hardening_factor : float
    liquidus_temperature : float
    material_yield_strength : float
    name : str
    nucleation_constant_bulk : float
    nucleation_constant_interface : float
    penetration_depth_maximum : float
    penetration_depth_minimum : float
    penetration_depth_powder_coefficient_a : float
    penetration_depth_powder_coefficient_b : float
    penetration_depth_solid_coefficient_a : float
    penetration_depth_solid_coefficient_b : float
    poisson_ratio : float
    powder_packing_density : float
    purging_gas_convection_coefficient : float
    solid_density_at_room_temperature : float
    solid_specific_heat_at_room_temperature : float
    solid_thermal_conductivity_at_room_temperature : float
    solidus_temperature : float
    strain_scaling_factor : float
    support_yield_strength_ratio : float
    thermal_expansion_coefficient : float
    vaporization_temperature : float
    characteristic_width_data : CharacteristicWidthDataPoint[]
    thermal_characteristic_data : ThermalCharacteristicDataPoint[]

    """

    __PROPERTIES = [
        "absorptivity_maximum",
        "absorptivity_minimum",
        "absorptivity_powder_coefficient_a",
        "absorptivity_powder_coefficient_b",
        "absorptivity_solid_coefficient_a",
        "absorptivity_solid_coefficient_b",
        "anisotropic_strain_coefficient_parallel",
        "anisotropic_strain_coefficient_perpendicular",
        "anisotropic_strain_coefficient_z",
        "elastic_modulus",
        "hardening_factor",
        "liquidus_temperature",
        "material_yield_strength",
        "name",
        "nucleation_constant_bulk",
        "nucleation_constant_interface",
        "penetration_depth_maximum",
        "penetration_depth_minimum",
        "penetration_depth_powder_coefficient_a",
        "penetration_depth_powder_coefficient_b",
        "penetration_depth_solid_coefficient_a",
        "penetration_depth_solid_coefficient_b",
        "poisson_ratio",
        "powder_packing_density",
        "purging_gas_convection_coefficient",
        "solid_density_at_room_temperature",
        "solid_specific_heat_at_room_temperature",
        "solid_thermal_conductivity_at_room_temperature",
        "solidus_temperature",
        "strain_scaling_factor",
        "support_yield_strength_ratio",
        "thermal_expansion_coefficient",
        "vaporization_temperature",
    ]

    def __init__(self, **kwargs):
        for p in self.__PROPERTIES:
            if p == "name":
                setattr(self, p, "")
            else:
                setattr(self, p, 0)
        self.characteristic_width_data = []
        self.thermal_characteristic_data = []
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)

    def __repr__(self) -> str:
        desc = self.__class__.__name__ + "\n"
        for p in self.__PROPERTIES:
            desc = desc + "{}: {}\n".format(p, getattr(self, p))
        desc = (
            desc
            + "characteristic_width_data: CharacteristicWidthDataPoint[]\n"
            + "thermal_characteristic_data: ThermalCharacteristicDataPoint[]\n"
        )
        return desc

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, AdditiveMaterial):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(__o, k):
                return False
        return True

    @classmethod
    def from_material_message(cls, msg: MaterialMessage):
        """Create an AdditiveMaterial from a MaterialMessage"""
        if not isinstance(msg, MaterialMessage):
            raise ValueError("Invalid object passed to constructor of " + cls.__class__.__name__)
        material = AdditiveMaterial()
        for p in cls.__PROPERTIES:
            setattr(material, p, getattr(msg, p))
        for c in msg.characteristic_width_data_set.characteristic_width_data_points:
            material.characteristic_width_data.append(
                CharacteristicWidthDataPoint.from_characteristic_width_data_point_message(c)
            )
        for t in msg.thermal_characteristic_data_set.thermal_characteristic_data_points:
            material.thermal_characteristic_data.append(
                ThermalCharacteristicDataPoint.from_thermal_characteristic_data_point_message(t)
            )
        return material

    def to_material_message(self) -> MaterialMessage:
        msg = MaterialMessage()
        for p in self.__PROPERTIES:
            setattr(msg, p, getattr(self, p))
        for c in self.characteristic_width_data:
            msg.characteristic_width_data_set.characteristic_width_data_points.append(
                c.to_characteristic_width_data_point_message()
            )
        for t in self.thermal_characteristic_data:
            msg.thermal_characteristic_data_set.thermal_characteristic_data_points.append(
                t.to_thermal_characteristic_data_point_message()
            )
        return msg


class CharacteristicWidthDataPoint:
    """Sample in material characteristic width data file

    Properties
    ----------

    characteristic_width : float
    power : float
    speed : float

    """

    __PROPERTIES = [
        "characteristic_width",
        "power",
        "speed",
    ]

    def __init__(self, **kwargs):
        for p in self.__PROPERTIES:
            setattr(self, p, 0)
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)

    def __repr__(self) -> str:
        repr = self.__class__.__name__ + ":\n"
        for p in self.__PROPERTIES:
            repr = repr + "{} {}\n".format(p, getattr(self, p))
        return repr

    @classmethod
    def from_characteristic_width_data_point_message(cls, msg: CharacteristicWidthDataPointMessage):
        if not isinstance(msg, CharacteristicWidthDataPointMessage):
            raise ValueError("Invalid object passed to constructor of " + cls.__class__.__name__)
        point = cls()
        for p in cls.__PROPERTIES:
            setattr(point, p, getattr(msg, p))
        return point

    def to_characteristic_width_data_point_message(
        self,
    ) -> CharacteristicWidthDataPointMessage:
        message = CharacteristicWidthDataPointMessage()
        for p in self.__PROPERTIES:
            setattr(message, p, getattr(self, p))
        return message

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, CharacteristicWidthDataPoint):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(__o, k):
                return False
        return True


class ThermalCharacteristicDataPoint:
    """Sample in material thermal characteristic lookup file

    Properties
    ----------

    density : float
    density_ratio : float
    specific_heat : float
    specific_heat_ratio : float
    temperature : float
    thermal_conductivity : float
    thermal_conductivity_ratio : float

    """

    __PROPERTIES = [
        "density",
        "density_ratio",
        "specific_heat",
        "specific_heat_ratio",
        "temperature",
        "thermal_conductivity",
        "thermal_conductivity_ratio",
    ]

    def __init__(self, **kwargs):
        for p in self.__PROPERTIES:
            setattr(self, p, 0)
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)

    def __repr__(self) -> str:
        repr = self.__class__.__name__ + ":\n"
        for p in self.__PROPERTIES:
            repr = repr + "{} {}\n".format(p, getattr(self, p))
        return repr

    @classmethod
    def from_thermal_characteristic_data_point_message(
        cls, msg: ThermalCharacteristicDataPointMessage
    ):
        """Create a ThermalCharacteristicDataPoint from a ThermalCharacteristicDataPointMessage"""
        if not isinstance(msg, ThermalCharacteristicDataPointMessage):
            raise ValueError("Invalid object passed to constructor of " + cls.__class__.__name__)
        point = cls()
        for p in cls.__PROPERTIES:
            setattr(point, p, getattr(msg, p))
        return point

    def to_thermal_characteristic_data_point_message(
        self,
    ) -> ThermalCharacteristicDataPointMessage:
        """Create a ThermalCharacteristicDataPointMessage"""
        msg = ThermalCharacteristicDataPointMessage()
        for p in self.__PROPERTIES:
            setattr(msg, p, getattr(self, p))
        return msg

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, ThermalCharacteristicDataPoint):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(__o, k):
                return False
        return True
