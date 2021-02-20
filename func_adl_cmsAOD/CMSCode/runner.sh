#!/bin/bash

set -e

set -x

## Create a subdir for the analysis
mkdir analysis
cd analysis

## copy the analyzer to the analysis for folder
cp -r /scripts/* .

## build the HiggsDemoAnalyzer
cd Analyzer
scram b

## run the analysis
cmsRun analyzer_cfg.py

