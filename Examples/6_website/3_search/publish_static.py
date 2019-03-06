#!/usr/bin/env python

import os, shutil, sys

import httk 
from httk.httkweb import render_website

if not os.path.exists("public"):
    os.mkdir("public")

for filename in os.listdir("public"):
    if not filename.startswith("."):
        f = os.path.join("public",filename)
        if os.path.isdir(f):
            shutil.rmtree(f)
        else:
            os.unlink(f)

render_website("src","public",'./')

sys.stdout.write("*****\nNow open public/index.html in your web browser.\n*****\n")

