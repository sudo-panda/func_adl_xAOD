import FWCore.ParameterSet.Config as cms

process = cms.Process("Demo")

process.load("FWCore.MessageService.MessageLogger_cfi")

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))

process.source = cms.Source("PoolSource",
                            # replace 'myfile.root' with the source file you want to use
                            fileNames=cms.untracked.vstring(
                                'root://eospublic.cern.ch//eos/opendata/cms/Run2012C/DoubleMuParked/AOD/22Jan2013-v1/10000/F2878994-766C-E211-8693-E0CB4EA0A939.root'
                            )
                            )

process.demo = cms.EDAnalyzer('Analyzer'
                              )

process.TFileService = cms.Service("TFileService",
                                   fileName=cms.string('/results/ANALYSIS.root')
                                   )

process.p = cms.Path(process.demo)
