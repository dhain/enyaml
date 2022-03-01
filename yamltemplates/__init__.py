import sys
import yaml
import copy
import types
import typing
import functools
from collections import ChainMap
from yaml.constructor import ConstructorError
from pprint import pprint


SENTINEL = object()


def copy_func_with_globals(f, globals):
    newf = types.FunctionType(
        f.__code__, globals, name=f.__name__,
        argdefs=f.__defaults__, closure=f.__closure__
    )
    newf = functools.update_wrapper(newf, f)
    newf.__kwdefaults__ = copy.copy(f.__kwdefaults__)
    return newf


class AttrChainMap(ChainMap):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return super().__getattr__(name)


class TemplateLoader(yaml.SafeLoader):
    def __init__(self, stream):
        yaml.SafeLoader.__init__(self, stream)
        self.set_context()
        self._current_node = None

    def set_context(self, ctx=None):
        if ctx is None:
            ctx = AttrChainMap()
        self.ctx = ctx

    def get_eval_env(self, globals=(), locals=None):
        return (
            dict(globals, loader=self, ctx=self.ctx),
            self.ctx if locals is None else locals
        )

    def check_node(self):
        if self._current_node:
            return True
        while super().check_node():
            node = self.get_node()
            if node.tag != '!set':
                self._current_node = node
                return True
            super().construct_document(node)
        return False

    def get_node(self):
        if self._current_node:
            node, self._current_node = self._current_node, None
            return node
        return super().get_node()

    def construct_sequence(self, node, deep=False):
        return [
            i for i in super().construct_sequence(node, deep)
            if i is not SENTINEL
        ]

    def construct_mapping(self, node, deep=False):
        return dict(
            i for i in super().construct_mapping(node, deep).items()
            if SENTINEL not in i
        )

    def construct_pairs(self, node, deep=False):
        return [
            i for i in super().construct_pairs(node, deep)
            if SENTINEL not in i
        ]

    def construct_setter(self, node):
        self.ctx.update(self.construct_mapping(node))
        return SENTINEL

    def construct_if(self, node):
        expr, result, *rest = self.construct_sequence(node, deep=True)
        while not expr:
            if rest:
                if len(rest) > 1:
                    expr, result, *rest = rest
                    continue
                return rest[0]
            return SENTINEL
        return result

    def construct_ctx_var(self, node):
        expr = self.construct_scalar(node)
        # TODO: is this safe?
        return eval(expr, *self.get_eval_env())

    def construct_fmt_str(self, node):
        tmpl = self.construct_scalar(node)
        return tmpl.format(ctx=self.ctx, **self.ctx)

    def construct_template(self, tag, node):
        return Template(self, tag, node)

    def construct_for_loop(self, node):
        if isinstance(node, yaml.SequenceNode):
            fornode, = node.value
        else:
            fornode = node

        forinfo = {}
        for left, right in fornode.value:
            left = self.construct_object(left, deep=True)
            if isinstance(left, str) and left in {'ret', 'if'}:
                forinfo[left] = Template(self, right)
            else:
                forinfo['args'] = self.construct_object(right, deep=True)
                if isinstance(forinfo['args'], str):
                    forinfo['args'] = (forinfo['args'],)
                arglist = ', '.join(forinfo['args'])
                forinfo['code'] = compile(f'{arglist} = obj', '', 'exec')
                forinfo['obj'] = left

        if isinstance(node, yaml.SequenceNode):
            return list(self.execute_for_loop(forinfo))
        elif isinstance(node, yaml.MappingNode):
            ret = {}
            for i in self.execute_for_loop(forinfo):
                ret.update(i)
            return ret

    def execute_for_loop(self, forinfo):
        for i in forinfo['obj']:
            globals, locals = self.get_eval_env({'obj': i}, {})
            exec(forinfo['code'], globals, locals)
            ret = forinfo['ret'].render(locals)
            if 'if' not in forinfo or forinfo['if'].render(locals):
                yield ret

    def clear_constructed_nodes(self, node):
        try:
            del self.constructed_objects[node]
        except KeyError as k:
            pass
        if isinstance(node.value, list):
            for child in node.value:
                if isinstance(child, tuple):
                    k, v = child
                    self.clear_constructed_nodes(k)
                    self.clear_constructed_nodes(v)
                else:
                    self.clear_constructed_nodes(child)
        elif isinstance(node.value, yaml.Node):
            self.clear_constructed_nodes(node.value)


class TemplateDumper(yaml.SafeDumper):
    pass


class Template(yaml.YAMLObject):
    yaml_loader = TemplateLoader
    yaml_dumper = TemplateDumper
    yaml_tag = '!tmpl'

    @classmethod
    def from_yaml(cls, loader, node):
        if node.tag == '!tmpl':
            node.tag = loader.resolve(type(node), None, (None, None))
        return cls(loader, node)

    @classmethod
    def to_yaml(cls, dumper, data):
        node = copy.copy(data.node)
        node.tag = '!tmpl'
        return node

    def __init__(self, loader, node):
        self.loader = loader
        self.node = node

    def render(self, local_ctx=None):
        if local_ctx:
            self.loader.ctx.maps.insert(0, local_ctx)
        result = self.loader.construct_object(self.node, deep=True)
        self.loader.clear_constructed_nodes(self.node)
        if local_ctx:
            self.loader.ctx.maps.pop(0)
        return result


TemplateLoader.add_constructor(
    '!set', TemplateLoader.construct_setter)

TemplateLoader.add_constructor(
    '!if', TemplateLoader.construct_if)

TemplateLoader.add_constructor(
    '!$', TemplateLoader.construct_ctx_var)

TemplateLoader.add_constructor(
    '!$f', TemplateLoader.construct_fmt_str)

TemplateLoader.add_constructor(
    '!for', TemplateLoader.construct_for_loop)


yaml.dump_all(
    yaml.load_all(open(sys.argv[1]), Loader=TemplateLoader),
    sys.stdout, Dumper=TemplateDumper)
