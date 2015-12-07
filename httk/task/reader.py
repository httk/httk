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
import glob, os, datetime, hashlib, ConfigParser, re, base64, bz2, sys
from httk.core.crypto import manifest_dir, verify_crytpo_signature, read_keys
from httk.core import Computation, ComputationProject, Code, IoAdapterFileReader, Signature, SignatureKey


def reader(projectpath, inpath, excludes=None, default_description=None, project_counter=0, force_remake_manifests=False):
    """
    Read and yield all tasks from the project in path
    """

    keydir = os.path.join(projectpath, 'ht.project', 'keys')    
    pk = None
    sk = None
    
    for root, dirs, files in os.walk(inpath, topdown=True):
        walkdirs = list(dirs)
        for dir in walkdirs:
            if dir.startswith('ht.task.'):
                dirs.remove(dir)
                if dir.endswith('.finished'):
                    dirpath = os.path.join(root, dir)
                    filepath = os.path.join(dirpath, 'ht.manifest.bz2')
                    runs = glob.glob(os.path.join(dirpath, "ht.run.*"))
                    runs = sorted(runs, key=lambda d: datetime.datetime.strptime(os.path.basename(d)[7:], "%Y-%m-%d_%H.%M.%S"))
                    if len(runs) < 1:
                        continue
                    rundir = runs[-1]
                    dates = [datetime.datetime.strptime(os.path.basename(run)[7:], "%Y-%m-%d_%H.%M.%S") for run in runs]
                    now = datetime.datetime.now()
                    if os.path.exists(os.path.join(dirpath, 'ht_steps')):
                        f = open(os.path.join(dirpath, 'ht_steps'))
                        ht_steps_file = f.readlines()
                        f.close()
                        # Handle runs I did before policy of code name and version in ht_steps script...
                        codename = ht_steps_file[2][1:].strip()
                        codeversion = ht_steps_file[3][1:].strip()
                        code = Code(codename, codeversion)
                    else:
                        code = Code('unknown', '0')
                    if os.path.exists(os.path.join(dirpath, 'ht.config')):
                        configparser = ConfigParser.ConfigParser()
                        configparser.read(os.path.join(dirpath, 'ht.config'))
                        if configparser.has_option('main', 'description'):
                            description = configparser.get('main', 'description')
                        else:
                            description = default_description  
                    else:
                        description = default_description
                    if not os.path.exists(os.path.join(dirpath, 'ht.manifest.bz2')) or force_remake_manifests:
                        if pk is None:
                            sk, pk = read_keys(keydir)
                        sys.stderr.write("Warning: generating manifest for "+str(dirpath)+", this takes some time.\n")
                        manifestfile = bz2.BZ2File(os.path.join(dirpath, 'ht.tmp.manifest.bz2'), 'w')
                        manifest_dir(dirpath, manifestfile, os.path.join(dirpath, 'ht.config'), keydir, sk, pk, force=force_remake_manifests)
                        manifestfile.close()
                        os.rename(os.path.join(dirpath, 'ht.tmp.manifest.bz2'), os.path.join(dirpath, 'ht.manifest.bz2'))

                    (manifest_hash, signatures, project_key, keys) = read_manifest(os.path.join(dirpath, 'ht.manifest.bz2'), verify_signature=False)
                    
                    #(input_manifest, input_hexhash) = check_or_generate_manifest_for_dir(code.name,code.version, path, excluderuns, None, False)
                    # Relpath is this tasks path relative to the *project* path.
                    relpath = os.path.relpath(root, projectpath)
                    computation = Computation.create(computation_date=dates[-1], added_date=now, description=description, 
                                                     code=code, manifest_hash=manifest_hash, 
                                                     signatures=signatures, keys=keys, relpath=relpath, project_counter=project_counter)

                    yield rundir, computation


def submit_reader(projectpath, default_description=None, excludes=None, project=None, project_counter=0):
    """
    Read and yield all tasks from the project in path
    
    For 'submitted' projects that already have manifests and should not be altered in any way.
    """
    for root, dirs, files in os.walk(projectpath, topdown=True):
        walkdirs = list(dirs)
        for file in files:
            if file == 'ht.manifest.bz2':
                dirs[:] = []
                if root.endswith('.finished'):
                    filepath = os.path.join(root, file)
                    dirpath = root
                    runs = glob.glob(os.path.join(dirpath, "ht.run.*"))
                    runs = sorted(runs, key=lambda d: datetime.datetime.strptime(os.path.basename(d)[7:], "%Y-%m-%d_%H.%M.%S"))
                    if len(runs) >= 1:
                        rundir = runs[-1]
                        dates = [datetime.datetime.strptime(os.path.basename(run)[7:], "%Y-%m-%d_%H.%M.%S") for run in runs]
                    now = datetime.datetime.now()
                    if os.path.exists(os.path.join(dirpath, 'ht_steps')):
                        f = open(os.path.join(dirpath, 'ht_steps'))
                        ht_steps_file = f.readlines()
                        f.close()
                        # Handle runs I did before policy of code name and version in ht_steps script...
                        if ht_steps_file[2].strip() == "# PREINIT run. Runs two relaxations, without being overly concerned with":
                            code = Code('httk formation energy relaxation runs', '0.9')
                        else:
                            codename = ht_steps_file[2][1:].strip()
                            codeversion = ht_steps_file[3][1:].strip()
                            code = Code(codename, codeversion)
                    else:
                        code = Code('unknown', '0')
                    if os.path.exists(os.path.join(dirpath, 'ht.config')):
                        configparser = ConfigParser.ConfigParser()
                        configparser.read(os.path.join(dirpath, 'ht.config'))
                        if configparser.has_option('main', 'description'):
                            description = configparser.get('main', 'description')
                        else:
                            description = default_description  
                    else:
                        description = default_description                        
                    (manifest_hash, signatures, project_key, keys) = read_manifest(filepath, verify_signature=False)
                    relpath = os.path.relpath(root, projectpath)
                    computation = Computation.create(computation_date=dates[-1], added_date=now, description=description, 
                                                     code=code, manifest_hash=manifest_hash, 
                                                     signatures=signatures, keys=keys, relpath=relpath, project_counter=project_counter)
                    if project is not None:
                        computation.add_project(project)

                    yield dirpath, computation


def read_manifest(ioa, verify_signature=True):
    hashlib.sha1()
    ioa = IoAdapterFileReader.use(ioa)
    lines = ioa.file.readlines()
    ioa.close()

    message = "".join(lines[:-2]) 
    s = hashlib.sha256(message) 
    hexhash = s.hexdigest()

    keys = []
    b64projkey = lines[0].strip()
    projectkey = SignatureKey.create(b64projkey, "project key")
    keys += [projectkey]
    for line in lines[1:]:
        line = line.strip()
        if line == '':
            break
        keystr, description = line.split(" ", 1)
        key = SignatureKey.create(keystr.strip(), description.strip())
        keys += [key]
    b64sigstr = lines[-1]
    signature = Signature.create(b64sigstr, projectkey)
    signatures = [signature]
    if verify_signature:
        #print "Verifying manifest"
        if not verify_crytpo_signature(b64sigstr, message, b64projkey):
            raise Exception("Project manifest did not verify.")
        #print "Manifest verified ok"
   
    return (hexhash, signatures, projectkey, keys) 
