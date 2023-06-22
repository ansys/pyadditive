..
   Just reuse the root readme to avoid duplicating the documentation.
   Provide any documentation specific to your online documentation
   here.

.. include:: ../../README.rst

.. jinja:: main_toctree

    .. toctree::
       :hidden:
       :maxdepth: 2
    
       getting_started/index
       {% if build_api %}
       api/index
       {% endif %}
       {% if build_examples %}
       examples/index
       {% endif %} 
       contributing
