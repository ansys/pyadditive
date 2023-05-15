.. _ref_readme:

##########
PyAdditive
##########
|pyansys| |python| |pypi| |GH-CI| |codecov| |MIT| |black|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/pypi/pyversions/ansys-additive?logo=pypi
   :target: https://pypi.org/project/ansys-additive/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/ansys-additive.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/ansys-additive
   :alt: PyPI

.. |codecov| image:: https://codecov.io/gh/pyansys/ansys-additive/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/pyansys/pyadditive
   :alt: Codecov

.. |GH-CI| image:: https://github.com/ansys-internal/pyadditive/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/ansys-internal/pyadditive/actions/workflows/ci_cd.yml
   :alt: GH-CI

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat
   :target: https://github.com/psf/black
   :alt: Black


A Python client library for the Ansys additive service.

.. note::

    PyAdditive has not been made public and is currently hosted in a private
    PyPI repository. The PyAnsys team can provide you a read-only token to be
    assigned to an environment variable called ``PYANSYS_PYPI_PRIVATE_PAT``.
    To request a token, email
    `pyansys.support@ansys.com <mailto:pyansys.support@ansys.com>`_.


    Additionally, the additive service docker image is stored under the private
    PyAnsys organization packages on GitHub. If you want to run the image yourself,
    you'll need to have a GitHub account with
    `two factor authentication <https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication>`_
    and request to be added to the PyAnsys organization by contacting
    `pyansys.support@ansys.com <mailto:pyansys.support@ansys.com>`_.
    You will also need to create a
    `personal access token <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token>`_
    with ``read:packages`` scope and `authorize it for single sign on
    <https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/authorizing-a-personal-access-token-for-use-with-saml-single-sign-on>`_.


Ansys Lab Usage
===============

The easiest way to use PyAdditive is within a jupyter notebook in the `Ansys Lab
<https://account.activedirectory.windowsazure.com/applications/signin/d95b9231-50da-45bf-badd-4afa22a5d067?tenantId=34c6ce67-15b8-4eff-80e9-52da8be89706>`_
cloud environment.

Once logged in to Ansys Lab, create a new jupyter notebook and connect to the additive service using:

.. code:: python

   >>> import ansys.additive as pyadditive
   >>> additive = pyadditive.Additive()

Example notebooks can found in the `Examples <https://additive.docs.pyansys.com/dev/examples/index.html>`_
section of the `PyAdditive documentation <https://additive.docs.pyansys.com/dev/index.html>`_.


Standalone Usage
================

To use PyAdditive in a standalone mode, first start the service locally. If you have docker installed and have
`authenticated to ghcr.io
<https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry>`_,
you can start the additive service locally using ``docker`` with:

.. warning::
   In order to authenticate to ghcr.io, you will need to have your GitHub user
   account added to the PyAnsys organization. See note above.

.. code:: bash

   docker run --rm --name additive -p 50052:50052 ghcr.io/pyansys/pyadditive:latest

Next, connect to the service with:

.. code:: python

   >>> import ansys.additive as pyadditive
   >>> additive = pyadditive.Additive()

Installation
============

Package dependencies
--------------------

PyAdditive is supported on Python versions >= 3.8. Previous versions of Python are
no longer supported as outlined `here <https://python3statement.org/>`_.
PyAdditive dependencies are automatically checked when packages are installed.
The following projects are required dependencies for PyAdditive:

* `ansys-api-additive` - The gRPC code generated from Protobuf files.
* `pandoc <https://pandoc.org/installing.html>`_ - pandoc is used for documentation generation
* `NumPy <https://pypi.org/project/numpy/>`_ - NumPy arrays provide a core foundation for data array access for PyAdditive.
* `PyVista <https://pypi.org/project/pyvista/>`_ - PyVista is used for result visualization interactive 3D plotting.

..
   * `Pint <https://pypi.org/project/Pint/>`_ - Pint is used for the measurement units.

How to install
--------------

We have three modes of installation: user, developer and offline.

For users
^^^^^^^^^

On Windows systems, download and install `Python <https://www.python.org/downloads>`_, if it is not
already installed.
In order to install PyAdditive, make sure you have the latest version of `pip <https://pypi.org/project/pip/>`_, then run:

.. code:: bash

   python -m pip install -U pip

Then, you can simply execute:

.. code:: bash

   python -m pip install ansys-additive

.. warning::

    Until PyAdditive is made public, you must provide the index
    URL to the private PyPI repository when performing a ``pip install``.

    * Index URL: ``https://pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/``

    .. code:: bash

        # On linux
        pip install ansys-additive --index-url=https://${PYANSYS_PYPI_PRIVATE_PAT}@pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/

        # On Windows
        pip install ansys-additive --index-url=https://%PYANSYS_PYPI_PRIVATE_PAT%@pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/

    See note above for how to get the access token to use for ``PYANSYS_PYPI_PRIVATE_PAT``.


