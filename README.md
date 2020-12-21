# func_adl_xAOD

 Backend that converts `qastle` to run on an ATLAS xAOD backend.

[![GitHub Actions Status](https://github.com/iris-hep/func_adl_xAOD/workflows/CI/CD/badge.svg)](https://github.com/iris-hep/func_adl_xAOD/actions?branch=master)
[![Code Coverage](https://codecov.io/gh/iris-hep/func_adl_xAOD/graph/badge.svg)](https://codecov.io/gh/iris-hep/func_adl_xAOD)

[![PyPI version](https://badge.fury.io/py/func-adl-xAOD.svg)](https://badge.fury.io/py/func-adl-xAOD)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/func-adl-xAOD.svg)](https://pypi.org/project/func-adl-xAOD/)

## Introduction

This allows you to query hierarchical data stored in a root file that has been written using the ATLAS xAOD format.
This code allows you to query that.

## Features

A short list of some of the features that are supported by the `xAOD` C++ translator follows.

### Python

Many, but not all, parts of the `python` language are supported. As a general rule, anything that is a statement or flow control is not supported. So no `if` or `while` or `for` statements, for example. Assignment isn't supported, which may sound limiting - but this is a functional implementation so it is less to than one might think.

What follows are the parts of the language that are covered:

- Function calls, method calls, and lambda calls (and lambda functions), with some limitations.
- Integer indexing into arrays
- Limited tuple support as a means of collecting information together, or as an output to a ROOT file or pandas `DataFrame` or `awkward` array.
- Limited list support (in same way as above). In particular, the `append` method is not supported as that modifies the list, rather than creating a new one.
- Unary, Binary, and comparison operations. Only 2 argument comparisons are supported (e.g. `a > b` and not `a > b > c`).
- Using `and` and `or` to combine conditional expressions. Note that this is written as `&` and `|` when writing an expression due to the fact `python` demands a `bool` return from `and` and `or` when written in code.
- The conditional if expression (`10 if a > 10 else 20`)
- Floating point numbers, integers, and strings.

### xAOD Functions

You can call the functions that are supported by the C++ objects as long as the required arguments are primitive types. Listed below are special _extra_ functions attached to various objects in the ATLAS xAOD data model.

#### The Event

The event object has the following special functions to access collections:

- `Jets`, `Tracks`, `EventInfo`, `TruthParticles`, `Electrons`, `Muons`, and `MissingET`. Each function takes a single argument, the name of the bank in the xAOD. For example, for the electrons one can pass `"Electrons"`.

Adding new collections is fairly easy.

#### The Jet Object

Template functions don't make sense yet in python.

- `getAttribute` - this function is templated, so must be called as either `getAttributeFloat` or `getAttributeVectorFloat`.

### Math

- Math Operators: +, -, *, /, %
- Comparison Operators: <, <=, >, >=, ==, !=
- Unary Operators: +, -, not
- Math functions are pulled from the C++ [`cmath` library](http://www.cplusplus.com/reference/cmath/): `sin`, `cos`, `tan`, `acos`, `asin`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`, `exp`, `ldexp`, `log`, `ln`, `log10`, `exp2`, `expm1`, `ilogb`, `log1p`, `log2`, `scalbn`, `scalbln`, `pow`, `sqrt`, `cbrt`, `hypot`, `erf`, `erfc`, `tgamma`, `lgamma`, `ceil`, `floor`, `fmod`, `trunc`, `round`, `rint`, `nearbyint`, `remainder`, `remquo`, `copysign`, `nan`, `nextafter`, `nexttoward`, `fdim`, `fmax`, `fmin`, `fabs`, `abs`, `fma`.
- Do not use `math.sin` in a call. However `sin` is just fine. If you do, you'll get an exception during resolution that it doesn't know how to translate `math`.
- for things like `sum`, `min`, `max`, etc., use the `Sum`, `Min`, `Max` LINQ predicates.

## Testing and Development

Setting up the development environment:

- After creating a virtual environment, do a setup-in-place: `pip install -e .[test]`

To run tests:

- `pytest -m "not xaod_runner"` will run the _fast_ tests.
- `pytest -m "xaod_runner"` will run the slow tests that require docker installed on your command line. `docker` is involved via pythons `os.system` - so it needs to be available to the test runner.

Contributing:

- Develop in another repo or on a branch
- Submit a PR against the `master` branch.

In general, the `master` branch should pass all tests all the time. Releases are made by tagging on the master branch.
