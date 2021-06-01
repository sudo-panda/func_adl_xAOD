from func_adl_xAOD.atlas.xaod.event_collections import \
    atlas_xaod_event_collections as ec
from func_adl_xAOD.atlas.xaod.jets import get_jet_methods
from func_adl_xAOD.atlas.xaod.query_ast_visitor import \
    atlas_xaod_query_ast_visitor
from func_adl_xAOD.common.executor import executor


class atlas_xaod_executor(executor):
    def __init__(self):
        file_names = ['ATestRun_eljob.py', 'package_CMakeLists.txt', 'query.cxx', 'query.h', 'runner.sh']
        runner_name = 'runner.sh'
        template_dir_name = 'func_adl_xAOD/template/atlas/r21'
        method_names = ec().get_method_names()
        method_names.update(get_jet_methods())
        super().__init__(file_names, runner_name, template_dir_name, method_names)

    def get_visitor_obj(self):
        return atlas_xaod_query_ast_visitor()
