#! /usr/bin/env python

import sys, os, hashlib, base64, re, bz2
import hashlib

if sys.version_info[0] == 3:
    import configparser
else:
    import ConfigParser as configparser

b = 256
q = 2**255 - 19
l = 2**252 + 27742317777372353535851937790883648493

def H(m):
    return hashlib.sha512(m).digest()

def expmod(b,e,m):
    if e == 0: return 1
    t = expmod(b,e/2,m)**2 % m
    if e & 1: t = (t*b) % m
    return t

def inv(x):
    return expmod(x,q-2,q)

d = -121665 * inv(121666)
I = expmod(2,(q-1)/4,q)

def xrecover(y):
    xx = (y*y-1) * inv(d*y*y+1)
    x = expmod(xx,(q+3)/8,q)
    if (x*x - xx) % q != 0: x = (x*I) % q
    if x % 2 != 0: x = q-x
    return x

By = 4 * inv(5)
Bx = xrecover(By)
B = [Bx % q,By % q]

def edwards(P,Q):
    x1 = P[0]
    y1 = P[1]
    x2 = Q[0]
    y2 = Q[1]
    x3 = (x1*y2+x2*y1) * inv(1+d*x1*x2*y1*y2)
    y3 = (y1*y2+x1*x2) * inv(1-d*x1*x2*y1*y2)
    return [x3 % q,y3 % q]

def scalarmult(P,e):
    if e == 0: return [0,1]
    Q = scalarmult(P,e/2)
    Q = edwards(Q,Q)
    if e & 1: Q = edwards(Q,P)
    return Q

def encodeint(y):
    bits = [(y >> i) & 1 for i in range(b)]
    return ''.join([chr(sum([bits[i * 8 + j] << j for j in range(8)])) for i in range(b/8)])

def encodepoint(P):
    x = P[0]
    y = P[1]
    bits = [(y >> i) & 1 for i in range(b - 1)] + [x & 1]
    return ''.join([chr(sum([bits[i * 8 + j] << j for j in range(8)])) for i in range(b/8)])

def bit(h,i):
    return (ord(h[i/8]) >> (i%8)) & 1

def publickey(sk):
    h = H(sk)
    a = 2**(b-2) + sum(2**i * bit(h,i) for i in range(3,b-2))
    A = scalarmult(B,a)
    return encodepoint(A)

def Hint(m):
    h = H(m)
    return sum(2**i * bit(h,i) for i in range(2*b))

def signature(m,sk,pk):
    h = H(sk)
    a = 2**(b-2) + sum(2**i * bit(h,i) for i in range(3,b-2))
    r = Hint(''.join([h[i] for i in range(b/8,b/4)]) + m)
    R = scalarmult(B,r)
    S = (r + Hint(encodepoint(R) + pk + m) * a) % l
    return encodepoint(R) + encodeint(S)

def isoncurve(P):
    x = P[0]
    y = P[1]
    return (-x*x + y*y - 1 - d*x*x*y*y) % q == 0

def decodeint(s):
    return sum(2**i * bit(s,i) for i in range(0,b))

def decodepoint(s):
    y = sum(2**i * bit(s,i) for i in range(0,b-1))
    x = xrecover(y)
    if x & 1 != bit(s,b-1): x = q-x
    P = [x,y]
    if not isoncurve(P): raise Exception("decoding point that is not on curve")
    return P

def checkvalid(s,m,pk):
    if len(s) != b/4: raise Exception("signature length is wrong")
    if len(pk) != b/8: raise Exception("public-key length is wrong")
    R = decodepoint(s[0:b/8])
    A = decodepoint(pk)
    S = decodeint(s[b/8:b/4])
    h = Hint(encodepoint(R) + pk + m)
    if scalarmult(B,S) != edwards(R,scalarmult(A,h)):
        #raise Exception("signature does not pass verification")
        return False
    else:
        return True

# Extra checks
assert b >= 10
assert 8 * len(H("hash input")) == 2 * b
assert expmod(2,q-1,q) == 1
assert q % 4 == 1
assert expmod(2,l-1,l) == 1
assert l >= 2**(b-4)
assert l <= 2**(b-3)
assert expmod(d,(q-1)/2,q) == q-1
assert expmod(I,2,q) == q-1
assert isoncurve(B)
assert scalarmult(B,l) == [0,1]

