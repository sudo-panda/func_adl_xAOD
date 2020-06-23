# Code to support running an ast at a remote func-adl server.
import ast
from typing import List, Union
import urllib

import pandas as pd
from qastle import python_ast_to_text_ast
import servicex

from .util_LINQ import extract_dataset_info


class FuncADLServerException (Exception):
    'Thrown when an exception happens contacting the server'
    def __init__(self, msg):
        Exception.__init__(self, msg)


def _clean_url(ds: str) -> str:
    'If the dataset name coming in is a url, then strip everything off'
    if ds.find('//') < 0:
        return ds

    # Strip off the scheme name
    url_p = urllib.parse.urlparse(ds)  # type: ignore
    ds_name = ds[len(url_p.scheme) + 3:]
    return ds_name


def _resolve_dataset(ast_request: ast.AST) -> Union[str, List[str]]:
    '''Return any datasets in the request.

    Arguments:
        ast_request         The full AST of the request. Must contains a EventDataset call.

    Returns:
        str                 Name of the dataset
        List[str]           List of all names of the datasets. URLs are stripped out, if present.

    Exceptions:
        No EventDataset     If no call to EventDataset is made, this will blow up.
    '''
    class dataset_finder (ast.NodeVisitor):
        def __init__(self):
            self._datasets = None

        'Any event datasets are resolved to be local.'
        def visit_Call(self, node: ast.Call):
            '''
            Look at the call and see if the event dataset is in there.
            '''
            if not isinstance(node.func, ast.Name):
                return super().generic_visit(node)
            if node.func.id != 'EventDataset':
                return super().generic_visit(node)

            assert len(node.args) > 0
            # Cache the names and return them.
            if self._datasets is not None:
                raise Exception('Unable to deal with more than one EventDataset in a single query')
            self._datasets = extract_dataset_info(node)

    df = dataset_finder()
    df.visit(ast_request)
    if df._datasets is None:
        raise Exception('Unable to find EventDataset call - so cannot tell what dataset this query starts from!')

    # If there is any encoding in the dataset, remove it.
    datasets = [_clean_url(ds) for ds in df._datasets]

    return datasets


async def use_exe_servicex(a: ast.AST,
                           endpoint: str = 'http://localhost:5000/servicex'
                           ) -> pd.DataFrame:
    r'''
    Run a query against a func-adl server backend. The appropriate part of the AST is shipped there, and it is interpreted.

    Arguments:

        a:                  The ast that we should evaluate
        endpoint:           The ServiceX node/port endpoint where we can make the query. Defaults to the local thing.

    Returns:
        dataframe           A Pandas DataFrame object that contains the result of the query.
    '''
    # Now, make sure the ast is formed in a way we cna deal with.
    if not isinstance(a, ast.Call):
        raise FuncADLServerException(f'Unable to use ServiceX to fetch a {a}.')
    a_func = a.func
    if not isinstance(a_func, ast.Name):
        raise FuncADLServerException(f'Unable to use ServiceX to fetch a call from {a_func}')

    # Parse out the dataset components, which will drive the servicex call.
    datasets = _resolve_dataset(a)
    assert len(datasets) == 1
    sa_adaptor = servicex.ServiceXAdaptor(endpoint)
    se = servicex.ServiceXDataset(datasets[0], servicex_adaptor=sa_adaptor)

    # Make the servicex call, asking for the appropriate return type. Depending on the return-type
    # alter it so it can return something that ServiceX can understand.
    if a_func.id == 'ResultPandasDF':
        source = a.args[0]
        cols = a.args[1]
        top_level_ast = ast.Call(func=ast.Name('ResultTTree'), args=[source, cols, ast.Str('treeme'), ast.Str('file.root')])
        q_str = python_ast_to_text_ast(top_level_ast)
        return await se.get_data_pandas_df_async(q_str)
    elif a_func.id == 'ResultAwkwardArray':
        source = a.args[0]
        cols = a.args[1]
        top_level_ast = ast.Call(func=ast.Name('ResultTTree'), args=[source, cols, ast.Str('treeme'), ast.Str('file.root')])
        q_str = python_ast_to_text_ast(top_level_ast)
        return await se.get_data_awkward_async(q_str)
    else:
        raise FuncADLServerException(f'Unable to use ServiceX to fetch a result in the form {a_func.id} - Only ResultPandasDF and ResultAwkwardArray are supported')
