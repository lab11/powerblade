#!/bin/sh
export GR_DONT_LOAD_PREFS=1
export srcdir=/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/lib
export PATH=/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/lib:$PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DYLD_LIBRARY_PATH
export DYLD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DYLD_LIBRARY_PATH
export PYTHONPATH=$PYTHONPATH
test-PowerBlade_Utils 
