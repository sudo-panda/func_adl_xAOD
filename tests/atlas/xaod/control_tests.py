import os
import pytest

from pathlib import Path
from .LocalFile import LocalFile

# This mark should be turned off if we want to run long-running tests.
run_long_running_tests = pytest.mark.xaod_runner

# The file we can use in our test. It has only 10 events...
local_path = 'tests/atlas/xaod/jets_10_events.root'
f_location = Path(os.path.abspath(local_path))
f_single = LocalFile(f_location)
f_multiple = LocalFile([f_location, f_location])
