from .errors import ExprSyntaxError


class Token:
    def __init__(self, value, start_pos, end_pos):
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos

    def __repr__(self):
        return (
            f'{self.__class__.__name__}({self.value!r}, '
            f'{self.start_pos}, {self.end_pos})'
        )

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and other.value == self.value
            and other.start_pos == self.start_pos
            and other.end_pos == self.end_pos
        )


class IdentifierToken(Token): pass      # noqa: E701
class NumberToken(Token): pass          # noqa: E701


class OpToken(Token):
    valid_operators = {
        '.', '^', '*', '/', '//', '%', '+', '-',
        '<', '>', '<=', '>=', '==', '!=', '=',
        'and', 'or', 'if', 'else', 'not',
    }

    def __new__(cls, value, start_pos, end_pos):
        if value not in cls.valid_operators:
            raise TypeError(f'unknown operator: {value}')
        return super().__new__(cls)


class GroupingToken(Token):
    def __new__(cls, value, start_pos, end_pos):
        return super().__new__(cls.__class_map[value])


class OpenGroupingToken(GroupingToken):
    def opens(self, other):
        return isinstance(other, self.closer)


class CloseGroupingToken(GroupingToken):
    def closes(self, other):
        return isinstance(other, self.opener)


class OpenParenToken(OpenGroupingToken): pass       # noqa: E701
class OpenBracketToken(OpenGroupingToken): pass     # noqa: E701
class OpenBraceToken(OpenGroupingToken): pass       # noqa: E701
class CloseParenToken(CloseGroupingToken): pass     # noqa: E701
class CloseBracketToken(CloseGroupingToken): pass   # noqa: E701
class CloseBraceToken(CloseGroupingToken): pass     # noqa: E701


OpenParenToken.closer = CloseParenToken
OpenBracketToken.closer = CloseBracketToken
OpenBraceToken.closer = CloseBraceToken
CloseParenToken.opener = OpenParenToken
CloseBracketToken.opener = OpenBracketToken
CloseBraceToken.opener = OpenBraceToken
GroupingToken._GroupingToken__class_map = {
    '(': OpenParenToken,
    '[': OpenBracketToken,
    '{': OpenBraceToken,
    ')': CloseParenToken,
    ']': CloseBracketToken,
    '}': CloseBraceToken,
}


class StringToken(Token):
    def __init__(self, value, start_pos, end_pos, style=None):
        super().__init__(value, start_pos, end_pos)
        self.style = style


class Lexer:
    def __init__(self, string):
        self.string = string
        self.pos = 0

    def __iter__(self):
        return self

    def syntax_error(self, msg=None, offset=None, text=None):
        if offset is None:
            offset = self.pos
        if text is None:
            text = self.string
        return ExprSyntaxError(msg, offset, text)

    def check_token(self):
        return self.pos < len(self.string)

    def get_token(self):
        return next(self, None)

    def __next__(self):
        lookbehind = None
        try:
            while self.string[self.pos].isspace():
                lookbehind = self.string[self.pos]
                self.pos += 1
            ch = self.string[self.pos]
        except IndexError:
            raise StopIteration()
        if ch.isalpha() or ch == '_':
            return self.get_identifier_token(lookbehind)
        if ch.isdecimal() or ch == '.':
            return self.get_num_token()
        if ch in '~%^*-+/<>=:!':
            return self.get_op_token()
        if ch in '"' "'":
            return self.get_string_token()
        if ch in '[({})]':
            return self.get_group_token()
        raise self.syntax_error('illegal character')

    def get_identifier_token(self, lookbehind):
        start_pos = self.pos
        self.pos += 1
        while self.pos < len(self.string):
            ch = self.string[self.pos]
            if not (ch.isalnum() or ch == '_'):
                break
            self.pos += 1
        value = self.string[start_pos:self.pos]
        if value in OpToken.valid_operators:
            if not (
                lookbehind is None
                or lookbehind.isspace()
                or lookbehind in '[({'
            ):
                raise self.syntax_error('syntax error', start_pos)
            if not ch.isspace():
                raise self.syntax_error('expecting whitespace')
            return OpToken(value, start_pos, self.pos)
        return IdentifierToken(value, start_pos, self.pos)

    def get_num_token(self):
        start_pos = self.pos
        has_dot = False
        while self.pos < len(self.string):
            ch = self.string[self.pos]
            if ch == '.':
                if has_dot:
                    raise self.syntax_error('invalid syntax')
                has_dot = True
            elif not ch.isdecimal():
                break
            self.pos += 1
        value = self.string[start_pos:self.pos]
        if value == '.':
            return OpToken(value, start_pos, self.pos)
        return NumberToken(value, start_pos, self.pos)

    def get_op_token(self):
        start_pos = self.pos
        self.pos += 2
        op = self.string[start_pos:self.pos]
        if op not in OpToken.valid_operators:
            self.pos -= 1
            op = self.string[start_pos:self.pos]
        try:
            return OpToken(op, start_pos, self.pos)
        except TypeError:
            raise self.syntax_error('unknown operator', start_pos)

    def get_string_token(self):
        style = self.string[self.pos]
        start_pos = self.pos
        ppos = self.pos = start_pos + 1
        parts = []
        while self.pos < len(self.string):
            ch = self.string[self.pos]
            if ch == '\\':
                parts.append(self.string[ppos:self.pos])
                parts.append(self.handle_esc(style))
                ppos = self.pos
                continue
            elif ch == style:
                parts.append(self.string[ppos:self.pos])
                self.pos += 1
                break
            self.pos += 1
        else:
            raise self.syntax_error('EOL while scanning string')
        return StringToken(''.join(parts), start_pos, self.pos, style)

    def handle_esc(self, style):
        ch = self.string[self.pos + 1]
        try:
            str_or_handler = self._esc[style][ch]
        except KeyError:
            return self.handle_unknown_escape(style, ch)
        self.pos += 2
        if isinstance(str_or_handler, str):
            return str_or_handler
        return str_or_handler.__get__(self, self.__class__)()

    def handle_unknown_escape(self, style, ch):
        if style == "'":
            start_pos = self.pos
            self.pos += 2
            return self.string[start_pos:self.pos]
        self.pos += 1
        raise self.syntax_error('invalid escape')

    def handle_hex_esc(self):
        start_pos = self.pos
        self.pos += 2
        hexdigits = self.string[start_pos:self.pos]     # noqa: F841
        raise NotImplementedError()

    def handle_u16_esc(self):
        start_pos = self.pos
        self.pos += 4
        hexdigits = self.string[start_pos:self.pos]     # noqa: F841
        raise NotImplementedError()

    def handle_u32_esc(self):
        start_pos = self.pos
        self.pos += 8
        hexdigits = self.string[start_pos:self.pos]     # noqa: F841
        raise NotImplementedError()

    def handle_uname_esc(self):
        start_pos = self.pos                            # noqa: F841
        raise NotImplementedError()

    _esc = {
        '"': {
            'n': '\n',
            't': '\t',
            '\\': '\\',
            '"': '"',
            'x': handle_hex_esc,
            'u': handle_u16_esc,
            'U': handle_u32_esc,
            'N': handle_uname_esc,
        },
        "'": {
            "'": "'",
        },
    }

    def get_group_token(self):
        start_pos = self.pos
        ch = self.string[start_pos]
        self.pos += 1
        return GroupingToken(ch, start_pos, self.pos)


if __name__ == '__main__':
    import traceback
    while True:
        try:
            print(list(Lexer(input())))
        except ExprSyntaxError:
            traceback.print_exc()
