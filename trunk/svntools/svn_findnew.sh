#!/bin/bash
DIRNAME=$(dirname $0)

svn status | grep -e ^? | cat - "$DIRNAME/svn_excludes" "$DIRNAME/svn_excludes" | sort | uniq -u 
