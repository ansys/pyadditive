# Changelog

## PyAdditive 0.20.0

### New Features

* Simulation logs are included in the simulation summary.
* Added support for Python 3.13.

### Bug Fixes

* Return `False` from `Additive.connected()` if the `_server` attribute is `None`
* Assign id to simulations imported into a parametric study if the value is missing.

### Doc Improvements

### Contributors

* pkrull-ansys
* safeerehman
* deleon117

# PyAdditive 0.19.0

## Breaking Changes

* Removed support for multiple server connections. Specifically, the `nservers` parameter was removed from `Additive()` and the `server_connections` parameter was renamed to `channel`.
* Simulation inputs no longer allow setting the `id` field. It is generated automatically.
* Removed `nsims_per_server` property from the `Additive `class.
* `ParametricStudy.set_status()` and `ParametricStudy.reset_status()` have been renamed to `ParametricStudy.set_simulation_status()` and `ParametricStudy.reset_simulation_status()`.
* `ParametricStudy()` now requires a material name parameter. As a consequence, the `material_name` parameter has been removed from `ParametricStudy.generate_single_bead_permutations()`, `ParametricStudy.generate_porosity_permutations()`, and `ParametricStudy.generate_microstructure_permutations()`. The parametric study `FORMAT_VERSION` value has been incremented to 3.
* The `ParametricRunner` class has been removed. To run a parametric study, use `Additive.simulate_study()` or `Additive.simulate_study_async()`.
* The `ParametricStudy.generate_single_bead_permutations()` will now accept minimum and maximum p/v ratios as constraints instead of minimum and maximum area energy densities.
* Thermal history simulations require the `enable_beta_features` flag to be set to `True` when instantiating an `Additive` object.

## New Features

* Default version of Additive Server is 25.1 when creating a client connection.
* Single bead simulations with thermal history are now supported.
* Added description field to `AdditiveMaterial`.
* Added support for running simulations asynchronously.
* Added support to list and apply server settings.
* Parametric study data is updated while simulations are running.
* Added global `LOG` for logging in Additive object.
* Added P/V Ratio (Laser Power / Laser Scan Speed) column to the parametric study.
* Added `connected` property to `Additive` to indicate if the client is connected to a server.

## Bug Fixes
* Fixed import of microstructure simulations in csv file when random seed is undefined.

## Doc Improvements
* Updated the single bead example to show usage with the thermal history option.

## Contributors
* pkrull-ansys
* safeerehman
* julieatansys
* jorgepiloto

### New Contributors
* @AdvaitChandorkar07 made their first contribution in https://github.com/ansys/pyadditive/pull/416


## PyAdditive 0.18.0

### Breaking Changes
* Removed the `save_file_name` parameter from `ParametricStudy.load()`. [#302](https://github.com/ansys/pyadditive/pull/302)
* Removed the `display` module from `ansys.additive.core.parametric_study` as part of [#194](https://github.com/ansys/pyadditive/issues/194)

### New Features
* Added ability to import a csv file containing a parametric study [#118](https://github.com/ansys/pyadditive/issues/118)
* Added separate logging class [#163](https://github.com/ansys/pyadditive/issues/163)
* Updated parametric study to check for duplicate entries [#228](https://github.com/ansys/pyadditive/issues/228)
* Added 3D microstructure (BETA) simulations [#276](https://github.com/ansys/pyadditive/issues/276)
* Increased max random seed limit for microstructure simulations [#325](https://github.com/ansys/pyadditive/pull/325/files)
* Added a progress handler parameter to simulation functions [#315] (https://github.com/ansys/pyadditive/pull/315/files)

### Bug Fixes
* Removed side effect from `ParametricStudy.save()` which changed the study file path if the `file_name` parameter differed from the `ParameticStudy.file_name` property. Also removed the `save_file_name` parameter from `ParametricStudy.load()`. [#301](https://github.com/ansys/pyadditive/issues/301)
* Fixed handling of material CSV files with alternative language settings (additiveserver) [#261](https://github.com/ansys/pyadditive/issues/261)
* Duplicate simulations will be dropped from a parametric study [#290](https://github.com/ansys/pyadditive/issues/290)
* Added Ansys installation path for linux to Additive object initializer. [#308](https://github.com/ansys/pyadditive/issues/308)
* CSV files with empty thermal parameters of a microstructure simulation will be imported [#309](https://github.com/ansys/pyadditive/issues/309)
* Gracefully return from run_simulations when no simulations meet criteria [#318](https://github.com/ansys/pyadditive/pull/318)
* Fixed simulation results being updated for incorrect simulations in parametric studies. [#364] (https://github.com/ansys/pyadditive/issues/364)

### Doc Improvements
* Updated parametric study examples to show importing a study from a csv file in [#259](https://github.com/ansys/pyadditive/pull/259/)
* Fixed truncation problem on summary doc strings (material and single-bead API docs) [#271](https://github.com/ansys/pyadditive/pull/271)
* Added license warning to Getting started page [#262](https://github.com/ansys/pyadditive/issues/262)
* Edited introductory sentences in examples [#275](https://github.com/ansys/pyadditive/pull/275)

### Contributors
* pkrull-ansys
* safeerehman
* julieatansys

## PyAdditive 0.17.2

### Doc Improvements
* Use print statement for material list in examples [#269](https://github.com/ansys/pyadditive/issues/269)

### Contributors
* pkrull-ansys

## PyAdditive 0.17.1

### Doc Improvements
* Add license warning to Getting started page [#262](https://github.com/ansys/pyadditive/issues/262)

### Contributors
* pkrull-ansys

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

* pkrull-ansys
* ABDULKHADERKHAN
* PipKat
* julieatansys

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

* pkrull-ansys

## PyAdditive 0.15.0, 2023-10-09

### New Features

* PyAdditive uses new server name when starting server locally [#105](https://github.com/ansys/pyadditive/issues/105).
* Dropped support for Python 3.8 and added support for Python 3.12 [#106](https://github.com/ansys/pyadditive/issues/106).

### Bug Fixes

* PyAdditive client can connect to server using server name rather than IPv4 address [#10](https://github.com/ansys/pyadditive/issues/10).

### Doc improvements

* Added interrogate to pre-commit checks [#48](https://github.com/ansys/pyadditive/issues/48).

### Contributors

* pkrull-ansys


## PyAdditive 0.14.0, 2023-08-08

### New features

* Microstructure circle equivalence data now returned as Pandas DataFrame [#2](https://github.com/ansys/pyadditive/issues/2).
* Added ParametricStudy [#2](https://github.com/ansys/pyadditive/issues/2).

### Doc improvements

* Added link checks during doc builds [#19](https://github.com/ansys/pyadditive/pull/19)

### Contributors

* pkrull-ansys

## PyAdditive 0.13.0, 2023-07-17

<!-- ### Bugs fixed

* Brief description of the bug. Link to the associated issue and pull request -->

### New features

* Added about endpoint, [#17](https://github.com/ansys/pyadditive/pull/17)

### Doc improvements

* Added required project files, [#13](https://github.com/ansys/pyadditive/issues/13)

### Contributors

* pkrull-ansys
