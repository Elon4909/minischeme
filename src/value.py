"""mini-Scheme 数据表示与基础类型。

本模块只负责"值长什么样"，不涉及求值逻辑：
- Symbol         符号（不是 str 子类，避免与字符串混为一谈）
- Nil / NIL       空表（单例）
- Pair            点对（cons 的产物，列表是点对链）
- Procedure 基类  可调用对象；内置过程与用户 lambda 各一个子类
- SchemeError     解释器运行期错误
"""


class SchemeError(Exception):
    """求值过程中出现的错误（未绑定符号、类型不符、参数个数错误等）。"""


class Symbol:
    """符号：表示"名字"。刻意不作为 str 的子类。"""

    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Symbol) and other.name == self.name

    def __hash__(self):
        return hash(("symbol", self.name))

    def __repr__(self):
        return "Symbol(%r)" % self.name


class Nil:
    """空表 `()` 的单例。列表链的终点，也是 `quote` 的结果之一。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "()"


NIL = Nil()


class Pair:
    """点对：car 是第一项，cdr 是第二项。列表即 (a . (b . (c . ())))。"""

    __slots__ = ("car", "cdr")

    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def __repr__(self):
        return "Pair(%r, %r)" % (self.car, self.cdr)


class Procedure:
    """所有可调用对象的基类，便于用 isinstance 统一判定 procedure?。"""

    __slots__ = ()


class BuiltinProcedure(Procedure):
    """内置过程：直接包装一个 Python 函数。"""

    __slots__ = ("name", "fn")

    def __init__(self, name, fn):
        self.name = name
        self.fn = fn


class LambdaProcedure(Procedure):
    """用户函数（闭包）：参数名、函数体、以及定义时捕获的环境。"""

    __slots__ = ("params", "body", "env", "name")

    def __init__(self, params, body, env, name="lambda"):
        self.params = params      # list[Symbol]
        self.body = body          # list[表达式]，按 begin 语义求值
        self.env = env            # 定义时的环境（闭包）
        self.name = name


def is_true(value):
    """Scheme 真值判断：只有 #f（Python False）为假，其余（含 0、'()、""）为真。"""
    return value is not False


def is_number(value):
    """数值判断（布尔在 Python 里是 int 子类，必须排除）。"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_nil(value):
    return value is NIL or isinstance(value, Nil)


def list_to_pair(items, tail=NIL):
    """Python 列表 -> 点对链（末尾接 tail），供 quote 与 list 使用。"""
    result = tail
    for item in reversed(items):
        result = Pair(item, result)
    return result


def pair_to_list(value):
    """点对链 -> Python 列表；要求是真列表，否则抛 SchemeError。"""
    items = []
    node = value
    while isinstance(node, Pair):
        items.append(node.car)
        node = node.cdr
    if not is_nil(node):
        raise SchemeError("expected a proper list")
    return items


def is_proper_list(value):
    """判断是否为真列表（含空表）。"""
    node = value
    while isinstance(node, Pair):
        node = node.cdr
    return is_nil(node)
