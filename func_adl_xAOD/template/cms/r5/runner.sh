#!/bin/bash

set -e

set -x

## Create a subdir for the analysis
mkdir analysis
cd analysis

## Create the ED Analyzer package
mkedanlzr Analyzer
cd Analyzer

## Copy the Analyzer files to the Analyzer
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cp $DIR/Analyzer.cc ./src/
cp $DIR/analyzer_cfg.py .
cp $DIR/BuildFile.xml .

## build the HiggsDemoAnalyzer
scram b

## run the analysis
cmsRun analyzer_cfg.py