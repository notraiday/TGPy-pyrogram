"""
    name: context_aliases
    origin: tgpy://module/context_aliases
    priority: 200
"""

import ast
import tgpy.api

ALIASES = {
    'r': 'orig',
}

class ContextAliasTransformer(ast.NodeTransformer):
    """
    AST transformer that replaces specified aliases with their actual names.
    """
    def visit_Name(self, node: ast.Name):
        if node.id in ALIASES:
            return ast.Name(id=ALIASES[node.id], ctx=node.ctx)
        return self.generic_visit(node)

def ast_trans(tree: ast.AST) -> ast.AST:
    transformer = ContextAliasTransformer()
    transformed_tree = transformer.visit(tree)
    return ast.fix_missing_locations(transformed_tree)
tgpy.api.ast_transformers.add('context_aliases', ast_trans)
