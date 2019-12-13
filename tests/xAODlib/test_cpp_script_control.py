# Tests that will make sure the runner.sh script can do everything it is supposed to do,
# as we are now asking a fair amount from it.
from .control_tests import run_long_running_tests, f
from func_adl_xAOD.backend.xAODlib.exe_atlas_xaod_hash_cache import use_executor_xaod_hash_cache
#pytestmark = run_long_running_tests
import pytest
import tempfile
import os
from typing import cast, Optional
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


def generate_test_jet_fetch_bad(cache_dir: str):
    '''
    Generate an expression and C++ files, etc., that contains code for a invalid C++ run
    '''
    return f \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.ptt()/1000.0') \
        .AsROOTTTree('file.root', "analysis", 'JetPt') \
        .value(executor=lambda a: use_executor_xaod_hash_cache(a, cache_path=cache_dir, no_hash_subdir=True))


class docker_run_error(BaseException):
    def __init__(self, message):
        BaseException.__init__(self, message)


def run_docker(info, code_dir: str, data_file_on_cmd_line:bool = False,
               compile_only:bool = False, run_only:bool = False,
               add_position_argument_at_start:Optional[str] = None,
               extra_flag:Optional[str] = None) -> TemporaryDirectory:
    'Run the docker command'

    # Unravel the file path. How we do this depends on how we are doing this work.
    filepaths = info.filelist
    assert len(filepaths) == 1
    filepath_url = cast(str, filepaths[0])
    filepath = parse.urlparse(filepath_url).path[1:]
    base_dir = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    # Write the file list into a filelist in the scripts directory. If that isn't going to be what we do, then
    # create it as a cmd line option.
    cmd_options = ''
    if data_file_on_cmd_line:
        cmd_options += f'-d /data/{filename} '
    else:
        with open(os.path.join(code_dir, 'filelist.txt'), 'w') as f_out:
            f_out.writelines([f'/data/{filename}'])

    # Compile or run only?
    if compile_only:
        cmd_options += '-c '
    if run_only:
        cmd_options += '-r '

    # Extra random flag
    if extra_flag is not None:
        cmd_options += f'{extra_flag} '
    
    # Add an argument at the start?
    initial_args = ''
    if add_position_argument_at_start is not None:
        initial_args = f'{add_position_argument_at_start} '

    # Docker command
    results_dir = tempfile.TemporaryDirectory()
    docker_cmd = f'docker run --rm -v {code_dir}:/scripts -v {str(results_dir.name)}:/results -v {base_dir}:/data atlas/analysisbase:21.2.62 /scripts/{info.main_script} {initial_args} {cmd_options}'
    result = os.system(docker_cmd)
    if result != 0:
        raise docker_run_error(f"nope, that didn't work {result}!")
    return results_dir


def test_good_cpp_total_run(cache_directory):
    'Good C++, and no arguments that does full run'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_good_cpp_total_run_file_as_arg(cache_directory):
    'Bad C++ generated, should throw an exception'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory, data_file_on_cmd_line=True) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_bad_cpp_total_run(cache_directory):
    'Bad C++, and no arguments that does full run'

    try:
        info = generate_test_jet_fetch_bad(cache_directory)
        with run_docker(info, cache_directory, data_file_on_cmd_line=True) as result_dir:
            assert False
    except docker_run_error:
        pass

def test_good_cpp_just_compile(cache_directory):
    'Good C++, only do the compile'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory, compile_only=True) as result_dir:
        assert not os.path.exists(os.path.join(result_dir, info.output_filename))

def test_bad_cpp_just_compile(cache_directory):
    'Bad C++, only do the compile'

    try:
        info = generate_test_jet_fetch_bad(cache_directory)
        with run_docker(info, cache_directory, compile_only=True) as result_dir:
            assert False
    except docker_run_error:
        pass

def test_good_cpp_compile_and_run(cache_directory):
    'Good C++, first do the compile, and then do the run'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory, compile_only=True) as result_dir1:
        with run_docker(info, cache_directory, run_only=True) as result_dir2:
            assert os.path.exists(os.path.join(result_dir2, info.output_filename))

def test_run_with_bad_position_arg(cache_directory):
    'Pass in a bogus argument at the end with no flag'
    try:
        info = generate_test_jet_fetch(cache_directory)
        with run_docker(info, cache_directory, add_position_argument_at_start="/results") as result_dir:
            assert False
    except docker_run_error:
        pass

def test_run_with_bad_flag(cache_directory):
    'Pass in a bogus flag'
    try:
        info = generate_test_jet_fetch(cache_directory)
        with run_docker(info, cache_directory, extra_flag="-k") as result_dir:
            assert False
    except docker_run_error:
        pass
