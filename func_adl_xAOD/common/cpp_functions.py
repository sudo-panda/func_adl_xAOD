# Infrastructure to replace simple functions (like "abs") in python with their
# equivalent in C++.
import ast
from collections import namedtuple


class FunctionAST(ast.AST):
    '''
    An AST node that represents a function that can be a drop-in replacement for
    a python function
    '''

    def __init__(self, cpp_name, include_files, cpp_return_type):
        ''' Initialize an AST node that represents a C++ drop-in function call

        cpp_name: The C++ name that we will use to do the call
        include_files: List of include files to be put at the start of the emitted source.
        '''
        self.cpp_name = cpp_name
        self.include_files = include_files
        self.cpp_return_type = cpp_return_type
        self.fields = []


class find_known_functions(ast.NodeTransformer):
    def visit_Call(self, node):
        'Look for a call to a Name function that is in our list'
        # First go one level down.
        self.generic_visit(node)

        # See if we are candidate for replacement
        # Get a fully qualified name as possible.
        if type(node.func) is not ast.Name:
            return node

        try:
            fnc = eval(node.func.id)
            fnc_name = '{0}.{1}'.format(fnc.__module__, node.func.id)
        except NameError:
            fnc_name = node.func.id

        if fnc_name not in functions_to_replace:
            return node

        # Build the replacement.
        info = functions_to_replace[fnc_name]
        node.func = FunctionAST(info.cpp_name, info.include_files, info.cpp_return_type)

        return node


def add_function_mapping(python_name, cpp_name, include_files, return_type):
    '''Add a re-mapping from a python function to an actual function.

    python_name: fully qualified name of the python function
    cpp_name: fully qualified name of the C++ function
    include_files: any include files that should be included in the C++ source. Can also be a single string.
    return_type: C++ return type
    '''
    global functions_to_replace
    functions_to_replace[python_name] = cpp_function(cpp_name, include_files if type(include_files) is list else [include_files, ], return_type)


# The list of functions to do the replacement
functions_to_replace = {}


# The named tuple that stores the replacement info.
cpp_function = namedtuple('cpp_function', ['cpp_name', 'include_files', 'cpp_return_type'])

# CMATH functions - the catalog was pulled from
# http://www.cplusplus.com/reference/cmath/
# Trig
add_function_mapping('sin', 'std::sin', 'cmath', 'double')
add_function_mapping('cos', 'std::cos', 'cmath', 'double')
add_function_mapping('tan', 'std::tan', 'cmath', 'double')
add_function_mapping('acos', 'std::acos', 'cmath', 'double')
add_function_mapping('asin', 'std::asin', 'cmath', 'double')
add_function_mapping('atan', 'std::atan', 'cmath', 'double')
add_function_mapping('atan2', 'std::atan2', 'cmath', 'double')

# Hyperbolic
add_function_mapping('sinh', 'std::sinh', 'cmath', 'double')
add_function_mapping('cosh', 'std::cosh', 'cmath', 'double')
add_function_mapping('tanh', 'std::tanh', 'cmath', 'double')
add_function_mapping('asinh', 'std::asinh', 'cmath', 'double')
add_function_mapping('acosh', 'std::acosh', 'cmath', 'double')
add_function_mapping('atanh', 'std::atanh', 'cmath', 'double')

# Exponential and Log functions
add_function_mapping('exp', 'std::exp', 'cmath', 'double')
# add_function_mapping('frexp', 'std::frexp', 'cmath', 'double')  # By value parameter
add_function_mapping('ldexp', 'std::ldexp', 'cmath', 'double')
add_function_mapping('log', 'std::log', 'cmath', 'double')
add_function_mapping('ln', 'std::log', 'cmath', 'double')
add_function_mapping('log10', 'std::log10', 'cmath', 'double')
# add_function_mapping('modf', 'std::modf', 'cmath', 'double')  # By value parameter
add_function_mapping('exp2', 'std::exp2', 'cmath', 'double')
add_function_mapping('expm1', 'std::expm1', 'cmath', 'double')
add_function_mapping('ilogb', 'std::ilogb', 'cmath', 'double')
add_function_mapping('log1p', 'std::log1p', 'cmath', 'double')
add_function_mapping('log2', 'std::log2', 'cmath', 'double')
add_function_mapping('scalbn', 'std::scalbn', 'cmath', 'double')
add_function_mapping('scalbln', 'std::scalbln', 'cmath', 'double')

# Power Functions
add_function_mapping('pow', 'std::pow', 'cmath', 'double')
add_function_mapping('sqrt', 'std::sqrt', 'cmath', 'double')
add_function_mapping('cbrt', 'std::cbrt', 'cmath', 'double')
add_function_mapping('hypot', 'std::hypot', 'cmath', 'double')

# Error and Gamma Functions
add_function_mapping('erf', 'std::erf', 'cmath', 'double')
add_function_mapping('erfc', 'std::erfc', 'cmath', 'double')
add_function_mapping('tgamma', 'std::tgamma', 'cmath', 'double')
add_function_mapping('lgamma', 'std::lgamma', 'cmath', 'double')

# Rounding and remainder functions
add_function_mapping('ceil', 'std::ceil', 'cmath', 'double')
add_function_mapping('floor', 'std::ceil', 'cmath', 'double')
add_function_mapping('fmod', 'std::ceil', 'cmath', 'double')
add_function_mapping('trunc', 'std::ceil', 'cmath', 'double')
add_function_mapping('round', 'std::ceil', 'cmath', 'double')
# add_function_mapping('lround', 'std::ceil', 'cmath', 'double')  # Long int
# add_function_mapping('llround', 'std::ceil', 'cmath', 'double')  # Long int
add_function_mapping('rint', 'std::ceil', 'cmath', 'double')
# add_function_mapping('lrint', 'std::ceil', 'cmath', 'double')  # Long int
# add_function_mapping('llrint', 'std::ceil', 'cmath', 'double')  # Long int
add_function_mapping('nearbyint', 'std::ceil', 'cmath', 'double')
add_function_mapping('remainder', 'std::ceil', 'cmath', 'double')
add_function_mapping('remquo', 'std::ceil', 'cmath', 'double')

# Floating-point manipulation functions
add_function_mapping('copysign', 'std::copysign', 'cmath', 'double')
add_function_mapping('nan', 'std::nan', 'cmath', 'double')
add_function_mapping('nextafter', 'std::nextafter', 'cmath', 'double')
add_function_mapping('nexttoward', 'std::nexttoward', 'cmath', 'double')

# Minimum, maximum, difference functions
add_function_mapping('fdim', 'std::fdim', 'cmath', 'double')
add_function_mapping('fmax', 'std::fmax', 'cmath', 'double')
add_function_mapping('fmin', 'std::fmin', 'cmath', 'double')

# Other functions
add_function_mapping('fabs', 'std::fabs', 'cmath', 'double')
add_function_mapping('abs', 'std::fabs', 'cmath', 'double')
add_function_mapping('fma', 'std::fma', 'cmath', 'double')

# Python built-in functions. These are weird as they get a different name, and
# don't really come in as a function.
add_function_mapping('builtins.abs', 'std::abs', 'cmath', 'double')
add_function_mapping('builtins.pow', 'std::pow', 'cmath', 'double')  # Not the 3 arg version!

# add_function_mapping('builtins.max', 'std::abs', 'cmath', 'double')  # Do not use to do a sequence
# add_function_mapping('builtins.min', 'std::abs', 'cmath', 'double')  # Do not use to do a sequence
