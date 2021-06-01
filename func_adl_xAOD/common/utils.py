from typing import Dict, List

import func_adl_xAOD.common.cpp_types as ctyp

_type_priority: Dict[str, int] = {
    'int': 0,
    'float': 1,
    'double': 2,
}


def most_accurate_type(type_list: List[ctyp.terminal]) -> ctyp.terminal:
    '''
    Return the best type we can for most accurate sum. So if one is floating or double, return that.

    We only deal with terminals we know about.
    '''
    assert len(type_list) > 0, 'Internal error - looking for best types in null list'
    assert all(t.type in _type_priority for t in type_list), \
        f'Not all types ({", ".join(t.type for t in type_list)}) are known (known: {", ".join(_type_priority.keys())})'

    ordered = sorted(type_list, key=lambda t: _type_priority[t.type], reverse=True)
    return ordered[0]
