# Tests to make sure we get at the functionality in the remote executor.
import ast
import asyncio

from func_adl import EventDataset
import pandas as pd
import pytest

from func_adl_xAOD import use_exe_servicex
from servicex import ServiceXDataset

async def dummy_executor_coroutine(a: ast.AST) -> ast.AST:
    'Called to evaluate a guy - but it will take a long time'
    await asyncio.sleep(0.01)
    return a

# @pytest.fixture()
# def simple_query_ast_ROOT():
#     'Return a simple ast for a query'
#     f_ds = EventDataset(r'localds://bogus_ds')
#     return f_ds \
#         .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
#         .Select('lambda j: j.pt()/1000.0') \
#         .AsROOTTTree('output.root', 'trees', 'JetPt') \
#         .value(executor=dummy_executor_coroutine)

@pytest.fixture()
def simple_query_ast_Pandas():
    'Return a simple ast for a query'
    f_ds = EventDataset(r'localds://bogus_ds')
    return f_ds \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsPandasDF('JetPt') \
        .value(executor=dummy_executor_coroutine)

@pytest.fixture()
def simple_scoped_query_ast_Pandas():
    'Return a simple ast for a query'
    f_ds = EventDataset(r'localds://user.fork:bogus_ds')
    return f_ds \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsPandasDF('JetPt') \
        .value(executor=dummy_executor_coroutine)

@pytest.fixture()
def simple_query_ast_Awkward():
    'Return a simple ast for a query'
    f_ds = EventDataset(r'localds://bogus_ds')
    return f_ds \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsAwkwardArray('JetPt') \
        .value(executor=dummy_executor_coroutine)

def get_async_mock(mocker):
    import sys
    if sys.version_info[1] <= 7:
        import asyncmock
        return asyncmock.MagicMock
    else:
        return mocker.MagicMock

@pytest.fixture()
def simple_Servicex_fe_watcher(mocker):
    'Mock out the servicex guy'
    m_servicex = get_async_mock(mocker)(spec=ServiceXDataset)
    m_servicex.get_data_pandas_df_async.return_value = pd.DataFrame()
    p_servicex = mocker.patch('servicex.ServiceXDataset', return_value=m_servicex)
    return m_servicex, p_servicex
    

@pytest.mark.asyncio
async def test_pandas_query(simple_query_ast_Pandas, simple_Servicex_fe_watcher):
    'Simple pandas based query'
    r = await(use_exe_servicex(simple_query_ast_Pandas))
    assert r is not None
    assert isinstance(r, pd.DataFrame)
    assert len(r) == 0

    caller = simple_Servicex_fe_watcher[0].get_data_pandas_df_async
    caller.assert_called_once()
    args = caller.call_args[0]
    kwargs = caller.call_args[1]
    assert len(args) == 1
    assert args[0].find('SelectMany') >= 0
    assert args[0].startswith('(call ResultTTree')


@pytest.mark.asyncio
async def test_awkward_query(simple_query_ast_Awkward, simple_Servicex_fe_watcher):
    'Simple pandas based query'
    await(use_exe_servicex(simple_query_ast_Awkward))

    caller = simple_Servicex_fe_watcher[0].get_data_awkward_async
    caller.assert_called_once()
    args = caller.call_args[0]
    assert len(args) == 1
    assert args[0].find('SelectMany') >= 0
    assert args[0].startswith('(call ResultTTree')


@pytest.mark.asyncio
async def test_scoped_dataset_name(simple_scoped_query_ast_Pandas, simple_Servicex_fe_watcher):
    'Simple pandas based query'
    r = await(use_exe_servicex(simple_scoped_query_ast_Pandas))

    simple_Servicex_fe_watcher[1].assert_called_once()
    assert simple_Servicex_fe_watcher[1].call_args[0][0] == 'user.fork:bogus_ds'
