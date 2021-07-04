from tests.utils.locators import find_line_with
from tests.utils.general import get_lines_of_code
from tests.cms.aod.utils import cms_aod_dataset

# Tests that make sure the cms aod executor is working correctly


class CMS_AOD_File_Type:
    def __init__(self):
        pass


def test_Select_member_variable():
    r = cms_aod_dataset() \
        .SelectMany(lambda e: e.Muons("muons")) \
        .Select(lambda m: m.pfIsolationR04().sumChargedHadronPt) \
        .value()
    lines = get_lines_of_code(r)
    _ = find_line_with(".sumChargedHadronPt", lines)
    assert find_line_with(".sumChargedHadronPt()", lines, throw_if_not_found=False) == -1
