# Some very direct white box testing
import ast
from func_adl_xAOD.backend.xAODlib.ast_to_cpp_translator import query_ast_visitor
import func_adl_xAOD.backend.cpplib.cpp_representation as crep
import func_adl_xAOD.backend.cpplib.cpp_types as ctyp


def test_binary_plus_return_type_1():
    q = query_ast_visitor()
    q.visit(ast.parse('1+1.2'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'


def test_binary_plus_return_type_2():
    q = query_ast_visitor()
    q.visit(ast.parse('1.2+1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'

def test_binary_plus_return_type_3():
    q = query_ast_visitor()
    q.visit(ast.parse('1+1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'int'


def test_binary_mult_return_type_1():
    q = query_ast_visitor()
    q.visit(ast.parse('1.2*1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'


def test_binary_mult_return_type_2():
    q = query_ast_visitor()
    q.visit(ast.parse('1*1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'int'


def test_binary_divide_return_type_1():
    q = query_ast_visitor()
    q.visit(ast.parse('1.2/1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'


def test_binary_divide_return_type_2():
    q = query_ast_visitor()
    q.visit(ast.parse('1/1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'
