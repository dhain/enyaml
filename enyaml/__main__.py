import sys
import argparse
from . import *


parser = argparse.ArgumentParser(
    description='Render YAML templates.')
parser.add_argument(
    'file', nargs='?', type=argparse.FileType('r'), default=sys.stdin)


opts = parser.parse_args()
ctx = Context()
loader = TemplateLoader(opts.file)
yaml.dump_all(loader.render_all(ctx), sys.stdout, Dumper=TemplateDumper)
