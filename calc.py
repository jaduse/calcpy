import operator as op
import copy
import math

from enum import Enum
from functools import partial

ENV = dict()


def last(list):
    if not list:
        return None

    return list[-1]


def shift(a, b, dir):
    if not a.is_integer() or not b.is_integer():
        raise ValueError("Can't shift floats")

    return int(a) << int(b) if dir == "L" else int(a) >> int(b)


class TokenType(Enum):
    OPERATOR = 0
    NUMBER = 1
    LBRACKET = 3
    RBRACKET = 4


class Token:

    def __init__(self, type, value=None):
        self.type = type
        self.value = value

    def __repr__(self):
        return "Token({}, {})".format(self.type, self.value)

    @staticmethod
    def create(tok):

        if tok in ENV:
            operator = copy.copy(ENV[tok])

            if tok == "(":
                type = TokenType.LBRACKET
            elif tok == ")":
                type = TokenType.RBRACKET
            else:
                type = TokenType.OPERATOR

            return Token(type, operator)

        else:
            try:
                return Token(TokenType.NUMBER, float(tok))

            except ValueError:
                raise SyntaxError(
                    "Invalid value: {}".format(tok)) from ValueError


class Operator:

    def __init__(
            self, f_bin=None, f_un=None,
            *, priority=9, unary=False):

        self.f_bin = f_bin  # function for binary operation
        self.f_un = f_un  # function for unary operation
        self.priority = priority
        self.unary = unary

    def eval(self, *args):
        if self.unary:
            if not self.f_un:
                raise SyntaxError("Invalid syntax: Does not support unary op.")

            return self.f_un(*args)

        return self.f_bin(*args)


class Calcly:

    def __init__(self):
        # global environment
        ENV.update({
            "+": Operator(op.add, op.pos),
            "-": Operator(op.sub, op.neg),
            "*": Operator(op.mul, priority=8),
            "/": Operator(op.truediv, priority=8),
            "%": Operator(op.mod, priority=8),
            "^": Operator(op.pow, priority=7),
            "<<": Operator(partial(shift, dir="L"), priority=10),
            ">>": Operator(partial(shift, dir="R"), priority=10),
            "sin": Operator(None, math.sin),
            "cos": Operator(None, math.cos),
            "tan": Operator(None, math.tan),
            "sqrt": Operator(None, math.sqrt),
            "round": Operator(None, round),
            "abs": Operator(None, abs),
            "(": Operator(priority=11),
            ")": Operator()
        })

    def tokenize(self, src):
        for operator in ENV.keys():
            src = src.replace(operator, " {} ".format(operator))

        src = src.replace("(", " ( ").replace(")", " ) ")

        return [Token.create(t) for t in src.split()]

    def eval(self, tokens):
        stack = []
        rpn = []
        prev_token = TokenType.OPERATOR

        def rpn_add(token):
            rpn.append(token)

        def stack_push(token):
            stack.append(token)

        def stack_pop():
            return stack.pop()

        def resolve_lbracket(token):
            stack_push(token)

        def resolve_rbracket(token):
            while last(stack).type != TokenType.LBRACKET:
                rpn_add(stack_pop())

            stack_pop()  # pop left bracket

        def resolve_operator(operator):
            value = operator.value

            # check if previous token is not a NUMBER, change operator to
            # unary operator
            if prev_token != TokenType.NUMBER:
                value.unary = True

            if (stack and not value.unary and
                    value.priority >= last(stack).value.priority):
                rpn_add(stack_pop())

            operator.value = value

            stack_push(operator)

        resolvers = {
            TokenType.LBRACKET: resolve_lbracket,
            TokenType.RBRACKET: resolve_rbracket,
            TokenType.NUMBER: rpn_add,
            TokenType.OPERATOR: resolve_operator
        }

        for t in tokens:
            resolvers[t.type](t)
            prev_token = t.type

        while stack:
            rpn_add(stack_pop())

        return rpn

    def calc(self, src):
        # TODO refactor this
        tokens = self.tokenize(src)
        rpn = self.eval(tokens)
        stack = []

        def stack_pop(count=1):
            return [stack.pop() for _ in range(count)]

        def stack_push(value):
            stack.append(value)

        for t in rpn:
            if t.type == TokenType.OPERATOR:
                operator = t.value

                if operator.unary:
                    args = stack_pop()
                else:
                    b, a = stack_pop(2)
                    args = a, b

                stack_push(operator.eval(*args))

            else:
                stack_push(t.value)

        return stack_pop()
