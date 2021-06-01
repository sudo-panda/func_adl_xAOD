
import ast

import pytest
from func_adl.util_ast import function_call
from func_adl_xAOD.atlas.xaod.event_collections import (
    atlas_xaod_collections, atlas_xaod_event_collections)


def test_good_ev_call():
    'Test a good call for an event collection'
    doit = function_call('Jets', [ast.parse('"antikt"').body[0].value])  # type: ignore

    atlas_xaod_event_collections().get_collection(atlas_xaod_collections[0], doit)


def test_good_ev_call_bad_arg_type():
    'Bad collection type'
    doit = function_call('Jets', [ast.parse('55').body[0].value])  # type: ignore

    with pytest.raises(ValueError):
        atlas_xaod_event_collections().get_collection(atlas_xaod_collections[0], doit)


def test_good_ev_call_arg_number_bad():
    'Wrong number of arguments to a collection call'
    doit = function_call('Jets', [ast.parse('"antikt"').body[0].value, ast.parse('55').body[0].value])  # type: ignore

    with pytest.raises(ValueError):
        atlas_xaod_event_collections().get_collection(atlas_xaod_collections[0], doit)
