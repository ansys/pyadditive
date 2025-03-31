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

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os
import pathlib
import platform
import warnings
from functools import wraps
from typing import Callable

import dill
import numpy as np

import ansys.additive.core.misc as misc
from ansys.additive.core.logger import LOG
from ansys.additive.core.machine import AdditiveMachine, MachineConstants
from ansys.additive.core.material import AdditiveMaterial
from ansys.additive.core.microstructure import (
    MicrostructureInput,
    MicrostructureSummary,
)
from ansys.additive.core.porosity import PorosityInput, PorositySummary
from ansys.additive.core.simulation import (
    SimulationStatus,
    SimulationType,
)
from ansys.additive.core.simulation_error import SimulationError
from ansys.additive.core.single_bead import MeltPool, SingleBeadInput, SingleBeadSummary

from .constants import DEFAULT_ITERATION, DEFAULT_PRIORITY, FORMAT_VERSION, ColumnNames
from .parametric_utils import build_rate, energy_density

# Suppress: FutureWarning in pandas: The behavior of DataFrame concatenation with empty or
# all-NA entries is deprecated. In a future version, this will no longer exclude
# empty or all-NA columns when determining the result dtypes. To retain the old
# behavior, exclude the relevant entries before the concat operation.
warnings.simplefilter(action="ignore", category=FutureWarning)
import pandas as pd  # noqa: E402


