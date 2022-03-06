__all__ = [
    'ScalarTemplate',
    'SequenceTemplate',
    'MappingTemplate',
    'Setter',
    'Expression',
    'FormatString',
    'If',
    'SequenceComprehension',
    'MappingComprehension',
]

import yaml
import copy
from itertools import chain
from .loader import TemplateLoader
from .dumper import TemplateDumper
from .util import SENTINEL


class BaseTemplate:
    tag_prefix = '!'
    tag_suffix = 'tmpl'
    _map = {}

    @classmethod
    def _register(cls, template_cls, node_cls):
        cls._map[template_cls.tag_suffix, node_cls] = template_cls

    @classmethod
    def from_yaml(cls, loader, tag, node):
        if tag is None:
            tag = node.tag
            if tag.startswith(cls.tag_prefix):
                tag = tag[len(cls.tag_prefix):]
            else:
                tag = f'tmpl:{tag}'
        tag, *subtag = tag.split(':', 1)
        if subtag:
            subtag, = subtag
        else:
            subtag = None
        return cls._map[tag, type(node)].from_yaml(loader, subtag, node)

    @classmethod
    def _expand_tag(cls, dumper, data):
        tag = f'{cls.tag_prefix}{data.tag_suffix}'
        if data.subtag is None or data.subtag in (
            dumper.DEFAULT_SCALAR_TAG,
            dumper.DEFAULT_SEQUENCE_TAG,
            dumper.DEFAULT_MAPPING_TAG
        ):
            return tag
        return ':'.join((tag, data.subtag))

    def __init__(self, data, subtag=None, orig_node=None):
        self.data = data
        self.subtag = subtag
        self.orig_node = orig_node

    def get_globals(self, ctx):
        return {
            '__builtins__': {},
            'ctx': ctx
        }


TemplateLoader.template_base_class = BaseTemplate
TemplateLoader.add_multi_constructor(BaseTemplate.tag_prefix, BaseTemplate.from_yaml)


class ScalarTemplate(BaseTemplate):
    @classmethod
    def from_yaml(cls, loader, subtag, node):
        data = loader.construct_scalar(node)
        return cls(data, subtag, orig_node=node)

    @classmethod
    def to_yaml(cls, dumper, data):
        if data.orig_node is not None:
            return data.orig_node
        tag = cls._expand_tag(dumper, data)
        return dumper.represent_scalar(tag, data.data)

    def render(self, ctx, render_subtemplates=True):
        data = self.data
        if (
            hasattr(data, 'render') and
            (render_subtemplates or not isinstance(data, BaseTemplate))
        ):
            data = data.render(ctx)
        return data


BaseTemplate._register(ScalarTemplate, yaml.ScalarNode)
TemplateDumper.add_representer(ScalarTemplate, ScalarTemplate.to_yaml)


class SequenceTemplate(BaseTemplate):
    @classmethod
    def from_yaml(cls, loader, subtag, node):
        data = loader.construct_sequence(node, deep=True)
        return cls(data, subtag, orig_node=node)

    @classmethod
    def to_yaml(cls, dumper, data):
        if data.orig_node is not None:
            return data.orig_node
        tag = cls._expand_tag(dumper, data)
        return dumper.represent_sequence(tag, data.data)

    def render(self, ctx, render_subtemplates=True):
        value = []
        for i in self.data:
            if (
                hasattr(i, 'render') and
                (render_subtemplates or not isinstance(i, BaseTemplate))
            ):
                i = i.render(ctx)
            if i is not SENTINEL:
                value.append(i)
        return value


BaseTemplate._register(SequenceTemplate, yaml.SequenceNode)
TemplateDumper.add_representer(SequenceTemplate, SequenceTemplate.to_yaml)


class MappingTemplate(BaseTemplate):
    @classmethod
    def from_yaml(cls, loader, subtag, node):
        loader.flatten_mapping(node)
        data = [
            (loader.construct_object(k, True), loader.construct_object(v, True))
            for k, v in node.value
        ]
        return cls(data, subtag, orig_node=node)

    @classmethod
    def to_yaml(cls, dumper, data):
        if data.orig_node is not None:
            return data.orig_node
        tag = cls._expand_tag(dumper, data)
        return dumper.represent_mapping(tag, data.data)

    def render(self, ctx, render_subtemplates=True):
        value = {}
        for k, v in self.data:
            if (
                hasattr(k, 'render') and
                (render_subtemplates or not isinstance(k, BaseTemplate))
            ):
                k = k.render(ctx)
            if (
                hasattr(v, 'render') and
                (render_subtemplates or not isinstance(v, BaseTemplate))
            ):
                v = v.render(ctx)
            if SENTINEL not in (k, v):
                value[k] = v
        return value


BaseTemplate._register(MappingTemplate, yaml.MappingNode)
TemplateDumper.add_representer(MappingTemplate, MappingTemplate.to_yaml)


class Setter(MappingTemplate):
    tag_suffix = 'set'

    def render(self, ctx):
        ctx.update(super().render(ctx, render_subtemplates=False))
        return SENTINEL


