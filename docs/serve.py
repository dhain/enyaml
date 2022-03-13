#!python3
import os
import http.server
import socketserver

DIRECTORY = 'build/html'

class DocRequestHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        '': 'application/octet-stream',
        '.manifest': 'text/cache-manifest',
        '.html': 'text/html',
        '.png': 'image/png',
        '.jpg': 'image/jpg',
        '.svg':	'image/svg+xml',
        '.css':	'text/css',
        '.js':'application/x-javascript',
        '.wasm': 'application/wasm',
        '.json': 'application/json',
        '.xml': 'application/xml',
    }

    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = DIRECTORY
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
    http.server.test(HandlerClass=DocRequestHandler, port=8080)
