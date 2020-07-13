# Code to support running an ast at a remote func-adl server.
import ast
import importlib.util
from io import StringIO
import logging
import os
import time
from typing import Any, List, Union, Dict
import urllib

from func_adl.util_ast import as_ast, function_call
import numpy as np
import pandas as pd
from qastle import python_ast_to_text_ast
import requests
from retry import retry
import servicex
import uproot

from .util_LINQ import extract_dataset_info


class FuncADLServerException (Exception):
    'Thrown when an exception happens contacting the server'
    def __init__(self, msg):
        Exception.__init__(self, msg)


def _uri_exists(uri):
    'Look to see if a file:// uri exists'
    r = urllib.parse.urlparse(uri)  # type: ignore
    if r.scheme != 'file':
        return False
    if os.path.exists(r.path):
        return True
    # Give a chance for a relative path.
    return os.path.exists(r.path[1:])


@retry(tries=10, delay=0.5)
def _make_request(node: str, ast_data):
    'Make the request from the end point'
    r = requests.post(f'{node}/query',
                      headers={"content-type": "application/octet-stream"},
                      data=ast_data)

    # Need to handle errors (see https://github.com/gordonwatts/functional_adl/issues/22).
    try:
        return r.json()
    except Exception as e:
        # Wrap the error in the full text if possible.
        raise FuncADLServerException(f'Error from server "{str(e)}" while parsing response "{r.text}"') from e


def _best_access(files):
    'Given a list of ways to a file, determine which one is best'
    for uri, t_name in files:
        r = urllib.parse.urlparse(uri)  # type: ignore
        if r.scheme == 'file':
            if os.path.exists(r.path):
                return [uri, t_name]
            if os.path.exists(r.path[1:]):
                return [uri, t_name]
        else:
            # A different method of accessing besides a local file. Assume it is
            # awesome.
            return [uri, t_name]


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


class WalkFuncADLAST(ast.NodeTransformer):
    'Walk the AST, replace the ROOT lookup node by something we know how to deal with.'
    def __init__(self, node: str, sleep_interval_seconds: int, partial_ds_ok: bool, quiet: bool):
        'Set the node were we can go pick up the data'
        ast.NodeTransformer.__init__(self)
        self._node = node
        self._sleep_time = sleep_interval_seconds
        self._partial_ds_ok = partial_ds_ok
        self._quiet = quiet

    def extract_filespec(self, response: dict):
        'Given the dictionary of info that came back from the webservice, extract the proper set of files'

        # Get a list of the valid items we can load into uproot.
        access_list = ['localfiles', 'files', 'httpfiles']
        if importlib.util.find_spec('XRootD') is None:
            # We can't do root:// easily on windows, so drop it.
            access_list = ['localfiles', 'httpfiles']
        access_list = [a for a in access_list if a in response]

        if len(access_list) == 0:
            raise FuncADLServerException(f'No viable data sources came back accessible. The complete response from the server was {response}."')

        # Next, check for visibility of all of these things.
        pairs = zip(*[response[n] for n in access_list])
        r = [_best_access(fr) for fr in pairs]
        return r

    def process_ResultTTree(self, result_ast: ast.AST):
        '''Send a query to the remote node. Then hang out until something we can work with shows up.


        TODO: Convert this to be async
        '''

        # Convert the python AST into the natural language for the backend.
        ast_data = python_ast_to_text_ast(result_ast)

        # Repeat until we get a good-enough answer.
        phases = {}
        print_count = 0
        while True:
            dr = _make_request(self._node, ast_data)
            logging.info(f'returned info: {dr}')

            # Accumulate statistics
            p = dr['phase']
            if p in phases:
                phases[p] += 1
            else:
                phases[p] = 1

            # If we are done, return the information.
            if dr['done'] or (self._partial_ds_ok and len(dr['files']) > 0):
                if not self._quiet and len(phases) > 1:
                    # Report on how much time we spent waiting.
                    total = sum([phases[k] for k in phases.keys()])
                    print('Where we spent time waiting for column data:')
                    for k in phases.keys():
                        print(f'  {k}: {phases[k]*100/total}%')

                if dr['phase'] != 'done':
                    # Yikes! Something bad happened. Try to assemble a error messages and blow up.
                    with StringIO() as s:
                        print('The request failed:', file=s)
                        if 'message' in dr:
                            print(f'  Message: {dr["message"]}', file=s)
                        if 'log' in dr:
                            print('  Log lines:', file=s)
                            for line in dr['log']:
                                print(f'    {line}', file=s)
                        raise FuncADLServerException(s.getvalue())

                r = {'files': self.extract_filespec(dr)}
                if not self._quiet:
                    print('Files that were returned:')
                    for f in r['files']:
                        print(f'  {f}')

                return r

            # See if we should print
            if not self._quiet:
                if print_count == 0:
                    localtime = time.asctime(time.localtime(time.time()))
                    print(f'{localtime} : Status: {dr["phase"]}')
                print_count = (print_count + 1) % 10

            # Wait a short amount of time before pinging again.
            if self._sleep_time > 0:
                time.sleep(self._sleep_time)

    def _clean_name(self, url):
        'Clean up a name. Mostly dealing with URIs, uproot, and windows.'
        p = urllib.parse.urlparse(url)  # type: ignore
        if p.scheme != 'file':
            return url
        if os.path.exists(p.path):
            return url
        return f'file://{p.path[1:]}'

    def _load_df(self, f_name, t_name):
        data_file = uproot.open(self._clean_name(f_name))
        df_new = data_file[t_name].pandas.df()  # type: ignore
        data_file._context.source.close()
        return df_new

    def _load_awkward(self, f_name, t_name):
        data_file = uproot.open(self._clean_name(f_name))
        df_new = data_file[t_name].arrays()  # type: ignore
        data_file._context.source.close()
        return df_new

    def process_ResultPandasDF(self, source_node: ast.AST, column_names: ast.AST) -> pd.DataFrame:
        r'''
        Our backend only does root-tuples. So we will open them and load them into a DF. By whatever
        method they are fetched, we don't care. As long as they show up here in the same form as ResultTTree above.False

        Arguments:
            source_node:                The AST node represending the source sequence for the pandas df
            column_names:               An AST that is a list of column names.

        Returns:
            df:                 The data frame, ready to go, with all events loaded.
        '''
        # Build the root TTree result so we can get a list of files back. We will then
        # import those into a pandas dataframe.
        a_root = function_call("ResultTTree", [source_node, column_names, as_ast('pandas_tree'), as_ast('output.root')])

        files = self.visit(a_root)
        if not isinstance(files, dict) or "files" not in files:
            raise Exception(f"Fetch of data for conversion to pandas cameback in a format we don't know: {files}.")

        # Now, open them, one by one.
        frames = [self._load_df(f_name, t_name) for f_name, t_name in files['files']]
        if len(frames) == 1:
            return frames[0]
        else:
            return pd.concat(frames)

    def process_ResultAwkwardArray(self, source_node: ast.AST, column_names: ast.AST):
        r'''
        Our backend only does root-tuples. So we will open them and load them into a awkward array. By whatever
        method they are fetched, we don't care. As long as they show up here in the same form as ResultTTree above.False

        Arguments:
            source_node:                The AST node represending the source sequence for the awkward array
            column_names:               An AST that is a list of column names.

        Returns:
            df:                         The awkward array, ready to go, with all events loaded.
        '''
        # Build the root TTree result so we can get a list of files, and
        # render it.
        a_root = function_call("ResultTTree", [source_node, column_names, as_ast('pandas_tree'), as_ast('output.root')])

        files = self.visit(a_root)
        if not isinstance(files, dict) or "files" not in files:
            raise Exception(f"Fetch of data for conversion to pandas cameback in a format we don't know: {files}.")

        # Now, open them, one by one.
        frames = [self._load_awkward(f_name, t_name) for f_name, t_name in files['files']]
        if len(frames) == 1:
            return frames[0]
        else:
            col_names = frames[0].keys()
            return {c: np.concatenate([ar[c] for ar in frames]) for c in col_names}

    def visit_Call(self, call_node: ast.Call) -> Any:
        '''
        Look for one of our special call functions: Select, SelectMany, etc.
        Unpack the arguments and dispatch the calls.
        '''
        if not isinstance(call_node.func, ast.Name):
            return call_node

        func_name = call_node.func.id
        args = call_node.args
        if func_name == 'ResultTTree':
            return self.process_ResultTTree(call_node)
        elif func_name == 'ResultPandasDF':
            return self.process_ResultPandasDF(args[0], args[1])
        elif func_name == 'ResultAwkwardArray':
            return self.process_ResultAwkwardArray(args[0], args[1])
        else:
            return call_node


