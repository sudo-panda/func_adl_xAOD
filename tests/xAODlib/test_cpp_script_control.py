# Tests that will make sure the runner.sh script can do everything it is supposed to do,
# as we are now asking a fair amount from it.
import ast
from collections import namedtuple

from func_adl import EventDataset
from func_adl_xAOD.xAODlib.atlas_xaod_executor import atlas_xaod_executor
import os
import sys
import tempfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, List, Optional, Union, cast
from urllib import parse

import pytest

from .control_tests import local_path, run_long_running_tests

pytestmark = run_long_running_tests

ExecutorInfo = namedtuple('ExecutorInfo', 'main_script output_filename')

class hash_event_dataset(EventDataset):
    def __init__(self, output_dir: Path):
        super().__init__()
        self._dir = output_dir

    async def execute_result_async(self, a: ast.AST) -> Any:
        if self._dir.exists():
            self._dir.mkdir(parents=True, exist_ok=True)
        exe = atlas_xaod_executor()
        f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), self._dir)
        return ExecutorInfo(f_spec.main_script, f_spec.result_rep.filename)


@pytest.yield_fixture()
def cache_directory():
    'Return a directory that can be deleted when the test is done'
    with tempfile.TemporaryDirectory() as d_temp:
        yield Path(d_temp)


def generate_test_jet_fetch(cache_dir: Path):
    '''
    Generate an expression and C++ files, etc., that contains code for a valid C++ run
    '''
    return hash_event_dataset(cache_dir) \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsROOTTTree('file.root', "analysis", 'JetPt') \
        .value()


def generate_test_jet_fetch_bad(cache_dir: Path):
    '''
    Generate an expression and C++ files, etc., that contains code for a valid C++ run
    '''
    return hash_event_dataset(cache_dir) \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.ptt()/1000.0') \
        .AsROOTTTree('file.root', "analysis", 'JetPt') \
        .value()


class docker_run_error(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)



class docker_runner:
    def __init__ (self, name: str, results_dir):
        self._name = name
        self.results_dir = results_dir

    def compile(self, info):
        'Run the script as a compile'

        results_dir = tempfile.TemporaryDirectory()
        docker_cmd = f'docker exec {self._name} /bin/bash -c "cd /home/atlas; /scripts/{info.main_script} -c"'
        result = os.system(docker_cmd)
        if result != 0:
            raise docker_run_error(f"nope, that didn't work {result}!")
        return results_dir

    def run(self, info: ExecutorInfo, files: List[Path]):
        'Run the docker command'

        # Unravel the file path. How we do this depends on how we are doing this work.
        filename = files[0].name

        # Write the file list into a filelist in the scripts directory. If that isn't going to be what we do, then
        # create it as a cmd line option.
        cmd_options = ''
        cmd_options += f'-d /data/{filename} '

        # We are just going to run
        cmd_options += '-r '

        # Docker command
        results_dir = tempfile.TemporaryDirectory()
        docker_cmd = f'docker exec {self._name} /bin/bash -c "cd /home/atlas; /scripts/{info.main_script} {cmd_options}"'
        result = os.system(docker_cmd)
        if result != 0:
            raise docker_run_error(f"nope, that didn't work {result}!")
        return results_dir

class docker_running_container:
    '''
    This will start up a docker container running our analysis base.
    '''
    def __init__(self, info, code_dir:str, files: List[Path]):
        'Init with directories for mapping, etc'
        
        self._code_dir = code_dir
        self._files = files

    def __enter__(self):
        'Get the docker command up and running'
        data_dir = self._files[0].parent
        self._results_dir = tempfile.TemporaryDirectory()
        docker_cmd = f'docker run --name test_func_xAOD --rm -d -v {self._code_dir}:/scripts:ro -v {str(self._results_dir.name)}:/results -v {data_dir.absolute()}:/data:ro atlas/analysisbase:latest /bin/bash -c "while [ 1 ] ; do sleep 1; echo hi ; done"'
        r = os.system(docker_cmd)
        if r != 0:
            raise Exception(f'Unable to start docker deamon: {r}')
        return docker_runner('test_func_xAOD', self._results_dir.name)

    def __exit__(self, type, value, traceback):
        with self._results_dir:
            r = os.system('docker rm -f test_func_xAOD')
            if r != 0:
                raise Exception(f'Unable to stop docker container: {r}')


