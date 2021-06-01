# Drive the translate of the AST from start into a set of files, which one can then do whatever
# is needed to.
import ast
import os
import sys
from abc import ABC, abstractmethod
from collections import namedtuple
from pathlib import Path

import func_adl_xAOD.common.cpp_ast as cpp_ast
import func_adl_xAOD.common.cpp_representation as crep
import jinja2
from func_adl.ast.aggregate_shortcuts import aggregate_node_transformer
from func_adl.ast.func_adl_ast_utils import change_extension_functions_to_calls
from func_adl.ast.function_simplifier import simplify_chained_calls
from func_adl_xAOD.common.ast_to_cpp_translator import query_ast_visitor
from func_adl_xAOD.common.cpp_functions import find_known_functions
from func_adl_xAOD.common.util_scope import top_level_scope

ExecutionInfo = namedtuple('ExecutionInfo', 'result_rep output_path main_script all_filenames')


class _cpp_source_emitter:
    r'''
    Helper class to emit C++ code as we go
    '''

    def __init__(self):
        self._lines_of_query_code = []
        self._indent_level = 0

    def add_line(self, ll):
        'Add a line of code, automatically deal with the indent'
        if ll == '}':
            self._indent_level -= 1

        self._lines_of_query_code += [
            "{0}{1}".format("  " * self._indent_level, ll)]

        if ll == '{':
            self._indent_level += 1

    def lines_of_query_code(self):
        return self._lines_of_query_code


# The following was copied from: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s22.html
def _find(pathname: str, matchFunc=os.path.isfile):
    assert len(pathname) > 0
    for dirname in (sys.path + ['/usr/local']):
        candidate = os.path.join(dirname, pathname)
        if matchFunc(candidate):
            return candidate
    all_dirs = ','.join(sys.path + ['/usr/local'])
    raise RuntimeError(f"Can't find file '{pathname}'. Looked in {all_dirs}")


def _find_dir(path):
    return _find(path, matchFunc=os.path.isdir)


def _is_format_request(a: ast.AST) -> bool:
    '''Return true if the top level ast is a call to generate a ROOT file output.

    Args:
        ast (ast.AST): AST to check at the top level

    Returns:
        bool: True if the ast is not format agnostic.
    '''
    if not isinstance(a, ast.Call):
        raise ValueError(f'A func_adl ast must start with a function call. This does not: {ast.dump(a)}')
    if not isinstance(a.func, ast.Name):
        raise ValueError(f'A func_adl ast must start with a function call to something like Select or AsROOTTTree. This does not: {ast.dump(a)}')
    return a.func.id == 'ResultTTree'


class executor(ABC):
    def __init__(self, file_names: list, runner_name: str, template_dir_name: str, method_names: dict):
        self._file_names = file_names
        self._runner_name = runner_name
        self._template_dir_name = template_dir_name
        self._method_names = method_names

    def _copy_template_file(self, j2_env, info, template_file, final_dir: Path):
        'Copy a file to a final directory'
        j2_env.get_template(template_file).stream(info).dump(str(final_dir / template_file))

    def apply_ast_transformations(self, a: ast.AST):
        r'''
        Run through all the transformations that we have on tap to be run on the client side.
        Return a (possibly) modified ast.
        '''

        # Do tuple resolutions. This might eliminate a whole bunch fo code!
        a = change_extension_functions_to_calls(a)
        a = aggregate_node_transformer().visit(a)
        a = simplify_chained_calls().visit(a)
        a = find_known_functions().visit(a)

        # Any C++ custom code needs to be threaded into the ast
        a = cpp_ast.cpp_ast_finder(self._method_names).visit(a)

        # And return the modified ast
        return a

    @abstractmethod
    def get_visitor_obj(self) -> query_ast_visitor:
        pass

    def write_cpp_files(self, ast: ast.AST, output_path: Path) -> ExecutionInfo:
        r"""
        Given the AST generate the C++ files that need to run. Return them along with
        the input files.
        """

        # Find the base file dataset and mark it.
        from func_adl import find_EventDataset
        file = find_EventDataset(ast)
        iterator = crep.cpp_variable("bogus-do-not-use", top_level_scope(), cpp_type=None)
        file.rep = crep.cpp_sequence(iterator, iterator, top_level_scope())  # type: ignore

        # Visit the AST to generate the code structure and find out what the
        # result is going to be.
        qv = self.get_visitor_obj()
        result_rep = qv.get_rep(ast) if _is_format_request(ast) \
            else qv.get_as_ROOT(ast)

        # Emit the C++ code into our dictionaries to be used in template generation below.
        query_code = _cpp_source_emitter()
        qv.emit_query(query_code)
        book_code = _cpp_source_emitter()
        qv.emit_book(book_code)
        class_decl_code = qv.class_declaration_code()
        includes = qv.include_files()

        # The replacement dict to pass to the template generator can now be filled
        info = {}
        info['query_code'] = query_code.lines_of_query_code()
        info['class_decl'] = class_decl_code
        info['book_code'] = book_code.lines_of_query_code()
        info['include_files'] = includes

        # We use jinja2 templates. Write out everything.
        template_dir = _find_dir(self._template_dir_name)
        j2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir))

        for file_name in self._file_names:
            self._copy_template_file(j2_env, info, file_name, output_path)

        (output_path / self._runner_name).chmod(0o755)

        # Build the return object.
        return ExecutionInfo(result_rep, output_path, self._runner_name, self._file_names)
