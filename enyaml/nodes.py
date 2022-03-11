__all__ = [
    'ScalarTemplateNode',
    'SequenceTemplateNode',
    'MappingTemplateNode',
    'SetterNode',
    'ExpressionNode',
    'FormatStringNode',
    'IfNode',
    'SequenceForNode',
    'MappingForNode',
]

import copy
import functools
import yaml


TAG_PREFIX = 'tag:enyaml.org,2022:'


def split_tag(tag):
    if tag.startswith(TAG_PREFIX):
        basetag, *subtag = tag[len(TAG_PREFIX):].split(':', 1)
        skip_render = (basetag[-1] == '~')
        if skip_render:
            basetag = basetag[:-1]
        subtag = subtag[0] if subtag else None
        return basetag, subtag, skip_render
    return None, None, None


def unsplit_tag(basetag, subtag, skip_render):
    return ''.join((
        TAG_PREFIX, basetag,
        '~' if skip_render else '',
        ':'+subtag if subtag else ''
    ))


def maybe_render(node, loader, ctx):
    if hasattr(node, 'render') and not node.skip_render:
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


class BaseTemplateNode:
    basetag = 'tmpl'

    @classmethod
    def to_yaml(cls, dumper, data):
        node = copy.copy(data)
        if data.subtag == dumper.resolve(cls.node_type, None, (None, None)):
            node.tag = node.tag[:len(data.subtag)]
            node.subtag = None
        return node

    def make_result_node(self, loader, value, implicit=True):
        node = copy.copy(self)
        node.__class__ = self.node_type
        node.__dict__.pop('subtag', None)
        node.__dict__.pop('skip_render', None)
        if self.subtag is None:
            node.tag = loader.resolve(self.node_type, value, (implicit, False))
        else:
            node.tag = self.subtag
        node.value = value
        return node

    def render(self, loader, ctx):
        return self.make_result_node(loader, self.value)


class ScalarTemplateNode(BaseTemplateNode, yaml.ScalarNode):
    node_type = yaml.ScalarNode

    def __init__(
        self, value, start_mark=None, end_mark=None,
        style=None, subtag=None, skip_render=False
    ):
        self.subtag = subtag
        self.skip_render = skip_render
        tag = unsplit_tag(self.basetag, subtag, skip_render)
        yaml.ScalarNode.__init__(
            self, tag, value, start_mark, end_mark, style)


class BaseCollectionTemplateNode(BaseTemplateNode):
    def __init__(
        self, value, start_mark=None, end_mark=None,
        flow_style=None, subtag=None, skip_render=False
    ):
        self.subtag = subtag
        self.skip_render = skip_render
        tag = unsplit_tag(self.basetag, subtag, skip_render)
        yaml.CollectionNode.__init__(
            self, tag, value, start_mark, end_mark, flow_style)

    def render_value(self, loader, ctx):
        return self.value


class SequenceTemplateNode(BaseCollectionTemplateNode, yaml.SequenceNode):
    node_type = yaml.SequenceNode

    def render(self, loader, ctx):
        value = []
        for item in self.render_value(loader, ctx):
            item = maybe_render(item, loader, ctx)
            if item is not None:
                value.append(item)
        return self.make_result_node(loader, value)


class MappingTemplateNode(BaseCollectionTemplateNode, yaml.MappingNode):
    node_type = yaml.MappingNode

    def render(self, loader, ctx):
        value = []
        for item_key, item_value in self.render_value(loader, ctx):
            item_key = maybe_render(item_key, loader, ctx)
            item_value = maybe_render(item_value, loader, ctx)
            if None not in (item_key, item_value):
                value.append((item_key, item_value))
        return self.make_result_node(loader, value)


class SetterNode(MappingTemplateNode):
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
    basetag = '$'

    def render(self, loader, ctx):
        globals = get_globals(loader, ctx)
        value = eval(self.value, globals, ctx)
        if isinstance(value, BaseTemplateNode):
            return maybe_render(value, loader, ctx)
        elif isinstance(value, yaml.Node):
            return value
        return self.make_result_node(loader, value, implicit=False)


class FormatStringNode(ScalarTemplateNode):
    basetag = '$f'

    def render(self, loader, ctx):
        dct = get_globals(loader, ctx)
        dct.update(ctx)
        return self.make_result_node(
            loader, self.value.format(**dct))


class IfNode(SequenceTemplateNode):
    basetag = 'if'

    def render(self, loader, ctx):
        rest = self.value
        while rest:
            if len(rest) == 1:
                result, = rest
                break
            test, result, *rest = rest
            test = loader.construct_object(maybe_render(test, loader, ctx), deep=True)
            if test:
                break
        else:
            return None
        return maybe_render(result, loader, ctx)


class BaseForNode(BaseTemplateNode):
    basetag = 'for'

    def _forinfo(self, loader, ctx):
        items = None
        ret_tmpl = None
        if_tmpl = None
        for left, right in self._value():
            if left.value == 'ret':
                ret_tmpl = right
            elif left.value == 'if':
                if_tmpl = right
            elif items is None:
                items = left
                arglist = right
            else:
                raise ValueError('items already set')
        arglist = loader.construct_object(maybe_render(arglist, loader, ctx), deep=True)
        if isinstance(arglist, str):
            arglist = (arglist,)
        arglist = ', '.join(arglist)
        code = compile(f'{arglist} = item', '', 'exec')
        return items, ret_tmpl, if_tmpl, code

    def render_value(self, loader, ctx):
        items, ret_tmpl, if_tmpl, code = self._forinfo(loader, ctx)
        globals = get_globals(loader, ctx)
        items = maybe_render(items, loader, ctx)
        for item in loader.construct_object(items, deep=True):
            with ctx.push():
                with ctx.push({'item': item}, 1):
                    exec(code, globals, ctx)
                if if_tmpl is None:
                    test = True
                else:
                    test = loader.construct_object(
                        maybe_render(if_tmpl, loader, ctx), deep=True)
                if not test:
                    continue
                yield maybe_render(ret_tmpl, loader, ctx)


class SequenceForNode(BaseForNode, SequenceTemplateNode):
    def _value(self):
        value, = self.value
        return value.value


class MappingForNode(BaseForNode, MappingTemplateNode):
    def _value(self):
        return self.value

    def render_value(self, loader, ctx):
        for node in super().render_value(loader, ctx):
            for item in node.value:
                yield item
