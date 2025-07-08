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
"""Provides a container for machine parameters."""

import math

import ansys.additive.core.conversions as conversions
from ansys.api.additive.v0.additive_domain_pb2 import (
    HeatSourceModelType as HeatSourceModelEnumMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    MachineSettings as MachineMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    RingModeCoefficientSets as RingModeCoefficientSetsEnumMessage,
)


class MachineConstants:
    """Provides constants for additive manufacturing machine settings."""

    DEFAULT_LASER_POWER = 195
    """Default laser power (W)."""
    MIN_LASER_POWER = 50
    """Minimum laser power (W)."""
    MAX_LASER_POWER = 700
    """Maximum laser power (W)."""
    DEFAULT_SCAN_SPEED = 1.0
    """Default scan speed (m/s)."""
    MIN_SCAN_SPEED = 0.35
    """Minimum scan speed (m/s)."""
    MAX_SCAN_SPEED = 2.5
    """Maximum scan speed (m/s)."""
    DEFAULT_HEATER_TEMP = 80
    """Default heater temperature (C)."""
    MIN_HEATER_TEMP = 20
    """Minimum heater temperature (C)."""
    MAX_HEATER_TEMP = 500
    """Maximum heater temperature (C)."""
    DEFAULT_LAYER_THICKNESS = 5e-5
    """Default layer thickness (m)."""
    MIN_LAYER_THICKNESS = 1e-5
    """Minimum layer thickness (m)."""
    MAX_LAYER_THICKNESS = 1e-4
    """Maximum layer thickness (m)."""
    DEFAULT_BEAM_DIAMETER = 1e-4
    """Default beam diameter (m)."""
    MIN_BEAM_DIAMETER = 2e-5
    """Minimum beam diameter (m)."""
    MAX_BEAM_DIAMETER = 1.4e-4
    """Maximum beam diameter (m)."""
    DEFAULT_STARTING_LAYER_ANGLE = 57
    """Default starting layer angle (degrees)."""
    MIN_STARTING_LAYER_ANGLE = 0
    """Minimum starting layer angle (degrees)."""
    MAX_STARTING_LAYER_ANGLE = 180
    """Maximum starting layer angle (degrees)."""
    DEFAULT_LAYER_ROTATION_ANGLE = 67
    """Default layer rotation angle (degrees)."""
    MIN_LAYER_ROTATION_ANGLE = 0
    """Minimum layer rotation angle (degrees)."""
    MAX_LAYER_ROTATION_ANGLE = 180
    """Maximum layer rotation angle (degrees)."""
    DEFAULT_HATCH_SPACING = 1e-4
    """Default hatch spacing (m)."""
    MIN_HATCH_SPACING = 6e-5
    """Minimum hatch spacing (m)."""
    MAX_HATCH_SPACING = 2e-4
    """Maximum hatch spacing (m)."""
    DEFAULT_SLICING_STRIPE_WIDTH = 0.01
    """Default slicing stripe width (m)."""
    MIN_SLICING_STRIPE_WIDTH = 0.001
    """Minimum slicing stripe width (m)."""
    MAX_SLICING_STRIPE_WIDTH = 0.1
    """Maximum slicing stripe width (m)."""
    HEAT_SOURCE_MODEL_NAME_GAUSSIAN = "gaussian"
    """Heat source model name for a Gaussian heat source."""
    HEAT_SOURCE_MODEL_NAME_RING = "ring"
    """Heat source model name for a Ring Mode heat source."""
    DEFAULT_HEAT_SOURCE_MODEL_NAME = HEAT_SOURCE_MODEL_NAME_GAUSSIAN
    """Default heat source model type used in simulations."""
    DEFAULT_RING_COEFFICIENTS_SET_INDEX = 0
    """Default ring coefficient set (only applicable for ring heat source)."""
    MIN_RING_COEFFICIENTS_SET_INDEX = 0
    """Minimum ring coefficient set index."""
    MAX_RING_COEFFICIENTS_SET_INDEX = 6
    """Maximum ring coefficient set index."""


