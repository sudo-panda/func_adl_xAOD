# Code to work with the various types of data the executor is going to have to
# return to the front end.

from func_adl_xAOD.cpplib.cpp_representation import cpp_value
import func_adl_xAOD.cpplib.cpp_types as ctyp
from func_adl_xAOD.cpplib.cpp_vars import unique_name
import uproot


##################
# TTree return
class cpp_ttree_rep(cpp_value):
    'This is what a TTree operator returns'
    def __init__(self, filename, treename, scope):
        cpp_value.__init__(self, unique_name("ttree_rep"), scope, ctyp.terminal("ttreetfile"))
        self.filename = filename
        self.treename = treename


def extract_result_TTree(rep, run_dir):
    '''
    Given the tree info, return the appropriate data to the client. In this case it is just
    a full filename along with a tree name which the client can then use to open the tree.

    rep: the cpp_tree_rep of the file that is going to come back.
    run_dir: location where run wrote all the files

    returns:
    path_to_root_file: Full path to the file, copied into the local directory
    tree_name: the name of the tree.
    '''
    raise Exception("extract_result_TTree is not yet implemented.")
    # # This would be trivial other than the directory is about to be deleted. So in this case we are going to
    # # need to copy the file over somewhere else!
    # df_name = os.path.join(os.getcwd(), unique_name("datafile") + ".root")
    # df_current = os.path.join(run_dir, 'data.root')

    # if not os.path.exists(df_current):
    #     raise Exception("Unable to find ROOT file '{0}' which contains the data we need!".format(df_current))

    # shutil.copyfile(df_current, df_name)

    # return ROOTTreeResult(True, [ROOTTreeFileInfo(df_name, rep.treename)])


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
