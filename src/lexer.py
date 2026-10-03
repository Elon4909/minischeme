"""词法分析：把程序文本切成 token 列表。

token 以 (kind, value) 元组表示：
- ("LPAREN", None) ("RPAREN", None)   括号
- ("QUOTE", None)                     引用简写 '
- ("DOT", None)                       点对里的 `.`
- ("ATOM", value)                     已归类的基本值
                                      value 是 int / float / bool / str / Symbol
"""

from value import SchemeError, Symbol

# 转义字符表：\n \t \" \\ 等
_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    '"': '"',
    "\\": "\\",
}

_DELIMITERS = set("()'\" \t\r\n;")


def _is_number(text):
    """返回解析后的数字，无法解析则返回 None。"""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return None


def tokenize(text):
    """把源文本转换为 token 列表。"""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # 注释：; 到行尾
        if ch == ";":
            while i < n and text[i] != "\n":
                i += 1
        elif ch.isspace():
            i += 1
        elif ch == "(":
            tokens.append(("LPAREN", None))
            i += 1
        elif ch == ")":
            tokens.append(("RPAREN", None))
            i += 1
        elif ch == "'":
            tokens.append(("QUOTE", None))
            i += 1
        elif ch == '"':
            i += 1
            buf = []
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    buf.append(_ESCAPES.get(text[i + 1], text[i + 1]))
                    i += 2
                else:
                    buf.append(text[i])
                    i += 1
            if i >= n:
                raise SchemeError("unterminated string literal")
            i += 1  # 跳过收尾的引号
            tokens.append(("ATOM", "".join(buf)))
        else:
            # 原子：读取到下一个分隔符
            start = i
            while i < n and text[i] not in _DELIMITERS:
                i += 1
            word = text[start:i]
            tokens.append(("ATOM", _classify(word)))
    return tokens


def _classify(word):
    """把一段原子文本归类成数字 / 布尔 / 符号。"""
    if word == ".":
        # 单独的点（用于点对语法）在词法层特殊标记
        return DOT_TOKEN
    if word == "#t":
        return True
    if word == "#f":
        return False
    number = _is_number(word)
    if number is not None:
        return number
    return Symbol(word)


class _Dot:
    """内部占位：标记独立出现的 `.`，供 parser 识别点对。"""

    __slots__ = ()

    def __repr__(self):
        return "."


DOT_TOKEN = _Dot()
