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
from ed25519_utils import run_extra_checks, publickey, signature


# Extra checks
run_extra_checks()

if len(sys.argv) < 2:
    sys.exit('Usage: %s private-key-file' % sys.argv[0])

message = sys.stdin.read().strip()
# message = "test message"

secret_key_path = sys.argv[1]
secfile = open(secret_key_path,'r')
b64secret_key = secfile.readlines()[0]
secfile.close()

secret_key = base64.b64decode(b64secret_key)
public_key = publickey(secret_key)
signature = signature(message, secret_key, public_key)
b64signature = base64.b64encode(signature).decode('utf-8')
print(b64signature)
