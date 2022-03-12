.. ENYAML documentation master file, created by
   sphinx-quickstart on Sat Mar 12 12:28:42 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ENYAML's documentation!
==================================

**ENYAML** is Evaluation Notation YAML.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


A Note On Building Documentation
================================

After cloning the ENYAML repository, and before you build documentation using
``make html`` from the ``docs/`` directory, it is recommended to add a git
worktree for the ``gh-pages`` branch::

  $ git clone https://github.com/dhain/enyaml.git
  $ cd enyaml
  $ git worktree add docs/build/html gh-pages
  $ cd docs
  $ make html
  $ cd build/html
  $ git status

This way, the Sphinx output can be directly committed to the ``gh-pages``
branch.
