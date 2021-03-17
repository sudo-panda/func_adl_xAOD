# Contains test that will run the full query.
import asyncio
import logging
import os
import pandas as pd
from pathlib import Path
from tests.cmsAODlib.utils_for_testing import as_awkward, as_pandas, as_pandas_async, load_root_as_pandas

import pytest
import uproot
from func_adl import EventDataset
from func_adl_xAOD.cpplib.math_utils import DeltaR
from testfixtures import LogCapture

from tests.cmsAODlib.control_tests import f_single, run_long_running_tests

pytestmark = run_long_running_tests

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@pytest.fixture(autouse=True)
def turn_on_logging():
    logging.basicConfig(level=logging.DEBUG)
    yield None
    logging.basicConfig(level=logging.WARNING)

def test_select_pt_of_global_muons():
    training_df = as_pandas(f_single \
        .SelectMany('lambda e: e.Muons("globalMuons")') \
        .Select('lambda m: m.pt()'))
    
    assert training_df.iloc[0]['col1'] == 2.587212580137943
    assert training_df.iloc[1]['col1'] == 9.61424481835254
    assert training_df.iloc[-1]['col1'] == 6.501343718188815

