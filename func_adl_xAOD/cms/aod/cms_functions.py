import func_adl_xAOD.common.cpp_ast as cpp_ast
from func_adl_xAOD.common.cpp_representation import cpp_variable
from func_adl_xAOD.common.cpp_vars import unique_name


def isNonnullAst(call_node):
    r'''
    User is trying to test, on certian objects, if the object, when dereferenced, will be a null
    pointer. This is tricky for our data model because it treats an object as both a poitner and
    a object. Most of `func_adl_xAOD` is setup to deal with it as a pointer. This allows us to
    get around ths.
    '''

    if len(call_node.args) != 1:
        raise ValueError("Calling isNonnull(object) has incorrect number of arguments")

    # Create an AST to hold onto all of this.
    r = cpp_ast.CPPCodeValue()

    # We need all four arguments pushed through.
    r.args = ['cms_object']

    # The code is three steps
    r.running_code += ['auto result = (cms_object).isNonnull();']
    r.result = 'result'
    r.result_rep = lambda scope: cpp_variable(unique_name('is_non_null'), scope=scope, cpp_type='bool')

    call_node.func = r
    return call_node


def isNonnull(cms_object) -> bool:
    'See if dereferencing the cms object will return a null pointer or not'
    raise NotImplementedError('IsNonnull should never be called in python!')


def get_cms_functions():
    return {
        'isNonnull': isNonnullAst
    }
