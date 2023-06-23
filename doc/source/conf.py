"""Sphinx documentation configuration file."""
from datetime import datetime
import os
import re
import warnings

from ansys_sphinx_theme import ansys_favicon, get_version_match, pyansys_logo_black
import numpy as np
import pyvista
from sphinx_gallery.sorting import FileNameSortKey

from ansys.additive import __version__

# Manage errors
pyvista.set_error_output_file("errors.txt")

# Ensure that offscreen rendering is used for docs generation
pyvista.OFF_SCREEN = True

# must be less than or equal to the XVFB window size
pyvista.rcParams["window_size"] = np.array([1024, 768])

# Save figures in specified directory
pyvista.FIGURE_PATH = os.path.join(os.path.abspath("./images/"), "auto-generated/")
if not os.path.exists(pyvista.FIGURE_PATH):
    os.makedirs(pyvista.FIGURE_PATH)

# suppress annoying matplotlib bug
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure.",
)

# Project information
project = "PyAdditive"
copyright = f"(c) {datetime.now().year} ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
release = version = __version__
cname = os.getenv("DOCUMENTATION_CNAME", "nocname.com")

# use the default pyansys logo
html_logo = pyansys_logo_black
html_theme = "ansys_sphinx_theme"
html_favicon = ansys_favicon

# specify the location of your github repo
html_theme_options = {
    "github_url": "https://github.com/ansys-internal/pyadditive",
    "show_prev_next": False,
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": get_version_match(__version__),
    },
    "navbar_end": ["version-switcher", "theme-switcher", "navbar-icon-links"],
}

# Sphinx extensions
extensions = [
    "jupyter_sphinx",
    "notfound.extension",
    "enum_tools.autoenum",
    "numpydoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinxemoji.sphinxemoji",
    "sphinx_jinja",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # kept here as an example
    # "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "pyvista": ("https://docs.pyvista.org/", None),
    "pypim": ("https://pypim.docs.pyansys.com/", None),
}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

# numpydoc configuration
numpydoc_show_class_members = False
numpydoc_xref_param_type = True

# Consider enabling numpydoc validation. See:
# https://numpydoc.readthedocs.io/en/latest/validation.html#
numpydoc_validate = True
numpydoc_validation_checks = {
    "GL06",  # Found unknown section
    "GL07",  # Sections are in the wrong order.
    "GL08",  # The object does not have a docstring
    "GL09",  # Deprecation warning should precede extended summary
    "GL10",  # reST directives {directives} must be followed by two colons
    "SS01",  # No summary found
    "SS02",  # Summary does not start with a capital letter
    "SS03",  # Summary does not end with a period
    "SS04",  # Summary contains heading whitespaces
    # "SS05", # Summary must start with infinitive verb, not third person
    "RT02",  # The first line of the Returns section should contain only the
    # type, unless multiple values are being returned"
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "custom.css",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The master toctree document.
master_doc = "index"

# The suffix(es) of source filenames.
source_suffix = {
    ".rst": "restructuredtext",
}

# Prevent showing return type multiple times
typehints_document_rtype = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# Copy button customization ---------------------------------------------------
# exclude traditional Python prompts from the copied code
copybutton_prompt_text = r">>> ?|\.\.\. "
copybutton_prompt_is_regexp = True

# -- Declare the Jinja context -----------------------------------------------
BUILD_API = True if os.environ.get("BUILD_API", "true") == "true" else False
if not BUILD_API:
    exclude_patterns.append("api")

BUILD_EXAMPLES = True if os.environ.get("BUILD_EXAMPLES", "true") == "true" else False
BUILD_EXAMPLES_LONG = True if os.environ.get("BUILD_EXAMPLES_LONG", "true") == "true" else False
if BUILD_EXAMPLES is True:
    # Necessary to build examples using PyVista
    pyvista.BUILDING_GALLERY = True
    extensions.append("sphinx_gallery.gen_gallery")

    # Declare the ignore patterns for sphinx gallery
    ignore_patterns = ["flycheck*"]

    # Include additional examples if required
    if not BUILD_EXAMPLES_LONG:
        ignore_patterns.extend(
            [
                # "00_additive_single_bead.py",
                # "01_additive_porosity.py",
                "02_additive_microstructure.py",
                "03_additive_thermal_history.py",
                "04_additive_doe.py",
                "05_optimization_workflow.py",
                "06_additive_custom_material_tuning.py",
                "07_using_a_custom_material.py",
            ]
        )

    # Sphinx gallery configuration
    sphinx_gallery_conf = {
        # convert rst to md for ipynb
        "pypandoc": True,
        # path to your examples scripts
        "examples_dirs": ["../../examples/"],
        # where to save gallery generated examples
        "gallery_dirs": ["examples"],
        # Pattern to search for example files
        "filename_pattern": r"\.py",
        # Remove the "Download all examples" button from the top level gallery
        "download_all_examples": False,
        # Sort gallery examples by file name instead of number of lines (default)
        "within_subsection_order": FileNameSortKey,
        # directory where function granular galleries are stored
        "backreferences_dir": None,
        # Modules for which function level galleries are created.
        "doc_module": "ansys-additive",
        "image_scrapers": ("pyvista", "matplotlib"),
        "ignore_pattern": r"\b(" + "|".join(map(re.escape, ignore_patterns)) + r")\b",
        "thumbnail_size": (350, 350),
        # Set plot_gallery to False for building docs without running examples.
        # "plot_gallery": False,
    }

jinja_contexts = {
    "main_toctree": {
        "build_api": BUILD_API,
        "build_examples": BUILD_EXAMPLES,
    },
}
