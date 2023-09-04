:orphan:

.. _ref_getting_started:

###############
Getting started
###############

PyAdditive is a Python client library for the Ansys Additive service.

.. note::

    PyAdditive has not been made public and is currently hosted in a private
    PyPI repository. The PyAnsys team can provide you a read-only token to
    assign to an environment variable named ``PYANSYS_PYPI_PRIVATE_PAT``.
    To request a token, email
    `pyansys.support@ansys.com <mailto:pyansys.support@ansys.com>`_.


    Additionally, the Docker image for the Additive service is stored under the private
    PyAnsys organization packages on GitHub. If you want to run the image yourself,
    you must have a GitHub account with two-factor authentication. For more
    information, see `Configuring two-factor authentication
    <https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication>`_
    in the GitHub documentation. You must also contact
    `pyansys.support@ansys.com <mailto:pyansys.support@ansys.com>`_
    to request that you be added to the PyAnsys organization.
    Lastly, you must create a personal access token with ``read:packages`` scope and
    authorize it for single sign on. For more information, see these topics in the
    GitHub documentation:

    - `Managing your personal access tokens <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token>`_
    - `Authorizing a personal access token for use with SAML single sign-on <https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/authorizing-a-personal-access-token-for-use-with-saml-single-sign-on>`_.


Ansys Lab usage
===============

The easiest way to use PyAdditive is within a Jupyter notebook in the `Ansys Lab
<https://account.activedirectory.windowsazure.com/applications/signin/d95b9231-50da-45bf-badd-4afa22a5d067?tenantId=34c6ce67-15b8-4eff-80e9-52da8be89706>`_
cloud environment.

Once you sign in to Ansys Lab, create a Jupyter notebook and connect to the Additive
service with this code:

.. code:: pycon

   >>> import ansys.additive.core as pyadditive
   >>> additive = pyadditive.Additive()

Example notebooks are available in `Examples <https://additive.docs.pyansys.com/version/dev/examples/gallery_examples/index.html>`_.


Standalone usage
================

To use PyAdditive in standalone mode, first start the Additive service locally. If you have
Docker installed, you must be authenticated to ghcr.io. For more information, see
`Working with the Container registry <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry>`_
in the GitHub documentation.

.. warning::
   To authenticate to ghcr.io, you must have your GitHub user
   account added to the PyAnsys organization as indicated in
   the preceding note.


Start the Additive service locally with this Docker command:

.. code:: bash

   docker run --rm --name additive -p 50052:50052 ghcr.io/pyansys/pyadditive:latest

Next, connect to the Additive service with this code:

.. code:: pycon

   >>> import ansys.additive.core as pyadditive
   >>> additive = pyadditive.Additive()

Installation
============

Package dependencies
--------------------

PyAdditive is supported on Python version 3.8 and later. Previous versions of Python are
no longer supported as outlined in this `Moving to require Python 3 <https://python3statement.org/>`_
statement.

PyAdditive dependencies are automatically checked when packages are installed. These projects
are required dependencies for PyAdditive:

* `ansys-api-additive <https://github.com/ansys/ansys-api-additive>`_: Python package containing the auto-generated
   gRPC Python interface files for the Additive service
* `pandoc <https://pandoc.org/installing.html>`_: Universal document converter for documentation generation
* `NumPy <https://pypi.org/project/numpy/>`_: Fundamental package for scientific computing with Python, providing
   data array access for PyAdditive
* `PyVista <https://pypi.org/project/pyvista/>`_: 3D visualization library for interactive 3D plotting of
  PyAdditive results.

..
   * `Pint <https://pypi.org/project/Pint/>`_: Python package to define, operate, and manipulate physical quantities,
     including conversions from and to different measurement units.

Install the package
-------------------

PyAdditive has three installation modes: user, developer, and offline.

Install in user mode
^^^^^^^^^^^^^^^^^^^^

On a Windows system, install `Python <https://www.python.org/downloads>`_ if it is not already installed.

Before installing PyAdditive in user mode, run this command to make sure that you have the latest version
of `pip <https://pypi.org/project/pip/>`_:

.. code:: bash

   python -m pip install -U pip

Then, run this command to install PyAdditive:

.. code:: bash

   python -m pip install ansys-additive-core

.. caution::

    Until PyAdditive is made public, you must provide the index
    URL to the private PyPI repository when performing a ``pip`` install:

    * Index URL: ``https://pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/``

    If access to this package registry is needed, email `pyansys.core@ansys.com <mailto:pyansys.core@ansys.com>`_
    to request access. The PyAnsys team can provide you a read-only token to be inserted in ``${PRIVATE_PYPI_ACCESS_TOKEN}``.

    Once you have the token run the installation command for your OS:

    .. code:: bash

        # On Linux
        pip install ansys-additive-core --index-url=https://${PYANSYS_PYPI_PRIVATE_PAT}@pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/

        # On Windows
        pip install ansys-additive --index-url=https://%PYANSYS_PYPI_PRIVATE_PAT%@pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/


Install in developer mode
^^^^^^^^^^^^^^^^^^^^^^^^^

Installing PyAdditive in developer mode allows you to modify the source code and enhance it.

.. note::
   Before contributing to PyAdditive, see the `Contributing <https://dev.docs.pyansys.com/how-to/contributing.html>`_ topic
in the *PyAnsys Developer's Guide*. You should be thoroughly familiar with this guide.

