"""Sphinx documentation configuration file."""

from datetime import datetime
import os
from pathlib import Path
import sys
import warnings

from ansys_sphinx_theme import (
    ansys_favicon,
    get_autoapi_templates_dir_relative_path,
    get_version_match,
    pyansys_logo_black,
)
import numpy as np
import pyvista
from sphinx_gallery.sorting import FileNameSortKey

from ansys.additive.core import __version__

path_root = Path(__file__).parents[0]
sys.path.append(str(path_root))
from _utils.png_scraper import PNGScraper

# Manage errors
pyvista.set_error_output_file("errors.txt")

# Ensure that offscreen rendering is used for docs generation
pyvista.OFF_SCREEN = True

try:
    pyvista.global_theme.window_size = np.array([1024, 768])
except AttributeError:
    # for compatibility with pyvista < 0.40
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
switcher_version = get_version_match(__version__)

REPOSITORY_NAME = "pyadditive"
USERNAME = "ansys"
BRANCH = "main"
GALLERY_EXAMPLES_PATH = "examples/gallery_examples"
EXAMPLES_ROOT = "examples"
EXAMPLES_PATH_FOR_DOCS = f"../../{EXAMPLES_ROOT}/"
DOC_PATH = "doc/source"
SEARCH_HINTS = ["def", "class"]

# use the default pyansys logo
html_logo = pyansys_logo_black
html_theme = "ansys_sphinx_theme"
html_favicon = ansys_favicon
html_show_sourcelink = False

# specify the location of your github repo
html_theme_options = {
    "github_url": f"https://github.com/ansys/{REPOSITORY_NAME}",
    "show_prev_next": False,
    "show_breadcrumbs": True,
    "collapse_navigation": True,
    "use_edit_page_button": True,
    "additional_breadcrumbs": [
        ("PyAnsys", "https://docs.pyansys.com/"),
    ],
    "icon_links": [
        {
            "name": "Support",
            "url": f"https://github.com/{USERNAME}/{REPOSITORY_NAME}/discussions",
            "icon": "fa fa-comment fa-fw",
        },
    ],
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": switcher_version,
    },
    "check_switcher": False,
}

html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": USERNAME,
    "github_repo": REPOSITORY_NAME,
    "github_version": BRANCH,
    "doc_path": DOC_PATH,
}

# Sphinx extensions
extensions = [
    "enum_tools.autoenum",
    "jupyter_sphinx",
    "notfound.extension",
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
    "sphinx_design",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # kept here as an example
    # "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    "ansys.additive.core": (f"https://additive.docs.pyansys.com/version/{switcher_version}", None),
    "grpc": ("https://grpc.github.io/grpc/python/", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "pyvista": ("https://docs.pyvista.org/version/stable", None),
    "pypim": ("https://pypim.docs.pyansys.com/version/stable", None),
    "panel": ("https://panel.holoviz.org/", None),
}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "links.rst",
]

# numpydoc configuration
numpydoc_show_class_members = False
numpydoc_xref_param_type = True

# Consider enabling numpydoc validation. See:
# https://numpydoc.readthedocs.io/en/latest/validation.html#
# TODO: Replace this with ruff pre-commit hook
numpydoc_validate = True
numpydoc_validation_checks = {
    "GL06",  # Found unknown section
    "GL07",  # Sections are in the wrong order.
    # "GL08",  # The object does not have a docstring
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

# Common content for every RST file such us links
rst_epilog = ""
links_filepath = Path(__file__).parent.absolute() / "links.rst"
with open(links_filepath) as links_file:
    rst_epilog += links_file.read()

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
    exclude_patterns.append("autoapi")
else:
    # Configuration for Sphinx autoapi
    extensions.append("autoapi.extension")
    autoapi_root = "api"
    autoapi_type = "python"
    autoapi_dirs = ["../../src/ansys"]
    autoapi_options = [
        "members",
        "undoc-members",
        "show-inheritance",
        "show-module-summary",
        # "special-members", - don't doc dunder methods
    ]
    autoapi_template_dir = get_autoapi_templates_dir_relative_path(Path(__file__))
    suppress_warnings = ["autoapi.python_import_resolution"]
    exclude_patterns.append("_autoapi_templates/index.rst")
    autoapi_python_use_implicit_namespaces = True
    autoapi_keep_files = True
    autoapi_render_in_single_page = ["class", "enum", "exception"]


BUILD_EXAMPLES = True if os.environ.get("BUILD_EXAMPLES", "true") == "true" else False
BUILD_EXAMPLES_LONG = True if os.environ.get("BUILD_EXAMPLES_LONG", "true") == "true" else False
PLOT_GALLERY = True if os.environ.get("PLOT_GALLERY", "true") == "true" else False
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
                ".*advanced.*",
            ]
        )

    # Sphinx gallery configuration
    sphinx_gallery_conf = {
        # convert rst to md for ipynb
        "pypandoc": True,
        # path to your examples scripts
        "examples_dirs": [f"{EXAMPLES_PATH_FOR_DOCS}"],
        # where to save gallery generated examples
        "gallery_dirs": [f"{GALLERY_EXAMPLES_PATH}"],
        # Pattern to search for example files
        "filename_pattern": r"\.py",
        # Remove the "Download all examples" button from the top level gallery
        "download_all_examples": False,
        # Sort gallery examples by file name instead of number of lines (default)
        "within_subsection_order": FileNameSortKey,
        # directory where function granular galleries are stored
        "backreferences_dir": None,
        # Modules for which function level galleries are created.
        "doc_module": "ansys-additive-core",
        "image_scrapers": ("pyvista", "matplotlib", PNGScraper()),
        "ignore_pattern": r"\b(" + "|".join(ignore_patterns) + r")\b",
        "thumbnail_size": (350, 350),
        # Set plot_gallery to False for building docs without running examples.
        "plot_gallery": PLOT_GALLERY,
    }
    print(f"sphinx_gallery_conf {sphinx_gallery_conf}")

jinja_contexts = {
    "main_toctree": {
        "build_api": BUILD_API,
        "build_examples": BUILD_EXAMPLES,
    },
    "install_guide": {
        "version": f"v{version}" if not version.endswith("dev0") else "main",
    },
}

linkcheck_ignore = [
    r"https://ansyshelp.ansys.com/.*",
    r"https://ansysproducthelpqa.win.ansys.com/.*",
    r"https://www.ansys.com/.*",
]

linkcheck_retries = 3


def prepare_jinja_env(jinja_env) -> None:
    """Customize the jinja env.

    Notes
    -----
    See https://jinja.palletsprojects.com/en/3.0.x/api/#jinja2.Environment
    """
    jinja_env.globals["project_name"] = project


autoapi_prepare_jinja_env = prepare_jinja_env
