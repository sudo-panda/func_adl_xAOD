# Contains test that will run the full query.
import os
import pytest
import uproot
import asyncio
import logging
import pandas as pd

from pathlib import Path
from testfixtures import LogCapture

from func_adl import EventDataset
from func_adl_xAOD.common_lib.math_utils import DeltaR

from tests.cms_AOD_lib.control_tests import f_single, run_long_running_tests
from tests.cms_AOD_lib.utils_for_testing import as_awkward, as_pandas, as_pandas_async, load_root_as_pandas

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
                            .SelectMany('lambda e: e.Muons("globalMuons")')
                            .Select('lambda m: m.pt()'))

    assert training_df.iloc[0]['col1'] == 2.587212580137943
    assert training_df.iloc[1]['col1'] == 9.61424481835254
    assert training_df.iloc[-1]['col1'] == 6.501343718188815


def test_select_twice_pt_of_global_muons():
    training_df = as_pandas(f_single
                            .SelectMany('lambda e: e.Muons("globalMuons")')
                            .Select('lambda m: m.pt() * 2'))

    assert training_df.iloc[0]['col1'] == 5.174425160275886
    assert training_df.iloc[1]['col1'] == 19.22848963670508
    assert training_df.iloc[-1]['col1'] == 13.00268743637763


def test_select_eta_of_global_muons():
    training_df = as_pandas(f_single
                            .SelectMany('lambda e: e.Muons("globalMuons")')
                            .Select('lambda m: m.eta()'))

    assert training_df.iloc[0]['col1'] == 1.8461242323191596
    assert training_df.iloc[1]['col1'] == 1.3034489505966336
    assert training_df.iloc[-1]['col1'] == 1.0993582143911786


def test_select_pt_eta_of_global_muons():
    training_df = as_pandas(f_single
                            .SelectMany('lambda e: e.Muons("globalMuons")')
                            .Select('lambda m: m.pt() + m.eta()'))

    assert training_df.iloc[0]['col1'] == 4.433336812457103
    assert training_df.iloc[1]['col1'] == 10.917693768949174
    assert training_df.iloc[-1]['col1'] == 7.6007019325799945