To install PyAdditive in developer mode, perform these steps:

#. Clone the repository and access the directory where it has been cloned:

   .. code:: bash

      git clone https://github.com/ansys-internal/pyadditive
      cd pyadditive

#. Create a clean Python virtual environment and activate it:

   .. code:: bash

      # Create a virtual environment
      python -m venv .venv

      # Activate it in a POSIX system
      source .venv/bin/activate

      # Activate it in Windows CMD shell
      .venv\Scripts\activate.bat

      # Activate it in Windows Powershell
      .venv\Scripts\Activate.ps1

   If you require additional information on virtual environments, see `Creation of virtual environments
   <https://docs.python.org/3/library/venv.html>`_ in the Python documentation.

#. Install the required build system tools:

   .. code:: bash

      python -m pip install -U pip tox

#. Verify your development installation:

    .. code:: bash

       tox

#. Optionally, install the project in editable mode:

    .. code:: bash

       python -m pip install -e .

#. When finished, you can exit the virtual environment:

   .. code:: bash

      deactivate

Install in offline mode
^^^^^^^^^^^^^^^^^^^^^^^

If you lack an internet connection on your installation machine (or you do not have access to the
private Ansys PyPI packages repository), you should install PyAdditive by downloading the wheelhouse
archive from the `Releases <https://github.com/ansys-internal/pyadditive/releases>`_ page for your
corresponding machine architecture.

Each wheelhouse archive contains all the Python wheels necessary to install PyAdditive from scratch on Windows,
Linux, and MacOS from Python 3.8 to 3.11. You can unzip and install the wheelhouse archive on an isolated
system with a fresh Python installation or in a virtual environment.

For example, on Linux with Python 3.8, unzip and install the wheelhouse archive with these commands:

.. code:: bash

    unzip ansys-additive-core-v0.1.dev0-wheelhouse-Linux-3.8.zip wheelhouse
    pip install ansys-additive-core -f wheelhouse --no-index --upgrade --ignore-installed

If you're on Windows with Python 3.9, unzip the wheelhouse archive to a wheelhouse directory and
then install using the preceding command.

Consider using a virtual environment for the installation.


Testing
=======

This project takes advantage of `tox`_. This tool automates common
development tasks (similar to Makefile), but it is oriented towards Python
development.

Using ``tox``
-------------

While Makefile has rules, `tox`_ has environments. In fact, ``tox`` creates its
own virtual environment so that anything being tested is isolated from the project to
guarantee the project's integrity.

The following commands are provided:

.. vale off

- **tox -e style**: Checks for coding style quality.
- **tox -e py**: Checks for and runs unit tests.
- **tox -e py-coverage**: Checks for and runs unit tests, generating code coverage reports.
- **tox -e doc**: Checks for building the documentation successfully.

.. vale on

Raw testing
-----------

If required, from the command line, you can call style commands like `black`_, `isort`_,
and `flake8`_ and call unit testing commands like `pytest`_. However,
this does not guarantee that your project is being tested in an isolated
environment, which is the reason why tools like ``tox`` exist.

To run unit tests without using ``tox``, first install the ``pytest-cov`` package in
editable mode:

.. code:: bash

   python -m pip install pytest-cov

   python -m pip install -e .

Then, run this command from the root folder of the project:

.. code:: bash

   python -m pytest

System testing on localhost
---------------------------

Install the `docker-compose <https://docs.docker.com/compose/>`_ package, if necessary.
Start the server by running this command from the root folder of the project:

.. code:: bash

   docker compose up

Open a Jupyter notebook in Visual Studio Code and execute it.

Or, use these commands to start `JupyterLab <https://pypi.org/project/jupyterlab/>`_:

.. code:: bash

   python -m venv jupyter_venv​

   jupyter_venv\Scripts\activate.bat​

   pip install jupyterlab​

   pip install jupyterlab

   jupyter lab


The URL for opening JupyterLab in your browser is ``http://localhost:8888/lab``. Note that the port number may
be different, but the port number that you should use is listed in the JupyterLab startup messages. You can find
example Jupyter notebooks in the ``examples`` folder of the PyAdditive repository.

pre-commit
==========

The style checks take advantage of `pre-commit`_. Developers are not forced but
encouraged to install this tool by running this command:

.. code:: bash

    python -m pip install pre-commit && pre-commit install


Documentation
=============

For building documentation, you can run the usual rules provided in the
`Sphinx`_ Makefile, such as:

.. code:: bash

    make -C doc/ html && your_browser_name doc/html/index.html

However, the recommended way of checking documentation integrity is to use ``tox``:

.. code:: bash

    tox -e doc && your_browser_name .tox/doc_out/index.html


Distributing
============

If you would like to create either source or wheel files, start by installing
the building requirements and then executing the build module:

.. code:: bash

    python -m pip install -U pip build twine
    python -m build
    python -m twine check dist/*

.. LINKS AND REFERENCES
.. _black: https://github.com/psf/black
.. _flake8: https://flake8.pycqa.org/en/latest/
.. _isort: https://github.com/PyCQA/isort
.. _pip: https://pypi.org/project/pip/
.. _pre-commit: https://pre-commit.com/
.. _PyAnsys Developer's guide: https://dev.docs.pyansys.com/
.. _pytest: https://docs.pytest.org/en/stable/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _tox: https://tox.wiki/
