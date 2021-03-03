# `func_adl_xAOD` Architecture

This file provides a brief overview of how the repository is layed out and how the various bits of code in it cooperate to produce C++ code from a `func_adl` query.

After some general information, more details on how things work follow below.

## General Theory

At the most general level:

1. Client starts with a `func_adl` query in a python `ast.AST`.
1. Client creates a `atlas_xaod_executor` object
1. Client calls `apply_ast_transformation` method with the `ast`. This does `ast` -> `ast` transformations that simplify and combine `ast` elements.
1. Client calls `write_cpp_files` method with the resulting `ast` from the previous step. The output directory where the C++ files can be written
   need to be given to the method as well.
1. The C++ files produced are ready to run on the input files.

Though only part of the tests, you can see how the template files are run against a file in the `test/LocalFile.py` file, specifically the `execute_result_async` method. Given a `func_adl` ast, it calls `atlas_xaod_executor` as above, and then uses a `docker` image to run against some test files.

The `atlas_xaod_executor` doesn't do much - almost all the work is done inside the `query_ast_visitor` object. This object traverses the `ast` and turns each `ast` into some sort of C++ result (see the `cpplib` folder). As it goes it accumulates the appropriate C++ type definitions, temp variables, and variable declarations - including output ROOT files, etc. See below for a more detailed description of this object.

## File Layout

All the source code for the repository is in the `func_adl_xAOD` directory.

- cpplib - Code that is generic to the C++ language - a rudimentary type system, objects that represent variables, etc.
- R21Code - Template C++ code for running against an ATLAS xAOD data file.
- xAODlib - Code that does the translation from a `func_adl` query to generate the C++ template code.

### R21 Code Layout

The files in this directory are templates to run against an ATLAS xAOD in an atlas software release docker container. Note that these containers currently contain only Python 2. The upgrade to Python three will come with R22.

- `runner.sh` is the top level file that controls the run, and is the "api" that is used by the ServiceX container when it spins up a container. This script is responsible for:
  - First run, copy over generated C++ files into an ATLAS analysis release directory structure, compile, and then run against the file(s) given on `runner.sh`'s command line.
  - Second and other runs, auto-detect that the compile step has occurred, and run with any new files requested.
- `package_CMakeList.txt` is a template `cmake` file that is filled in by the generation system. It allows the compile to include only packages that are needed by the query to optimize compile time.
- `ATestRun_eljob.py` is the top level configuration file that controls the xAOD analysis job.
- `query.cxx` and `query.h` are the (mostly empty) template files where the generated query code is inserted.

Note that compile time also defines the time between the query and first data out. Currently it takes about 15 seconds to do the build, and about 15 seconds to run over a single file: it is worth keeping the compile time to a minimum.

## C++ Model

### Type System

The type system is needed to do at least rudimentary tracking of types in the query. For example, to reason about objects and collections and terminals (like float). The Python type system is quite rich, though it lacks introspection utilities, and this provides some extensions to that type system.

- `terminal` this is a type that we can't look inside of - a `float` or an `int` or a `bool`, for example. Some objects will get labeled as `terminals` as well. It has a flag to indicate that it isn't just a terminal, but a pointer to a terminal. It tracks the C++ name of the type, not the Python name.

- `collection` is any sort of grouping of common object that can be iterated over. It tracks the interior type. In C++ the expected semantics are that of a forward iteratable collection.

- `tuple` is a funny: it doesn't actually represent a C++ object or type. Rather, it is a way of collecting a group of python types together that represent a tuple in Python. Tuples like this can/do appear in queries.

More recent versions of Python are gaining introspection tools. It could be at some future point the type system could be removed in favor of a pure Python type system.

### Variables

As the query is turned into C++ code, C++ variables and collections are declared. The `cpp_representations` objects tracks these. Every variable has a type and a scope where it is defined.

Scope is a little tricky:

- Scope defines where the variable is defined. Scope mimics/tracks the standard C++ scoping rules (e.g. it is visible below, but not above/outside the current level).
- It can't be redefined once set. However, there are times where query assembly requires one to know the variable before the scope is set.
- See the `Scope` section for more information.

As different types of things have different capabilities, several objects track variables:

- `cpp_value` - A basic value, like a value (double `123`). It contains the type and scope and name of the variable. This is used for constants and also for variables that do not need to be declared (e.g. are globally available).
- `cpp_variable` - a variable that is declared. An iterator for a loop, or a temp storage for the results of a C++ tertiary operator. Besides everything a `cpp_value` tracks, it also tracks an initial value. When the C++ code is emitted, it will be initialized with the given value.
- `cpp_collection` - Represents a `vector<float>` or similar. Any container with forward iterator semantics.
- `cpp_tuple` - a tuple as a container of other values. This has no direct C++ analogy/type. It is never emitted directly to C++ code. Rather it is used to track an ordered list of values during query building.
- `cpp_dict` - a dictionary as a container of other values. This has no direct C++ analogy/type. It is never emitted directly to C++ code. Rather it is used to track a named list of values during query building.
- `cpp_sequence` - basically, an iterator that points to some object in a collection. It contains the variable that is the actual iterator as well as a pointer to the parent collection.

### Statements

Statements are very simple - they contain very little intelligence; by the time the code has been reduced to a C++ statement all variable naming and placement, etc., has been performed.

### Scope and Statements

When variables are declared the scope at which they are defined must be tracked. Since variables are intertwined with statements, these two things go hand-in-hand.

Broadly, there are two kinds of statements - simple statements and compound statements. All statements must support the `emit` method, which is how code is emitted to the strings that are placed in the template files.

Simple Statements:

- `arbitrary_statement` - an arbitrary line of code.
- `set_var` - 
- `push_back` - 
- `container_clear` - 
- `book_ttree` and `ttree_fill` (these are ATLAS specific statements) - 

Block Statements:

- `block` - 
- `loop` - 
- `iftest` and `elsephrase` -

### Function Mapping

## Traversing the `func_adl` AST

### Statements

### Accumulating the Generated Code & Scope

### Event Collections

### Math Utils

### Traversing the Code
