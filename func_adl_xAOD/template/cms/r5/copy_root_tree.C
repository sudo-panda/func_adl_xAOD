void copy_root_tree(const char* input_name, const char* output_name)
{
  TFile *f_in = new TFile(input_name, "READ");
  TFile *f_out = new TFile(output_name, "RECREATE");

  f_in->cd("demo");
  TDirectory *d_current = gDirectory;
  TIter next(gDirectory->GetListOfKeys());
  TKey *key;
  while ((key=(TKey*)next())) {
    if (TString(key->GetClassName()) == "TTree") {
      cout << "Processing " << key->GetName() << endl;

      // Get the old TTree from the old file (make sure the cwd is as expected)
      d_current->cd();
      TTree *t;
      gDirectory->GetObject(key->GetName(), t);

      // Write it out to the new file.
      f_out->cd();
      t->CloneTree()->Write();
    }
  }

  f_out->Write();
  f_out->Close();
  f_in->Close();
}