ENYAML: Evaluation Notation YAML
================================

Basically, it's a templating language for YAML documents.

Here's a simple example:

.. code-block:: yaml
   :linenos:

    _: !set
      name: Guido
    salutation: !$f "Hello, {name}!"

When rendered, the resulting YAML document would look like this:

.. code-block:: yaml
   :linenos:

    salutation: Hello, Guido!

Traditional approaches to templating YAML, eg. jinja+yaml from the saltstack
world, are just text-based templates that produce (hopefully valid) YAML
output.  ENYAML's approach is to use valid YAML as input, then render the
document structure directly as native objects. You can then consume the data
directly, or dump it back out to YAML, which is guaranteed to be valid.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   syntax
   api
   LICENSE


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
