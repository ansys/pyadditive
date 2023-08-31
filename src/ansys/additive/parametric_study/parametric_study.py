# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import Any, Dict, List, Optional, Union

import dill
import numpy as np
import pandas as pd
import panel as pn

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
import ansys.additive.misc as misc

from .constants import DEFAULT_ITERATION, DEFAULT_PRIORITY, ColumnNames
from .parametric_runner import ParametricRunner
from .parametric_utils import build_rate, energy_density

pn.extension("tabulator")


class ParametricStudy:
    """Provides data storage and utility methods for a parametric study."""

    def __init__(self, project_name: str):
        pn.extension()
        self._project_name = project_name
        columns = [getattr(ColumnNames, k) for k in ColumnNames.__dict__ if not k.startswith("_")]
        self._data_frame = pd.DataFrame(columns=columns)

    @property
    def project_name(self):
        """Name of the parametric study."""
        return self._project_name

    def __eq__(self, other):
        return self.project_name == other.project_name and self._data_frame.equals(
            other._data_frame
        )

    def data_frame(self) -> pd.DataFrame:
        """Return a copy of the internal data frame for the parametric study.

        For the column names used in the returned data frame, see the `:class:`ColumnNames` class.

        .. note::
           Updating the returned data frame does not update the internal data frame.
        """
        return self._data_frame.copy()

    def run_simulations(
        self,
        additive: Additive,
        type: Optional[List[SimulationType]] = None,
        priority: Optional[int] = None,
        # workers: int = 1,
        # threads: int = 4,
    ):
        """Run the simulations in the parametric study with
        ``SimulationStatus.PENDING`` in the ``ColumnNames.STATUS`` column.
        Execution order is determined by the values in the
        ``ColumnNames.PRIORITY`` column. Lower values are interpreted as having
        higher priority and are run first.

        Parameters
        ----------
        additive: :class:`Additive <ansys.additive.additive.Additive>`
            Additive service to use for running simulations.
        type : list[SimulationType], None
            Type of simulations to run. The default is ``None``, in which case
            all simulation types are run.
        priority : int, None
            Priority of simulations to run. The default is ``None``, in which
            case all priorities are run.
        """
        # TODO: Add support for running multiple simulations in parallel
        # once issue https://github.com/ansys-internal/pyadditive/issues/9
        # is resolved
        # workers : int, 1
        #     Number of workers to use for multiprocessing. Each worker
        #     must be able to check out an Additive license.
        # threads : int, 4
        #     Number of threads to use for each worker. Each thread must
        #     be able to check out an HPC license.
        summaries = ParametricRunner.simulate(
            self.data_frame(),
            additive,
            type=type,
            priority=priority,
            # workers=workers,
            # threads=threads,
        )
        self.update(summaries)

    def save(self, filename):
        """Save the parametric study to a file.

        Parameters
        ----------
        filename : str
            Name of the file to save the parametric study to.
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
            Loaded parametric study.
        """
        with open(filename, "rb") as f:
            return dill.load(f)

    def add_summaries(
        self,
        summaries: List[Union[SingleBeadSummary, PorositySummary, MicrostructureSummary]],
        iteration: int = DEFAULT_ITERATION,
    ):
        """Add summaries of previously executed simulations to the parametric
        study.

        This method adds new simulations to the parametric study. To update existing
        simulations, use the :meth:`update` method.

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
        br = build_rate(summary.input.machine.scan_speed, summary.input.machine.layer_thickness)
        ed = energy_density(
            summary.input.machine.laser_power,
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
        )
        row = pd.Series(
            {
                **self._common_param_to_dict(summary, iteration),
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
        br = build_rate(
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        ed = energy_density(
            summary.input.machine.laser_power,
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        row = pd.Series(
            {
                **self._common_param_to_dict(summary, iteration),
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
        br = build_rate(
            summary.input.machine.scan_speed,
            summary.input.machine.layer_thickness,
            summary.input.machine.hatch_spacing,
        )
        ed = energy_density(
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
                **self._common_param_to_dict(summary, iteration),
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

    def _common_param_to_dict(
        self,
        summary: Union[SingleBeadSummary, PorositySummary, MicrostructureSummary],
        iteration: int = DEFAULT_ITERATION,
    ) -> Dict[str, Any]:
        """Convert common simulation parameters to a dictionary.

        Parameters
        ----------
        summary : Union[SingleBeadSummary, PorositySummary, MicrostructureSummary]
            Summary of common simulation parameters to convert.

        iteration : int, DEFAULT_ITERATION
            Iteration number for this simulation.

        Returns
        -------
        Dict[str, Any]
            Dictionary of common simulation parameters.
        """
        return {
            ColumnNames.PROJECT: self._project_name,
            ColumnNames.ITERATION: iteration,
            ColumnNames.ID: self._create_unique_id(id=summary.input.id),
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
            Material name.
        laser_powers : list[float]
            Laser powers (W) to use for single bead simulations.
        scan_speeds : list[float]
            Scan speeds (m/s) to use for single bead simulations.
        bead_length : float, DEFAULT_BEAD_LENGTH
            Length of the bead (m).
        layer_thicknesses : list[float], None
            Layer thicknesses (m) to use for single bead simulations.
            The default is ``None``, in which case ``MachineConstants.DEFAULT_LAYER_THICKNESS``
            is used. For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        heater_temperatures : List[float], None
            Heater temperatures (C) to use for single bead simulations.
            The default is ``None``, in which case ``MachineConstants.DEFAULT_HEATER_TEMP``
            is used. For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        beam_diameters : List[float], None
            Beam diameters (m) to use for single bead simulations.
            The default is ``None``, in which case``MachineConstants.DEFAULT_BEAM_DIAMETER``
            is used. For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        min_area_energy_density : float, None
            Minimum area energy density (J/m^2) to use for single bead simulations.
            Parameter combinations with an area energy density below this value are
            not included. Area energy density is defined as laser power / (layer thickness * scan speed).
        max_area_energy_density : float, None
            Maximum area energy density (J/m^2) to use for single bead simulations.
            Parameter combinations with an area energy density above this value are
            not included. Area energy density is defined as laser power / (layer thickness * scan speed).
        iteration : int, DEFAULT_ITERATION
            Iteration number for this set of simulations.
        priority : int, DEFAULT_PRIORITY
            Priority for this set of simulations.
        """
        lt = (
            layer_thicknesses
            if layer_thicknesses is not None
            else [MachineConstants.DEFAULT_LAYER_THICKNESS]
        )
        bd = (
            beam_diameters
            if beam_diameters is not None
            else [MachineConstants.DEFAULT_BEAM_DIAMETER]
        )
        ht = (
            heater_temperatures
            if heater_temperatures is not None
            else [MachineConstants.DEFAULT_HEATER_TEMP]
        )
        min_aed = min_area_energy_density or 0.0
        max_aed = max_area_energy_density or float("inf")
        for p in laser_powers:
            for v in scan_speeds:
                for l in lt:
                    aed = energy_density(p, v, l)
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
                                    ColumnNames.ID: self._create_unique_id(
                                        prefix=f"sb_{iteration}"
                                    ),
                                    ColumnNames.STATUS: SimulationStatus.PENDING,
                                    ColumnNames.MATERIAL: material_name,
                                    ColumnNames.HEATER_TEMPERATURE: t,
                                    ColumnNames.LAYER_THICKNESS: l,
                                    ColumnNames.BEAM_DIAMETER: d,
                                    ColumnNames.LASER_POWER: p,
                                    ColumnNames.SCAN_SPEED: v,
                                    ColumnNames.ENERGY_DENSITY: aed,
                                    ColumnNames.BUILD_RATE: build_rate(v, l),
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
            Material name.
        laser_powers : list[float]
            Laser powers (W) to use for porosity simulations.
        scan_speeds : list[float]
            Scan speeds (m/s) to use for porosity simulations.
        size_x : float, DEFAULT_SAMPLE_SIZE
            Size (m) of the porosity sample in the x direction.
            Valid values are between 0.001 and 0.01.
        size_y : float, DEFAULT_SAMPLE_SIZE
            Size (m) of the porosity sample in the y direction.
            Valid values are between 0.001 and 0.01.
        size_z : float, DEFAULT_SAMPLE_SIZE
            Size (m) of the porosity sample in the z direction.
            Valid values are between 0.001 and 0.01.
        layer_thicknesses : list[float], None
            Layer thicknesses (m) to use for porosity simulations.
            The default is ``None``, in which case ``MachineConstants.DEFAULT_LAYER_THICKNESS``
            is used. For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        heater_temperatures : list[float], None
            Heater temperatures (C) to use for porosity simulations.
            The default is ``None``, in which case ``MachineConstants.DEFAULT_HEATER_TEMP``
            is used. For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        beam_diameters : list[float], None
            Beam diameters (m) to use for porosity simulations.
            The default is ``None``, in which case ``MachineConstants.DEFAULT_BEAM_DIAMETER``
            is used. For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        start_angles : list[float], None
            Scan angles (deg) for the first layer to use for porosity simulations.
            The default is ``None``, in which case ``MachineConstants.DEFAULT_STARTING_LAYER_ANGLE``
            is used. For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>` class.
        rotation_angles : list[float], None
            Angles (deg) by which the scan direction is rotated with each layer
            to use for porosity simulations. The default is ``None``, in which
            case ``MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE`` is used. For more
            information, see the :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        hatch_spacings : list[float], None
            Hatch spacings (m) to use for porosity simulations. The default is ``None``,
            in which case ``MachineConstants.DEFAULT_HATCH_SPACING`` is used. For more
            information, see the :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        stripe_widths : list[float], None
            Stripe widths (m) to use for porosity simulations. The default is ``None``, in
            which case ``MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH`` is used. For more
            information, see the :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        min_energy_density : float, None
            Minimum energy density (J/m^3) to use for porosity simulations. Parameter combinations
            with an area energy density below this value are not included. Area energy density is
            defined as laser power / (layer thickness * scan speed * hatch spacing).
        max_energy_density : float, None
            Maximum energy density (J/m^3) to use for porosity simulations. Parameter combinations
            with an area energy density above this value are not included. Energy density is defined
            as laser power / (layer thickness * scan speed * hatch spacing).
        min_build_rate : float, None
            Minimum build rate (m^3/s) to use for porosity simulations. Parameter combinations
            with a build rate below this value are not included. Build rate is defined as
            layer thickness * scan speed * hatch spacing.
        max_build_rate : float, None
            Maximum build rate (m^3/s) to use for porosity simulations. Parameter combinations
            with a build rate above this value are not included. Build rate is defined as
            layer thickness * scan speed * hatch spacing.
        iteration : int, DEFAULT_ITERATION
            Iteration number for this set of simulations.
        priority : int, DEFAULT_PRIORITY
            Priority for this set of simulations.
        """
        lt = (
            layer_thicknesses
            if layer_thicknesses is not None
            else [MachineConstants.DEFAULT_LAYER_THICKNESS]
        )
        bd = (
            beam_diameters
            if beam_diameters is not None
            else [MachineConstants.DEFAULT_BEAM_DIAMETER]
        )
        ht = (
            heater_temperatures
            if heater_temperatures is not None
            else [MachineConstants.DEFAULT_HEATER_TEMP]
        )
        sa = (
            start_angles
            if start_angles is not None
            else [MachineConstants.DEFAULT_STARTING_LAYER_ANGLE]
        )
        ra = (
            rotation_angles
            if rotation_angles is not None
            else [MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE]
        )
        hs = (
            hatch_spacings
            if hatch_spacings is not None
            else [MachineConstants.DEFAULT_HATCH_SPACING]
        )
        sw = (
            stripe_widths
            if stripe_widths is not None
            else [MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH]
        )
        min_ed = min_energy_density or 0.0
        max_ed = max_energy_density or float("inf")
        min_br = min_build_rate or 0.0
        max_br = max_build_rate or float("inf")
        for p in laser_powers:
            for v in scan_speeds:
                for l in lt:
                    for h in hs:
                        br = build_rate(v, l, h)
                        ed = energy_density(p, v, l, h)
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
                                                    ColumnNames.ID: self._create_unique_id(
                                                        prefix=f"por_{iteration}"
                                                    ),
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
            Material name.
        laser_powers : list[float]
            Laser powers (W) to use for microstructure simulations.
        scan_speeds : list[float]
            Scan speeds (m/s) to use for microstructure simulations.
        min_x : float, DEFAULT_POSITION_COORDINATE
            Minimum x coordinate (m) of the microstructure sample.
        min_y : float, DEFAULT_POSITION_COORDINATE
            Minimum y coordinate (m) of the microstructure sample.
        min_z : float, DEFAULT_POSITION_COORDINATE
            Minimum z coordinate (m) of the microstructure sample.
        size_x : float, DEFAULT_SAMPLE_SIZE
            Size (m) of the microstructure sample in the x direction.
            Valid values are between 0.001 and 0.01.
        size_y : float, DEFAULT_SAMPLE_SIZE
            Size (m) of the microstructure sample in the y direction.
            Valid values are between 0.001 and 0.01.
        size_z : float, DEFAULT_SAMPLE_SIZE
            Size (m) of the microstructure sample in the z direction.
            Valid values are between 0.001 and 0.01.
        sensor_dimension : float, DEFAULT_SENSOR_DIMENSION
            Sensor dimension (m) to use for microstructure simulations.
            Valid values are between 0.0001 and 0.001. The values for the
            ``size_x`` and ``size_y`` parameters must be greater than the
            ``sensor_dimension`` parameter by 0.0005. The value for the
            ``size_z`` parameter must be greater than ``sensor_dimension``
            parameter by 0.001.
        layer_thicknesses : list[float], None
            Layer thicknesses (m) to use for microstructure simulations.
            The default is ``None``, in which case
            ``MachineConstants.DEFAULT_LAYER_THICKNESS`` is used.
            For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        heater_temperatures : list[float], None
            Heater temperatures (C) to use for microstructure simulations.
            The default is ``None``, in which case
            ``MachineConstants.DEFAULT_HEATER_TEMP`` is used.
            For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>` class.
        beam_diameters : list[float], None
            Beam diameters (m) to use for microstructure simulations. The default is
            ``None``, in which case ``MachineConstants.DEFAULT_BEAM_DIAMETER`` is used.
            For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>` class.
        start_angles : list[float], None
            Scan angles (deg) for the first layer to use for microstructure simulations.
            The default is ``None``, in which case ``MachineConstants.DEFAULT_STARTING_LAYER_ANGLE``
            is used. For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>` class.
        rotation_angles : List[float], None
            Angles (deg) by which the scan direction is rotated with each layer
            to use for microstructure simulations. The default is ``None``, in
            which case ``MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE`` is used.
            For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>` class.
        hatch_spacings : list[float], None
            Hatch spacings (m) to use for microstructure simulations. The default is
            ``None``, in which case ``MachineConstants.DEFAULT_HATCH_SPACING`` is used.
            For more information, see the
            :class:`MachineConstants <ansys.additive.machine.MachineConstants>` class.
        stripe_widths : list[float], None
            Stripe widths (m) to use for microstructure simulations. The default is
            ``None``, in which case``MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH`` is used.
            For more information, see the :class:`MachineConstants <ansys.additive.machine.MachineConstants>`
            class.
        min_energy_density : float, None
            Minimum energy density (J/m^3) to use for microstructure simulations. Parameter combinations
            with an area energy density below this value are not included. Area energy density is defined as
            laser power / (layer thickness * scan speed * hatch spacing).
        max_energy_density : float
            Xaximum energy density (J/m^3) to use for microstructure simulations. Parameter combinations
            with an area energy density above this value are not included. Energy density is defined as
            laser power / (layer thickness * scan speed * hatch spacing).
        min_build_rate : float, None
            Minimum build rate (m^3/s) to use for microstructure simulations. Parameter combinations
            with a build rate below this value are not included. Build rate is defined as
            layer thickness * scan speed * hatch spacing.
        max_build_rate : float, None
            Maximum build rate (m^3/s) to use for microstructure simulations. Parameter combinations
            with a build rate above this value are not included. Build rate is defined as
            layer thickness * scan speed * hatch spacing.
        cooling_rate : float, None
            Cooling rate (K/s) to use for microstructure simulations. The default is ``None``,
            in which case if the values are also ``None`` for the ``thermal_gradient``,
            ``melt_pool_width``, and  ``melt_pool_depth`` parameters, the cooling rate is
            calculated. If the value for the ``cooling_rate`` parameter is ``None`` and any of
            the other three parameters have a value other than ``None``, the cooling rate is set
            to ``MicrostructureInput.DEFAULT_COOLING_RATE``. For more information, see the
            :class:`MicrostructureInput <ansys.additive.machine.MicrostructureInput>` class.
        thermal_gradient : float, None
            Thermal gradient (K/m) to use for microstructure simulations. The default is
            ``None``, in which case if the values are also ``None`` for the ``cooling_rate``,
            ``melt_pool_width``, and ``melt_pool_depth`` parameters, the thermal gradient is
            calculated. If the value for the ``thermal_gradient`` parameter is ``None`` and any
            of the other three parameters have a value other than ``None``, the thermal gradient
            is set to ``MicrostructureInput.DEFAULT_THERMAL_GRADIENT``. For more information,
            see the :class:`MicrostructureInput <ansys.additive.machine.MicrostructureInput>`
            class.
        melt_pool_width : float, None
            Melt pool width (m) to use for microstructure simulations. The default is
            ``None``, in which case if the values are also ``None`` for the ``cooling_rate``,
            ``thermal_gradient``, and ``melt_pool_depth`` parameters, the melt pool width
            is calculated. If the value for the ``melt_pool_width`` parameter is ``None`` and
            any of the other three parameters have a value other than ``None``, the melt pool
            width is set to ``MicrostructureInput.DEFAULT_MELT_POOL_WIDTH``. For more information,
            see the :class:`MicrostructureInput <ansys.additive.machine.MicrostructureInput>` class.
        melt_pool_depth : float, None
            Melt pool depth (m) to use for microstructure simulations. The default is
            ``None``, in which case if the values are also ``None`` for the ``cooling_rate``,
            ``thermal_gradient``, and ``melt_pool_width`` parameters, melt pool depth is
            calculated. If the value for the ``melt_pool_depth`` parameter is ``None`` and any
            of the other three parameters have value other than ``None``, the melt pool depth
            is set to ``MicrostructureInput.DEFAULT_MELT_POOL_DEPTH``. For more information,
            see the :class:`MicrostructureInput <ansys.additive.machine.MicrostructureInput>`
            class.
        random_seed : int, None
            Random seed to use for microstructure simulations. The default is ``None``,
            in which case a random seed is automatically generated. Valid values are between
            1 and 2^31 - 1.
        iteration : int, optiDEFAULT_ITERATION
            Iteration number for this set of simulations.
        priority : int, DEFAULT_PRIORITY
            Priority for this set of simulations.
        """
        lt = (
            layer_thicknesses
            if layer_thicknesses is not None
            else [MachineConstants.DEFAULT_LAYER_THICKNESS]
        )
        bd = (
            beam_diameters
            if beam_diameters is not None
            else [MachineConstants.DEFAULT_BEAM_DIAMETER]
        )
        ht = (
            heater_temperatures
            if heater_temperatures is not None
            else [MachineConstants.DEFAULT_HEATER_TEMP]
        )
        sa = (
            start_angles
            if start_angles is not None
            else [MachineConstants.DEFAULT_STARTING_LAYER_ANGLE]
        )
        ra = (
            rotation_angles
            if rotation_angles is not None
            else [MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE]
        )
        hs = (
            hatch_spacings
            if hatch_spacings is not None
            else [MachineConstants.DEFAULT_HATCH_SPACING]
        )
        sw = (
            stripe_widths
            if stripe_widths is not None
            else [MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH]
        )
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
            cooling_rate = cooling_rate or MicrostructureInput.DEFAULT_COOLING_RATE
            thermal_gradient = thermal_gradient or MicrostructureInput.DEFAULT_THERMAL_GRADIENT
            melt_pool_width = melt_pool_width or MicrostructureInput.DEFAULT_MELT_POOL_WIDTH
            melt_pool_depth = melt_pool_depth or MicrostructureInput.DEFAULT_MELT_POOL_DEPTH

        for p in laser_powers:
            for v in scan_speeds:
                for l in lt:
                    for h in hs:
                        br = build_rate(v, l, h)
                        ed = energy_density(p, v, l, h)
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
                                                    cooling_rate=MicrostructureInput.DEFAULT_COOLING_RATE
                                                    if cooling_rate is None
                                                    else cooling_rate,
                                                    thermal_gradient=MicrostructureInput.DEFAULT_THERMAL_GRADIENT  # noqa: E501, line too long
                                                    if thermal_gradient is None
                                                    else thermal_gradient,
                                                    melt_pool_width=MicrostructureInput.DEFAULT_MELT_POOL_WIDTH  # noqa: E501, line too long
                                                    if melt_pool_width is None
                                                    else melt_pool_width,
                                                    melt_pool_depth=MicrostructureInput.DEFAULT_MELT_POOL_DEPTH  # noqa: E501, line too long
                                                    if melt_pool_depth is None
                                                    else melt_pool_depth,
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
                                                    ColumnNames.ID: self._create_unique_id(
                                                        prefix=f"micro_{iteration}"
                                                    ),
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
                                                    ColumnNames.COOLING_RATE: float("nan")
                                                    if cooling_rate is None
                                                    else cooling_rate,
                                                    ColumnNames.THERMAL_GRADIENT: float("nan")
                                                    if thermal_gradient is None
                                                    else thermal_gradient,
                                                    ColumnNames.MICRO_MELT_POOL_WIDTH: float("nan")
                                                    if melt_pool_width is None
                                                    else melt_pool_width,
                                                    ColumnNames.MICRO_MELT_POOL_DEPTH: float("nan")
                                                    if melt_pool_depth is None
                                                    else melt_pool_depth,
                                                    ColumnNames.RANDOM_SEED: float("nan")
                                                    if random_seed is None
                                                    else random_seed,
                                                }
                                            )
                                            self._data_frame = pd.concat(
                                                [self._data_frame, row.to_frame().T],
                                                ignore_index=True,
                                            )

    def update(
        self, summaries: List[Union[SingleBeadSummary, PorositySummary, MicrostructureSummary]]
    ):
        """Update the results of simulations in the parametric study.

        This method updates values for existing simulations in the parametric study. To add
        completed simulations, use the :meth:`add_summaries` method instead.

        Parameters
        ----------
        summaries : list[Union[SingleBeadSummary, PorositySummary, MicrostructureSummary, SimulationError]]
            List of simulation summaries to use for updating the parametric study.
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
                raise TypeError(f"Invalid simulation summary type: {type(summary)}")

    def _update_single_bead(self, summary: SingleBeadSummary):
        """Update the results of a single bead simulation in the parametric
        study data frame."""
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
        """Update the results of a porosity simulation in the parametric study
        data frame."""
        idx = self._data_frame[
            (self._data_frame[ColumnNames.ID] == summary.input.id)
            & (self._data_frame[ColumnNames.TYPE] == SimulationType.POROSITY)
        ].index

        self._data_frame.loc[idx, ColumnNames.STATUS] = SimulationStatus.COMPLETED
        self._data_frame.loc[idx, ColumnNames.RELATIVE_DENSITY] = summary.relative_density

    def _update_microstructure(self, summary: MicrostructureSummary):
        """Update the results of a microstructure simulation in the parametric
        study data frame."""
        idx = self._data_frame[
            (self._data_frame[ColumnNames.ID] == summary.input.id)
            & (self._data_frame[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE)
        ].index

        self._data_frame.loc[idx, ColumnNames.STATUS] = SimulationStatus.COMPLETED
        self._data_frame.loc[idx, ColumnNames.XY_AVERAGE_GRAIN_SIZE] = summary.xy_average_grain_size
        self._data_frame.loc[idx, ColumnNames.XZ_AVERAGE_GRAIN_SIZE] = summary.xz_average_grain_size
        self._data_frame.loc[idx, ColumnNames.YZ_AVERAGE_GRAIN_SIZE] = summary.yz_average_grain_size

    def add_inputs(
        self,
        inputs: List[Union[SingleBeadInput, PorosityInput, MicrostructureInput]],
        iteration: int = DEFAULT_ITERATION,
        priority: int = DEFAULT_PRIORITY,
        status: SimulationStatus = SimulationStatus.PENDING,
    ):
        """Add new simulations to the parametric study.

        Parameters
        ----------
        inputs : list[Union[SingleBeadInput, PorosityInput, MicrostructureInput]]
            List of simulation inputs to add to the parametric study.

        iteration : int, DEFAULT_ITERATION
            Iteration number for the simulation inputs.

        priority : int, DEFAULT_PRIORITY
            Priority for the simulations.
        """
        for input in inputs:
            dict = {}
            if isinstance(input, SingleBeadInput):
                dict[ColumnNames.TYPE] = SimulationType.SINGLE_BEAD
                dict[ColumnNames.SINGLE_BEAD_LENGTH] = input.bead_length
            elif isinstance(input, PorosityInput):
                dict[ColumnNames.TYPE] = SimulationType.POROSITY
                dict[ColumnNames.POROSITY_SIZE_X] = input.size_x
                dict[ColumnNames.POROSITY_SIZE_Y] = input.size_y
                dict[ColumnNames.POROSITY_SIZE_Z] = input.size_z
            elif isinstance(input, MicrostructureInput):
                dict[ColumnNames.TYPE] = SimulationType.MICROSTRUCTURE
                dict[ColumnNames.MICRO_MIN_X] = input.sample_min_x
                dict[ColumnNames.MICRO_MIN_Y] = input.sample_min_y
                dict[ColumnNames.MICRO_MIN_Z] = input.sample_min_z
                dict[ColumnNames.MICRO_SIZE_X] = input.sample_size_x
                dict[ColumnNames.MICRO_SIZE_Y] = input.sample_size_y
                dict[ColumnNames.MICRO_SIZE_Z] = input.sample_size_z
                dict[ColumnNames.MICRO_SENSOR_DIM] = input.sensor_dimension
                if input.use_provided_thermal_parameters:
                    dict[ColumnNames.COOLING_RATE] = input.cooling_rate
                    dict[ColumnNames.THERMAL_GRADIENT] = input.thermal_gradient
                    dict[ColumnNames.MICRO_MELT_POOL_WIDTH] = input.melt_pool_width
                    dict[ColumnNames.MICRO_MELT_POOL_DEPTH] = input.melt_pool_depth
                if input.random_seed != MicrostructureInput.DEFAULT_RANDOM_SEED:
                    dict[ColumnNames.RANDOM_SEED] = input.random_seed
            else:
                print(f"Invalid simulation input type: {type(input)}")
                continue

            dict[ColumnNames.PROJECT] = self.project_name
            dict[ColumnNames.ITERATION] = iteration
            dict[ColumnNames.PRIORITY] = priority
            dict[ColumnNames.ID] = self._create_unique_id(id=input.id)
            dict[ColumnNames.STATUS] = status
            dict[ColumnNames.MATERIAL] = input.material.name
            dict[ColumnNames.LASER_POWER] = input.machine.laser_power
            dict[ColumnNames.SCAN_SPEED] = input.machine.scan_speed
            dict[ColumnNames.LAYER_THICKNESS] = input.machine.layer_thickness
            dict[ColumnNames.BEAM_DIAMETER] = input.machine.beam_diameter
            dict[ColumnNames.HEATER_TEMPERATURE] = input.machine.heater_temperature
            dict[ColumnNames.START_ANGLE] = input.machine.starting_layer_angle
            dict[ColumnNames.ROTATION_ANGLE] = input.machine.layer_rotation_angle
            dict[ColumnNames.HATCH_SPACING] = input.machine.hatch_spacing
            dict[ColumnNames.STRIPE_WIDTH] = input.machine.slicing_stripe_width

            self._data_frame = pd.concat(
                [self._data_frame, pd.Series(dict).to_frame().T], ignore_index=True
            )

    def remove(self, ids: Union[str, List[str]]):
        """Remove simulations from the parametric study.

        Parameters
        ----------
        ids : Union[str, List[str]]
            One or more ID field values for the rows to remove.
        """
        if isinstance(ids, str):
            ids = [ids]
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)].tolist()
        self._data_frame.drop(index=idx, inplace=True)

    def set_status(self, ids: Union[str, List[str]], status: SimulationStatus):
        """Set the status of simulations in the parametric study.

        Parameters
        ----------
        index : Union[int, List[int]]
            One or more IDs of the simulations to update.

        status : SimulationStatus
            Status for the simulations.
        """
        if isinstance(ids, str):
            ids = [ids]
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)]
        self._data_frame.loc[idx, ColumnNames.STATUS] = status

    def set_priority(self, ids: Union[str, List[str]], priority: int):
        """Set the priority of simulations in the parametric study.

        Parameters
        ----------
        index : Union[int, List[int]]
            One or more IDs of the simulations to update.

        priority : int
            Priority for the simulations.
        """
        if isinstance(ids, str):
            ids = [ids]
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)]
        self._data_frame.loc[idx, ColumnNames.PRIORITY] = priority

    def set_iteration(self, ids: Union[str, List[str]], iteration: int):
        """Set the iteration of simulations in the parametric study.

        Parameters
        ----------
        index : Union[int, List[int]]
            One or more IDs of the simulations to update.

        iteration : int
            Iteration for the simulations.
        """
        if isinstance(ids, str):
            ids = [ids]
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)]
        self._data_frame.loc[idx, ColumnNames.ITERATION] = iteration

    def _create_unique_id(self, prefix: Optional[str] = None, id: Optional[str] = None) -> str:
        """Create a unique simulation ID for a permutation.

        Parameters
        ----------
        prefix : str
            Prefix for the ID.
        id: str
            ID to use if it is unique. ``id`` is used as the prefix if
            the ID is not unique.

        Returns
        -------
        str
            Unique ID. If ``id`` is unique, it is returned. Otherwise,
        """

        if id is not None and not self._data_frame[ColumnNames.ID].str.match(f"{id}").any():
            return id
        _prefix = id or prefix or "sim"
        uid = f"{_prefix}_{misc.short_uuid()}"
        while self._data_frame[ColumnNames.ID].str.match(f"{uid}").any():
            uid = f"{_prefix}_{misc.short_uuid()}"
        return uid

    def clear(self):
        """Remove all permutations from the parametric study."""
        self._data_frame = self._data_frame[0:0]
