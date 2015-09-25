#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# It simply loads the httk module and print out its version.

from __future__ import print_function, division
import sys, os.path

# If you have set everything up correctly, you should simply be able to do 
#    import httk
# But, for this to work you need to 'source' the 'setup_paths.shell' 
# script in the httk directory.
# (Preferably you add it to your login init files.)
# All the httk examples and tutorial assumes this is working. 
#
# If this is *not* working, you get the error message:
#     ImportError: No module named httk
# If you have trouble getting this to work, you can instead use the below 
# block of code to import httk. 
# This should fix things (but hard-codes the path you use for httk inside 
# your programs, which is an ugly hack.)

############## code block to import httk ####################
import sys, os
try:    
    import httk
except Exception:
    # This variable must be set to the path where you downloaded
    # and uncompressed httk:
    PATH_TO_HTTK="~/path/to/httk"
    sys.path.insert(1, os.path.expanduser(PATH_TO_HTTK))
    import httk
#############################################################

print("httk imported. Version:",httk.version)

