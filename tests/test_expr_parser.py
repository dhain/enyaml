import pytest

from enyaml.expr.lexer import *
from enyaml.expr.parser import *
from enyaml.expr.expr import *


@pytest.fixture
def parser(request):
    marker = request.node.get_closest_marker('expression')
    return Parser(Lexer(marker.args[0]))


@pytest.fixture
def expr(parser):
    return parser.get_expr()


@pytest.mark.expression('')
def test_empty_expression(parser):
    with pytest.raises(ExprSyntaxError):
        parser.get_expr()


@pytest.mark.expression('()')
def test_empty_expression_paren(parser):
    with pytest.raises(ExprSyntaxError):
        parser.get_expr()


@pytest.mark.expression('1')
def test_bare_literal(expr):
    assert expr == Expression(NumberToken('1', 0, 1))


@pytest.mark.expression('(1)')
def test_paren_literal(expr):
    assert expr == Expression(NumberToken('1', 1, 2))


@pytest.mark.expression('-1')
def test_negation(expr):
    assert expr == NegExpression(
        Expression(NumberToken('1', 1, 2)),
    )


@pytest.mark.expression('--1')
def test_multiple_negations(expr):
    assert expr == NegExpression(
        NegExpression(
            Expression(NumberToken('1', 2, 3)),
        )
    )


@pytest.mark.expression('1+2')
def test_addition(expr):
    assert expr == AddExpression(
        Expression(NumberToken('1', 0, 1)),
        Expression(NumberToken('2', 2, 3))
    )


@pytest.mark.expression('1+2+3')
def test_multiple_additions(expr):
    assert expr == AddExpression(
        AddExpression(
            Expression(NumberToken('1', 0, 1)),
            Expression(NumberToken('2', 2, 3)),
        ),
        Expression(NumberToken('3', 4, 5)),
    )


@pytest.mark.expression('1+2*3')
def test_add_and_mult(expr):
    assert expr == AddExpression(
        Expression(NumberToken('1', 0, 1)),
        MultExpression(
            Expression(NumberToken('2', 2, 3)),
            Expression(NumberToken('3', 4, 5)),
        ),
    )


@pytest.mark.expression('1*2+3')
def test_mult_and_add(expr):
    assert expr == AddExpression(
        MultExpression(
            Expression(NumberToken('1', 0, 1)),
            Expression(NumberToken('2', 2, 3)),
        ),
        Expression(NumberToken('3', 4, 5)),
    )


@pytest.mark.expression('1*(2+3)')
def test_mult_and_add_paren(expr):
    assert expr == MultExpression(
        Expression(NumberToken('1', 0, 1)),
        AddExpression(
            Expression(NumberToken('2', 3, 4)),
            Expression(NumberToken('3', 5, 6)),
        ),
    )


@pytest.mark.expression('(1')
def test_missing_close_paren(parser):
    with pytest.raises(ExprSyntaxError):
        parser.get_expr()


@pytest.mark.expression('1)')
def test_missing_open_paren(parser):
    with pytest.raises(ExprSyntaxError):
        parser.get_expr()
