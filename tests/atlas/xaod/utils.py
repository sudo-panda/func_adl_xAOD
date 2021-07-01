import ast
from pathlib import Path
from typing import Any, Dict, List, Union

import awkward as ak
import pandas as pd
import uproot
from func_adl.object_stream import ObjectStream
from func_adl_xAOD.atlas.xaod.executor import atlas_xaod_executor
from func_adl_xAOD.atlas.xaod.query_ast_visitor import \
    atlas_xaod_query_ast_visitor
from func_adl_xAOD.common.cpp_representation import cpp_sequence, cpp_variable
from func_adl_xAOD.common.util_scope import top_level_scope
from tests.utils.base import LocalFile, dataset, dummy_executor


class atlas_xaod_dummy_executor(dummy_executor):
    def __init__(self):
        super().__init__()

    def get_executor_obj(self) -> atlas_xaod_executor:
        return atlas_xaod_executor()

    def get_visitor_obj(self) -> atlas_xaod_query_ast_visitor:
        return atlas_xaod_query_ast_visitor()


class atlas_xaod_dataset(dataset):
    def __init__(self, qastle_roundtrip=False):
        super().__init__(qastle_roundtrip=qastle_roundtrip)

    def get_dummy_executor_obj(self) -> dummy_executor:
        return atlas_xaod_dummy_executor()


class AtlasXAODDockerException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class AtlasXAODLocalFile(LocalFile):
    def __init__(self, local_files: Union[Path, List[Path]]):
        super().__init__("atlas/analysisbase:latest", "query.cxx", local_files)

    def raise_docker_exception(self, message: str):
        raise AtlasXAODDockerException(message)

    def get_executor_obj(self) -> atlas_xaod_executor:
        return atlas_xaod_executor()


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
    exe = atlas_xaod_dummy_executor()
    exe.evaluate(a)
    return exe


def load_root_as_pandas(file: Path) -> pd.DataFrame:
    '''Given the result from a query as a ROOT file path, return
    the contents as a pandas dataframe.

    Args:
        file (Path): [description]

    Returns:
        pandas.DataFrame: [description]
    '''
    assert isinstance(file, Path)
    assert file.exists()

    with uproot.open(file) as input:
        return input['atlas_xaod_tree'].arrays(library='pd')  # type: ignore


def load_root_as_awkward(file: Path) -> ak.Array:
    '''Given the result from a query as a ROOT file path, return
    the contents as a pandas dataframe.

    Args:
        file (Path): [description]

    Returns:
        pandas.DataFrame: [description]
    '''
    assert isinstance(file, Path)
    assert file.exists()

    with uproot.open(file) as input:
        return input['atlas_xaod_tree'].arrays()  # type: ignore


def as_pandas(o: ObjectStream) -> pd.DataFrame:
    '''Return a query as a pandas dataframe.

    Args:
        o (ObjectStream): The query

    Returns:
        pd.DataFrame: The result
    '''
    return load_root_as_pandas(o.value())


def as_awkward(o: ObjectStream) -> ak.Array:
    '''Return a query as a pandas dataframe.

    Args:
        o (ObjectStream): The query

    Returns:
        pd.DataFrame: The result
    '''
    return load_root_as_awkward(o.value())


async def as_pandas_async(o: ObjectStream) -> pd.DataFrame:
    '''Return a query as a pandas dataframe.

    Args:
        o (ObjectStream): The query

    Returns:
        pd.DataFrame: The result
    '''
    return load_root_as_pandas(await o.value_async())


def ast_parse_with_replacement(ast_string: str, replacements: Dict[str, ast.AST]) -> ast.AST:
    '''Returns an ast, where any ast.Name elements are replaced by the ast that is in
    the dict.

    Args:
        ast_string (str): The string to parse
        replacements (Dict[str, ast.AST]): Dict of what to replace

    Returns:
        (ast.AST): Ast from the parse, with the names replaced.
    '''
    a = ast.parse(ast_string)

    class replacer(ast.NodeTransformer):
        def visit_Name(self, node: ast.Name) -> Any:
            if node.id in replacements:
                return replacements[node.id]

            return super().visit_Name(node)

    return replacer().visit(a)
