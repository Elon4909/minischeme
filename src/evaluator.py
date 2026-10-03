"""求值器：整个解释器的心脏。

evaluate(expr, env) 与 apply(proc, args) 互相递归：
表达式 -> 值；调用过程 -> 回到表达式求值函数体。
"""

from value import (
    BuiltinProcedure,
    LambdaProcedure,
    Pair,
    Procedure,
    Symbol,
    SchemeError,
    list_to_pair,
    is_true,
)


# ---------------------------------------------------------------------------
# 特殊形式
# ---------------------------------------------------------------------------
def _quote_to_data(node):
    """把"代码结构"原样转成"数据"：Python list -> 点对链。"""
    if isinstance(node, list):
        return list_to_pair([_quote_to_data(item) for item in node])
    if isinstance(node, Pair):
        return Pair(_quote_to_data(node.car), _quote_to_data(node.cdr))
    return node


def _sf_quote(args, env):
    if len(args) != 1:
        raise SchemeError("quote: expects exactly 1 argument")
    return _quote_to_data(args[0])


def _sf_if(args, env):
    if len(args) < 2:
        raise SchemeError("if: expects at least 2 arguments")
    if is_true(evaluate(args[0], env)):
        return evaluate(args[1], env)
    if len(args) > 2:
        return evaluate(args[2], env)
    return None


def _sf_cond(args, env):
    for clause in args:
        if not isinstance(clause, list) or len(clause) == 0:
            raise SchemeError("cond: malformed clause")
        test = clause[0]
        if isinstance(test, Symbol) and test.name == "else":
            return _eval_body(clause[1:], env)
        value = evaluate(test, env)
        if is_true(value):
            if len(clause) == 1:
                return value
            return _eval_body(clause[1:], env)
    return None


def _sf_and(args, env):
    result = True
    for expr in args:
        result = evaluate(expr, env)
        if result is False:
            return False
    return result


def _sf_or(args, env):
    for expr in args:
        result = evaluate(expr, env)
        if result is not False:
            return result
    return False


def _make_lambda(params, body, env, name="lambda"):
    for param in params:
        if not isinstance(param, Symbol):
            raise SchemeError("lambda: parameters must be symbols")
    return LambdaProcedure(params, body, env, name)


def _sf_define(args, env):
    target = args[0]
    if isinstance(target, Symbol):
        if len(args) != 2:
            raise SchemeError("define: expects (define name expr)")
        env.define(target.name, evaluate(args[1], env))
        return target
    if isinstance(target, list) and target:
        name = target[0]
        if not isinstance(name, Symbol):
            raise SchemeError("define: function name must be a symbol")
        proc = _make_lambda(target[1:], args[1:], env, name.name)
        env.define(name.name, proc)
        return name
    raise SchemeError("define: invalid target")


def _sf_lambda(args, env):
    if not args:
        raise SchemeError("lambda: expects parameters and a body")
    params = args[0]
    if not isinstance(params, list):
        raise SchemeError("lambda: parameter list must be a list")
    return _make_lambda(params, args[1:], env)


def _sf_let(args, env):
    if not args:
        raise SchemeError("let: expects bindings and a body")
    bindings = args[0]
    # 并行绑定：先在"外层环境"求值所有绑定表达式
    names = []
    values = []
    for binding in bindings:
        if not isinstance(binding, list) or len(binding) != 2:
            raise SchemeError("let: malformed binding")
        name = binding[0]
        if not isinstance(name, Symbol):
            raise SchemeError("let: binding name must be a symbol")
        names.append(name)
        values.append(evaluate(binding[1], env))
    child = env.extend(names, values)
    return _eval_body(args[1:], child)


def _sf_begin(args, env):
    return _eval_body(args, env)


_SPECIAL_FORMS = {
    "quote": _sf_quote,
    "if": _sf_if,
    "cond": _sf_cond,
    "and": _sf_and,
    "or": _sf_or,
    "define": _sf_define,
    "lambda": _sf_lambda,
    "let": _sf_let,
    "begin": _sf_begin,
}


# ---------------------------------------------------------------------------
# 求值 / 应用
# ---------------------------------------------------------------------------
def _eval_body(body, env):
    """按 begin 语义依次求值，返回最后一个；空体返回 None。"""
    result = None
    for expr in body:
        result = evaluate(expr, env)
    return result


def evaluate(expr, env):
    # 符号：查环境
    if isinstance(expr, Symbol):
        return env.lookup(expr.name)
    # 原子：数字/布尔/字符串原样返回
    if not isinstance(expr, list):
        if isinstance(expr, Pair):
            raise SchemeError("cannot evaluate a dotted pair")
        return expr
    # 组合式
    if len(expr) == 0:
        raise SchemeError("cannot evaluate the empty combination ()")
    head = expr[0]
    if isinstance(head, Symbol):
        handler = _SPECIAL_FORMS.get(head.name)
        if handler is not None:
            return handler(expr[1:], env)
    proc = evaluate(head, env)
    args = [evaluate(arg, env) for arg in expr[1:]]
    return apply_procedure(proc, args)


def apply_procedure(proc, args):
    if isinstance(proc, BuiltinProcedure):
        return proc.fn(args)
    if isinstance(proc, LambdaProcedure):
        child = proc.env.extend(proc.params, args)
        return _eval_body(proc.body, child)
    if isinstance(proc, Procedure):
        raise SchemeError("cannot apply this procedure")
    raise SchemeError("not a procedure: %r" % (proc,))


def run_program(forms, env, emit):
    """依次求值顶层表达式并即时输出结果，保证与 display 的输出顺序一致。

    emit(value) 由调用方提供，负责把非 None 的结果打印出去。
    """
    for form in forms:
        value = evaluate(form, env)
        if value is not None:
            emit(value)
