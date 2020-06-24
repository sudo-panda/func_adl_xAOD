# Python code to help with working with a grid dataset
# that should be downloaded locally to be run on.False
import ast
import errno
import os
from typing import List, Optional
from urllib import parse

from func_adl.ast.func_adl_ast_utils import (
    FuncADLNodeTransformer, function_call)
from func_adl.util_ast import as_ast
import requests

# TODO: update this to run "properly" locally.


# Resolvers:
def resolve_file(parsed_url, url: str):
    if len(parsed_url.netloc) != 0:
        raise FileNotFoundError(errno.ENOENT, f'Unable to find files that are remote: {parsed_url.netloc} and path {parsed_url.path}.')
    l_path = parsed_url.path[1:]
    if not os.path.exists(l_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), l_path)
    return [url]


def resolve_localds(parsed_url, url: str):
    ds = parsed_url.netloc
    r = requests.post(f'http://localhost:8000/ds?ds_name={ds}')
    result = r.json()
    if result['status'] == 'downloading':
        return None
    if result['status'] == 'does_not_exist':
        raise GridDsException(f'Dataset {url} does not exist and cannot be downloaded locally.')

    # Turn these into file url's, relative to the file location returned.
    return [f for f in result['filelist']]


def resolve_root(parsed_url, url: str):
    'We are given a root schema - this points to a single file. So we ignore it and just use it. No easy way to check it...'
    return [url]


# We use this here so we can mock things for testing
resolve_callbacks = {
    'file': resolve_file,
    'localds': resolve_localds,
    'root': resolve_root
}


class GridDsException (Exception):
    'Thrown when an error occurs going after a grid dataset of some sort'
    def __init__(self, message):
        Exception.__init__(self, message)


def resolve_local_ds_url(url: str) -> Optional[List[str]]:
    '''
    Given a url, check that it is either a local dataset request or a file.
    If it is a file, return it. If it is a local dataset, attempt to resolve it.
    Trigger a download if need be.

    Args:
        url:        The URL of the dataset

    Returns:
        None        We've asked for the file, but it isn't local yet.
        [urls]      List of URL's this translates to

    Exceptions:
        xxx                 The url scheme isn't `file` or `localds`
        FileNotFoundError   a url with "file" on it was not found on this machine.
        Other               For example, can't get a hold of desktop-rucio to do the download.
    '''
    parsed = parse.urlparse(url)

    # Run resolver callbacks.
    if parsed.scheme in resolve_callbacks:
        return resolve_callbacks[parsed.scheme](parsed, url)

    # If we are here, then we don't know what to do.
    raise GridDsException(f'Do not know how to resolve dataset of type {parsed.scheme} from url {url}.')


def resolve_dataset(ast_request: ast.AST) -> Optional[ast.AST]:
    '''Find the datasets in a request and work to make them local so we can
    run on them.

    Arguments:
        ast_request         The full AST of the request. Must contains a EventDataset call.

    Returns:
        updated_ast         The AST gets altered with local versions of the dataset after they
                            have been downloaded.
                            If the data hasn't been downloaded yet, then None is returned in stead.

    Exceptions:
        No EventDataset     If no call to EventDataset is made, this will blow up.
        Error Downloading   If some error occurs during downloading an exception will be thrown.
    '''

    class dataset_finder (FuncADLNodeTransformer):
        'Any event datasets are resolved to be local.'
        def __init__(self):
            'Dataset Locally Resolved becomes true only if all datasets are local.'
            self.DatasetsLocallyResolves = False

        def call_EventDataset(self, node: ast.Call, args: List[ast.AST]):
            '''
            Look at the URL's for the event dataset. Try to replace them with
            files that have been downloaded locally, if we can.
            '''
            # Resolve all the url's
            urls = []  # extract_dataset_info(node)
            resolved_urls = [resolve_local_ds_url(u) for u in urls]

            # If any None's, then we aren't ready to go.
            if any(u is None for u in resolved_urls):
                return node

            u_list = [u for ulist in resolved_urls for u in ulist]
            if len(u_list) == 0:
                raise GridDsException(f'Resolving the dataset urls {urls} gave the empty list of files')

            # All good! Create a new event dataset!
            self.DatasetsLocallyResolves = True
            return function_call('EventDataset', [as_ast(u_list), ])

    if not isinstance(ast_request, ast.AST):
        raise GridDsException(f'Expecting an ast.AST, but got something else: {ast_request}')

    df = dataset_finder()
    updated_request = df.visit(ast_request)
    if not df.DatasetsLocallyResolves:
        return None
    return updated_request


# async def use_executor_dataset_resolver(a: ast.AST, chained_executor=use_executor_xaod_docker):
#     'Run - keep re-doing query until we crash or we can run'
#     am = None
#     while am is None:
#         am = resolve_dataset(a)
#         if am is None:
#             await asyncio.sleep(5 * 60)

#     # Ok, we have a modified AST and we can now get it processed.
#     if am is None:
#         raise Exception("internal programming error - resolved AST should not be null")
#     return await chained_executor(am)
