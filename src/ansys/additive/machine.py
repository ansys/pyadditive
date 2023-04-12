# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import math

from ansys.api.additive.v0.additive_domain_pb2 import MachineSettings as MachineMessage

import ansys.additive.conversions as conversions


class AdditiveMachine:
    """Additive manufacturing machine settings used during simulation.

    Units are SI (m, kg, s, K) unless otherwise noted. Exceptions include
    angles, which are in degrees, and ``heater_temperature``, which is in
    degrees Celsius.

    """

    __DEFAULT_LASER_POWER = 195
    __MIN_LASER_POWER = 50
    __MAX_LASER_POWER = 700
    __DEFAULT_SCAN_SPEED = 1.0
    __MIN_SCAN_SPEED = 0.35
    __MAX_SCAN_SPEED = 2.5
    __DEFAULT_HEATER_TEMP = 80
    __MIN_HEATER_TEMP = 20
    __MAX_HEATER_TEMP = 500
    __DEFAULT_LAYER_THICKNESS = 5e-5
    __MIN_LAYER_THICKNESS = 1e-5
    __MAX_LAYER_THICKNESS = 1e-4
    __DEFAULT_BEAM_DIAMETER = 1e-4
    __MIN_BEAM_DIAMETER = 2e-5
    __MAX_BEAM_DIAMETER = 1.4e-4
    __DEFAULT_STARTING_LAYER_ANGLE = 57
    __MIN_STARTING_LAYER_ANGLE = 0
    __MAX_STARTING_LAYER_ANGLE = 180
    __DEFAULT_LAYER_ROTATION_ANGLE = 67
    __MIN_LAYER_ROTATION_ANGLE = 0
    __MAX_LAYER_ROTATION_ANGLE = 180
    __DEFAULT_HATCH_SPACING = 1e-4
    __MIN_HATCH_SPACING = 6e-5
    __MAX_HATCH_SPACING = 2e-4
    __DEFAULT_SLICING_STRIPE_WIDTH = 0.01
    __MIN_SLICING_STRIPE_WIDTH = 0.001
    __MAX_SLICING_STRIPE_WIDTH = 0.1

    def __init__(
        self,
        *,
        laser_power: float = __DEFAULT_LASER_POWER,
        scan_speed: float = __DEFAULT_SCAN_SPEED,
        heater_temperature: float = __DEFAULT_HEATER_TEMP,
        layer_thickness: float = __DEFAULT_LAYER_THICKNESS,
        beam_diameter: float = __DEFAULT_BEAM_DIAMETER,
        starting_layer_angle: float = __DEFAULT_STARTING_LAYER_ANGLE,
        layer_rotation_angle: float = __DEFAULT_LAYER_ROTATION_ANGLE,
        hatch_spacing: float = __DEFAULT_HATCH_SPACING,
        slicing_stripe_width: float = __DEFAULT_SLICING_STRIPE_WIDTH
    ):
        self.laser_power = laser_power
        self.scan_speed = scan_speed
        self.heater_temperature = heater_temperature
        self.layer_thickness = layer_thickness
        self.beam_diameter = beam_diameter
        self.starting_layer_angle = starting_layer_angle
        self.layer_rotation_angle = layer_rotation_angle
        self.hatch_spacing = hatch_spacing
        self.slicing_stripe_width = slicing_stripe_width

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, AdditiveMachine):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(__o, k):
                return False
        return True

    def __validate_range(self, value, min, max, name):
        if value < min or value > max:
            raise ValueError("{} must be between {} and {}.".format(name, min, max))

    @property
    def laser_power(self) -> float:
        """Scanning laser power (W).
        Valid values are from 50 to 700 Watts."""
        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: float):
        self.__validate_range(value, self.__MIN_LASER_POWER, self.__MAX_LASER_POWER, "laser_power")
        self._laser_power = value

    @property
    def scan_speed(self) -> float:
        """Laser scanning speed in (m/s).
        Valid values are from 0.35 to 2.5 m/s."""
        return self._scan_speed

    @scan_speed.setter
    def scan_speed(self, value: float):
        self.__validate_range(value, self.__MIN_SCAN_SPEED, self.__MAX_SCAN_SPEED, "scan_speed")
        self._scan_speed = value

    @property
    def heater_temperature(self) -> float:
        """Temperature of machine build chamber heater (°C).
        Valid values are from 20 to 500 °C."""
        return self._heater_temperature

    @heater_temperature.setter
    def heater_temperature(self, value: float):
        self.__validate_range(
            value, self.__MIN_HEATER_TEMP, self.__MAX_HEATER_TEMP, "heater_temperature"
        )
        self._heater_temperature = value

    @property
    def layer_thickness(self) -> float:
        """The thickness of the powder layer deposited with each pass of the recoater blade (m).
        Valid values are from 1e-5 to 1e-4 m (10 and 100 µm)."""
        return self._layer_thickness

    @layer_thickness.setter
    def layer_thickness(self, value: float):
        self.__validate_range(
            value, self.__MIN_LAYER_THICKNESS, self.__MAX_LAYER_THICKNESS, "layer_thickness"
        )
        self._layer_thickness = value

    @property
    def beam_diameter(self) -> float:
        """The width of the laser on the powder or substrate surface defined
        using the D4σ beam diameter definition (m). Usually this value is provided by the
        machine manufacturer. Sometimes called laser spot diameter.
        Valid values are from 2e-5 to 1.4e-4 m (20 and 140 µm)."""
        return self._beam_diameter

    @beam_diameter.setter
    def beam_diameter(self, value: float):
        self.__validate_range(
            value, self.__MIN_BEAM_DIAMETER, self.__MAX_BEAM_DIAMETER, "beam_diameter"
        )
        self._beam_diameter = value

    @property
    def starting_layer_angle(self) -> float:
        """The angle at which the first layer will be scanned (°). It is measured
        counter clockwise from the X axis, such that a value of 90° results in scan lines
        parallel to the Y axis.
        Valid values are from 0 to 180°."""
        return self._starting_layer_angle

    @starting_layer_angle.setter
    def starting_layer_angle(self, value: float):
        self.__validate_range(
            value,
            self.__MIN_STARTING_LAYER_ANGLE,
            self.__MAX_STARTING_LAYER_ANGLE,
            "starting_layer_angle",
        )
        self._starting_layer_angle = value

    @property
    def layer_rotation_angle(self) -> float:
        """The angle, in degrees, at which scan vector orientation changes from
        layer to layer (°).
        Valid values are from 0 to 180°."""
        return self._layer_rotation_angle

    @layer_rotation_angle.setter
    def layer_rotation_angle(self, value: float):
        self.__validate_range(
            value,
            self.__MIN_LAYER_ROTATION_ANGLE,
            self.__MAX_LAYER_ROTATION_ANGLE,
            "layer_rotation_angle",
        )
        self._layer_rotation_angle = value

    @property
    def hatch_spacing(self) -> float:
        """The distance between adjacent scan vectors, or hatches when rastering
        back and forth with the laser (m). Hatch spacing should allow for a slight overlap of
        scan vector tracks such that some of the material re-melts to ensure full coverage
        of solid material.
        Valid values are from 6e-5 to 2e-4 m (0.06 and 0.2 mm)."""
        return self._hatch_spacing

    @hatch_spacing.setter
    def hatch_spacing(self, value: float):
        self.__validate_range(
            value, self.__MIN_HATCH_SPACING, self.__MAX_HATCH_SPACING, "hatch_spacing"
        )
        self._hatch_spacing = value

    @property
    def slicing_stripe_width(self) -> float:
        """The width of a stripe (m). A stripe is a section of scan lines within a layer.
        Valid values must be between 0.001 and 0.1 m (1 and 100 mm)."""
        return self._slicing_stripe_width

    @slicing_stripe_width.setter
    def slicing_stripe_width(self, value: float):
        self.__validate_range(
            value,
            self.__MIN_SLICING_STRIPE_WIDTH,
            self.__MAX_SLICING_STRIPE_WIDTH,
            "slicing_stripe_width",
        )
        self._slicing_stripe_width = value

    @staticmethod
    def _from_machine_message(msg: MachineMessage):
        """Create an ``AdditiveMachine`` from a machine message received from the Additive service."""
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
            raise ValueError("Invalid message type passed to _from_machine_message()")

    def _to_machine_message(self) -> MachineMessage:
        """Create a machine message from this ``AdditiveMachine`` to send to the Additive service."""
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
