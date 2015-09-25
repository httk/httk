#! /usr/bin/env python

import hashlib, sys, StringIO

def hexhash(filename):
    def chunks(f, size=8192): 
        while True: 
            s = f.read(size) 
            if not s: break 
            yield s     
    f = open(filename,'rb')
    s = hashlib.sha256() 
    for chunk in chunks(f): 
        s.update(chunk) 
    f.close()
    return s.hexdigest() 

if len(sys.argv)<2:
    message = sys.stdin.read()
    s = hashlib.sha256() 
    s.update(message) 
    print s.hexdigest()+"  -"
    exit(0)
else:
    for arg in sys.argv[1:]:
        print hexhash(arg)+"  "+arg
    exit(0)
