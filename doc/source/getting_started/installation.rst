Installation
############

Package dependencies
--------------------

PyAdditive is supported on Python versions 3.7+. Previous versions of Python are
no longer support as outlined `here <https://python3statement.org/>`_.
PyAdditive dependencies are automatically checked when packages are installed.
The following projects are required dependencies for PyAdditive:

* `ansys-api-geometry` - The gRPC code generated from Protobuf files.
* `NumPy <https://pypi.org/project/numpy/>`_ - NumPy arrays provide a core foundation for data array access for PyAdditive.
* `PyVista <https://pypi.org/project/pyvista/>`_ - PyVista is used for interactive 3D plotting.
..
   * `Pint <https://pypi.org/project/Pint/>`_ - Pint is used for the measurement units.

PyPI
----

In order to install PyAdditive, make sure you have the latest version of
`pip`_. To do so, run:

   .. code:: bash

      python -m pip install -U pip

Then, you can simply execute:

   .. code:: bash

      poetry run python -m pip install ansys-additive

.. caution::

    PyAdditive is currently hosted in a private PyPI repository. You must provide the index
    URL to the private PyPI repository:

    * Index URL: ``https://pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/``

    If access to this package registry is needed, email `pyansys.support@ansys.com <mailto:pyansys.support@ansys.com>`_
    to request access. The PyAnsys team can provide you a read-only token to be inserted in ``${PRIVATE_PYPI_ACCESS_TOKEN}``.
    Once you have it, run the following command:

    .. code:: bash

        pip install ansys-additive --index-url=https://${PRIVATE_PYPI_ACCESS_TOKEN}@pkgs.dev.azure.com/pyansys/_packaging/pyansys/pypi/simple/

Alternatively, install the latest from `PyAdditive`_ GitHub via:

   .. code:: bash

      git clone https://github.com/pyansys/pyadditive
      cd pyadditive
      pip install -e .

You can verify your development installation by running:

   .. code:: bash

      tox

Offline mode installation
-------------------------

If you lack an internet connection on your installation machine (or you do not have access to the
private PyPI package), the recommended way of installing PyAdditive is downloading the wheelhouse
archive from the `Releases Page <https://github.com/pyansys/pyadditive/releases>`_ for your
corresponding machine architecture.

Each wheelhouse archive contains all the Python wheels necessary to install PyAdditive from scratch on Windows,
Linux, and MacOS from Python 3.7 to 3.10. You can install this on an isolated system with a fresh Python
installation or on a virtual environment.

For example, on Linux with Python 3.7, unzip the wheelhouse archive and install it with the following:

.. code:: bash

    unzip ansys-additive-v0.2.dev0-wheelhouse-Linux-3.7.zip wheelhouse
    pip install ansys-additive -f wheelhouse --no-index --upgrade --ignore-installed

If you're on Windows with Python 3.9, unzip to a wheelhouse directory and install using the same command as preceding.

Consider installing using a `virtual environment <https://docs.python.org/3/library/venv.html>`_.

.. Verify your installation
   ------------------------
   Check the :class:`Additive() <ansys.additive.()>` connection by:
   .. code:: python
    >>> from ansys.geometry.core import Modeler
    >>> modeler = Modeler()
    >>> print(modeler)
    Ansys Additive Modeler (0x205c5c17d90)
    Ansys Additive Modeler Client (0x205c5c16e00)
    Target:     localhost:652
    Connection: Healthy
   If you see a response from the server, you are ready to get started using PyAdditive as a service.
   For more details regarding the PyAdditive interface, see :ref:`user guide <ref_user_guide>`.

.. LINKS AND REFERENCES
.. _pip: https://pypi.org/project/pip/
.. _PyAdditive: https://github.com/pyansys/pyadditive
