# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""
PyAdditive is a Python client for the Ansys additive service.
"""

# Version
# ------------------------------------------------------------------------------

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:  # pragma: no cover
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

from .additive import *
from .geometry_file import *
from .machine import *
from .material import *
from .microstructure import *
from .porosity import *
from .single_bead import *
from .thermal_history import *
