#! /usr/bin/env python
#
# This code is a (slightly modified) version of the code published here:
#   http://ed25519.cr.yp.to/python/ed25519.py (fetched 2015-02-15)
# And described here:
#   http://ed25519.cr.yp.to/software.html (fetched 2015-02-15)
#
# Specifically, the authors state:
# "Copyrights: The Ed25519 software is in the public domain."
#
# The modification made here to the code published at ed25519.cr.yp.to are not regarded
# by its author to be significant enough to consitute a derivative work, protected on its own,
# and thus the same rights should hold that applies to the published files.

import sys, base64
from ed25519_utils import run_extra_checks, checkvalid


# Extra checks
run_extra_checks()


if len(sys.argv) < 3:
    sys.exit('Usage: %s public-key-file signature' % sys.argv[0])

public_key_path = sys.argv[1]
b64signature = sys.argv[2]

message = sys.stdin.read().strip()
# message = "test message"

secfile=open(public_key_path, 'r')
b64public_key = secfile.readlines()[0]
secfile.close()
public_key = base64.b64decode(b64public_key)

signature=base64.b64decode(b64signature)
if checkvalid(signature, message, public_key):
    print("TRUE")
else:
    print("FALSE")
