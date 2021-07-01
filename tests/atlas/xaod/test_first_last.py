# Code to do the testing starts here.
from tests.utils.locators import find_line_with, find_open_blocks
from tests.utils.general import get_lines_of_code, print_lines
from tests.atlas.xaod.utils import atlas_xaod_dataset


def test_first_jet_in_event():
    atlas_xaod_dataset() \
        .Select('lambda e: e.Jets("bogus").Select(lambda j: j.pt()).First()') \
        .value()


def test_first_after_selectmany():
    atlas_xaod_dataset() \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .value()


def test_first_after_where():
    # Part of testing that First puts its outer settings in the right place.
    # This also tests First on a collection of objects that hasn't been pulled a part
    # in a select.
    atlas_xaod_dataset() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Where(lambda j: j.pt() > 10).First().pt()') \
        .value()


def test_first_object_in_each_event():
    # Part of testing that First puts its outer settings in the right place.
    # This also tests First on a collection of objects that hasn't been pulled a part
    # in a select.
    atlas_xaod_dataset() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").First().pt()/1000.0') \
        .value()


def test_First_Of_Select_is_not_array():
    # The following statement should be a straight sequence, not an array.
    r = atlas_xaod_dataset() \
        .Select(lambda e:
                {
                    'FirstJetPt': e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt() / 1000.0).Where(lambda jpt: jpt > 10.0).First()
                }) \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert all("push_back" not in ln for ln in lines)
    l_fill = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_fill])
    assert 3 == [(("for" in a) or ("if" in a)) for a in active_blocks].count(True)
    l_set = find_line_with("_FirstJetPt", lines)
    active_blocks = find_open_blocks(lines[:l_set])
    assert 3 == [(("for" in a) or ("if" in a)) for a in active_blocks].count(True)
    l_true = find_line_with("(true)", lines)
    active_blocks = find_open_blocks(lines[:l_true])
    assert 0 == [(("for" in a) or ("if" in a)) for a in active_blocks].count(True)


def test_First_Of_Select_After_Where_is_in_right_place():
    # Make sure that we have the "First" predicate after if Where's if statement.
    r = atlas_xaod_dataset() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0).First()') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    ln = find_line_with(">10.0", lines)
    # Look for the "false" that First uses to remember it has gone by one.
    assert find_line_with("false", lines[ln:], throw_if_not_found=False) > 0
