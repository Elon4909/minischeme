"""mini-Scheme 解释器入口。

用法：
    python3 main.py file1.scm [file2.scm ...]
    python3 main.py < program.scm

约定见 spec §2：按顺序求值每个顶层表达式，非 None 的结果独占一行打印；
多个文件共享同一个全局环境。
"""

import importlib.util
import os
import sys

# 保证 src/ 目录在模块搜索路径上（同一目录下的模块可直接 import）
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from evaluator import run_program          # noqa: E402
from parser import parse                   # noqa: E402
from printer import to_string              # noqa: E402
from value import SchemeError              # noqa: E402


def _load_builtins():
    """加载内置库模块。

    文件名必须保留为 builtins.py，但 `builtins` 是 Python 标准库模块名，
    直接 import 会命中内建模块。这里按路径显式加载并挂成私有名，
    既保留规范的模块文件名，又避免命名冲突。
    """
    path = os.path.join(_SRC_DIR, "builtins.py")
    spec = importlib.util.spec_from_file_location("_mini_scheme_builtins", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _emit(value):
    """打印一个顶层结果（写入式，字符串带引号）。"""
    sys.stdout.write(to_string(value) + "\n")


def run_source(text, env):
    """解析并求值一段源码。"""
    run_program(parse(text), env, _emit)


def main(argv):
    builtins_mod = _load_builtins()
    env = builtins_mod.standard_env()

    files = argv[1:]
    try:
        if files:
            for path in files:
                with open(path, "r", encoding="utf-8") as handle:
                    run_source(handle.read(), env)
        else:
            run_source(sys.stdin.read(), env)
    except SchemeError as error:
        sys.stdout.flush()
        sys.stderr.write("error: %s\n" % error)
        return 1

    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