BaseTemplate._register(Setter, yaml.MappingNode)
TemplateDumper.add_representer(Setter, Setter.to_yaml)


class Expression(ScalarTemplate):
    tag_suffix = '$'

    def render(self, ctx):
        globals = self.get_globals(ctx)
        return eval(self.data, globals, ctx)


BaseTemplate._register(Expression, yaml.ScalarNode)
TemplateDumper.add_representer(Expression, Expression.to_yaml)


class FormatString(Expression):
    tag_suffix = '$f'

    def render(self, ctx):
        return self.data.format(**ctx)


BaseTemplate._register(FormatString, yaml.ScalarNode)
TemplateDumper.add_representer(FormatString, FormatString.to_yaml)


class If(SequenceTemplate):
    tag_suffix = 'if'

    def render(self, ctx):
        rest = self.data
        while rest:
            if len(rest) == 1:
                result, = rest
                break
            test, result, *rest = rest
            if hasattr(test, 'render'):
                test = test.render(ctx)
            if test:
                break
        else:
            return SENTINEL
        if hasattr(result, 'render'):
            result = result.render(ctx)
        return result


BaseTemplate._register(If, yaml.SequenceNode)
TemplateDumper.add_representer(If, If.to_yaml)


class BaseComprehension(BaseTemplate):
    tag_suffix = 'for'

    @classmethod
    def _construct_forinfo(cls, loader, value):
        items = None
        ret_tmpl = None
        if_tmpl = None
        for left, right in value:
            left = loader.construct_object(left, deep=True)
            if left == 'ret':
                ret_tmpl = BaseTemplate.from_yaml(loader, None, right)
            elif left == 'if':
                if_tmpl = loader.construct_object(right, deep=True)
            elif items is None:
                items = left
                arglist = loader.construct_object(right, deep=True)
            else:
                raise ValueError('items already set')
        return {
            'items': items,
            'ret_tmpl': ret_tmpl,
            'if_tmpl': if_tmpl,
            'arglist': arglist,
        }

    @classmethod
    def _represent_forinfo(cls, dumper, data, tag=None):
        if tag is None:
            tag = dumper.DEFAULT_MAPPING_TAG
        value = [
            (dumper.represent_data(data.items), dumper.represent_data(data.arglist)),
            (dumper.represent_data('ret'), dumper.represent_data(data.ret_tmpl)),
        ]
        if data.if_tmpl is not None:
            value.append(
                (dumper.represent_data('if'), dumper.represent_data(data.if_tmpl))
            )
        return yaml.MappingNode(tag, value)

    def __init__(self, arglist, items, ret_tmpl, if_tmpl=None, subtag=None, orig_node=None):
        if not isinstance(arglist, str):
            arglist = ', '.join(arglist)
        self.arglist = arglist
        self.code = compile(f'{arglist} = item', '', 'exec')
        self.items = items
        self.ret_tmpl = ret_tmpl
        self.if_tmpl = if_tmpl
        self.subtag = subtag
        self.orig_node = orig_node

    def _execute(self, ctx):
        globals = self.get_globals(ctx)
        if hasattr(self.items, 'render'):
            items = self.items.render(ctx)
        else:
            items = self.items
        for item in items:
            with ctx.push():
                with ctx.push({'item': item}, 1):
                    exec(self.code, globals, ctx)
                ret = self.ret_tmpl.render(ctx)
                if (
                    self.if_tmpl is None or
                    (hasattr(self.if_tmpl, 'render') and self.if_tmpl.render(ctx)) or
                    self.if_tmpl
                ):
                    yield ret


class SequenceComprehension(SequenceTemplate, BaseComprehension):
    @classmethod
    def from_yaml(cls, loader, subtag, node):
        return cls(
            subtag=subtag, orig_node=node,
            **cls._construct_forinfo(loader, node.value[0].value)
        )

    @classmethod
    def to_yaml(cls, dumper, data):
        if data.orig_node is not None:
            return data.orig_node
        tag = cls._expand_tag(dumper, data)
        node = dumper.represent_sequence(tag, [])
        node.value = [cls._represent_forinfo(dumper, data)]
        return node

    def render(self, ctx):
        return list(self._execute(ctx))


BaseTemplate._register(SequenceComprehension, yaml.SequenceNode)
TemplateDumper.add_representer(SequenceComprehension, SequenceComprehension.to_yaml)


class MappingComprehension(MappingTemplate, BaseComprehension):
    @classmethod
    def from_yaml(cls, loader, subtag, node):
        return cls(
            subtag=subtag, orig_node=node,
            **cls._construct_forinfo(loader, node.value)
        )

    @classmethod
    def to_yaml(cls, dumper, data):
        if data.orig_node is not None:
            return data.orig_node
        tag = cls._expand_tag(dumper, data)
        return cls._represent_forinfo(dumper, data, tag)

    def render(self, ctx):
        return dict(chain.from_iterable(i.items() for i in self._execute(ctx)))


BaseTemplate._register(MappingComprehension, yaml.MappingNode)
TemplateDumper.add_representer(MappingComprehension, MappingComprehension.to_yaml)
