import pytest
from func_adl_xAOD.common.math_utils import DeltaR
from tests.atlas.xaod.utils import atlas_xaod_dataset


def test_deltaR_call():
    r = atlas_xaod_dataset().Select(lambda e: DeltaR(1.0, 1.0, 1.0, 1.0)).value()
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())


def test__bad_deltaR_call():
    with pytest.raises(ValueError):
        atlas_xaod_dataset().Select(lambda e: DeltaR(1.0, 1.0, 1.0)).value()  # type: ignore
