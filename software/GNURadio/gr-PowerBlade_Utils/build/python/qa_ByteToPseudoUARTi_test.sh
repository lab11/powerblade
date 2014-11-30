#!/bin/sh
export GR_DONT_LOAD_PREFS=1
export srcdir=/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/python
export PATH=/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/python:$PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DYLD_LIBRARY_PATH
export DYLD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DYLD_LIBRARY_PATH
export PYTHONPATH=/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/swig:$PYTHONPATH
/usr/bin/python2 /home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/python/qa_ByteToPseudoUARTi.py 
