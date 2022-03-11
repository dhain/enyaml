__all__ = [
    'TemplateLoader',
]

import re
import yaml
from yaml.composer import ComposerError
from . import nodes


TAG_RX = re.compile(r'(!(?:[^!]*!)?)?(.*)$')


class TemplateLoader(yaml.SafeLoader):
    TMPL_MAP = {}
    DEFAULT_TAGS = yaml.SafeLoader.DEFAULT_TAGS.copy()
    DEFAULT_TAGS['!'] = nodes.TMPL_PREFIX

    def render_data(self, ctx):
        while self.check_node():
            node = self.get_node()
            if hasattr(node, 'render'):
                node = node.render(self, ctx)
            if node:
                return self.construct_document(node)

    def render_single_data(self, ctx):
        node = None
        while self.check_node():
            node = self.get_node().render(self, ctx)
            if node:
                break
        if self.check_node():
            event = self.get_event()
            raise ComposerError(
                'expected a single document', node.start_mark,
                'but found another document', event.start_mark
            )
        return node

    def render_all(self, ctx):
        while self.check_data():
            yield self.render_data(ctx)

    def construct_object(self, node, deep=False):
        if getattr(node, 'skip_render', False):
            return node
        return super().construct_object(node, deep)

    def parse_node(self, block=False, indentless_sequence=False):
        event = super().parse_node(block, indentless_sequence)
        if isinstance(event, yaml.ScalarEvent) and (
            event.tag is None or
            not event.tag.startswith(nodes.TMPL_PREFIX)
        ):
            return event
        if event.tag is None:
            event.tag = f'{nodes.TMPL_PREFIX}tmpl'
        elif not event.tag.startswith(nodes.TMPL_PREFIX):
            event.tag = f'{nodes.TMPL_PREFIX}tmpl:{event.tag}'
        event.basetag, event.subtag = nodes.split_tag(event.tag)
        if event.subtag:
            m = TAG_RX.match(event.subtag)
            if m:
                handle, suffix = m.groups()
                if handle:
                    event.subtag = self.tag_handles[handle]+suffix
                    event.tag = f'{nodes.TMPL_PREFIX}{event.basetag}:{event.subtag}'
        return event

    def compose_node(self, parent, index):
        event = self.peek_event()
        node = super().compose_node(parent, index)
        if not hasattr(event, 'basetag'):
            return node
        tag = event.basetag
        subtag = event.subtag
        if tag.endswith('~'):
            skip_render = True
            tag = tag[:-1]
        else:
            skip_render = False
        for cls in type(node).__mro__:
            try:
                node.__class__ = self.TMPL_MAP[tag, cls]
            except KeyError:
                continue
            break
        node.subtag = subtag
        node.skip_render = skip_render
        return node


for name in nodes.__all__:
    obj = getattr(nodes, name)
    if hasattr(obj, 'tmpl_tag') and hasattr(obj, 'node_type'):
        TemplateLoader.TMPL_MAP[obj.tmpl_tag, obj.node_type] = obj
