import pytest

from tests.atlas.xaod.utils_for_testing import (dataset_for_testing,
                                                exe_from_qastle,
                                                find_line_numbers_with,
                                                find_line_with, find_open_blocks,
                                                get_lines_of_code, print_lines)


def test_get_attribute_float():
    # The following statement should be a straight sequence, not an array.
    r = dataset_for_testing() \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.getAttributeFloat("emf"))') \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_attribute = find_line_with("getAttribute", lines)
    assert 'getAttribute<float>("emf")' in lines[l_attribute]


def test_get_attribute_float_wrong_args():
    with pytest.raises(Exception) as e:
        dataset_for_testing() \
            .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.getAttributeFloat())') \
            .value()

    assert 'getAttribute' in str(e.value)


def test_get_attribute_float_wrong_arg_type():
    with pytest.raises(Exception) as e:
        dataset_for_testing() \
            .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.getAttributeFloat(1))') \
            .value()

    assert 'getAttribute' in str(e.value)


def test_get_attribute_vector_float():
    # The following statement should be a straight sequence, not an array.
    r = dataset_for_testing() \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .SelectMany('lambda j: j.getAttributeVectorFloat("emf")') \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_attribute = find_line_with("getAttribute", lines)
    assert 'getAttribute<std::vector<double>>("emf")' in lines[l_attribute]


def test_get_attribute_vector_float_wrong_args():
    with pytest.raises(Exception) as e:
        dataset_for_testing() \
            .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
            .SelectMany('lambda j: j.getAttributeVectorFloat("emf", 22)') \
            .value()

    assert 'getAttributeVectorFloat' in str(e.value)


def test_get_attribute_vector_float_wrong_arg_type():
    with pytest.raises(Exception) as e:
        dataset_for_testing() \
            .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
            .SelectMany('lambda j: j.getAttributeVectorFloat(1)') \
            .value()

    assert 'getAttributeVectorFloat' in str(e.value)


def test_get_attribute():
    with pytest.raises(Exception) as e:
        dataset_for_testing() \
            .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.getAttribute("emf"))') \
            .value()

    assert "getAttributeFloat" in str(e.value)