class AdditiveMachine:
    """Provides the additive manufacturing machine settings used during simulations.

    Units are SI (m, kg, s, or K) unless otherwise noted. Exceptions include angles,
    which are (degrees), and the heater temperature, which is (degrees) Celsius.
    """

    def __init__(
        self,
        *,
        laser_power: float = MachineConstants.DEFAULT_LASER_POWER,
        scan_speed: float = MachineConstants.DEFAULT_SCAN_SPEED,
        heater_temperature: float = MachineConstants.DEFAULT_HEATER_TEMP,
        layer_thickness: float = MachineConstants.DEFAULT_LAYER_THICKNESS,
        beam_diameter: float = MachineConstants.DEFAULT_BEAM_DIAMETER,
        starting_layer_angle: float = MachineConstants.DEFAULT_STARTING_LAYER_ANGLE,
        layer_rotation_angle: float = MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE,
        hatch_spacing: float = MachineConstants.DEFAULT_HATCH_SPACING,
        slicing_stripe_width: float = MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH,
        heat_source_model: str = MachineConstants.DEFAULT_HEAT_SOURCE_MODEL_NAME,
        ring_mode_coefficient_set_index: int = MachineConstants.DEFAULT_RING_COEFFICIENTS_SET_INDEX,
    ):
        """Initialize an ``AdditiveMachine`` object."""
        self.laser_power = laser_power
        self.scan_speed = scan_speed
        self.heater_temperature = heater_temperature
        self.layer_thickness = layer_thickness
        self.beam_diameter = beam_diameter
        self.starting_layer_angle = starting_layer_angle
        self.layer_rotation_angle = layer_rotation_angle
        self.hatch_spacing = hatch_spacing
        self.slicing_stripe_width = slicing_stripe_width
        self.heat_source_model = heat_source_model
        self.ring_mode_coefficient_set_index = ring_mode_coefficient_set_index

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        repr += "laser_power: {} W\n".format(self._laser_power)
        repr += "scan_speed: {} m/s\n".format(self._scan_speed)
        repr += "heater_temperature: {} °C\n".format(self._heater_temperature)
        repr += "layer_thickness: {} m\n".format(self._layer_thickness)
        repr += "beam_diameter: {} m\n".format(self._beam_diameter)
        repr += "starting_layer_angle: {} °\n".format(self._starting_layer_angle)
        repr += "layer_rotation_angle: {} °\n".format(self._layer_rotation_angle)
        repr += "hatch_spacing: {} m\n".format(self._hatch_spacing)
        repr += "slicing_stripe_width: {} m\n".format(self._slicing_stripe_width)
        repr += "heat_source_model: {}\n".format(self._heat_source_model)
        repr += "ring_mode_coefficient_set_index: {}\n".format(
            self._ring_mode_coefficient_set_index
        )
        return repr

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, AdditiveMachine):
            return False
        return all(getattr(self, k) == getattr(__o, k) for k in self.__dict__)

    def __validate_range(self, value, min, max, name):
        if math.isnan(value):
            raise ValueError("{} must be a number.".format(name))
        if value < min or value > max:
            raise ValueError("{} must be between {} and {}.".format(name, min, max))

    @staticmethod
    def __convert_heat_source_model_str(name: str):
        """Convert a heat source model string to the corresponding enum value."""
        if name == MachineConstants.HEAT_SOURCE_MODEL_NAME_GAUSSIAN:
            return HeatSourceModelEnumMessage.HEAT_SOURCE_MODEL_GAUSSIAN
        elif name == MachineConstants.HEAT_SOURCE_MODEL_NAME_RING:
            return HeatSourceModelEnumMessage.HEAT_SOURCE_MODEL_RING
        else:
            raise ValueError(
                "Invalid heat_source_model name: {}. "
                "Valid values are 'gaussian' and 'ring'.".format(name)
            )

    @staticmethod
    def __convert_heat_source_model_type(modelType: HeatSourceModelEnumMessage):
        """Convert a heat source model enum value to the corresponding string."""
        if modelType == HeatSourceModelEnumMessage.HEAT_SOURCE_MODEL_GAUSSIAN:
            return MachineConstants.HEAT_SOURCE_MODEL_NAME_GAUSSIAN
        elif modelType == HeatSourceModelEnumMessage.HEAT_SOURCE_MODEL_RING:
            return MachineConstants.HEAT_SOURCE_MODEL_NAME_RING
        else:
            raise ValueError("Invalid heat_source_model type: {}. ".format(modelType))

    @staticmethod
    def __convert_ring_mode_coefficients_set_index(index: int):
        """Convert a ring mode coefficient set index to the corresponding enum value."""
        if index == 0:
            return RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_00
        elif index == 1:
            return RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_01
        elif index == 2:
            return RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_02
        elif index == 3:
            return RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_03
        elif index == 4:
            return RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_04
        elif index == 5:
            return RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_05
        elif index == 6:
            return RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_06
        else:
            raise ValueError(
                "Invalid ring_mode_coefficient_set_index: {}. "
                "Valid values are from 0 to 6.".format(index)
            )

    @staticmethod
    def __convert_ring_mode_coefficients_set(coefficients: RingModeCoefficientSetsEnumMessage):
        """Convert a ring mode coefficient set enum value to the corresponding index."""
        if coefficients == RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_00:
            return 0
        elif coefficients == RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_01:
            return 1
        elif coefficients == RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_02:
            return 2
        elif coefficients == RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_03:
            return 3
        elif coefficients == RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_04:
            return 4
        elif coefficients == RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_05:
            return 5
        elif coefficients == RingModeCoefficientSetsEnumMessage.RING_MODE_COEFFICIENT_SET_06:
            return 6
        else:
            raise ValueError("Invalid ring mode coefficient set: {}. ".format(coefficients))

    @property
    def laser_power(self) -> float:
        """Scanning laser power (W).

        Valid values are from 50 to 700 Watts.
        """
        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_LASER_POWER,
            MachineConstants.MAX_LASER_POWER,
            "laser_power",
        )
        self._laser_power = value

    @property
    def scan_speed(self) -> float:
        """Laser scanning speed (m/s).

        Valid values are from 0.35 to 2.5 m/s.
        """
        return self._scan_speed

    @scan_speed.setter
    def scan_speed(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_SCAN_SPEED,
            MachineConstants.MAX_SCAN_SPEED,
            "scan_speed",
        )
        self._scan_speed = value

    @property
    def heater_temperature(self) -> float:
        """Temperature (°C) of the machine build chamber heater.

        Valid values are from 20 to 500 °C.
        """
        return self._heater_temperature

    @heater_temperature.setter
    def heater_temperature(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_HEATER_TEMP,
            MachineConstants.MAX_HEATER_TEMP,
            "heater_temperature",
        )
        self._heater_temperature = value

    @property
    def layer_thickness(self) -> float:
        """Thickness (m) of the powder layer deposited with each pass of the
        recoater blade.

        Valid values are from 1e-5 to 1e-4 m (10 to 100 µm).
        """
        return self._layer_thickness

    @layer_thickness.setter
    def layer_thickness(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_LAYER_THICKNESS,
            MachineConstants.MAX_LAYER_THICKNESS,
            "layer_thickness",
        )
        self._layer_thickness = value

    @property
    def beam_diameter(self) -> float:
        """Width (m) of the laser on the powder or substrate surface defined
        using the D4σ beam diameter definition.

        Usually this value is provided by the machine manufacturer. It is sometimes
        called the laser spot diameter.

        Valid values are from 2e-5 to 1.4e-4 m (20 and 140 µm).
        """
        return self._beam_diameter

    @beam_diameter.setter
    def beam_diameter(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_BEAM_DIAMETER,
            MachineConstants.MAX_BEAM_DIAMETER,
            "beam_diameter",
        )
        self._beam_diameter = value

    @property
    def starting_layer_angle(self) -> float:
        """Angle (°) to scan the first layer at.

        The angle is measured counterclockwise from the X axis, such that a value of 90°
        results in scan lines parallel to the Y axis.

        Valid values are from 0 to 180°.
        """
        return self._starting_layer_angle

    @starting_layer_angle.setter
    def starting_layer_angle(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_STARTING_LAYER_ANGLE,
            MachineConstants.MAX_STARTING_LAYER_ANGLE,
            "starting_layer_angle",
        )
        self._starting_layer_angle = value

    @property
    def layer_rotation_angle(self) -> float:
        """Angle (°) to change the scan vector orientation from layer to layer.

        Valid values are from 0 to 180°.
        """
        return self._layer_rotation_angle

    @layer_rotation_angle.setter
    def layer_rotation_angle(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_LAYER_ROTATION_ANGLE,
            MachineConstants.MAX_LAYER_ROTATION_ANGLE,
            "layer_rotation_angle",
        )
        self._layer_rotation_angle = value

    @property
    def hatch_spacing(self) -> float:
        """Distance (m) between adjacent scan vectors, or hatches, when
        rastering back and forth with the laser.

        Hatch spacing should allow for a slight overlap of scan vector tracks such that
        some of the material re-melts to ensure full coverage of solid material.

        Valid values are from 6e-5 to 2e-4 m (0.06 and 0.2 mm).
        """
        return self._hatch_spacing

    @hatch_spacing.setter
    def hatch_spacing(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_HATCH_SPACING,
            MachineConstants.MAX_HATCH_SPACING,
            "hatch_spacing",
        )
        self._hatch_spacing = value

    @property
    def slicing_stripe_width(self) -> float:
        """Width (m) of a stripe, which is a section of scan lines within a
        layer.

        Valid values are from 0.001 to 0.1 m (1 and 100 mm).
        """
        return self._slicing_stripe_width

    @slicing_stripe_width.setter
    def slicing_stripe_width(self, value: float):
        self.__validate_range(
            value,
            MachineConstants.MIN_SLICING_STRIPE_WIDTH,
            MachineConstants.MAX_SLICING_STRIPE_WIDTH,
            "slicing_stripe_width",
        )
        self._slicing_stripe_width = value

    @property
    def heat_source_model(self) -> str:
        """Type of heat source model used in simulations.
        The heat source model defines how the laser beam is modeled in the simulation.

        Valid values are "gaussian" and "ring".
        """
        return self._heat_source_model

    @heat_source_model.setter
    def heat_source_model(self, value: str):
        self.__convert_heat_source_model_str(value)
        self._heat_source_model = value

    @property
    def ring_mode_coefficient_set_index(self) -> int:
        """Ring mode coefficient set index.

        Valid values are from 0 to 6.
        """
        return self._ring_mode_coefficient_set_index

    @ring_mode_coefficient_set_index.setter
    def ring_mode_coefficient_set_index(self, value: int):
        self.__validate_range(
            value,
            MachineConstants.MIN_RING_COEFFICIENTS_SET_INDEX,
            MachineConstants.MAX_RING_COEFFICIENTS_SET_INDEX,
            "ring_mode_coefficient_set_index",
        )
        self._ring_mode_coefficient_set_index = value

    @staticmethod
    def _from_machine_message(msg: MachineMessage):
        """Create an additive machine from a machine message received from the
        Additive service.
        """
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
                heat_source_model=AdditiveMachine.__convert_heat_source_model_type(
                    modelType=msg.heat_source_model
                ),
                ring_mode_coefficient_set_index=AdditiveMachine.__convert_ring_mode_coefficients_set(
                    coefficients=msg.ring_mode_coefficient_set
                ),
            )
        else:
            raise ValueError("Invalid message type passed to _from_machine_message()")

    def _to_machine_message(self) -> MachineMessage:
        """Create a machine message from the additive machine to send to the
        Additive service.
        """
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
            heat_source_model=self.__convert_heat_source_model_str(self.heat_source_model),
            ring_mode_coefficient_set=self.__convert_ring_mode_coefficients_set_index(
                self.ring_mode_coefficient_set_index
            ),
        )
