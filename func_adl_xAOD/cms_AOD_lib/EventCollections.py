# Collected code to get collections from the event object
import ast
import copy

import func_adl_xAOD.common_lib.cpp_ast as cpp_ast
import func_adl_xAOD.common_lib.cpp_types as ctyp
import func_adl_xAOD.common_lib.cpp_representation as crep

from func_adl_xAOD.common_lib.cpp_vars import unique_name


# Need a type for our type system to reason about the containers.
class event_collection_container:
    def __init__(self, type_name, is_pointer=True):
        self._type_name = type_name
        self._is_pointer = is_pointer

    def is_pointer(self):
        'All CMS event collections are pointers'
        return self._is_pointer

    def __str__(self):
        return "edm::Handle<{0}>".format(self._type_name)


class event_collection_collection(event_collection_container):
    def __init__(self, type_name, element_name):
        event_collection_container.__init__(self, type_name)
        self._element_name = element_name

    def element_type(self):
        'Return the type of the elements in the collection'
        return ctyp.terminal(self._element_name, is_pointer=False)

    def dereference(self):
        'Return a new version of us that is not a pointer'
        new_us = copy.copy(self)
        new_us._is_pointer = False
        return new_us


# all the collections types that are available. This is required because C++
# is strongly typed, and thus we have to transmit this information.
collections = [
    {
        'function_name': "Tracks",
        'include_files': ['DataFormats/TrackReco/interface/TrackFwd.h'],
        'container_type': event_collection_collection('reco::TrackCollection', 'reco::Track')
    },
    {
        'function_name': "Muons",
        'include_files': ['DataFormats/MuonReco/interface/Muon.h'],
        'container_type': event_collection_collection('reco::TrackCollection', 'reco::Track')
    },
]


def getCollection(info, call_node):
    r'''
    Return a cpp ast for accessing the jet collection
    '''
    # Get the name collection to look at.
    if len(call_node.args) != 1:
        raise ValueError(f"Calling {info['function_name']} - only one argument is allowed")
    if not isinstance(call_node.args[0], ast.Str):
        raise ValueError(f"Calling {info['function_name']} - only acceptable argument is a string")

    # Fill in the CPP block next.
    r = cpp_ast.CPPCodeValue()
    r.args = ['collection_name', ]
    r.include_files += info['include_files']

    r.running_code += ['{0} result;'.format(info['container_type']),
                       'iEvent.getByLabel(collection_name, result);']
    r.result = 'result'

    is_collection = info['is_collection'] if 'is_collection' in info else True
    if is_collection:
        r.result_rep = lambda scope: crep.cpp_collection(unique_name(info['function_name'].lower()), scope=scope, collection_type=info['container_type'])  # type: ignore
    else:
        r.result_rep = lambda scope: crep.cpp_variable(unique_name(info['function_name'].lower()), scope=scope, cpp_type=info['container_type'])

    # Replace it as the function that is going to get called.
    call_node.func = r

    return call_node


# Config everything.
def create_higher_order_function(info):
    'Creates a higher-order function because python scoping is broken'
    return lambda call_node: getCollection(info, call_node)


for info in collections:
    cpp_ast.method_names[info['function_name']] = create_higher_order_function(info)


# Configure some info about the types.
ctyp.add_method_type_info("xAOD::TruthParticle", "prodVtx", ctyp.terminal('xAODTruth::TruthVertex', is_pointer=True))
ctyp.add_method_type_info("xAOD::TruthParticle", "decayVtx", ctyp.terminal('xAODTruth::TruthVertex', is_pointer=True))
ctyp.add_method_type_info("xAOD::TruthParticle", "parent", ctyp.terminal('xAOD::TruthParticle', is_pointer=True))
ctyp.add_method_type_info("xAOD::TruthParticle", "child", ctyp.terminal('xAOD::TruthParticle', is_pointer=True))
