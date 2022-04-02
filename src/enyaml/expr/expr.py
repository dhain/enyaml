from .lexer import OpToken, IdentifierToken, NumberToken, StringToken


class Expression:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'{self.__class__.__name__}({self.value!r})'

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return (
            isinstance(other, Expression)
            and hasattr(other, 'value')
            and other.value == self.value
        )

    def evaluate(self, ctx):
        if isinstance(self.value, NumberToken):
            if '.' in self.value.value:
                return float(self.value.value)
            return int(self.value.value)
        elif isinstance(self.value, StringToken):
            return self.value.value
        elif isinstance(self.value, IdentifierToken):
            return ctx[self.value.value]
        elif isinstance(self.value, Expression):
            return self.value.evaluate(ctx)


class OpExpression(Expression):
    @classmethod
    def lookup(cls, token):
        if isinstance(token, OpToken):
            return cls._cls_map.get(token.value)

    def __repr__(self):
        operands = ', '.join(repr(op) for op in self.operands())
        return f'{self.__class__.__name__}({operands})'


class UnaryOpExpression(OpExpression):
    def __init__(self, rhs=None):
        self.rhs = rhs

    def operands(self, idx=None):
        operands = (self.rhs,)
        if idx is None:
            return operands
        return operands[idx]

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and other.rhs == self.rhs
        )


class BinaryOpExpression(OpExpression):
    def __init__(self, lhs=None, rhs=None):
        self.lhs = lhs
        self.rhs = rhs

    def operands(self, idx=None):
        operands = (self.lhs, self.rhs)
        if idx is None:
            return operands
        return operands[idx]

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and other.lhs == self.lhs
            and other.rhs == self.rhs
        )


class TernaryOpExpression(OpExpression):
    def __init__(self, lhs=None, middle=None, rhs=None):
        self.lhs = lhs
        self.middle = middle
        self.rhs = rhs

    def operands(self, idx=None):
        operands = (self.lhs, self.middle, self.rhs)
        if idx is None:
            return operands
        return operands[idx]

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and other.lhs == self.lhs
            and other.middle == self.middle
            and other.rhs == self.rhs
        )


class DotExpression(BinaryOpExpression):
    precedence = 11

    def __str__(self):
        return f'({self.lhs}.{self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx)[self.rhs.value]


class PowExpression(BinaryOpExpression):
    precedence = 10

    def __str__(self):
        return f'({self.lhs} ^ {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) ** self.rhs.evaluate(ctx)


class PosExpression(UnaryOpExpression):
    precedence = 9

    def __str__(self):
        return f'(+{self.rhs})'

    def evaluate(self, ctx):
        return +self.rhs.evaluate(ctx)


class NegExpression(UnaryOpExpression):
    precedence = 9

    def __str__(self):
        return f'(-{self.rhs})'

    def evaluate(self, ctx):
        return -self.rhs.evaluate(ctx)


class MultExpression(BinaryOpExpression):
    precedence = 8

    def __str__(self):
        return f'({self.lhs} * {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) * self.rhs.evaluate(ctx)


class DivExpression(BinaryOpExpression):
    precedence = 8

    def __str__(self):
        return f'({self.lhs} / {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) / self.rhs.evaluate(ctx)


class FloorDivExpression(BinaryOpExpression):
    precedence = 8

    def __str__(self):
        return f'({self.lhs} // {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) // self.rhs.evaluate(ctx)


class ModExpression(BinaryOpExpression):
    precedence = 8

    def __str__(self):
        return f'({self.lhs} % {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) % self.rhs.evaluate(ctx)


class AddExpression(BinaryOpExpression):
    precedence = 7

    def __str__(self):
        return f'({self.lhs} + {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) + self.rhs.evaluate(ctx)


class SubtractExpression(BinaryOpExpression):
    precedence = 7

    def __str__(self):
        return f'({self.lhs} - {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) - self.rhs.evaluate(ctx)


class LtExpression(BinaryOpExpression):
    precedence = 6

    def __str__(self):
        return f'({self.lhs} < {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) < self.rhs.evaluate(ctx)


class GtExpression(BinaryOpExpression):
    precedence = 6

    def __str__(self):
        return f'({self.lhs} > {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) > self.rhs.evaluate(ctx)


class LeExpression(BinaryOpExpression):
    precedence = 6

    def __str__(self):
        return f'({self.lhs} <= {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) <= self.rhs.evaluate(ctx)


class GeExpression(BinaryOpExpression):
    precedence = 6

    def __str__(self):
        return f'({self.lhs} >= {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) >= self.rhs.evaluate(ctx)


class EqExpression(BinaryOpExpression):
    precedence = 6

    def __str__(self):
        return f'({self.lhs} == {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) == self.rhs.evaluate(ctx)


class NeExpression(BinaryOpExpression):
    precedence = 6

    def __str__(self):
        return f'({self.lhs} != {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) != self.rhs.evaluate(ctx)


class InExpression(BinaryOpExpression):
    precedence = 6

    def __str__(self):
        return f'({self.lhs} in {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) in self.rhs.evaluate(ctx)


class NotInExpression(BinaryOpExpression):
    precedence = 6

    def __str__(self):
        return f'({self.lhs} not in {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) not in self.rhs.evaluate(ctx)


class NotExpression(UnaryOpExpression):
    precedence = 5

    def __str__(self):
        return f'(not {self.rhs})'

    def evaluate(self, ctx):
        return not self.rhs.evaluate(ctx)


class AndExpression(BinaryOpExpression):
    precedence = 4

    def __str__(self):
        return f'({self.lhs} and {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) and self.rhs.evaluate(ctx)


class OrExpression(BinaryOpExpression):
    precedence = 3

    def __str__(self):
        return f'({self.lhs} or {self.rhs})'

    def evaluate(self, ctx):
        return self.lhs.evaluate(ctx) or self.rhs.evaluate(ctx)


class IfExpression(TernaryOpExpression):
    precedence = 1
    sep = 'else'

    def __str__(self):
        return f'({self.lhs} if {self.middle} else {self.rhs})'

    def evaluate(self, ctx):
        return (
            self.lhs.evaluate(ctx)
            if self.middle.evaluate(ctx)
            else self.rhs.evaluate(ctx)
        )


class AssignExpression(BinaryOpExpression):
    precedence = 0

    def __str__(self):
        return f'({self.lhs} = {self.rhs})'

    def evaluate(self, ctx):
        raise NotImplementedError()


UnaryOpExpression._cls_map = {
    '+': PosExpression,
    '-': NegExpression,
    'not': NotExpression,
}

BinaryOpExpression._cls_map = {
    '.': DotExpression,
    '^': PowExpression,
    '*': MultExpression,
    '/': DivExpression,
    '//': FloorDivExpression,
    '%': ModExpression,
    '+': AddExpression,
    '-': SubtractExpression,
    '<': LtExpression,
    '>': GtExpression,
    '<=': LeExpression,
    '>=': GeExpression,
    '==': EqExpression,
    '!=': NeExpression,
    'and': AndExpression,
    'or': OrExpression,
    '=': AssignExpression,
}

TernaryOpExpression._cls_map = {
    'if': IfExpression,
}


def lookup_precedence(token):
    if not isinstance(token, OpToken):
        return 0
    if token.value in TernaryOpExpression._cls_map:
        cls = TernaryOpExpression.lookup(token)
    else:
        cls = BinaryOpExpression.lookup(token)
    return 0 if cls is None else cls.precedence
