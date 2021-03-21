from func_adl_xAOD.common_lib.executor import executor
from func_adl_xAOD.atlas_xAOD_lib.atlas_xaod_translator import atlas_xaod_query_ast_visitor


class atlas_xaod_executor(executor):
    def __init__(self):
        file_names = ['ATestRun_eljob.py', 'package_CMakeLists.txt', 'query.cxx', 'query.h', 'runner.sh']
        runner_name = 'runner.sh'
        template_dir_name = 'func_adl_xAOD/template/atlas/r21'
        super().__init__(file_names, runner_name, template_dir_name)

    def get_visitor_obj(self):
        return atlas_xaod_query_ast_visitor()
