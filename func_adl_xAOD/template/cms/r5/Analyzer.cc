// -*- C++ -*-
//
// Package:    Analyzer
// Class:      Analyzer
//
/**\class Analyzer Analyzer.cc analysis/Analyzer/src/Analyzer.cc

 Description: [one line class summary]

 Implementation:
     [Notes on implementation]
*/
//
// Original Author:
//         Created:  Sat Feb 20 10:48:29 CET 2021
// $Id$
//
//

// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"

// ****************
// //------ EXTRA HEADER FILES--------------------//

{% for i in include_files %}
#include "{{i}}"
{% endfor %}

// for Root tree
#include "TTree.h"

// for muon information
// #include "DataFormats/MuonReco/interface/Muon.h"
// ++++++++++++++++
//
// class declaration
//

class Analyzer : public edm::EDAnalyzer
{
public:
   explicit Analyzer(const edm::ParameterSet &);
   ~Analyzer();

   static void fillDescriptions(edm::ConfigurationDescriptions &descriptions);

private:
   virtual void beginJob();
   virtual void analyze(const edm::Event &, const edm::EventSetup &);
   virtual void endJob();

   virtual void beginRun(edm::Run const &, edm::EventSetup const &);
   virtual void endRun(edm::Run const &, edm::EventSetup const &);
   virtual void beginLuminosityBlock(edm::LuminosityBlock const &, edm::EventSetup const &);
   virtual void endLuminosityBlock(edm::LuminosityBlock const &, edm::EventSetup const &);

   // ----------member data ---------------------------

   TTree *myTree;

   // *******************
   // double pt_gmu;

   // int nRun, nEvt, nLumi;
   {% for l in class_decl %}
   {{l}} 
   {% endfor %}
   // +++++++++++++++++++
};

//
// constants, enums and typedefs
//

//
// static data member definitions
//

//
// constructors and destructor
//
Analyzer::Analyzer(const edm::ParameterSet &iConfig)

{
   //now do what ever initialization is needed
   // *************
   // edm::Service<TFileService> fs;

   // // Transverse momentum of Global Muon in a Tree
   // t1 = fs->make<TTree>("treegmu", "My analysis ntuple");
   // t1->Branch("pt_gmu", &pt_gmu, "pt_gmu/D");

   {% for l in book_code %}
   {{l}} 
   {% endfor %}

   // +++++++++++++
}

Analyzer::~Analyzer()
{

   // do anything here that needs to be done at desctruction time
   // (e.g. close files, deallocate resources etc.)
}

//
// member functions
//

// ------------ method called for each event  ------------
void Analyzer::analyze(const edm::Event &iEvent, const edm::EventSetup &iSetup)
{
   using namespace edm;

#ifdef THIS_IS_AN_EVENT_EXAMPLE
   Handle<ExampleData> pIn;
   iEvent.getByLabel("example", pIn);
#endif

#ifdef THIS_IS_AN_EVENTSETUP_EXAMPLE
   ESHandle<SetupData> pSetup;
   iSetup.get<SetupRecord>().get(pSetup);
#endif

   // edm::Handle<reco::TrackCollection> trackmuons0; 
   //   { 
   //     edm::Handle<reco::TrackCollection> result; 
   //     iEvent.getByLabel("globalMuons", result); 
   //     trackmuons0 = result; 
   //   } 
   //   for (auto &i_obj1 : *trackmuons0) 
   //   { 
   //     _col12 = i_obj1.pt(); 
   //     myTree->Fill(); 
   //   } 

   {% for l in query_code %}
   {{l}} 
   {% endfor %}
}

// ------------ method called once each job just before starting event loop  ------------
void Analyzer::beginJob()
{
}

// ------------ method called once each job just after ending the event loop  ------------
void Analyzer::endJob()
{
}

// ------------ method called when starting to processes a run  ------------
void Analyzer::beginRun(edm::Run const &, edm::EventSetup const &)
{
}

// ------------ method called when ending the processing of a run  ------------
void Analyzer::endRun(edm::Run const &, edm::EventSetup const &)
{
}

// ------------ method called when starting to processes a luminosity block  ------------
void Analyzer::beginLuminosityBlock(edm::LuminosityBlock const &, edm::EventSetup const &)
{
}

// ------------ method called when ending the processing of a luminosity block  ------------
void Analyzer::endLuminosityBlock(edm::LuminosityBlock const &, edm::EventSetup const &)
{
}

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void Analyzer::fillDescriptions(edm::ConfigurationDescriptions &descriptions)
{
   //The following says we do not know what parameters are allowed so do no validation
   // Please change this to state exactly what you do use, even if it is no parameters
   // ************
   edm::ParameterSetDescription desc;
   desc.setUnknown();
   descriptions.addDefault(desc);
   // ++++++++++++
}

//define this as a plug-in
DEFINE_FWK_MODULE(Analyzer);
