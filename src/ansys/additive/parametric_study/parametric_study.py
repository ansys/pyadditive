# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Any, Dict, List, Optional, Union

import dill
import numpy as np
import pandas as pd

from ansys.additive import (
    MeltPoolColumnNames,
    MicrostructureSummary,
    PorositySummary,
    SingleBeadSummary,
)


class SimulationType:
    """Simulation types for a parametric study."""

    #: Single bead simulation.
    SINGLE_BEAD = "single_bead"
    #: Porosity simulation.
    POROSITY = "porosity"
    #: Microstructure simulation.
    MICROSTRUCTURE = "microstructure"


class SimulationStatus:
    """Simulation status values for a parametric study."""

    #: Simulation is awaiting execution.
    PENDING = "pending"
    #: Simulation was executed.
    COMPLETED = "completed"
    #: Simulation failed.
    FAILURE = "failure"
    #: Do not execute this simulation.
    SKIP = "skip"


class ColumnNames:
    """Column names for the parametric study data frame.

    Values are stored internally as a :class:`Pandas DataFrame <pandas.DataFrame>`.
    The column names are defined here.
    """

    #: Name of the parametric summary project.
    PROJECT = "project"
    #: Iteration number, useful for tracking the sequence of simulation groups.
    ITERATION = "iteration"
    #: Type of simulation, e.g. single bead, porosity, microstructure.
    TYPE = "type"
    #: Identifier for the simulation.
    ID = "id"
    #: Status of the simulation, e.g. pending, success, failure.
    STATUS = "status"
    #: Name of material used during simulation.
    #: See :class:`AdditiveMaterial <ansys.additive.material.AdditiveMaterial>` for more information.
    MATERIAL = "material"
    #: Heater temperature (°C).
    HEATER_TEMPERATURE = "heater_temperature"
    #: Powder deposition layer thickness (m).
    LAYER_THICKNESS = "layer_thickness"
    #: Laser beam diameter (m).
    BEAM_DIAMETER = "beam_diameter"
    #: Laser power (W).
    LASER_POWER = "laser_power"
    #: Laser scan speed (m/s).
    SCAN_SPEED = "scan_speed"
    #: Hatch scan angle for first layer (°).
    START_ANGLE = "start_angle"
    #: Hatch rotation angle for subsequent layers (°).
    ROTATION_ANGLE = "rotation_angle"
    #: Hatch spacing (m).
    HATCH_SPACING = "hatch_spacing"
    #: Stripe width (m).
    STRIPE_WIDTH = "stripe_width"
    #: Energy density calculated as laser power divided by build rate (J/m^2 or J/m^3).
    ENERGY_DENSITY = "energy_density"
    #: Build rate, calculated as layer thickness * scan speed (m^2/s) for single bead simulations,
    #: or as layer thickness * scan speed * hatch spacing (m^3/s) for porosity and microstructure.
    BUILD_RATE = "build_rate"
    #: Length of single bead to simulate (m).
    SINGLE_BEAD_LENGTH = "single_bead_length"
    #: Median melt pool width measured at the top of the powder layer (m).
    MELT_POOL_WIDTH = "melt_pool_width"
    #: Median melt pool depth measured from the top of the powder layer (m).
    MELT_POOL_DEPTH = "melt_pool_depth"
    #: Median melt pool length measured at the top of the powder layer (m).
    MELT_POOL_LENGTH = "melt_pool_length"
    #: Ratio of MELT_POOL_LENGTH to the median melt pool width at the top of the powder layer.
    MELT_POOL_LENGTH_OVER_WIDTH = "melt_pool_length_over_width"
    #: Median melt pool width measured at the top of the base plate (m).
    MELT_POOL_REFERENCE_WIDTH = "melt_pool_ref_width"
    #: Median melt pool depth measured from the top of the base plate (m).
    MELT_POOL_REFERENCE_DEPTH = "melt_pool_ref_depth"
    #: Ratio of MELT_POOL_REFERENCE_DEPTH to MELT_POOL_REFERENCE_WIDTH.
    MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH = "melt_pool_ref_depth_over_width"
    #: X dimension size of porosity sample to simulate (m).
    POROSITY_SIZE_X = "porosity_size_x"
    #: Y dimension size of porosity sample to simulate (m).
    POROSITY_SIZE_Y = "porosity_size_y"
    #: Z dimension size of porosity sample to simulate (m).
    POROSITY_SIZE_Z = "porosity_size_z"
    #: Relative density of simulated porosity sample.
    RELATIVE_DENSITY = "relative_density"
    #: Minimum X dimension position of microstructure sample (m).
    MICRO_MIN_X = "micro_min_x"
    #: Minimum Y dimension position of microstructure sample (m).
    MICRO_MIN_Y = "micro_min_y"
    #: Minimum Z dimension position of microstructure sample (m).
    MICRO_MIN_Z = "micro_min_z"
    #: X dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_X = "micro_size_x"
    #: Y dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_Y = "micro_size_y"
    #: Z dimension size of microstructure sample to simulate (m).
    MICRO_SIZE_Z = "micro_size_z"
    #: Sensor dimension used in microstructure simulations (m).
    MICRO_SENSOR_DIM = "micro_sensor_dim"
    #: User provided random seed used in microstructure simulation.
    #: May be NAN if random seed was not provided.
    RANDOM_SEED = "random_seed"
    #: Average microstructure grain size in the XY plane (microns).
    XY_AVERAGE_GRAIN_SIZE = "xy_average_grain_size"
    #: Average microstructure grain size in the XZ plane (microns).
    XZ_AVERAGE_GRAIN_SIZE = "xz_average_grain_size"
    #: Average microstructure grain size in the YY plane (microns).
    YZ_AVERAGE_GRAIN_SIZE = "yz_average_grain_size"


