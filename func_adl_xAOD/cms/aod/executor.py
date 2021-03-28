from func_adl_xAOD.common.executor import executor
from func_adl_xAOD.cms.aod.query_ast_visitor import cms_aod_query_ast_visitor


class cms_aod_executor(executor):
    def __init__(self):
        file_names = ['analyzer_cfg.py', 'Analyzer.cc', 'BuildFile.xml', 'runner.sh']
        runner_name = 'runner.sh'
        template_dir_name = 'func_adl_xAOD/template/cms/r5'
        super().__init__(file_names, runner_name, template_dir_name)

    def get_visitor_obj(self):
        return cms_aod_query_ast_visitor()
