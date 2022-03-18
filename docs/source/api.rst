API
===

ENYAML is Evaluation Notation YAML.

It is implemented on top of the PyYAML module, using the
:class:`.TemplateLoader` and :class:`.TemplateDumper` classes, and a handful of
:mod:`Node <enyaml.nodes>` subclasses.

.. contents:: Contents
   :local:
   :backlinks: none

High-Level API
--------------

.. automodule:: enyaml
   :members: render, render_all
   :show-inheritance:

Context
-------

.. automodule:: enyaml.util
   :members:
   :show-inheritance:

Loader
------

.. automodule:: enyaml.loader
   :members:
   :show-inheritance:

Dumper
------

.. automodule:: enyaml.dumper
   :members:
   :show-inheritance:

Node Representation
-------------------

.. automodule:: enyaml.nodes
   :members:
   :show-inheritance:

