.. _ref_contribute:

##########
Contribute
##########

Overall guidance on contributing to a PyAnsys library appears in the
`Contributing <https://dev.docs.pyansys.com/how-to/contributing.html>`_ topic
in the *PyAnsys developer's guide*. Ensure that you are thoroughly familiar
with this guide before attempting to contribute to PyAdditive.

Configure your development environment
--------------------------------------

For instructions on setting up your development environment, see
:ref:`ref_getting_started`, particularly the :ref:`ref_install_in_developer_mode`
section.

Post issues
-----------

Use the `PyAdditive Issues <https://github.com/ansys/pyadditive/issues>`_
page to submit questions, report bugs, and request new features. When possible, you
should use these issue templates:

* Bug, problem, error: For filing a bug report
* Documentation error: For requesting modifications to the documentation
* Adding an example: For proposing a new example
* New feature: For requesting enhancements to the code

If your issue does not fit into one of these template categories, you can click
the link for opening a blank issue.

To reach the project support team, email `pyansys.core@ansys.com <pyansys.core@ansys.com>`_.

View documentation
------------------

Documentation for the latest stable release of PyAdditive is hosted at
`PyAdditive Documentation <https://additive.docs.pyansys.com>`_.

In the upper right corner of the documentation's title bar, there is an option
for switching from viewing the documentation for the latest stable release
to viewing the documentation for the development version or previously
released versions.

Adhere to code style
--------------------

PyAdditive follows the PEP8 standard as outlined in
`PEP 8 <https://dev.docs.pyansys.com/coding-style/pep8.html>`_ in
the `PyAnsys Developer's Guide <https://dev.docs.pyansys.com/>`_
and implements style checking using `pre-commit <https://pre-commit.com/>`_.

To ensure your code meets minimum code styling standards, run these commands::

  pip install pre-commit
  pre-commit run --all-files

You can also install this as a `git` pre-commit hook by running this command::

  pre-commit install

This way, it's not possible for you to push code that fails the style checks::

  $ pre-commit install
  $ git commit -am "added my cool feature"
  ruff.....................................................................Passed
  ruff-format..............................................................Passed
  codespell................................................................Passed
  check for merge conflicts................................................Passed
  debug statements (python)................................................Passed
  check yaml...............................................................Passed
  Validate GitHub Workflows................................................Passed
  interrogate..............................................................Passed
  uncomment-coverage-options...............................................Passed