# Copyright (c) 2022, Sadie Hain. All rights reserved.
# Released under the BSD 3-Clause License
# https://enyaml.org/LICENSE

import sys
import argparse
from . import *


parser = argparse.ArgumentParser(
    description='Render YAML templates.')
parser.add_argument(
    'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
parser.add_argument(
    '--outfile', '-o', type=argparse.FileType('w'), default=sys.stdout)


if __name__ == '__main__':
    opts = parser.parse_args()
    ctx = Context()
    dump_all(render_all(opts.infile, ctx), opts.outfile)
