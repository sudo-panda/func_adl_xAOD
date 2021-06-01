import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.common.event_collections import (
    event_collection_collection, event_collection_container, event_collections)


class atlas_xaod_event_collection_container(event_collection_container):
    def __init__(self, type_name, is_pointer=True):
        super().__init__(type_name, is_pointer)

    def __str__(self):
        return f"edm::Handle<{self._type_name}>"


class atlas_xaod_event_collection_collection(event_collection_collection):
    def __init__(self, type_name, element_name, is_type_pointer=True, is_element_pointer=True):
        super().__init__(type_name, element_name, is_type_pointer, is_element_pointer)

    def __str__(self):
        return f"const {self._type_name}*"


# all the collections types that are available. This is required because C++
# is strongly typed, and thus we have to transmit this information.
atlas_xaod_collections = [
    {
        'function_name': "Jets",
        'include_files': ['xAODJet/JetContainer.h'],
        'container_type': atlas_xaod_event_collection_collection('xAOD::JetContainer', 'xAOD::Jet'),
    },
    {
        'function_name': "Tracks",
        'include_files': ['xAODTracking/TrackParticleContainer.h'],
        'container_type': atlas_xaod_event_collection_collection('xAOD::TrackParticleContainer', 'xAOD::TrackParticle')
    },
    {
        'function_name': "EventInfo",
        'include_files': ['xAODEventInfo/EventInfo.h'],
        'container_type': atlas_xaod_event_collection_container('xAOD::EventInfo'),
        'is_collection': False,
    },
    {
        'function_name': "TruthParticles",
        'include_files': ['xAODTruth/TruthParticleContainer.h', 'xAODTruth/TruthParticle.h', 'xAODTruth/TruthVertex.h'],
        'container_type': atlas_xaod_event_collection_collection('xAOD::TruthParticleContainer', 'xAOD::TruthParticle')
    },
    {
        'function_name': "Electrons",
        'include_files': ['xAODEgamma/ElectronContainer.h', 'xAODEgamma/Electron.h'],
        'container_type': atlas_xaod_event_collection_collection('xAOD::ElectronContainer', 'xAOD::Electron')
    },
    {
        'function_name': "Muons",
        'include_files': ['xAODMuon/MuonContainer.h', 'xAODMuon/Muon.h'],
        'container_type': atlas_xaod_event_collection_collection('xAOD::MuonContainer', 'xAOD::Muon')
    },
    {
        'function_name': "MissingET",
        'include_files': ['xAODMissingET/MissingETContainer.h', 'xAODMissingET/MissingET.h'],
        'container_type': atlas_xaod_event_collection_collection('xAOD::MissingETContainer', 'xAOD::MissingET'),
    },
]


class atlas_xaod_event_collections(event_collections):
    def __init__(self):
        super().__init__(atlas_xaod_collections)

    def get_running_code(self, container_type: event_collection_container) -> list:
        return [f'{container_type} result = 0;',
                'ANA_CHECK (evtStore()->retrieve(result, collection_name));']


# Configure some info about the types.
ctyp.add_method_type_info("xAOD::TruthParticle", "prodVtx", ctyp.terminal('xAODTruth::TruthVertex', is_pointer=True))
ctyp.add_method_type_info("xAOD::TruthParticle", "decayVtx", ctyp.terminal('xAODTruth::TruthVertex', is_pointer=True))
ctyp.add_method_type_info("xAOD::TruthParticle", "parent", ctyp.terminal('xAOD::TruthParticle', is_pointer=True))
ctyp.add_method_type_info("xAOD::TruthParticle", "child", ctyp.terminal('xAOD::TruthParticle', is_pointer=True))
