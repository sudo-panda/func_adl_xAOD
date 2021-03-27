import os
import ast
import shutil
import asyncio
import logging
import tempfile

from typing import Any, Callable, List, Optional, Union
from pathlib import Path

from func_adl import EventDataset
from func_adl_xAOD.common.result_ttree import cpp_ttree_rep
from func_adl_xAOD.atlas.xaod.executor import atlas_xaod_executor

# Use this to turn on dumping of output and C++
dump_running_log = True
dump_cpp = False


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


class AtlasXAODDockerException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


def dump_split_string(s: str, dump: Callable[[str], None]):
    for ll in s.split('\n'):
        dump(ll)


class LocalFile(EventDataset):
    '''
    A dataset that is represented by a local file on disk. It will be processed in
    the back end via a docker container.
    '''

    def __init__(self, local_files: Union[Path, List[Path]]):
        EventDataset.__init__(self)
        if isinstance(local_files, Path):
            self._files = [local_files]
        else:
            self._files = local_files

    async def execute_result_async(self, a: ast.AST) -> Any:
        '''
        Run the file locally with docker
        '''
        # Construct the files we will run.
        with tempfile.TemporaryDirectory() as local_run_dir_p:
            local_run_dir = Path(local_run_dir_p)
            local_run_dir.chmod(0o777)

            exe = atlas_xaod_executor()
            f_spec = exe.write_cpp_files(exe.apply_ast_transformations(a), local_run_dir)

            # Write out a file with the mapped in directories.
            # Until we better figure out how to deal with this, there are some restrictions
            # on file locations.
            datafile_dir: Optional[Path] = None
            with open(f'{local_run_dir}/filelist.txt', 'w') as flist_out:
                for u in self._files:
                    if not u.exists():
                        raise AtlasXAODDockerException(f'Cannot access (or find) file {u}')

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
            docker_cmd = f'docker run --rm -v {f_spec.output_path}:/scripts -v {f_spec.output_path}:/results {datafile_mount} atlas/analysisbase:latest /scripts/{f_spec.main_script}'
            proc = await asyncio.create_subprocess_shell(docker_cmd,
                                                         stdout=asyncio.subprocess.PIPE,  # type: ignore
                                                         stderr=asyncio.subprocess.PIPE)  # type: ignore
            p_stdout, p_stderr = await proc.communicate()
            if proc.returncode != 0 or dump_running_log:
                lg = logging.getLogger(__name__)
                level = logging.INFO if proc.returncode == 0 else logging.ERROR
                lg.log(level, f"Result of run: {proc.returncode}")
                lg.log(level, 'std Output: ')
                dump_split_string(p_stdout.decode(), lambda l: lg.log(level, f'  {l}'))
                lg.log(level, 'std Error: ')
                dump_split_string(p_stderr.decode(), lambda l: lg.log(level, f'  {l}'))
            if dump_cpp or proc.returncode != 0:
                level = logging.INFO if proc.returncode == 0 else logging.ERROR
                lg = logging.getLogger(__name__)
                with open(os.path.join(str(local_run_dir), "query.cxx"), 'r') as f:
                    lg.log(level, 'C++ Source Code:')
                    dump_split_string(f.read(), lambda l: lg.log(level, f'  {l}'))
            if proc.returncode != 0:
                raise Exception(f"Docker command failed with error {proc.returncode} ({docker_cmd})")

            # Now that we have run, we can pluck out the result.
            assert isinstance(f_spec.result_rep, cpp_ttree_rep), 'Unknown return type'
            return _extract_result_TTree(f_spec.result_rep, local_run_dir)
