# Code to translate from a reduced AST into C++ code. This is done by traversing the
# Python AST code.

import ast
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Union, cast

import func_adl_xAOD.common.cpp_ast as cpp_ast
import func_adl_xAOD.common.cpp_representation as crep
import func_adl_xAOD.common.cpp_types as ctyp
import func_adl_xAOD.common.math_utils  # NOQA
import func_adl_xAOD.common.result_ttree as rh
import func_adl_xAOD.common.statement as statement
from func_adl.ast.call_stack import argument_stack, stack_frame
from func_adl.ast.func_adl_ast_utils import FuncADLNodeVisitor, function_call
from func_adl.util_ast import lambda_unwrap
from func_adl_xAOD.common.cpp_functions import FunctionAST
from func_adl_xAOD.common.cpp_vars import unique_name
from func_adl_xAOD.common.generated_code import generated_code
from func_adl_xAOD.common.util_scope import (deepest_scope, gc_scope,
                                             gc_scope_top_level,
                                             top_level_scope)
from func_adl_xAOD.common.utils import most_accurate_type

# Convert between Python comparisons and C++.
compare_operations = {
    ast.Lt: '<',
    ast.LtE: '<=',
    ast.Gt: '>',
    ast.GtE: '>=',
    ast.Eq: '==',
    ast.NotEq: '!=',
}


# Unary operators - we aren't doing not and invert just yet.
_known_unary_operators: Dict[Type, str] = {
    ast.UAdd: '+',
    ast.USub: '-',
    ast.Not: '!',
}


# Known binary operators
_known_binary_operators: Dict[Type, str] = {
    ast.Add: '+',
    ast.Sub: '-',
    ast.Mult: '*',
    ast.Div: '/',
    ast.Mod: '%',
}


class xAODTranslationError(Exception):
    'Thrown when a translation error happens of one sort or another.'

    def __init__(self, msg):
        Exception.__init__(self, msg)


def check_accumulator_type(t: ctyp.terminal):
    'We can only deal with certain types for doing an accumulation. Make sure this is one.'
    t_str = str(t)
    return (t_str == "float") or (t_str == "double") or (t_str == "int")


def guess_type_from_number(n):
    if int(n) == n:
        return ctyp.terminal("int")
    return ctyp.terminal("double")


def rep_is_collection(rep) -> bool:
    if isinstance(rep, crep.cpp_sequence):
        return True
    if isinstance(rep, crep.cpp_collection):
        return True
    return False


def get_ttree_type(rep):
    'Looking at a rep, figure out how it should get stored in a tree'
    if isinstance(rep, crep.cpp_sequence):
        if not isinstance(rep.sequence_value(), (crep.cpp_value, crep.cpp_sequence)):
            raise Exception("Nested data structures (2D arrays, etc.) in TTree's are not yet supported. Numbers or arrays of numbers only for now.")
        return ctyp.collection(rep.sequence_value().cpp_type())
    else:
        return rep.cpp_type()


def determine_type_mf(parent_type, function_name):
    '''
    Determine the return type of the member function. Do our best to make
    an intelligent case when we can.

    parent_type:        the type of the parent
    function_name:      the name of the function we are calling
    '''
    # If we don't know the type...
    if parent_type is None:
        raise RuntimeError("Internal Error: Trying to call member function for a type we do not know!")
    # If we are doing one of the normal "terminals", then we can just bomb. This should not happen!

    rtn_type = ctyp.method_type_info(str(parent_type), function_name)
    if rtn_type is not None:
        return rtn_type

    # We didn't know it. Lets make a guess, and error out if we are clearly making a mistake.
    base_types = ['double', 'float', 'int']
    s_parent_type = str(parent_type)
    if s_parent_type in base_types:
        raise xAODTranslationError(f'Unable to call method {function_name} on type {str(parent_type)}.')

    # Ok - we give up. Return a double.
    logging.getLogger(__name__).warning(f"Warning: assumping that the method '{str(s_parent_type)}.{function_name}(...)' has return type 'double'. Use cpp_types.add_method_type_info to suppress (or correct) this warning.")
    return ctyp.terminal('double')


def _extract_column_names(names_ast: ast.AST) -> List[str]:
    'Extract a list of strings from an ast using literal evaluation. A single name is returned as a list.'
    names = ast.literal_eval(names_ast)
    if isinstance(names, str):
        return [names]
    return names


