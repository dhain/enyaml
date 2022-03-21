# Copyright (c) 2022, Sadie Hain. All rights reserved.
# Released under the BSD 3-Clause License
# https://enyaml.org/LICENSE

__all__ = [
    'TAG_PREFIX',
    'BaseTemplateNode',
    'ScalarTemplateNode',
    'BaseCollectionTemplateNode',
    'SequenceTemplateNode',
    'MappingTemplateNode',
    'ForNode',
    'SetterNode',
    'ExpressionNode',
    'FormatStringNode',
    'IfNode',
]

import re
import copy
import functools
import yaml
from yaml.constructor import ConstructorError


TAG_PREFIX = 'tag:enyaml.org,2022:'
FLAGS = '~'
FOR_RX = re.compile(r'((?:(?:^|\s*,\s*)[a-zA-Z_]\w*)+)\s+in\s')


def split_tag(tag):
    if tag.startswith(TAG_PREFIX):
        basetag, *subtag = tag[len(TAG_PREFIX):].split(':', 1)
        i = len(basetag)
        while i > 0:
            if basetag[i-1] in FLAGS:
                i -= 1
            else:
                break
        basetag, flags = basetag[:i], basetag[i:]
        subtag = subtag[0] if subtag else None
        return basetag, subtag, flags
    return None, None, None


def unsplit_tag(basetag, subtag, flags):
    return ''.join((
        TAG_PREFIX, basetag,
        ''.join(flags),
        ':'+subtag if subtag else ''
    ))


def maybe_render(node, loader, ctx):
    if hasattr(node, 'render') and '~' not in node.flags:
        return node.render(loader, ctx)
    return node


def user_render(loader, ctx, tmpl, local_ctx=None):
    if local_ctx is None:
        local_ctx = {}
    with ctx.push(local_ctx):
        return loader.construct_object(tmpl.render(loader, ctx), deep=True)


def get_globals(loader, ctx):
    return {
        '__builtins__': {
            'list': list,
            'render': functools.partial(user_render, loader, ctx),
        },
        'ctx': ctx,
    }


class RenderError(yaml.error.MarkedYAMLError):
    pass


class BaseTemplateNode:
    basetag = 'tmpl'

    @classmethod
    def to_yaml(cls, dumper, data):
        node = copy.copy(data)
        if data.subtag == dumper.resolve(cls.node_type, None, (None, None)):
            node.tag = node.tag[:len(data.subtag)]
            node.subtag = None
        return node

    def _detemplify(self, loader, implicit=True, deep=False):
        self.tag = self.subtag or loader.resolve(
            self.node_type, self.value, (implicit, False))
        self.__class__ = self.node_type
        self.__dict__.pop('subtag', None)
        self.__dict__.pop('flags', None)

    def make_result_node(self, loader, value, implicit=True):
        node = copy.copy(self)
        node.value = value
        node._detemplify(loader, implicit)
        return node

    def render(self, loader, ctx):
        return self.make_result_node(loader, self.value)


class ScalarTemplateNode(BaseTemplateNode, yaml.ScalarNode):
    node_type = yaml.ScalarNode


class BaseCollectionTemplateNode(BaseTemplateNode):
    pass


class SequenceTemplateNode(BaseCollectionTemplateNode, yaml.SequenceNode):
    node_type = yaml.SequenceNode

    def _detemplify(self, loader, implicit=True, deep=False):
        super()._detemplify(loader, implicit, deep)
        if deep:
            for node in self.value:
                if isinstance(node, BaseTemplateNode):
                    node._detemplify(loader, implicit, deep)

    def render(self, loader, ctx):
        value = []
        for item in self.value:
            item = maybe_render(item, loader, ctx)
            if item is not None:
                if isinstance(item, ForResult):
                    value.extend(item.value)
                else:
                    value.append(item)
        return self.make_result_node(loader, value)


