from .errors import ExprSyntaxError
from .lexer import Lexer, OpToken, OpenParenToken, CloseParenToken, \
    IdentifierToken, NumberToken, StringToken
from .expr import Expression, UnaryOpExpression, BinaryOpExpression, \
    TernaryOpExpression, DotExpression, lookup_precedence


class Parser:
    def __init__(self, tokens, string=None):
        self.string = string or getattr(tokens, 'string', None)
        self.tokens = tokens
        self.token_iter = iter(tokens)
        self.token = None

    def syntax_error(self, msg=None, offset=None, text=None):
        if text is None:
            text = self.string
        if offset is None and text is not None:
            offset = getattr(self.token, 'start_pos', len(text))
        return ExprSyntaxError(msg, offset, text)

    def check_token(self, *classes):
        if self.token is None:
            self.token = next(self.token_iter, None)
        if self.token is None:
            return False
        if not classes:
            return True
        for cls in classes:
            if isinstance(self.token, cls):
                return True
        return False

    def peek_token(self):
        if self.check_token():
            return self.token

    def get_token(self):
        if self.check_token():
            token = self.token
            self.token = None
            return token

    def get_expr(self):
        expr = self.get_sub_expr()
        if self.check_token():
            raise self.syntax_error('expecting single expression')
        return expr

    def get_sub_expr(self, precedence=0):
        lhs = self.handle_head()
        while lookup_precedence(self.peek_token()) > precedence:
            lhs = self.handle_tail(lhs)
        if lhs is None:
            raise self.syntax_error('expecting expression')
        return lhs

    def handle_head(self):
        if self.check_token(IdentifierToken, NumberToken, StringToken):
            return self.handle_literal()
        elif self.check_token(OpToken):
            return self.handle_unary_op()
        elif self.check_token(OpenParenToken):
            return self.handle_paren()
        elif self.check_token(CloseParenToken):
            raise self.syntax_error('closing parenthesis without opening')

    def handle_tail(self, lhs):
        if self.check_token(IdentifierToken, NumberToken, StringToken):
            return self.handle_literal()
        elif self.check_token(OpToken):
            if self.token.value in TernaryOpExpression._cls_map:
                return self.handle_ternary_op(lhs)
            return self.handle_binary_op(lhs)
        elif self.check_token(OpenParenToken):
            return self.handle_paren()

    def handle_paren(self):
        self.token = None
        expr = self.get_sub_expr()
        if not self.check_token(CloseParenToken):
            raise self.syntax_error('expecting closing parenthesis')
        self.token = None
        return expr

    def handle_literal(self):
        token = self.token
        self.token = None
        return Expression(token)

    def handle_unary_op(self):
        cls = UnaryOpExpression.lookup(self.token)
        if cls is None:
            raise self.syntax_error('not a unary operator')
        self.token = None
        return cls(self.get_sub_expr(cls.precedence))

    def handle_binary_op(self, lhs):
        cls = BinaryOpExpression.lookup(self.token)
        if cls is None:
            raise self.syntax_error('not a binary operator')
        self.token = None
        if (
            issubclass(cls, DotExpression)
            and not self.check_token(IdentifierToken)
        ):
            raise self.syntax_error('expecting identifier')
        return cls(lhs, self.get_sub_expr(cls.precedence))

    def handle_ternary_op(self, lhs):
        cls = TernaryOpExpression.lookup(self.token)
        if cls is None:
            raise self.syntax_error('not a ternary operator')
        self.token = None
        middle = self.get_sub_expr(cls.precedence)
        if self.check_token(OpToken) and self.token.value == cls.sep:
            self.token = None
            rhs = self.get_sub_expr(cls.precedence)
        else:
            raise self.syntax_error(f'expecting {cls.sep}')
        return cls(lhs, middle, rhs)


if __name__ == '__main__':
    import traceback
    while True:
        try:
            parser = Parser(Lexer(input()))
            print(parser.get_expr())
        except ExprSyntaxError:
            traceback.print_exc()