class query_ast_visitor(FuncADLNodeVisitor, ABC):
    r"""
    Drive the conversion to C++ from the top level query
    """

    def __init__(self, prefix, is_loop_var_a_ref):
        r'''
        Initialize the visitor.
        '''
        # Tracks the output of the code.
        self._gc = generated_code()
        self._arg_stack = argument_stack()
        self._result = None
        self._prefix = prefix
        self._is_loop_var_a_ref = is_loop_var_a_ref

    def include_files(self):
        return self._gc.include_files()

    def emit_query(self, e):
        'Emit the parsed lines'
        self._gc.emit_query_code(e)

    def emit_book(self, e):
        'Emit the parsed lines'
        self._gc.emit_book_code(e)

    def class_declaration_code(self):
        return self._gc.class_declaration_code()

    def visit(self, node):
        '''Visit a node. If the node already has a rep, then it has been visited and we
        do not need to visit it again.

        node - if the node has a rep, just return

        '''
        if not hasattr(node, 'rep'):
            FuncADLNodeVisitor.visit(self, node)

        # Lots of nodes never get a representation - like `ast.Name`, so we
        # need to protect the access here.
        if hasattr(node, 'rep'):
            self._result = node.rep

    def get_rep(self, node: ast.AST, retain_scope: bool = False) -> Union[crep.cpp_value, crep.cpp_sequence]:
        r'''Return the rep for the node. If it isn't set yet, then run our visit on it.

        node - The ast node to generate a representation for.
        retain_scope - If true, then the scope level will remain the same before and after the call.

        RULES for .rep: NEVER access it without using get_rep. It is fine, of course, if you are setting it as a result
        of visiting. BUT ALWAYS GO THROUGH get_rep to get the rep for a node you aren't handling directly. If you ever find yourself
        writing a "hasattr(node, 'rep')" you will almost certainly be introducing a bug. Use get_rep instead!!
        '''
        # If the rep is present, make sure it is still valid by checking the scope.
        result = None
        if hasattr(node, 'rep'):
            result = node.rep  # type: ignore
            if not self._gc.current_scope().starts_with(result.scope()):
                result = None

        # If this node already has a representation, then it has been
        # processed and we do not need to do it again.
        if result is None:
            s = self._gc.current_scope() if retain_scope else None
            self.visit(node)
            if s is not None:
                self._gc.set_scope(s)

        # If it still didn't work, this is an internal error. But make the error message a bit nicer.
        if not hasattr(node, 'rep'):
            raise Exception('Internal Error: attempted to get C++ representation for AST node "{0}", but failed.'.format(ast.dump(node)))
        self._result = node.rep  # type: ignore

        return node.rep  # type: ignore

    @abstractmethod
    def create_ttree_fill_obj(self, tree_name: str) -> statement.ttree_fill:
        pass

    @abstractmethod
    def create_book_ttree_obj(self, tree_name: str, leaves: list) -> statement.book_ttree:
        pass

    def get_as_ROOT(self, node: ast.AST) -> rh.cpp_ttree_rep:
        '''For a given node, return a root ttree rep.

        This is used to make sure whatever the sequence is, that it returns a RootTTree. Use this
        when the user may not have explicitly requested an output format. For example, if they end
        with a tuple or a dict request, but not a AsAwkwardArray or similar.

        1. If the top level ast node already requests an ROOTTTree, the representation is returned.
        1. If the node is a sequence of `cpp_values`, then a single column tree is created.
        1. If the node is a sequence of dict's, a ttree is created that uses the dictionary
           key's as column names.
        1. Anything else causes an exception to be raised.

        Args:
            node (ast.AST): Top level `func_adl` expression that is to be renered as a ROOT file.

        Returns:
            rh.cpp_ttree_rep: The resulting node that will generate a root file.

        Exceptions:
            ValueError: If we end with something other than above, we raise `ValueError` to
                        indicate that we can't figure out how to convert something into a ROOT
                        file.
        '''
        r = self.get_rep(node)
        if isinstance(r, rh.cpp_ttree_rep):
            return r

        # If this isn't a sequence, then we are totally blown here.
        if not isinstance(r, crep.cpp_sequence):
            raise ValueError(f'Do not know how to convert {r} into a ROOT file')

        # If this is a dict, then pull out each item and re-assemble into a tuple
        # which we can feed to the root guy.
        values = r.sequence_value()
        if isinstance(values, crep.cpp_dict):
            values = cast(crep.cpp_dict, values)
            col_values = values.value_dict.values()
            col_names = ast.List(elts=list(values.value_dict.keys()))
            s_tuple = crep.cpp_tuple(tuple(col_values), values.scope())
            tuple_sequence = crep.cpp_sequence(s_tuple, r.iterator_value(), r.scope())  # type: ignore
            ast_dummy_source = ast.Constant(value=1)
            ast_dummy_source.rep = tuple_sequence  # type: ignore
            ast_ttree = function_call('ResultTTree',
                                      [ast_dummy_source,
                                       col_names,
                                       ast.parse(f'"{self._prefix}_tree"').body[0].value,  # type: ignore
                                       ast.parse(f'"{self._prefix}_output"').body[0].value])  # type: ignore
            result = self.get_rep(ast_ttree)
            assert isinstance(result, rh.cpp_ttree_rep)
            return result

        if isinstance(values, crep.cpp_tuple):
            col_names = ast.List(elts=[ast.parse(f"'col{i}'").body[0].value for i, _ in enumerate(values.values())])  # type: ignore
            ast_ttree = function_call('ResultTTree',
                                      [node,
                                       col_names,
                                       ast.parse(f'"{self._prefix}_tree"').body[0].value,  # type: ignore
                                       ast.parse(f'"{self._prefix}_output"').body[0].value])  # type: ignore
            result = self.get_rep(ast_ttree)
            assert isinstance(result, rh.cpp_ttree_rep)
            return result
        elif isinstance(values, crep.cpp_value) or isinstance(values, crep.cpp_sequence):
            ast_ttree = function_call('ResultTTree',
                                      [node,
                                       ast.parse('"col1"').body[0].value,  # type: ignore
                                       ast.parse(f'"{self._prefix}_tree"').body[0].value,  # type: ignore
                                       ast.parse(f'"{self._prefix}_output"').body[0].value])  # type: ignore
            result = self.get_rep(ast_ttree)
            assert isinstance(result, rh.cpp_ttree_rep)
            return result
        else:
            raise ValueError(f'Do not know how to convert a sequence of {r.sequence_value()} into a ROOT file.')

        raise NotImplementedError()

    def get_rep_value(self, node, retain_scope=False) -> crep.cpp_value:
        r'''Return the rep for the node. If it isn't set yet, then run our visit on it. Assure we are returning a value

        node - The ast node to generate a representation for.
        retain_scope - If true, then the scope level will remain the same before and after the call.
        '''
        v = self.get_rep(node, retain_scope)
        if not isinstance(v, crep.cpp_value):
            raise Exception("Expected a cpp value! Internal error")
        return v

    def resolve_id(self, id):
        'Look up the in our local dict. This takes care of function arguments, etc.'
        return self._arg_stack.lookup_name(id)

    def make_sequence_from_collection(self, rep):
        '''
        Take a collection and produce a sequence. Eventually this should likely be some sort of
        plug-in architecture. But for now, we will just assume everything looks like a vector. When
        it comes time for a new type, this is where it should go.
        '''
        element_type = rep.cpp_type().element_type()
        element_type = element_type.get_dereferenced_type() if self._is_loop_var_a_ref else element_type
        iterator_value = crep.cpp_value(unique_name("i_obj"), None, element_type)  # type: ignore
        l_statement = statement.loop(iterator_value, crep.dereference_var(rep), is_loop_var_a_ref=self._is_loop_var_a_ref)  # type: ignore
        self._gc.add_statement(l_statement)
        iterator_value.reset_scope(self._gc.current_scope())

        # For a new sequence like this the sequence and iterator value are the same
        return crep.cpp_sequence(iterator_value, iterator_value, self._gc.current_scope())

    def as_sequence(self, generation_ast: ast.AST):
        r'''
        We will convert the generation_ast into a sequence if we can. If we can't, that indicates
        a likely programming error by this library or by the user.

        generation_ast - The AST that will generate the collection (a call to something that
                         returns a collection or a Select statement, etc.)

        returns:

        sequence:       An object of type crep.cpp_sequence that contains all the information
                        about the sequence.
        '''
        # Get the representation for the ast
        rep = self.get_rep(generation_ast)

        # If this is already a sequence then we are done!
        if isinstance(rep, crep.cpp_sequence):
            return rep

        # Next do a lookup to see if we have already defined a sequence at this level
        r = self._gc.get_rep(rep)
        if r is not None:
            return r

        # If this is a collection, then we need to turn it into a sequence.
        if isinstance(rep, crep.cpp_collection):
            r = self.make_sequence_from_collection(rep)
            self._gc.set_rep(rep, r)
            return r

        # If it isn't a sequence or a collection, then something has gone wrong.
        raise Exception(f"Unable to generate a sequence from the given AST. Either there is an internal error, or you are trying to manipulate a '{type(rep).__name__}' as a sequence (ast is: {ast.dump(generation_ast)})")

    def visit_Call_Lambda(self, call_node):
        'Call to a lambda function. We propagate the arguments through the function'

        with stack_frame(self._arg_stack):
            for c_arg, l_arg in zip(call_node.args, call_node.func.args.args):
                self._arg_stack.define_name(l_arg.arg, c_arg)

            # Next, process the lambda's body.
            call_node.rep = self.get_rep(call_node.func.body)

    def _create_accumulator(self, seq: crep.cpp_sequence, acc_type: ctyp.terminal, initial_value=None):
        'Helper to create an accumulator for the Aggregate function'
        accumulator_type = acc_type

        # When we implement other types of aggregate, this code will need to
        # be back in.
        # if accumulator_type is None:
        #     sv = seq.sequence_value()
        #     if not isinstance(sv, crep.cpp_value):
        #         raise Exception("Do not know how to accumulate a sequence!")
        #     accumulator_type = sv.cpp_type()
        if not check_accumulator_type(accumulator_type):
            raise ValueError(f"Aggregate over a sequence of type '{str(accumulator_type)}' is not supported.")

        # Getting the scope level right is tricky. If this is a straight sequence of items, then we want the sequence level.
        # But if this is a sequence of sequences, we are aggregating over the sequence itself. So we need to do it one level
        # up from where the iterator is running on the interior sequence.
        seq_val = seq.sequence_value()
        if isinstance(seq_val, crep.cpp_sequence):
            accumulator_scope = seq_val.iterator_value().scope()[-1]
        else:
            accumulator_scope = seq.iterator_value().scope()[-1]
        accumulator = crep.cpp_variable(unique_name("aggResult"),
                                        accumulator_scope,
                                        accumulator_type,
                                        initial_value=initial_value if initial_value is not None else crep.cpp_value(accumulator_type.default_value(), self._gc.current_scope(), accumulator_type))
        accumulator_scope.declare_variable(accumulator)

        return accumulator, accumulator_scope

    def visit_Call_Aggregate_only(self, node: ast.Call, args: List[ast.AST]):
        '''
        - (acc lambda): the accumulator is set to the first element, and the lambda is called to
                        update it after that. This is called `agg_only`.
        '''
        raise NotImplementedError()
        # This is commented out b.c. we've not written detailed testing nor found a real
        # use yet in code - though it may very well happen! So we'll leave our first guess in here.
        # agg_lambda = node.args[0]

        # # Get the sequence we are calling against and the accumulator
        # if not isinstance(node.func, ast.Attribute):
        #     raise Exception("Wrong type of function")
        # seq = self.as_sequence(node.func.value)
        # accumulator, accumulator_scope = self._create_accumulator(seq)

        # # We have to do a simple if statement here so that the first time through we can set the
        # # accumulator, and the second time we can add to it.

        # is_first_iter = crep.cpp_variable(unique_name("is_first"), self._gc.current_scope(), cpp_type=ctyp.terminal('bool'), initial_value=crep.cpp_value('true', self._gc.current_scope(), ctyp.terminal('bool')))
        # accumulator_scope.declare_variable(is_first_iter)

        # # Set the scope where we will be doing the accumulation
        # sv = seq.sequence_value()
        # if isinstance(sv, crep.cpp_sequence):
        #     self._gc.set_scope(sv.iterator_value().scope()[-1])
        # else:
        #     self._gc.set_scope(sv.scope())

        # # Code up if statement to select out the first element.
        # if_first = statement.iftest(is_first_iter)
        # self._gc.add_statement(if_first)
        # self._gc.add_statement(statement.set_var(is_first_iter, crep.cpp_value("false", self._gc.current_scope(), ctyp.terminal('bool'))))

        # # Set the accumulator
        # self._gc.add_statement(statement.set_var(accumulator, seq.sequence_value()))
        # self._gc.pop_scope()

        # # Now do the if statement and make the call to calculate the accumulation.
        # self._gc.add_statement(statement.elsephrase())
        # call = ast.Call(func=agg_lambda, args=[accumulator.as_ast(), seq.sequence_value().as_ast()])
        # self._gc.add_statement(statement.set_var(accumulator, self.get_rep(call)))

        # # Finally, since this is a terminal, we need to pop off the top.
        # self._gc.set_scope(accumulator_scope)

        # # Cache the results in our result in case we are skipping nodes in the AST.
        # node.rep = accumulator
        # self._result = accumulator

    def visit_call_Aggregate_initial(self, node: ast.Call, args: List[ast.AST]):
        '''
        - (const, acc lambda): the accumulator is set to the value, and then the lambda is called to
                        update it on every single element. This is called `agg_initial`
        '''
        raw_seq = node.args[0]
        init_val = self.get_rep(node.args[1])
        agg_lambda = node.args[2]
        assert isinstance(agg_lambda, ast.Lambda)

        # Get the sequence we are calling against and the accumulator
        seq = self.as_sequence(raw_seq)
        accumulator, accumulator_scope = self._create_accumulator(seq, initial_value=init_val, acc_type=init_val.cpp_type())

        # Now do the accumulation. This happens at the current iterator scope.
        sv = seq.sequence_value()
        if isinstance(sv, crep.cpp_sequence):
            self._gc.set_scope(sv.iterator_value().scope()[-1])
        else:
            self._gc.set_scope(sv.scope())
        call = ast.Call(func=agg_lambda, args=[accumulator.as_ast(), seq.sequence_value().as_ast()])
        update_lambda = self.get_rep(call)

        # Check the accumulator value still hols out. Since we need the accumulator previously,
        # this will allow us to patch things up. This isn't perfect, but it will do.
        if update_lambda.cpp_type().type != init_val.cpp_type().type:
            best_type = most_accurate_type([init_val.cpp_type(), update_lambda.cpp_type()])
            accumulator.update_type(best_type)

        self._gc.add_statement(statement.set_var(accumulator, update_lambda))

        # Finally, since this is a terminal, we need to pop off the top.
        self._gc.set_scope(accumulator_scope)

        # Cache the results in our result in case we are skipping nodes in the AST.
        node.rep = accumulator  # type: ignore
        self._result = accumulator

    def visit_call_Aggregate_initial_func(self, node: ast.Call, args: List[ast.AST]):
        '''
        - (start lambda, acc lambda): the accumulator is set to the start lambda call on the first
                        element in the sequence, and then acc is called to update it after that.
                        This is called `agg_initial_func`
        '''
        raise NotImplementedError()
        # Needs testing!
        # agg_lambda = node.args[1]
        # init_lambda = node.args[0]

        # # Get the sequence we are calling against and the accumulator
        # seq = self.as_sequence(node.func.value)
        # accumulator, accumulator_scope = self._create_accumulator(seq, initial_value=init_val)

        # is_first_iter = crep.cpp_value(unique_name("is_first"), accumulator_scope, cpp_type=ctyp.terminal("bool"), initial_value='true')
        # accumulator_scope.declare_variable(is_first_iter)

        # # BELOW HERE NOT CONVERTED YET.

        # # We have to initialized the variable to some value, and it depends on how the user
        # # is trying to initialize things - first iteration or with a value. We've done the value case above.
        # is_first_iter = None
        # if use_first_element_separately:
        #     is_first_iter = cpp_variable(unique_name("is_first"), self._gc.current_scope(), cpp_type="bool", initial_value='true')
        #     decl_block.declare_variable(is_first_iter)

        # # Now we need to emit code at the accumulator level.
        # self._gc.set_scope(c_loop.scope())

        # # If we have to use the first lambda to set the first value, then we need that code up front.
        # if use_first_element_separately:
        #     if_first = statement.iftest(cpp_constant(is_first_iter.as_cpp()))
        #     self._gc.add_statement(if_first)
        #     self._gc.add_statement(statement.set_var(is_first_iter, cpp_constant("false")))
        #     first_scope = self._gc.current_scope()

        #     if init_lambda is not None:
        #         call = ast.Call(init_lambda, [c_iter.as_ast()])
        #         self._gc.add_statement(statement.set_var(result, self.get_rep(call)))
        #     else:
        #         self._gc.add_statement(statement.set_var(result, c_iter))

        #     self._gc.set_scope(first_scope)
        #     self._gc.pop_scope()
        #     self._gc.add_statement(statement.elsephrase())

        # # Perform the aggregation function. We need to call it with the value and the accumulator.
        # call = ast.Call(func=agg_lambda, args=[result.as_ast(), c_iter.as_ast()])
        # self._gc.add_statement(statement.set_var(result, self.get_rep(call)))

        # # Finally, since this is a terminal, we need to pop off the top.
        # self._gc.set_scope(decl_block_scope)

        # # Cache the results in our result incase we are skipping nodes in the AST.
        # node.rep = result
        # self._result = result

    def call_Aggregate(self, node: ast.Call, args: List[ast.AST]):
        r'''Implement the aggregate algorithm in C++

        Our source we loop over, and we count out everything. The final result is whatever it is
        we are counting.

        Possible arguments to the call:

        - (acc lambda): the accumulator is set to the first element, and the lambda is called to
                        update it after that. This is called `agg_only`.
        - (const, acc lambda): the accumulator is set to the value, and then the lambda is called to
                        update it on every single element. This is called `agg_initial`
        - (start lambda, acc lambda): the accumulator is set to the start lambda call on the first
                        element in the sequence, and then acc is called to update it after that.
                        This is called `agg_initial_func`

        Limitations: only floats for now!
        '''
        # figure out which version of Aggregate we have here.
        if len(node.args) == 2:
            return self.visit_Call_Aggregate_only(node, args)
        elif len(node.args) == 3:
            if isinstance(node.args[0], ast.Lambda):
                return self.visit_call_Aggregate_initial_func(node, args)
            else:
                return self.visit_call_Aggregate_initial(node, args)

        # This isn't good!
        raise Exception("Unknown call to Aggregate. Must be Aggregate(func), Aggregate(const, func), or Aggregate(func, func)")

    def visit_Call_Member(self, call_node):
        'Method call on an object'

        # Visit everything down a level.
        self.generic_visit(call_node)

        # figure out what we are calling against, and the
        # method name we are going to be calling against.
        calling_against = self.get_rep(call_node.func.value)
        function_name = call_node.func.attr
        if not isinstance(calling_against, crep.cpp_value):
            # We didn't use get_rep_value above because now we can make a better error message.
            raise Exception("Do not know how to call '{0}' on '{1}'".format(function_name, type(calling_against).__name__))

        # We support member calls that directly translate only. Here, for example, this is only for
        # obj.pt() or similar. The translation is direct.
        c_stub = calling_against.as_cpp() + ("->" if calling_against.is_pointer() else ".")
        result_type = determine_type_mf(calling_against.cpp_type(), function_name)

        args = call_node.args
        self._result = crep.cpp_value(c_stub + function_name + f"({','.join(self.get_rep(arg).as_cpp() for arg in args)})", calling_against.scope(), result_type)

    def visit_function_ast(self, call_node):
        'Drop-in replacement for a function'
        # Get the arguments
        cpp_func = call_node.func
        arg_reps = [self.get_rep_value(a) for a in call_node.args]

        # Code up a call
        r = crep.cpp_value('{0}({1})'.format(cpp_func.cpp_name, ','.join(a.as_cpp() for a in arg_reps)), self._gc.current_scope(), cpp_type=cpp_func.cpp_return_type)

        # Include files and return the resulting expression
        for i in cpp_func.include_files:
            self._gc.add_include(i)
        call_node.rep = r
        return r

    def call_EventDataset(self, node: ast.Call, args: List[ast.AST]):
        'This has already been resolved, so return it.'
        assert hasattr(node, 'rep')
        self._result = node.rep  # type: ignore
        return node.rep  # type: ignore

    def visit_Call(self, call_node: ast.Call):
        r'''
        Very limited call forwarding.
        '''
        # What kind of a call is this?
        if isinstance(call_node.func, ast.Lambda):
            self.visit_Call_Lambda(call_node)
        elif isinstance(call_node.func, ast.Attribute):
            self.visit_Call_Member(call_node)
        elif isinstance(call_node.func, cpp_ast.CPPCodeValue):
            self._result = cpp_ast.process_ast_node(self, self._gc, call_node)
        elif isinstance(call_node.func, FunctionAST):
            self._result = self.visit_function_ast(call_node)
        else:
            # Perhaps a method call we can normalize?
            r = FuncADLNodeVisitor.visit_Call(self, call_node)
            if r is None and not hasattr(call_node, 'rep'):
                raise Exception("Do not know how to call '{0}'".format(ast.dump(call_node.func, annotate_fields=False)))
            if r is not None:
                self._result = r
        call_node.rep = self._result  # type: ignore

    def visit_Name(self, name_node: ast.Name):
        'Visiting a name - which should represent something'
        id = self.resolve_id(name_node.id)
        if isinstance(id, ast.AST):
            name_node.rep = self.get_rep(id)  # type: ignore

    def visit_Subscript(self, node):
        'Index into an array. Check types, as tuple indexing can be very bad for us'
        v = self.get_rep(node.value)
        if not isinstance(v, crep.cpp_collection):
            raise Exception("Do not know how to take the index of type '{0}'".format(v.cpp_type()))

        index = self.get_rep(node.slice)
        node.rep = crep.cpp_value("{0}.at({1})".format(v.as_cpp(), index.as_cpp()), self._gc.current_scope(), cpp_type=v.get_element_type())  # type: ignore
        self._result = node.rep

    def visit_Index(self, node):
        'We can only do single items, we cannot do slices yet'
        v = self.get_rep(node.value)
        node.rep = v
        self._result = node

    def visit_Tuple(self, tuple_node):
        r'''
        Process a tuple. We visit each component of it, and build up a representation from each result.

        See github bug #21 for the special case of dealing with (x1, x2, x3)[0].
        '''
        tuple_node.rep = crep.cpp_tuple(tuple(self.get_rep(e, retain_scope=True) for e in tuple_node.elts), self._gc.current_scope())
        self._result = tuple_node.rep

    def visit_Dict(self, node: ast.Dict):
        '''Process a dictionary. We create a C++ representation of this. The
        dict, as things currently stand, will not make its way into C++, but it might
        help us sort out some sort of output or similar.

        Args:
            node (ast.Dict): The dictionary node for us to process
        '''
        if not all(v is not None for v in node.keys):
            raise ValueError('The python construction of adding a dictionary into another dictionary is not supported ({1: 10, **old_dict})')

        values = {k: self.get_rep(v, retain_scope=True) for k, v in zip(node.keys, node.values)}
        node.rep = crep.cpp_dict(values, self._gc.current_scope())  # type: ignore
        self._result = node.rep  # type: ignore

    def visit_List(self, list_node):
        r'''
        Process a list. We visit each component of it, and build up a representation from each result.

        See github bug #21 for the special case of dealing with (x1, x2, x3)[0].
        '''
        list_node.rep = crep.cpp_tuple(tuple(self.get_rep(e, retain_scope=True) for e in list_node.elts), self._gc.current_scope())
        self._result = list_node.rep

    def visit_BinOp(self, node):
        'An in-line add'
        if type(node.op) not in _known_binary_operators:
            raise Exception(f"Do not know how to translate Binary operator {ast.dump(node.op)}!")
        left = self.get_rep(node.left)
        right = self.get_rep(node.right)

        best_type = most_accurate_type([left.cpp_type(), right.cpp_type()])
        if type(node.op) is ast.Div:
            best_type = ctyp.terminal('double', False)

        s = deepest_scope(left, right).scope()
        r = crep.cpp_value(f"({left.as_cpp()}{_known_binary_operators[type(node.op)]}{right.as_cpp()})",
                           s, best_type)

        # Cache the result to push it back further up.
        node.rep = r
        self._result = r

    def visit_UnaryOp(self, node: ast.UnaryOp):
        if type(node.op) not in _known_unary_operators:
            raise Exception(f"Do not know how to translate Unary operator {ast.dump(node.op)}!")

        operand = self.get_rep(node.operand)

        s = operand.scope()
        r = crep.cpp_value(f"({_known_unary_operators[type(node.op)]}({operand.as_cpp()}))",
                           s, operand.cpp_type())
        node.rep = r  # type: ignore
        self._result = r

    def visit_IfExp(self, node):
        r'''
        We'd like to be able to use the "?" operator in C++, but the
        problem is lazy evaluation. It could be when we look at one or the
        other item, a bunch of prep work has to be done - and that will
        show up in separate statements. So we have to use if/then/else with
        a result value.
        '''

        # The result we'll store everything in.
        result = crep.cpp_variable(unique_name("if_else_result"), self._gc.current_scope(), cpp_type=ctyp.terminal("double"))
        self._gc.declare_variable(result)

        # We always have to evaluate the test.
        current_scope = self._gc.current_scope()
        test_expr = self.get_rep(node.test)
        self._gc.add_statement(statement.iftest(test_expr))
        if_scope = self._gc.current_scope()

        # Next, we do the true and false if statement.
        self._gc.add_statement(statement.set_var(result, self.get_rep(node.body)))
        self._gc.set_scope(if_scope)
        self._gc.pop_scope()
        self._gc.add_statement(statement.elsephrase())
        self._gc.add_statement(statement.set_var(result, self.get_rep(node.orelse)))
        self._gc.set_scope(current_scope)

        # Done, the result is the rep of this node!
        node.rep = result
        self._result = result

    def visit_Compare(self, node):
        'A compare between two things. Python supports more than that, but not implemented yet.'
        if len(node.ops) != 1:
            raise Exception("Do not support 1 < a < 10 comparisons yet!")

        left = self.get_rep(node.left)
        right = self.get_rep(node.comparators[0])

        r = crep.cpp_value('({0}{1}{2})'.format(left.as_cpp(), compare_operations[type(node.ops[0])], right.as_cpp()), self._gc.current_scope(), ctyp.terminal("bool"))
        node.rep = r
        self._result = r

    def visit_BoolOp(self, node):
        '''A bool op like And or Or on a set of values
        This is a bit more complex than just "anding" things as we want to make sure to short-circuit the
        evaluation if we need to.
        '''

        # The result of this test
        result = crep.cpp_variable(unique_name('bool_op'), self._gc.current_scope(), cpp_type='bool')
        self._gc.declare_variable(result)

        # How we check and short-circuit depends on if we are doing and or or.
        check_expr = result.as_cpp() if type(node.op) == ast.And else '!{0}'.format(result.as_cpp())
        check = crep.cpp_value(check_expr, self._gc.current_scope(), cpp_type=ctyp.terminal('bool'))

        first = True
        scope = self._gc.current_scope()
        for v in node.values:
            if not first:
                self._gc.add_statement(statement.iftest(check))

            rep_v = self.get_rep(v)
            self._gc.add_statement(statement.set_var(result, rep_v))

            if not first:
                self._gc.set_scope(scope)
            first = False

        # Cache result variable so those above us have something to use.
        self._result = result
        node.rep = result

    def visit_Num(self, node):
        node.rep = crep.cpp_value(node.n, self._gc.current_scope(), guess_type_from_number(node.n))
        self._result = node.rep

    def visit_Str(self, node):
        node.rep = crep.cpp_value('"{0}"'.format(node.s), self._gc.current_scope(), ctyp.terminal("string"))
        self._result = node.rep

    def code_fill_ttree(self, e_rep: crep.cpp_rep_base, e_name: crep.cpp_variable,
                        scope_fill: Union[gc_scope, gc_scope_top_level]) -> Union[gc_scope, gc_scope_top_level]:
        '''
        How we code up setting the variables that will get collected by the 'TTree::Fill' method is a bit tricky.

        - If we have a sequence then we have to make sure to use push_back into a vector
        - If we have sequences of sequences, then we have to do multiple vector decl and push-backs, including
          declaring some extra variables
        - If the variable is set at a very low level, we need to make sure the Fill is triggered at the proper
          depth.

        Arguments:
            e_rep           XXX
            e_name          The variable that we are saving everything to
            scope_fill      The scope at which the current fill statement is going to be run. We should
                            put the statements that set the variable for collection by Fill at that scope level.

        Returns
            scope_fill      Possibly updated fill scope setting - if we were forced to go down a level (or so).

        '''
        def set_scope(scope: Union[gc_scope_top_level, gc_scope], fill_scope: Union[gc_scope, gc_scope_top_level]):
            if scope.starts_with(fill_scope):
                self._gc.set_scope(scope)
            else:
                self._gc.set_scope(fill_scope)

        # If this is a sequence of a sequence (or deeper) then we need to setup the proper variables.
        if rep_is_collection(e_rep):
            assert isinstance(e_rep, crep.cpp_sequence), \
                f'Do not know how to loop over a {type(e_rep)}'

            def fill_collection_levels(seq: crep.cpp_sequence, accumulator: crep.cpp_value):
                inner = seq.sequence_value()
                scope = seq.scope()
                if isinstance(inner, crep.cpp_sequence):
                    scope = seq.iterator_value().scope()
                    storage = crep.cpp_variable(unique_name('ntuple'), scope, cpp_type=inner.cpp_type())
                    assert not isinstance(scope, gc_scope_top_level)
                    scope.declare_variable(storage)
                    fill_collection_levels(inner, storage)
                    inner = storage

                set_scope(scope, scope_fill)
                self._gc.add_statement(statement.push_back(accumulator, inner))

            fill_collection_levels(e_rep, e_name)

        else:
            # Set the scope. Normally we want to do it where the variable was calculated
            # (think of cases when you have to calculate something with a `push_back`),
            # but if the variable was already calculated, we want to make sure we are at least
            # in the same scope as the tree fill.
            assert isinstance(e_rep, crep.cpp_value)
            set_scope(e_rep.scope(), scope_fill)

            # If the variable is something we are iterating over, then fill it, otherwise,
            # just set it.
            # if rep_is_collection(e_rep):
            #     self._gc.add_statement(statement.push_back(e_name, e_rep.sequence_value()))
            # else:
            self._gc.add_statement(statement.set_var(e_name, e_rep))
            cs = self._gc.current_scope()
            if cs.starts_with(scope_fill):
                scope_fill = cs

        return scope_fill

    def call_ResultTTree(self, node: ast.Call, args: List[ast.AST]):
        '''This AST means we are taking an iterable and converting it to a ROOT file.
        '''
        # Unpack the variables.
        assert len(args) == 4
        source = args[0]
        column_names = _extract_column_names(args[1])
        tree_name = ast.literal_eval(args[2])
        assert isinstance(tree_name, str)
        # root_filename = args[3]

        # Get the representations for each variable. We expect some sort of structure
        # for the variables - or perhaps a single variable.
        self.generic_visit(source)
        v_rep_not_norm = self.as_sequence(source)

        # What we have is a sequence of the data values we want to fill. The iterator at play
        # here is the scope we want to use to run our Fill() calls to the TTree.
        scope_fill = v_rep_not_norm.iterator_value().scope()

        # Clean the data up so it is uniform and the next bit can proceed smoothly.
        # If we don't have a tuple of data to log, turn it into a tuple.
        seq_values = v_rep_not_norm.sequence_value()
        if not isinstance(seq_values, crep.cpp_tuple):
            seq_values = crep.cpp_tuple((v_rep_not_norm.sequence_value(),), scope_fill)

        # Make sure the number of items is the same as the number of columns specified.
        if len(seq_values.values()) != len(column_names):
            raise Exception("Number of columns ({0}) is not the same as labels ({1}) in TTree creation".format(len(seq_values.values()), len(column_names)))

        # Next, look at each on in turn to decide if it is a vector or a simple variable.
        # Create a variable that we will fill for each one.
        var_names = [(name, crep.cpp_variable(unique_name(name, is_class_var=True), self._gc.current_scope(), cpp_type=get_ttree_type(rep)))
                     for name, rep in zip(column_names, seq_values.values())]

        # For each incoming variable, we need to declare something we are going to write.
        for cv in var_names:
            self._gc.declare_class_variable(cv[1])

        # Next, emit the booking code
        self._gc.add_book_statement(self.create_book_ttree_obj(tree_name, var_names))

        # Note that the output file and tree are what we are going to return.
        # The output filename is fixed - the hose code in AnalysisBase has that hard coded.
        # To allow it to be different we have to modify that template too, and pass the
        # information there. If more than one tree is written, the current code would
        # lead to a bug.
        node.rep = rh.cpp_ttree_rep("ANALYSIS.root", tree_name, self._gc.current_scope())  # type: ignore

        # For each varable we need to save, cache it or push it back, depending.
        # Make sure that it happens at the proper scope, where what we are after is defined!
        s_orig = self._gc.current_scope()
        for e_rep, e_name in zip(seq_values.values(), var_names):
            scope_fill = self.code_fill_ttree(e_rep, e_name[1], scope_fill)

        # The fill statement. This should happen at the scope where the tuple was defined.
        # The scope where this should be done is a bit tricky (note the update above):
        # - If a sequence, you want it where the sequence iterator is defined - or outside that scope
        # - If a value, you want it at the level where the value is set.
        self._gc.set_scope(scope_fill)
        self._gc.add_statement(self.create_ttree_fill_obj(tree_name))
        for e in zip(seq_values.values(), var_names):
            if rep_is_collection(e[0]):
                self._gc.add_statement(statement.container_clear(e[1][1]))

        # And we are a terminal, so pop off the block.
        self._gc.set_scope(s_orig)
        self._gc.pop_scope()
        return node.rep  # type: ignore

    def call_Select(self, node: ast.Call, args: List[ast.arg]):
        'Transform the iterable from one form to another'

        assert len(args) == 2
        source = args[0]
        selection = cast(ast.Lambda, args[1])

        # Make sure we are in a loop
        seq = self.as_sequence(source)

        # Simulate this as a "call"
        selection = lambda_unwrap(selection)
        c = ast.Call(func=selection, args=[seq.sequence_value().as_ast()])
        new_sequence_value = self.get_rep(c)

        # We need to build a new sequence.
        rep = crep.cpp_sequence(new_sequence_value, seq.iterator_value(), self._gc.current_scope())

        node.rep = rep  # type: ignore
        self._result = rep
        return rep

    def call_SelectMany(self, node: ast.AST, args: List[ast.AST]):
        r'''
        Apply the selection function to the base to generate a collection, and then
        loop over that collection.
        '''
        assert len(args) == 2
        source = args[0]
        selection = args[1]
        assert isinstance(selection, ast.Lambda)

        # Make sure the source is around. We have to do this because code generation in this
        # framework is lazy. And if the `selection` function does not use the source, and
        # looking at that source might generate a loop, that loop won't be generated! Ops!
        _ = self.as_sequence(source)

        # We need to "call" the source with the function. So build up a new
        # call, and then visit it.

        c = ast.Call(func=lambda_unwrap(selection), args=[source])

        # Get the collection, and then generate the loop over it.
        # It could be that this comes back from something that is already iterating (like a Select statement),
        # in which case we are already looping.
        seq = self.as_sequence(c)

        node.rep = seq  # type: ignore
        self._result = seq
        return seq

    def call_Where(self, node: ast.AST, args: List[ast.AST]):
        'Apply a filtering to the current loop.'

        assert len(args) == 2
        source = args[0]
        filter = args[1]
        assert isinstance(filter, ast.Lambda)

        # Make sure we are in a loop
        seq = self.as_sequence(source)

        # Simulate the filtering call - we want the resulting value to test.
        filter = lambda_unwrap(filter)
        c = ast.Call(func=filter, args=[seq.sequence_value().as_ast()])
        rep = self.get_rep(c)

        # Create an if statement
        self._gc.add_statement(statement.iftest(rep))

        # Ok - new sequence. This the same as the old sequence, only the sequence value is updated.
        # Protect against sequence of sequences (LOVE type checkers, which caught this as a possibility)
        w_val = seq.sequence_value()
        if isinstance(w_val, crep.cpp_sequence):
            raise Exception("Error: A Where clause must evaluate to a value, not a sequence")
        new_sequence_var = w_val.copy_with_new_scope(self._gc.current_scope())
        node.rep = crep.cpp_sequence(new_sequence_var, seq.iterator_value(), self._gc.current_scope())  # type: ignore

        self._result = node.rep  # type: ignore

    def call_Range(self, node: ast.AST, args: List[ast.AST]):
        'Create a collection of numbers from lower_bound'

        if len(args) != 2:
            raise Exception('blah blah')
        lower_bound = args[0]
        upper_bound = args[1]

        self._gc.add_statement(statement.block())

        element_type = ctyp.terminal("int")
        begin_value = crep.cpp_variable(unique_name("begin"), self._gc.current_scope(), element_type, initial_value=self.get_rep(lower_bound))  # type: ignore
        end_value = crep.cpp_variable(unique_name("end"), self._gc.current_scope(), element_type, initial_value=self.get_rep(upper_bound))  # type: ignore
        self._gc.declare_variable(begin_value)
        self._gc.declare_variable(end_value)

        vector_value = crep.cpp_collection(unique_name("r_obj"), self._gc.current_scope(), ctyp.collection(element_type))
        self._gc.declare_variable(crep.cpp_variable(vector_value.as_cpp(), self._gc.current_scope(),
                                                    ctyp.collection(element_type),
                                                    crep.cpp_value(f"{end_value.as_cpp()} - {begin_value.as_cpp()}",
                                                                   self._gc.current_scope(),
                                                                   ctyp.terminal("int"))))

        vector_value_begin = crep.cpp_value(f"{vector_value.as_cpp()}.begin()",
                                            self._gc.current_scope(),
                                            ctyp.terminal(f"std::vector<{element_type}>::iterator"))
        vector_value_end = crep.cpp_value(f"{vector_value.as_cpp()}.end()",
                                          self._gc.current_scope(),
                                          ctyp.terminal(f"std::vector<{element_type}>::iterator"))

        c = ast.Call(func=FunctionAST("std::iota", ["numeric"], "void"),
                     args=[vector_value_begin.as_ast(),
                           vector_value_end.as_ast(),
                           begin_value.as_ast()])

        self._gc.add_statement(statement.arbitrary_statement(self.get_rep(c).as_cpp()))

        seq = self.make_sequence_from_collection(vector_value)
        node.rep = seq  # type: ignore
        self._result = seq
        return seq

    def call_First(self, node: ast.AST, args: List[ast.AST]) -> Any:
        'We are in a sequence. Take the first element of the sequence and use that for future things.'

        # Unpack the source here
        assert len(args) == 1
        source = args[0]

        # Make sure we are in a loop.
        seq = self.as_sequence(source)

        # The First terminal works by protecting the code with a if (first_time) {} block.
        # We need to declare the first_time variable outside the block where the thing we are
        # looping over here is defined. This is a little tricky, so we delegate to another method.
        loop_scope = seq.iterator_value().scope()
        outside_block_scope = loop_scope[-1]

        # Define the variable to track this outside that block.
        is_first = crep.cpp_variable(unique_name('is_first'),
                                     outside_block_scope,
                                     cpp_type=ctyp.terminal('bool'),
                                     initial_value=crep.cpp_value('true', self._gc.current_scope(), ctyp.terminal('bool')))
        outside_block_scope.declare_variable(is_first)

        # Now, as long as is_first is true, we can execute things inside this statement.
        # The trick is putting the if statement in the right place. We need to locate it just one level
        # below where we defined the scope above.
        s = statement.iftest(is_first)
        s.add_statement(statement.set_var(is_first, crep.cpp_value('false', top_level_scope(), cpp_type=ctyp.terminal('bool'))))

        sv = seq.sequence_value()
        if isinstance(sv, crep.cpp_sequence):
            self._gc.set_scope(sv.iterator_value().scope()[-1])
        else:
            self._gc.set_scope(sv.scope())
        self._gc.add_statement(s)

        # If we just found the first sequence in a sequence, return that.
        # Otherwise return a new version of the value.
        first_value = sv if isinstance(sv, crep.cpp_sequence) else sv.copy_with_new_scope(self._gc.current_scope())

        node.rep = first_value  # type: ignore
        self._result = first_value
