# Test out substituting in routines of various types

from func_adl_xAOD.backend.cpplib.math_utils import DeltaR
from func_adl import EventDataset
from tests.xAODlib.utils_for_testing import exe_for_test

def test_deltaR_call():
    r=EventDataset("file://root.root").Select('lambda e: DeltaR(1.0, 1.0, 1.0, 1.0)').AsROOTTTree('root.root', 'analysis', 'RunNumber').value(executor=exe_for_test)
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())
