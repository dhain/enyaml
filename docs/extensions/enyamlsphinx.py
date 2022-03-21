from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_id, make_refnode
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx import domains
import enyaml


TARGET_IDS = {
    '$': 'expr',
    '$f': 'strfrm',
}


class RenderDirective(SphinxDirective):
    has_content = True
    option_spec = {
        'filename': directives.unchanged,
        'show-template': directives.unchanged,
    }

    def run(self):
        if 'filename' in self.options:
            if self.content:
                raise ValueError("can't specify both filename and content")
            rel_filename, filename = self.env.relfn2path(
                self.options['filename'])
            self.env.note_dependency(rel_filename)
            with open(filename) as f:
                template = f.read()
        else:
            template = '\n'.join(self.content)
        ctx = enyaml.Context()
        rendered = enyaml.dump_all(enyaml.render_all(template, ctx))
        if rendered.endswith('\n...\n'):
            rendered = rendered[:-5]
        rendered_node = nodes.literal_block(rendered, rendered)
        rendered_node['language'] = 'yaml'
        ret = [rendered_node]
        if 'show-template' in self.options:
            template_node = nodes.literal_block(template, template)
            template_node['language'] = 'yaml'
            sep = nodes.paragraph(text=self.options['show-template'])
            if sep:
                ret.insert(0, sep)
            ret.insert(0, template_node)
        return ret


class TagDirective(ObjectDescription):
    has_content = False
    optional_arguments = 1
    final_argument_whitespace = False

    def handle_signature(self, sig, signode):
        return sig

    def add_target_and_index(self, target, sig, signode):
        signode.clear()
        if len(self.arguments) > 1 and self.arguments[1]:
            node_id = make_id(
                self.env, self.state.document,
                '', self.arguments[1]
            )
        else:
            node_id = make_id(
                self.env, self.state.document,
                '', TARGET_IDS.get(target, target)
            )
            node = nodes.target()
            node['ids'].append(node_id)
            signode += node
            self.state.document.note_explicit_target(node)
        domain = self.env.get_domain(self.domain)
        domain.note_tag(target, self.env.docname, node_id)

    def run(self):
        indexnode, node = super().run()
        return [self.indexnode] + node.children[0].children


class ENYAMLDomain(domains.Domain):
    name = 'tmpl'
    label = 'ENYAML'
    directives = {
        'render': RenderDirective,
        'tag': TagDirective,
    }
    roles = {
        'tag': XRefRole(),
    }

    @property
    def tags(self):
        return self.data.setdefault('tags', {})

    def note_tag(self, name, docname, node_id):
        self.tags[name] = docname, node_id

    def resolve_xref(
        self, env, fromdocname, builder, typ, target, node, contnode
    ):
        if typ == 'tag':
            contnode.children[0] = nodes.Text(f'!{target}')
            try:
                todocname, node_id = self.tags[target]
            except KeyError:
                return None
            return make_refnode(
                builder, fromdocname, todocname,
                node_id, [contnode], f'{enyaml.TAG_PREFIX}{target}'
            )


def setup(app):
    app.add_domain(ENYAMLDomain)
