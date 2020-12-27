# Test the simple type information system.

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
# Code to do the testing starts here.
from tests.xAODlib.utils_for_testing import dataset_for_testing
from func_adl import EventDataset
import func_adl_xAOD.cpplib.cpp_types as ctyp
from func_adl_xAOD.xAODlib.ast_to_cpp_translator import xAODTranslationError


def test_cant_call_double():
    msg = ""
    try: 
        dataset_for_testing("file://root.root") \
            .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt().eta()).Sum()") \
            .value()
    except xAODTranslationError as e:
        msg = str(e)

    assert 'Unable to call method eta on type double' in msg


def test_can_call_prodVtx():
    ctyp.add_method_type_info("xAOD::TruthParticle", "prodVtx", ctyp.terminal('xAODTruth::TruthVertex', is_pointer=True))
    dataset_for_testing("file://root.root") \
        .Select("lambda e: e.TruthParticles('TruthParticles').Select(lambda t: t.prodVtx().x()).Sum()") \
        .value()
