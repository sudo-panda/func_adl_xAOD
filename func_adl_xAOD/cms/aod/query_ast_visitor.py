from func_adl_xAOD.common.ast_to_cpp_translator import query_ast_visitor
from func_adl_xAOD.common.statement import book_ttree, ttree_fill


class book_cms_aod_ttree(book_ttree):
    'Book an ATLAS TTree for writing out. Meant to be in the Book method'

    def __init__(self, tree_name, leaves):
        super().__init__(tree_name, leaves)

    def emit(self, e):
        'Emit the book statement for a tree'
        e.add_line("edm::Service<TFileService> fs;")
        e.add_line('myTree = fs->make<TTree>("{0}", "My analysis ntuple");'.format(
            self._tree_name))
        for var_pair in self._leaves:
            e.add_line('myTree->Branch("{0}", &{1});'.format(var_pair[0], var_pair[1].as_cpp()))


class cms_aod_ttree_fill(ttree_fill):
    'Fill a CMS TTree'

    def __init__(self, tree_name):
        super().__init__(tree_name)

    def emit(self, e):
        e.add_line('myTree->Fill();')


class cms_aod_query_ast_visitor(query_ast_visitor):
    r"""
    Drive the conversion to C++ from the top level query
    for CMS AOD
    """

    def __init__(self):
        prefix = 'cms_aod'
        is_loop_var_a_ref = True
        super().__init__(prefix, is_loop_var_a_ref)

    def create_book_ttree_obj(self, tree_name: str, leaves: list) -> book_ttree:
        return book_cms_aod_ttree(tree_name, leaves)

    def create_ttree_fill_obj(self, tree_name: str) -> ttree_fill:
        return cms_aod_ttree_fill(tree_name)
