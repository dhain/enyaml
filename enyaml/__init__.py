import yaml
from functools import partial
from .util import *
from .nodes import *
from .loader import *
from .dumper import *


scan = partial(yaml.scan, Loader=TemplateLoader)
parse = partial(yaml.parse, Loader=TemplateLoader)
compose = partial(yaml.compose, Loader=TemplateLoader)
compose_all = partial(yaml.compose_all, Loader=TemplateLoader)
load = partial(yaml.load, Loader=TemplateLoader)
load_all = partial(yaml.load_all, Loader=TemplateLoader)

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


def render(stream, ctx, Loader=TemplateLoader):
    loader = Loader(stream)
    try:
        return loader.render_single_data(ctx)
    finally:
        loader.dispose()


def render_all(stream, ctx, Loader=TemplateLoader):
    loader = Loader(stream)
    try:
        while loader.check_data():
            yield loader.render_data(ctx)
    finally:
        loader.dispose()


class YAMLObject(yaml.YAMLObject):
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper
