import ast
import asyncio
import logging
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, List, Union, Optional

from func_adl import EventDataset

from func_adl_xAOD.backend.xAODlib.atlas_xaod_executor import atlas_xaod_executor
import func_adl_xAOD.backend.xAODlib.result_handlers as rh


# Use this to turn on dumping of output and C++
dump_running_log = True
dump_cpp = False


# Result handlers - for each return type representation, add a handler that can process it
result_handlers = {
    rh.cpp_ttree_rep: rh.extract_result_TTree,
    rh.cpp_awkward_rep: rh.extract_awkward_result,
    rh.cpp_pandas_rep: rh.extract_pandas_result,
}


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
        with tempfile.TemporaryDirectory() as local_run_dir:
            os.chmod(local_run_dir, 0o777)

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
            if type(f_spec.result_rep) not in result_handlers:
                raise Exception(f'Do not know how to process result of type {type(f_spec.result_rep.__name__)}.')
            return result_handlers[type(f_spec.result_rep)](f_spec.result_rep, local_run_dir)
