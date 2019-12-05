# A few tests on the LINQ ast functionality
from func_adl import EventDataset
from func_adl_xAOD.backend.util_LINQ import find_dataset, extract_dataset_info
import ast

async def do_exe(a):
    return a

def test_find_EventDataSet_good():
    a = EventDataset("file://junk.root") \
        .value(executor=do_exe)

    assert isinstance(a, ast.Call)
    d = extract_dataset_info(a)
    assert ["file:///junk.root"] == d

def test_find_EventDataSet_none():
    a = ast.parse("a+b*2")

    try:
        find_dataset(a)
        assert False
    except:
        pass

def test_find_EventDataset_Select():
    a = EventDataset("file://dude.root") \
        .Select("lambda x: x") \
        .value(executor=do_exe)

    assert ["file:///dude.root"] == extract_dataset_info(find_dataset(a))

def test_find_EventDataset_SelectMany():
    a = EventDataset("file://dude.root") \
        .SelectMany("lambda x: x") \
        .value(executor=do_exe)

    assert ["file:///dude.root"] == extract_dataset_info(find_dataset(a))

def test_find_EventDataset_Select_and_Many():
    a = EventDataset("file://dude.root") \
        .Select("lambda x: x") \
        .SelectMany("lambda x: x") \
        .value(executor=do_exe)

    assert ["file:///dude.root"] == extract_dataset_info(find_dataset(a))