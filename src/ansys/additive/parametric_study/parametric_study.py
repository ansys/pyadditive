# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Any, Dict, List, Optional, Union

import dill
import numpy as np
import pandas as pd

from ansys.additive import (
    Additive,
    AdditiveMachine,
    AdditiveMaterial,
    MachineConstants,
    MeltPoolColumnNames,
    MicrostructureInput,
    MicrostructureSummary,
    PorosityInput,
    PorositySummary,
    SimulationError,
    SimulationStatus,
    SimulationType,
    SingleBeadInput,
    SingleBeadSummary,
)


class ColumnNames:
    """Column names for the parametric study data frame.

    Values are stored internally as a :class:`Pandas DataFrame <pandas.DataFrame>`.
    The column names are defined here.
    """

    #: Name of the parametric summary project.
    PROJECT = "project"
    #: Iteration number, useful for tracking the sequence of simulation groups.
    ITERATION = "iteration"
    #: Priority value used to determine execution order.
    PRIORITY = "priority"
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
    #: User provided cooling rate used in microstructure simulations (°K/s).
    COOLING_RATE = "cooling_rate"
    #: User provided thermal gradient used in microstructure simulations (°K/m).
    THERMAL_GRADIENT = "thermal_gradient"
    #: User provided melt pool width used in microstructure simulation (m).
    MICRO_MELT_POOL_WIDTH = "micro_melt_pool_width"
    #: User provided melt pool depth used in microstructure simulation (m).
    MICRO_MELT_POOL_DEPTH = "micro_melt_pool_depth"
    #: User provided random seed used in microstructure simulation.
    RANDOM_SEED = "random_seed"
    #: Average microstructure grain size in the XY plane (microns).
    XY_AVERAGE_GRAIN_SIZE = "xy_average_grain_size"
    #: Average microstructure grain size in the XZ plane (microns).
    XZ_AVERAGE_GRAIN_SIZE = "xz_average_grain_size"
    #: Average microstructure grain size in the YY plane (microns).
    YZ_AVERAGE_GRAIN_SIZE = "yz_average_grain_size"
    #: Error message if simulation failed.
    ERROR_MESSAGE = "error_message"


