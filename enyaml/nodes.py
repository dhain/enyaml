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
        if basetag[-1] == '~':
            basetag = basetag[:-1]
            skip_render = True
        else:
            skip_render = False
        if subtag:
            subtag, = subtag
        else:
            subtag = None
        return basetag, subtag, skip_render
    return None, None, None


def unsplit_tag(basetag, subtag, skip_render):
    return ''.join((
        TAG_PREFIX, basetag,
        '~' if skip_render else '',
        ':', subtag
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


class BaseTemplateNode:
    basetag = 'tmpl'

    @classmethod
    def to_yaml(cls, dumper, data):
        node = copy.copy(data)
        if node.subtag == dumper.resolve(cls.node_type, None, (None, None)):
            node.tag = node.tag[:len(node.subtag)]
            node.subtag = None
        return node

    def get_globals(self, loader, ctx):
        return {
            '__builtins__': {
                'list': list,
                'render': functools.partial(user_render, loader, ctx),
            },
            'loader': loader,
            'ctx': ctx
        }

    def render(self, loader, ctx):
        new = copy.copy(self)
        new.__class__ = self.node_type
        new.skip_render = False
        if self.subtag is None:
            new.tag = loader.resolve(self.node_type, None, (None, None))
        else:
            new.tag = self.subtag
        return new


class ScalarTemplateNode(BaseTemplateNode, yaml.ScalarNode):
    node_type = yaml.ScalarNode


class BaseCollectionTemplateNode(BaseTemplateNode):
    def _render(self, loader, ctx):
        return self.value


class SequenceTemplateNode(BaseCollectionTemplateNode, yaml.SequenceNode):
    node_type = yaml.SequenceNode

    def render(self, loader, ctx):
        new = super().render(loader, ctx)
        new.value = []
        for item in self._render(loader, ctx):
            item = maybe_render(item, loader, ctx)
            if item is not None:
                new.value.append(item)
        return new


class MappingTemplateNode(BaseCollectionTemplateNode, yaml.MappingNode):
    node_type = yaml.MappingNode

    def render(self, loader, ctx):
        new = super().render(loader, ctx)
        new.value = []
        for key, value in self._render(loader, ctx):
            key = maybe_render(key, loader, ctx)
            value = maybe_render(value, loader, ctx)
            if None not in (key, value):
                new.value.append((key, value))
        return new


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
        globals = self.get_globals(loader, ctx)
        value = eval(self.value, globals, ctx)
        if isinstance(value, BaseTemplateNode):
            new = maybe_render(value, loader, ctx)
        elif isinstance(value, yaml.Node):
            new = value
        else:
            new = super().render(loader, ctx)
            new.value = value
        return new


class FormatStringNode(ScalarTemplateNode):
    basetag = '$f'

    def render(self, loader, ctx):
        dct = self.get_globals(loader, ctx)
        dct.update(ctx)
        new = super().render(loader, ctx)
        new.value = self.value.format(**dct)
        return new


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

    def _render(self, loader, ctx):
        items, ret_tmpl, if_tmpl, code = self._forinfo(loader, ctx)
        globals = self.get_globals(loader, ctx)
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

    def _render(self, loader, ctx):
        for node in super()._render(loader, ctx):
            for item in node.value:
                yield item
