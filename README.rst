##########
PyAdditive
##########

|pyansys| |python| |pypi| |GH-CI| |codecov| |MIT|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/pypi/pyversions/ansys-additive-core?logo=pypi
   :target: https://pypi.org/project/ansys-additive-core/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/ansys-additive-core.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/ansys-additive-core
   :alt: PyPI

.. |codecov| image:: https://codecov.io/gh/ansys/pyadditive/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/pyansys/pyadditive
   :alt: Codecov

.. |GH-CI| image:: https://github.com/ansys/pyadditive/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/ansys/pyadditive/actions/workflows/ci_cd.yml
   :alt: GH-CI

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

Overview
========

PyAdditive is a Python client library for the `Ansys Additive`_ service.

Installation
============
You can use `pip <https://pypi.org/project/pip/>`_ to install PyAdditive.

.. code:: bash

    pip install ansys-additive-core

To install the latest development version, run these commands:

.. code:: bash

   git clone https://github.com/ansys/pyadditive
   cd pyadditive
   pip install -e .

For more information, see `Getting Started`_.

Basic usage
===========

This code shows how to import PyAdditive and use some basic capabilities:

.. code:: python

   import ansys.additive.core as pyadditive

   additive = pyadditive.Additive()

   input = pyadditive.SingleBeadInput(
       machine=pyadditive.AdditiveMachine(),
       material=additive.material("Ti64"),
       id="bead1",
       bead_length=0.001,  # meters
   )

   summary = additive.simulate(input)

For comprehensive usage information, see `Examples`_ in the `PyAdditive Documentation`_.

Documentation and issues
========================
Documentation for the latest stable release of PyAdditive is hosted at `PyAdditive documentation`_.

In the upper right corner of the documentation's title bar, there is an option for switching from
viewing the documentation for the latest stable release to viewing the documentation for the
development version or previously released versions.

On the `PyAdditive Issues <https://github.com/ansys/pyadditive/issues>`_ page,
you can create issues to report bugs and request new features. On the `PyAdditive Discussions
<https://github.com/ansys/pyadditive/discussions>`_ page or the `Discussions <https://discuss.ansys.com/>`_
page on the Ansys Developer portal, you can post questions, share ideas, and get community feedback.

To reach the project support team, email `pyansys.core@ansys.com <mailto:pyansys.core@ansys.com>`_.


.. LINKS AND REFERENCES
.. _Ansys Additive: https://www.ansys.com/products/additive
.. _Getting Started: https://additive.docs.pyansys.com/version/stable/getting_started/index.html
.. _Examples: https://additive.docs.pyansys.com/version/stable/examples/gallery_examples/index.html
.. _PyAdditive documentation: https://additive.docs.pyansys.com/version/stable/index.html
