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
from .util import *     # noqa: F403
from .nodes import *    # noqa: F403
from .loader import *   # noqa: F403
from .dumper import *   # noqa: F403


def render(stream, ctx, Loader=TemplateLoader):  # noqa: F405
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


def render_all(stream, ctx, Loader=TemplateLoader):  # noqa: F405
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


load = partial(yaml.load, Loader=TemplateLoader)  # noqa: F405
load_all = partial(yaml.load_all, Loader=TemplateLoader)  # noqa: F405
scan = partial(yaml.scan, Loader=TemplateLoader)  # noqa: F405
parse = partial(yaml.parse, Loader=TemplateLoader)  # noqa: F405
compose = partial(yaml.compose, Loader=TemplateLoader)  # noqa: F405

compose_all = partial(yaml.compose_all, Loader=TemplateLoader)  # noqa: F405

emit = partial(yaml.emit, Dumper=TemplateDumper)  # noqa: F405
serialize = partial(yaml.serialize, Dumper=TemplateDumper)  # noqa: F405
serialize_all = partial(
    yaml.serialize_all, Dumper=TemplateDumper)  # noqa: F405
dump = partial(yaml.dump, Dumper=TemplateDumper)  # noqa: F405
dump_all = partial(yaml.dump_all, Dumper=TemplateDumper)  # noqa: F405

add_implicit_resolver = partial(
    yaml.add_implicit_resolver,
    Loader=TemplateLoader, Dumper=TemplateDumper  # noqa: F405
)
add_path_resolver = partial(
    yaml.add_path_resolver,
    Loader=TemplateLoader, Dumper=TemplateDumper  # noqa: F405
)

add_constructor = partial(
    yaml.add_constructor, Loader=TemplateLoader)  # noqa: F405
add_multi_constructor = partial(
    yaml.add_multi_constructor, Loader=TemplateLoader)  # noqa: F405

add_representer = partial(
    yaml.add_representer, Dumper=TemplateDumper)  # noqa: F405
add_multi_representer = partial(
    yaml.add_multi_representer, Dumper=TemplateDumper)  # noqa: F405


class YAMLObject(yaml.YAMLObject):
    yaml_loader = TemplateLoader  # noqa: F405
    yaml_dumper = TemplateDumper  # noqa: F405
