# Test the cpp representations. These objects are quite simple, so there
# aren't that many tests. Mostly when bugs are found something gets added here.
import pytest

import func_adl_xAOD.common_lib.cpp_types as ctyp

from func_adl_xAOD.common_lib.util_scope import top_level_scope


def test_int_pointer():
    t_int = ctyp.terminal('int')
    assert False == t_int.is_pointer()


def test_no_method_type_found():
    assert None == ctyp.method_type_info("bogus", "pt")


def test_method_type_found():
    ctyp.add_method_type_info("bogus", "pt", ctyp.terminal('double'))
    assert 'double' == str(ctyp.method_type_info("bogus", "pt"))


def test_terminal_type():
    t = ctyp.terminal('double', False)
    assert t.type == 'double'


def test_collection():
    c = ctyp.collection('double', False)
    assert c.type == 'std::vector<double>'
