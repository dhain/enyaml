# Copyright (c) 2022, Sadie Hain. All rights reserved.
# Released under the BSD 3-Clause License
# https://enyaml.org/LICENSE

"""
The ENYAML high-level API is the same as that of the :mod:`yaml` module. The
top-level functions are wrappers around the functions from that module, which
pass :class:`.TemplateLoader` and :class:`.TemplateDumper` as the default
``Loader`` and ``Dumper`` arguments. A subclass of :class:`yaml.YAMLObject` is
also provided for convenience.

Additionally, two new high-level functions are provided for rendering ENYAML
templates.
"""

__version__ = '0.1'

import yaml
from functools import partial
from .util import *
from .nodes import *
from .loader import *
from .dumper import *


def render(stream, ctx, Loader=TemplateLoader):
    """Load and render a single-document template.

    :param file-like stream: The stream to read the template from.
    :param Context ctx: A Context instance.
    :param Loader: The loader class to instantiate.
    :return: The rendered data.

    .. note::

       The input YAML can have multiple documents, as long as only the last one
       produces output when rendered. For example, the following counts as a
       single-document template:

       .. code-block:: yaml

          ---
          !set
          name: Guido
          ---
          salutation: !$f "Hello, {name}"
    """
    loader = Loader(stream)
    try:
        return loader.render_single_data(ctx)
    finally:
        loader.dispose()


def render_all(stream, ctx, Loader=TemplateLoader):
    """Load and render a stream of template documents.

    :param file-like stream: The stream to read the templates from.
    :param Context ctx: A Context instance.
    :param Loader: The loader class to instantiate.
    :return: An iterable containing rendered data.

    Only documents which produce output when rendered will be included in the
    result.
    """
    loader = Loader(stream)
    try:
        while loader.check_data():
            yield loader.render_data(ctx)
    finally:
        loader.dispose()


load = partial(yaml.load, Loader=TemplateLoader)
load_all = partial(yaml.load_all, Loader=TemplateLoader)
scan = partial(yaml.scan, Loader=TemplateLoader)
parse = partial(yaml.parse, Loader=TemplateLoader)
compose = partial(yaml.compose, Loader=TemplateLoader)

compose_all = partial(yaml.compose_all, Loader=TemplateLoader)

emit = partial(yaml.emit, Dumper=TemplateDumper)
serialize = partial(yaml.serialize, Dumper=TemplateDumper)
serialize_all = partial(yaml.serialize_all, Dumper=TemplateDumper)
dump = partial(yaml.dump, Dumper=TemplateDumper)
dump_all = partial(yaml.dump_all, Dumper=TemplateDumper)

add_implicit_resolver = partial(
    yaml.add_implicit_resolver, Loader=TemplateLoader, Dumper=TemplateDumper)
add_path_resolver = partial(
    yaml.add_path_resolver, Loader=TemplateLoader, Dumper=TemplateDumper)

add_constructor = partial(yaml.add_constructor, Loader=TemplateLoader)
add_multi_constructor = partial(yaml.add_multi_constructor, Loader=TemplateLoader)

add_representer = partial(yaml.add_representer, Dumper=TemplateDumper)
add_multi_representer = partial(yaml.add_multi_representer, Dumper=TemplateDumper)


class YAMLObject(yaml.YAMLObject):
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper
