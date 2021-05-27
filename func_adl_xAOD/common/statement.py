# Statements
from abc import ABC, abstractmethod  # For declaring abstract base class
from typing import Any

import func_adl_xAOD.common.cpp_representation as crep


class BlockException (Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class block:
    'This is a block of statements surrounded by a scoping (like open close bracket, for loop, etc.)'

    def __init__(self):
        self._statements = []
        self._variables = []
        self._rep_dict = {}

    def add_statement(self, s):
        'Add statement s to the list of statements'
        self._statements += [s]

    def declare_variable(self, n):
        'Declare a variable n, which is of type cpp_variable'
        self._variables += [n]

    def emit(self, e):
        'Render the block of code'
        e.add_line("{")
        for v in self._variables:
            init_value = "" if not isinstance(v, crep.cpp_variable) or not v.initial_value() else " ({0})".format(v.initial_value().as_cpp())
            e.add_line("{0} {1}{2};".format(v.cpp_type(), v.as_cpp(), init_value))
        for s in self._statements:
            s.emit(e)
        e.add_line("}")

    def get_rep(self, name: Any) -> Any:
        '''Return the representation for some object. If we do not know its value
        then ask our parent for the value. Return None if we can't find it.

        Args:
            name:           Key for lookup

        Returns:
            None if there is nothing defined with that key in the hierarchy, or
            an actual value if there is.
        '''
        if name in self._rep_dict:
            return self._rep_dict[name]
        return None

    def set_rep(self, name: Any, value: Any):
        '''Defines the `value` for a lookup of `name` at any time in this block and
        below.

        Args:
            name:       The lookup key
            value       The value to be cached
        '''
        if name in self._rep_dict:
            raise BlockException(f'Internal Error: Representation for {str(name)} already exists. Cannot set twice')
        self._rep_dict[name] = value


class loop(block):
    'A for loop'

    def __init__(self, loop_var_rep: crep.cpp_value,
                 collection_rep: crep.cpp_collection,
                 is_loop_var_a_pntr=False, is_loop_var_a_ref=False):
        '''
        Create a new implicit for loop statement. A new var is created, and the scope is set to
        be the one down from here.
        '''
        block.__init__(self)
        self._collection = collection_rep
        self._loop_variable = loop_var_rep
        self._is_loop_var_a_pointer = is_loop_var_a_pntr
        self._is_loop_var_a_reference = is_loop_var_a_ref

    def emit(self, e):
        'Emit a for loop enclosed by a block of code'
        e.add_line("for (auto {0}{1} : {2})".format(
            '*' if self._is_loop_var_a_pointer
            else ('&' if self._is_loop_var_a_reference else ''),
            self._loop_variable.as_cpp(), self._collection.as_cpp()))
        block.emit(self, e)


class iftest(block):
    'An if statement'

    def __init__(self, if_expr):
        block.__init__(self)
        self._expr = if_expr

    def emit(self, e):
        e.add_line('if ({0})'.format(self._expr.as_cpp()))
        block.emit(self, e)


class elsephrase(block):
    'An else statement. Must come after you pop and if statement off'

    def __init__(self):
        block.__init__(self)

    def emit(self, e):
        'Emit an else statement'
        e.add_line('else')
        block.emit(self, e)


# By Inheriting from ABC we declare it as an Abstract Base Class
class book_ttree(ABC):
    'Book a TTree for writing out. Meant to be in the Book method'

    def __init__(self, tree_name, leaves):
        self._tree_name = tree_name
        self._leaves = leaves

    @abstractmethod
    def emit(self, e):
        # It is marked as an abstract method and will have to be
        # implemented before being used
        pass


class ttree_fill(ABC):
    'Fill a TTree'

    def __init__(self, tree_name):
        self._tree_name = tree_name

    @abstractmethod
    def emit(self, e):
        pass


class set_var:
    'Assing a value to a variable'

    def __init__(self, target_var, value_var):
        r'''
        target_var, value_var: representations we will use
        '''
        self._target = target_var
        self._value = value_var

    def emit(self, e):
        e.add_line('{0} = {1};'.format(self._target.as_cpp(), self._value.as_cpp()))


class push_back:
    'push a variable onto a vector'

    def __init__(self, target_collection, value_var):
        r'''
        target_col, value_var: representations we will use
        '''
        self._target = target_collection
        self._value = value_var

    def emit(self, e):
        e.add_line('{0}.push_back({1});'.format(self._target.as_cpp(), self._value.as_cpp()))


class container_clear:
    'push a variable onto a vector'

    def __init__(self, collection):
        r'''
        target_col, value_var: representations we will use
        '''
        self._collection = collection

    def emit(self, e):
        e.add_line('{0}.clear();'.format(self._collection.as_cpp()))


class arbitrary_statement:
    'An arbitrary line of C++ code. Avoid if possible, as it makes analysis impossible'

    def __init__(self, line: str):
        self._line = line

    def emit(self, e):
        ll = self._line
        if not ll.endswith(';'):
            ll += ';'
        e.add_line(ll)
