import os
import ast
import shutil
import asyncio
import logging
import tempfile

from typing import Any, Callable, List, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod

from func_adl import EventDataset

from func_adl_xAOD.common.result_ttree import cpp_ttree_rep
from func_adl_xAOD.common.executor import executor
from func_adl_xAOD.common.ast_to_cpp_translator import query_ast_visitor
from func_adl_xAOD.common.util_scope import top_level_scope
from func_adl_xAOD.common.cpp_representation import cpp_sequence, cpp_variable

# Use this to turn on dumping of output and C++
dump_running_log = True
dump_cpp = True


def _extract_result_TTree(rep: cpp_ttree_rep, run_dir):
    '''Copy the final file into a place that is "safe", and return that as a path.

    The reason for this is that the temp directory we are using is about to be deleted!

    Args:
        rep (cpp_base_rep): The representation of the final result
        run_dir ([type]): Directory where it ran

    Raises:
        Exception: [description]
    '''
    current_path = run_dir / rep.filename
    new_path = Path('.') / rep.filename
    shutil.copy(current_path, new_path)
    return new_path


def _dump_split_string(s: str, dump: Callable[[str], None]):
    for ll in s.split('\n'):
        dump(ll)


class LocalFile(EventDataset, ABC):
    '''
    A dataset that is represented by a local file on disk. It will be processed in
    the back end via a docker container.
    '''

    def __init__(self, docker_image: str, source_file_name: str, local_files: Union[Path, List[Path]]):
        EventDataset.__init__(self)
        self._docker_image = docker_image
        self._source_file_name = source_file_name
        if isinstance(local_files, Path):
            self._files = [local_files]
        else:
            self._files = local_files
    
    @abstractmethod
    def raise_docker_exception(self, message: str):
        pass

    @abstractmethod
    def get_executor_obj(self) -> executor:
        pass

    async def execute_result_async(self, a: ast.AST) -> Any:
        '''
        Run the file locally with docker
        '''
        # Construct the files we will run.
        with tempfile.TemporaryDirectory() as local_run_dir_p:

            local_run_dir = Path(local_run_dir_p)
            local_run_dir.chmod(0o777)

            exe = self.get_executor_obj()
            f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), local_run_dir)

            # Write out a file with the mapped in directories.
            # Until we better figure out how to deal with this, there are some restrictions
            # on file locations.
            datafile_dir: Optional[Path] = None
            with open(f'{local_run_dir}/filelist.txt', 'w') as flist_out:
                for u in self._files:
                    if not u.exists():
                        self.raise_docker_exception(f'Cannot access (or find) file {u}')

                    ds_path = u.parent
                    datafile = u.name
                    flist_out.write(f'/data/{datafile}\n')
                    if datafile_dir is None:
                        datafile_dir = ds_path
                    else:
                        if ds_path != datafile_dir:
                            raise Exception(f'Data files must be from the same directory. Have seen {ds_path} and {datafile_dir} so far.')

            # Build a docker command to run this.
            datafile_mount = "" if datafile_dir is None else f'-v {datafile_dir}:/data'
            docker_cmd = f'docker run --rm -v {f_spec.output_path}:/scripts -v {f_spec.output_path}:/results {datafile_mount} {self._docker_image} /scripts/{f_spec.main_script}'
            proc = await asyncio.create_subprocess_shell(docker_cmd,
                                                         stdout=asyncio.subprocess.PIPE,  # type: ignore
                                                         stderr=asyncio.subprocess.PIPE)  # type: ignore
            p_stdout, p_stderr = await proc.communicate()
            if proc.returncode != 0 or dump_running_log:
                lg = logging.getLogger(__name__)
                level = logging.INFO if proc.returncode == 0 else logging.ERROR
                lg.log(level, f"Result of run: {proc.returncode}")
                lg.log(level, 'std Output: ')
                _dump_split_string(p_stdout.decode(), lambda l: lg.log(level, f'  {l}'))
                lg.log(level, 'std Error: ')
                _dump_split_string(p_stderr.decode(), lambda l: lg.log(level, f'  {l}'))
            if dump_cpp or proc.returncode != 0:
                level = logging.INFO if proc.returncode == 0 else logging.ERROR
                lg = logging.getLogger(__name__)
                with open(os.path.join(str(local_run_dir), self._source_file_name), 'r') as f:
                    lg.log(level, 'C++ Source Code:')
                    _dump_split_string(f.read(), lambda l: lg.log(level, f'  {l}'))
            if proc.returncode != 0:
                raise Exception(f"Docker command failed with error {proc.returncode} ({docker_cmd})")

            # Now that we have run, we can pluck out the result.
            assert isinstance(f_spec.result_rep, cpp_ttree_rep), 'Unknown return type'
            return _extract_result_TTree(f_spec.result_rep, local_run_dir)


class dummy_executor(ABC):
    'Override the docker part of the execution engine'

    def __init__(self):
        self.QueryVisitor = None
        self.ResultRep = None

    @abstractmethod
    def get_executor_obj(self) -> executor:
        pass

    @abstractmethod
    def get_visitor_obj(self) -> query_ast_visitor:
        pass

    def evaluate(self, a: ast.AST):
        rnr = self.get_executor_obj()
        self.QueryVisitor = self.get_visitor_obj()
        # TODO: #126 query_ast_visitor needs proper arguments
        a_transformed = rnr.apply_ast_transformations(a)
        self.ResultRep = \
            self.QueryVisitor.get_as_ROOT(a_transformed)

    def get_result(self, q_visitor, result_rep):
        'Got the result. Cache for use in tests'
        self.QueryVisitor = q_visitor
        self.ResultRep = result_rep
        return self


class dataset(EventDataset, ABC):
    def __init__(self, qastle_roundtrip=False):
        EventDataset.__init__(self)
        self._q_roundtrip = qastle_roundtrip

    def __repr__(self) -> str:
        # When we need to move into a representation, use
        # this as a place holder for now.
        return "'sx_placeholder'"

    @abstractmethod
    def get_dummy_executor_obj(self) -> dummy_executor:
        pass

    async def execute_result_async(self, a: ast.AST) -> Any:
        'Dummy executor that will return the ast properly rendered. If qastle_roundtrip is true, then we will round trip the ast via qastle first.'
        # Round trip qastle if requested.
        if self._q_roundtrip:
            import qastle
            print(f'before: {ast.dump(a)}')
            a_text = qastle.python_ast_to_text_ast(a)
            a = qastle.text_ast_to_python_ast(a_text).body[0].value
            print(f'after: {ast.dump(a)}')

        # Setup the rep for this dataset
        from func_adl import find_EventDataset
        file = find_EventDataset(a)
        iterator = cpp_variable("bogus-do-not-use", top_level_scope(), cpp_type=None)
        file.rep = cpp_sequence(iterator, iterator, top_level_scope())  # type: ignore

        # Use the dummy executor to process this, and return it.
        exe = self.get_dummy_executor_obj()
        exe.evaluate(a)
        return exe

