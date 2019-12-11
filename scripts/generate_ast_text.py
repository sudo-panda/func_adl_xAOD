# Generate AST text for putput
import sys
from func_adl import EventDataset
from qastle import python_ast_to_text_ast
import ast


async def translate_to_ast_language(a: ast.AST) -> str:
    return python_ast_to_text_ast(a)


def as_ast_lang_query_0():
    'Extract jet pt of all jets'
    r = EventDataset("localds://did_01") \
        .SelectMany("lambda e: e.Jets('')") \
        .Select("lambda j: j.pt()") \
        .AsROOTTTree("junk.root", 'analysis', ['jet_pt']) \
        .value(executor=translate_to_ast_language)
    return r


def as_ast_lang(query_number: int) -> str:
    if query_number == 0:
        return as_ast_lang_query_0()
    else:
        raise BaseException(f"Query number {query_number} is not known")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <query-number>")
        exit(1)
    query_number = int(sys.argv[1])
    print(as_ast_lang(query_number))
