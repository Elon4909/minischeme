"""内置过程库：spec §5 的全部标准函数，放进初始全局环境。

约定：内置过程一律"参数先求值再调用"（由求值器保证）。
"""

import sys

from env import Env
from value import (
    BuiltinProcedure,
    Pair,
    Procedure,
    Symbol,
    SchemeError,
    NIL,
    is_number,
    is_nil,
    is_proper_list,
    list_to_pair,
    pair_to_list,
)


# ---------------------------------------------------------------------------
# 参数校验辅助
# ---------------------------------------------------------------------------
def _require_number(value, who):
    if not is_number(value):
        raise SchemeError("%s: not a number: %r" % (who, value))
    return value


def _require_all_numbers(args, who):
    for value in args:
        _require_number(value, who)
    return args


def _require_pair(value, who):
    if not isinstance(value, Pair):
        raise SchemeError("%s: not a pair: %r" % (who, value))
    return value


# ---------------------------------------------------------------------------
# 算术
# ---------------------------------------------------------------------------
def _trunc_div(a, b):
    """整数除法，商向零截断。"""
    if b == 0:
        raise SchemeError("division by zero")
    quotient = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        quotient = -quotient
    return quotient


def _add(args):
    _require_all_numbers(args, "+")
    return sum(args)


def _sub(args):
    _require_all_numbers(args, "-")
    if not args:
        raise SchemeError("-: needs at least one argument")
    if len(args) == 1:
        return -args[0]
    result = args[0]
    for value in args[1:]:
        result -= value
    return result


def _mul(args):
    _require_all_numbers(args, "*")
    result = 1
    for value in args:
        result *= value
    return result


def _div(args):
    _require_all_numbers(args, "/")
    if not args:
        raise SchemeError("/: needs at least one argument")
    if len(args) == 1:
        return 1 / args[0]          # 单参数：求倒数（浮点）
    if all(isinstance(v, int) for v in args):
        result = args[0]
        for value in args[1:]:
            result = _trunc_div(result, value)
        return result
    result = args[0]
    for value in args[1:]:
        result = result / value
    return result


def _modulo(args):
    a, b = args
    _require_all_numbers(args, "modulo")
    if b == 0:
        raise SchemeError("modulo: division by zero")
    return a % b                    # Python % 与 Scheme modulo 同符号规则


def _quotient(args):
    a, b = args
    _require_all_numbers(args, "quotient")
    return _trunc_div(a, b)


def _expt(args):
    a, b = args
    _require_all_numbers(args, "expt")
    return a ** b


def _abs(args):
    (value,) = args
    _require_number(value, "abs")
    return abs(value)


# ---------------------------------------------------------------------------
# 比较（链式）
# ---------------------------------------------------------------------------
def _cmp_key(value, who):
    if is_number(value):
        return ("num", value)
    if isinstance(value, Symbol):
        return ("sym", value.name)
    raise SchemeError("%s: cannot compare %r" % (who, value))


def _chain(op, args, who):
    keys = [_cmp_key(v, who) for v in args]
    for left, right in zip(keys, keys[1:]):
        if left[0] != right[0]:
            raise SchemeError("%s: type mismatch" % who)
        if not op(left[1], right[1]):
            return False
    return True


# ---------------------------------------------------------------------------
# 布尔
# ---------------------------------------------------------------------------
def _not(args):
    (value,) = args
    return value is False


# ---------------------------------------------------------------------------
# 列表
# ---------------------------------------------------------------------------
def _cons(args):
    a, b = args
    return Pair(a, b)


def _car(args):
    (value,) = args
    return _require_pair(value, "car").car


def _cdr(args):
    (value,) = args
    return _require_pair(value, "cdr").cdr


def _list(args):
    return list_to_pair(args)


def _length(args):
    (value,) = args
    return len(pair_to_list(value))


def _append(args):
    if not args:
        return NIL
    result = args[-1]
    for value in reversed(args[:-1]):
        result = list_to_pair(pair_to_list(value), result)
    return result


