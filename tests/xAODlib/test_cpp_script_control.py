# Tests that will make sure the runner.sh script can do everything it is supposed to do,
# as we are now asking a fair amount from it.
from .control_tests import run_long_running_tests, f
from func_adl_xAOD.backend.xAODlib.exe_atlas_xaod_hash_cache import use_executor_xaod_hash_cache
#pytestmark = run_long_running_tests
import pytest
import tempfile
import os
from typing import cast
import sys
from urllib import parse

from tempfile import TemporaryDirectory

@pytest.yield_fixture()
def cache_directory():
    'Return a directory that can be deleted when the test is done'
    with tempfile.TemporaryDirectory() as d_temp:
        yield d_temp


def generate_test_jet_fetch(cache_dir: str):
    '''
    Generate an expression and C++ files, etc., that contains code for a valid C++ run
    '''
    return f \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsROOTTTree('file.root', "analysis", 'JetPt') \
        .value(executor=lambda a: use_executor_xaod_hash_cache(a, cache_path=cache_dir, no_hash_subdir=True))


def run_docker(info, code_dir: str) -> TemporaryDirectory:
    'Run the docker command'

    # Unravel the file path
    filepaths = info.filelist
    assert len(filepaths) == 1
    filepath_url = cast(str, filepaths[0])
    filepath = parse.urlparse(filepath_url).path[1:]
    base_dir = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    # Write the file list into a filelist in the scripts directory.
    with open(os.path.join(code_dir, 'filelist.txt'), 'w') as f_out:
        f_out.writelines([f'/data/{filename}'])

    results_dir = tempfile.TemporaryDirectory()
    docker_cmd = f'docker run --rm -v {code_dir}:/scripts -v {str(results_dir.name)}:/results -v {base_dir}:/data atlas/analysisbase:21.2.62 /scripts/{info.main_script} /results'
    result = os.system(docker_cmd)
    if result != 0:
        raise BaseException(f"nope, that didn't work {result}!")
    return results_dir


def test_good_cpp_total_run(cache_directory):
    'Good C++, and no arguments that does full run'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_good_cpp_total_run_file_as_arg(cache_directory):
    'Good C++, and no arguments that does full run'

    assert False
    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_bad_cpp_total_run(cache_directory):
    'Bad C++, and no arguments that does full run'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))
    assert False

def test_good_cpp_just_compile(cache_directory):
    'Good C++, and no arguments that does full run'

    assert False
    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_bad_cpp_just_compile(cache_directory):
    'Good C++, and no arguments that does full run'

    assert False
    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_good_cpp_compile_and_run(cache_directory):
    'Good C++, and no arguments that does full run'

    assert False
    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))
