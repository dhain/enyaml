from .lexer import Lexer
from .parser import Parser


def parse(string):
    return Parser(Lexer(string)).get_expr()
