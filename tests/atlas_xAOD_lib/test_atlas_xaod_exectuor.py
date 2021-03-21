import ast
import pytest

from func_adl.event_dataset import EventDataset
from func_adl_xAOD.atlas_xAOD_lib.atlas_xaod_executor import atlas_xaod_executor


def test_ctor():
    'Make sure that the ctor works'
    atlas_xaod_executor()


class query_as_ast(EventDataset):
    async def execute_result_async(self, a: ast.AST):
        return a


def test_xaod_executor(tmp_path):
    'Write out C++ files for a simple query'

    # Get the ast to play with
    a = query_as_ast() \
        .Select('lambda e: e.EventInfo("EventInfo").runNumber()') \
        .value()

    exe = atlas_xaod_executor()
    f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)
    for name in f_spec.all_filenames:
        assert (tmp_path / name).exists()


def test_find_exception():
    'Make sure _find exception is well formed'
    from func_adl_xAOD.common_lib.executor import _find

    with pytest.raises(RuntimeError) as e:
        _find('fork-it-over.txt')

    assert 'find file' in str(e.value)


def test_bad_ast_no_call(tmp_path):
    'Pass a really bogus ast to the executor'
    # Get the ast to play with
    q = query_as_ast()
    a = ast.UnaryOp(op=ast.USub(), operand=q.query_ast)

    exe = atlas_xaod_executor()
    with pytest.raises(ValueError) as e:
        exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)

    assert 'func_adl ast' in str(e.value)


def test_bad_ast_no_call_to_name(tmp_path):
    'Pass a really bogus ast to the executor'
    # Get the ast to play with
    q = query_as_ast()
    a = ast.Call(func=ast.Attribute(value=ast.Constant(10), attr='fork'), args=[q.query_ast])

    exe = atlas_xaod_executor()
    with pytest.raises(ValueError) as e:
        exe.write_cpp_files(exe.apply_ast_transformations(a), tmp_path)

    assert 'func_adl ast' in str(e.value)
