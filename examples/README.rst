.. _ref_example_gallery:

========
Examples
========
End-to-end examples show how you can use PyAdditve. You can download
these examples as Python files or Jupyter notebooks and run them locally.


.. jinja:: examples_toctree

    .. toctree::
       :maxdepth: 1
       :hidden:

       00_additive_single_bead.py
       01_additive_porosity.py
       02_additive_microstructure.py
       03_additive_thermal_history.py
       04_additive_doe.py
       05_optimization_workflow.py
       {% if build_examples_long %}
       06_additive_custom_material_tuning.py
       07_using_a_custom_material.py
       {% endif%}
