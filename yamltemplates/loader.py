__all__ = [
    'TemplateLoader',
]

import yaml


class TemplateLoader(yaml.SafeLoader):
    def construct_document(self, node):
        return self.template_base_class.from_yaml(self, None, node)
