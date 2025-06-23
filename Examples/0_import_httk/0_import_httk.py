#!/usr/bin/env python
"""
Simple example program using the High-Throughput toolkit (httk)
It simply loads the httk module and print out its version.
"""

from __future__ import print_function, division
import sys, os.path

# If you have set everything up correctly, you should simply be
# to put
#    import httk
# in your script. All other httk examples and tutorial assumes
# this is working.
#
# If this is *not* working, you get the error message:
#     ImportError: No module named httk
# If you have trouble getting this to work, there is the
# possibility to instead use the below code to hard code the
# search path to httk on your system and use that. How to do
# so is shown below. This is an ugly hack, but sometimes
# useful
#
############## code block to import httk ####################
import sys, os
try:
    import httk
except Exception:
    # This variable must be set to the path where you downloaded
    # and uncompressed httk + '/src':
    PATH_TO_HTTK = "~/path/to/httk/src"
    sys.path.insert(1, os.path.expanduser(PATH_TO_HTTK))
    import httk
    print("Note: had to insert the httk path manually")
#############################################################

print("Imported httk version: " + httk.__version__)

