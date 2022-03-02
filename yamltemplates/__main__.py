import sys
from . import *


yaml.dump_all(
    render_all(yaml.load_all(open(sys.argv[1]), Loader=TemplateLoader)),
    sys.stdout, Dumper=TemplateDumper)
