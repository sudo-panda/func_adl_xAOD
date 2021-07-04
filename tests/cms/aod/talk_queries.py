import asyncio
import logging
import os
import sys

import pytest
from func_adl import Range
from func_adl_xAOD.cms.aod import isNonnull
from tests.cms.aod.config import f_single, run_long_running_tests
from tests.cms.aod.utils import as_pandas

pytestmark = run_long_running_tests

def test_muon():
    training_df = as_pandas(
        f_single
        .Select(lambda e: {"m": e.Muons("muons"), "p": e.Vertex("offlinePrimaryVertices")[0].position()})
        .Select(lambda i:
                (
                    i.m
                    .Where(lambda m: m.isPFMuon()
                           and m.isPFIsolationValid()
                           and isNonnull(m.globalTrack())
                           and abs(sqrt((m.globalTrack().dxy(i.p) * m.globalTrack().dxy(i.p))
                                        + (m.globalTrack().dz(i.p) * m.globalTrack().dz(i.p)))
                                   / sqrt((m.globalTrack().d0Error() * m.globalTrack().d0Error())
                                          + (m.globalTrack().dzError() * m.globalTrack().dzError()))) < 4.0
                           and abs((m.globalTrack()).dxy(i.p)) < 0.5
                           and abs((m.globalTrack()).dz(i.p)) < 1.
                           and ((m.pfIsolationR04()).sumChargedHadronPt
                                + (m.pfIsolationR04()).sumNeutralHadronEt
                                + (m.pfIsolationR04()).sumPhotonEt) / m.pt() < 0.4
                           and m.pt() > 5.
                           and abs(m.eta()) < 2.4
                           )
                    .Select(lambda m: m.p()),
                    i.m
                    .Where(lambda m: m.isPFMuon()
                           and m.isPFIsolationValid()
                           and isNonnull(m.globalTrack())
                           and abs(sqrt((m.globalTrack().dxy(i.p) * m.globalTrack().dxy(i.p))
                                        + (m.globalTrack().dz(i.p) * m.globalTrack().dz(i.p)))
                                   / sqrt((m.globalTrack().d0Error() * m.globalTrack().d0Error())
                                          + (m.globalTrack().dzError() * m.globalTrack().dzError()))) < 4.0
                           and abs((m.globalTrack()).dxy(i.p)) < 0.5
                           and abs((m.globalTrack()).dz(i.p)) < 1.
                           and ((m.pfIsolationR04()).sumChargedHadronPt
                                + (m.pfIsolationR04()).sumNeutralHadronEt
                                + (m.pfIsolationR04()).sumPhotonEt) / m.pt() < 0.4
                           and m.pt() > 5.
                           and abs(m.eta()) < 2.4
                           )
                    .Select(lambda m: m.pt()),
                    i.m
                    .Where(lambda m: m.isPFMuon()
                           and m.isPFIsolationValid()
                           and isNonnull(m.globalTrack())
                           and abs(sqrt((m.globalTrack().dxy(i.p) * m.globalTrack().dxy(i.p)) + (m.globalTrack().dz(i.p) * m.globalTrack().dz(i.p)))
                                   / sqrt((m.globalTrack().d0Error() * m.globalTrack().d0Error()) + (m.globalTrack().dzError() * m.globalTrack().dzError()))) < 4.0
                           and abs((m.globalTrack()).dxy(i.p)) < 0.5
                           and abs((m.globalTrack()).dz(i.p)) < 1.
                           and ((m.pfIsolationR04()).sumChargedHadronPt
                                + (m.pfIsolationR04()).sumNeutralHadronEt
                                + (m.pfIsolationR04()).sumPhotonEt) / m.pt() < 0.4
                           and m.pt() > 5.
                           and abs(m.eta()) < 2.4
                           )
                    .Select(lambda m: m.px()),
                    i.m
                    .Where(lambda m: m.isPFMuon()
                           and m.isPFIsolationValid()
                           and isNonnull(m.globalTrack())
                           and abs(sqrt((m.globalTrack().dxy(i.p) * m.globalTrack().dxy(i.p)) + (m.globalTrack().dz(i.p) * m.globalTrack().dz(i.p)))
                                   / sqrt((m.globalTrack().d0Error() * m.globalTrack().d0Error()) + (m.globalTrack().dzError() * m.globalTrack().dzError()))) < 4.0
                           and abs((m.globalTrack()).dxy(i.p)) < 0.5
                           and abs((m.globalTrack()).dz(i.p)) < 1.
                           and ((m.pfIsolationR04()).sumChargedHadronPt
                                + (m.pfIsolationR04()).sumNeutralHadronEt
                                + (m.pfIsolationR04()).sumPhotonEt) / m.pt() < 0.4
                           and m.pt() > 5.
                           and abs(m.eta()) < 2.4
                           )
                    .Select(lambda m: m.py()),
                    i.m
                    .Where(lambda m: m.isPFMuon()
                           and m.isPFIsolationValid()
                           and isNonnull(m.globalTrack())
                           and abs(sqrt((m.globalTrack().dxy(i.p) * m.globalTrack().dxy(i.p)) + (m.globalTrack().dz(i.p) * m.globalTrack().dz(i.p)))
                                   / sqrt((m.globalTrack().d0Error() * m.globalTrack().d0Error()) + (m.globalTrack().dzError() * m.globalTrack().dzError()))) < 4.0
                           and abs((m.globalTrack()).dxy(i.p)) < 0.5
                           and abs((m.globalTrack()).dz(i.p)) < 1.
                           and ((m.pfIsolationR04()).sumChargedHadronPt
                                + (m.pfIsolationR04()).sumNeutralHadronEt
                                + (m.pfIsolationR04()).sumPhotonEt) / m.pt() < 0.4
                           and m.pt() > 5.
                           and abs(m.eta()) < 2.4
                           )
                    .Select(lambda m: m.pz()),
                    i.m
                    .Where(lambda m: m.isPFMuon()
                           and m.isPFIsolationValid()
                           and isNonnull(m.globalTrack())
                           and abs(sqrt((m.globalTrack().dxy(i.p) * m.globalTrack().dxy(i.p)) + (m.globalTrack().dz(i.p) * m.globalTrack().dz(i.p)))
                                   / sqrt((m.globalTrack().d0Error() * m.globalTrack().d0Error()) + (m.globalTrack().dzError() * m.globalTrack().dzError()))) < 4.0
                           and abs((m.globalTrack()).dxy(i.p)) < 0.5
                           and abs((m.globalTrack()).dz(i.p)) < 1.
                           and ((m.pfIsolationR04()).sumChargedHadronPt
                                + (m.pfIsolationR04()).sumNeutralHadronEt
                                + (m.pfIsolationR04()).sumPhotonEt) / m.pt() < 0.4
                           and m.pt() > 5.
                           and abs(m.eta()) < 2.4
                           )
                    .Select(lambda m: m.charge())
                )
                )
    )


