# Code to support running an ast at a remote func-adl server.
import ast
from typing import Any
import requests
import os
import importlib.util
import time
import uproot
import pandas as pd
import numpy as np
import urllib
from retry import retry
import logging
from io import StringIO
import asyncio
from qastle import python_ast_to_text_ast
from func_adl.util_ast import function_call, as_ast


class FuncADLServerException (BaseException):
    'Thrown when an exception happens contacting the server'
    def __init__(self, msg):
        BaseException.__init__(self, msg)


def _uri_exists(uri):
    'Look to see if a file:// uri exists'
    r = urllib.parse.urlparse(uri)
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
        r = urllib.parse.urlparse(uri)
        if r.scheme == 'file':
            if os.path.exists(r.path):
                return [uri, t_name]
            if os.path.exists(r.path[1:]):
                return [uri, t_name]
        else:
            # A different method of accessing besides a local file. Assume it is
            # awesome.
            return [uri, t_name]


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
                            for l in dr['log']:
                                print(f'    {l}', file=s)
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
        p = urllib.parse.urlparse(url)
        if p.scheme != 'file':
            return url
        if os.path.exists(p.path):
            return url
        return f'file://{p.path[1:]}'

    def _load_df(self, f_name, t_name):
        data_file = uproot.open(self._clean_name(f_name))
        df_new = data_file[t_name].pandas.df()
        data_file._context.source.close()
        return df_new

    def _load_awkward(self, f_name, t_name):
        data_file = uproot.open(self._clean_name(f_name))
        df_new = data_file[t_name].arrays()
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
            raise BaseException(f"Fetch of data for conversion to pandas cameback in a format we don't know: {files}.")

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
            raise BaseException(f"Fetch of data for conversion to pandas cameback in a format we don't know: {files}.")

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


async def use_exe_func_adl_server(a: ast.AST,
                                  node='http://localhost:30000',
                                  sleep_interval=5,
                                  wait_for_finished=True,
                                  quiet=True):
    r'''
    Run a query against a func-adl server backend. The appropriate part of the AST is shipped there, and it is interpreted.

    Arguments:

        a:                  The ast that we should evaluate
        node:               The remote node/port combo where we can make the query. Defaults to the local thing.
        sleep_interval:     How many seconds to wait between queries to the server when the data isn't yet ready
        wait_for_finished:  If true will wait until the dataset has been fully processed. Otherwise will
                            come back without a complete dataset just fine, as long as a least one file is done.
        quiet               If true, run with as little output as possible.

    Returns:
        A dictionary with the following keys:
        'files'          A list of files that contain the requested data. These are either local
                         or they are available via xrootd (they will be file:// or root://).
    '''

    # The func-adl server can only deal with certian types of queries. So we need to
    # make sure we only send those. Do that by walking the nodes.
    # This is syncrhonous code, unfortunately, so we have to have it running
    # in another thread to make this async (there is no way to fix this since the NodeVisitor
    # class is totally synchronous).
    async def run_task(wlk, run_ast):
        # Todo: We shouldn't have to run in a separate thread. Most of the time we are spending
        # sleeping!
        return await asyncio.get_event_loop().run_in_executor(None, wlk.visit, run_ast)

    walker = WalkFuncADLAST(node, sleep_interval, partial_ds_ok=not wait_for_finished, quiet=quiet)
    return await run_task(walker, a)