class MappingTemplateNode(BaseCollectionTemplateNode, yaml.MappingNode):
    node_type = yaml.MappingNode

    def _detemplify(self, loader, implicit=True, deep=False):
        super()._detemplify(loader, implicit, deep)
        if deep:
            for key_node, value_node in self.value:
                if isinstance(key_node, BaseTemplateNode):
                    key_node._detemplify(loader, implicit, deep)
                if isinstance(value_node, BaseTemplateNode):
                    value_node._detemplify(loader, implicit, deep)

    def render(self, loader, ctx):
        value = []
        for item_key, item_value in self.value:
            if isinstance(item_key, ForNode):
                if len(self.value) > 1:
                    raise RenderError(
                        'not expecting other items', item_key.start_mark)
                return item_key.render_items(loader, ctx, item_value)
            item_key = maybe_render(item_key, loader, ctx)
            item_value = maybe_render(item_value, loader, ctx)
            if None not in (item_key, item_value):
                value.append((item_key, item_value))
        return self.make_result_node(loader, value)


class ForResult(yaml.SequenceNode):
    pass


class ForNode(yaml.ScalarNode):
    '''Represents a :tmpl:tag:`for` expression node.
    '''
    node_type = yaml.ScalarNode
    basetag = 'for'
    flags = ''

    def render_items(self, loader, ctx, tmpl):
        m = FOR_RX.match(self.value)
        if m is None:
            raise RenderError(
                'invalid for expression', self.start_mark)
        names, = m.groups()
        expr = self.value[m.end():].strip()
        namelist = [n.strip() for n in names.split(',')]
        value = []
        globals = get_globals(loader, ctx)
        for i in eval(expr, globals, ctx):
            with ctx.push():
                with ctx.push({'i': i}, 1):
                    exec(f'{names} = i', globals, ctx)
                node = maybe_render(tmpl, loader, ctx)
                if node is not None:
                    value.append(node)
        tag = self.subtag or loader.resolve(
            yaml.SequenceNode, None, (None, None))
        return ForResult(tag, value)

    def render(self, loader, ctx):
        raise RenderError("can't render a ForNode", self.start_mark)

    def _detemplify(self, loader, implicit=True, deep=False):
        raise ConstructorError(
            "can't construct a ForNode", self.start_mark)


class SetterNode(MappingTemplateNode):
    '''Represents a :tmpl:tag:`set` node.

    When rendered, updates the Context with the result. :tmpl:tag:`set` nodes
    are removed from rendered documents.
    '''
    basetag = 'set'

    def render(self, loader, ctx):
        ctx.update(
            (
                loader.construct_object(key, deep=True),
                loader.construct_object(value, deep=True)
            )
            for key, value in
            super().render(loader, ctx).value
        )
        return None


class ExpressionNode(ScalarTemplateNode):
    '''Represents a :tmpl:tag:`$` node.

    When rendered, is replaced by the result of the expression. If the
    expression evaluates to a template node, it will be rendered.
    '''
    basetag = '$'

    def render(self, loader, ctx):
        globals = get_globals(loader, ctx)
        value = eval(self.value, globals, ctx)
        if isinstance(value, yaml.Node):
            return maybe_render(value, loader, ctx)
        return self.make_result_node(loader, value, implicit=False)


class FormatStringNode(ScalarTemplateNode):
    '''Represents a :tmpl:tag:`$f` node.

    When rendered, is replaced by the result of the format-string.
    '''
    basetag = '$f'

    def render(self, loader, ctx):
        dct = get_globals(loader, ctx)
        dct.update(ctx)
        return self.make_result_node(loader, self.value.format(**dct))


class IfNode(SequenceTemplateNode):
    '''Represents an :tmpl:tag:`if` node.

    When rendered, is replaced by the first matching node. If no nodes match,
    but a default is provided, then will be replaced by the default node. If no
    default is provided, then node will not appear in output.
    '''
    basetag = 'if'

    def render(self, loader, ctx):
        rest = self.value
        if len(rest) < 2:
            raise ValueError('expecting more')
        while rest:
            if len(rest) == 1:
                result, = rest
                break
            test, result, *rest = rest
            if loader.construct_object(
                maybe_render(test, loader, ctx), deep=True
            ):
                break
        else:
            return None
        return maybe_render(result, loader, ctx)
