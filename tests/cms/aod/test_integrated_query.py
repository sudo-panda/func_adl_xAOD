# Contains test that will run the full query.
import asyncio
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import pytest
import uproot
from func_adl import EventDataset, Range
from func_adl_xAOD.common.math_utils import DeltaR
from testfixtures import LogCapture
from tests.cms.aod.config import f_single, run_long_running_tests
from tests.cms.aod.utils import (as_awkward, as_pandas, as_pandas_async,
                                 load_root_as_pandas)

pytestmark = run_long_running_tests

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@pytest.fixture(autouse=True)
def turn_on_logging():
    logging.basicConfig(level=logging.DEBUG)
    yield None
    logging.basicConfig(level=logging.WARNING)


def test_select_pt_of_global_muons():
    training_df = as_pandas(f_single
                            .SelectMany('lambda e: e.TrackMuons("globalMuons")')
                            .Select('lambda m: m.pt()'))

    assert training_df.iloc[0]['col1'] == 10.523032870843785
    assert training_df.iloc[1]['col1'] == 3.914596361447311
    assert training_df.iloc[-1]['col1'] == 29.390803160094887


def test_select_twice_pt_of_global_muons():
    training_df = as_pandas(f_single
                            .SelectMany('lambda e: e.TrackMuons("globalMuons")')
                            .Select('lambda m: m.pt() * 2'))

    assert training_df.iloc[0]['col1'] == 21.04606574168757
    assert training_df.iloc[1]['col1'] == 7.829192722894622
    assert training_df.iloc[-1]['col1'] == 58.78160632018977


def test_select_eta_of_global_muons():
    training_df = as_pandas(f_single
                            .SelectMany('lambda e: e.TrackMuons("globalMuons")')
                            .Select('lambda m: m.eta()'))

    assert training_df.iloc[0]['col1'] == -1.8779354371325043
    assert training_df.iloc[1]['col1'] == -2.127157548674547
    assert training_df.iloc[-1]['col1'] == 0.29603168003675756


def test_select_pt_eta_of_global_muons():
    training_df = as_pandas(f_single
                            .SelectMany('lambda e: e.TrackMuons("globalMuons")')
                            .Select('lambda m: m.pt() + m.eta()'))

    assert training_df.iloc[0]['col1'] == 8.645097433711282
    assert training_df.iloc[1]['col1'] == 1.787438812772764
    assert training_df.iloc[-1]['col1'] == 29.686834840131645

def test_select_hitpattern_of_global_muons():
    sys.setrecursionlimit(10000)
    training_df = as_pandas(f_single
                            .SelectMany(lambda e: e.TrackMuons("globalMuons"))
                            .Select(lambda m: m.hitPattern())
                            .Select(lambda hp: Range(0, hp.numberOfHits()) 
                                .Select(lambda i: hp.getHitPattern(i))))

    assert training_df.iloc[0]['col1'] == 1160.0
    assert training_df.iloc[1]['col1'] == 1168.0
    assert training_df.iloc[-1]['col1'] == 248.0 
