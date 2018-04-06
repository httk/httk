#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2015 Rickard Armiento
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Provides a few central and very helpful functions for cryptographic hashes, etc.
"""
import hashlib, os.path, base64, re
try:
    import bz2
except Exception:
    pass
import ConfigParser
from .ioadapters import IoAdapterFileReader, IoAdapterFileWriter
from httk.core.basic import nested_split


def hexhash_str(data, prepend=None):
    s = hashlib.sha1()
    s.update("httk\0")
    if prepend is not None:
        s.update(prepend)
        s.update("\0")
    s.update(data)
    s.update("\0%u\0" % len(data))
    return s.hexdigest()


def tuple_to_hexhash(t):
    return hexhash_str(tuple_to_str(t))


def hexhash_ioa(ioa, prepend=None):
    def chunks(f, size=8192):
        while True:
            s = f.read(size)
            if not s:
                break
            yield s
    ioa = IoAdapterFileReader.use(ioa)
    f = ioa.file
    s = hashlib.sha1()
    size = 0
    s.update("httk\0")
    if prepend is not None:
        s.update("\0")
        s.update(prepend)
    for chunk in chunks(f):
        size += len(chunk)
        s.update(chunk)
    ioa.close()
    s.update("\0%u\0" % size)
    return s.hexdigest()

# def generate_manifest_for_files(codename,codever, basedir, filenames,fakenames=None,skip_filenames=False,write=False,excludes=None):
#     hash_manifest=codename+" "+codever+"\n\n"
#     # We should always exclude the ht.manifest file form the manifest
#     if excludes == None:
#         excludes = ['ht.manifest']
#     else:
#         excludes.append('ht.manifest')
#
#     for i in range(len(filenames)):
#         f = filenames[i]
#         if skip_filenames:
#             try:
#                 hash_manifest += hexhash_ioa(f)+"\n"
#             except IOError:
#                 hash_manifest += "0\n"
#         else:
#             if fakenames != None and fakenames[i] != None:
#                 relpath = fakenames[i]
#             else:
#                 common_prefix = os.path.commonprefix([basedir, f])
#                 if common_prefix == '':
#                     relpath = f
#                 else:
#                     relpath = os.path.relpath(f, common_prefix)
#             if relpath in excludes:
#                 continue
#             try:
#                 hash_manifest += relpath+" "+hexhash_ioa(f)+"\n"
#             except IOError:
#                 hash_manifest += relpath+" "+"0\n"
#
#     hash_hex = hexhash_str(hash_manifest)
#
#     if write != None:
#         ioa = IoAdapterFileWriter.use(os.path.join(basedir,"ht.manifest"))
#         ioa.file.write(hash_manifest)
#         ioa.file.close()
#
#     return (hash_manifest,hash_hex)

# def generate_manifest_for_dir(codename,codever, basedir, excludes=None, fakenames=None, skip_filenames=False,write=False):
#     filelist = []
#
#     for root, dirs, files in os.walk(basedir):
#         filelist += [os.path.join(root,x) for x in files]
#         # Make sure we always generate the same manifest
#     filelist = sorted(filelist)
#
#     return generate_manifest_for_files(codename, codever, basedir, filelist, fakenames=fakenames, skip_filenames=skip_filenames,write=write,excludes=excludes)
#
#
#    #raise Exception("generate_manifest_for_dir: Not implemented, sorry")
#
# def check_or_generate_manifest_for_dir(codename,codever, basedir, excludes=None, fakenames=None, skip_filenames=False):
#     manifestpath = os.path.join(basedir,"ht.manifest")
#     if excludes == None:
#         excludes = ['ht.manifest']
#     else:
#         excludes.append('ht.manifest')
#
#     if os.path.exists(manifestpath):
#         # Just verify that manifest is correct
#         (manifest, hexhash) = generate_manifest_for_dir(codename,codever, basedir, excludes=None, fakenames=None, skip_filenames=False,write=False)
#         test = IoAdapterFileReader.use(manifestpath).file.read()
#         hexhash1 = hexhash_str(manifest)
#         hexhash2 = hexhash_str(test)
#         hexhash3 = hexhash_ioa(manifestpath)
#         #print hexhash,hexhash1, hexhash2,hexhash3
#         #print "-----"
#         #print test
#         #print "-----"
#         #print manifest
#         #print "-----"
#         if hexhash != hexhash2:
#             raise Exception("Manifest mismatch, the ht.manifest in the directory does not match the actual files! Hashes are:"+str(hexhash)+" vs. "+str(hexhash2))
#     else:
#         # Generate a new manifest
#         (manifest, hexhash) = generate_manifest_for_dir(codename,codever, basedir, excludes=None, fakenames=None, skip_filenames=False,write=True)
#
#     return (manifest, hexhash)


def tuple_to_str(t):
    strlist = []
    for i in t:
        if isinstance(i, tuple):
            tuplestr = "\n"
            tuplestr += tuple_to_str(i)
            #tuplestr += "\n"
            strlist.append(tuplestr)
        else:
            strlist.append(unicode(i).encode("utf-8"))
    return " ".join(strlist)


def read_keys(keydir):
    from . import ed25519

    f = open(os.path.join(keydir, 'key1.priv'), "r")
    b64sk = f.read()
    f.close()
    sk = base64.b64decode(b64sk)
    pk = ed25519.publickey(sk)
    return (sk, pk)


def sha256file(filename):
    def chunks(f, size=8192):
        while True:
            s = f.read(size)
            if not s:
                break
            yield s
    f = open(filename, 'rb')
    s = hashlib.sha256()
    for chunk in chunks(f):
        s.update(chunk)
    f.close()
    return s.hexdigest()


def manifest_dir(basedir, manifestfile, excludespath, keydir, sk, pk, debug=False, force=False):
    from . import ed25519

    message = ""

    excludes = []
    if os.path.exists(os.path.join(excludespath, "excludes")):
        f = open(os.path.join(excludespath, "excludes"))
        excludes = [x.strip() for x in f.readlines()]
        f.close()
    try:
        cp = ConfigParser.ConfigParser()
        cp.read(os.path.join(excludespath, "config"))
        excludestr = cp.get('main', 'excludes').strip()
        excludes += nested_split(excludestr, '[', ']')
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        pass

    if len(excludes) == 0:
        excludes = ['.*~']
    excludes += ['ht\.manifest\..*', 'ht\.project/keys', 'ht\.project/manifest', 'ht\.project/computers',
                 'ht\.project/excludes', 'ht\.project/tags', 'ht\.project/references', 'ht\.tmp\..*']

    f = open(os.path.join(keydir, 'key1.pub'), "r")
    pubkey = f.readlines()[0].strip()
    f.close()

    manifestfile.write(pubkey+"\n")
    message += pubkey+"\n"

    for root, unsorteddirs, unsortedfiles in os.walk(keydir, topdown=True, followlinks=False):
        files = sorted(unsortedfiles)
        for filename in files:
            if filename != 'key1.pub' and re.match(".*\.pub", filename):
                f = open(os.path.join(root, filename), "r")
                filedata = f.readlines()
                f.close()
                pubkey = filedata[0].strip()
                comment = filedata[1].strip()
                manifestfile.write(pubkey+" "+str(comment)+"\n")
                message += pubkey+" "+str(comment)+"\n"

    manifestfile.write("\n")
    message += "\n"

    for root, unsorteddirs, unsortedfiles in os.walk(basedir, topdown=True, followlinks=False):
        if root == basedir:
            root = ""
        else:
            root = os.path.relpath(root, basedir)
        files = sorted(unsortedfiles)
        dirs = sorted(unsorteddirs)
        filenames = [os.path.join(root, x) for x in files]
        for i, f in enumerate(files):
            filename = filenames[i]
            for exclude in excludes:
                if re.match(exclude, f) is not None or re.match(exclude, filename) is not None:
                    break
            else:
                truefilename = os.path.join(basedir, filename)
                hh = sha256file(truefilename)
                manifestfile.write(hh+" "+filename+"\n")
                message += hh+" "+filename+"\n"
                if debug:
                    print "Adding:", hh+" "+filename
        keepdirs = []
        for d in dirs:
            fulldir = os.path.join(root, d)
            for exclude in excludes:
                if re.match(exclude, d) is not None or re.match(exclude, fulldir) is not None:
                    break
            else:
                if d.startswith("ht.task.") or os.path.exists(os.path.join(fulldir, 'ht.config')):
                    if force or (not os.path.exists(os.path.join(fulldir, 'ht.manifest.bz2'))):
                        submanifestfile = bz2.BZ2File(os.path.join(fulldir, 'ht.tmp.manifest.bz2'), 'w')
                        print "Generating manifest:", os.path.join(fulldir, 'ht.manifest.bz2')
                        manifest_dir(fulldir, submanifestfile, os.path.join(fulldir, 'ht.config'), keydir, sk, pk)
                        submanifestfile.close()
                        os.rename(os.path.join(fulldir, 'ht.tmp.manifest.bz2'), os.path.join(fulldir, 'ht.manifest.bz2'))
                    hh = sha256file(os.path.join(fulldir, 'ht.manifest.bz2'))
                    manifestfile.write(hh+" "+fulldir+"/\n")
                    message += hh+" "+fulldir+"/\n"
                    if debug:
                        print "Adding:", hh+" "+fulldir+"/ "
                else:
                    keepdirs += [d]
        unsorteddirs[:] = keepdirs

    #print "===="+message+"===="

    sig = ed25519.signature(message, sk, pk)
    b64sig = base64.b64encode(sig)

    manifestfile.write("\n")
    manifestfile.write(b64sig)
    manifestfile.write("\n")


#def generate_rsa_keys(path,extraargs=[]):
#    args = ['ssh-keygen','-q','-N','','-f']+extraargs+[path]
#    p = Popen(args, stdout=PIPE)
#    stdout = p.communicate()[0]
#    if p.returncode != 0:
#        raise Exception("httk.crypto.crypto: failed to generate keys")
#    return stdout.strip()

# def generate_keys_ssl(key,pubkey):
#     args = ['openssl','genrsa','-out',key,'-passout','pass:','2048']
#     p = Popen(args, stdout=PIPE)
#     stdout = p.communicate()[0]
#     if p.returncode != 0:
#         raise Exception("httk.crypto.crypto: failed to generate keys")
#     args = ['openssl','rsa','-pubout','-out',pubkey,'-in',key]
#     p = Popen(args, stdout=PIPE)
#     stdout += p.communicate()[0]
#     if p.returncode != 0:
#         raise Exception("httk.crypto.crypto: failed to generate keys")
#     return stdout
#
# def sign_message_ssl(msg,key):
#     args = ['openssl','genrsa','-sign','-key',key]
#     p = Popen(args, stdout=PIPE, stdin=msg)
#     stdout = p.communicate()[0]
#     if p.returncode != 0:
#         raise Exception("httk.crypto.crypto: failed to sign message")
#     return stdout
#
# def encrypt_message_ssl(msg,pubkey):
#     args = ['openssl','rsautl','-encrypt','-pubin','-inkey',pubkey]
#     p = Popen(args, stdout=PIPE, stdin=msg)
#     stdout = p.communicate()[0]
#     if p.returncode != 0:
#         raise Exception("httk.crypto.crypto: failed to encrypt message")
#     return stdout
#
# def decrypt_message_sll(msg,key):
#     args = ['openssl','rsautl','-decrypt','-inkey',key]
#     p = Popen(args, stdout=PIPE, stdin=msg)
#     stdout = p.communicate()[0]
#     if p.returncode != 0:
#         raise Exception("httk.crypto.crypto: failed to decrypt message")
#     return stdout


def generate_keys(public_key_path, secret_key_path):
    """
    Generates a public and a private key pair and stores them in respective files
    """
    from . import ed25519
    try:
        secret_key = os.urandom(64)
        #sr = random.SystemRandom()
        #secret_key = sr.getrandbits(512)
    except NotImplementedError:
        raise Exception("crypto.generate_keys: Running on a system without a safe random number generator,cannot create safe cryptographic keys on this system.")
    public_key = ed25519.publickey(secret_key)

    b64secret_key = base64.b64encode(secret_key)
    b64public_key = base64.b64encode(public_key)

    pubfile = IoAdapterFileWriter.use(public_key_path)
    pubfile.file.write(b64public_key)
    pubfile.close()

    secfile = IoAdapterFileWriter.use(secret_key_path)
    secfile.file.write(b64secret_key)
    secfile.close()


def get_crypto_signature(message, secret_key_path):
    from . import ed25519

    ioa = IoAdapterFileReader.use(secret_key_path)
    b64secret_key = ioa.file.read()
    ioa.close()
    secret_key = base64.b64decode(b64secret_key)
    public_key = ed25519.publickey(secret_key)
    signature = ed25519.signature(message, secret_key, public_key)
    b64signature = base64.b64encode(signature)
    return b64signature


def verify_crytpo_signature(signature, message, public_key):
    from . import ed25519

    binsignature = base64.b64decode(signature)
    binpublic_key = base64.b64decode(public_key)
    return ed25519.checkvalid(binsignature, message, binpublic_key)


def verify_crytpo_signature_old(signature, message, public_key_path):
    from . import ed25519

    ioa = IoAdapterFileReader.use(public_key_path)
    b64public_key = ioa.file.read()
    ioa.close()
    binsignature = base64.b64decode(signature)
    public_key = base64.b64decode(b64public_key)
    return ed25519.checkvalid(binsignature, message, public_key)


def main():
    print "Generating keys, this may take some time."
    generate_keys("/tmp/pub.key", "/tmp/priv.key")
    message = "This is my message."
    print "Signing message"
    my_signature = get_crypto_signature(message, "/tmp/priv.key")
    print "Signature is"
    print my_signature
    print "Check if signature is valid"
    result = verify_crytpo_signature(my_signature, message, "/tmp/pub.key")
    print "True message validates", result
    forged_message = "This is not my message."
    result = verify_crytpo_signature(my_signature, forged_message, "/tmp/pub.key")
    print "Forged message validates", result
    print "Finished"

if __name__ == "__main__":
    main()