class ParametricStudy:
    """Data storage and utility methods for a parametric study."""

    def __init__(self, project_name: str):
        self._project_name = project_name
        columns = [getattr(ColumnNames, k) for k in ColumnNames.__dict__ if not k.startswith("_")]
        self._data_frame = pd.DataFrame(columns=columns)

    def save(self, filename):
        """Save the parametric study to a file.

        Parameters
        ----------
        filename : str
            Name of file to save the parametric study to.

        """
        with open(filename, "wb") as f:
            dill.dump(self, f)

    @staticmethod
    def load(filename):
        """Load a parametric study from a file.

        Parameters
        ----------
        filename : str
            Name of file to load the parametric study from.

        Returns
        -------
        ParametricStudy
            The loaded parametric study.

        """
        with open(filename, "rb") as f:
            return dill.load(f)

    @property
    def project_name(self):
        """Name of the parametric study."""
        return self._project_name

    def __eq__(self, other):
        return self.project_name == other.project_name and self._data_frame.equals(
            other._data_frame
        )

    def data_frame(self):
        """Return the parametric study data as a Pandas DataFrame.
        See :class:`ColumnNames` for the column names."""
        return self._data_frame

    def status(self):
        """Print the current status of the parametric study."""
        name = self.name if self.name else ""
        print(f"Parametric study: {name}")
        print(self._data_frame)

    def add_results(
        self,
        results: List[Union[SingleBeadSummary, PorositySummary, MicrostructureSummary]],
        iteration: int = 0,
    ):
        """Add simulation results to the parametric study.

        Parameters
        ----------
        results : list[SingleBeadSummary | PorositySummary | MicrostructureSummary]
            List of simulation result summaries to add to the parametric study.

        """
        for result in results:
            if isinstance(result, SingleBeadSummary):
                self._add_single_bead_result(result, iteration)
            elif isinstance(result, PorositySummary):
                self._add_porosity_result(result, iteration)
            elif isinstance(result, MicrostructureSummary):
                self._add_microstructure_result(result, iteration)
            else:
                raise TypeError(f"Unknown result type: {type(result)}")

    def _add_single_bead_result(self, summary: SingleBeadSummary, iteration: int = 0):
        median_mp = summary.melt_pool.data_frame.median()
        dw = (
            median_mp[MeltPoolColumnNames.REFERENCE_DEPTH]
            / median_mp[MeltPoolColumnNames.REFERENCE_WIDTH]
            if median_mp[MeltPoolColumnNames.REFERENCE_WIDTH]
            else np.nan
        )
        lw = (
            median_mp[MeltPoolColumnNames.LENGTH] / median_mp[MeltPoolColumnNames.WIDTH]
            if median_mp[MeltPoolColumnNames.WIDTH]
            else np.nan
        )
        br = ParametricStudy.build_rate(
            summary.input.machine.scan_speed, summary.input.machine.layer_thickness
        )
        row = pd.Series(
            {
                **self.__common_param_to_dict(summary, iteration),
                ColumnNames.TYPE: SimulationType.SINGLE_BEAD,
                ColumnNames.BUILD_RATE: br,
                ColumnNames.ENERGY_DENSITY: summary.input.machine.laser_power / br,
                ColumnNames.SINGLE_BEAD_LENGTH: summary.input.bead_length,
                ColumnNames.MELT_POOL_WIDTH: median_mp[MeltPoolColumnNames.WIDTH],
                ColumnNames.MELT_POOL_DEPTH: median_mp[MeltPoolColumnNames.DEPTH],
                ColumnNames.MELT_POOL_LENGTH: median_mp[MeltPoolColumnNames.LENGTH],
                ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH: lw,
                ColumnNames.MELT_POOL_REFERENCE_WIDTH: median_mp[
                    MeltPoolColumnNames.REFERENCE_WIDTH
                ],
                ColumnNames.MELT_POOL_REFERENCE_DEPTH: median_mp[
                    MeltPoolColumnNames.REFERENCE_DEPTH
                ],
                ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH: dw,
            }
        )
        self._data_frame = pd.concat([self._data_frame, row.to_frame().T], ignore_index=True)

    def _add_porosity_result(self, summary: PorositySummary, iteration: int = 0):
        br = ParametricStudy.build_rate(
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        row = pd.Series(
            {
                **self.__common_param_to_dict(summary, iteration),
                ColumnNames.TYPE: SimulationType.POROSITY,
                ColumnNames.BUILD_RATE: br,
                ColumnNames.ENERGY_DENSITY: summary.input.machine.laser_power / br,
                ColumnNames.POROSITY_SIZE_X: summary.input.size_x,
                ColumnNames.POROSITY_SIZE_Y: summary.input.size_y,
                ColumnNames.POROSITY_SIZE_Z: summary.input.size_z,
                ColumnNames.RELATIVE_DENSITY: summary.relative_density,
            }
        )
        self._data_frame = pd.concat([self._data_frame, row.to_frame().T], ignore_index=True)

    def _add_microstructure_result(self, summary: MicrostructureSummary, iteration: int = 0):
        br = ParametricStudy.build_rate(
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        random_seed = summary.input.random_seed if summary.input.random_seed > 0 else np.nan
        row = pd.Series(
            {
                **self.__common_param_to_dict(summary, iteration),
                ColumnNames.TYPE: SimulationType.MICROSTRUCTURE,
                ColumnNames.BUILD_RATE: br,
                ColumnNames.ENERGY_DENSITY: summary.input.machine.laser_power / br,
                ColumnNames.MICRO_SENSOR_DIM: summary.input.sensor_dimension,
                ColumnNames.MICRO_MIN_X: summary.input.sample_min_x,
                ColumnNames.MICRO_MIN_Y: summary.input.sample_min_y,
                ColumnNames.MICRO_MIN_Z: summary.input.sample_min_z,
                ColumnNames.MICRO_SIZE_X: summary.input.sample_size_x,
                ColumnNames.MICRO_SIZE_Y: summary.input.sample_size_y,
                ColumnNames.MICRO_SIZE_Z: summary.input.sample_size_z,
                ColumnNames.RANDOM_SEED: random_seed,
                ColumnNames.XY_AVERAGE_GRAIN_SIZE: summary.xy_average_grain_size,
                ColumnNames.XZ_AVERAGE_GRAIN_SIZE: summary.xz_average_grain_size,
                ColumnNames.YZ_AVERAGE_GRAIN_SIZE: summary.yz_average_grain_size,
            }
        )
        self._data_frame = pd.concat([self._data_frame, row.to_frame().T], ignore_index=True)

    @staticmethod
    def build_rate(v: float, lt: float, hs: Optional[float] = None) -> float:
        """Calculate the build rate.

        Parameters
        ----------
        v : float
            Scan speed.
        lt : float
            Layer thickness.
        hs : float, optional
            Hatch spacing.

        Returns
        -------
        float
            The volumetric build rate if hatch spacing is provided,
            otherwise an area build rate. If input units are m/s, m, m,
            the output units are m^3/s or m^2/s.

        """
        if hs is None:
            return v * lt
        return v * lt * hs

    def __common_param_to_dict(
        self,
        summary: Union[SingleBeadSummary, PorositySummary, MicrostructureSummary],
        iteration: int = 0,
    ) -> Dict[str, Any]:
        """Convert common simulation parameters to a dictionary.

        Parameters
        ----------
        summary : Union[SingleBeadSummary, PorositySummary, MicrostructureSummary]
            The summary to convert.

        iteration : int, optional
            The iteration number for this simulation.

        Returns
        -------
        Dict[str, Any]
            The dictionary of common parameters.

        """
        return {
            ColumnNames.PROJECT: self._project_name,
            ColumnNames.ITERATION: iteration,
            ColumnNames.ID: summary.input.id,
            ColumnNames.STATUS: SimulationStatus.COMPLETED,
            ColumnNames.MATERIAL: summary.input.material.name,
            ColumnNames.HEATER_TEMPERATURE: summary.input.machine.heater_temperature,
            ColumnNames.LAYER_THICKNESS: summary.input.machine.layer_thickness,
            ColumnNames.BEAM_DIAMETER: summary.input.machine.beam_diameter,
            ColumnNames.LASER_POWER: summary.input.machine.laser_power,
            ColumnNames.SCAN_SPEED: summary.input.machine.scan_speed,
            ColumnNames.HATCH_SPACING: summary.input.machine.hatch_spacing,
            ColumnNames.START_ANGLE: summary.input.machine.starting_layer_angle,
            ColumnNames.ROTATION_ANGLE: summary.input.machine.layer_rotation_angle,
            ColumnNames.STRIPE_WIDTH: summary.input.machine.slicing_stripe_width,
        }
