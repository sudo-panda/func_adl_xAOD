from func_adl_xAOD.cms.aod import isNonnull
from tests.cms.aod.utils import cms_aod_dataset


def test_isnonnull_call():
    r = cms_aod_dataset().Select(lambda e: isNonnull(e)).value()
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "bool" == str(vs[0].cpp_type())