def test_electron():
    training_df = as_pandas(
        f_single
        .Select(lambda e: {"m": e.GsfElectrons("gsfElectrons"), "p": e.Vertex("offlinePrimaryVertices")[0].position()})
        .Select(lambda i:
                (
                    i.m
                    .Where(lambda e: e.passingPflowPreselection()
                           and e.pt() > 7.
                           and abs(e.superCluster().eta()) < 2.5
                           and e.gsfTrack().trackerExpectedHitsInner().numberOfHits() <= 1
                           and abs(sqrt((e.gsfTrack().dxy(i.p) * e.gsfTrack().dxy(i.p))
                                        + (e.gsfTrack().dz(i.p) * e.gsfTrack().dz(i.p)))
                                   / sqrt((e.gsfTrack().d0Error() * e.gsfTrack().d0Error())
                                          + (e.gsfTrack().dzError() * e.gsfTrack().dzError()))) < 4.
                           and abs(e.gsfTrack().dxy(i.p)) < 0.5 and abs(e.gsfTrack().dz(i.p)) < 1.
                           and (e.isEB() or e.isEE())
                           and (e.pfIsolationVariables().chargedHadronIso
                                + e.pfIsolationVariables().neutralHadronIso
                                + e.pfIsolationVariables().photonIso) / e.pt() < 0.4
                           )
                    .Select(lambda e: e.p()),
                    i.m
                    .Where(lambda e: e.passingPflowPreselection()
                           and e.pt() > 7.
                           and abs(e.superCluster().eta()) < 2.5
                           and e.gsfTrack().trackerExpectedHitsInner().numberOfHits() <= 1
                           and abs(sqrt((e.gsfTrack().dxy(i.p) * e.gsfTrack().dxy(i.p))
                                        + (e.gsfTrack().dz(i.p) * e.gsfTrack().dz(i.p)))
                                   / sqrt((e.gsfTrack().d0Error() * e.gsfTrack().d0Error())
                                          + (e.gsfTrack().dzError() * e.gsfTrack().dzError()))) < 4.
                           and abs(e.gsfTrack().dxy(i.p)) < 0.5 and abs(e.gsfTrack().dz(i.p)) < 1.
                           and (e.isEB() or e.isEE())
                           and (e.pfIsolationVariables().chargedHadronIso
                                + e.pfIsolationVariables().neutralHadronIso
                                + e.pfIsolationVariables().photonIso) / e.pt() < 0.4
                           )
                    .Select(lambda e: e.pt()),
                    i.m
                    .Where(lambda e: e.passingPflowPreselection()
                           and e.pt() > 7.
                           and abs(e.superCluster().eta()) < 2.5
                           and e.gsfTrack().trackerExpectedHitsInner().numberOfHits() <= 1
                           and abs(sqrt((e.gsfTrack().dxy(i.p) * e.gsfTrack().dxy(i.p))
                                        + (e.gsfTrack().dz(i.p) * e.gsfTrack().dz(i.p)))
                                   / sqrt((e.gsfTrack().d0Error() * e.gsfTrack().d0Error())
                                          + (e.gsfTrack().dzError() * e.gsfTrack().dzError()))) < 4.
                           and abs(e.gsfTrack().dxy(i.p)) < 0.5 and abs(e.gsfTrack().dz(i.p)) < 1.
                           and (e.isEB() or e.isEE())
                           and (e.pfIsolationVariables().chargedHadronIso
                                + e.pfIsolationVariables().neutralHadronIso
                                + e.pfIsolationVariables().photonIso) / e.pt() < 0.4
                           )
                    .Select(lambda e: e.px()),
                    i.m
                    .Where(lambda e: e.passingPflowPreselection()
                           and e.pt() > 7.
                           and abs(e.superCluster().eta()) < 2.5
                           and e.gsfTrack().trackerExpectedHitsInner().numberOfHits() <= 1
                           and abs(sqrt((e.gsfTrack().dxy(i.p) * e.gsfTrack().dxy(i.p))
                                        + (e.gsfTrack().dz(i.p) * e.gsfTrack().dz(i.p)))
                                   / sqrt((e.gsfTrack().d0Error() * e.gsfTrack().d0Error())
                                          + (e.gsfTrack().dzError() * e.gsfTrack().dzError()))) < 4.
                           and abs(e.gsfTrack().dxy(i.p)) < 0.5 and abs(e.gsfTrack().dz(i.p)) < 1.
                           and (e.isEB() or e.isEE())
                           and (e.pfIsolationVariables().chargedHadronIso
                                + e.pfIsolationVariables().neutralHadronIso
                                + e.pfIsolationVariables().photonIso) / e.pt() < 0.4
                           )
                    .Select(lambda e: e.py()),
                    i.m
                    .Where(lambda e: e.passingPflowPreselection()
                           and e.pt() > 7.
                           and abs(e.superCluster().eta()) < 2.5
                           and e.gsfTrack().trackerExpectedHitsInner().numberOfHits() <= 1
                           and abs(sqrt((e.gsfTrack().dxy(i.p) * e.gsfTrack().dxy(i.p))
                                        + (e.gsfTrack().dz(i.p) * e.gsfTrack().dz(i.p)))
                                   / sqrt((e.gsfTrack().d0Error() * e.gsfTrack().d0Error())
                                          + (e.gsfTrack().dzError() * e.gsfTrack().dzError()))) < 4.
                           and abs(e.gsfTrack().dxy(i.p)) < 0.5 and abs(e.gsfTrack().dz(i.p)) < 1.
                           and (e.isEB() or e.isEE())
                           and (e.pfIsolationVariables().chargedHadronIso
                                + e.pfIsolationVariables().neutralHadronIso
                                + e.pfIsolationVariables().photonIso) / e.pt() < 0.4
                           )
                    .Select(lambda e: e.pz()),
                    i.m
                    .Where(lambda e: e.passingPflowPreselection()
                           and e.pt() > 7.
                           and abs(e.superCluster().eta()) < 2.5
                           and e.gsfTrack().trackerExpectedHitsInner().numberOfHits() <= 1
                           and abs(sqrt((e.gsfTrack().dxy(i.p) * e.gsfTrack().dxy(i.p))
                                        + (e.gsfTrack().dz(i.p) * e.gsfTrack().dz(i.p)))
                                   / sqrt((e.gsfTrack().d0Error() * e.gsfTrack().d0Error())
                                          + (e.gsfTrack().dzError() * e.gsfTrack().dzError()))) < 4.
                           and abs(e.gsfTrack().dxy(i.p)) < 0.5 and abs(e.gsfTrack().dz(i.p)) < 1.
                           and (e.isEB() or e.isEE())
                           and (e.pfIsolationVariables().chargedHadronIso
                                + e.pfIsolationVariables().neutralHadronIso
                                + e.pfIsolationVariables().photonIso) / e.pt() < 0.4
                           )
                    .Select(lambda e: e.charge()),
                )
                )
    )
