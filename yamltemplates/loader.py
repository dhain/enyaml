__all__ = [
    'TemplateLoader',
]

import yaml


class TemplateLoader(yaml.SafeLoader):
    def construct_document(self, node):
        return self.yaml_constructors['!tmpl'](self, node)

    def clear_constructed_nodes(self, node):
        try:
            del self.constructed_objects[node]
        except KeyError as k:
            pass
        if hasattr(node, 'value'):
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
