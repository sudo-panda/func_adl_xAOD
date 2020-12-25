import shutil
from pathlib import Path

import func_adl_xAOD.cpplib.cpp_types as ctyp
import uproot
from func_adl_xAOD.cpplib.cpp_representation import cpp_value
from func_adl_xAOD.cpplib.cpp_vars import unique_name


##################
# TTree return
class cpp_ttree_rep(cpp_value):
    'This is what a TTree operator returns'
    def __init__(self, filename, treename, scope):
        cpp_value.__init__(self, unique_name("ttree_rep"), scope, ctyp.terminal("ttreetfile"))
        self.filename = filename
        self.treename = treename


def extract_result_TTree(rep: cpp_ttree_rep, run_dir):
    '''Copy the final file into a place that is "safe", and return that as a path.

    The reason for this is that the temp directory we are using is about to be deleted!

    Args:
        rep (cpp_base_rep): The representation of the final result
        run_dir ([type]): Directory where it ran

    Raises:
        Exception: [description]
    '''
    current_path = run_dir / rep.filename
    new_path = Path('.') / rep.filename
    shutil.copy(current_path, new_path)
    return new_path


#############
# Awkward Array Return
class cpp_awkward_rep(cpp_value):
    'This is how an awkward array comes back'
    def __init__(self, filename, treename, scope):
        cpp_value.__init__(self, unique_name("awk_array"), scope, ctyp.terminal("awkwardarray"))
        self.filename = filename
        self.treename = treename


def extract_awkward_result(rep, run_dir):
    '''
    Given the rep, and the local running directory, load the result into memory. Once we are done the
    file can be removed or discarded.

    rep: the cpp_awkward_rep which will tell us what file to go after
    run_dir: location where all the data was written out by the docker run.

    returns:
    awk: THe awkward array
    '''
    output_file = "file://{0}/{1}".format(run_dir, rep.filename)
    data_file = uproot.open(output_file)
    df = data_file[rep.treename].arrays()  # type: ignore
    data_file._context.source.close()
    return df


#############
# Pandas Return
class cpp_pandas_rep(cpp_value):
    'This is how an awkward array comes back'
    def __init__(self, filename, treename, scope):
        cpp_value.__init__(self, unique_name("pandas"), scope, ctyp.terminal("pandasdf"))
        self.filename = filename
        self.treename = treename


def extract_pandas_result(rep, run_dir):
    '''
    Given the rep, and the local running directory, load the result into memory. Once we are done the
    file can be removed or discarded.

    rep: the cpp_pandas_rep which will tell us what file to go after
    run_dir: location where all the data was written out by the docker run.

    returns:
    awk: THe awkward array
    '''
    output_file = "file://{0}/{1}".format(run_dir, rep.filename)
    data_file = uproot.open(output_file)
    df = data_file[rep.treename].pandas.df()  # type: ignore
    data_file._context.source.close()
    return df
