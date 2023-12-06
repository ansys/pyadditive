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
"""Provides an interactive interface for the parametric study simulation table."""
from __future__ import annotations

import os

import pandas as pd
import panel as pn

from ansys.additive.core import SimulationStatus, SimulationType
from ansys.additive.core.misc import short_uuid
from ansys.additive.core.parametric_study import ColumnNames, ParametricStudy

# global variables
_df = None
_ps = None
_iter_select = None
_pri_select = None

pn.extension("tabulator")


def show_table(ps: ParametricStudy, page_size: int = 10):
    """Generate an interactive display of the parametric study table.

    Parameters
    ----------
    ps : :class:`ParametricStudy <ansys.additive.core.parametric_study.ParametricStudy>`
        Parametric study to display.
    page_size : int, 10
        Number of table rows to display per page.

    Returns
    -------
    :class:`panel.Column <panel.Column>`
        Interactive table.
    """
    global _df, _ps, _iter_select, _pri_select

    _ps = ps
    _df = _ps.data_frame()

    (
        _iter_select,
        _pri_select,
        type_select,
        status_select,
    ) = __init_controls(_df)

    table = pn.widgets.Tabulator(
        _df,
        pagination="local",
        page_size=page_size,
        layout="fit_data_stretch",
        editors=__editors(_df),
    ).servable()
    table.add_filter(_iter_select, ColumnNames.ITERATION)
    table.add_filter(_pri_select, ColumnNames.PRIORITY)
    table.add_filter(type_select, ColumnNames.TYPE)
    table.add_filter(status_select, ColumnNames.STATUS)
    table.on_edit(__on_edit)

    control_bar = pn.Row(
        _iter_select,
        _pri_select,
        type_select,
        status_select,
        sizing_mode="stretch_width",
    )
    col = pn.Column(
        pn.widgets.StaticText(value="<b>Parametric Study</b>"),
        control_bar,
        pn.widgets.StaticText(value="<i>Use CTRL + click to select multiple values.</i>"),
        table,
        sizing_mode="stretch_both",
    ).servable()
    if os.getenv("GENERATING_DOCS"):
        name = show_table.__name__
        col.save(f"{name}_{short_uuid()}.png")
        col.__repr__ = lambda: name
    return col


def __init_controls(df: pd.DataFrame) -> tuple[pn.widgets.MultiSelect, ...]:
    iter_options = sorted(df[ColumnNames.ITERATION].unique().tolist())
    pri_options = sorted(df[ColumnNames.PRIORITY].unique().tolist())
    type_options = [
        SimulationType.SINGLE_BEAD,
        SimulationType.POROSITY,
        SimulationType.MICROSTRUCTURE,
    ]
    status_options = [
        SimulationStatus.PENDING,
        SimulationStatus.COMPLETED,
        SimulationStatus.SKIP,
        SimulationStatus.ERROR,
    ]
    iter_select = pn.widgets.MultiSelect(
        name="Iteration", options=iter_options, value=iter_options, sizing_mode="stretch_width"
    ).servable()
    pri_select = pn.widgets.MultiSelect(
        name="Priority", options=pri_options, value=pri_options, sizing_mode="stretch_width"
    ).servable()
    type_select = pn.widgets.MultiSelect(
        name="Type", options=type_options, value=type_options, sizing_mode="stretch_width"
    ).servable()
    status_select = pn.widgets.MultiSelect(
        name="Status", options=status_options, value=status_options, sizing_mode="stretch_width"
    ).servable()

    return iter_select, pri_select, type_select, status_select


def __editors(df: pd.DataFrame):
    editors = {}
    for col in df.columns:
        if col == ColumnNames.STATUS:
            editors[col] = {
                "type": "list",
                "values": [
                    SimulationStatus.PENDING,
                    SimulationStatus.COMPLETED,
                    SimulationStatus.ERROR,
                    SimulationStatus.SKIP,
                ],
                "multiselect": False,
            }
        elif col in [ColumnNames.PRIORITY, ColumnNames.ITERATION]:
            editors[col] = {
                "type": "number",
                "step": 1,
            }
        else:
            editors[col] = None
    return editors


def __on_edit(event: any):
    global _df, _iter_select, _pri_select
    if event.column in [ColumnNames.STATUS, ColumnNames.PRIORITY, ColumnNames.ITERATION]:
        id = _df.loc[event.row, ColumnNames.ID]
        if event.column == ColumnNames.STATUS:
            _ps.set_status(id, event.value)
        elif event.column == ColumnNames.PRIORITY:
            _ps.set_priority(id, event.value)
            _pri_select.options = sorted(_ps.data_frame()[ColumnNames.PRIORITY].unique().tolist())
            # _pri_select.value is not type(list), so we need to create a list
            selections = [x for x in _pri_select.value]
            selections.append(event.value)
            _pri_select.value = selections
        elif event.column == ColumnNames.ITERATION:
            _ps.set_iteration(id, event.value)
            _iter_select.options = sorted(_ps.data_frame()[ColumnNames.ITERATION].unique().tolist())
            # _iter_select.value is not type(list), so we need to create a list
            selections = [x for x in _iter_select.value]
            selections.append(event.value)
            _iter_select.value = selections
        _df = _ps.data_frame()
