# Contains code to transform the AST into files and C++ code, but not actually run them.
import ast
from collections import namedtuple
import os
import pickle
from pathlib import Path

from func_adl.ast.func_adl_ast_utils import is_call_of

from .atlas_xaod_executor import atlas_xaod_executor


class CacheExeException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


# Return info
HashXAODExecutorInfo = namedtuple('HashXAODExecutorInfo', 'hash main_script treename output_filename')


def _build_result(cache: tuple) -> HashXAODExecutorInfo:
    'Helper routine to build out a full result'
    return HashXAODExecutorInfo(cache[0], cache[1], cache[2], cache[3])


def use_executor_xaod_hash_cache(a: ast.AST, query_file_path: Path) -> HashXAODExecutorInfo:
    r'''Write out the C++ code and supporting files to a cache

    Arguments:
        a               The ast that will be transformed
        cache_path      Path the cache directory. We will write everything out in there.
        no_hash_subdir  Do not put files in the hash subdirectory

    Returns:
        HashXAODExecutorInfo    Named tuple with the hash and the list of files in it.
    '''
    # We can only do this if the result is going to be a ROOT file(s). So make sure.
    if not is_call_of(a, 'ResultTTree'):
        raise CacheExeException(f'Can only cache results for a ROOT tree, not for {type(a).__name__} - {ast.dump(a)} (that should have been a call to ResultTTree).')

    # Create the files to run in that location.
    if not os.path.exists(query_file_path):
        os.makedirs(query_file_path)
    exe = atlas_xaod_executor()
    f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), query_file_path)

    # Write out the basic info for the result rep and the runner into that location.
    result_cache = (hash, f_spec.main_script, f_spec.result_rep.treename, f_spec.result_rep.filename)
    with open(os.path.join(query_file_path, 'rep_cache.pickle'), 'wb') as f:
        pickle.dump(result_cache, f)

    return _build_result(result_cache)
