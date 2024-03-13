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
"""Provides data storage and utilities to perform a parametric study."""

from __future__ import annotations

from functools import wraps
import math
import os
import pathlib
import platform

import dill
import numpy as np
import pandas as pd

from ansys.additive.core import (
    LOG,
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
        result = func(self, *args, **kwargs)
        self.save(self.file_name)
        return result

    return wrap


class ParametricStudy:
    """Provides data storage and utility methods for a parametric study."""

    def __init__(self, file_name: str | os.PathLike):
        """Initialize the parametric study.

        Parameters
        ----------
        file_name: str, os.PathLike
            Name of the file the parametric study is written to. If the file exists, it is
            loaded and updated to the latest version of the file format.
        """
        study_path = pathlib.Path(file_name).absolute()
        if study_path.suffix != ".ps":
            study_path = pathlib.Path(str(study_path) + ".ps")
        if study_path.exists():
            self.__dict__ = ParametricStudy.load(study_path).__dict__
        else:
            self._init_new_study(study_path)
        print(f"Saving parametric study to {self.file_name}")

    def _init_new_study(self, study_path: pathlib.Path):
        self._file_name = study_path
        columns = [getattr(ColumnNames, k) for k in ColumnNames.__dict__ if not k.startswith("_")]
        self._data_frame = pd.DataFrame(columns=columns)
        self._format_version = FORMAT_VERSION
        self.save(self.file_name)

    @classmethod
    def _new(cls, study_path: pathlib.Path):
        """Create a new parametric study.

        Parameters
        ----------
        study_path: pathlib.Path
            Path to the study file.
        """
        study = cls.__new__(cls)
        study._init_new_study(study_path)
        return study

    def import_csv_study(self, file_name: str | os.PathLike) -> list[str]:
        """Import a parametric study from a CSV file.

        Parameters
        ----------
        file_name: str, os.PathLike
            Name of the csv file containing the simulation parameters.

        For the column names used in the returned data frame, see
        the :class:`ColumnNames <constants.ColumnNames>` class.

        Returns
        -------
        list[str]
            List of error messages of any simulations that have invalid
            input parameters.
        """

        file_path = pathlib.Path(file_name).absolute()
        if not file_path.exists():
            raise ValueError(f"{file_name} does not exist.")

        # The first column of the CSV file is expected to be the index column.
        columns = [getattr(ColumnNames, k) for k in ColumnNames.__dict__ if not k.startswith("_")]
        if all([set(pd.read_csv(file_path, index_col=0, nrows=0).columns) == set(columns)]):
            return self.add_simulations_from_data_frame(pd.read_csv(file_path, index_col=0))
        else:
            raise ValueError(f"{file_name} does not have the expected columns.")

    @property
    def format_version(self) -> int:
        """Version of the parametric study file format."""
        return self._format_version

    @property
    def file_name(self) -> os.PathLike:
        """Name of the file where the parametric study is stored."""
        return self._file_name

    @file_name.setter
    def file_name(self, value: str | os.PathLike):
        self._file_name = pathlib.Path(value)

    def data_frame(self) -> pd.DataFrame:
        """Return a :class:`DataFrame <pandas.DataFrame>` containing the study simulations.

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
        iteration: int = None,
    ):
        """Run the simulations with ``Pending`` for their ``Status`` values.

        Execution order is determined by the simulations
        ``Priority`` values. Lower values are interpreted as having
        higher priority and are run first.

        Parameters
        ----------
        additive : Additive
            Additive service connection to use for running simulations.
        type : list[SimulationType], default: None
            Type of simulations to run. If this value is ``None``,
            all simulation types are run.
        priority : int, default: None
            Priority of simulations to run. If this value is ``None``,
            all priorities are run.
        iteration : int, default: None
            Iteration number of simulations to run. The default is ``None``,
            all iterations are run.
        """
        summaries = ParametricRunner.simulate(
            self.data_frame(),
            additive,
            type=type,
            priority=priority,
            iteration=iteration,
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
    def load(file_name: str | os.PathLike) -> ParametricStudy:
        """Load a parametric study from a file.

        Parameters
        ----------
        file_name : str, os.PathLike
            Name of the parametric study file to load. This file is overwritten
            when the parametric study is updated. To prevent this behavior, update
            the ``file_name`` attribute of the returned parametric study after
            calling ``load()``.

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

        study.file_name = file_name
        study = ParametricStudy.update_format(study)
        return study

    @save_on_return
    def add_summaries(
        self,
        summaries: list[SingleBeadSummary | PorositySummary | MicrostructureSummary],
        iteration: int = DEFAULT_ITERATION,
    ) -> int:
        """Add summaries of executed simulations to the parametric study.

        Simulation summaries are created using the :meth:`Additive.simulate` method.
        This method adds new simulations to the parametric study. To update existing
        simulations, use the :meth:`update` method.

        A summary that matches an existing simulation will overwrite the results for
        that simulation.

        Parameters
        ----------
        summaries : list[SingleBeadSummary, PorositySummary, MicrostructureSummary]
            List of simulation result summaries to add to the parametric study.
        iteration : int, default: :obj:`DEFAULT_ITERATION`
            Iteration number for the new simulations.

        Returns
        -------
        int
            Number of new simulations added to the parametric study.
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
        return len(summaries) - self._remove_duplicate_entries(overwrite=True)

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
        summary : SingleBeadSummary, PorositySummary, MicrostructureSummary
            Summary of common simulation parameters to convert.

        iteration : int, default: :obj:`DEFAULT_ITERATION`
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
            Laser powers (W) to use for single bead simulations. Valid values
            are from :obj:`MIN_LASER_POWER <MachineConstants.MIN_LASER_POWER>`
            to :obj:`MAX_LASER_POWER <MachineConstants.MAX_LASER_POWER>`.
        scan_speeds : list[float]
            Scan speeds (m/s) to use for single bead simulations. Valid values are
            from :obj:`MIN_SCAN_SPEED <MachineConstants.MIN_SCAN_SPEED>` to
            :obj:`MAX_SCAN_SPEED <MachineConstants.MAX_SCAN_SPEED>`.
        bead_length : float, default: :class:`DEFAULT_BEAD_LENGTH <SingleBeadInput.DEFAULT_BEAD_LENGTH>`
            Length of the bead (m). Valid values are from :obj:`MIN_BEAD_LENGTH <SingleBeadInput.MIN_BEAD_LENGTH>`
            to :obj:`MAX_BEAD_LENGTH <SingleBeadInput.MAX_BEAD_LENGTH>`.
        layer_thicknesses : list[float], default: None
            Layer thicknesses (m) to use for single bead simulations.
            If this value is ``None``, :obj:`DEFAULT_LAYER_THICKNESS <MachineConstants.DEFAULT_LAYER_THICKNESS>`
            is used. Valid values are from :obj:`MIN_LAYER_THICKNESS <MachineConstants.MIN_LAYER_THICKNESS>`
            to :obj:`MAX_LAYER_THICKNESS <MachineConstants.MAX_LAYER_THICKNESS>`.
        heater_temperatures : list[float], default: None
            Heater temperatures (C) to use for single bead simulations.
            If this value is ``None``, :obj:`DEFAULT_HEATER_TEMP <MachineConstants.DEFAULT_HEATER_TEMP>`
            is used. Valid values are from :obj:`MIN_HEATER_TEMP <MachineConstants.MIN_HEATER_TEMP>`
            to :obj:`MAX_HEATER_TEMP <MachineConstants.MAX_HEATER_TEMP>`.
        beam_diameters : list[float], default: None
            Beam diameters (m) to use for single bead simulations.
            If this value is ``None``, :obj:`DEFAULT_BEAM_DIAMETER <MachineConstants.DEFAULT_BEAM_DIAMETER>`
            is used. Valid values are from :obj:`MIN_BEAM_DIAMETER <MachineConstants.MIN_BEAM_DIAMETER>`
            to :obj:`MAX_BEAM_DIAMETER <MachineConstants.MAX_BEAM_DIAMETER>`.
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
        """  # noqa: E501
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
            Laser powers (W) to use for porosity simulations. Valid values
            are from :obj:`MIN_LASER_POWER <MachineConstants.MIN_LASER_POWER>`
            to :obj:`MAX_LASER_POWER <MachineConstants.MAX_LASER_POWER>`.
        scan_speeds : list[float]
            Scan speeds (m/s) to use for porosity simulations. Valid values are from
            :obj:`MIN_SCAN_SPEED <MachineConstants.MIN_SCAN_SPEED>` to
            :obj:`MAX_SCAN_SPEED <MachineConstants.MAX_SCAN_SPEED>`.
        size_x : float, default: :obj:`DEFAULT_SAMPLE_SIZE <PorosityInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the porosity sample in the x direction.
            Valid values are from :obj:`MIN_SAMPLE_SIZE <PorosityInput.MIN_SAMPLE_SIZE>`
            to :obj:`MAX_SAMPLE_SIZE <PorosityInput.MAX_SAMPLE_SIZE>`.
        size_y : float, :obj:`DEFAULT_SAMPLE_SIZE <PorosityInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the porosity sample in the y direction.
            Valid values are from :obj:`MIN_SAMPLE_SIZE <PorosityInput.MIN_SAMPLE_SIZE>`
            to :obj:`MAX_SAMPLE_SIZE <PorosityInput.MAX_SAMPLE_SIZE>`.
        size_z : float, :obj:`DEFAULT_SAMPLE_SIZE <PorosityInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the porosity sample in the z direction.
            Valid values are from :obj:`MIN_SAMPLE_SIZE <PorosityInput.MIN_SAMPLE_SIZE>`
            to :obj:`MAX_SAMPLE_SIZE <PorosityInput.MAX_SAMPLE_SIZE>`.
        layer_thicknesses : list[float], default: None
            Layer thicknesses (m) to use for porosity simulations.
            If this value is ``None``,
            :obj:`DEFAULT_LAYER_THICKNESS <MachineConstants.DEFAULT_LAYER_THICKNESS>`
            is used. Valid values are from :obj:`MIN_LAYER_THICKNESS <MachineConstants.MIN_LAYER_THICKNESS>`
            to :obj:`MAX_LAYER_THICKNESS <MachineConstants.MAX_LAYER_THICKNESS>`.
        heater_temperatures : list[float], default: None
            Heater temperatures (C) to use for porosity simulations.
            If this value is ``None``,
            :obj:`DEFAULT_HEATER_TEMP <MachineConstants.DEFAULT_HEATER_TEMP>`
            is used. Valid values are from :obj:`MIN_HEATER_TEMP <MachineConstants.MIN_HEATER_TEMP>`
            to :obj:`MAX_HEATER_TEMP <MachineConstants.MAX_HEATER_TEMP>`.
        beam_diameters : list[float], default: None
            Beam diameters (m) to use for porosity simulations.
            If this value is ``None``, :obj:`DEFAULT_BEAM_DIAMETER`
            is used. Valid values are from :obj:`MIN_BEAM_DIAMETER <MachineConstants.MIN_BEAM_DIAMETER>`
            to :obj:`MAX_BEAM_DIAMETER <MachineConstants.MAX_BEAM_DIAMETER>`.
        start_angles : list[float], default: None
            Scan angles (deg) for the first layer to use for porosity simulations.
            If this value is ``None``,
            :obj:`DEFAULT_STARTING_LAYER_ANGLE <MachineConstants.DEFAULT_STARTING_LAYER_ANGLE>`
            is used. Valid values are from :obj:`MIN_STARTING_LAYER_ANGLE <MachineConstants.MIN_STARTING_LAYER_ANGLE>`
            to :obj:`MAX_STARTING_LAYER_ANGLE <MachineConstants.MAX_STARTING_LAYER_ANGLE>`.
        rotation_angles : list[float], default: None
            Angles (deg) by which the scan direction is rotated with each layer
            to use for porosity simulations. If this value is ``None``,
            :obj:`DEFAULT_LAYER_ROTATION_ANGLE <MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE>`
            is used. Valid values are from :obj:`MIN_LAYER_ROTATION_ANGLE <MachineConstants.MIN_LAYER_ROTATION_ANGLE>`
            to :obj:`MAX_LAYER_ROTATION_ANGLE <MachineConstants.MAX_LAYER_ROTATION_ANGLE>`.
        hatch_spacings : list[float], default: None
            Hatch spacings (m) to use for porosity simulations. If this value is ``None``,
            :obj:`DEFAULT_HATCH_SPACING <MachineConstants.DEFAULT_HATCH_SPACING>` is used.
            Valid values are from :obj:`MIN_HATCH_SPACING <MachineConstants.MIN_HATCH_SPACING>`
            to :obj:`MAX_HATCH_SPACING <MachineConstants.MAX_HATCH_SPACING>`.
        stripe_widths : list[float], default: None
            Stripe widths (m) to use for porosity simulations. If this value is ``None``,
            :obj:`DEFAULT_SLICING_STRIPE_WIDTH <MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH>`
            is used. Valid values are from :obj:`MIN_SLICING_STRIPE_WIDTH <MachineConstants.MIN_SLICING_STRIPE_WIDTH>`
            to :obj:`MAX_SLICING_STRIPE_WIDTH <MachineConstants.MAX_SLICING_STRIPE_WIDTH>`.
        min_energy_density : float, default: None
            Minimum energy density (J/m^3) to use for porosity simulations. Parameter combinations
            with an area energy density below this value are not included. Area energy density is
            defined as laser power / (layer thickness * scan speed * hatch spacing).
        max_energy_density : float, default: None
            Maximum energy density (J/m^3) to use for porosity simulations. Parameter combinations
            with an area energy density above this value are not included. Energy density is defined
            as laser power / (layer thickness * scan speed * hatch spacing).
        min_build_rate : float, default: None
            Minimum build rate (m^3/s) to use for porosity simulations. Parameter combinations
            with a build rate below this value are not included. Build rate is defined as
            layer thickness * scan speed * hatch spacing.
        max_build_rate : float, default: None
            Maximum build rate (m^3/s) to use for porosity simulations. Parameter combinations
            with a build rate above this value are not included. Build rate is defined as
            layer thickness * scan speed * hatch spacing.
        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            Iteration number for this set of simulations.
        priority : int, default: :obj:`DEFAULT_PRIORITY <constants.DEFAULT_PRIORITY>`
            Priority for this set of simulations.
        """  # noqa: E501
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
            Laser powers (W) to use for microstructure simulations. Valid values
            are from :obj:`MIN_LASER_POWER <MachineConstants.MIN_LASER_POWER>`
            to :obj:`MAX_LASER_POWER <MachineConstants.MAX_LASER_POWER>`.
        scan_speeds : list[float]
            Scan speeds (m/s) to use for microstructure simulations. Valid values are from
            :obj:`MIN_SCAN_SPEED <MachineConstants.MIN_SCAN_SPEED>` to
            :obj:`MAX_SCAN_SPEED <MachineConstants.MAX_SCAN_SPEED>`.
        min_x : float, default: :obj:`DEFAULT_POSITION_COORDINATE <MicrostructureInput.DEFAULT_POSITION_COORDINATE>`
            Minimum x coordinate (m) of the microstructure sample. Valid values are from
            :obj:`MIN_POSITION_COORDINATE <MicrostructureInput.MIN_POSITION_COORDINATE>`
            to :obj:`MAX_POSITION_COORDINATE <MicrostructureInput.MAX_POSITION_COORDINATE>`.
        min_y : float, default: :obj:`DEFAULT_POSITION_COORDINATE <MicrostructureInput.DEFAULT_POSITION_COORDINATE>`
            Minimum y coordinate (m) of the microstructure sample. Valid values are from
            :obj:`MIN_POSITION_COORDINATE <MicrostructureInput.MIN_POSITION_COORDINATE>`
            to :obj:`MAX_POSITION_COORDINATE <MicrostructureInput.MAX_POSITION_COORDINATE>`.
        min_z : float, default: :obj:`DEFAULT_POSITION_COORDINATE <MicrostructureInput.DEFAULT_POSITION_COORDINATE>`
            Minimum z coordinate (m) of the microstructure sample. Valid values are from
            :obj:`MIN_POSITION_COORDINATE <MicrostructureInput.MIN_POSITION_COORDINATE>`
            to :obj:`MAX_POSITION_COORDINATE <MicrostructureInput.MAX_POSITION_COORDINATE>`.
        size_x : float, default: :obj:`DEFAULT_SAMPLE_SIZE <MicrostructureInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the microstructure sample in the x direction.
            Valid values are from :obj:`MIN_SAMPLE_SIZE <MicrostructureInput.MIN_SAMPLE_SIZE>`
            to :obj:`MAX_SAMPLE_SIZE <MicrostructureInput.MAX_SAMPLE_SIZE>`.
        size_y : float, default: :obj:`DEFAULT_SAMPLE_SIZE <MicrostructureInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the microstructure sample in the y direction.
            Valid values are from :obj:`MIN_SAMPLE_SIZE <MicrostructureInput.MIN_SAMPLE_SIZE>`
            to :obj:`MAX_SAMPLE_SIZE <MicrostructureInput.MAX_SAMPLE_SIZE>`.
        size_z : float, default: :obj:`DEFAULT_SAMPLE_SIZE <MicrostructureInput.DEFAULT_SAMPLE_SIZE>`
            Size (m) of the microstructure sample in the z direction.
            Valid values are from :obj:`MIN_SAMPLE_SIZE <MicrostructureInput.MIN_SAMPLE_SIZE>`
            to :obj:`MAX_SAMPLE_SIZE <MicrostructureInput.MAX_SAMPLE_SIZE>`.
        sensor_dimension : float, default: :obj:`DEFAULT_SENSOR_DIMENSION <MicrostructureInput.DEFAULT_SENSOR_DIMENSION>`
            Sensor dimension (m) to use for microstructure simulations.
            Valid values are from :obj:`MIN_SENSOR_DIMENSION <MicrostructureInput.MIN_SENSOR_DIMENSION>`
            to :obj:`MAX_SENSOR_DIMENSION <MicrostructureInput.MAX_SENSOR_DIMENSION>`.
            The values for the ``size_x`` and ``size_y`` parameters must be greater than the
            ``sensor_dimension`` parameter by :obj:`MIN_XY_SIZE_CUSHION <MicrostructureInput.MIN_XY_SIZE_CUSHION>`
            meters. The value for the ``size_z`` parameter must be greater than ``sensor_dimension``
            parameter by :obj:`MIN_Z_SIZE_CUSHION <MicrostructureInput.MIN_Z_SIZE_CUSHION>` meters.
        layer_thicknesses : list[float], default: None
            Layer thicknesses (m) to use for microstructure simulations.
            If this value is ``None``,
            :obj:`DEFAULT_LAYER_THICKNESS <MachineConstants.DEFAULT_LAYER_THICKNESS>` is used.
            Valid values are from :obj:`MIN_LAYER_THICKNESS <MachineConstants.MIN_LAYER_THICKNESS>`
            to :obj:`MAX_LAYER_THICKNESS <MachineConstants.MAX_LAYER_THICKNESS>`.
        heater_temperatures : list[float], default: None
            Heater temperatures (C) to use for microstructure simulations.
            If this value is ``None``,
            :obj:`DEFAULT_HEATER_TEMP <MachineConstants.DEFAULT_HEATER_TEMP>` is used.
            Valid values are from :obj:`MIN_HEATER_TEMP <MachineConstants.MIN_HEATER_TEMP>`
            to :obj:`MAX_HEATER_TEMP <MachineConstants.MAX_HEATER_TEMP>`.
        beam_diameters : list[float], default: None
            Beam diameters (m) to use for microstructure simulations. If this value is ``None``,
            :obj:`DEFAULT_BEAM_DIAMETER <MachineConstants.DEFAULT_BEAM_DIAMETER>` is used.
            Valid values are from :obj:`MIN_BEAM_DIAMETER <MachineConstants.MIN_BEAM_DIAMETER>`
            to :obj:`MAX_BEAM_DIAMETER <MachineConstants.MAX_BEAM_DIAMETER>`.
        start_angles : list[float], default: None
            Scan angles (deg) for the first layer to use for microstructure simulations.
            If this value is ``None``,
            :obj:`DEFAULT_STARTING_LAYER_ANGLE <MachineConstants.DEFAULT_STARTING_LAYER_ANGLE>`
            is used. Valid values are from :obj:`MIN_STARTING_LAYER_ANGLE <MachineConstants.MIN_STARTING_LAYER_ANGLE>`
            to :obj:`MAX_STARTING_LAYER_ANGLE <MachineConstants.MAX_STARTING_LAYER_ANGLE>`.
        rotation_angles : list[float], default: None
            Angles (deg) by which the scan direction is rotated with each layer
            to use for microstructure simulations.
            If this value is ``None``, :obj:`DEFAULT_LAYER_ROTATION_ANGLE <MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE>`
            is used. Valid values are from :obj:`MIN_LAYER_ROTATION_ANGLE <MachineConstants.MIN_LAYER_ROTATION_ANGLE>`
            to :obj:`MAX_LAYER_ROTATION_ANGLE <MachineConstants.MAX_LAYER_ROTATION_ANGLE>`.
        hatch_spacings : list[float], default: None
            Hatch spacings (m) to use for microstructure simulations.
            If this value is ``None``, :obj:`DEFAULT_HATCH_SPACING <MachineConstants.DEFAULT_HATCH_SPACING>` is used.
            Valid values are from :obj:`MIN_HATCH_SPACING <MachineConstants.MIN_HATCH_SPACING>`
            to :obj:`MAX_HATCH_SPACING <MachineConstants.MAX_HATCH_SPACING>`.
        stripe_widths : list[float], default: None
            Stripe widths (m) to use for microstructure simulations.
            If this value is ``None``, :obj:`DEFAULT_SLICING_STRIPE_WIDTH <MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH>`
            is used. Valid values are from :obj:`MIN_SLICING_STRIPE_WIDTH <MachineConstants.MIN_SLICING_STRIPE_WIDTH>`
            to :obj:`MAX_SLICING_STRIPE_WIDTH <MachineConstants.MAX_SLICING_STRIPE_WIDTH>`.
        min_energy_density : float, default: None
            Minimum energy density (J/m^3) to use for microstructure simulations.
            Parameter combinations with an area energy density below this value are not included.
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
            If this value is ``None``, and ``thermal_gradient``, ``melt_pool_width``, and ``melt_pool_depth``
            are ``None``, the cooling rate is calculated. If ``None`` and any of the other three parameters
            are not ``None``, :obj:`DEFAULT_COOLING_RATE <MicrostructureInput.DEFAULT_COOLING_RATE>`
            is used. Valid values are from :obj:`MIN_COOLING_RATE <MicrostructureInput.MIN_COOLING_RATE>`
            to :obj:`MAX_COOLING_RATE <MicrostructureInput.MAX_COOLING_RATE>`.
        thermal_gradient : float, default: None
            Thermal gradient (K/m) to use for microstructure simulations.
            If this value is ``None``, and ``cooling_rate``, ``melt_pool_width``, and ``melt_pool_depth``
            are ``None``, the thermal gradient is calculated. If this value is ``None`` and any of the other three parameters
            are not ``None``, :obj:`DEFAULT_THERMAL_GRADIENT <MicrostructureInput.DEFAULT_THERMAL_GRADIENT>`\
           is used. Valid values are from :obj:`MIN_THERMAL_GRADIENT <MicrostructureInput.MIN_THERMAL_GRADIENT>`
            to :obj:`MAX_THERMAL_GRADIENT <MicrostructureInput.MAX_THERMAL_GRADIENT>`.
        melt_pool_width : float, default: None
            Melt pool width (m) to use for microstructure simulations.
            If this value is ``None`` and ``cooling_rate``, ``thermal_gradient``, and ``melt_pool_depth``
            are ``None``, the melt pool is calculated. If this value is ``None`` and any of the other three parameters
            are not ``None``, :obj:`DEFAULT_MELT_POOL_WIDTH <MicrostructureInput.DEFAULT_MELT_POOL_WIDTH>` is used.
            Valid values are from :obj:`MIN_MELT_POOL_WIDTH <MicrostructureInput.MIN_MELT_POOL_WIDTH>`
            to :obj:`MAX_MELT_POOL_WIDTH <MicrostructureInput.MAX_MELT_POOL_WIDTH>`.
        melt_pool_depth : float, default: None
            Melt pool depth (m) to use for microstructure simulations.
            If this value is ``None``, and ``cooling_rate``, ``thermal_gradient``, and ``melt_pool_width``
            are ``None``, the melt pool depth is calculated. If this value is ``None`` and any of the other three parameters
            are not ``None``, :obj:`DEFAULT_MELT_POOL_DEPTH <MicrostructureInput.DEFAULT_MELT_POOL_DEPTH>` is used.
            Valid values are from :obj:`MIN_MELT_POOL_DEPTH <MicrostructureInput.MIN_MELT_POOL_DEPTH>`
            to :obj:`MAX_MELT_POOL_DEPTH <MicrostructureInput.MAX_MELT_POOL_DEPTH>`.
        random_seed : int, default: None
            The random seed to use for microstructure simulations. If this value is ``None``,
            an automatically generated random seed is used.
            Valid values are from :obj:`MIN_RANDOM_SEED <MicrostructureInput.MIN_RANDOM_SEED>`
            to :obj:`MAX_RANDOM_SEED <MicrostructureInput.MAX_RANDOM_SEED>`.
        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            Iteration number for this set of simulations.
        priority : int, default: :obj:`DEFAULT_PRIORITY <constants.DEFAULT_PRIORITY>`
            Priority for this set of simulations.
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
                                                    cooling_rate=(
                                                        MicrostructureInput.DEFAULT_COOLING_RATE
                                                        if cooling_rate is None
                                                        else cooling_rate
                                                    ),
                                                    thermal_gradient=(
                                                        MicrostructureInput.DEFAULT_THERMAL_GRADIENT  # noqa: E501, line too long
                                                        if thermal_gradient is None
                                                        else thermal_gradient
                                                    ),
                                                    melt_pool_width=(
                                                        MicrostructureInput.DEFAULT_MELT_POOL_WIDTH  # noqa: E501, line too long
                                                        if melt_pool_width is None
                                                        else melt_pool_width
                                                    ),
                                                    melt_pool_depth=(
                                                        MicrostructureInput.DEFAULT_MELT_POOL_DEPTH  # noqa: E501, line too long
                                                        if melt_pool_depth is None
                                                        else melt_pool_depth
                                                    ),
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
                                                    ColumnNames.COOLING_RATE: (
                                                        float("nan")
                                                        if cooling_rate is None
                                                        else cooling_rate
                                                    ),
                                                    ColumnNames.THERMAL_GRADIENT: (
                                                        float("nan")
                                                        if thermal_gradient is None
                                                        else thermal_gradient
                                                    ),
                                                    ColumnNames.MICRO_MELT_POOL_WIDTH: (
                                                        float("nan")
                                                        if melt_pool_width is None
                                                        else melt_pool_width
                                                    ),
                                                    ColumnNames.MICRO_MELT_POOL_DEPTH: (
                                                        float("nan")
                                                        if melt_pool_depth is None
                                                        else melt_pool_depth
                                                    ),
                                                    ColumnNames.RANDOM_SEED: (
                                                        float("nan")
                                                        if random_seed is None
                                                        else random_seed
                                                    ),
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
        completed simulations, use the :meth:`add_summaries` method instead. This method is
        automatically called by the :meth:`run_simulations` method when simulations are completed.

        Parameters
        ----------
        summaries : list[SingleBeadSummary, PorositySummary, MicrostructureSummary, SimulationError]
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
    ) -> int:
        """Add new simulations to the parametric study.

        If the input matches an existing simulation, the input will be ignored.

        Parameters
        ----------
        inputs : list[SingleBeadInput, PorosityInput, MicrostructureInput]
            List of simulation inputs to add to the parametric study.

        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            Iteration number for the simulation inputs.

        priority : int, default: :obj:`DEFAULT_PRIORITY <constants.DEFAULT_PRIORITY>`
            Priority for the simulations.

        status : SimulationStatus, default: :obj:`SimulationStatus.PENDING`
            Valid types are :obj:`SimulationStatus.PENDING` and :obj:`SimulationStatus.SKIP`.

        Returns
        -------
        int
            The number of simulations added to the parametric study.
        """
        if status not in [SimulationStatus.SKIP, SimulationStatus.PENDING]:
            raise ValueError(
                f"Simulation status must be '{SimulationStatus.PENDING}' or '{SimulationStatus.SKIP}'"
            )
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
                raise TypeError(f"Invalid simulation input type: {type(input)}")

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
        return len(inputs) - self._remove_duplicate_entries(overwrite=False)

    @save_on_return
    def _remove_duplicate_entries(self, overwrite: bool = False) -> int:
        """Remove or update duplicate simulations from the parametric study.

        Parameters
        ----------
        overwrite : bool, default: False
            If True, drop duplicates and keep the latest entry.
            If False, drop duplicates and keep the earlier entry.

        Returns
        -------
        int
            The number of duplicate simulations removed.
        """

        # For duplicate removal, the following rules are applied:
        # - Sort simulatiuons by priority in the following order: completed > pending > skip > error
        # - Select a subset of input columns based on simulation type to check for duplicates
        # - Completed simulations will overwrite pending, skip and error simulations
        # - Completed simulations will be overwritten by newer completed simulations if overwrite is True

        column_names = [
            getattr(ColumnNames, k) for k in ColumnNames.__dict__ if not k.startswith("_")
        ]
        sorted_df = pd.DataFrame(columns=column_names)
        duplicates_removed_df = pd.DataFrame(columns=column_names)
        current_df = self.data_frame()

        if len(current_df) == 0:
            return 0

        # Filter and arrange as per status so that completed simulations are not overwritten by the
        # ones lower in the list
        for status in [
            SimulationStatus.COMPLETED,
            SimulationStatus.PENDING,
            SimulationStatus.SKIP,
            SimulationStatus.ERROR,
        ]:
            if len(current_df[current_df[ColumnNames.STATUS] == status]) > 0:
                sorted_df = pd.concat(
                    [sorted_df, current_df[current_df[ColumnNames.STATUS] == status]],
                    ignore_index=True,
                )

        # Common columns to check for duplicates
        common_params = [
            ColumnNames.MATERIAL,
            ColumnNames.HEATER_TEMPERATURE,
            ColumnNames.LAYER_THICKNESS,
            ColumnNames.BEAM_DIAMETER,
            ColumnNames.LASER_POWER,
            ColumnNames.SCAN_SPEED,
            ColumnNames.TYPE,
        ]

        # Additional columns to check for duplicates as per simulation type
        sb_params = common_params + [ColumnNames.SINGLE_BEAD_LENGTH]

        porosity_params = common_params + [
            ColumnNames.START_ANGLE,
            ColumnNames.ROTATION_ANGLE,
            ColumnNames.HATCH_SPACING,
            ColumnNames.STRIPE_WIDTH,
            ColumnNames.POROSITY_SIZE_X,
            ColumnNames.POROSITY_SIZE_Y,
            ColumnNames.POROSITY_SIZE_Z,
        ]

        microstructure_params = common_params + [
            ColumnNames.START_ANGLE,
            ColumnNames.ROTATION_ANGLE,
            ColumnNames.HATCH_SPACING,
            ColumnNames.STRIPE_WIDTH,
            ColumnNames.MICRO_MIN_X,
            ColumnNames.MICRO_MIN_Y,
            ColumnNames.MICRO_MIN_Z,
            ColumnNames.MICRO_SIZE_X,
            ColumnNames.MICRO_SIZE_Y,
            ColumnNames.MICRO_SIZE_Z,
            ColumnNames.MICRO_SENSOR_DIM,
            ColumnNames.COOLING_RATE,
            ColumnNames.THERMAL_GRADIENT,
            ColumnNames.MICRO_MELT_POOL_DEPTH,
            ColumnNames.MICRO_MELT_POOL_WIDTH,
            ColumnNames.RANDOM_SEED,
        ]

        single_bead_df = sorted_df[sorted_df[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD]
        porosity_df = sorted_df[sorted_df[ColumnNames.TYPE] == SimulationType.POROSITY]
        microstructure_df = sorted_df[sorted_df[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE]

        if overwrite:
            # Drop duplicates and keep the latest completed simulation entry in case of adding a
            # completed simulation when using add_summaries.
            # Simulation status further narrows down subset of columns to check.

            for df, params in zip(
                [single_bead_df, porosity_df, microstructure_df],
                [sb_params, porosity_params, microstructure_params],
            ):
                df.drop_duplicates(
                    subset=params + [ColumnNames.STATUS],
                    ignore_index=True,
                    keep="last",
                    inplace=True,
                )

        # Drop duplicates and keep the earlier entry in case of adding a pending/skip simulation
        # when using add_inputs.
        # Completed simulations will remain as is since they are already sorted and are higher
        # up in the list.

        for df, params in zip(
            [single_bead_df, porosity_df, microstructure_df],
            [sb_params, porosity_params, microstructure_params],
        ):
            if len(df) > 0:
                duplicates_removed_df = pd.concat(
                    [
                        duplicates_removed_df,
                        df.drop_duplicates(subset=params, ignore_index=True, keep="first"),
                    ]
                )

        self._data_frame = duplicates_removed_df
        n_removed = len(current_df) - len(duplicates_removed_df)
        LOG.debug(f"Removed {n_removed} duplicate simulation(s).")
        return n_removed

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

        status : SimulationStatus
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
            Unique ID.
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

    @staticmethod
    def update_format(study: ParametricStudy) -> ParametricStudy:
        """Update a parametric study to the latest format version.

        Parameters
        ----------
        study : ParametricStudy
            Parametric study to update.

        Returns
        -------
        ParametricStudy
            Updated parametric study.
        """

        # The format_version property was implemented incorrectly in version 1.
        # Check the column names to determine if the study is version 1.
        if "Heater Temp (°C)" in study.data_frame().columns:
            version = 1
        else:
            version = study.format_version

        if version > FORMAT_VERSION:
            raise ValueError(
                f"Unsupported version, study version = {version},"
                + "latest supported version is {FORMAT_VERSION}."
            )

        if version == FORMAT_VERSION:
            return study

        print("Updating parametric study to latest version.")

        df = study.data_frame()
        if version < 2:
            df = df.rename(
                columns={
                    "Heater Temp (°C)": ColumnNames.HEATER_TEMPERATURE,
                    "Start Angle (°)": ColumnNames.START_ANGLE,
                    "Rotation Angle (°)": ColumnNames.ROTATION_ANGLE,
                    "Cooling Rate (°K/s)": ColumnNames.COOLING_RATE,
                    "Thermal Gradient (°K/m)": ColumnNames.THERMAL_GRADIENT,
                    "XY Average Grain Size (µm)": ColumnNames.XY_AVERAGE_GRAIN_SIZE,
                    "XZ Average Grain Size (µm)": ColumnNames.XZ_AVERAGE_GRAIN_SIZE,
                    "YZ Average Grain Size (µm)": ColumnNames.YZ_AVERAGE_GRAIN_SIZE,
                    "Melt Pool Length/Width (m)": ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH,
                    "Melt Pool Ref Depth/Width (m)": ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH,
                }
            )
            version = 2

        new_study = ParametricStudy._new(study.file_name)
        new_study._data_frame = df
        return new_study

    @save_on_return
    def add_simulations_from_data_frame(self, df: pd.DataFrame) -> list[str]:
        """Add simulations from an imported CSV file to the parametric study.

        Parameters
        ----------
        df : pd.DataFrame
            Data frame of the csv file containing simulations to be added to the parametric study.

        Returns
        -------
        list[str]
            List of error messages for invalid simulations.
        """

        # check valid inputs
        drop_indices, error_list = list(), list()
        duplicates = 0
        allowed_status = [
            SimulationStatus.COMPLETED,
            SimulationStatus.PENDING,
            SimulationStatus.SKIP,
            SimulationStatus.ERROR,
        ]
        for index, row in df.iterrows():
            valid = False
            if row[ColumnNames.STATUS] in allowed_status:
                valid, error = self._validate_input(row)
            else:
                valid, error = (False, f"Invalid simulation status {row[ColumnNames.STATUS]}")
            if not valid:
                drop_indices.append(index)
                error_list.append(error)

        # drop invalid inputs
        df = df.drop(drop_indices)

        # add simulations to the parametric study and drop duplicates
        for status, overwrite in [
            (SimulationStatus.COMPLETED, True),
            (SimulationStatus.PENDING, False),
            (SimulationStatus.SKIP, False),
            (SimulationStatus.ERROR, False),
        ]:
            if len(df[df[ColumnNames.STATUS] == status]) > 0:
                self._data_frame = pd.concat(
                    [self._data_frame, df[df[ColumnNames.STATUS] == status]],
                    ignore_index=True,
                )
                duplicates += self._remove_duplicate_entries(overwrite=overwrite)

        if duplicates > 0:
            error_list.append(f"Removed {duplicates} duplicate simulation(s).")
        return error_list

    def _validate_input(self, input: pd.Series):
        """Test input from a row of a CSV file for valid input parameters.

        Parameters
        ----------
        input : pd.Series
            Row of a CSV file containing the simulation input.

        Returns
        -------
        tuple[bool, str]
            bool, True if the input is valid, False otherwise.
            string, Error message if the input is invalid.
        """

        try:
            allowed_types = [
                SimulationType.SINGLE_BEAD,
                SimulationType.POROSITY,
                SimulationType.MICROSTRUCTURE,
            ]
            if input[ColumnNames.TYPE] not in allowed_types:
                return (False, f"Invalid simulation type: {input[ColumnNames.TYPE]}.")

            # convert nan to default values only for single bead simulations
            # for other simulation types, nan values are not allowed
            if input[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD:
                if np.isnan(input[ColumnNames.START_ANGLE]):
                    input[ColumnNames.START_ANGLE] = MachineConstants.DEFAULT_STARTING_LAYER_ANGLE
                if np.isnan(input[ColumnNames.ROTATION_ANGLE]):
                    input[
                        ColumnNames.ROTATION_ANGLE
                    ] = MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE
                if np.isnan(input[ColumnNames.HATCH_SPACING]):
                    input[ColumnNames.HATCH_SPACING] = MachineConstants.DEFAULT_HATCH_SPACING
                if np.isnan(input[ColumnNames.STRIPE_WIDTH]):
                    input[ColumnNames.STRIPE_WIDTH] = MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH

            machine = AdditiveMachine(
                laser_power=input[ColumnNames.LASER_POWER],
                scan_speed=input[ColumnNames.SCAN_SPEED],
                heater_temperature=input[ColumnNames.HEATER_TEMPERATURE],
                layer_thickness=input[ColumnNames.LAYER_THICKNESS],
                beam_diameter=input[ColumnNames.BEAM_DIAMETER],
                starting_layer_angle=input[ColumnNames.START_ANGLE],
                layer_rotation_angle=input[ColumnNames.ROTATION_ANGLE],
                hatch_spacing=input[ColumnNames.HATCH_SPACING],
                slicing_stripe_width=input[ColumnNames.STRIPE_WIDTH],
            )

            material = AdditiveMaterial(name=str(input[ColumnNames.MATERIAL]))

            if input[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD:
                valid, error = self._validate_single_bead_input(machine, material, input)
            if input[ColumnNames.TYPE] == SimulationType.POROSITY:
                valid, error = self._validate_porosity_input(machine, material, input)
            if input[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE:
                valid, error = self._validate_microstructure_input(machine, material, input)
            if not valid:
                return (False, error)
            return (True, "")

        except ValueError as e:
            return (False, (f"Invalid parameter combination: {e}"))

    def _validate_single_bead_input(
        self, machine: AdditiveMachine, material: AdditiveMaterial, input: pd.Series
    ) -> tuple[bool, str]:
        """Validate single bead simulation input values.

        Parameters
        ----------
        input : pd.Series
            Single bead simulation input.

        machine : AdditiveMachine
            Additive machine object to use for validating the single bead input.

        material : AdditiveMaterial
            Additive material object to use for validating the single bead input.

        Returns
        -------
        tuple[bool, str]
            bool, True if the single bead input is valid, False otherwise.
            string, Error message if the single bead input is invalid.
        """
        try:
            test_bead_length = input[ColumnNames.SINGLE_BEAD_LENGTH]

            test_single_bead_input = SingleBeadInput(
                bead_length=test_bead_length, machine=machine, material=material
            )
            return (True, "")
        except ValueError as e:
            return (False, (f"Invalid parameter combination: {e}"))

    def _validate_porosity_input(
        self, machine: AdditiveMachine, material: AdditiveMaterial, input: pd.Series
    ) -> tuple[bool, str]:
        """Validate porosity simulation input values.

        Parameters
        ----------
        input : pd.Series
            Porosity simulation input.

        machine : AdditiveMachine
            Additive machine object to use for validating the porosity input.

        material : AdditiveMaterial
            Additive material object to use for validating the porosity input.

        Returns
        -------
        tuple[bool, str]
            bool, True if the porosity input is valid, False otherwise.
            string, Error message if the porosity input is invalid.
        """

        try:
            test_porosity_input = PorosityInput(
                size_x=input[ColumnNames.POROSITY_SIZE_X],
                size_y=input[ColumnNames.POROSITY_SIZE_Y],
                size_z=input[ColumnNames.POROSITY_SIZE_Z],
                machine=machine,
                material=material,
            )
            return (True, "")
        except ValueError as e:
            return (False, (f"Invalid parameter combination: {e}"))

    def _validate_microstructure_input(
        self, machine: AdditiveMachine, material: AdditiveMaterial, input: pd.Series
    ) -> tuple[bool, str]:
        """Validate microstructure simulation input values.

        Parameters
        ----------
        input : pd.Series
            Microstructure simulation input.

        machine : AdditiveMachine
            Additive machine object to use for validating the microstructure input.

        material : AdditiveMaterial
            Additive material object to use for validating the microstructure input.

        Returns
        -------
        tuple[bool, str]
            bool, True if the microstructure input is valid, False otherwise.
            string, Error message if the microstructure input is invalid.
        """
        try:
            test_cooling_rate = input[ColumnNames.COOLING_RATE]
            test_thermal_gradient = input[ColumnNames.THERMAL_GRADIENT]
            test_melt_pool_width = input[ColumnNames.MICRO_MELT_POOL_WIDTH]
            test_melt_pool_depth = input[ColumnNames.MICRO_MELT_POOL_DEPTH]
            test_random_seed = input[ColumnNames.RANDOM_SEED]

            if (
                math.isnan(test_cooling_rate)
                or math.isnan(test_thermal_gradient)
                or math.isnan(test_melt_pool_width)
                or math.isnan(test_melt_pool_depth)
            ):
                test_use_provided_thermal_parameters = False
            else:
                test_use_provided_thermal_parameters = True

            test_microstructure_input = MicrostructureInput(
                sample_min_x=input[ColumnNames.MICRO_MIN_X],
                sample_min_y=input[ColumnNames.MICRO_MIN_Y],
                sample_min_z=input[ColumnNames.MICRO_MIN_Z],
                sample_size_x=input[ColumnNames.MICRO_SIZE_X],
                sample_size_y=input[ColumnNames.MICRO_SIZE_Y],
                sample_size_z=input[ColumnNames.MICRO_SIZE_Z],
                sensor_dimension=input[ColumnNames.MICRO_SENSOR_DIM],
                use_provided_thermal_parameters=test_use_provided_thermal_parameters,
                cooling_rate=test_cooling_rate,
                thermal_gradient=test_thermal_gradient,
                melt_pool_width=test_melt_pool_width,
                melt_pool_depth=test_melt_pool_depth,
                random_seed=test_random_seed,
                machine=machine,
                material=material,
            )
            return (True, "")
        except ValueError as e:
            return (False, (f"Invalid parameter combination: {e}"))
