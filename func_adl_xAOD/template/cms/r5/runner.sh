#!/bin/bash

set -e
set -x

# Parse the command line arguments. Our defaults
output_method="cp"
output_dir="/results"
input_method="filelist"
input_file=""
compile=1
run=1

while getopts "d:o:cr" opt; do
    case "$opt" in
    d)
        input_method="cmd"
        input_file=$OPTARG
        ;;
    c)
        run=0
        ;;
    r)
        compile=0
        ;;
    o)
        output_dir=$OPTARG
        ;;
    ?)
        exit 10
    esac
done

# If there are any arguments left over, then very bad things have happened.
shift $((OPTIND-1))
if [ $# != 0 ]; then
  echo "Extra arguments on the command line $@"
  exit 1
fi

# Setup the CMS software (normally done automatically, but not for ServiceX)
if [ -z "$CVSROOT" ]; then
    . /opt/cms/entrypoint.sh; 
fi

## Get the location of this script, and, hence where we are going to be doing things.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
local=`pwd`

# Build the analysis is need be
if [ $compile = 1 ]; then

    ## Create a subdir for the analysis
    mkdir analysis
    cd analysis

    ## Create the ED Analyzer package
    mkedanlzr Analyzer
    cd Analyzer


    cp $DIR/Analyzer.cc ./src/
    cp $DIR/analyzer_cfg.py .
    cp $DIR/BuildFile.xml .

    ## build the analyzer
    scram b
else
    cd analysis/Analyzer
fi

# Run the analysis
if [ $run = 1 ]; then
    # Figure out the input file
    if [ "$input_method" == "filelist" ]; then
        if [ -e $DIR/filelist.txt ]; then
            cp $DIR/filelist.txt .
        else
            cp $local/filelist.txt .
        fi
    elif [ "$input_method" == "cmd" ]; then
        echo $input_file > filelist.txt
    fi

    # Figure out the output file
    if [ $output_method == "cp" ]; then
        destination=$output_dir
        cmd="cp"
    else
        destination=$1
      cmd="cp"
      if [[ $destination == "root:"* ]]; then
         cmd="xrdcp"
      fi
    fi
    export CMS_OUTPUT_FILE=ANALYSIS.root

    # run the analysis
    cmsRun analyzer_cfg.py

    # And copy out the thing
    # TODO: why doesn't cms deal with the very long filename we give it?
    $cmd ./$CMS_OUTPUT_FILE $destination
fi
