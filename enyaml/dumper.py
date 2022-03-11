__all__ = [
    'TemplateDumper',
]

import yaml
from . import nodes


class TemplateDumper(yaml.SafeDumper):
    DEFAULT_TAG_PREFIXES = yaml.SafeDumper.DEFAULT_TAG_PREFIXES.copy()
    DEFAULT_TAG_PREFIXES[nodes.TAG_PREFIX] = '!'

    def choose_scalar_style(self):
        style = super().choose_scalar_style()
        if (
            self.event.tag.startswith(nodes.TAG_PREFIX) and
            not self.event.style and
            (not (self.simple_key_context and
                    (self.analysis.empty or self.analysis.multiline))
                and (self.flow_level and self.analysis.allow_flow_plain
                    or (not self.flow_level and self.analysis.allow_block_plain)))
        ):
            return ''
        return style

    def prepare_tag(self, tag):
        basetag, subtag, skip_render = nodes.split_tag(tag)
        if subtag:
            subtag = super().prepare_tag(subtag)
            tag = nodes.unsplit_tag(basetag, subtag, skip_render)
        elif basetag == nodes.BaseTemplateNode.basetag and not skip_render:
            return ''
        return super().prepare_tag(tag)


for name in nodes.__all__:
    obj = getattr(nodes, name)
    if hasattr(obj, 'to_yaml'):
        TemplateDumper.add_representer(obj, obj.to_yaml)
