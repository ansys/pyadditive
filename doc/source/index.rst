PyAdditive documentation  |version|
###################################

PyAdditive provides a Python API to interact with the Ansys Additive server.
The Additive server is included in the Additive option of the Structures package
of the Ansys release.


.. grid:: 2

    .. grid-item-card:: Getting started :fa:`person-running`
        :link: ref_getting_started
        :link-type: ref

        Step-by-step guidelines on how to set up your environment to work with
        PyAdditive.

    .. grid-item-card:: User guide :fa:`book-open-reader`
        :link: user-guide
        :link-type: doc

        Learn about the capabilities, features, and key topics in PyAdditive.
        This guide provides useful background information and explanations.

.. jinja:: main_toctree

    {% if build_api or build_examples %}
    .. grid:: 2

       {% if build_api %}
       .. grid-item-card:: API reference :fa:`book-bookmark`
           :link: api/index
           :link-type: doc

           A detailed guide describing the PyAdditive API. This guide documents
           all the methods and properties for each interface, class, and
           enumerations of each PyAdditive module.
        {% endif %}

       {% if build_examples %}
       .. grid-item-card:: Gallery of examples :fa:`laptop-code`
           :link: examples/gallery_examples/index
           :link-type: doc

           Learn how to use PyAdditive for creating custom applications and
           automating your existing Additive workflows. This guide contains a
           gallery of examples showing how to integrate PyAdditive with other
           popular tools in the Python ecosystem.
        {% endif %}
    {% endif %}

.. jinja:: main_toctree

    .. toctree::
       :hidden:
       :maxdepth: 2

       getting-started/index
       {% if build_api %}
       api/index
       {% endif %}
       {% if build_examples %}
       examples/gallery_examples/index
       {% endif %}
       contributing
