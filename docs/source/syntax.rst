Template Syntax
===============

ENYAML templates are simply YAML documents. Control structures are marked up
using YAML tags.

.. note::

   The fully qualified tags begin with ``tag:enyaml.org,2022:``, and can be
   aliased using the ``%TAG`` directive in your YAML documents. This can
   usually be omitted, however, because the :class:`.TemplateLoader` class
   aliases this prefix to ``!`` by default.


A Simple Example
----------------

The following is a simple example template that uses the :tmpl:tag:`$` tag to
evaluate an expression:

.. tmpl:render::
   :show-template: When rendered, this template outputs:

   !$ 1 + 1


The Context
-----------

Templates are rendered with a :class:`.Context`. The Context is a mapping of
variable names to values. This allows you to provide variables to the template
for rendering, and allows templates to read and set variables during rendering.


.. tmpl:tag:: set setting-context-variables

Setting Context Variables
-------------------------

You can set Context variables by defining a YAML mapping with the
:tmpl:tag:`set` tag. These mapping nodes will not appear in the rendered output
of the template. If a set node appears within a sequence or mapping, that item
will be removed. The variables will be updated as this node is processed, so
generally, expressions accessing these variables *after* the set node in the
source template will see the updated values. For example:

.. tmpl:render::
   :show-template: Will render as:

   - !set
     foo: 1
   - !$ foo
   - !set
     foo: 2
   - !$ foo

Context variables persist across documents in a given template file. For example:

.. tmpl:render::
   :show-template: Will render as:

   ---
   !set
   foo: 1

   ---
   - !$ foo


.. tmpl:tag:: $ expressions

Expressions
-----------

As seen above, you can access Context variables using expression nodes.
Expression nodes are represented by the :tmpl:tag:`$` tag, and are replaced by
the value of the expression.


.. tmpl:tag:: $f format-string-expressions

Format String Expressions
-------------------------

Format string nodes are represented by the :tmpl:tag:`$f` tag.


.. tmpl:tag:: for loops

Loops
-----

Loops are made by the :tmpl:tag:`for` tag.


.. tmpl:tag:: if conditionals

Conditionals
------------

Conditionals are made by the :tmpl:tag:`if` tag.
