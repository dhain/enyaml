A Note On Building Documentation
================================

After cloning the ENYAML repository, and before you build documentation using
``make html`` from the ``docs/`` directory, it is recommended to add a git
worktree for the ``gh-pages`` branch:

.. code-block:: sh

  $ git clone https://github.com/dhain/enyaml.git
  $ cd enyaml
  $ git worktree add docs/build/html gh-pages
  $ cd docs
  $ make html
  $ cd build/html
  $ git status

This way, the Sphinx output can be directly committed to the ``gh-pages``
branch.

