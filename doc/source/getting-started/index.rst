:orphan:

.. _ref_getting_started:

###############
Getting started
###############

PyAdditive is a Python client library for the Ansys Additive server. The Ansys
Additive server is distributed with the Additive option of the Structures package
in the Ansys unified installation.

.. note::
   PyAdditive requires Ansys 2024 R1 or later.

.. warning::
   The simulations described in this documentation require an Additive Suite license. To obtain a license,
   contact your Ansys sales representative or see https://www.ansys.com/contact-us.


Starting a session
==================

There are multiple ways to start a session with the PyAdditive client.

.. _ref_starting_a_local_session:

Starting a local session
------------------------

Instantiating an ``Additive`` object starts the local installation of the Additive server.

.. code:: pycon

   import ansys.additive.core as pyadditive
   additive = pyadditive.Additive()

Starting a remote session
-------------------------

You can start a remote session by specifying the host name and port of the server.

.. code:: pycon

   import ansys.additive.core as pyadditive
   additive = pyadditive.Additive(host="additiveserver.mydomain.com", port=12345)

Alternative startup methods
---------------------------

For additional session startup methods, see the documentation for the
`Additive class <https://additive.docs.pyansys.com/version/stable/api/ansys/additive/core/additive/index.html#additive.Additive>`_.


Run simulations
===============

For examples of the types of simulations possible with PyAdditive, see
`Examples <https://additive.docs.pyansys.com/version/dev/examples/gallery_examples/index.html>`_.



Installation
============

Package dependencies
--------------------

PyAdditive is supported on Python version 3.9 and later. Previous versions of Python are
no longer supported as outlined in this `Moving to require Python 3 <https://python3statement.org/>`_
statement.

PyAdditive dependencies are automatically checked when packages are installed. Included
in these dependencies are these projects:

* `ansys-api-additive <https://github.com/ansys/ansys-api-additive>`_: Python package containing the auto-generated
   gRPC Python interface files for the Additive service
* `NumPy <https://pypi.org/project/numpy/>`_: Fundamental package for scientific computing with Python, providing
   data array access for PyAdditive
* `PyVista <https://pypi.org/project/pyvista/>`_: 3D visualization library for interactive 3D plotting of
  PyAdditive results.
* `Panel <https://panel.holoviz.org/>`_: Web app framework used for interactive visualization
  of PyAdditive results.


Install the package
-------------------

PyAdditive has three installation modes: user, developer, and offline.

Install in user mode
^^^^^^^^^^^^^^^^^^^^

Install `Python <https://www.python.org/downloads>`_ if it is not already installed.

Before installing PyAdditive in user mode, run this command to make sure that you have the latest version
of `pip <https://pypi.org/project/pip/>`_:

.. code:: bash

   python -m pip install -U pip

Then, run this command to install PyAdditive:

.. code:: bash

   python -m pip install ansys-additive-core

.. _ref_install_in_developer_mode:

Install in developer mode
^^^^^^^^^^^^^^^^^^^^^^^^^

Installing PyAdditive in developer mode allows you to modify the source code and enhance it.

.. note::
   Before contributing to PyAdditive, see the `Contributing <https://dev.docs.pyansys.com/how-to/contributing.html>`_ topic
   in the *PyAnsys Developer's Guide*. You should be thoroughly familiar with this guide.

To install PyAdditive in developer mode, perform these steps:

#. Clone the repository and access the directory where it has been cloned:

   .. code:: bash

      git clone https://github.com/ansys/pyadditive
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

      tox -e py

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
archive from the `Releases <https://github.com/ansys/pyadditive/releases>`_ page for your
corresponding machine architecture.

Each wheelhouse archive contains all the Python wheels necessary to install PyAdditive from scratch on Windows,
Linux, and MacOS from Python 3.9 to 3.12. You can unzip and install the wheelhouse archive on an isolated
system with a fresh Python installation or in a virtual environment.

For example, on Linux with Python 3.9, unzip then install the wheelhouse archive with these commands:

.. code:: bash

    unzip ansys-additive-core-v0.1.dev0-wheelhouse-Linux-3.9.zip wheelhouse
    pip install ansys-additive-core -f wheelhouse --no-index --upgrade --ignore-installed

If you're on Windows with Python 3.9, unzip the wheelhouse archive to a wheelhouse directory and
then install using the preceding ``pip`` command.

Consider using a virtual environment for the installation.


Testing

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

System testing can be done on localhost using the startup method
described in :ref:`ref_starting_a_local_session` within a Python script
or Jupyter notebook. The ``examples`` folder of the PyAdditive
repository contains script files that can be used for testing or
converted to Jupyter notebooks using
`Jupytext <https://jupytext.readthedocs.io/en/latest/install.html>`_.

To test with a notebook, you need to install and run
`JupyterLab <https://pypi.org/project/jupyterlab/>`_:

.. code:: bash

   python -m venv jupyter_venv​

   jupyter_venv\Scripts\activate.bat​

   pip install jupyterlab​

   pip install jupyterlab

   jupyter lab


The URL for opening JupyterLab in your browser is ``http://localhost:8888/lab``. Note that the port number may
be different, but the port number is listed in the JupyterLab startup messages.

A note on ``pre-commit``
^^^^^^^^^^^^^^^^^^^^^^^^

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
