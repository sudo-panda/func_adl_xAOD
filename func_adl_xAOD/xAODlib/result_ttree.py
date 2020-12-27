import shutil
from pathlib import Path

import func_adl_xAOD.cpplib.cpp_types as ctyp
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
