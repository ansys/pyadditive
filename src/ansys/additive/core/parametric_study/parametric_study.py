# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
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

from __future__ import annotations

from functools import wraps
import os
import pathlib
import platform

import dill
import numpy as np
import pandas as pd

from ansys.additive.core import (
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
import ansys.additive.core.misc as misc

from .constants import DEFAULT_ITERATION, DEFAULT_PRIORITY, FORMAT_VERSION, ColumnNames
from .parametric_runner import ParametricRunner
from .parametric_utils import build_rate, energy_density


def save_on_return(func):
    """Decorator to save study file upon method return."""

    @wraps(func)
    def wrap(self, *args, **kwargs):
        func(self, *args, **kwargs)
        self.save(self.file_name)

    return wrap


class ParametricStudy:
    """Provides data storage and utility methods for a parametric study."""

    def __init__(self, study_name: str, study_dir: str | os.PathLike = "."):
        """Initialize the parametric study.

        Parameters
        ----------
        study_name: str
            Name of study.
        study_dir: str, os.PathLike, default: "."
            Directory where study will be stored.
        """
        self._file_name = pathlib.Path(study_dir).absolute() / f"{study_name}.ps"
        columns = [getattr(ColumnNames, k) for k in ColumnNames.__dict__ if not k.startswith("_")]
        self._data_frame = pd.DataFrame(columns=columns)
        self.save(self.file_name)
        print(f"Saving parametric study to {self.file_name}")

    @property
    def format_version(self) -> int:
        """Version of the parametric study file format."""
        return FORMAT_VERSION

    @property
    def file_name(self) -> os.PathLike:
        """Name of the file where the parametric study is stored."""
        return self._file_name

    @file_name.setter
    def file_name(self, value: str | os.PathLike):
        self._file_name = pathlib.Path(value)

    def data_frame(self) -> pd.DataFrame:
        """Return a :class:`DataFrame <pandas.DataFrame>` representing the
        parametric study.

        For the column names used in the returned data frame, see
        the :class:`ColumnNames <constants.ColumnNames>` class.

        .. note::
           Updating the returned data frame does not update this parametric study.
        """
        return self._data_frame.copy()

    @save_on_return
    def run_simulations(
        self,
        additive: Additive,
        type: list[SimulationType] | None = None,
        priority: int | None = None,
    ):
        """Run the simulations in the parametric study with
        ``SimulationStatus.PENDING`` in the ``ColumnNames.STATUS`` column.
        Execution order is determined by the values in the
        ``ColumnNames.PRIORITY`` column. Lower values are interpreted as having
        higher priority and are run first.

        Parameters
        ----------
        additive: :class:`Additive <ansys.additive.core.Additive>`
            Additive service connection to use for running simulations.
        type : list[SimulationType], default: None
            Type of simulations to run. If ``None``, all simulation types are run.
        priority : int, default: None
            Priority of simulations to run. If ``None``, all priorities are run.
        """
        summaries = ParametricRunner.simulate(
            self.data_frame(),
            additive,
            type=type,
            priority=priority,
        )
        self.update(summaries)

    def save(self, file_name: str | os.PathLike):
        """Save the parametric study to a file.

        Parameters
        ----------
        file_name : str, os.PathLike
            Name of the file to save the parametric study to.
        """

        pathlib.Path(file_name).parent.mkdir(parents=True, exist_ok=True)
        with open(file_name, "wb") as f:
            dill.dump(self, f)

    @staticmethod
    def load(file_name) -> ParametricStudy:
        """Load a parametric study from a file.

        Parameters
        ----------
        file_name : str, os.PathLike
            Name of file to load the parametric study from.

        Returns
        -------
        ParametricStudy
            Loaded parametric study.
        """
        if not pathlib.Path(file_name).is_file():
            raise ValueError(f"{file_name} is not a valid file.")

        # Hack to allow for sharing study files cross-platform.
        temp = None
        if platform.system() == "Windows":
            temp = pathlib.PosixPath
            pathlib.PosixPath = pathlib.WindowsPath
        else:
            temp = pathlib.WindowsPath
            pathlib.WindowsPath = pathlib.PosixPath

        try:
            with open(file_name, "rb") as f:
                study = dill.load(f)
        except Exception:
            raise
        finally:
            # Undo hack
            if platform.system() == "Windows":
                pathlib.PosixPath = temp
            else:
                pathlib.WindowsPath = temp

        if not isinstance(study, ParametricStudy):
            raise ValueError(f"{file_name} is not a parametric study.")

        if hasattr(study, "format_version") and study.format_version > FORMAT_VERSION:
            raise ValueError(
                f"Unsupported version, study version = {study.format_version},"
                + "current supported versions up to {FORMAT_VERSION}."
            )

        study.file_name = file_name
        return study

    @save_on_return
    def add_summaries(
        self,
        summaries: list[SingleBeadSummary | PorositySummary | MicrostructureSummary],
        iteration: int = DEFAULT_ITERATION,
    ):
        """Add summaries of previously executed simulations to the parametric
        study.

        This method adds new simulations to the parametric study. To update existing
        simulations, use the
        :meth:`update() <ansys.additive.core.parametric_study.ParametricStudy.update>` method.

        Parameters
        ----------
        summaries : list[:class:`SingleBeadSummary <ansys.additive.core.SingleBeadSummary>`,
        :class:`PorositySummary <ansys.additive.core.PorositySummary>`,
        :class:`MicrostructureSummary <ansys.additive.core.MicrostructureSummary>`]
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
        summary: SingleBeadSummary | PorositySummary | MicrostructureSummary,
        iteration: int = DEFAULT_ITERATION,
    ) -> dict[str, any]:
        """Convert common simulation parameters to a dictionary.

        Parameters
        ----------
        summary : :class:`SingleBeadSummary <ansys.additive.core.SingleBeadSummary>`,
        :class:`PorositySummary <ansys.additive.core.PorositySummary>`,
        :class:`MicrostructureSummary <ansys.additive.core.MicrostructureSummary>`
            Summary of common simulation parameters to convert.

        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            Iteration number for this simulation.

        Returns
        -------
        Dict[str, Any]
            Dictionary of common simulation parameters.
        """
        return {
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

    @save_on_return
    def generate_single_bead_permutations(
        self,
        material_name: str,
        laser_powers: list[float],
        scan_speeds: list[float],
        bead_length: float = SingleBeadInput.DEFAULT_BEAD_LENGTH,
        layer_thicknesses: list[float] | None = None,
        heater_temperatures: list[float] | None = None,
        beam_diameters: list[float] | None = None,
        min_area_energy_density: float | None = None,
        max_area_energy_density: float | None = None,
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
        bead_length : float, default: :class:`DEFAULT_BEAD_LENGTH <SingleBeadInput.DEFAULT_BEAD_LENGTH>`
            Length of the bead (m).
        layer_thicknesses : list[float], default: None
            Layer thicknesses (m) to use for single bead simulations.
            If ``None``, :obj:`DEFAULT_LAYER_THICKNESS <MachineConstants.DEFAULT_LAYER_THICKNESS>`
            is used.
        heater_temperatures : list[float], default: None
            Heater temperatures (C) to use for single bead simulations.
            If ``None``, :obj:`DEFAULT_HEATER_TEMP <MachineConstants.DEFAULT_HEATER_TEMP>`
            is used.
        beam_diameters : list[float], default: None
            Beam diameters (m) to use for single bead simulations.
            If ``None``, :obj:`DEFAULT_BEAM_DIAMETER <MachineConstants.DEFAULT_BEAM_DIAMETER>`
            is used.
        min_area_energy_density : float, default: None
            Minimum area energy density (J/m^2) to use for single bead simulations.
            Parameter combinations with an area energy density below this value are
            not included. Area energy density is defined as laser power / (layer thickness * scan speed).
        max_area_energy_density : float, default: None
            Maximum area energy density (J/m^2) to use for single bead simulations.
            Parameter combinations with an area energy density above this value are
            not included. Area energy density is defined as laser power / (layer thickness * scan speed).
        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            Iteration number for this set of simulations.
        priority : int, default: :obj:`DEFAULT_PRIORITY <constants.DEFAULT_PRIORITY>`
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

    @save_on_return
    def generate_porosity_permutations(
        self,
        material_name: str,
        laser_powers: list[float],
        scan_speeds: list[float],
        size_x: float = PorosityInput.DEFAULT_SAMPLE_SIZE,
        size_y: float = PorosityInput.DEFAULT_SAMPLE_SIZE,
        size_z: float = PorosityInput.DEFAULT_SAMPLE_SIZE,
        layer_thicknesses: list[float] | None = None,
        heater_temperatures: list[float] | None = None,
        beam_diameters: list[float] | None = None,
        start_angles: list[float] | None = None,
        rotation_angles: list[float] | None = None,
        hatch_spacings: list[float] | None = None,
        stripe_widths: list[float] | None = None,
        min_energy_density: float | None = None,
        max_energy_density: float | None = None,
        min_build_rate: float | None = None,
        max_build_rate: float | None = None,
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
        size_x : float, default: :obj:`DEFAULT_SAMPLE_SIZE`
            Size (m) of the porosity sample in the x direction.
            Valid values are between 0.001 and 0.01.
        size_y : float, :obj:`DEFAULT_SAMPLE_SIZE`
            Size (m) of the porosity sample in the y direction.
            Valid values are between 0.001 and 0.01.
        size_z : float, :obj:`DEFAULT_SAMPLE_SIZE`
            Size (m) of the porosity sample in the z direction.
            Valid values are between 0.001 and 0.01.
        layer_thicknesses : list[float], None
            Layer thicknesses (m) to use for porosity simulations.
            If ``None``, :obj:`DEFAULT_LAYER_THICKNESS <MachineConstants.DEFAULT_LAYER_THICKNESS>`
            is used.
        heater_temperatures : list[float], None
            Heater temperatures (C) to use for porosity simulations.
            If ``None``, :obj:`DEFAULT_HEATER_TEMP <MachineConstants.DEFAULT_HEATER_TEMP>`
            is used.
        beam_diameters : list[float], None
            Beam diameters (m) to use for porosity simulations.
            If ``None``, :obj:`DEFAULT_BEAM_DIAMETER <MachineConstants.DEFAULT_BEAM_DIAMETER>`
            is used.
        start_angles : list[float], None
            Scan angles (deg) for the first layer to use for porosity simulations.
            If ``None``, :obj:`DEFAULT_STARTING_LAYER_ANGLE <MachineConstants.DEFAULT_STARTING_LAYER_ANGLE>`
            is used.
        rotation_angles : list[float], None
            Angles (deg) by which the scan direction is rotated with each layer
            to use for porosity simulations. If ``None``,
            :obj:`DEFAULT_LAYER_ROTATION_ANGLE <MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE>`
            is used.
        hatch_spacings : list[float], None
            Hatch spacings (m) to use for porosity simulations. If ``None``,
            :obj:`DEFAULT_HATCH_SPACING <MachineConstants.DEFAULT_HATCH_SPACING>` is used.
        stripe_widths : list[float], None
            Stripe widths (m) to use for porosity simulations. If ``None``,
            :obj:`DEFAULT_SLICING_STRIPE_WIDTH <MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH>` is used.
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
        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            Iteration number for this set of simulations.
        priority : int, default: :obj:`DEFAULT_PRIORITY <constants.DEFAULT_PRIORITY>`
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

    @save_on_return
    def generate_microstructure_permutations(
        self,
        material_name: str,
        laser_powers: list[float],
        scan_speeds: list[float],
        min_x: float = MicrostructureInput.DEFAULT_POSITION_COORDINATE,
        min_y: float = MicrostructureInput.DEFAULT_POSITION_COORDINATE,
        min_z: float = MicrostructureInput.DEFAULT_POSITION_COORDINATE,
        size_x: float = MicrostructureInput.DEFAULT_SAMPLE_SIZE,
        size_y: float = MicrostructureInput.DEFAULT_SAMPLE_SIZE,
        size_z: float = MicrostructureInput.DEFAULT_SAMPLE_SIZE,
        sensor_dimension: float = MicrostructureInput.DEFAULT_SENSOR_DIMENSION,
        layer_thicknesses: list[float] | None = None,
        heater_temperatures: list[float] | None = None,
        beam_diameters: list[float] | None = None,
        start_angles: list[float] | None = None,
        rotation_angles: list[float] | None = None,
        hatch_spacings: list[float] | None = None,
        stripe_widths: list[float] | None = None,
        min_energy_density: float | None = None,
        max_energy_density: float | None = None,
        min_build_rate: float | None = None,
        max_build_rate: float | None = None,
        cooling_rate: float | None = None,
        thermal_gradient: float | None = None,
        melt_pool_width: float | None = None,
        melt_pool_depth: float | None = None,
        random_seed: int | None = None,
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
        min_x : float, default: :obj:`DEFAULT_POSITION_COORDINATE <MicrostructureInput.DEFAULT_POSITION_COORDINATE>`
            Minimum x coordinate (m) of the microstructure sample.
        min_y : float, default: :obj:`DEFAULT_POSITION_COORDINATE <MicrostructureInput.DEFAULT_POSITION_COORDINATE>`
            Minimum y coordinate (m) of the microstructure sample.
        min_z : float, default: :obj:`DEFAULT_POSITION_COORDINATE <MicrostructureInput.DEFAULT_POSITION_COORDINATE>`
            Minimum z coordinate (m) of the microstructure sample.
        size_x : float, default: :obj:`DEFAULT_SAMPLE_SIZE <MicrostructureInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the microstructure sample in the x direction.
            Valid values are between 0.001 and 0.01.
        size_y : float, default: :obj:`DEFAULT_SAMPLE_SIZE <MicrostructureInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the microstructure sample in the y direction.
            Valid values are between 0.001 and 0.01.
        size_z : float, default: :obj:`DEFAULT_SAMPLE_SIZE <MicrostructureInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the microstructure sample in the z direction.
            Valid values are between 0.001 and 0.01.
        sensor_dimension : float, default: :obj:`DEFAULT_SENSOR_DIMENSION <MicrostructureInput.DEFAULT_SENSOR_DIMENSION>`
            Sensor dimension (m) to use for microstructure simulations.
            Valid values are between 0.0001 and 0.001. The values for the
            ``size_x`` and ``size_y`` parameters must be greater than the
            ``sensor_dimension`` parameter by 0.0005. The value for the
            ``size_z`` parameter must be greater than ``sensor_dimension``
            parameter by 0.001.
        layer_thicknesses : list[float], default: None
            Layer thicknesses (m) to use for microstructure simulations.
            If ``None``,
            :obj:`DEFAULT_LAYER_THICKNESS <MachineConstants.DEFAULT_LAYER_THICKNESS>` is used.
        heater_temperatures : list[float], default: None
            Heater temperatures (C) to use for microstructure simulations.
            If ``None``,
            :obj:`DEFAULT_HEATER_TEMP <MachineConstants.DEFAULT_HEATER_TEMP>` is used.
        beam_diameters : list[float], default: None
            Beam diameters (m) to use for microstructure simulations. If ``None``,
            :obj:`DEFAULT_BEAM_DIAMETER <MachineConstants.DEFAULT_BEAM_DIAMETER>` is used.
        start_angles : list[float], default: None
            Scan angles (deg) for the first layer to use for microstructure simulations.
            If ``None``,
            :obj:`DEFAULT_STARTING_LAYER_ANGLE <MachineConstants.DEFAULT_STARTING_LAYER_ANGLE>`
            is used.
        rotation_angles : list[float], default: None
            Angles (deg) by which the scan direction is rotated with each layer
            to use for microstructure simulations.
            If ``None``, :obj:`DEFAULT_LAYER_ROTATION_ANGLE <MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE>`
            is used.
        hatch_spacings : list[float], default: None
            Hatch spacings (m) to use for microstructure simulations.
            If ``None``, :obj:`DEFAULT_HATCH_SPACING <MachineConstants.DEFAULT_HATCH_SPACING>` is used.
        stripe_widths : list[float], default: None
            Stripe widths (m) to use for microstructure simulations.
            If ``None``, :obj:`DEFAULT_SLICING_STRIPE_WIDTH <MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH>`
            is used.
        min_energy_density : float, default: None
            The minimum energy density (J/m^3) to use for microstructure simulations.
            Parameter combinations with an area energy density below this value will not be included.
            Area energy density is defined as laser power / (layer thickness * scan speed * hatch spacing).
        max_energy_density : float, default: None
            The maximum energy density (J/m^3) to use for microstructure simulations.
            Parameter combinations with an area energy density above this value will not be included.
            Energy density is defined as laser power / (layer thickness * scan speed * hatch spacing).
        min_build_rate : float, default: None
            The minimum build rate (m^3/s) to use for microstructure simulations.
            Parameter combinations with a build rate below this value will not be included.
            Build rate is defined as layer thickness * scan speed * hatch spacing.
        max_build_rate : float, default: None
            The maximum build rate (m^3/s) to use for microstructure simulations.
            Parameter combinations with a build rate above this value will not be included.
            Build rate is defined as layer thickness * scan speed * hatch spacing.
        cooling_rate : float, default: None
            The cooling rate (K/s) to use for microstructure simulations.
            If ``None``, and ``thermal_gradient``, ``melt_pool_width``, and ``melt_pool_depth``
            are ``None``, it will be calculated. If ``None`` and any of the other three parameters
            are not ``None``, :obj:`DEFAULT_COOLING_RATE <MicrostructureInput.DEFAULT_COOLING_RATE>`
            will be used.
        thermal_gradient : float, default: None
            The thermal gradient (K/m) to use for microstructure simulations.
            If ``None``, and ``cooling_rate``, ``melt_pool_width``, and ``melt_pool_depth``
            are ``None``, it will be calculated. If ``None`` and any of the other three parameters
            are not ``None``, :obj:`DEFAULT_THERMAL_GRADIENT <MicrostructureInput.DEFAULT_THERMAL_GRADIENT>` will be used.
        melt_pool_width : float, default: None
            The melt pool width (m) to use for microstructure simulations.
            If ``None``, and ``cooling_rate``, ``thermal_gradient``, and ``melt_pool_depth``
            are ``None``, it will be calculated. If ``None`` and any of the other three parameters
            are not ``None``, :obj:`DEFAULT_MELT_POOL_WIDTH <MicrostructureInput.DEFAULT_MELT_POOL_WIDTH>`.
        melt_pool_depth : float, default: None
            The melt pool depth (m) to use for microstructure simulations.
            If ``None``, and ``cooling_rate``, ``thermal_gradient``, and ``melt_pool_width``
            are ``None``, it will be calculated. If ``None`` and any of the other three parameters
            are not ``None``, :obj:`DEFAULT_MELT_POOL_DEPTH <MicrostructureInput.DEFAULT_MELT_POOL_DEPTH>`.
        random_seed : int, default: None
            The random seed to use for microstructure simulations. If ``None``,
            an automatically generated random seed will be used.
            Valid values are between 1 and 2^31 - 1.
        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            The iteration number for this set of simulations.

        priority : int, default: :obj:`DEFAULT_PRIORITY <constants.DEFAULT_PRIORITY>`
            The priority for this set of simulations.
        """  # noqa
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

    @save_on_return
    def update(self, summaries: list[SingleBeadSummary | PorositySummary | MicrostructureSummary]):
        """Update the results of simulations in the parametric study.

        This method updates values for existing simulations in the parametric study. To add
        completed simulations, use the :meth:`add_summaries` method instead.

        Parameters
        ----------
        summaries : list[:class:`SingleBeadSummary <ansys.additive.core.SingleBeadSummary>`,
        :class:`PorositySummary <ansys.additive.core.PorositySummary>`,
        :class:`MicrostructureSummary <ansys.additive.core.MicrostructureSummary>`,
        :class:`SimulationError <ansys.additive.core.SimulationError>`]
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

    @save_on_return
    def add_inputs(
        self,
        inputs: list[SingleBeadInput | PorosityInput | MicrostructureInput],
        iteration: int = DEFAULT_ITERATION,
        priority: int = DEFAULT_PRIORITY,
        status: SimulationStatus = SimulationStatus.PENDING,
    ):
        """Add new simulations to the parametric study.

        Parameters
        ----------
        inputs : list[:class:`SingleBeadSummary <ansys.additive.core.SingleBeadSummary>`,
        :class:`PorosityInput <ansys.additive.core.PorosityInput>`,
        :class:`MicrostructureInput <ansys.additive.core.MicrostructureInput>`]
            List of simulation inputs to add to the parametric study.

        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            Iteration number for the simulation inputs.

        priority : int, default: :obj:`DEFAULT_PRIORITY <constants.DEFAULT_PRIORITY>`
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

    @save_on_return
    def remove(self, ids: str | list[str]):
        """Remove simulations from the parametric study.

        Parameters
        ----------
        ids : str, list[str]
            One or more ID values for the simulations to remove.
        """
        if isinstance(ids, str):
            ids = [ids]
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)].tolist()
        self._data_frame.drop(index=idx, inplace=True)

    @save_on_return
    def set_status(self, ids: str | list[str], status: SimulationStatus):
        """Set the status of simulations in the parametric study.

        Parameters
        ----------
        ids : str, list[str]
            One or more IDs of the simulations to update.

        status : :class:`SimulationStatus <ansys.additive.core.SimulationStatus>`
            Status for the simulations.
        """
        if isinstance(ids, str):
            ids = [ids]
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)]
        self._data_frame.loc[idx, ColumnNames.STATUS] = status

    @save_on_return
    def set_priority(self, ids: str | list[str], priority: int):
        """Set the priority of simulations in the parametric study.

        Parameters
        ----------
        ids : str, list[str]
            One or more IDs of the simulations to update.

        priority : int
            Priority for the simulations.
        """
        if isinstance(ids, str):
            ids = [ids]
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)]
        self._data_frame.loc[idx, ColumnNames.PRIORITY] = priority

    @save_on_return
    def set_iteration(self, ids: str | list[str], iteration: int):
        """Set the iteration number of simulations in the parametric study.

        The iteration number is used to track the evolution of a
        design of experiments. Its use is optional.

        Parameters
        ----------
        ids : str, list[str]
            One or more IDs of the simulations to update.

        iteration : int
            Iteration for the simulations.
        """
        if isinstance(ids, str):
            ids = [ids]
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)]
        self._data_frame.loc[idx, ColumnNames.ITERATION] = iteration

    def _create_unique_id(self, prefix: str | None = None, id: str | None = None) -> str:
        """Create a unique simulation ID for a permutation.

        Parameters
        ----------
        prefix : str, default: None
            Prefix for the ID.
        id: str, default: None
            ID to use if it is unique. ``id`` is used as the prefix if
            the ID is not unique.

        Returns
        -------
        str
            Unique ID. If the combination of ``prefix`` and ``id`` is unique,
            it is returned. Otherwise, they are combined and a suffix is added to
            create a unique ID.
        """

        if id is not None and not self._data_frame[ColumnNames.ID].str.match(f"{id}").any():
            return id
        _prefix = id or prefix or "sim"
        uid = f"{_prefix}_{misc.short_uuid()}"
        while self._data_frame[ColumnNames.ID].str.match(f"{uid}").any():
            uid = f"{_prefix}_{misc.short_uuid()}"
        return uid

    @save_on_return
    def clear(self):
        """Remove all permutations from the parametric study."""
        self._data_frame = self._data_frame[0:0]
