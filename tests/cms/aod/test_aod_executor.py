from tests.utils.locators import find_line_with, find_next_closing_bracket
from tests.utils.general import get_lines_of_code, print_lines
from tests.cms.aod.utils import cms_aod_dataset
from func_adl_xAOD.cms.aod import isNonnull

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


def test_complex_dict():
    'Seen to fail in the wild, so a test case to track'
    r = cms_aod_dataset() \
        .Select(lambda e: {"muons": e.Muons("muons"), "primvtx": e.Vertex("offlinePrimaryVertices")}) \
        .Select(lambda i: i.muons
                .Where(lambda m: isNonnull(m.globalTrack()))
                .Select(lambda m: m.globalTrack().dx(i.primvtx[0].position()))
                ) \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)

    find_line_with("globalTrack()->dx", lines)
    find_line_with("at(0).position()", lines)


def test_2nd_order_lookup():
    'Seen in the wild to generate an out-of-scope error'
    r = (cms_aod_dataset()
         .Select(lambda e: {"m": e.Muons("muons"), "p": e.Vertex("offlinePrimaryVertices")[0].position()})
         .Select(lambda i:
                 i.m
                 .Where(lambda m: m.isPFMuon()
                        and m.isPFIsolationValid()
                        and isNonnull(m.globalTrack())
                        and abs((m.globalTrack()).dxy(i.p)) < 0.5
                        and abs((m.globalTrack()).dz(i.p)) < 1.
                        )
                 .Select(lambda m: m.p()),
                 )
         .value()
         )

    lines = get_lines_of_code(r)
    print_lines(lines)

    # Make sure the vertex line isn't used after it goes out of scope
    vertex_decl_line = find_line_with('edm::Handle<reco::VertexCollection>', lines)

    vertex_variable_name = lines[vertex_decl_line].split(' ')[-1].strip(';')

    closing_scope = find_next_closing_bracket(lines[vertex_decl_line:])
    vertex_used_too_late = find_line_with(vertex_variable_name, lines[vertex_decl_line + closing_scope:], throw_if_not_found=False)
    if vertex_used_too_late != -1:
        print('Here is where it is used and down')
        print_lines(lines[closing_scope + vertex_decl_line + vertex_used_too_late:])
    assert vertex_used_too_late == -1
