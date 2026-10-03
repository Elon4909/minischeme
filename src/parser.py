"""语法分析：把 token 列表组装成嵌套的表达式结构。

表示方式：
- 数字/布尔/字符串 -> 对应的 Python 值
- 符号            -> Symbol
- 代码里的组合式   -> Python list（如 [+ 1 2] 表示 (+ 1 2)）
- 点对写法 (a . b) -> 直接构造成 Pair（供 quote 使用）
"""

from lexer import tokenize, DOT_TOKEN
from value import Pair, Symbol, SchemeError, NIL


class Parser:
    """递归下降解析器。"""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse_all(self):
        """解析出全部顶层表达式。"""
        forms = []
        while self.peek() is not None:
            forms.append(self.parse_expr())
        return forms

    def parse_expr(self):
        kind, value = self.advance()
        if kind == "LPAREN":
            return self.parse_list()
        if kind == "RPAREN":
            raise SchemeError("unexpected ')'")
        if kind == "QUOTE":
            return [Symbol("quote"), self.parse_expr()]
        # ATOM
        if value is DOT_TOKEN:
            raise SchemeError("unexpected '.'")
        return value

    def parse_list(self):
        items = []
        while True:
            token = self.peek()
            if token is None:
                raise SchemeError("unexpected end of input: missing ')'")
            kind, value = token
            if kind == "RPAREN":
                self.advance()
                return items
            if kind == "ATOM" and value is DOT_TOKEN:
                # 点对写法 (a b . c)：解析尾部后结束
                self.advance()
                tail = self.parse_expr()
                closing = self.peek()
                if closing is None or closing[0] != "RPAREN":
                    raise SchemeError("expected ')' after dotted tail")
                self.advance()
                return _make_dotted(items, tail)
            items.append(self.parse_expr())


def _make_dotted(items, tail):
    """把 [a, b] 与尾 c 组成 (a . (b . c)) 的点对链。"""
    result = tail
    for item in reversed(items):
        result = Pair(item, result)
    return result


def parse(text):
    """便捷入口：文本 -> 顶层表达式列表。"""
    return Parser(tokenize(text)).parse_all()