def _null_p(args):
    (value,) = args
    return is_nil(value)


def _pair_p(args):
    (value,) = args
    return isinstance(value, Pair)


def _list_p(args):
    (value,) = args
    return is_nil(value) or is_proper_list(value)


# ---------------------------------------------------------------------------
# 谓词
# ---------------------------------------------------------------------------
def _number_p(args):
    return is_number(args[0])


def _boolean_p(args):
    return isinstance(args[0], bool)


def _symbol_p(args):
    return isinstance(args[0], Symbol)


def _string_p(args):
    return isinstance(args[0], str)


def _procedure_p(args):
    return isinstance(args[0], Procedure)


def _zero_p(args):
    return _require_number(args[0], "zero?") == 0


def _even_p(args):
    return _require_number(args[0], "even?") % 2 == 0


def _odd_p(args):
    return _require_number(args[0], "odd?") % 2 != 0


def _eq(a, b):
    """eq?：符号/数字/布尔按值比较；复合数据按同一性。"""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if is_number(a) and is_number(b):
        return a == b
    if isinstance(a, Symbol) or isinstance(b, Symbol):
        return isinstance(a, Symbol) and isinstance(b, Symbol) and a.name == b.name
    if is_nil(a) or is_nil(b):
        return is_nil(a) and is_nil(b)
    return a is b


def _eq_p(args):
    a, b = args
    return _eq(a, b)


def _equal(a, b):
    """equal?：结构相等，且区分类型（布尔≠数字，符号≠字符串）。"""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if is_number(a) or is_number(b):
        return is_number(a) and is_number(b) and a == b
    if isinstance(a, Symbol) or isinstance(b, Symbol):
        return isinstance(a, Symbol) and isinstance(b, Symbol) and a.name == b.name
    if isinstance(a, str) or isinstance(b, str):
        return isinstance(a, str) and isinstance(b, str) and a == b
    if is_nil(a) or is_nil(b):
        return is_nil(a) and is_nil(b)
    if isinstance(a, Pair) and isinstance(b, Pair):
        return _equal(a.car, b.car) and _equal(a.cdr, b.cdr)
    return a is b


def _equal_p(args):
    a, b = args
    return _equal(a, b)


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------
def _display(args):
    from printer import to_display_string

    (value,) = args
    sys.stdout.write(to_display_string(value))
    return None


def _newline(args):
    sys.stdout.write("\n")
    return None


# ---------------------------------------------------------------------------
# 注册表
# ---------------------------------------------------------------------------
_BUILTINS = {
    "+": _add,
    "-": _sub,
    "*": _mul,
    "/": _div,
    "modulo": _modulo,
    "quotient": _quotient,
    "expt": _expt,
    "abs": _abs,
    "=": lambda args: _chain(lambda a, b: a == b, args, "="),
    "<": lambda args: _chain(lambda a, b: a < b, args, "<"),
    ">": lambda args: _chain(lambda a, b: a > b, args, ">"),
    "<=": lambda args: _chain(lambda a, b: a <= b, args, "<="),
    ">=": lambda args: _chain(lambda a, b: a >= b, args, ">="),
    "not": _not,
    "cons": _cons,
    "car": _car,
    "cdr": _cdr,
    "list": _list,
    "length": _length,
    "append": _append,
    "null?": _null_p,
    "pair?": _pair_p,
    "list?": _list_p,
    "number?": _number_p,
    "boolean?": _boolean_p,
    "symbol?": _symbol_p,
    "string?": _string_p,
    "procedure?": _procedure_p,
    "zero?": _zero_p,
    "even?": _even_p,
    "odd?": _odd_p,
    "eq?": _eq_p,
    "equal?": _equal_p,
    "display": _display,
    "newline": _newline,
}


def standard_env():
    """构建含全部内置过程的初始环境。"""
    env = Env()
    for name, fn in _BUILTINS.items():
        env.define(name, BuiltinProcedure(name, fn))
    return env