async def use_exe_servicex(a: ast.AST,
                           endpoint: str = 'http://localhost:5000/servicex'
                           ) -> Union[pd.DataFrame, Dict[str, Any]]:
    r'''
    Run a query against a func-adl server backend. The appropriate part of the AST is shipped there, and it is interpreted.

    Arguments:

        a:                  The ast that we should evaluate
        endpoint:           The ServiceX node/port endpoint where we can make the query. Defaults to the local thing.
        cached_results_OK:  If true, then pull the result from a cache if possible. Otherwise run the servicex
                            query.

    Returns:
        dataframe           A Pandas DataFrame object that contains the result of the query.
    '''
    # Now, make sure the ast is formed in a way we cna deal with.
    if not isinstance(a, ast.Call):
        raise FuncADLServerException(f'Unable to use ServiceX to fetch a {a}.')
    a_func = a.func
    if not isinstance(a_func, ast.Name):
        raise FuncADLServerException(f'Unable to use ServiceX to fetch a call from {a_func}')

    # Make the servicex call, asking for the appropriate return type. Depending on the return-type
    # alter it so it can return something that ServiceX can understand.
    return_type = ''
    top_level_ast = a

    if a_func.id == 'ResultPandasDF':
        return_type = 'pandas'
        source = a.args[0]
        cols = a.args[1]
        top_level_ast = ast.Call(func=ast.Name('ResultTTree'), args=[source, cols, ast.Str('treeme'), ast.Str('file.root')])
    elif a_func.id == 'ResultAwkwardArray':
        return_type = 'awkward'
        source = a.args[0]
        cols = a.args[1]
        top_level_ast = ast.Call(func=ast.Name('ResultTTree'), args=[source, cols, ast.Str('treeme'), ast.Str('file.root')])
    else:
        raise FuncADLServerException(f'Unable to use ServiceX to fetch a result in the form {a_func.id}')

    # Parse out the dataset components, which will drive the servicex call.
    q_str = python_ast_to_text_ast(top_level_ast)
    datasets = _resolve_dataset(a)
    assert len(datasets) > 0, 'Zero length dataset list not possible'
    assert len(datasets) == 1, 'Can only deal with a single dataset atm'

    return await servicex.get_data_async(q_str, datasets[0], servicex_endpoint=endpoint, data_type=return_type)
