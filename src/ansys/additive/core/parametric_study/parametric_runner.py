# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
from typing import List, Optional, Union

import numpy as np
import pandas as pd

from ansys.additive.core import (
    Additive,
    AdditiveMachine,
    AdditiveMaterial,
    MachineConstants,
    MicrostructureInput,
    MicrostructureSummary,
    PorosityInput,
    PorositySummary,
    SimulationStatus,
    SimulationType,
    SingleBeadInput,
    SingleBeadSummary,
)
from ansys.additive.core.parametric_study.constants import ColumnNames


class ParametricRunner:
    @staticmethod
    def simulate(
        df: pd.DataFrame,
        additive: Additive,
        type: Optional[List[SimulationType]] = None,
        priority: Optional[int] = None,
    ) -> List[Union[MicrostructureSummary, PorositySummary, SingleBeadSummary]]:
        """Run the simulations in the parametric study with
        ``SimulationStatus.PENDING`` in the ``ColumnNames.STATUS`` column.

        Execution order is determined by the values in the ``ColumnNames.PRIORITY`` column.
        Lower values are interpreted as having higher priority and will be run first.

        Parameters
        ----------
        df : pd.DataFrame
            The parametric study data frame.
        additive: Additive
            The :class:`Additive <ansys.additive.core.additive.Additive>` service connection to
            use for running simulations.
        type : Optional[List[SimulationType]], optional
            The type of simulations to run, ``None`` indicates all types.
        priority : Optional[int]
            The priority of simulations to run, ``None`` indicates all priorities.

        Returns
        -------
        List[Union[MicrostructureSummary, PorositySummary, SingleBeadSummary]]
            A list of simulation summaries.
        """
        if type is None:
            type = [
                SimulationType.SINGLE_BEAD,
                SimulationType.POROSITY,
                SimulationType.MICROSTRUCTURE,
            ]
        elif not isinstance(type, list):
            type = [type]

        view = df[
            (df[ColumnNames.STATUS] == SimulationStatus.PENDING) & df[ColumnNames.TYPE].isin(type)
        ]
        if priority is not None:
            view = view[view[ColumnNames.PRIORITY] == priority]
        view = view.sort_values(by=ColumnNames.PRIORITY, ascending=True)

        inputs = []
        # NOTICE: We use iterrows() instead of itertuples() here in order to
        # access values by column name
        for _, row in view.iterrows():
            try:
                material = additive.get_material(row[ColumnNames.MATERIAL])
            except Exception:
                print(
                    f"Material {row[ColumnNames.MATERIAL]} not found, skipping {row[ColumnNames.ID]}"
                )
                continue
            machine = ParametricRunner._create_machine(row)
            sim_type = row[ColumnNames.TYPE]
            if sim_type == SimulationType.SINGLE_BEAD:
                inputs.append(ParametricRunner._create_single_bead_input(row, material, machine))
            elif sim_type == SimulationType.POROSITY:
                inputs.append(ParametricRunner._create_porosity_input(row, material, machine))
            elif sim_type == SimulationType.MICROSTRUCTURE:
                inputs.append(ParametricRunner._create_microstructure_input(row, material, machine))
            else:  # pragma: no cover
                print(
                    f"Invalid simulation type: {row[ColumnNames.TYPE]} for {row[ColumnNames.ID]}, skipping"
                )
                continue

        summaries = additive.simulate(inputs)

        # TODO: Return the summaries one at a time, possibly as an iterator,
        # so that the data frame can be updated as each simulation completes.
        return summaries

    @staticmethod
    def _create_machine(row: pd.Series) -> AdditiveMachine:
        return AdditiveMachine(
            laser_power=row[ColumnNames.LASER_POWER],
            scan_speed=row[ColumnNames.SCAN_SPEED],
            layer_thickness=row[ColumnNames.LAYER_THICKNESS],
            beam_diameter=row[ColumnNames.BEAM_DIAMETER],
            heater_temperature=row[ColumnNames.HEATER_TEMPERATURE],
            starting_layer_angle=row[ColumnNames.START_ANGLE]
            if not np.isnan(row[ColumnNames.START_ANGLE])
            else MachineConstants.DEFAULT_STARTING_LAYER_ANGLE,
            layer_rotation_angle=row[ColumnNames.ROTATION_ANGLE]
            if not np.isnan(row[ColumnNames.ROTATION_ANGLE])
            else MachineConstants.DEFAULT_LAYER_ROTATION_ANGLE,
            hatch_spacing=row[ColumnNames.HATCH_SPACING]
            if not np.isnan(row[ColumnNames.HATCH_SPACING])
            else MachineConstants.DEFAULT_HATCH_SPACING,
            slicing_stripe_width=row[ColumnNames.STRIPE_WIDTH]
            if not np.isnan(row[ColumnNames.STRIPE_WIDTH])
            else MachineConstants.DEFAULT_SLICING_STRIPE_WIDTH,
        )

    @staticmethod
    def _create_single_bead_input(
        row: pd.Series, material: AdditiveMaterial, machine: AdditiveMachine
    ) -> SingleBeadInput:
        return SingleBeadInput(
            id=row[ColumnNames.ID],
            material=material,
            machine=machine,
            bead_length=row[ColumnNames.SINGLE_BEAD_LENGTH],
        )

    @staticmethod
    def _create_porosity_input(
        row: pd.Series, material: AdditiveMaterial, machine: AdditiveMachine
    ) -> PorosityInput:
        return PorosityInput(
            id=row[ColumnNames.ID],
            material=material,
            machine=machine,
            size_x=row[ColumnNames.POROSITY_SIZE_X],
            size_y=row[ColumnNames.POROSITY_SIZE_Y],
            size_z=row[ColumnNames.POROSITY_SIZE_Z],
        )

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

        return MicrostructureInput(
            id=row[ColumnNames.ID],
            material=material,
            machine=machine,
            sample_size_x=row[ColumnNames.MICRO_SIZE_X],
            sample_size_y=row[ColumnNames.MICRO_SIZE_Y],
            sample_size_z=row[ColumnNames.MICRO_SIZE_Z],
            sensor_dimension=row[ColumnNames.MICRO_SENSOR_DIM],
            use_provided_thermal_parameters=use_provided_thermal_param,
            sample_min_x=row[ColumnNames.MICRO_MIN_X]
            if not np.isnan(row[ColumnNames.MICRO_MIN_X])
            else MicrostructureInput.DEFAULT_POSITION_COORDINATE,
            sample_min_y=row[ColumnNames.MICRO_MIN_Y]
            if not np.isnan(row[ColumnNames.MICRO_MIN_Y])
            else MicrostructureInput.DEFAULT_POSITION_COORDINATE,
            sample_min_z=row[ColumnNames.MICRO_MIN_Z]
            if not np.isnan(row[ColumnNames.MICRO_MIN_Z])
            else MicrostructureInput.DEFAULT_POSITION_COORDINATE,
            cooling_rate=row[ColumnNames.COOLING_RATE]
            if not np.isnan(row[ColumnNames.COOLING_RATE])
            else MicrostructureInput.DEFAULT_COOLING_RATE,
            thermal_gradient=row[ColumnNames.THERMAL_GRADIENT]
            if not np.isnan(row[ColumnNames.THERMAL_GRADIENT])
            else MicrostructureInput.DEFAULT_THERMAL_GRADIENT,
            melt_pool_width=row[ColumnNames.MICRO_MELT_POOL_WIDTH]
            if not np.isnan(row[ColumnNames.MICRO_MELT_POOL_WIDTH])
            else MicrostructureInput.DEFAULT_MELT_POOL_WIDTH,
            melt_pool_depth=row[ColumnNames.MICRO_MELT_POOL_DEPTH]
            if not np.isnan(row[ColumnNames.MICRO_MELT_POOL_DEPTH])
            else MicrostructureInput.DEFAULT_MELT_POOL_DEPTH,
            random_seed=row[ColumnNames.RANDOM_SEED]
            if not np.isnan(row[ColumnNames.RANDOM_SEED])
            else MicrostructureInput.DEFAULT_RANDOM_SEED,
        )