def save_on_return(func):
    """Save study file upon method return."""

    @wraps(func)
    def wrap(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.save(self.file_name)
        return result

    return wrap


class ParametricStudy:
    """Provides data storage and utility methods for a parametric study."""

    def __init__(self, file_name: str | os.PathLike, material_name: str):
        """Initialize the parametric study.

        Parameters
        ----------
        file_name: str, os.PathLike
            Name of the file the parametric study is written to. If the file exists, it is
            loaded and updated to the latest version of the file format.
        material_name: str
            Name of the material used in the parametric study.

        """
        study_path = pathlib.Path(file_name).absolute()
        if study_path.suffix != ".ps":
            study_path = pathlib.Path(str(study_path) + ".ps")
        if study_path.exists():
            self.__dict__ = ParametricStudy.load(study_path).__dict__
        else:
            self._init_new_study(study_path, material_name)
            LOG.info(f"Saving parametric study to {self.file_name}")

    def _init_new_study(self, study_path: pathlib.Path, material: str):
        self._file_name = study_path
        columns = [getattr(ColumnNames, k) for k in ColumnNames.__dict__ if not k.startswith("_")]
        self._data_frame = pd.DataFrame(columns=columns)
        self._format_version = FORMAT_VERSION
        self._material_name = material
        self.save(self.file_name)

    @classmethod
    def _new(cls, study_path: pathlib.Path, material: str = ""):
        """Create a new parametric study with an empty dataframe.

        Parameters
        ----------
        study_path: pathlib.Path
            Path to the study file.

        material: str, default ""
            Material to use for study.

        """
        study = cls.__new__(cls)
        study._init_new_study(study_path, material)
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
        return self._add_simulations_from_csv(file_path)

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

    @property
    def material_name(self) -> str | None:
        """Name of material used in the parametric study."""
        return self._material_name

    def data_frame(self) -> pd.DataFrame:
        """Return a :class:`DataFrame <pandas.DataFrame>` containing the study simulations.

        For the column names used in the returned data frame, see
        the :class:`ColumnNames <constants.ColumnNames>` class.

        .. note::
           Updating the returned data frame does not update this parametric study.
        """
        return self._data_frame.copy()

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
                study = dill.load(f)  # noqa: S301
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
        study.reset_simulation_status()
        return study

    @save_on_return
    def reset_simulation_status(self):
        """Reset the status of any ``Pending`` or ``Running`` simulations to ``New``."""
        idx = self._data_frame[
            self._data_frame[ColumnNames.STATUS].isin(
                [SimulationStatus.PENDING, SimulationStatus.RUNNING]
            )
        ].index
        self._data_frame.loc[idx, ColumnNames.STATUS] = SimulationStatus.NEW

    @save_on_return
    def clear_errors(self, simulation_ids: list[str] | None = None):
        """Clear the error messages for the specified simulations.

        Parameters
        ----------
        simulation_ids : list[str], default: None
            List of simulation IDs to clear the error messages for. If this value
            is ``None``, all error messages are cleared.

        """
        LOG.debug(f"Clearing errors {', '.join(simulation_ids) if simulation_ids else ''}")
        if simulation_ids is None:
            idx = self._data_frame.index
        else:
            idx = self._data_frame[self._data_frame[ColumnNames.ID].isin(simulation_ids)].index
        self._data_frame.loc[idx, ColumnNames.ERROR_MESSAGE] = None

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
        mp = summary.melt_pool
        row = pd.Series(
            {
                **self._common_param_to_dict(summary, iteration),
                ColumnNames.TYPE: SimulationType.SINGLE_BEAD,
                ColumnNames.BUILD_RATE: None,
                ColumnNames.ENERGY_DENSITY: None,
                ColumnNames.SINGLE_BEAD_LENGTH: summary.input.bead_length,
                ColumnNames.MELT_POOL_WIDTH: mp.median_width(),
                ColumnNames.MELT_POOL_DEPTH: mp.median_depth(),
                ColumnNames.MELT_POOL_LENGTH: mp.median_length(),
                ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH: mp.length_over_width(),
                ColumnNames.MELT_POOL_REFERENCE_WIDTH: mp.median_reference_width(),
                ColumnNames.MELT_POOL_REFERENCE_DEPTH: mp.median_reference_depth(),
                ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH: mp.depth_over_width(),
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
        laser_powers: list[float],
        scan_speeds: list[float],
        bead_length: float = SingleBeadInput.DEFAULT_BEAD_LENGTH,
        layer_thicknesses: list[float] | None = None,
        heater_temperatures: list[float] | None = None,
        beam_diameters: list[float] | None = None,
        min_pv_ratio: float | None = None,
        max_pv_ratio: float | None = None,
        iteration: int = DEFAULT_ITERATION,
        priority: int = DEFAULT_PRIORITY,
    ) -> int:
        """Add single bead permutations to the parametric study.

        Parameters
        ----------
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
        min_pv_ratio : float, default: None
            The P/V ratio is defined as the ratio of laser power (w) to the velocity of the laser beam, which
            is the scan speed (m/s). Parameter combinations with ratios less than this value are not included.
        max_pv_ratio : float, default: None
            The P/V ratio is defined as the ratio of laser power (w) to the velocity of the laser beam, which
            is the scan speed (m/s). Parameter combinations with ratios greater than this value are not included.
        iteration : int, default: :obj:`DEFAULT_ITERATION <constants.DEFAULT_ITERATION>`
            Iteration number for this set of simulations.
        priority : int, default: :obj:`DEFAULT_PRIORITY <constants.DEFAULT_PRIORITY>`
            Priority for this set of simulations.

        Returns
        -------
        int
            Number of single bead permutations added to the parametric study.

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
        min_pv = min_pv_ratio or 0.0
        max_pv = max_pv_ratio or float("inf")
        num_permutations_added = int()
        for p in laser_powers:
            for v in scan_speeds:
                for thickness in lt:
                    pv_ratio = round(p / v, 5)
                    if pv_ratio < min_pv or pv_ratio > max_pv:
                        continue

                    for t in ht:
                        for d in bd:
                            # validate parameters by trying to create input objects
                            try:
                                machine = AdditiveMachine(
                                    laser_power=p,
                                    scan_speed=v,
                                    heater_temperature=t,
                                    layer_thickness=thickness,
                                    beam_diameter=d,
                                )
                                SingleBeadInput(
                                    bead_length=bead_length,
                                    machine=machine,
                                    material=AdditiveMaterial(),
                                )
                            except ValueError as e:
                                LOG.error(f"Invalid parameter combination: {e}")
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
                                    ColumnNames.STATUS: SimulationStatus.NEW,
                                    ColumnNames.MATERIAL: self.material_name,
                                    ColumnNames.HEATER_TEMPERATURE: t,
                                    ColumnNames.LAYER_THICKNESS: thickness,
                                    ColumnNames.BEAM_DIAMETER: d,
                                    ColumnNames.LASER_POWER: p,
                                    ColumnNames.SCAN_SPEED: v,
                                    ColumnNames.PV_RATIO: p / v,
                                    ColumnNames.ENERGY_DENSITY: None,
                                    ColumnNames.BUILD_RATE: None,
                                    ColumnNames.SINGLE_BEAD_LENGTH: bead_length,
                                }
                            )
                            self._data_frame = pd.concat(
                                [self._data_frame, row.to_frame().T], ignore_index=True
                            )
                            num_permutations_added += 1
        return num_permutations_added - self._remove_duplicate_entries(overwrite=False)

    @save_on_return
    def generate_porosity_permutations(
        self,
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
    ) -> int:
        """Add porosity permutations to the parametric study.

        Parameters
        ----------
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
            Minimum energy density (J/m^3) to use for porosity simulations. Energy density is
            defined as laser power / (layer thickness * scan speed * hatch spacing).
            Parameter combinations with an energy density below this value are not included.
        max_energy_density : float, default: None
            Maximum energy density (J/m^3) to use for porosity simulations. Energy density is
            defined as laser power / (layer thickness * scan speed * hatch spacing).
            Parameter combinations with an energy density above this value are not included.
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

        Returns
        -------
        int
            Number of porosity permutations added to the parametric study.

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
        num_permutations_added = int()
        for p in laser_powers:
            for v in scan_speeds:
                for thickness in lt:
                    for h in hs:
                        br = build_rate(v, thickness, h)
                        ed = energy_density(p, v, thickness, h)
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
                                                    layer_thickness=thickness,
                                                    beam_diameter=d,
                                                    starting_layer_angle=a,
                                                    layer_rotation_angle=r,
                                                    hatch_spacing=h,
                                                    slicing_stripe_width=w,
                                                )
                                                PorosityInput(
                                                    size_x=size_x,
                                                    size_y=size_y,
                                                    size_z=size_z,
                                                    machine=machine,
                                                    material=AdditiveMaterial(),
                                                )
                                            except ValueError as e:
                                                LOG.error(f"Invalid parameter combination: {e}")
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
                                                    ColumnNames.STATUS: SimulationStatus.NEW,
                                                    ColumnNames.MATERIAL: self.material_name,
                                                    ColumnNames.HEATER_TEMPERATURE: t,
                                                    ColumnNames.LAYER_THICKNESS: thickness,
                                                    ColumnNames.BEAM_DIAMETER: d,
                                                    ColumnNames.LASER_POWER: p,
                                                    ColumnNames.SCAN_SPEED: v,
                                                    ColumnNames.PV_RATIO: p / v,
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
                                            num_permutations_added += 1
        return num_permutations_added - self._remove_duplicate_entries(overwrite=False)

    @save_on_return
    def generate_microstructure_permutations(
        self,
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
    ) -> int:
        """Add microstructure permutations to the parametric study.

        Parameters
        ----------
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
            Minimum energy density (J/m^3) to use for microstructure simulations. Energy density is
            defined as laser power / (layer thickness * scan speed * hatch spacing).
            Parameter combinations with an energy density below this value are not included.
        max_energy_density : float, default: None
            Maximum energy density (J/m^3) to use for microstructure simulations. Energy density is
            defined as laser power / (layer thickness * scan speed * hatch spacing).
            Parameter combinations with an energy density above this value are not included.
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

        Returns
        -------
        int
            Number of microstructure permutations added to the parametric study.
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

        num_permutations_added = int()
        for p in laser_powers:
            for v in scan_speeds:
                for thickness in lt:
                    for h in hs:
                        br = build_rate(v, thickness, h)
                        ed = energy_density(p, v, thickness, h)
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
                                                    layer_thickness=thickness,
                                                    beam_diameter=d,
                                                    starting_layer_angle=a,
                                                    layer_rotation_angle=r,
                                                    hatch_spacing=h,
                                                    slicing_stripe_width=w,
                                                )
                                                MicrostructureInput(
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
                                                        or np.isnan(cooling_rate)
                                                        else cooling_rate
                                                    ),
                                                    thermal_gradient=(
                                                        MicrostructureInput.DEFAULT_THERMAL_GRADIENT  # noqa: E501, line too long
                                                        if thermal_gradient is None
                                                        or np.isnan(thermal_gradient)
                                                        else thermal_gradient
                                                    ),
                                                    melt_pool_width=(
                                                        MicrostructureInput.DEFAULT_MELT_POOL_WIDTH  # noqa: E501, line too long
                                                        if melt_pool_width is None
                                                        or np.isnan(melt_pool_width)
                                                        else melt_pool_width
                                                    ),
                                                    melt_pool_depth=(
                                                        MicrostructureInput.DEFAULT_MELT_POOL_DEPTH  # noqa: E501, line too long
                                                        if melt_pool_depth is None
                                                        or np.isnan(melt_pool_depth)
                                                        else melt_pool_depth
                                                    ),
                                                    random_seed=(
                                                        MicrostructureInput.DEFAULT_RANDOM_SEED
                                                        if random_seed is None
                                                        or np.isnan(random_seed)
                                                        else random_seed
                                                    ),
                                                    machine=machine,
                                                    material=AdditiveMaterial(),
                                                )
                                            except ValueError as e:
                                                LOG.error(f"Invalid parameter combination: {e}")
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
                                                    ColumnNames.STATUS: SimulationStatus.NEW,
                                                    ColumnNames.MATERIAL: self.material_name,
                                                    ColumnNames.HEATER_TEMPERATURE: t,
                                                    ColumnNames.LAYER_THICKNESS: thickness,
                                                    ColumnNames.BEAM_DIAMETER: d,
                                                    ColumnNames.LASER_POWER: p,
                                                    ColumnNames.SCAN_SPEED: v,
                                                    ColumnNames.PV_RATIO: p / v,
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
                                                        pd.NA  # random seed is of type int
                                                        if random_seed is None
                                                        or np.isnan(random_seed)
                                                        else random_seed
                                                    ),
                                                }
                                            )
                                            self._data_frame = pd.concat(
                                                [self._data_frame, row.to_frame().T],
                                                ignore_index=True,
                                            )
                                            num_permutations_added += 1
        return num_permutations_added - self._remove_duplicate_entries(overwrite=False)

    @save_on_return
    def update(
        self,
        summaries: list[
            SingleBeadSummary | PorositySummary | MicrostructureSummary | SimulationError
        ],
    ):
        """Update the results of simulations in the parametric study.

        This method updates values for existing simulations in the parametric study. To add
        completed simulations, use the :meth:`add_summaries` method instead.

        Parameters
        ----------
        summaries : list[SingleBeadSummary, PorositySummary, MicrostructureSummary, SimulationError]
             List of simulation summaries to use for updating the parametric study.

        """
        for summary in summaries:
            if isinstance(summary, SingleBeadSummary):
                self._update_single_bead(summary.input.id, summary.status, summary.melt_pool)
            elif isinstance(summary, PorositySummary):
                self._update_porosity(summary.input.id, summary.status, summary.relative_density)
            elif isinstance(summary, MicrostructureSummary):
                self._update_microstructure(
                    summary.input.id,
                    summary.status,
                    summary.xy_average_grain_size,
                    summary.xz_average_grain_size,
                    summary.yz_average_grain_size,
                )
            elif isinstance(summary, SimulationError):
                idx = self._data_frame[self._data_frame[ColumnNames.ID] == summary.input.id].index
                self._data_frame.loc[idx, ColumnNames.STATUS] = SimulationStatus.ERROR
                self._data_frame.loc[idx, ColumnNames.ERROR_MESSAGE] = summary.message
            else:
                raise TypeError(f"Invalid simulation summary type: {type(summary)}")

    def _update_single_bead(self, id: str, status: SimulationStatus, melt_pool: MeltPool):
        """Update the results of a single bead simulation in the parametric
        study data frame.
        """
        idx = self._data_frame[
            (self._data_frame[ColumnNames.ID] == id)
            & (self._data_frame[ColumnNames.TYPE] == SimulationType.SINGLE_BEAD)
        ].index
        self._data_frame.loc[idx, ColumnNames.STATUS] = status
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_WIDTH] = melt_pool.median_width()
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_DEPTH] = melt_pool.median_depth()
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_LENGTH] = melt_pool.median_length()
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_LENGTH_OVER_WIDTH] = (
            melt_pool.length_over_width()
        )
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_REFERENCE_DEPTH] = (
            melt_pool.median_reference_depth()
        )
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_REFERENCE_WIDTH] = (
            melt_pool.median_reference_width()
        )
        self._data_frame.loc[idx, ColumnNames.MELT_POOL_REFERENCE_DEPTH_OVER_WIDTH] = (
            melt_pool.depth_over_width()
        )

    def _update_porosity(self, id: str, status: SimulationStatus, relative_density: float):
        """Update the results of a porosity simulation in the parametric study
        data frame.
        """
        idx = self._data_frame[
            (self._data_frame[ColumnNames.ID] == id)
            & (self._data_frame[ColumnNames.TYPE] == SimulationType.POROSITY)
        ].index

        self._data_frame.loc[idx, ColumnNames.STATUS] = status
        self._data_frame.loc[idx, ColumnNames.RELATIVE_DENSITY] = relative_density

    def _update_microstructure(
        self,
        id: str,
        status: SimulationStatus,
        xy_avg_grain_size: float,
        xz_avg_grain_size: float,
        yz_avg_grain_size: float,
    ):
        """Update the results of a microstructure simulation in the parametric
        study data frame.
        """
        idx = self._data_frame[
            (self._data_frame[ColumnNames.ID] == id)
            & (self._data_frame[ColumnNames.TYPE] == SimulationType.MICROSTRUCTURE)
        ].index

        self._data_frame.loc[idx, ColumnNames.STATUS] = status
        self._data_frame.loc[idx, ColumnNames.XY_AVERAGE_GRAIN_SIZE] = xy_avg_grain_size
        self._data_frame.loc[idx, ColumnNames.XZ_AVERAGE_GRAIN_SIZE] = xz_avg_grain_size
        self._data_frame.loc[idx, ColumnNames.YZ_AVERAGE_GRAIN_SIZE] = yz_avg_grain_size

    @save_on_return
    def add_inputs(
        self,
        inputs: list[SingleBeadInput | PorosityInput | MicrostructureInput],
        iteration: int = DEFAULT_ITERATION,
        priority: int = DEFAULT_PRIORITY,
        status: SimulationStatus = SimulationStatus.NEW,
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

        status : SimulationStatus, default: :obj:`SimulationStatus.NEW`
            Valid types are :obj:`SimulationStatus.NEW` and :obj:`SimulationStatus.SKIP`.

        Returns
        -------
        int
            The number of simulations added to the parametric study.

        """
        if status not in [SimulationStatus.SKIP, SimulationStatus.NEW]:
            raise ValueError(
                f"Simulation status must be '{SimulationStatus.NEW}' or '{SimulationStatus.SKIP}'"
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
            dict[ColumnNames.ID] = input.id
            dict[ColumnNames.STATUS] = status
            dict[ColumnNames.MATERIAL] = self.material_name
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
        for status in SimulationStatus:
            if len(current_df[current_df[ColumnNames.STATUS] == status.value]) > 0:
                sorted_df = pd.concat(
                    [
                        sorted_df,
                        current_df[current_df[ColumnNames.STATUS] == status.value],
                    ],
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
                strict=False,
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
            strict=False,
        ):
            if len(df) > 0:
                duplicates_removed_df = pd.concat(
                    [
                        duplicates_removed_df,
                        df.drop_duplicates(subset=params, ignore_index=True, keep="first"),
                    ]
                )

        self._data_frame = duplicates_removed_df
        self._data_frame.reset_index(drop=True, inplace=True)
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
    def set_simulation_status(
        self, ids: str | list[str], status: SimulationStatus, err_msg: str = ""
    ):
        """Set the status of simulations in the parametric study.

        Parameters
        ----------
        ids : str, list[str]
            One or more IDs of the simulations to update.
        status : SimulationStatus
            Status for the simulations.
        err_msg : str, default: ""
            Error message for the simulations. Only used if status is SimulationStatus.ERROR.

        """
        if isinstance(ids, str):
            ids = [ids]
        LOG.debug(f"Setting status of simulations {', '.join(ids)} to {status}.")
        idx = self._data_frame.index[self._data_frame[ColumnNames.ID].isin(ids)]
        self._data_frame.loc[idx, ColumnNames.STATUS] = status
        if status == SimulationStatus.ERROR:
            self._data_frame.loc[idx, ColumnNames.ERROR_MESSAGE] = err_msg

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
        uid = f"{_prefix}_{misc.short_uuid(6)}"
        while self._data_frame[ColumnNames.ID].str.match(f"{uid}").any():
            uid = f"{_prefix}_{misc.short_uuid(6)}"
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
        version = 1 if "Heater Temp (°C)" in study.data_frame().columns else study.format_version

        if version > FORMAT_VERSION:
            raise ValueError(
                f"Unsupported version, study version = {version}, "
                "latest supported version is {FORMAT_VERSION}."
            )

        if version == FORMAT_VERSION:
            return study

        LOG.warning("Updating parametric study to latest version.")

        # WARNING: Create a new study with the same file name but empty data frame
        new_study = ParametricStudy._new(study.file_name)
        df = study.data_frame()

        if version < 2:
            df = df.rename(
                columns={
                    "Heater Temp (°C)": "Heater Temp (C)",
                    "Start Angle (°)": "Start Angle (degrees)",
                    "Rotation Angle (°)": "Rotation Angle (degrees)",
                    "Cooling Rate (°K/s)": "Cooling Rate (K/s)",
                    "Thermal Gradient (°K/m)": "Thermal Gradient (K/m)",
                    "XY Average Grain Size (µm)": "XY Average Grain Size (microns)",
                    "XZ Average Grain Size (µm)": "XZ Average Grain Size (microns)",
                    "YZ Average Grain Size (µm)": "YZ Average Grain Size (microns)",
                    "Melt Pool Length/Width (m)": "Melt Pool Length/Width",
                    "Melt Pool Ref Depth/Width (m)": "Melt Pool Ref Depth/Width",
                }
            )
            version = 2
        if version < 3:
            materials = df[ColumnNames.MATERIAL].array
            if not materials:
                raise ValueError(
                    "Unable to determine material. "
                    "Study has no simulations. "
                    "Create new study instead of loading from file."
                )
            new_study._material_name = materials[0]
            version = 3

            # add p/v column to the dataframe
            df = ParametricStudy._add_pv_ratio(df)

        # Update the dataframe in the new study
        new_study._data_frame = df
        return new_study

    @staticmethod
    def _add_pv_ratio(df: pd.DataFrame) -> pd.DataFrame:
        """Add PV Ratio column to the parametric study.

        Parameters
        ----------
        df : pd.DataFrame
            Data frame containing the parametric study.

        Returns
        -------
        pd.DataFrame
            Updated data frame.

        """
        if ColumnNames.PV_RATIO not in df.columns:
            scan_speed_index = df.columns.get_loc(ColumnNames.SCAN_SPEED)
            df.insert(scan_speed_index + 1, ColumnNames.PV_RATIO, None)

        df[ColumnNames.PV_RATIO] = df[ColumnNames.LASER_POWER] / df[ColumnNames.SCAN_SPEED]
        return df

    @save_on_return
    def _add_simulations_from_csv(self, file_path: str | os.PathLike) -> list[str]:
        """Add simulations from an imported CSV file to the parametric study.

        Parameters
        ----------
        file_path : str, os.PathLike
            Absolute path to the CSV file containing simulation data.

        Returns
        -------
        list[str]
            List of error messages for invalid simulations.

        """
        try:
            df = pd.read_csv(file_path, index_col=0)
        except Exception as e:
            raise ValueError(f"Unable to read CSV file: {e}") from e

        columns = {getattr(ColumnNames, c) for c in ColumnNames.__dict__ if not c.startswith("_")}
        # older CSV files may not have the PV_RATIO column
        columns.remove(ColumnNames.PV_RATIO)

        if not set(df.columns).issuperset(columns):
            raise ValueError(
                f"CSV is missing expected columns: {', '.join(str(v) for v in (columns - set(df.columns)))}"
            )

        # add PV_RATIO column to the dataframe if not present
        if ColumnNames.PV_RATIO not in df:
            df = ParametricStudy._add_pv_ratio(df)

        # check material name
        csv_material = str(df[ColumnNames.MATERIAL].iloc[0])
        if self.material_name and not csv_material.lower() == self.material_name.lower():
            raise ValueError(
                f"Material in CSV '{csv_material}' does not match study material '{self.material_name}'"
            )

        # check valid inputs
        drop_indices, error_list = [], []
        duplicates = 0
        allowed_status = [s.value for s in SimulationStatus]
        for index, row in df.iterrows():
            valid = False
            if row[ColumnNames.STATUS] in allowed_status:
                valid, error = self._validate_input(row)
            else:
                valid, error = (
                    False,
                    f"Invalid simulation status {row[ColumnNames.STATUS]}",
                )
            if not valid:
                drop_indices.append(index)
                error_list.append(error)

        # drop invalid inputs
        df = df.drop(drop_indices)

        # assign any missing simulation ids
        if any(df[ColumnNames.ID].isna() | df[ColumnNames.ID].eq("")):
            df[ColumnNames.ID] = df[ColumnNames.ID].fillna("")
            df[ColumnNames.ID] = df[ColumnNames.ID].apply(lambda x: x if x else misc.short_uuid())

        # add simulations to the parametric study and drop duplicates
        for status in [s.value for s in SimulationStatus]:
            if len(df[df[ColumnNames.STATUS] == status]) > 0:
                self._data_frame = pd.concat(
                    [self._data_frame, df[df[ColumnNames.STATUS] == status]],
                    ignore_index=True,
                )
                duplicates += self._remove_duplicate_entries(
                    overwrite=(status == SimulationStatus.COMPLETED)
                )

        # convert priority, iteration, and random seed to int type explicitly
        self._data_frame[ColumnNames.PRIORITY] = self._data_frame[ColumnNames.PRIORITY].astype(
            pd.Int64Dtype()
        )
        self._data_frame[ColumnNames.ITERATION] = self._data_frame[ColumnNames.ITERATION].astype(
            pd.Int64Dtype()
        )
        self._data_frame[ColumnNames.RANDOM_SEED] = self._data_frame[
            ColumnNames.RANDOM_SEED
        ].astype(pd.Int64Dtype())

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
                    input[ColumnNames.ROTATION_ANGLE] = (
                        MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE
                    )
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
            bead_length = input[ColumnNames.SINGLE_BEAD_LENGTH]

            SingleBeadInput(bead_length=bead_length, machine=machine, material=material)
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
            PorosityInput(
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

            MicrostructureInput(
                sample_min_x=input[ColumnNames.MICRO_MIN_X],
                sample_min_y=input[ColumnNames.MICRO_MIN_Y],
                sample_min_z=input[ColumnNames.MICRO_MIN_Z],
                sample_size_x=input[ColumnNames.MICRO_SIZE_X],
                sample_size_y=input[ColumnNames.MICRO_SIZE_Y],
                sample_size_z=input[ColumnNames.MICRO_SIZE_Z],
                sensor_dimension=input[ColumnNames.MICRO_SENSOR_DIM],
                use_provided_thermal_parameters=test_use_provided_thermal_parameters,
                cooling_rate=(
                    MicrostructureInput.DEFAULT_COOLING_RATE
                    if (test_cooling_rate is None or math.isnan(test_cooling_rate))
                    else test_cooling_rate
                ),
                thermal_gradient=(
                    MicrostructureInput.DEFAULT_THERMAL_GRADIENT
                    if (test_thermal_gradient is None or math.isnan(test_thermal_gradient))
                    else test_thermal_gradient
                ),
                melt_pool_width=(
                    MicrostructureInput.DEFAULT_MELT_POOL_WIDTH
                    if (test_melt_pool_width is None or math.isnan(test_melt_pool_width))
                    else test_melt_pool_width
                ),
                melt_pool_depth=(
                    MicrostructureInput.DEFAULT_MELT_POOL_DEPTH
                    if (test_melt_pool_depth is None or math.isnan(test_melt_pool_depth))
                    else test_melt_pool_depth
                ),
                random_seed=(
                    MicrostructureInput.DEFAULT_RANDOM_SEED
                    if (test_random_seed is None or math.isnan(test_random_seed))
                    else test_random_seed
                ),
                machine=machine,
                material=material,
            )
            return (True, "")
        except ValueError as e:
            return (False, (f"Invalid parameter combination: {e}"))

    def simulation_inputs(
        self,
        get_material_func: Callable[[str], AdditiveMaterial],
        simulation_ids: list[str] = None,
        types: list[SimulationType] = None,
        priority: int = None,
        iteration: int = None,
    ) -> list[SingleBeadInput | PorosityInput | MicrostructureInput]:
        """Get a list of simulation inputs from the parametric study.

        Parameters
        ----------
        get_material_func: Callable[[str], AdditiveMaterial]
            Function to get the material object from the material name.
            This can be a call to the Additive server or another source.
        simulation_ids : list[str], default: None
            List of simulation IDs to run. If this value is ``None``,
            all simulations with a status of ``New`` are run.
        types : list[SimulationType], default: None
            Type of simulations to run. If this value is ``None``,
            all simulation types are run.
        priority : int, default: None
            Priority of simulations to run. If this value is ``None``,
            all priorities are run.
        iteration : int, default: None
            Iteration number of simulations to run. The default is ``None``,
            all iterations are run.

        Returns
        -------
        list[SingleBeadInput, PorosityInput, MicrostructureInput]
            List of simulation inputs.

        """
        inputs = []

        df = self.filter_data_frame(simulation_ids, types, priority, iteration)

        material = get_material_func(self.material_name)

        # NOTE: We use iterrows() instead of itertuples() here to
        # access values by column name
        for _, row in df.iterrows():
            machine = ParametricStudy._create_machine(row)
            sim_type = row[ColumnNames.TYPE]
            if sim_type == SimulationType.SINGLE_BEAD:
                inputs.append(ParametricStudy._create_single_bead_input(row, material, machine))
            elif sim_type == SimulationType.POROSITY:
                inputs.append(ParametricStudy._create_porosity_input(row, material, machine))
            elif sim_type == SimulationType.MICROSTRUCTURE:
                inputs.append(ParametricStudy._create_microstructure_input(row, material, machine))
            else:  # pragma: no cover
                LOG.warning(
                    f"Invalid simulation type: {row[ColumnNames.TYPE]} for {row[ColumnNames.ID]}, skipping"
                )
                continue

        if len(inputs) == 0:
            LOG.warning("No simulations meet the specified crtiteria.")

        return inputs

    @staticmethod
    def _create_machine(row: pd.Series) -> AdditiveMachine:
        return AdditiveMachine(
            laser_power=row[ColumnNames.LASER_POWER],
            scan_speed=row[ColumnNames.SCAN_SPEED],
            layer_thickness=row[ColumnNames.LAYER_THICKNESS],
            beam_diameter=row[ColumnNames.BEAM_DIAMETER],
            heater_temperature=row[ColumnNames.HEATER_TEMPERATURE],
            starting_layer_angle=(
                row[ColumnNames.START_ANGLE]
                if not np.isnan(row[ColumnNames.START_ANGLE])
                else MachineConstants.DEFAULT_STARTING_LAYER_ANGLE
            ),
            layer_rotation_angle=(
                row[ColumnNames.ROTATION_ANGLE]
                if not np.isnan(row[ColumnNames.ROTATION_ANGLE])
                else MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE
            ),
            hatch_spacing=(
                row[ColumnNames.HATCH_SPACING]
                if not np.isnan(row[ColumnNames.HATCH_SPACING])
                else MachineConstants.DEFAULT_HATCH_SPACING
            ),
            slicing_stripe_width=(
                row[ColumnNames.STRIPE_WIDTH]
                if not np.isnan(row[ColumnNames.STRIPE_WIDTH])
                else MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH
            ),
        )

    @staticmethod
    def _create_single_bead_input(
        row: pd.Series, material: AdditiveMaterial, machine: AdditiveMachine
    ) -> SingleBeadInput:
        sb_input = SingleBeadInput(
            material=material,
            machine=machine,
            bead_length=row[ColumnNames.SINGLE_BEAD_LENGTH],
        )
        # overwrite the ID value with the simulation ID from the table
        sb_input._id = row[ColumnNames.ID]
        return sb_input

    @staticmethod
    def _create_porosity_input(
        row: pd.Series, material: AdditiveMaterial, machine: AdditiveMachine
    ) -> PorosityInput:
        p_input = PorosityInput(
            material=material,
            machine=machine,
            size_x=row[ColumnNames.POROSITY_SIZE_X],
            size_y=row[ColumnNames.POROSITY_SIZE_Y],
            size_z=row[ColumnNames.POROSITY_SIZE_Z],
        )
        # overwrite the ID value with the simulation ID from the table
        p_input._id = row[ColumnNames.ID]
        return p_input

    @staticmethod
    def _create_microstructure_input(
        row: pd.Series, material: AdditiveMaterial, machine: AdditiveMachine
    ) -> MicrostructureInput:
        use_provided_thermal_param = (
            not np.isnan(row[ColumnNames.COOLING_RATE])
            or not np.isnan(row[ColumnNames.THERMAL_GRADIENT])
            or not np.isnan(row[ColumnNames.MICRO_MELT_POOL_WIDTH])
            or not np.isnan(row[ColumnNames.MICRO_MELT_POOL_DEPTH])
        )

        ms_input = MicrostructureInput(
            material=material,
            machine=machine,
            sample_size_x=row[ColumnNames.MICRO_SIZE_X],
            sample_size_y=row[ColumnNames.MICRO_SIZE_Y],
            sample_size_z=row[ColumnNames.MICRO_SIZE_Z],
            sensor_dimension=row[ColumnNames.MICRO_SENSOR_DIM],
            use_provided_thermal_parameters=use_provided_thermal_param,
            sample_min_x=(
                row[ColumnNames.MICRO_MIN_X]
                if not np.isnan(row[ColumnNames.MICRO_MIN_X])
                else MicrostructureInput.DEFAULT_POSITION_COORDINATE
            ),
            sample_min_y=(
                row[ColumnNames.MICRO_MIN_Y]
                if not np.isnan(row[ColumnNames.MICRO_MIN_Y])
                else MicrostructureInput.DEFAULT_POSITION_COORDINATE
            ),
            sample_min_z=(
                row[ColumnNames.MICRO_MIN_Z]
                if not np.isnan(row[ColumnNames.MICRO_MIN_Z])
                else MicrostructureInput.DEFAULT_POSITION_COORDINATE
            ),
            cooling_rate=(
                row[ColumnNames.COOLING_RATE]
                if not np.isnan(row[ColumnNames.COOLING_RATE])
                else MicrostructureInput.DEFAULT_COOLING_RATE
            ),
            thermal_gradient=(
                row[ColumnNames.THERMAL_GRADIENT]
                if not np.isnan(row[ColumnNames.THERMAL_GRADIENT])
                else MicrostructureInput.DEFAULT_THERMAL_GRADIENT
            ),
            melt_pool_width=(
                row[ColumnNames.MICRO_MELT_POOL_WIDTH]
                if not np.isnan(row[ColumnNames.MICRO_MELT_POOL_WIDTH])
                else MicrostructureInput.DEFAULT_MELT_POOL_WIDTH
            ),
            melt_pool_depth=(
                row[ColumnNames.MICRO_MELT_POOL_DEPTH]
                if not np.isnan(row[ColumnNames.MICRO_MELT_POOL_DEPTH])
                else MicrostructureInput.DEFAULT_MELT_POOL_DEPTH
            ),
            # Use np.isscalar as RANDOM_SEED is of type Int64 and an empty value
            # will come in as pd.NA which is not scalar. np.isnan will result in a TypeError.
            random_seed=(
                row[ColumnNames.RANDOM_SEED]
                if np.isscalar(row[ColumnNames.RANDOM_SEED])
                else MicrostructureInput.DEFAULT_RANDOM_SEED
            ),
        )
        # overwrite the ID value with the simulation ID from the table
        ms_input._id = row[ColumnNames.ID]
        return ms_input

    def filter_data_frame(
        self,
        simulation_ids: list[str] = None,
        types: list[SimulationType] = None,
        priority: int = None,
        iteration: int = None,
    ) -> pd.DataFrame:
        """Apply filters to the parametric study and return the filtered data frame.

        Parameters
        ----------
        simulation_ids: list[str], default: None
            List of simulation IDs to include. The default is ``None``, in which case
            all simulations with status of :obj:`SimulationStatus.NEW` are selected.
        types : list, default: None
            List of simulation types to include. The default is ``None``, in which case
            all simulation types are selected.
        priority : int, default: None
            Priority of simulations to include. The default is ``None``, in which case
            all priorities are selected.
        iteration : int, default: None
            Iteration number of simulations to include. The default is ``None``, in which case
            all iterations are selected.

        Returns
        -------
        pd.DataFrame
            Filtered view of the parametric study data frame

        """

        # Initialize the filtered view with a copy of the data frame
        view = self.data_frame()

        # Filter the data frame based on the provided simulation IDs
        if isinstance(simulation_ids, list) and len(simulation_ids) > 0:
            simulation_ids_list = []
            for sim_id in simulation_ids:
                if sim_id not in view[ColumnNames.ID].values:
                    LOG.warning(f"Simulation ID '{sim_id}' not found in the parametric study")
                elif sim_id in simulation_ids_list:
                    LOG.debug(f"Simulation ID '{sim_id}' has already been added")
                else:
                    simulation_ids_list.append(sim_id)
            view = view[view[ColumnNames.ID].isin(simulation_ids_list)]
        else:
            # Select only the simulations with status NEW if no simulation IDs are provided
            view = view[view[ColumnNames.STATUS] == SimulationStatus.NEW]

        if types:
            # Filter the data frame based on the provided simulation types
            view = view[view[ColumnNames.TYPE].isin(types)]

        # Filter the data frame based on the provided priority then sort by priority
        if priority:
            view = view[view[ColumnNames.PRIORITY] == priority]

        view = view.sort_values(by=ColumnNames.PRIORITY, ascending=True)

        # Filter the data frame based on the provided iteration
        if iteration:
            view = view[(view[ColumnNames.ITERATION] == iteration)]

        return view
