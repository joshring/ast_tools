import ast
import typing as tp

from ast_tools.stack import SymbolTable
from . import Pass, PASS_ARGS_T
from ast_tools.transformers.loop_unroller import unroll_for_loops, unroll_for_loops_by_factor


class loop_unroll(Pass):
    def rewrite(self,
                tree: ast.AST,
                env: SymbolTable,
                metadata: tp.MutableMapping) -> PASS_ARGS_T:
        return unroll_for_loops(tree, env), env, metadata


class loop_unroll_by_factor(Pass):
    def rewrite(
            self,
            tree        : ast.AST,
            env         : SymbolTable,
            metadata    : tp.MutableMapping,
            factor      : int
            ) -> PASS_ARGS_T:
        return unroll_for_loops_by_factor(tree=tree, factor=factor, env=env), env, metadata
