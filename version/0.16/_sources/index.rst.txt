..
   Just reuse the root readme to avoid duplicating the documentation.
   Provide any documentation specific to your online documentation
   here.

.. vale off

PyAdditive documentation  |version|
===================================

.. include:: ../../README.rst
   :start-after: .. readme_start

.. jinja:: main_toctree

    .. toctree::
       :hidden:
       :maxdepth: 2

       getting_started/index
       {% if build_api %}
       api/index
       {% endif %}
       {% if build_examples %}
       examples/gallery_examples/index
       {% endif %}

.. vale on
