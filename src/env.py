"""环境模块：变量绑定表 + 指向外层环境的指针（实现词法作用域）。"""

from value import SchemeError, Symbol


class Env:
    """一层环境。lookup 沿 parent 链向上查找，实现词法作用域与闭包。"""

    __slots__ = ("vars", "parent")

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def lookup(self, name):
        """按符号名查找绑定；找不到抛 SchemeError。"""
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise SchemeError("unbound symbol: %s" % name)

    def define(self, name, value):
        """在当前层新增/覆盖绑定。"""
        self.vars[name] = value
        return value

    def extend(self, names, values):
        """为一次函数调用新建子环境，把实参绑定到形参名。"""
        if len(names) != len(values):
            raise SchemeError(
                "argument count mismatch: expected %d, got %d"
                % (len(names), len(values))
            )
        child = Env(self)
        for name, value in zip(names, values):
            # 形参可能是 Symbol 或字符串，统一以符号名（字符串）作键
            key = name.name if isinstance(name, Symbol) else name
            child.vars[key] = value
        return child
