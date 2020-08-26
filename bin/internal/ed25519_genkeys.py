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

import os, sys, hashlib, base64
from ed25519_utils import publickey, run_extra_checks


# Extra checks
run_extra_checks()

if len(sys.argv) < 3:
    sys.exit('Usage: %s public-key-file private-key-file' % sys.argv[0])

public_key_path = sys.argv[1]
secret_key_path = sys.argv[2]
if len(sys.argv)>=4:
    comment = sys.argv[3]
else:
    comment = ""

try:
    secret_key = os.urandom(64)
except NotImplementedError:
    raise Exception("crypto.generate_keys: Running on a system without a safe random number generator, cannot create safe cryptographic keys on this system.")

public_key = publickey(secret_key)

b64secret_key = base64.b64encode(secret_key).decode('utf-8')
b64public_key = base64.b64encode(public_key).decode('utf-8')

pubfile=open(public_key_path, 'w')
pubfile.write(b64public_key)
pubfile.write("\n")
pubfile.write(comment)
pubfile.close()

secfile=open(secret_key_path, 'w')
secfile.write(b64secret_key)
secfile.close()
