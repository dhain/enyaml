__all__ = [
    'Setter',
    'Expression',
    'FormatString',
    'If',
    'For',
    'Template',
]

import yaml
import copy
from .loader import TemplateLoader
from .dumper import TemplateDumper
from .util import SENTINEL


class Setter(yaml.YAMLObject):
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper
    yaml_tag = '!set'

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(loader, loader.construct_mapping(node))

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(cls.yaml_tag, data.data)

    def __init__(self, loader, data):
        self.loader = loader
        self.data = data

    def render(self, ctx):
        self.loader.clear_constructed_nodes(self)
        ctx.update(self.data)
        return SENTINEL


class Expression(yaml.YAMLObject):
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper
    yaml_tag = '!$'

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(loader, loader.construct_scalar(node), node.style)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.expr, data.style)

    def __init__(self, loader, expr, style=None):
        self.loader = loader
        self.expr = expr
        self.style = style

    def get_globals(self, ctx):
        return {
            '__builtins__': {},
            'loader': self.loader,
            'ctx': ctx
        }

    def render(self, ctx):
        self.loader.clear_constructed_nodes(self)
        globals = self.get_globals(ctx)
        return eval(self.expr, globals, ctx)


class FormatString(Expression):
    yaml_tag = '!$f'

    def render(self, ctx):
        return self.expr.format(**ctx)


class If(yaml.YAMLObject):
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper
    yaml_tag = '!if'

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(loader, loader.construct_sequence(node), node.flow_style)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_sequence(
            cls.yaml_tag, data.if_list, data.flow_style)

    def __init__(self, loader, if_list, flow_style=None):
        self.loader = loader
        self.if_list = if_list
        self.flow_style = flow_style

    def render(self, ctx):
        self.loader.clear_constructed_nodes(self)
        rest = self.if_list
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


class For(yaml.YAMLObject):
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper
    yaml_tag = '!for'

    @classmethod
    def from_yaml(cls, loader, node):
        self = object.__new__(cls)
        self.loader = loader
        self.node = node
        self.add_tag = True
        return self

    @classmethod
    def to_yaml(cls, dumper, data):
        if data.add_tag:
            node = copy.copy(data.node)
            node.tag = cls.yaml_tag
        else:
            node = data.node
        return node

    def __init__(
        self, loader, kind, arglist, obj, value_tmpl, if_tmpl=None, flow_style=None
    ):
        self.loader = loader
        self.add_tag = False
        value = [
            (obj, arglist),
            ('ret', value_tmpl),
        ]
        if if_tmpl is not None:
            value.append(('if', if_tmpl))
        if kind == 'sequence':
            self.node = yaml.SequenceNode(self.yaml_tag, value, flow_style)
        elif kind == 'mapping':
            self.node = yaml.MappingNode(self.yaml_tag, value, flow_style)

    def get_globals(self, ctx):
        return {
            '__builtins__': {},
            'loader': self.loader,
            'ctx': ctx
        }

    def render(self, ctx):
        self.loader.clear_constructed_nodes(self.node)
        if isinstance(self.node, yaml.SequenceNode):
            fornode, = self.node.value
        elif isinstance(self.node, yaml.MappingNode):
            fornode = self.node
        else:
            raise TypeError('wrong kind of node')

        value = []
        objs = None
        tmpls = {}
        for left, right in fornode.value:
            left = self.loader.construct_object(left, deep=True)
            if isinstance(left, str) and left in {'ret', 'if'}:
                tmpls[left] = Template(self.loader, right)
            elif objs is None:
                objs = left
                if hasattr(objs, 'render'):
                    objs = objs.render(ctx)
                arglist = self.loader.construct_object(right, deep=True)
                if isinstance(arglist, str):
                    arglist = (arglist,)
                arglist = ', '.join(arglist)
                code = compile(f'{arglist} = obj', '', 'exec')
            else:
                raise ValueError('objs already set')

        test = True
        globals = self.get_globals(ctx)
        for obj in objs:
            ctx.maps.insert(0, {'obj': obj})
            ctx.maps.insert(0, {})
            exec(code, globals, ctx)
            del ctx.maps[1] # obj
            ret = tmpls['ret'].render(ctx)
            if 'if' in tmpls:
                test = tmpls['if'].render(ctx)
            if test:
                value.append(ret)
            del ctx.maps[0]

        if isinstance(self.node, yaml.MappingNode):
            d = {}
            for i in value:
                d.update(i)
            value = d

        return value


class Template(yaml.YAMLObject):
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper
    yaml_tag = '!tmpl'

    @classmethod
    def from_yaml(cls, loader, node):
        if node.tag == cls.yaml_tag:
            node = copy.copy(node)
            node.tag = loader.resolve(type(node), None, (None, None))
        return cls(loader, node)

    @classmethod
    def to_yaml(cls, dumper, data):
        if data.add_tag:
            node = copy.copy(data.node)
            node.tag = cls.yaml_tag
        else:
            node = data.node
        return node

    def __init__(self, loader, node, add_tag=True):
        self.loader = loader
        self.node = node
        self.add_tag = add_tag

    def render(self, ctx):
        self.loader.clear_constructed_nodes(self.node)
        value = self.loader.construct_object(self.node, deep=True)

        if hasattr(value, 'render'):
            return value.render(ctx)

        elif isinstance(value, list):
            l = []
            for i in value:
                if hasattr(i, 'render'):
                    i = i.render(ctx)
                if i is not SENTINEL:
                    l.append(i)
            value = l

        elif isinstance(value, dict):
            d = {}
            for k, v in value.items():
                if hasattr(k, 'render'):
                    k = k.render(ctx)
                if hasattr(v, 'render'):
                    v = v.render(ctx)
                if SENTINEL not in (k, v):
                    d[k] = v
            value = d

        return value
