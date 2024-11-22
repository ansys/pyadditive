:orphan:

.. _ref_getting_started:

###############
Getting started
###############

PyAdditive is a Python client library for the Ansys Additive server application. The Ansys
Additive server is distributed with the Additive option of the Structures package
in the Ansys unified installation.

.. warning::
   The simulations described in this documentation require an Additive Suite license. To obtain a license,
   contact your Ansys sales representative or see https://www.ansys.com/contact-us.

Compatibility
=============

To use all the features of PyAdditive, you must have have a compatible version of Ansys installed.
The following table lists the compatibility between PyAdditive and Ansys releases.

.. list-table::
    :header-rows: 1
    :width: 50%
    :align: left

    * - PyAdditive Version
      - Ansys Release Version
    * - 0.19.x
      - 2025 R1
    * - 0.18.x
      - 2024 R2
    * - 0.17.x
      - 2024 R1


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



User installation
=================

There are multiple sources for installing the latest stable version of
PyAdditive. These include ``pip`` and ``GitHub``.


.. jinja:: install_guide

    .. tab-set::

        .. tab-item:: Public PyPI

            .. code-block::

                python -m pip install ansys-additive-core

        .. tab-item:: Ansys PyPI

            .. code-block::

                export PIP_EXTRA_INDEX_URL="https://${PYANSYS_PYPI_PRIVATE_PAT}@pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/"
                python -m pip install ansys-additive-core

        .. tab-item:: GitHub

            .. code-block::

                python -m pip install git+https://github.com/ansys/pyadditive.git@{{ version }}


.. _ref_install_in_developer_mode:

Developer installation
======================

Developer installation is specifically intended for project maintainers.
This specialized installation is tailored to equip developers with the essential
tools and resources required for effective contribution to the project's
development and maintenance. The developer installation assumes a certain level
of technical expertise and familiarity with the project's codebase, rendering it
most suitable for individuals actively engaged in its continuous development and
maintenance.

Start by cloning the repository:

.. code-block::

    git clone git@github.com:ansys/pyadditive


Move inside the project and create a new Python environment:

.. tab-set::

    .. tab-item:: Windows

        .. tab-set::

            .. tab-item:: CMD

                .. code-block:: text

                    py -m venv <venv>

            .. tab-item:: PowerShell

                .. code-block:: text

                    py -m venv <venv>

    .. tab-item:: Linux/UNIX

        .. code-block:: text

            python -m venv <venv>

Activate previous environment:

.. tab-set::

    .. tab-item:: Windows

        .. tab-set::

            .. tab-item:: CMD

                .. code-block:: text

                    <venv>\Scripts\activate.bat

            .. tab-item:: PowerShell

                .. code-block:: text

                    <venv>\Scripts\Activate.ps1

    .. tab-item:: Linux/UNIX

        .. code-block:: text

            source <venv>/bin/activate

Install the required build system tools:

.. code-block::

    python -m pip install -U pip tox

Verify your development installation:

.. code-block::

    tox -e py

Install the project in editable mode. This means that any changes you make to
the package's source code immediately reflect in your project without requiring you
to reinstall it.

.. code-block::

    python -m pip install --editable .


When finished, you can exit the virtual environment:

.. code-block::

    deactivate

Install in offline mode
-----------------------

If you lack an internet connection on your installation machine, you should install
PyAdditive by downloading the wheelhouse archive from the
`Releases <https://github.com/ansys/pyadditive/releases>`_ page for your
corresponding machine architecture.

Each wheelhouse archive contains all the Python wheels necessary to install PyAdditive from scratch on Windows,
Linux, and MacOS. You can unzip and install the wheelhouse archive on an isolated
system with a fresh Python installation or in a virtual environment.

For example, on Linux with Python 3.12, unzip then install the wheelhouse archive with these commands:

.. code-block::

    unzip ansys-additive-core-v0.1.0-wheelhouse-Linux-3.12.zip wheelhouse
    pip install ansys-additive-core -f wheelhouse --no-index --upgrade --ignore-installed

If you're on Windows, unzip the wheelhouse archive to a wheelhouse directory and
then install using the preceding ``pip`` command.

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

To run unit tests without using ``tox``, first install the ``tests`` dependencies.

.. code-block::

   python -m pip install -e .[tests]

Then, run this command from the root folder of the project:

.. code-block::

   python -m pytest

Debugging with Visual Studio Code
---------------------------------

In order to debug the code with Visual Studio Code, you need to Install
the **Python** and **Python Debugger** extensions. You will also need to
comment out the ``addopts`` line in ``pyproject.toml``. The coverage flags
for ``pytest`` prevent the debugger from stopping at breakpoints. Restore
the ``addopts`` line when you are finished debugging.

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

.. code-block::

   python -m venv jupyter_venv​

   jupyter_venv\Scripts\activate.bat​

   pip install jupyterlab​

   pip install jupyterlab

   jupyter lab


The URL for opening JupyterLab in your browser is ``http://localhost:8888/lab``. Note that the port number may
be different, but the port number is listed in the JupyterLab startup messages.

Adhere to code style
--------------------

PyAdditive follows the PEP8 standard as outlined in
`PEP 8 <https://dev.docs.pyansys.com/coding-style/pep8.html>`_ in
the *PyAnsys Developer's Guide* and implements style checking using
`pre-commit <https://pre-commit.com/>`_.

To ensure your code meets minimum code styling standards, run these commands::

  pip install pre-commit
  pre-commit run --all-files

You can also install this as a pre-commit hook by running this command::

  pre-commit install


Documentation
=============

For building documentation, you can run the usual rules provided in the
`Sphinx`_ Makefile, such as:

.. code-block::

    make -C doc/ html && your_browser_name doc/html/index.html

However, the recommended way of checking documentation integrity is to use ``tox``:

.. code-block::

    tox -e doc && your_browser_name .tox/doc_out/index.html


Distributing
============

If you would like to create either source or wheel files, start by installing
the building requirements and then executing the build module:

.. code-block::

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
