import os
import pytest

from pathlib import Path

from tests.cms_AOD_lib.LocalFile import LocalFile

# This mark should be turned off if we want to run long-running tests.
run_long_running_tests = pytest.mark.xaod_runner

# The file we can use in our test. It has only 10 events...
# local_path = 'tests/xAOD_lib/jets_10_events.root'
# f_location = Path(os.path.abspath(local_path))
f_location = 'root://eospublic.cern.ch//eos/opendata/cms/Run2012C/DoubleMuParked/AOD/22Jan2013-v1/10000/F2878994-766C-E211-8693-E0CB4EA0A939.root'
f_single = LocalFile(f_location)
f_multiple = LocalFile([f_location, f_location])
