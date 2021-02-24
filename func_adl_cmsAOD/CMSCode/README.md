## Usage

To run this test do the following:

*Assuming you are in the CMSCode directory*

- `docker run --rm --volume="$PWD:/scripts:ro" --volume="$PWD:/results" cmsopendata/cmssw_5_3_32 /scripts/runner.sh`

To run interactive (for testing, etc.) add the flags `-it`, and remove the `/scripts/runner.sh` and add `/bin/bash`. When the container starts up, you can then source the `runner.sh` file to have it correctly setup the release, etc.