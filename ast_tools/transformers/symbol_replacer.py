import ast
from .node_replacer import NodeReplacer

class SymbolReplacer(NodeReplacer):
    def _get_key(self, node):
        if isinstance(node, ast.Name):
            return node.id
        else:
            return None

def replace_symbols(tree, symbol_table):
    """
    variables defined in the symbol_table, matched on the keys, 
    will be replaced with the value defined within.
    all other variables will be unchanged
    """
    return SymbolReplacer(node_table = symbol_table).visit(tree)
