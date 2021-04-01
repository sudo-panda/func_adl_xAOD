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
cp /scripts/Analyzer.cc ./src/
cp /scripts/analyzer_cfg.py .
cp /scripts/BuildFile.xml .

## build the HiggsDemoAnalyzer
scram b

## run the analysis
cmsRun analyzer_cfg.py