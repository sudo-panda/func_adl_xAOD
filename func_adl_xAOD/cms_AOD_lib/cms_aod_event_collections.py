import func_adl_xAOD.common_lib.cpp_ast as cpp_ast

from func_adl_xAOD.common_lib.event_collections import event_collection_collection, event_collection_container, create_higher_order_function


class cms_aod_event_collection_container(event_collection_container):
    def __str__(self):
        return f"edm::Handle<{self._type_name}>"


class cms_aod_event_collection_collection(event_collection_collection):
    def __str__(self):
        return f"edm::Handle<{self._type_name}>"


# all the collections types that are available. This is required because C++
# is strongly typed, and thus we have to transmit this information.
cms_aod_collections = [
    {
        'function_name': "Tracks",
        'include_files': ['DataFormats/TrackReco/interface/TrackFwd.h'],
        'container_type': cms_aod_event_collection_collection('reco::TrackCollection', 'reco::Track')
    },
    {
        'function_name': "Muons",
        'include_files': ['DataFormats/MuonReco/interface/Muon.h'],
        'container_type': cms_aod_event_collection_collection('reco::TrackCollection', 'reco::Track')
    },
]

for info in cms_aod_collections:
    cpp_ast.method_names[info['function_name']] = create_higher_order_function(info)