def nested_split(s,start,stop):
    parts = []
    if s[0] != start:
        return [s]
    chars = []
    n = 0
    for c in s:
        if c == start:
            if n > 0:
                chars.append(c)
            n += 1
        elif c == stop:
            n -= 1
            if n > 0:
                chars.append(c)
            elif n == 0:
                parts.append(''.join(chars).lstrip().rstrip())
                chars = []
        elif n > 0:
            chars.append(c)
    return parts

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

def check_manifest_dir(basedir,manifestfilename, excludespath, debug=False):
    message=""

    excludes=[]
    if os.path.exists(os.path.join(excludespath,"excludes")):
        f = read(os.path.join(excludespath,"excludes"))
        excludes=[x.stip() for x in f.readlines()]
        f.close()
    try:
        cp=configparser.ConfigParser()
        cp.read(os.path.join(excludespath,"config"))
        excludestr=cp.get('main','excludes').strip()
        excludes+=nested_split(excludestr,'[',']')
    except (configparser.NoOptionError, configparser.NoSectionError):
        pass

    if len(excludes) == 0:
        excludes = ['.*~']
    excludes+=['ht\.manifest\..*','ht\.project/keys','ht\.project/manifest','ht\.project/computers','ht\.project/excludes','ht\.project/tags','ht\.project/references','ht\.tmp\..*']

    manifestfile = bz2.BZ2File(manifestfilename,'r')

    b64pubkey=manifestfile.readline()
    message += b64pubkey
    key = manifestfile.readline()
    while key!='\n' and key != '':
        message += key
        key = manifestfile.readline()
    message += key

    for root, unsorteddirs, unsortedfiles in os.walk(basedir,topdown=True, followlinks=False):
        if root==basedir:
            root = ""
        else:
            root = os.path.relpath(root, basedir)
        files = sorted(unsortedfiles)
        dirs = sorted(unsorteddirs)
        filenames = [os.path.join(root,x) for x in files]
        for i,f in enumerate(files):
            filename = filenames[i]
            for exclude in excludes:
                if re.match(exclude,f) != None or re.match(exclude,filename) != None:
                    break
            else:
                truefilename=os.path.join(basedir,filename)
                compare=manifestfile.readline()
                message+=compare
                hh = hexhash(truefilename)
                if compare != hh + " " + filename + "\n":
                    print("FAILURE1:",compare+"|"+ hh + " " + filename + "\n")
                    return False
                if debug:
                    print("Checked:",hh+" "+filename+" ")
        keepdirs = []
        for d in dirs:
            fulldir = os.path.join(root,d)
            for exclude in excludes:
                if re.match(exclude,d) != None or re.match(exclude,fulldir) != None:
                    break
            else:
                if d.startswith("ht.task.") or os.path.exists(os.path.join(fulldir,'ht.config')):
                    print("Validating task manifest in:",fulldir)
                    result = check_manifest_dir(fulldir,os.path.join(fulldir,'ht.manifest.bz2'),os.path.join(fulldir,'ht.config'))
                    if not result:
                        return False
                    compare=manifestfile.readline()
                    message+=compare
                    hh = hexhash(os.path.join(fulldir,'ht.manifest.bz2'))
                    if compare != hh + " " + fulldir + "/\n":
                        print("FAILURE2:",compare,"|"+ hh + " " + fulldir + "/\n")
                        return False
                    if debug:
                        print("Checked:",hh+" "+fulldir+"/ ")
                else:
                    keepdirs += [d]
        unsorteddirs[:] = keepdirs

    compare = manifestfile.readline()
    if compare != "\n":
        print("FAILURE3:",compare,"|","(should be empty)")
        return False

    b64signature = manifestfile.readline()
    #print("===="+message+"====")

    pk = base64.b64decode(b64pubkey)
    signature = base64.b64decode(b64signature)

    result = checkvalid(signature,message,pk)
    if not result:
        print("FAILURE: Signature does not verify.")
        return False

    manifestfile.close()
    return True

basedir = sys.argv[1]
result = check_manifest_dir(basedir,'ht.project/manifest.bz2', 'ht.project',debug=False)
if result:
    print("Manifest check sucessful.")
    exit(42)
else:
    print("Manifest check FAILED.")
    exit(13)
