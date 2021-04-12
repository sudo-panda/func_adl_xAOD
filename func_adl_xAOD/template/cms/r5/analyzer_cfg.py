#!/usr/bin/env python
import FWCore.ParameterSet.Config as cms  # type: ignore

process = cms.Process("Demo")

process.load("FWCore.MessageService.MessageLogger_cfi")

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))

filelistPath = '/scripts/filelist.txt'
fileNames = tuple(['file:{0}'.format(line) for line in open(filelistPath, 'r').readlines()])

process.source = cms.Source("PoolSource",
                            # replace 'myfile.root' with the source file you want to use
                            fileNames=cms.untracked.vstring(
                                *fileNames
                            )
                            )

process.demo = cms.EDAnalyzer('Analyzer'
                              )

process.TFileService = cms.Service("TFileService",
                                   fileName=cms.string('/results/ANALYSIS.root')
                                   )

process.p = cms.Path(process.demo)
