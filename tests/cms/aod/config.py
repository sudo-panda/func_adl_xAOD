import os
from pathlib import Path

import pytest
from tests.cms.aod.utils import CMSAODLocalFile

# This mark should be turned off if we want to run long-running tests.
run_long_running_tests = pytest.mark.cms_aod_runner

# The file we can use in our test. It has only 10 events...
# The CMS test file is 10 events from root://eospublic.cern.ch//eos/opendata/cms/MonteCarlo2011/Summer11LegDR/SMHiggsToZZTo4L_M-125_7TeV-powheg15-JHUgenV3-pythia6/AODSIM/PU_S13_START53_LV6-v1/20000/08CD3ECC-4C92-E411-B001-0025907B4F20.root
# f_location = Path('root://eospublic.cern.ch//eos/opendata/cms/Run2012C/DoubleMuParked/AOD/22Jan2013-v1/10000/F2878994-766C-E211-8693-E0CB4EA0A939.root')
local_path = 'tests/cms/aod/sample_cms_opendata_1507_0025907B4F20.root'
f_location = Path(os.path.abspath(local_path))
f_single = CMSAODLocalFile(f_location)
f_multiple = CMSAODLocalFile([f_location, f_location])
