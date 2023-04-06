# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
import os

from ansys.api.additive.v0.additive_domain_pb2 import (
    MaterialTuningInput as MaterialTuningInputMessage,
)
from ansys.api.additive.v0.additive_domain_pb2 import (
    MaterialTuningResult as MaterialTuningResultMessage,
)
from ansys.api.additive.v0.additive_materials_pb2 import TuneMaterialRequest


class MaterialTuningInput:
    """Input parameters for tuning a custom material.

    ``id: string``
        User provided identifier for this simulation.
    ``machine: AdditiveMachine``
        Machine related parameters.
    ``material: AdditiveMaterial``
        Material used during simulation.
    ``bead_length: float``
        Length of bead to simulate (m).
    ``bead_type: BeadType``
        Type of bead, either BEAD_ON_POWDER or BEAD_ON_BASE_PLATE.

    """

    def __init__(
        self,
        *,
        id: str,
        experiment_data_file: str,
        material_parameters_file: str,
        thermal_properties_lookup_file: str,
        characteristic_width_lookup_file: str = None,
        allowable_error: float = 0.05,
        max_iterations: int = 15,
        base_plate_temperature: float = 353.15,
    ):
        """
        Initialize a ``MaterialTuningInput`` object.

        Parameters
        ----------

        id: str
            Identifier for this set of tuning simulations.

        experiment_data_file: str
            Name of CSV file containing experimental results data.

        material_parameters_file: str
            Name of JSON file containing material parameters.

        thermal_properties_lookup_file: str
            Name of CSV file containing a lookup table for thermal dependent properties.

        characteristic_width_lookup_file: str
            Optional: Name of CSV file containing a lookup table for the characteristic melt pool
            width at a given temperature. If not provided, the characteristic width will be
            calculated and ``base_plate_temperature`` must be provided.
            Default is None.

        allowable_error: float
            Maximum allowable error between experimental and simulated results.
            Default is 0.05 (5%).

        max_iterations: int
            Maximum number of iterations to perform when trying to match
            simulation results to an experiment if the allowable error is not met.
            Default is 15.

        base_plate_temperature: float
            Temperature of the base plate in Kelvin. This is only required if
            ``characteristic_width_lookup_file`` is ``None``. It is ignored otherwise.
            Default is 353.15 K (80 C).
        """

        if not os.path.isfile(experiment_data_file):
            raise FileNotFoundError(f"File not found: {experiment_data_file}")
        if not os.path.isfile(material_parameters_file):
            raise FileNotFoundError(f"File not found: {material_parameters_file}")
        if not os.path.isfile(thermal_properties_lookup_file):
            raise FileNotFoundError(f"File not found: {thermal_properties_lookup_file}")
        if characteristic_width_lookup_file and not os.path.isfile(
            characteristic_width_lookup_file
        ):
            raise FileNotFoundError(f"File not found: {characteristic_width_lookup_file}")
        self.id = id
        self.allowable_error = allowable_error
        self.max_iterations = max_iterations
        self.experiment_data_file = experiment_data_file
        self.material_parameters_file = material_parameters_file
        self.thermal_properties_lookup_file = thermal_properties_lookup_file
        self.characteristic_width_lookup_file = characteristic_width_lookup_file
        self.base_plate_temperature = base_plate_temperature

    def _to_request(self) -> TuneMaterialRequest:
        """Convert this object into a material tuning request message"""
        input = MaterialTuningInputMessage(
            allowable_error=self.allowable_error,
            max_iterations=self.max_iterations,
            base_plate_temperature=self.base_plate_temperature,
        )
        with open(self.experiment_data_file, "rb") as f:
            input.experiment_data = f.read()
        with open(self.material_parameters_file, "rb") as f:
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
    """Summary of a material tuning simulations."""

    def __init__(self, input: MaterialTuningInput, msg: MaterialTuningResultMessage, out_dir: str):
        """Initialize a ``MaterialTuningSummary`` object."""
        if not isinstance(input, MaterialTuningInput):
            raise TypeError("Parameter 'input' is not a 'MaterialTuningInput' object")
        if not isinstance(msg, MaterialTuningResultMessage):
            raise TypeError("Parameter 'msg' is not a 'MaterialTuningResultMessage' object")
        self._input = input
        os.makedirs(out_dir, exist_ok=True)

        self._optimized_parameters_file = os.path.join(out_dir, "optimized_parameters.csv")
        self._characteristic_width_file = None
        self._log_file = None

        with open(self._optimized_parameters_file, "wb") as f:
            f.write(msg.optimized_parameters)

        if len(msg.characteristic_width_lookup) > 0:
            self._characteristic_width_file = os.path.join(
                out_dir, "characteristic_width_lookup.csv"
            )
            with open(self._characteristic_width_file, "wb") as f:
                f.write(msg.characteristic_width_lookup)
        elif len(input.characteristic_width_lookup_file) > 0:
            self._characteristic_width_file = input.characteristic_width_lookup_file

        if len(msg.log) > 0:
            self._log_file = os.path.join(out_dir, "log.txt")
            with open(self._log_file, "wb") as f:
                f.write(msg.log)

    @property
    def input(self) -> MaterialTuningInput:
        """Material tuning input."""
        return self._input

    @property
    def optimized_parameters_file(self) -> str:
        """Path to optimization parameters file."""
        return self._optimized_parameters_file

    @property
    def characteristic_width_file(self) -> str:
        """Path to characteristic width file or ``None``."""
        return self._characteristic_width_file

    @property
    def log_file(self) -> str:
        """Path to tuning log file or ``None``."""
        return self._log_file

    def __repr__(self):
        repr = type(self).__name__ + "\n"
        for k in self.__dict__:
            repr += k.replace("_", "", 1) + ": " + str(getattr(self, k)) + "\n"
        return repr