class ParametricStudy:
    """Data storage and utility methods for a parametric study."""

    DEFAULT_ITERATION = 0
    DEFAULT_PRIORITY = 1

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

    def data_frame(self) -> pd.DataFrame:
        """Return a copy of the internal parametric study :class:`DataFrame <pandas.DataFrame>`.
        See :class:`ColumnNames` for the column names used in the returned ``DataFrame``.
        .. note:: Updating the returned ``DataFrame`` will not update the internal ``DataFrame``."""
        return self._data_frame.copy()

    def status(self):
        """Print the current status of the parametric study."""
        name = self.name if self.name else ""
        print(f"Parametric study: {name}")
        print(self._data_frame)

    def add_summaries(
        self,
        summaries: List[Union[SingleBeadSummary, PorositySummary, MicrostructureSummary]],
        iteration: int = DEFAULT_ITERATION,
    ):
        """Add summaries of previously executed simulations to the parametric study.

        This function adds new rows to the parametric study data frame. To update existing rows,
        use :meth:`update`.

        Parameters
        ----------
        summaries : list[SingleBeadSummary | PorositySummary | MicrostructureSummary]
            List of simulation result summaries to add to the parametric study.

        """
        for summary in summaries:
            if isinstance(summary, SingleBeadSummary):
                self._add_single_bead_summary(summary, iteration)
            elif isinstance(summary, PorositySummary):
                self._add_porosity_summary(summary, iteration)
            elif isinstance(summary, MicrostructureSummary):
                self._add_microstructure_summary(summary, iteration)
            else:
                raise TypeError(f"Unknown summary type: {type(summary)}")

    def _add_single_bead_summary(
        self, summary: SingleBeadSummary, iteration: int = DEFAULT_ITERATION
    ):
        median_mp = summary.melt_pool.data_frame().median()
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
        ed = ParametricStudy.energy_density(
            summary.input.machine.laser_power,
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
        )
        row = pd.Series(
            {
                **self.__common_param_to_dict(summary, iteration),
                ColumnNames.TYPE: SimulationType.SINGLE_BEAD,
                ColumnNames.BUILD_RATE: br,
                ColumnNames.ENERGY_DENSITY: ed,
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

    def _add_porosity_summary(self, summary: PorositySummary, iteration: int = DEFAULT_ITERATION):
        br = ParametricStudy.build_rate(
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        ed = ParametricStudy.energy_density(
            summary.input.machine.laser_power,
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        row = pd.Series(
            {
                **self.__common_param_to_dict(summary, iteration),
                ColumnNames.TYPE: SimulationType.POROSITY,
                ColumnNames.BUILD_RATE: br,
                ColumnNames.ENERGY_DENSITY: ed,
                ColumnNames.POROSITY_SIZE_X: summary.input.size_x,
                ColumnNames.POROSITY_SIZE_Y: summary.input.size_y,
                ColumnNames.POROSITY_SIZE_Z: summary.input.size_z,
                ColumnNames.RELATIVE_DENSITY: summary.relative_density,
            }
        )
        self._data_frame = pd.concat([self._data_frame, row.to_frame().T], ignore_index=True)

    def _add_microstructure_summary(
        self, summary: MicrostructureSummary, iteration: int = DEFAULT_ITERATION
    ):
        br = ParametricStudy.build_rate(
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        ed = ParametricStudy.energy_density(
            summary.input.machine.laser_power,
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        random_seed = summary.input.random_seed if summary.input.random_seed > 0 else np.nan
        cooling_rate = thermal_gradient = melt_pool_width = melt_pool_depth = np.nan
        if summary.input.use_provided_thermal_parameters:
            cooling_rate = summary.input.cooling_rate
            thermal_gradient = summary.input.thermal_gradient
            melt_pool_width = summary.input.melt_pool_width
            melt_pool_depth = summary.input.melt_pool_depth

        row = pd.Series(
            {
                **self.__common_param_to_dict(summary, iteration),
                ColumnNames.TYPE: SimulationType.MICROSTRUCTURE,
                ColumnNames.BUILD_RATE: br,
                ColumnNames.ENERGY_DENSITY: ed,
                ColumnNames.MICRO_SENSOR_DIM: summary.input.sensor_dimension,
                ColumnNames.MICRO_MIN_X: summary.input.sample_min_x,
                ColumnNames.MICRO_MIN_Y: summary.input.sample_min_y,
                ColumnNames.MICRO_MIN_Z: summary.input.sample_min_z,
                ColumnNames.MICRO_SIZE_X: summary.input.sample_size_x,
                ColumnNames.MICRO_SIZE_Y: summary.input.sample_size_y,
                ColumnNames.MICRO_SIZE_Z: summary.input.sample_size_z,
                ColumnNames.COOLING_RATE: cooling_rate,
                ColumnNames.THERMAL_GRADIENT: thermal_gradient,
                ColumnNames.MICRO_MELT_POOL_WIDTH: melt_pool_width,
                ColumnNames.MICRO_MELT_POOL_DEPTH: melt_pool_depth,
                ColumnNames.RANDOM_SEED: random_seed,
                ColumnNames.XY_AVERAGE_GRAIN_SIZE: summary.xy_average_grain_size,
                ColumnNames.XZ_AVERAGE_GRAIN_SIZE: summary.xz_average_grain_size,
                ColumnNames.YZ_AVERAGE_GRAIN_SIZE: summary.yz_average_grain_size,
            }
        )
        self._data_frame = pd.concat([self._data_frame, row.to_frame().T], ignore_index=True)

    @staticmethod
    def build_rate(
        scan_speed: float, layer_thickness: float, hatch_spacing: Optional[float] = None
    ) -> float:
        """Calculate the build rate.

        This is an approximate value useful for comparison but not for an accurate prediction
        of build time. The returned value is simply the product of the scan speed, layer thickness,
        and hatch spacing (if provided).

        Parameters
        ----------
        scan_speed : float
            Laser scan speed.
        layer_thickness : float
            Powder deposit layer thickness.
        hatch_spacing : float, optional
            Distance between hatch scan lines.

        Returns
        -------
        float
            The volumetric build rate if hatch spacing is provided,
            otherwise an area build rate. If input units are m/s, m, m,
            the output units are m^3/s or m^2/s.

        """
        if hatch_spacing is None:
            return scan_speed * layer_thickness
        return scan_speed * layer_thickness * hatch_spacing

    @staticmethod
    def energy_density(
        laser_power: float,
        scan_speed: float,
        layer_thickness: float,
        hatch_spacing: Optional[float] = None,
    ) -> float:
        """Calculate the energy density.

        This is an approximate value useful for comparison. The returned value is simply
        the laser power divided by the build rate. See :method:`build_rate`.

        Parameters
        ----------
        laser_power : float
            Laser power.
        scan_speed : float
            Laser scan speed.
        layer_thickness : float
            Powder deposit layer thickness.
        hatch_spacing : float, optional
            Distance between hatch scan lines.

        Returns
        -------
        float
            The volumetric energy density if hatch spacing is provided,
            otherwise an area energy density. If input units are W, m/s, m, m,
            the output units are J/m^3 or J/m^2.

        """
        br = ParametricStudy.build_rate(scan_speed, layer_thickness, hatch_spacing)
        return laser_power / br if br else float("nan")

    def __common_param_to_dict(
        self,
        summary: Union[SingleBeadSummary, PorositySummary, MicrostructureSummary],
        iteration: int = DEFAULT_ITERATION,
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

    def generate_single_bead_permutations(
        self,
        material_name: str,
        laser_powers: List[float],
        scan_speeds: List[float],
        bead_length: float = SingleBeadInput.DEFAULT_BEAD_LENGTH,
        layer_thicknesses: Optional[List[float]] = None,
        heater_temperatures: Optional[List[float]] = None,
        beam_diameters: Optional[List[float]] = None,
        min_area_energy_density: Optional[float] = None,
        max_area_energy_density: Optional[float] = None,
        iteration: int = DEFAULT_ITERATION,
        priority: int = DEFAULT_PRIORITY,
    ):
        """Add single bead permutations to the parametric study.

        Parameters
        ----------
        material_name : str
            The material name.
        laser_powers : List[float]
            Laser powers (W) to use for single bead simulations.
        scan_speeds : List[float]
            Scan speeds (m/s) to use for single bead simulations.
        bead_length : float, optional
            The length of the bead (m).
        layer_thicknesses : Optional[List[float]]
            Layer thicknesses (m) to use for single bead simulations.
            If None, ``MachineConstants.DEFAULT_LAYER_THICKNESS`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        heater_temperatures : Optional[List[float]]
            Heater temperatures (C) to use for single bead simulations.
            If None, ``MachineConstants.DEFAULT_HEATER_TEMP`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        beam_diameters : Optional[List[float]]
            Beam diameters (m) to use for single bead simulations.
            If None, ``MachineConstants.DEFAULT_BEAM_DIAMETER`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        min_area_energy_density : Optional[float]
            The minimum area energy density (J/m^2) to use for single bead simulations.
            Parameter combinations with an area energy density below this value will
            not be included.
            Area energy density is defined as laser power / (layer thickness * scan speed).
        max_area_energy_density : Optional[float]
            The maximum area energy density (J/m^2) to use for single bead simulations.
            Parameter combinations with an area energy density above this value will
            not be included.
            Area energy density is defined as laser power / (layer thickness * scan speed).
        iteration : int, optional
            The iteration number for this set of simulations.
        priority : int, optional
            The priority for this set of simulations.
        """
        lt = layer_thicknesses or [MachineConstants.DEFAULT_LAYER_THICKNESS]
        bd = beam_diameters or [MachineConstants.DEFAULT_BEAM_DIAMETER]
        ht = heater_temperatures or [MachineConstants.DEFAULT_HEATER_TEMP]
        min_aed = min_area_energy_density or 0.0
        max_aed = max_area_energy_density or float("inf")
        for p in laser_powers:
            for v in scan_speeds:
                for l in lt:
                    aed = ParametricStudy.energy_density(p, v, l)
                    if aed < min_aed or aed > max_aed:
                        continue

                    for t in ht:
                        for d in bd:
                            # validate parameters by trying to create input objects
                            try:
                                machine = AdditiveMachine(
                                    laser_power=p,
                                    scan_speed=v,
                                    heater_temperature=t,
                                    layer_thickness=l,
                                    beam_diameter=d,
                                )
                                sb_input = SingleBeadInput(
                                    bead_length=bead_length,
                                    machine=machine,
                                    material=AdditiveMaterial(),
                                )
                            except ValueError as e:
                                print(f"Invalid parameter combination: {e}")
                                continue

                            # add row to parametric study data frame
                            row = pd.Series(
                                {
                                    ColumnNames.PROJECT: self.project_name,
                                    ColumnNames.ITERATION: iteration,
                                    ColumnNames.PRIORITY: priority,
                                    ColumnNames.TYPE: SimulationType.SINGLE_BEAD,
                                    ColumnNames.ID: f"sb_{iteration}_{sb_input.id}",
                                    ColumnNames.STATUS: SimulationStatus.PENDING,
                                    ColumnNames.MATERIAL: material_name,
                                    ColumnNames.HEATER_TEMPERATURE: t,
                                    ColumnNames.LAYER_THICKNESS: l,
                                    ColumnNames.BEAM_DIAMETER: d,
                                    ColumnNames.LASER_POWER: p,
                                    ColumnNames.SCAN_SPEED: v,
                                    ColumnNames.ENERGY_DENSITY: aed,
                                    ColumnNames.BUILD_RATE: ParametricStudy.build_rate(v, l),
                                    ColumnNames.SINGLE_BEAD_LENGTH: bead_length,
                                }
                            )
                            self._data_frame = pd.concat(
                                [self._data_frame, row.to_frame().T], ignore_index=True
                            )

    def generate_porosity_permutations(
        self,
        material_name: str,
        laser_powers: List[float],
        scan_speeds: List[float],
        size_x: float = PorosityInput.DEFAULT_SAMPLE_SIZE,
        size_y: float = PorosityInput.DEFAULT_SAMPLE_SIZE,
        size_z: float = PorosityInput.DEFAULT_SAMPLE_SIZE,
        layer_thicknesses: Optional[List[float]] = None,
        heater_temperatures: Optional[List[float]] = None,
        beam_diameters: Optional[List[float]] = None,
        start_angles: Optional[List[float]] = None,
        rotation_angles: Optional[List[float]] = None,
        hatch_spacings: Optional[List[float]] = None,
        stripe_widths: Optional[List[float]] = None,
        min_energy_density: Optional[float] = None,
        max_energy_density: Optional[float] = None,
        min_build_rate: Optional[float] = None,
        max_build_rate: Optional[float] = None,
        iteration: int = DEFAULT_ITERATION,
        priority: int = DEFAULT_PRIORITY,
    ):
        """Add porosity permutations to the parametric study.

        Parameters
        ----------
        material_name : str
            The material name.
        laser_powers : List[float]
            Laser powers (W) to use for porosity simulations.
        scan_speeds : List[float]
            Scan speeds (m/s) to use for porosity simulations.
        size_x : float, optional
            The size (m) of the porosity sample in the x direction.
            Valid values are between 0.001 and 0.01.
        size_y : float, optional
            The size (m) of the porosity sample in the y direction.
            Valid values are between 0.001 and 0.01.
        size_z : float, optional
            The size (m) of the porosity sample in the z direction.
            Valid values are between 0.001 and 0.01.
        layer_thicknesses : Optional[List[float]]
            Layer thicknesses (m) to use for porosity simulations.
            If None, ``MachineConstants.DEFAULT_LAYER_THICKNESS`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        heater_temperatures : Optional[List[float]]
            Heater temperatures (C) to use for porosity simulations.
            If None, ``MachineConstants.DEFAULT_HEATER_TEMP`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        beam_diameters : Optional[List[float]]
            Beam diameters (m) to use for porosity simulations.
            If None, ``MachineConstants.DEFAULT_BEAM_DIAMETER`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        start_angles : Optional[List[float]]
            Scan angles (deg) for the first layer to use for porosity simulations.
            If None, ``MachineConstants.DEFAULT_STARTING_LAYER_ANGLE`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        rotation_angles : Optional[List[float]]
            Angles (deg) by which the scan direction is rotated with each layer
            to use for porosity simulations.
            If None, ``MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        hatch_spacings : Optional[List[float]]
            Hatch spacings (m) to use for porosity simulations.
            If None, ``MachineConstants.DEFAULT_HATCH_SPACING`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        stripe_widths : Optional[List[float]]
            Stripe widths (m) to use for porosity simulations.
            If None, ``MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        min_energy_density : Optional[float]
            The minimum energy density (J/m^3) to use for porosity simulations.
            Parameter combinations with an area energy density below this value will
            not be included.
            Area energy density is defined as laser power / (layer thickness * scan speed * hatch spacing).
        max_energy_density : Optional[float]
            The maximum energy density (J/m^3) to use for porosity simulations.
            Parameter combinations with an area energy density above this value will
            not be included.
            Energy density is defined as laser power / (layer thickness * scan speed * hatch spacing).
        min_build_rate : Optional[float]
            The minimum build rate (m^3/s) to use for porosity simulations.
            Parameter combinations with a build rate below this value will
            not be included.
            Build rate is defined as layer thickness * scan speed * hatch spacing.
        max_build_rate : Optional[float]
            The maximum build rate (m^3/s) to use for porosity simulations.
            Parameter combinations with a build rate above this value will
            not be included.
            Build rate is defined as layer thickness * scan speed * hatch spacing.
        iteration : int, optional
            The iteration number for this set of simulations.
        priority : int, optional
            The priority for this set of simulations.
        """
        lt = layer_thicknesses or [MachineConstants.DEFAULT_LAYER_THICKNESS]
        bd = beam_diameters or [MachineConstants.DEFAULT_BEAM_DIAMETER]
        ht = heater_temperatures or [MachineConstants.DEFAULT_HEATER_TEMP]
        sa = start_angles or [MachineConstants.DEFAULT_STARTING_LAYER_ANGLE]
        ra = rotation_angles or [MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE]
        hs = hatch_spacings or [MachineConstants.DEFAULT_HATCH_SPACING]
        sw = stripe_widths or [MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH]
        min_ed = min_energy_density or 0.0
        max_ed = max_energy_density or float("inf")
        min_br = min_build_rate or 0.0
        max_br = max_build_rate or float("inf")
        for p in laser_powers:
            for v in scan_speeds:
                for l in lt:
                    for h in hs:
                        br = ParametricStudy.build_rate(v, l, h)
                        ed = ParametricStudy.energy_density(p, v, l, h)
                        if br < min_br or br > max_br or ed < min_ed or ed > max_ed:
                            continue

                        for t in ht:
                            for d in bd:
                                for a in sa:
                                    for r in ra:
                                        for w in sw:
                                            # validate parameters by trying to create input objects
                                            try:
                                                machine = AdditiveMachine(
                                                    laser_power=p,
                                                    scan_speed=v,
                                                    heater_temperature=t,
                                                    layer_thickness=l,
                                                    beam_diameter=d,
                                                    starting_layer_angle=a,
                                                    layer_rotation_angle=r,
                                                    hatch_spacing=h,
                                                    slicing_stripe_width=w,
                                                )
                                                input = PorosityInput(
                                                    size_x=size_x,
                                                    size_y=size_y,
                                                    size_z=size_z,
                                                    machine=machine,
                                                    material=AdditiveMaterial(),
                                                )
                                            except ValueError as e:
                                                print(f"Invalid parameter combination: {e}")
                                                continue

                                            # add row to parametric study data frame
                                            row = pd.Series(
                                                {
                                                    ColumnNames.PROJECT: self.project_name,
                                                    ColumnNames.ITERATION: iteration,
                                                    ColumnNames.PRIORITY: priority,
                                                    ColumnNames.TYPE: SimulationType.POROSITY,
                                                    ColumnNames.ID: f"por_{iteration}_{input.id}",
                                                    ColumnNames.STATUS: SimulationStatus.PENDING,
                                                    ColumnNames.MATERIAL: material_name,
                                                    ColumnNames.HEATER_TEMPERATURE: t,
                                                    ColumnNames.LAYER_THICKNESS: l,
                                                    ColumnNames.BEAM_DIAMETER: d,
                                                    ColumnNames.LASER_POWER: p,
                                                    ColumnNames.SCAN_SPEED: v,
                                                    ColumnNames.START_ANGLE: a,
                                                    ColumnNames.ROTATION_ANGLE: r,
                                                    ColumnNames.HATCH_SPACING: h,
                                                    ColumnNames.STRIPE_WIDTH: w,
                                                    ColumnNames.ENERGY_DENSITY: ed,
                                                    ColumnNames.BUILD_RATE: br,
                                                    ColumnNames.POROSITY_SIZE_X: size_x,
                                                    ColumnNames.POROSITY_SIZE_Y: size_y,
                                                    ColumnNames.POROSITY_SIZE_Z: size_z,
                                                }
                                            )
                                            self._data_frame = pd.concat(
                                                [self._data_frame, row.to_frame().T],
                                                ignore_index=True,
                                            )

    def generate_microstructure_permutations(
        self,
        material_name: str,
        laser_powers: List[float],
        scan_speeds: List[float],
        min_x: float = MicrostructureInput.DEFAULT_POSITION_COORDINATE,
        min_y: float = MicrostructureInput.DEFAULT_POSITION_COORDINATE,
        min_z: float = MicrostructureInput.DEFAULT_POSITION_COORDINATE,
        size_x: float = MicrostructureInput.DEFAULT_SAMPLE_SIZE,
        size_y: float = MicrostructureInput.DEFAULT_SAMPLE_SIZE,
        size_z: float = MicrostructureInput.DEFAULT_SAMPLE_SIZE,
        sensor_dimension: float = MicrostructureInput.DEFAULT_SENSOR_DIMENSION,
        layer_thicknesses: Optional[List[float]] = None,
        heater_temperatures: Optional[List[float]] = None,
        beam_diameters: Optional[List[float]] = None,
        start_angles: Optional[List[float]] = None,
        rotation_angles: Optional[List[float]] = None,
        hatch_spacings: Optional[List[float]] = None,
        stripe_widths: Optional[List[float]] = None,
        min_energy_density: Optional[float] = None,
        max_energy_density: Optional[float] = None,
        min_build_rate: Optional[float] = None,
        max_build_rate: Optional[float] = None,
        cooling_rate: Optional[float] = None,
        thermal_gradient: Optional[float] = None,
        melt_pool_width: Optional[float] = None,
        melt_pool_depth: Optional[float] = None,
        random_seed: Optional[int] = None,
        iteration: int = DEFAULT_ITERATION,
        priority: int = DEFAULT_PRIORITY,
    ):
        """Add microstructure permutations to the parametric study.

        Parameters
        ----------
        material_name : str
            The material name.
        laser_powers : List[float]
            Laser powers (W) to use for microstructure simulations.
        scan_speeds : List[float]
            Scan speeds (m/s) to use for microstructure simulations.
        min_x : float, optional
            The minimum x coordinate (m) of the microstructure sample.
        min_y : float, optional
            The minimum y coordinate (m) of the microstructure sample.
        min_z : float, optional
            The minimum z coordinate (m) of the microstructure sample.
        size_x : float, optional
            The size (m) of the microstructure sample in the x direction.
            Valid values are between 0.001 and 0.01.
        size_y : float, optional
            The size (m) of the microstructure sample in the y direction.
            Valid values are between 0.001 and 0.01.
        size_z : float, optional
            The size (m) of the microstructure sample in the z direction.
            Valid values are between 0.001 and 0.01.
        sensor_dimension : float, optional
            The sensor dimension (m) to use for microstructure simulations.
            Valid values are between 0.0001 and 0.001.
            ``size_x`` and ``size_y`` must be greater than ``sensor_dimension`` by 0.0005.
            ``size_z`` must be greater than ``sensor_dimension`` by 0.001.
        layer_thicknesses : Optional[List[float]]
            Layer thicknesses (m) to use for microstructure simulations.
            If None, ``MachineConstants.DEFAULT_LAYER_THICKNESS`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        heater_temperatures : Optional[List[float]]
            Heater temperatures (C) to use for microstructure simulations.
            If None, ``MachineConstants.DEFAULT_HEATER_TEMP`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        beam_diameters : Optional[List[float]]
            Beam diameters (m) to use for microstructure simulations.
            If None, ``MachineConstants.DEFAULT_BEAM_DIAMETER`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        start_angles : Optional[List[float]]
            Scan angles (deg) for the first layer to use for microstructure simulations.
            If None, ``MachineConstants.DEFAULT_STARTING_LAYER_ANGLE`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        rotation_angles : Optional[List[float]]
            Angles (deg) by which the scan direction is rotated with each layer
            to use for microstructure simulations.
            If None, ``MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        hatch_spacings : Optional[List[float]]
            Hatch spacings (m) to use for microstructure simulations.
            If None, ``MachineConstants.DEFAULT_HATCH_SPACING`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        stripe_widths : Optional[List[float]]
            Stripe widths (m) to use for microstructure simulations.
            If None, ``MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH`` is used.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        min_energy_density : Optional[float]
            The minimum energy density (J/m^3) to use for microstructure simulations.
            Parameter combinations with an area energy density below this value will
            not be included.
            Area energy density is defined as laser power / (layer thickness * scan speed * hatch spacing).
        max_energy_density : Optional[float]
            The maximum energy density (J/m^3) to use for microstructure simulations.
            Parameter combinations with an area energy density above this value will
            not be included.
            Energy density is defined as laser power / (layer thickness * scan speed * hatch spacing).
        min_build_rate : Optional[float]
            The minimum build rate (m^3/s) to use for microstructure simulations.
            Parameter combinations with a build rate below this value will
            not be included.
            Build rate is defined as layer thickness * scan speed * hatch spacing.
        max_build_rate : Optional[float]
            The maximum build rate (m^3/s) to use for microstructure simulations.
            Parameter combinations with a build rate above this value will
            not be included.
            Build rate is defined as layer thickness * scan speed * hatch spacing.
        cooling_rate : Optional[float]
            The cooling rate (K/s) to use for microstructure simulations.
            If None, and ``thermal_gradient``, ``melt_pool_width``, and ``melt_pool_depth``
            are None, it will be calculated. If None and any of the other three parameters
            are not None, it will be set to ``MachineConstants.DEFAULT_COOLING_RATE``.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        thermal_gradient : Optional[float]
            The thermal gradient (K/m) to use for microstructure simulations.
            If None, and ``cooling_rate``, ``melt_pool_width``, and ``melt_pool_depth``
            are None, it will be calculated. If None and any of the other three parameters
            are not None, it will be set to ``MachineConstants.DEFAULT_THERMAL_GRADIENT``.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        melt_pool_width : Optional[float]
            The melt pool width (m) to use for microstructure simulations.
            If None, and ``cooling_rate``, ``thermal_gradient``, and ``melt_pool_depth``
            are None, it will be calculated. If None and any of the other three parameters
            are not None, it will be set to ``MachineConstants.DEFAULT_MELT_POOL_WIDTH``.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        melt_pool_depth : Optional[float]
            The melt pool depth (m) to use for microstructure simulations.
            If None, and ``cooling_rate``, ``thermal_gradient``, and ``melt_pool_width``
            are None, it will be calculated. If None and any of the other three parameters
            are not None, it will be set to ``MachineConstants.DEFAULT_MELT_POOL_DEPTH``.
            See :class:`MachineConstants <ansys.additive.machine.MachineConstants>`.
        random_seed : Optional[int]
            The random seed to use for microstructure simulations. If None,
            an automatically generated random seed will be used.
            Valid values are between 1 and 2^31 - 1.
        iteration : int, optional
            The iteration number for this set of simulations.

        priority : int, optional
            The priority for this set of simulations.
        """
        lt = layer_thicknesses or [MachineConstants.DEFAULT_LAYER_THICKNESS]
        bd = beam_diameters or [MachineConstants.DEFAULT_BEAM_DIAMETER]
        ht = heater_temperatures or [MachineConstants.DEFAULT_HEATER_TEMP]
        sa = start_angles or [MachineConstants.DEFAULT_STARTING_LAYER_ANGLE]
        ra = rotation_angles or [MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE]
        hs = hatch_spacings or [MachineConstants.DEFAULT_HATCH_SPACING]
        sw = stripe_widths or [MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH]
        min_ed = min_energy_density or 0.0
        max_ed = max_energy_density or float("inf")
        min_br = min_build_rate or 0.0
        max_br = max_build_rate or float("inf")
        # determine if the user provided thermal parameters
        use_thermal_params = (
            (cooling_rate is not None)
            or (thermal_gradient is not None)
            or (melt_pool_width is not None)
            or (melt_pool_depth is not None)
        )
        if use_thermal_params:
            # set any uninitialized thermal parameters to default values
            cooling_rate = cooling_rate or MachineConstants.DEFAULT_COOLING_RATE
            thermal_gradient = thermal_gradient or MachineConstants.DEFAULT_THERMAL_GRADIENT
            melt_pool_width = melt_pool_width or MachineConstants.DEFAULT_MELT_POOL_WIDTH
            melt_pool_depth = melt_pool_depth or MachineConstants.DEFAULT_MELT_POOL_DEPTH

        for p in laser_powers:
            for v in scan_speeds:
                for l in lt:
                    for h in hs:
                        br = ParametricStudy.build_rate(v, l, h)
                        ed = ParametricStudy.energy_density(p, v, l, h)
                        if br < min_br or br > max_br or ed < min_ed or ed > max_ed:
                            continue

                        for t in ht:
                            for d in bd:
                                for a in sa:
                                    for r in ra:
                                        for w in sw:
                                            # validate parameters by trying to create input objects
                                            try:
                                                machine = AdditiveMachine(
                                                    laser_power=p,
                                                    scan_speed=v,
                                                    heater_temperature=t,
                                                    layer_thickness=l,
                                                    beam_diameter=d,
                                                    starting_layer_angle=a,
                                                    layer_rotation_angle=r,
                                                    hatch_spacing=h,
                                                    slicing_stripe_width=w,
                                                )
                                                input = MicrostructureInput(
                                                    sample_min_x=min_x,
                                                    sample_min_y=min_y,
                                                    sample_min_z=min_z,
                                                    sample_size_x=size_x,
                                                    sample_size_y=size_y,
                                                    sample_size_z=size_z,
                                                    sensor_dimension=sensor_dimension,
                                                    use_provided_thermal_parameters=use_thermal_params,
                                                    cooling_rate=cooling_rate
                                                    or MicrostructureInput.DEFAULT_COOLING_RATE,
                                                    thermal_gradient=thermal_gradient
                                                    or MicrostructureInput.DEFAULT_THERMAL_GRADIENT,
                                                    melt_pool_width=melt_pool_width
                                                    or MicrostructureInput.DEFAULT_MELT_POOL_WIDTH,
                                                    melt_pool_depth=melt_pool_depth
                                                    or MicrostructureInput.DEFAULT_MELT_POOL_DEPTH,
                                                    random_seed=random_seed
                                                    or MicrostructureInput.DEFAULT_RANDOM_SEED,
                                                    machine=machine,
                                                    material=AdditiveMaterial(),
                                                )
                                            except ValueError as e:
                                                print(f"Invalid parameter combination: {e}")
                                                continue

                                            # add row to parametric study data frame
                                            row = pd.Series(
                                                {
                                                    ColumnNames.PROJECT: self.project_name,
                                                    ColumnNames.ITERATION: iteration,
                                                    ColumnNames.PRIORITY: priority,
                                                    ColumnNames.TYPE: SimulationType.MICROSTRUCTURE,
                                                    ColumnNames.ID: f"micro_{iteration}_{input.id}",
                                                    ColumnNames.STATUS: SimulationStatus.PENDING,
                                                    ColumnNames.MATERIAL: material_name,
                                                    ColumnNames.HEATER_TEMPERATURE: t,
                                                    ColumnNames.LAYER_THICKNESS: l,
                                                    ColumnNames.BEAM_DIAMETER: d,
                                                    ColumnNames.LASER_POWER: p,
                                                    ColumnNames.SCAN_SPEED: v,
                                                    ColumnNames.START_ANGLE: a,
                                                    ColumnNames.ROTATION_ANGLE: r,
                                                    ColumnNames.HATCH_SPACING: h,
                                                    ColumnNames.STRIPE_WIDTH: w,
                                                    ColumnNames.ENERGY_DENSITY: ed,
                                                    ColumnNames.BUILD_RATE: br,
                                                    ColumnNames.MICRO_MIN_X: min_x,
                                                    ColumnNames.MICRO_MIN_Y: min_y,
                                                    ColumnNames.MICRO_MIN_Z: min_z,
                                                    ColumnNames.MICRO_SIZE_X: size_x,
                                                    ColumnNames.MICRO_SIZE_Y: size_y,
                                                    ColumnNames.MICRO_SIZE_Z: size_z,
                                                    ColumnNames.MICRO_SENSOR_DIM: sensor_dimension,
                                                    ColumnNames.COOLING_RATE: cooling_rate,
                                                    ColumnNames.THERMAL_GRADIENT: thermal_gradient,
                                                    ColumnNames.MICRO_MELT_POOL_WIDTH: melt_pool_width,
                                                    ColumnNames.MICRO_MELT_POOL_DEPTH: melt_pool_depth,
                                                    ColumnNames.RANDOM_SEED: random_seed,
                                                }
                                            )
                                            self._data_frame = pd.concat(
                                                [self._data_frame, row.to_frame().T],
                                                ignore_index=True,
                                            )

    def run_simulations(
        self,
        additive: Additive,
        type: Optional[List[SimulationType]] = None,
        priority: Optional[int] = None,
        workers: int = 1,
        threads: int = 4,
    ):
        """Run the simulations in the parametric study with ``SimulationStatus.PENDING`` in the
        ``ColumnNames.STATUS`` column.

        Execution order is determined by the values in the ``ColumnNames.PRIORITY`` column.
        Lower values are interpreted as having higher priority and will be run first.

        Parameters
        ----------
        additive: Additive
            The :class:`Additive <ansys.additive.additive.Additive>` service to use for running simulations.
        type : Optional[List[SimulationType]], optional
            The type of simulations to run, ``None`` indicates all types.
        priority : Optional[int]
            The priority of simulations to run, ``None`` indicates all priorities.
        workers : int, optional
            The number of workers to use for multiprocessing. Each worker
            will need to be able to check out an Additive license.
        threads : int, optional
            The number of threads to use for each worker. Each thread will
            check out an HPC license.
        """
        if type is None:
            type = [
                SimulationType.SINGLE_BEAD,
                SimulationType.POROSITY,
                SimulationType.MICROSTRUCTURE,
            ]

        df = self._data_frame
        view = df[
            df[ColumnNames.STATUS] == SimulationStatus.PENDING and df[ColumnNames.TYPE].isin(type)
        ]
        if priority is not None:
            view = view[view[ColumnNames.PRIORITY] == priority]
        view = view.sort_values(by=ColumnNames.PRIORITY, ascending=True)

        inputs = []
        for row in view.itertuples():
            material = additive.get_material(row[ColumnNames.MATERIAL])
            if row[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD:
                inputs.append(self._create_single_bead_input(additive, row))
            elif row[ColumnNames.TYPE] == SimulationType.POROSITY:
                inputs.append(self._create_porosity_input(additive, row))
            elif row[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE:
                inputs.append(self._create_microstructure_input(additive, row))
            else:
                raise ValueError(f"Invalid simulation type: {row[ColumnNames.TYPE]}")

        summaries = additive.simulate(inputs, workers=workers, threads=threads)

        self.update(summaries)

    def update(
        self, summaries: List[Union[SingleBeadSummary, PorositySummary, MicrostructureSummary]]
    ):
        """Update the results of simulations in the parametric study.

        This method updates values for existing rows in the parametric study data frame. To add new rows
        for completed simulations, use :meth:`add_summaries` instead.

        Parameters
        ----------
        summaries : List[Union[SingleBeadSummary, PorositySummary, MicrostructureSummary, SimulationError]]
            The list of simulation summaries to use for updating parametric study data frame.

        """
        for summary in summaries:
            if isinstance(summary, SingleBeadSummary):
                self._update_single_bead(summary)
            elif isinstance(summary, PorositySummary):
                self._update_porosity(summary)
            elif isinstance(summary, MicrostructureSummary):
                self._update_microstructure(summary)
            elif isinstance(summary, SimulationError):
                idx = self._data_frame[self._data_frame[ColumnNames.ID] == summary.input.id].index
                self._data_frame.loc[idx, ColumnNames.STATUS] = SimulationStatus.ERROR
                self._data_frame.loc[idx, ColumnNames.ERROR_MESSAGE] = summary.message
            else:
                raise ValueError(f"Invalid simulation summary type: {type(summary)}")

    def _update_single_bead(self, summary: SingleBeadSummary):
        """Update the results of a single bead simulation in the parametric study data frame."""
        median_df = summary.melt_pool.data_frame().median()
        idx = self._data_frame[
            (self._data_frame[ColumnNames.ID] == summary.input.id)
            & (self._data_frame[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD)
        ].index
        self._data_frame.loc[idx, ColumnNames.STATUS] = SimulationStatus.COMPLETED
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_WIDTH] = median_df[
            MeltPoolColumnNames.WIDTH
        ]
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_DEPTH] = median_df[
            MeltPoolColumnNames.DEPTH
        ]
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_LENGTH] = median_df[
            MeltPoolColumnNames.LENGTH
        ]
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH] = (
            median_df[MeltPoolColumnNames.LENGTH] / median_df[MeltPoolColumnNames.WIDTH]
            if median_df[MeltPoolColumnNames.WIDTH] > 0
            else np.nan
        )
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_REFERENCE_DEPTH] = median_df[
            MeltPoolColumnNames.REFERENCE_DEPTH
        ]
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_REFERENCE_WIDTH] = median_df[
            MeltPoolColumnNames.REFERENCE_WIDTH
        ]
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] = (
            median_df[MeltPoolColumnNames.REFERENCE_DEPTH]
            / median_df[MeltPoolColumnNames.REFERENCE_WIDTH]
            if median_df[MeltPoolColumnNames.REFERENCE_WIDTH] > 0
            else np.nan
        )

    def _update_porosity(self, summary: PorositySummary):
        """Update the results of a porosity simulation in the parametric study data frame."""
        idx = self._data_frame[
            (self._data_frame[ColumnNames.ID] == summary.input.id)
            & (self._data_frame[ColumnNames.TYPE] == SimulationType.POROSITY)
        ].index

        self._data_frame.loc[idx, ColumnNames.STATUS] = SimulationStatus.COMPLETED
        self._data_frame.loc[idx, ColumnNames.RELATIVE_DENSITY] = summary.relative_density

    def _update_microstructure(self, summary: MicrostructureSummary):
        """Update the results of a microstructure simulation in the parametric study data frame."""
        idx = self._data_frame[
            (self._data_frame[ColumnNames.ID] == summary.input.id)
            & (self._data_frame[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE)
        ].index

        self._data_frame.loc[idx, ColumnNames.STATUS] = SimulationStatus.COMPLETED
        self._data_frame.loc[idx, ColumnNames.XY_AVERAGE_GRAIN_SIZE] = summary.xy_average_grain_size
        self._data_frame.loc[idx, ColumnNames.XZ_AVERAGE_GRAIN_SIZE] = summary.xz_average_grain_size
        self._data_frame.loc[idx, ColumnNames.YZ_AVERAGE_GRAIN_SIZE] = summary.yz_average_grain_size
