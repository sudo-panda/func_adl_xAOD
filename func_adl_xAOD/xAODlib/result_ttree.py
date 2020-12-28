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
