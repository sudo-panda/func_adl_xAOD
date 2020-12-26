# Contains test that will run the full query.
import asyncio
from enum import auto
import logging
import os
from pathlib import Path

from func_adl import EventDataset
import pytest
import uproot

from func_adl_xAOD.cpplib.math_utils import DeltaR
from testfixtures import LogCapture

from .control_tests import f_single, run_long_running_tests

# These are *long* tests and so should not normally be run. Each test can take of order 30 seconds or so!!
pytestmark = run_long_running_tests

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # type: ignore

@pytest.fixture(autouse=True)
def turn_on_logging():
    logging.basicConfig(level=logging.DEBUG)
    yield None
    logging.basicConfig(level=logging.WARNING)

def test_select_first_of_array():
    # The hard part is that First() here does not return a single item, but, rather, an array that
    # has to be aggregated over.
    training_df = f_single \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
            .AsPandasDF('dude') \
            .value()
    assert training_df.iloc[0]['dude'] == 1897
    assert training_df.iloc[1]['dude'] == 605
    assert training_df.iloc[-1]['dude'] == 336

@pytest.yield_fixture()
def event_loop():
    'Get the loop done right on windows'
    if os.name == 'nt':
        loop = asyncio.ProactorEventLoop()  # type: ignore
    else:
        loop = asyncio.SelectorEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_two_simultaneous_runs():
    # Test the future return stuff
    f_training_df_1 = f_single \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
            .AsPandasDF('dude') \
            .value_async()
    f_training_df_2 = f_single \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
            .AsPandasDF('dude') \
            .value_async()
    r1, r2 = await asyncio.gather(f_training_df_1, f_training_df_2)
    assert r1.iloc[0]['dude'] == 1897
    assert r2.iloc[0]['dude'] == 1897

def test_flatten_array():
    # A very simple flattening of arrays
    training_df = f_single \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsPandasDF('JetPt') \
        .value()
    assert int(training_df.iloc[0]['JetPt']) == 257
    assert int(training_df.iloc[0]['JetPt']) != int(training_df.iloc[1]['JetPt'])

def test_simple_dict_output():
    # A very simple flattening of arrays
    training_df = f_single \
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets")) \
        .Select(lambda j: {
            'JetPt': j.pt()/1000.0
            }) \
        .value()
    assert isinstance(training_df, Path)
    assert training_df.exists()

    with uproot.open(training_df) as input:
        pd = input['xaod_tree'].pandas.df()  # type: ignore
    print(pd)
    assert int(pd.iloc[0]['JetPt']) == 257
    assert int(pd.iloc[0]['JetPt']) != int(pd.iloc[1]['JetPt'])


def test_single_column_output():
    # A very simple flattening of arrays
    training_df = f_single \
        .SelectMany(lambda e: e.Jets("AntiKt4EMTopoJets")) \
        .Select(lambda j: j.pt()/1000.0) \
        .value()
    assert isinstance(training_df, Path)
    assert training_df.exists()

    with uproot.open(training_df) as input:
        pd = input['xaod_tree'].pandas.df()  # type: ignore
    print(pd)
    assert int(pd.iloc[0]['col1']) == 257
    assert int(pd.iloc[0]['col1']) != int(pd.iloc[1]['col1'])


def test_First_two_outer_loops():
    # THis is a little tricky because the First there is actually running over one jet in the event. Further, the Where
    # on the number of tracks puts us another level down. So it is easy to produce code that compiles, but the First's if statement
    # is very much in the wrong place.
    training_df = f_single \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0)).First().Count()') \
            .AsPandasDF('dude') \
            .value()
    assert training_df.iloc[0]['dude'] == 693


def test_not_in_where():
    # THis is a little tricky because the First there is actually running over one jet in the event. Further, the Where
    # on the number of tracks puts us another level down. So it is easy to produce code that compiles, but the First's if statement
    # is very much in the wrong place.
    training_df = f_single \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles").Where(lambda t: not (t.pt() > 1000.0))).First().Count()') \
            .AsPandasDF('dude') \
            .value()
    assert training_df.iloc[0]['dude'] == 1204


def test_first_object_in_event():
    # Make sure First puts it if statement in the right place.
    training_df = f_single \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").First().pt()/1000.0') \
        .AsPandasDF('FirstJetPt') \
        .value()
    assert int(training_df.iloc[0]['FirstJetPt']) == 257

def test_no_reported_statistics():
    'Look at the log file and report if it contains a statistics line'

    with LogCapture() as l_cap:
        f_single \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").First().pt()/1000.0') \
            .AsPandasDF('FirstJetPt') \
            .value()
        assert str(l_cap).find('TFileAccessTracer   INFO    Sending') == -1

def test_first_object_in_event_with_where():
    # Make sure First puts it's if statement in the right place.
    training_df = f_single \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0).First()') \
        .AsPandasDF('FirstJetPt') \
        .value()
    assert int(training_df.iloc[0]['FirstJetPt']) == 257
    assert len(training_df) == 10

def test_truth_particles():
    training_df = f_single \
        .Select("lambda e: e.TruthParticles('TruthParticles').Count()") \
        .AsPandasDF('NTruthParticles') \
        .value()
    assert training_df.iloc[0]['NTruthParticles'] == 1557

def test_truth_particles_awk():
    training_df = f_single \
        .Select("lambda e: e.TruthParticles('TruthParticles').Count()") \
        .AsAwkwardArray('NTruthParticles') \
        .value()
    print (training_df)
    assert len(training_df[b'NTruthParticles']) == 10

def test_1D_array():
    # A very simple flattening of arrays
    training_df = f_single \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0)') \
        .AsAwkwardArray('JetPt') \
        .value()
    print (training_df)    
    assert len(training_df[b'JetPt']) == 10
    assert len(training_df[b'JetPt'][0]) == 32

def test_2D_array():
    # A very simple flattening of arrays
    training_df = f_single \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.Jets("AntiKt4EMTopoJets").Select(lambda j1: j1.pt()/1000.0))') \
        .AsAwkwardArray('JetPt') \
        .value()
    print (training_df)    
    assert len(training_df[b'JetPt']) == 10
    assert len(training_df[b'JetPt'][0]) == 32
    assert len(training_df[b'JetPt'][0][0]) == 32

def test_2D_nested_where():
    # Seen in the wild as generating bad C++.
    training_df = f_single \
        .Select('lambda e0304: (e0304.Jets("AntiKt4EMTopoJets"), e0304)') \
        .Select('lambda e0305: (e0305[0].Where(lambda e0352: (((e0352.pt() / 1000.0) > 20)) and (((abs(e0352.eta())) < 1.5))), e0305[1])') \
        .Select('lambda e0317: e0317[0].Select(lambda e0353: e0317[1].TruthParticles("TruthParticles").Where(lambda e0345: (e0345.pdgId() == 11)).Where(lambda e0346: (((e0346.pt() / 1000.0) > 20)) and (((abs(e0346.eta())) < 1.5))).Where(lambda e0347: (DeltaR(e0353.eta(), e0353.phi(), e0347.eta(), e0347.phi()) < 0.5)))') \
        .Select('lambda e0348: e0348.Select(lambda e0354: e0354.Count())') \
        .AsAwkwardArray('NTruthParticles') \
        .value()
    
    print(training_df)
    a = training_df[b'NTruthParticles']
    assert a.shape[0] == 10
    assert a[0].shape[0] == 8
