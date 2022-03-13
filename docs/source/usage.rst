Usage
=====

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

.. code-block:: yaml

   foo: bar
   mygreeting: Hello, Guido!


Rendering Within Python
-----------------------

.. testsetup::

   import os
   os.chdir('source/_static')

.. doctest::

   >>> import enyaml

   >>> ctx = enyaml.Context()
   >>> enyaml.render(open('helloworld.yaml'), ctx)
   {'foo': 'bar', 'mygreeting': 'Hello, Guido!'}
