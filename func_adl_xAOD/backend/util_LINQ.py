# Helpers for LINQ operators and LINQ expressions in AST form.
# Utility routines to manipulate LINQ expressions.
from func_adl.ast.func_adl_ast_utils import FuncADLNodeVisitor
import ast
from typing import Optional, List


def find_dataset(a: ast.AST) -> ast.Call:
    r'''
    Given an input query ast, find the EventDataSet and return it.

    Args:
        a:      An AST that represents a query

    Returns:
        The `EventDataSet` at the root of this query. It will not be None.

    Exceptions:
        If there is more than one `EventDataSet` found in the query or if there
        is no `EventDataSet` at the root of the query, then an exception is thrown.
    '''

    class ds_finder(FuncADLNodeVisitor):
        def __init__(self):
            self.ds: Optional[ast.Call] = None

        def call_EventDataset(self, node: ast.Call, args: List[ast.AST]):
            if self.ds is not None:
                raise BaseException("AST Query has more than one EventDataSet in it!")
            self.ds = node
            return node

    ds_f = ds_finder()
    ds_f.visit(a)

    if ds_f.ds is None:
        raise BaseException("AST Query has no root EventDataset")

    return ds_f.ds
