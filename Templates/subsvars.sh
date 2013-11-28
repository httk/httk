#!/bin/bash

VERSION=$(python -c "
import sys, os.path, inspect, datetime
_realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
sys.path.insert(1, os.path.join(_realpath,'..'))

import httk
print httk.version
")

DIR=$(dirname "$0")
cd "$DIR"

sed '
s/$HTTKVERSION/'$VERSION'/g
' 
