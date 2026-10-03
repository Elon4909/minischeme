"""打印模块：把值转换成文本。

- to_string(value)            写入式打印：字符串带引号、转义换行/制表符
- to_display_string(value)    display 式打印：字符串不带引号
"""

from value import Symbol, Nil, Pair, Procedure, NIL

_STRING_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\t": "\\t",
    "\r": "\\r",
}


def _escape_string(text):
    out = []
    for ch in text:
        out.append(_STRING_ESCAPES.get(ch, ch))
    return "".join(out)


def to_string(value):
    """值 -> 文本（顶层结果、字符串带引号）。"""
    if value is NIL or isinstance(value, Nil):
        return "()"
    if isinstance(value, bool):
        return "#t" if value else "#f"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _format_float(value)
    if isinstance(value, str):
        return '"' + _escape_string(value) + '"'
    if isinstance(value, Symbol):
        return value.name
    if isinstance(value, Pair):
        return _pair_to_string(value)
    if isinstance(value, Procedure):
        return "#<procedure>"
    return str(value)


def to_display_string(value):
    """display 用：字符串原样输出，其余同 to_string。"""
    if isinstance(value, str):
        return value
    return to_string(value)


def _format_float(value):
    """浮点格式化：整数值也保留 .0，保证是浮点写法。"""
    if value != value:  # NaN
        return "nan"
    if value in (float("inf"), float("-inf")):
        return "inf" if value > 0 else "-inf"
    text = repr(value)
    return text


def _pair_to_string(pair):
    """点对/列表打印：真列表用 (a b c)，非真列表用 (a b . c)。"""
    parts = []
    node = pair
    while isinstance(node, Pair):
        parts.append(to_string(node.car))
        node = node.cdr
    if node is NIL or isinstance(node, Nil):
        return "(" + " ".join(parts) + ")"
    # 非真列表：点对收尾
    return "(" + " ".join(parts) + " . " + to_string(node) + ")"
