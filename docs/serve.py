#!python3
import os
import re
import shlex
import http.server
import socketserver
import subprocess

SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))
BUILDDIR = os.path.join(SCRIPTDIR, 'build')
WATCH_DIRS = ' '.join(shlex.quote(i) for i in [
    SCRIPTDIR,
    os.path.abspath(os.path.join(SCRIPTDIR, '..', 'enyaml')),
])
EXCLUDES = ' '.join(f'-e {shlex.quote(i)}' for i in [
    f'^{re.escape(BUILDDIR)}',
    r'__pycache__',
])
WATCH_COMMAND = \
    f'fswatch -orE {EXCLUDES} {WATCH_DIRS} | xargs -n1 -I{{}} make html doctest'


class DocRequestHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        '': 'application/octet-stream',
        '.manifest': 'text/cache-manifest',
        '.html': 'text/html',
        '.png': 'image/png',
        '.jpg': 'image/jpg',
        '.svg': 'image/svg+xml',
        '.css': 'text/css',
        '.js': 'application/x-javascript',
        '.wasm': 'application/wasm',
        '.json': 'application/json',
        '.xml': 'application/xml',
    }

    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = os.path.join(BUILDDIR, 'html')
        super().__init__(*args, directory=directory, **kwargs)

    def translate_path(self, path):
        path = super().translate_path(path)
        if not path.endswith('/') and not os.path.exists(path):
            for ext in self.extensions_map:
                test = ''.join((path, ext))
                if os.path.exists(test):
                    path = test
                    break
        return path


if __name__ == '__main__':
    print(WATCH_COMMAND)
    watcher = subprocess.Popen(WATCH_COMMAND, shell=True)
    try:
        http.server.test(HandlerClass=DocRequestHandler, port=8080)
    finally:
        watcher.terminate()
        watcher.wait()
