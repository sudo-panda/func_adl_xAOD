from func_adl_xAOD.backend.xAODlib.utils import most_accurate_type
import func_adl_xAOD.backend.cpplib.cpp_types as ctyp

def test_accurate_type_single_int():
    t = ctyp.terminal('int', False)
    r = most_accurate_type([t])
    assert r._type == 'int'

def test_accurate_type_single_float():
    t = ctyp.terminal('float', False)
    r = most_accurate_type([t])
    assert r._type == 'float'

def test_accurate_type_two_int():
    t1 = ctyp.terminal('int', False)
    t2 = ctyp.terminal('int', False)
    r = most_accurate_type([t1, t2])
    assert r._type == 'int'

def test_accurate_type_int_and_float():
    t1 = ctyp.terminal('int', False)
    t2 = ctyp.terminal('float', False)
    r = most_accurate_type([t1, t2])
    assert r._type == 'float'

def test_accurate_type_float_and_double():
    t1 = ctyp.terminal('double', False)
    t2 = ctyp.terminal('float', False)
    r = most_accurate_type([t1, t2])
    assert r._type == 'double'
