# Some utilities to help with testing out when we have to run a dummy version of the
# xaod executor.
#
import ast
from typing import List, Any

from func_adl import EventDataset

from func_adl_xAOD.cpplib.cpp_representation import (
    cpp_sequence, cpp_variable)
from func_adl_xAOD.xAODlib.ast_to_cpp_translator import (
    query_ast_visitor)
from func_adl_xAOD.xAODlib.atlas_xaod_executor import (
    atlas_xaod_executor)
from func_adl_xAOD.xAODlib.util_scope import top_level_scope


class dummy_executor:
    'Override the docker part of the execution engine'
    def __init__ (self):
        self.QueryVisitor = None
        self.ResultRep = None

    def evaluate(self, a: ast.AST, get_root: bool = False):
        rnr = atlas_xaod_executor()
        self.QueryVisitor = query_ast_visitor()
        a_transformed = rnr.apply_ast_transformations(a)
        self.ResultRep = \
            self.QueryVisitor.get_as_ROOT(a_transformed) if get_root \
            else self.QueryVisitor.get_rep(a_transformed)
        

    def get_result(self, q_visitor, result_rep):
        'Got the result. Cache for use in tests'
        self.QueryVisitor = q_visitor
        self.ResultRep = result_rep
        return self


class dataset_for_testing(EventDataset):
    def __init__(self, qastle_roundtrip=False, root_result_only=False):
        EventDataset.__init__(self)
        self._q_roundtrip = qastle_roundtrip
        self._force_root_result = root_result_only

    def __repr__(self) -> str:
        # When we need to move into a representation, use
        # this as a place holder for now.
        return "'sx_placeholder'"

    async def execute_result_async(self, a: ast.AST) -> Any:
        'Dummy executor that will return the ast properly rendered. If qastle_roundtrip is true, then we will round trip the ast via qastle first.'
        # Round trip qastle if requested.
        if self._q_roundtrip:
            import qastle
            print(f'before: {ast.dump(a)}')
            a_text = qastle.python_ast_to_text_ast(a)
            a = qastle.text_ast_to_python_ast(a_text).body[0].value
            print(f'after: {ast.dump(a)}')

        # Setup the rep for this dataset
        from func_adl import find_EventDataset
        file = find_EventDataset(a)
        iterator = cpp_variable("bogus-do-not-use", top_level_scope(), cpp_type=None)
        file.rep = cpp_sequence(iterator, iterator, top_level_scope())  # type: ignore

        # Use the dummy executor to process this, and return it.
        exe = dummy_executor()
        rnr = atlas_xaod_executor()
        exe.evaluate(a, self._force_root_result)
        return exe


async def exe_from_qastle(q: str):
    'Dummy executor that will return the ast properly rendered. If qastle_roundtrip is true, then we will round trip the ast via qastle first.'
    # Round trip qastle if requested.
    import qastle
    a = qastle.text_ast_to_python_ast(q).body[0].value

    # Setup the rep for this filter
    from func_adl import find_EventDataset
    file = find_EventDataset(a)
    iterator = cpp_variable("bogus-do-not-use", top_level_scope(), cpp_type=None)
    file.rep = cpp_sequence(iterator, iterator, top_level_scope())  # type: ignore

    # Use the dummy executor to process this, and return it.
    exe = dummy_executor()
    rnr = atlas_xaod_executor()
    exe.evaluate(a)
    return exe

class dummy_emitter:
    def __init__ (self):
        self.Lines = []
        self._indent_level = 0

    def add_line (self, l):
        if l == '}':
            self._indent_level -= 1

        self.Lines += [
            "{0}{1}".format("  " * self._indent_level, l)]

        if l == '{':
            self._indent_level += 1

    def process (self, func):
        func(self)
        return self

def get_lines_of_code(executor) -> List[str]:
    'Return all lines of code'
    qv = executor.QueryVisitor
    d = dummy_emitter()
    qv.emit_query(d)
    return d.Lines

def find_line_with(text, lines, throw_if_not_found = True):
    'Find the first line with the text. Return its index, zero based'
    for index, l in enumerate(lines):
        if text in l:
            return index
    if throw_if_not_found:
        raise Exception("Unable to find text '{0}' in any lines in text output".format(text))
    return -1

def find_line_numbers_with(text, lines):
    return [index for index,l in enumerate(lines) if text in l]

def print_lines(lines):
    for l in lines:
        print(l)

def find_next_closing_bracket(lines):
    'Find the next closing bracket. If there is an opening one, then track through to the matching closing one.'
    depth = 0
    for index, l in enumerate(lines):
        if l.strip() == "{":
            depth += 1
        if l.strip() == "}":
            depth -= 1
            if depth < 0:
                return index
    return -1

def find_open_blocks(lines):
    'Search through and record the lines before a {. If a { is closed, then remove that lines'
    stack = []
    last_line_seen = 'xxx-xxx-xxx'
    for l in lines:
        if l.strip() == '{':
            stack += [last_line_seen]
        elif l.strip() == '}':
            stack = stack[:-1]
        last_line_seen = l
    return stack
