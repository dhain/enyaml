Getting Started
===============

Installation
------------

.. code-block:: sh

   python3 -m pip install enyaml


Writing a Simple Template
-------------------------

Here is a simple example template. Save this file to ``helloworld.yaml`` to run
the example code below.

.. literalinclude:: _static/helloworld.yaml
   :language: yaml
   :linenos:


Rendering a Template
--------------------

To render the template, simply run ``enyaml`` with the filename as the
argument:

.. code-block:: sh

   enyaml helloworld.yaml

The following output should be produced:

.. tmpl:render::
   :filename: _static/helloworld.yaml


Rendering Within Python
-----------------------

.. testsetup::

   filename = 'source/_static/helloworld.yaml'

.. doctest::

   >>> import enyaml

   >>> ctx = enyaml.Context()
   >>> enyaml.render(open(filename), ctx)   # filename = 'helloworld.yaml'
   {'foo': 'bar', 'mygreeting': 'Hello, Guido!'}


Next Steps
----------

Once you have ENYAML installed, you can get started writing templates. See
:doc:`syntax` to learn how.
