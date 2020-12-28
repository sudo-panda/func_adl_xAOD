import func_adl_xAOD.cpplib.cpp_representation as crep
import func_adl_xAOD.cpplib.cpp_types as ctyp
import pytest
from func_adl_xAOD.xAODlib.util_scope import (gc_scope_top_level,
                                              top_level_scope)


def test_expression_pointer_decl():
    e2 = crep.cpp_value("dude", top_level_scope(), ctyp.terminal("int"))
    assert False == e2.is_pointer()

    e3 = crep.cpp_value("dude", top_level_scope(), ctyp.terminal("int", is_pointer=True))
    assert True == e3.is_pointer()


def test_cpp_value_as_str():
    'Make sure we can generate a str from a value - this will be important for errors'
    v1 = crep.cpp_value('dude', top_level_scope(), ctyp.terminal('int'))
    assert 'dude' in str(v1)

    v2 = crep.cpp_value('dude', top_level_scope(), None)
    assert 'dude' in str(v2)


def test_variable_type_update():
    tc = gc_scope_top_level()
    expr = "a"
    ctype = ctyp.terminal('int', False)

    v = crep.cpp_variable(expr, tc, ctype)
    v.update_type(ctyp.terminal('float', False))

    assert v.cpp_type().type == 'float'


def test_variable_pointer():
    'Make sure is_pointer can deal with a non-type correctly'
    v1 = crep.cpp_value('dude', top_level_scope(), ctyp.terminal('int'))
    v2 = crep.cpp_value('dude', top_level_scope(), None)

    assert not v1.is_pointer()
    with pytest.raises(RuntimeError) as e:
        v2.is_pointer()


def test_variable_pointer():
    'Make sure is_pointer can deal with a non-type correctly'
    v1 = crep.cpp_value('dude', top_level_scope(), ctyp.terminal('int'))
    v2 = crep.cpp_value('dude', top_level_scope(), None)

    assert v1.cpp_type().type == 'int'
    with pytest.raises(RuntimeError) as e:
        v2.cpp_type()


def test_variable_type__with_initial_update():
    tc = gc_scope_top_level()
    expr = "a"
    c_type = ctyp.terminal('int', False)
    c_init = crep.cpp_value('0.0', tc, ctyp.terminal('int', False))

    v = crep.cpp_variable(expr, tc, c_type, c_init)
    v.update_type(ctyp.terminal('float', False))

    assert v.cpp_type().type == 'float'
    assert v.initial_value().cpp_type().type == 'float'

def test_sequence_type():
    tc = gc_scope_top_level()
    s_value = crep.cpp_value('0.0', tc, ctyp.terminal('int', False))
    i_value = crep.cpp_value('1.0', tc, ctyp.terminal('object', False))

    seq = crep.cpp_sequence(s_value, i_value, tc)

    assert seq.sequence_value().cpp_type().type == 'int'


def test_sequence_type():
    tc = gc_scope_top_level()
    s_value = crep.cpp_value('0.0', tc, ctyp.terminal('int', False))
    i_value = crep.cpp_value('1.0', tc, ctyp.terminal('object', False))

    seq = crep.cpp_sequence(s_value, i_value, tc)
    seq_array = crep.cpp_sequence(seq, i_value, tc)

    assert seq_array.sequence_value().cpp_type().type == 'std::vector<int>'