def run_docker(info: ExecutorInfo, code_dir: str, files: List[str],
               data_file_on_cmd_line:bool = False,
               compile_only:bool = False, run_only:bool = False,
               add_position_argument_at_start:Optional[str] = None,
               extra_flag:Optional[str] = None,
               output_dir:Optional[str] = None, mount_output:bool = True) -> Union[TemporaryDirectory]:
    'Run the docker command'

    # Unravel the file path. How we do this depends on how we are doing this work.
    assert len(files) == 1
    filepath = Path(files[0])
    base_dir = filepath.parent
    filename = filepath.name

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

    if output_dir is not None:
        cmd_options += f'-o {output_dir} '
    else:
        output_dir = '/results'

    results_dir = tempfile.TemporaryDirectory()
    mount_output_options = f'-v {str(results_dir.name)}:{output_dir}' if mount_output else ''
    
    # Add an argument at the start?
    initial_args = ''
    if add_position_argument_at_start is not None:
        initial_args = f'{add_position_argument_at_start} '

    # Docker command
    docker_cmd = f'docker run --rm -v {code_dir}:/scripts:ro {mount_output_options} -v {base_dir.absolute()}:/data:ro atlas/analysisbase:latest /scripts/{info.main_script} {initial_args} {cmd_options}'
    result = os.system(docker_cmd)
    if result != 0:
        raise docker_run_error(f"nope, that didn't work {result}!")
    return results_dir


def test_good_cpp_total_run(cache_directory):
    'Good C++, and no arguments that does full run'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory, [local_path]) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_good_cpp_total_run_output_dir(cache_directory):
    'Good C++, and no arguments that does full run'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory, [local_path], output_dir='/home/atlas/results') as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_good_cpp_total_run_output_dir_no_mount(cache_directory):
    'Good C++, and no arguments that does full run'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory, [local_path], output_dir='/home/atlas/results', mount_output=False) as result_dir:
        # We aren't mounting so we can't look. So we just want to make sure no errors occur.
        pass

def test_good_cpp_total_run_file_as_arg(cache_directory):
    'Bad C++ generated, should throw an exception'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory, [local_path], data_file_on_cmd_line=True) as result_dir:
        assert os.path.exists(os.path.join(result_dir, info.output_filename))

def test_bad_cpp_total_run(cache_directory):
    'Bad C++, and no arguments that does full run'

    try:
        info = generate_test_jet_fetch_bad(cache_directory)
        with run_docker(info, cache_directory, [local_path], data_file_on_cmd_line=True) as result_dir:
            assert False
    except docker_run_error:
        pass

def test_good_cpp_just_compile(cache_directory):
    'Good C++, only do the compile'

    info = generate_test_jet_fetch(cache_directory)
    with run_docker(info, cache_directory, [local_path], compile_only=True) as result_dir:
        assert not os.path.exists(os.path.join(result_dir, info.output_filename))

def test_bad_cpp_just_compile(cache_directory):
    'Bad C++, only do the compile'

    try:
        info = generate_test_jet_fetch_bad(cache_directory)
        with run_docker(info, cache_directory, [local_path], compile_only=True) as result_dir:
            assert False
    except docker_run_error:
        pass

def test_good_cpp_compile_and_run(cache_directory):
    'Good C++, first do the compile, and then do the run'

    info = generate_test_jet_fetch(cache_directory)
    with docker_running_container(info, cache_directory, [Path(local_path)]) as runner:
        runner.compile(info)
        runner.run(info, [Path(local_path)])
        assert os.path.exists(os.path.join(runner.results_dir, info.output_filename))

def test_good_cpp_compile_and_run_2_files(cache_directory):
    'Make sure we can run a second file w/out seeing errors'
    info = generate_test_jet_fetch(cache_directory)
    with docker_running_container(info, cache_directory, [Path(local_path)]) as runner:
        runner.compile(info)
        runner.run(info, [Path(local_path)])
        out_file = os.path.join(runner.results_dir, info.output_filename)
        os.unlink(out_file)
        runner.run(info, [Path(local_path)])
        assert os.path.exists(out_file)

def test_run_with_bad_position_arg(cache_directory):
    'Pass in a bogus argument at the end with no flag'
    try:
        info = generate_test_jet_fetch(cache_directory)
        with run_docker(info, cache_directory, [local_path], add_position_argument_at_start="/results") as result_dir:
            assert False
    except docker_run_error:
        pass

def test_run_with_bad_flag(cache_directory):
    'Pass in a bogus flag'
    try:
        info = generate_test_jet_fetch(cache_directory)
        with run_docker(info, cache_directory, [local_path], extra_flag="-k") as result_dir:
            assert False
    except docker_run_error:
        pass
