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
