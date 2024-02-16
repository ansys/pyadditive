# Changelog

## PyAdditive 0.17.2

### Doc Improvements
* Use print statement for material list in examples [#269](https://github.com/ansys/pyadditive/issues/269)
* Fixed truncation problem on summary doc strings [#271](https://github.com/ansys/pyadditive/pull/271)

### Contributors
* Peter Krull - <peter.krull@ansys.com>
* Julie O'Hara - <julie.ohara@ansys.com>

## PyAdditive 0.17.1

### Doc Improvements
* Add license warning to Getting started page [#262](https://github.com/ansys/pyadditive/issues/262)

### Contributors
* Peter Krull - <peter.krull@ansys.com>

## PyAdditive 0.17.0

### Breaking Changes

* The parameter `material_parameters_file` of `MaterialTuningInput` class has been changed to  `material_configuration_file`.
* The `Additive` class `__init__` method no longer has a `channel` parameter.

### New Features

* Add heatmap for porosity results of parametric study @ABDULKHADERKHAN in [#185](https://github.com/ansys/pyadditive/pull/185)
* Add number of simulations per server parameter to `Additive` class @pkrull-ansys in [#177](https://github.com/ansys/pyadditive/pull/177)
* Add product version parameter to `Additive` class  @pkrull-ansys in [#170](https://github.com/ansys/pyadditive/pull/170)

### Doc Improvements
* Several grammar and link corrections @pkrull-ansys in [#158](https://github.com/ansys/pyadditive/pull/158), [#160](https://github.com/ansys/pyadditive/pull/160)[#164](https://github.com/ansys/pyadditive/pull/164), [#184](https://github.com/ansys/pyadditive/pull/184)

### Contributors

* Peter Krull - <peter.krull@ansys.com>
* Abdul Khader Khan - <abdulkhader.khan@ansys.com>
* Kathy Pippert - <kathy.pippert@ansys.com>
* Julie O'Hara - <julie.ohara@ansys.com>

## PyAdditive 0.16.0

### Breaking Changes

* The `get_materials_list()` and `get_material()` methods of the `Additive` class have been renamed to [`materials_list()`](https://additive.docs.pyansys.com/version/stable/api/ansys/additive/core/additive/index.html#additive.materials_list) and
[`material()`](https://additive.docs.pyansys.com/version/stable/api/ansys/additive/core/additive/index.html#additive.material).

### New Features

* Use a heatmap instead of a contour plot for single bead evaluation plot by @pkrull-ansys in [#126](https://github.com/ansys/pyadditive/pull/126).
* Allow multiple additive server connections by @pkrull-ansys in [#143](https://github.com/ansys/pyadditive/pull/143).

### Bug Fixes

* Read parametric study files created on an alternate OS by @pkrull-ansys in [#128](https://github.com/ansys/pyadditive/pull/128).
* Make connecting to the server more robust by @pkrull-ansys in [#133](https://github.com/ansys/pyadditive/pull/133).

### Doc Improvements
* Update docs and build pipeline for public release by @pkrull-ansys in [#136](https://github.com/ansys/pyadditive/pull/136).

### Contributors

* Peter Krull - <peter.krull@ansys.com>

## PyAdditive 0.15.0, 2023-10-09

### New Features

* PyAdditive uses new server name when starting server locally [#105](https://github.com/ansys/pyadditive/issues/105).
* Dropped support for Python 3.8 and added support for Python 3.12 [#106](https://github.com/ansys/pyadditive/issues/106).

### Bug Fixes

* PyAdditive client can connect to server using server name rather than IPv4 address [#10](https://github.com/ansys/pyadditive/issues/10).

### Doc improvements

* Added interrogate to pre-commit checks [#48](https://github.com/ansys/pyadditive/issues/48).

### Contributors

* Peter Krull - <peter.krull@ansys.com>

## PyAdditive 0.14.0, 2023-08-08

### New features

* Microstructure circle equivalence data now returned as Pandas DataFrame [#2](https://github.com/ansys/pyadditive/issues/2).
* Added ParametricStudy [#2](https://github.com/ansys/pyadditive/issues/2).

### Doc improvements

* Added link checks during doc builds [#19](https://github.com/ansys/pyadditive/pull/19)

### Contributors

* Peter Krull - <peter.krull@ansys.com>

## PyAdditive 0.13.0, 2023-07-17

### New features

* Added about endpoint, [#17](https://github.com/ansys/pyadditive/pull/17)

### Doc improvements

* Added required project files, [#13](https://github.com/ansys/pyadditive/issues/13)

### Contributors

* Peter Krull - <peter.krull@ansys.com>

<!-- markdownlint-configure-file { "MD022": false, "MD024": false, "MD030": false, "MD032": false} -->