from func_adl_xAOD.cms.aod.event_collections import \
    cms_aod_event_collections as ec
from func_adl_xAOD.cms.aod.query_ast_visitor import cms_aod_query_ast_visitor
from func_adl_xAOD.common.executor import executor

from .cms_functions import get_cms_functions


class cms_aod_executor(executor):
    def __init__(self):
        file_names = ['analyzer_cfg.py', 'Analyzer.cc', 'BuildFile.xml', "copy_root_tree.C", 'runner.sh']
        runner_name = 'runner.sh'
        template_dir_name = 'func_adl_xAOD/template/cms/r5'
        method_names = ec().get_method_names()
        method_names.update(get_cms_functions())
        super().__init__(file_names, runner_name, template_dir_name, method_names)

    def get_visitor_obj(self):
        return cms_aod_query_ast_visitor()