For developers
^^^^^^^^^^^^^^

Installing PyAdditive in developer mode allows you to modify the source code and enhance it.

Before contributing to the project, please refer to the `Contributing <https://dev.docs.pyansys.com/how-to/contributing.html>`_ topic
in the *PyAnsys Developer's Guide*. You will need to follow these steps:

#. Clone this repository:

   .. code:: bash

      git clone https://github.com/ansys-internal/pyadditive
      cd pyadditive

#. Create a new Python environment and activate it:

   .. code:: bash

      # Create a virtual environment
      python -m venv .venv

      # Activate it in a POSIX system
      source .venv/bin/activate

      # Activate it in Windows CMD shell
      .venv\Scripts\activate.bat

      # Activate it in Windows Powershell
      .venv\Scripts\Activate.ps1

#. Install the required build system tools:

   .. code:: bash

      python -m pip install -U pip tox

#. Verify your development installation by running:

    .. code:: bash

       tox

    .. warning::

       ``PYANSYS_PYPI_PRIVATE_PAT`` must be defined for ``tox`` to run to completion.
       See note above for more information.

#. Optionally, install the project in editable mode:

    .. code:: bash

       python -m pip install -e .

#. When finished, you can exit the virtual environment by running:

   .. code:: bash

      deactivate

Offline mode installation
^^^^^^^^^^^^^^^^^^^^^^^^^

If you lack an internet connection on your installation machine (or you do not have access to the
private Ansys PyPI packages repository), the recommended way of installing PyAdditive is downloading the wheelhouse
archive from the `Releases Page <https://github.com/ansys-internal/pyadditive/releases>`_ for your
corresponding machine architecture.

Each wheelhouse archive contains all the Python wheels necessary to install PyAdditive from scratch on Windows,
Linux, and MacOS from Python 3.8 to 3.11. You can install this on an isolated system with a fresh Python
installation or on a virtual environment.

For example, on Linux with Python 3.8, unzip the wheelhouse archive and install it with the following:

.. code:: bash

    unzip ansys-additive-v0.1.dev0-wheelhouse-Linux-3.8.zip wheelhouse
    pip install ansys-additive -f wheelhouse --no-index --upgrade --ignore-installed

If you're on Windows with Python 3.9, unzip to a wheelhouse directory and install using the same command as above.

Consider installing using a `virtual environment <https://docs.python.org/3/library/venv.html>`_.

Testing
=======

This project takes advantage of `tox`_. This tool allows to automate common
development tasks (similar to Makefile) but it is oriented towards Python
development.

Using tox
---------

As Makefile has rules, `tox`_ has environments. In fact, the tool creates its
own virtual environment so anything being tested is isolated from the project in
order to guarantee project's integrity. The following environments commands are provided:

- **tox -e style**: will check for coding style quality.
- **tox -e py**: runs unit tests.
- **tox -e py-coverage**: runs unit tests and generates code coverage reports.
- **tox -e doc**: builds and checks the documentation.


Raw testing
-----------

If required, you can always call the style commands (`black`_, `isort`_,
`flake8`_...) or unit testing ones (`pytest`_) from the command line. However,
this does not guarantee that your project is being tested in an isolated
environment, which is the reason why tools like `tox`_ exist.

To run the unit tests without using tox, first install ``pytest-cov`` and the
project in editable mode.

.. code:: bash

   python -m pip install pytest-cov

   python -m pip install -e .

Then use the following command within the root folder of the project.

.. code:: bash

   python -m pytest

System testing on localhost
---------------------------

Install `docker-compose <https://docker-docs.netlify.app/compose/install/>`_, if necessary.
Start the server using the following command from the root folder of the project.

.. code:: bash

   docker compose up

Open a jupyter notebook in VS Code and execute it or start jupyter lab using the following
commands.

.. code:: bash

   python -m venv jupyter_venv​

   jupyter_venv\Scripts\activate.bat​

   pip install jupyterlab​

   pip install jupyterlab

   jupyter lab


Open jupyter lab in your browser using ``http://localhost:8888/lab``. Note the port number may
be different but it will be listed in the ``jupyter lab`` start up messages. Example
notebooks can be found in the ``examples`` folder of this repository.

A note on pre-commit
====================

The style checks take advantage of `pre-commit`_. Developers are not forced but
encouraged to install this tool via:

.. code:: bash

    python -m pip install pre-commit && pre-commit install


Documentation
=============

For building documentation, you can either run the usual rules provided in the
`Sphinx`_ Makefile, such us:

.. code:: bash

    make -C doc/ html && your_browser_name doc/html/index.html

However, the recommended way of checking documentation integrity is using:

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
