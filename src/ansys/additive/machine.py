import math

from ansys.api.additive.v0.additive_domain_pb2 import MachineSettings as MachineMessage

import ansys.additive.conversions as conversions


class AdditiveMachine:
    """Additive manufacturing machine settings used during simulation

    The properties listed use SI units unless otherwise noted.

    ``laser_power``
        Scanning laser power in watts. Valid values are between 50 and 700 Watts,
        default: 195.

    ``scan_speed``
        Laser scanning speed in meters per second. Valid values are between 0.35
        and 2.5 m/s, default: 1.

    ``heater_temperature``
        Temperature of machine build chamber heater in °C. Valid values are between
        20 and 500 °C, default: 80.

    ``layer_thickness``
        The thickness, in meters, of the powder layer coating that is applied with every
        pass of the recoater blade. Valid values are between 1e-5 to 1e-4 m (10 and 100 µm),
        default: 5e-5 m.

    ``beam_diameter``
        The width, in meters, of the laser on the powder or substrate surface defined
        using the D4σ beam diameter definition. Usually this value is provided by the
        machine manufacturer. Sometimes called laser spot diameter. Must be between
        2e-5 to 1.4e-4 m (20 and 140 µm), default: 1e-4.

    ``starting_layer_angle``
         The angle, in degrees, at which the first layer will be scanned. It is measured
         from the X axis, such that a value of 0° results in scan lines parallel to the
         X axis. Must be between 0 and 180°, default: 57.

    ``layer_rotation_angle``
        The angle, in degrees, at which the major scan vector orientation changes from
        layer to layer. Must be between 0 and 180°, default: 67.

    ``hatch_spacing``
        The distance between adjacent scan vectors, or hatches, in meters, when rastering
        back and forth with the laser. Hatch spacing should allow for a slight overlap of
        scan vector tracks such that some of the material re-melts to ensure full coverage
        of solid material. Valid values must be between 6e-5 to 2e-4 m (0.06 and 0.2 mm),
        default: 1e-4.

    ``slicing_stripe_width``
        The width, in meters, of a stripe. A stripe is a section of scan lines within a layer.
        Valid values must be between 0.001 and 0.1 m (1 and 100 mm), default: 0.01.


    """

    __DEFAULT_LASER_POWER = 195
    __DEFAULT_SCAN_SPEED = 1.0
    __DEFAULT_HEATER_TEMP = 80
    __DEFAULT_LAYER_THICKNESS = 5e-5
    __DEFAULT_BEAM_DIAMETER = 1e-4
    __DEFAULT_STARTING_LAYER_ANGLE = 57
    __DEFAULT_LAYER_ROTATION_ANGLE = 67
    __DEFAULT_HATCH_SPACING = 1e-4
    __DEFAULT_SLICING_STRIPE_WIDTH = 0.01

    def __init__(self, **kwargs):
        self.laser_power = self.__DEFAULT_LASER_POWER
        self.scan_speed = self.__DEFAULT_SCAN_SPEED
        self.heater_temperature = self.__DEFAULT_HEATER_TEMP
        self.layer_thickness = self.__DEFAULT_LAYER_THICKNESS
        self.beam_diameter = self.__DEFAULT_BEAM_DIAMETER
        self.starting_layer_angle = self.__DEFAULT_STARTING_LAYER_ANGLE
        self.layer_rotation_angle = self.__DEFAULT_LAYER_ROTATION_ANGLE
        self.hatch_spacing = self.__DEFAULT_HATCH_SPACING
        self.slicing_stripe_width = self.__DEFAULT_SLICING_STRIPE_WIDTH
        for key, value in kwargs.items():
            getattr(self, key)  # raises AttributeError if key not found
            setattr(self, key, value)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, AdditiveMachine):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(__o, k):
                return False
        return True

    @staticmethod
    def from_machine_message(msg: MachineMessage):
        """Create an ``AdditiveMachine`` from a machine message received from the Additive service"""
        if isinstance(msg, MachineMessage):
            return AdditiveMachine(
                laser_power=msg.laser_power,
                scan_speed=msg.scan_speed,
                heater_temperature=conversions.kelvin_to_celsius(msg.heater_temperature),
                layer_thickness=msg.layer_thickness,
                beam_diameter=msg.beam_diameter,
                starting_layer_angle=math.degrees(msg.starting_layer_angle),
                layer_rotation_angle=math.degrees(msg.layer_rotation_angle),
                hatch_spacing=msg.hatch_spacing,
                slicing_stripe_width=msg.slicing_stripe_width,
            )
        else:
            raise ValueError("Invalid message type passed to from_machine_message()")

    def to_machine_message(self) -> MachineMessage:
        """Create a machine message from this ``AdditiveMachine`` to send to the Additive service"""
        return MachineMessage(
            laser_power=self.laser_power,
            scan_speed=self.scan_speed,
            heater_temperature=conversions.celsius_to_kelvin(self.heater_temperature),
            layer_thickness=self.layer_thickness,
            beam_diameter=self.beam_diameter,
            starting_layer_angle=math.radians(self.starting_layer_angle),
            layer_rotation_angle=math.radians(self.layer_rotation_angle),
            hatch_spacing=self.hatch_spacing,
            slicing_stripe_width=self.slicing_stripe_width,
        )
