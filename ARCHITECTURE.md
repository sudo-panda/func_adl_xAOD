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

## C++ Model

### Type System

### Variables

### Function Mapping

## Traversing the `func_adl` AST

### Statements

### Accumulating the Generated Code & Scope

### Event Collections

### Math Utils

### Traversing the Code
