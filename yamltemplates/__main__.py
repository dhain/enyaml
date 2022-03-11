import sys
import yaml
from . import *


class MySeq(yaml.YAMLObject):
    yaml_tag = 'tag:something,2022:myseq'
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper

    @classmethod
    def from_yaml(cls, loader, node):
        return cls([loader.construct_object(item) for item in node.value])

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_sequence(cls.yaml_tag, data.value)

    def __init__(self, value):
        self.value = value


ctx = Context()
loader = TemplateLoader(open(sys.argv[1]))
yaml.dump_all(loader.render_all(ctx), sys.stdout, Dumper=TemplateDumper)
