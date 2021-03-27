# Some very direct white box testing
import ast

from typing import cast

import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
import func_adl_xAOD.common.result_ttree as rh

from func_adl_xAOD.common.util_scope import gc_scope_top_level
from func_adl_xAOD.atlas.xaod.translator import atlas_xaod_query_ast_visitor

from tests.atlas.xaod.utils_for_testing import ast_parse_with_replacement


def test_binary_plus_return_type_1():
    q = atlas_xaod_query_ast_visitor()
    q.visit(ast.parse('1+1.2'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'


def test_binary_plus_return_type_2():
    q = atlas_xaod_query_ast_visitor()
    q.visit(ast.parse('1.2+1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'


def test_binary_plus_return_type_3():
    q = atlas_xaod_query_ast_visitor()
    q.visit(ast.parse('1+1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'int'


def test_binary_mult_return_type_1():
    q = atlas_xaod_query_ast_visitor()
    q.visit(ast.parse('1.2*1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'


def test_binary_mult_return_type_2():
    q = atlas_xaod_query_ast_visitor()
    q.visit(ast.parse('1*1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'int'


def test_binary_divide_return_type_1():
    q = atlas_xaod_query_ast_visitor()
    q.visit(ast.parse('1.2/1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'


def test_binary_divide_return_type_2():
    q = atlas_xaod_query_ast_visitor()
    q.visit(ast.parse('1/1'))
    r = q._result

    assert isinstance(r, crep.cpp_value)
    assert r.cpp_type().type == 'double'


def test_as_root_rep_already_set():
    q = atlas_xaod_query_ast_visitor()
    node = ast.parse('1/1')
    v = rh.cpp_ttree_rep('junk', 'dude', gc_scope_top_level())
    node.rep = v  # type: ignore

    assert v is q.get_as_ROOT(node)


def test_as_root_as_dict():
    q = atlas_xaod_query_ast_visitor()
    node = ast.parse('1/1')
    dict_obj = crep.cpp_dict({ast.Constant(value='hi'): crep.cpp_value('i', gc_scope_top_level(), ctyp.terminal('int'))}, gc_scope_top_level())
    sequence = crep.cpp_sequence(dict_obj,  # type: ignore
                                 crep.cpp_value('i', gc_scope_top_level(), ctyp.terminal('int')),
                                 gc_scope_top_level())
    node.rep = sequence  # type: ignore
    as_root = q.get_as_ROOT(node)

    assert isinstance(as_root, rh.cpp_ttree_rep)


def test_as_root_as_single_column():
    q = atlas_xaod_query_ast_visitor()
    node = ast.parse('1/1')
    value_obj = crep.cpp_value('i', gc_scope_top_level(), ctyp.terminal('int'))
    sequence = crep.cpp_sequence(value_obj,
                                 crep.cpp_value('i', gc_scope_top_level(), ctyp.terminal('int')),
                                 gc_scope_top_level())
    node.rep = sequence  # type: ignore
    as_root = q.get_as_ROOT(node)

    assert isinstance(as_root, rh.cpp_ttree_rep)


def test_as_root_as_tuple():
    q = atlas_xaod_query_ast_visitor()
    node = ast.parse('1/1')
    value_obj = crep.cpp_tuple((crep.cpp_value('i', gc_scope_top_level(), ctyp.terminal('int')),), gc_scope_top_level())

    sequence = crep.cpp_sequence(value_obj,  # type: ignore
                                 crep.cpp_value('i', gc_scope_top_level(), ctyp.terminal('int')),
                                 gc_scope_top_level())
    node.rep = sequence  # type: ignore
    as_root = q.get_as_ROOT(node)

    assert isinstance(as_root, rh.cpp_ttree_rep)


def test_subscript():
    q = atlas_xaod_query_ast_visitor()
    our_a = ast.Name(id='a')
    our_a.rep = crep.cpp_collection('jets', gc_scope_top_level(), ctyp.collection('int'))  # type: ignore
    node = ast_parse_with_replacement('a[10]', {'a': our_a}).body[0].value  # type: ignore
    as_root = q.get_rep(node)

    assert isinstance(as_root, crep.cpp_value)
    assert as_root.cpp_type() == 'int'
    assert as_root.as_cpp() == 'jets.at(10)'
