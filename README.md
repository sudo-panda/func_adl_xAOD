# func_adl_xAOD
 Client interface to send a hierarchical SQL-like query to an xAOD backend

[![GitHub Actions Status](https://github.com/iris-hep/func_adl_xAOD/workflows/CI/CD/badge.svg)](https://github.com/iris-hep/func_adl_xAOD/actions?branch=master)
[![Code Coverage](https://codecov.io/gh/iris-hep/func_adl_xAOD/graph/badge.svg)](https://codecov.io/gh/iris-hep/func_adl_xAOD)

[![PyPI version](https://badge.fury.io/py/func-adl-xAOD.svg)](https://badge.fury.io/py/func-adl-xAOD)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/func-adl-xAOD.svg)](https://pypi.org/project/func-adl-xAOD/)

## Introduction

This allows you to query hierarchical data stored in a root file that has been written using the ATLAS xAOD format.
This code allows you to query that.

## Features

### xAOD Functions

You can call the functions that are supported by the C++ objects as long as the required arguments are primitive types.

#### The Event

The event object has the following special functions to access collections:

- `Jets`, `Tracks`, `EventInfo`, `TruthParticles`, `Electrons`, `Muons`, and `MissingET`. Each function takes a single argument, the name of the bank in the xAOD. For example, for the electrons one can pass `"Electrons"`.

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
