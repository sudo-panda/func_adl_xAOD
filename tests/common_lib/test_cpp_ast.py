import pytest

from func_adl_xAOD.common_lib.math_utils import DeltaR

from tests.atlas_xAOD_lib.utils_for_testing import dataset_for_testing


def test_deltaR_call():
    r = dataset_for_testing().Select('lambda e: DeltaR(1.0, 1.0, 1.0, 1.0)').value()
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())


def test__bad_deltaR_call():
    with pytest.raises(ValueError):
        dataset_for_testing().Select('lambda e: DeltaR(1.0, 1.0, 1.0)').value()
