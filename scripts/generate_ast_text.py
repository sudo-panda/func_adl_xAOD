# Generate AST text for putput
import ast
import sys

from qastle import python_ast_to_text_ast
from typing import Any

from func_adl import EventDataset


class ast_translator_ds(EventDataset):
    def __init__(self):
        EventDataset.__init__(self)

    async def execute_result_async(self, a: ast.AST) -> Any:
        return python_ast_to_text_ast(a)


def as_ast_lang_query_0():
    'Extract jet pt of all jets'
    r = ast_translator_ds() \
        .SelectMany("lambda e: e.Jets('')") \
        .Select("lambda j: j.pt()") \
        .AsROOTTTree("junk.root", 'analysis', ['jet_pt']) \
        .value()
    return r


def as_ast_lang_query_1():
    'Generate a real query that works on our 10 event root file'
    r = ast_translator_ds() \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda j: j.pt()/1000.0') \
        .AsROOTTTree("junk.root", "analysis", ['JetPt']) \
        .value()
    return r


def as_ast_lang_query_2():
    'Marc needed this to run some performance tests.'
    r = ast_translator_ds() \
        .Select('lambda e: (e.Electrons("Electrons"), e.Muons("Muons"))') \
        .Select('lambda e: (e[0].Select(lambda ele: ele.e()), e[0].Select(lambda ele: ele.pt()), e[0].Select(lambda ele: ele.phi()), e[0].Select(lambda ele: ele.eta()), e[1].Select(lambda mu: mu.e()), e[1].Select(lambda mu: mu.pt()), e[1].Select(lambda mu: mu.phi()), e[1].Select(lambda mu: mu.eta()))') \
        .AsROOTTTree('dude.root', 'forkme', ['e_E', 'e_pt', 'e_phi', 'e_eta', 'mu_E', 'mu_pt', 'mu_phi', 'mu_eta']) \
        .value()
    return r


def as_ast_lang(query_number: int) -> str:
    if query_number == 0:
        return as_ast_lang_query_0()
    elif query_number == 1:
        return as_ast_lang_query_1()
    elif query_number == 2:
        return as_ast_lang_query_2()
    else:
        raise Exception(f"Query number {query_number} is not known")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <query-number>")
        exit(1)
    query_number = int(sys.argv[1])
    print(as_ast_lang(query_number))
