import pytest
from func_adl_xAOD.backend import LocalFile
from pathlib import Path
import os

# This mark should be turned off if we want to run long-running tests.
run_long_running_tests = pytest.mark.skipif(True, reason='Long running tests, skipped except when run by hand')
# run_long_running_tests = pytest.mark.skipif(False, reason="ok to run")

# The file we can use in our test. It has only 10 events...
local_path = 'tests/xAODlib/jets_10_events.root'
f_location = Path(os.path.abspath(local_path))
f_single = LocalFile(f_location)
f_multiple = LocalFile([f_location, f_location])
