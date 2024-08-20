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
"""Provides input and result summary containers for material tuning."""

import os

from ansys.api.additive.v0.additive_domain_pb2 import (
    MaterialTuningInput as MaterialTuningInputMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    MaterialTuningResult as MaterialTuningResultMessage,
)
from ansys.api.additive.v0.additive_materials_pb2 import TuneMaterialRequest

from ansys.additive.core.simulation_input_base import SimulationInputBase


class MaterialTuningInput(SimulationInputBase):
    """Provides input parameters for tuning a custom material.

    Parameters
    ----------
    experiment_data_file: str
        Name of the CSV file containing the experimental results data.
    material_configuration_file: str
        Name of the JSON file containing the material parameters.
    thermal_properties_lookup_file: str
        Name of the CSV file containing a lookup table for thermal-dependent properties.
    characteristic_width_lookup_file: str, None
        Name of the CSV file containing a lookup table for the characteristic melt pool
        width at a given temperature. The default is ``None``, in which case the characteristic
        width is calculated. However, a value must be provided for the ``base_plate_temperature``
        parameter.
    allowable_error: float, 0.05
        Maximum allowable error between experimental and simulated results.
        The default is ``0.05``, which is 5 percent.
    max_iterations: int, 15
        Maximum number of iterations to perform when trying to match
        simulation results to an experiment if the allowable error is not met.
    base_plate_temperature: float, 353.15
        Temperature of the base plate in Kelvin. This is only required if the
        value for the ``characteristic_width_lookup_file`` parameter is ``None``.
        This value is ignored otherwise. The default is ``353.15`` K, which is 80 C.
    """

    def __init__(
        self,
        *,
        experiment_data_file: str,
        material_configuration_file: str,
        thermal_properties_lookup_file: str,
        characteristic_width_lookup_file: str = None,
        allowable_error: float = 0.05,
        max_iterations: int = 15,
        base_plate_temperature: float = 353.15,
    ):
        """Initialize a MaterialTuningInput object."""
        super().__init__()

        if not os.path.isfile(experiment_data_file):
            raise FileNotFoundError(f"File not found: {experiment_data_file}")
        if not os.path.isfile(material_configuration_file):
            raise FileNotFoundError(f"File not found: {material_configuration_file}")
        if not os.path.isfile(thermal_properties_lookup_file):
            raise FileNotFoundError(f"File not found: {thermal_properties_lookup_file}")
        if characteristic_width_lookup_file and not os.path.isfile(
            characteristic_width_lookup_file
        ):
            raise FileNotFoundError(f"File not found: {characteristic_width_lookup_file}")
        self.allowable_error = allowable_error
        self.max_iterations = max_iterations
        self.experiment_data_file = experiment_data_file
        self.material_configuration_file = material_configuration_file
        self.thermal_properties_lookup_file = thermal_properties_lookup_file
        self.characteristic_width_lookup_file = characteristic_width_lookup_file
        self.base_plate_temperature = base_plate_temperature

    def _to_request(self) -> TuneMaterialRequest:
        """Convert this object into a material tuning request message."""
        input = MaterialTuningInputMessage(
            allowable_error=self.allowable_error,
            max_iterations=self.max_iterations,
            base_plate_temperature=self.base_plate_temperature,
        )
        with open(self.experiment_data_file, "rb") as f:
            input.experiment_data = f.read()
        with open(self.material_configuration_file, "rb") as f:
            input.material_parameters = f.read()
        with open(self.thermal_properties_lookup_file, "rb") as f:
            input.thermal_properties_lookup = f.read()
        if self.characteristic_width_lookup_file:
            with open(self.characteristic_width_lookup_file, "rb") as f:
                input.characteristic_width_lookup = f.read()
        return TuneMaterialRequest(id=self.id, input=input)

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            if k == "_id":
                repr += "id: " + str(self.id) + "\n"
            else:
                repr += k + ": " + str(getattr(self, k)) + "\n"
        return repr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MaterialTuningInput):
            return False
        for k in self.__dict__:
            if getattr(self, k) != getattr(other, k):
                return False
        return True


class MaterialTuningSummary:
    """Provides a summary of material tuning simulations."""

    def __init__(self, input: MaterialTuningInput, msg: MaterialTuningResultMessage, out_dir: str):
        """Initialize a ``MaterialTuningSummary`` object."""
        if not isinstance(input, MaterialTuningInput):
            raise TypeError("Parameter 'input' is not a 'MaterialTuningInput' object")
        if not isinstance(msg, MaterialTuningResultMessage):
            raise TypeError("Parameter 'msg' is not a 'MaterialTuningResultMessage' object")
        self._input = input
        os.makedirs(out_dir, exist_ok=True)

        self._optimized_parameters_file = os.path.join(out_dir, "optimized_parameters.csv")
        self._coefficients_file = None
        self._material_configuration_file = None
        self._characteristic_width_file = None
        self._log_file = None

        with open(self._optimized_parameters_file, "wb") as f:
            f.write(msg.optimized_parameters)

        if msg.coefficients:
            self._coefficients_file = os.path.join(out_dir, "coefficients.csv")
            with open(self._coefficients_file, "wb") as f:
                f.write(msg.coefficients)

        if msg.material_parameters:
            self._material_configuration_file = os.path.join(out_dir, "material_configuration.json")
            with open(self._material_configuration_file, "wb") as f:
                f.write(msg.material_parameters)

        if msg.characteristic_width_lookup:
            self._characteristic_width_file = os.path.join(
                out_dir, "characteristic_width_lookup.csv"
            )
            with open(self._characteristic_width_file, "wb") as f:
                f.write(msg.characteristic_width_lookup)
        elif input.characteristic_width_lookup_file:
            self._characteristic_width_file = input.characteristic_width_lookup_file

        if msg.log:
            self._log_file = os.path.join(out_dir, "log.txt")
            with open(self._log_file, "wb") as f:
                f.write(msg.log)

    @property
    def input(self) -> MaterialTuningInput:
        """Material tuning input."""
        return self._input

    @property
    def optimized_parameters_file(self) -> str:
        """Path to the optimization parameters file."""
        return self._optimized_parameters_file

    @property
    def coefficients_file(self) -> str | None:
        """Path to the calculated coefficients file."""
        return self._coefficients_file

    @property
    def material_configuration_file(self) -> str | None:
        """Path to the updated material properties file.

        Penetration depth and absorptivity coefficients are updated based on the tuning
        results.
        """
        return self._material_configuration_file

    @property
    def characteristic_width_file(self) -> str | None:
        """Path to the characteristic width file or ``None``."""
        return self._characteristic_width_file

    @property
    def log_file(self) -> str:
        """Path to the tuning log file or ``None``."""
        return self._log_file

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
