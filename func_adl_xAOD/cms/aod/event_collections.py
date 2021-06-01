import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.common.event_collections import (
    event_collection_collection, event_collection_container, event_collections)


class cms_aod_event_collection_container(event_collection_container):
    def __init__(self, type_name, is_pointer=True):
        super().__init__(type_name, is_pointer)

    def __str__(self):
        return f"edm::Handle<{self._type_name}>"


class cms_aod_event_collection_collection(event_collection_collection):
    def __init__(self, type_name, element_name, is_type_pointer=True, is_element_pointer=True):
        super().__init__(type_name, element_name, is_type_pointer, is_element_pointer)

    def __str__(self):
        return f"edm::Handle<{self._type_name}>"


# all the collections types that are available. This is required because C++
# is strongly typed, and thus we have to transmit this information.
cms_aod_collections = [
    {
        'function_name': "Tracks",
        'include_files': ['DataFormats/TrackReco/interface/Track.h', 'DataFormats/TrackReco/interface/TrackFwd.h'],
        'container_type': cms_aod_event_collection_collection('reco::TrackCollection', 'reco::Track')
    },
    {
        'function_name': "TrackMuons",
        'include_files': ['DataFormats/MuonReco/interface/Muon.h'],
        'container_type': cms_aod_event_collection_collection('reco::TrackCollection', 'reco::Track')
    },
    {
        'function_name': "Muons",
        'include_files': ['DataFormats/MuonReco/interface/Muon.h'],
        'container_type': cms_aod_event_collection_collection('reco::MuonCollection', 'reco::Muon')
    },
]


class cms_aod_event_collections(event_collections):
    def __init__(self):
        super().__init__(cms_aod_collections)

    def get_running_code(self, container_type: event_collection_container) -> list:
        return [f'{container_type} result;',
                'iEvent.getByLabel(collection_name, result);']


ctyp.add_method_type_info("reco::Track", "hitPattern", ctyp.terminal('reco::HitPattern'))
ctyp.add_method_type_info("reco::Muon", "hitPattern", ctyp.terminal('reco::HitPattern'))
