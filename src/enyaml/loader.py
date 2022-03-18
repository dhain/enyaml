# Copyright (c) 2022, Sadie Hain. All rights reserved.
# Released under the BSD 3-Clause License
# https://enyaml.org/LICENSE

__all__ = [
    'TemplateLoader',
]

import re
import yaml
from yaml.composer import ComposerError
from . import nodes


TAG_RX = re.compile(r'(!(?:[0-9a-zA-Z-_]*!)?)?(.*)$')


class TemplateLoader(yaml.SafeLoader):
    """Loads and renders ENYAML templates.

    :param file-like stream: The stream to read the templates from.
    """
    TAG_MAP = {}
    DEFAULT_TAGS = yaml.SafeLoader.DEFAULT_TAGS.copy()
    DEFAULT_TAGS['!'] = nodes.TAG_PREFIX

    def _render_next_node(self, ctx):
        while self.check_node():
            node = self.get_node()
            if hasattr(node, 'render'):
                node = node.render(self, ctx)
            if node:
                return node

    def render_data(self, ctx):
        """Renders the next document in the stream.

        :param Context ctx: The Context with which to render.
        :return: Rendered result.
        """
        node = self._render_next_node(ctx)
        if node:
            return self.construct_document(node)

    def render_single_data(self, ctx):
        """Renders a single document stream.

        :param Context ctx: The Context with which to render.
        :return: Rendered result.
        :raises yaml.composer.ComposerError: when there are more than one
           document in the stream which produce output when rendered, or the
           document which produces output is not the last document in the
           stream.
        """
        node = self._render_next_node(ctx)
        if self.check_node():
            event = self.get_event()
            raise ComposerError(
                'expected a single document in the stream', node.start_mark,
                'but found another document', event.start_mark
            )
        if node:
            return self.construct_document(node)

    def _strip_tmpl_tags(self, node):
        if hasattr(node, 'subtag'):
            node.tag = node.subtag or self.resolve(
                node.node_type, node.value, (True, False))

    def get_data(self):
        if self.check_node():
            node = self.get_node()
            self._strip_tmpl_tags(node)
            return self.construct_document(node)

    def get_single_data(self):
        node = self.get_single_node()
        if node is not None:
            self._strip_tmpl_tags(node)
            return self.construct_document(node)
        return None

    def construct_object(self, node, deep=False):
        if getattr(node, 'skip_render', False):
            return node
        return super().construct_object(node, deep)

    def parse_node(self, block=False, indentless_sequence=False):
        event = super().parse_node(block, indentless_sequence)
        if isinstance(event, yaml.ScalarEvent) and (
            event.tag is None or
            not event.tag.startswith(nodes.TAG_PREFIX)
        ):
            return event
        if event.tag is None:
            event.tag = f'{nodes.TAG_PREFIX}tmpl'
        elif not event.tag.startswith(nodes.TAG_PREFIX):
            event.tag = f'{nodes.TAG_PREFIX}tmpl:{event.tag}'
        event.basetag, event.subtag, event.skip_render = nodes.split_tag(event.tag)
        if event.subtag:
            m = TAG_RX.match(event.subtag)
            if m:
                handle, suffix = m.groups()
                if handle:
                    event.subtag = self.tag_handles[handle]+suffix
                    event.tag = nodes.unsplit_tag(
                        event.basetag, event.subtag, event.skip_render)
        return event

    def compose_node(self, parent, index):
        event = self.peek_event()
        node = super().compose_node(parent, index)
        if not hasattr(event, 'basetag'):
            return node
        for cls in type(node).__mro__:
            try:
                node.__class__ = self.TAG_MAP[event.basetag, cls]
            except KeyError:
                continue
            break
        node.subtag = event.subtag
        node.skip_render = event.skip_render
        return node


for name in nodes.__all__:
    obj = getattr(nodes, name)
    if hasattr(obj, 'basetag') and hasattr(obj, 'node_type'):
        TemplateLoader.TAG_MAP[obj.basetag, obj.node_type] = obj
