# Test out the hash cache generator
from func_adl_xAOD.backend.xAODlib.exe_atlas_xaod_hash_cache import use_executor_xaod_hash_cache, CacheExeException
from func_adl import EventDataset
import pytest
import tempfile
import ast
import os
import shutil

async def do_exe(a):
    return a

@pytest.fixture
def local_cache_dir():
    with tempfile.TemporaryDirectory() as local_run_dir:
        cache_dir = os.path.join(local_run_dir, 'cache')
        yield cache_dir

def build_ast() -> ast.AST:
    return EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .AsROOTTTree('dude.root', 'forkme', 'JetPt') \
        .value(executor=do_exe)

def build_ast_dr() -> ast.AST:
    return EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .Select('lambda e: DeltaR(e.eta(), e.phi(), e.eta(), e.phi())') \
        .AsROOTTTree('dude.root', 'forkme', 'JetPt') \
        .value(executor=do_exe)

def build_ast_pandas() -> ast.AST:
    return EventDataset("file://root.root") \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .AsPandasDF('JetPt') \
        .value(executor=do_exe)

def build_ast_mark() -> ast.AST:
    return EventDataset('file://root.root') \
            .Select('lambda e: (e.Electrons("Electrons"), e.Muons("Muons"))') \
            .Select('lambda e: (e[0].Select(lambda ele: ele.E()), e[0].Select(lambda ele: ele.pt()), e[0].Select(lambda ele: ele.phi()), e[0].Select(lambda ele: ele.eta()), e[1].Select(lambda mu: mu.E()), e[1].Select(lambda mu: mu.pt()), e[1].Select(lambda mu: mu.phi()), e[1].Select(lambda mu: mu.eta()))') \
            .AsROOTTTree('dude.root', 'forkme', ['e_E', 'e_pt', 'e_phi', 'e_eta', 'mu_E', 'mu_pt', 'mu_phi', 'mu_eta']) \
            .value(executor=do_exe)

def test_no_cache_ever(local_cache_dir):
    # Item hasn't been cached before.
    r = use_executor_xaod_hash_cache(build_ast(), local_cache_dir)
    assert r is not None
    assert len(r.filelist) == 1
    assert r.filelist[0] == 'file:///root.root'
    assert os.path.exists(f'{local_cache_dir}/{r.hash}/{r.main_script}')
    assert r.treename.startswith('forkme')
    # Because it isn't easy to change this in the ATLAS framework
    assert r.output_filename == 'ANALYSIS.root'

def test_marcs_generates_cpp_code(local_cache_dir, ):
    r = use_executor_xaod_hash_cache(build_ast_mark(), local_cache_dir)
    assert r is not None


def test_deltaR(local_cache_dir):
    'Make sure there is no exception when doing a deltaR'
    use_executor_xaod_hash_cache(build_ast_dr(), local_cache_dir)


def test_cant_cache_non_root(local_cache_dir):
    try:
        use_executor_xaod_hash_cache(build_ast_pandas(), local_cache_dir)
        assert False
    except CacheExeException:
        pass

def test_twice(local_cache_dir):
    # Item hasn't been cached before.
    _ = use_executor_xaod_hash_cache(build_ast(), local_cache_dir)
    r = use_executor_xaod_hash_cache(build_ast(), local_cache_dir)
    assert r is not None
    assert len(r.filelist) == 1
    assert r.filelist[0] == 'file:///root.root'
    assert os.path.exists(f'{local_cache_dir}/{r.hash}/{r.main_script}')
    assert r.treename.startswith('forkme')
    # Because it isn't easy to change this in the ATLAS framework
    assert r.output_filename == 'ANALYSIS.root'
