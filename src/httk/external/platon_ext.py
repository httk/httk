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

from httk.core import citation
citation.add_ext_citation('Platon', "A. L. Spek, Utrecht University, Padualaan 8, 3584 CH Utrecht, The Netherlands.")

import os, StringIO, tempfile

from httk import config
from command import Command
import httk

platon_path = None

def ensure_has_platon():
    if platon_path is None or platon_path == "":
        raise Exception("httk.external.platon imported with no access to platon binary")

try:   
    platon_path = config.get('paths', 'platon')
except Exception:
    pass

def platon(cwd, args, timeout=60):
    ensure_has_platon()

    #p = subprocess.Popen([platon_path]+args, stdout=subprocess.PIPE, 
    #                                   stderr=subprocess.PIPE, cwd=cwd)
    #out, err = p.communicate()
    #print "COMMAND PLATON"
    #raise Exception("PLATON")
    #print "EXECUTING PLATON",platon_path,args
    out, err, completed = Command(platon_path, args, cwd=cwd).run(timeout)
    #print "COMMAND PLATON END", out, err, completed, cwd
    return out, err, completed


def addsym(struct):    
    path = "/tmp/platon/atom.spf"
    httk.basic.mkdir_p("/tmp/platon")
    f = False
    try:
        f = open(path, 'w')
        httk.iface.platon_if.structure_to_platon(f, struct, ["NOMOVE OFF"], ["CALC ADDSYM SHELX", "END"])
    finally:
        if f:
            f.close()
    if os.path.exists("/tmp/platon/atom.res"):
        os.unlink("/tmp/platon/atom.res")
    out, err = platon("/tmp/platon", ["atom.spf"])

    f = False
    try:
        f = open("/tmp/platon/atom.res")
        lines = f.readlines()
        lines[-1] = "STIDY"
    finally:
        if f:
            f.close()

    f = False
    try:
        f = open("/tmp/platon/atom.res", "w")
        f.writelines(lines)
    finally:
        if f:
            f.close()

    out, err = platon("/tmp/platon", ["atom.res"])

    f = False
    try:
        f = open("/tmp/platon/atom.sty")
        sgtidystruct = httk.iface.platon_if.platon_styin_to_sgstruct(f)
    finally:
        if f:
            f.close()
            
    return sgtidystruct


def structure_addsym_and_tidy(struct):    
    #TODO: use mktmpdir here
    httk.basic.mkdir_p("/tmp/platon")
    f = False
    try:
        f = open("/tmp/platon/atom.spf", 'w')
        httk.iface.platon_if.structure_to_platon(f, struct, ["NOMOVE OFF"], [])
    finally:
        if f:
            f.close()
    if os.path.exists("/tmp/platon/atom.res"):
        os.unlink("/tmp/platon/atom.res")
    #out, err = platon("/tmp/platon",["atom.spf"])
    out, err = platon("/tmp/platon", ["-n", "atom.spf"])
    if err != "":
        print err
 
    #os.remove("/tmp/platon/atom.spf")

    f = False
    try:
        f = open("/tmp/platon/atom.res")
        lines = f.readlines()
        lines[-1] = "STIDY"
    finally:
        if f:
            f.close()

    f = False
    try:
        f = open("/tmp/platon/atom.res", "w")
        f.writelines(lines)
    finally:
        if f:
            f.close()
    if os.path.exists("/tmp/platon/atom.sty"):
        os.unlink("/tmp/platon/atom.sty")
    out, err = platon("/tmp/platon", ["atom.res"])
    if err != "":
        print err
    out, err = platon("/tmp/platon", ["-Y", "atom.sty"])
    if err != "":
        print err

    sgtidystruct = httk.iface.platon_if.platon_styout_to_sgstruct(StringIO(out))
    sgtidystruct.nonequiv.tags['platon_sg'] = sgtidystruct.hall_symbol
    
    return sgtidystruct.to_structure()


def addsym_spacegroup(struct):    
    path = "/tmp/platon/atom.spf"
    httk.basic.mkdir_p("/tmp/platon")
    f = False
    try:
        f = open(path, 'w')
        httk.iface.platon_if.structure_to_platon(f, struct, ["NOMOVE OFF"], ["CALC ADDSYM", "END"])
    finally:
        if f:
            f.close()
    result, err = platon("/tmp/platon", ["atom.spf"])
    
    def grab(results, match):
        results[0] = match.group(1)
    out = httk.basic.micro_pyawk(StringIO(result), [['^Space Group ([^ ]+) ', None, grab]])
    try:
        return out[0]
    except AttributeError:
        return None


def structure_tidy_old(struct):    
    #TODO: use mktmpdir here
    httk.basic.mkdir_p("/tmp/platon")
    f = False
    try:
        f = open("/tmp/platon/atom.spf", 'w')
        httk.iface.platon_if.structure_to_platon(f, struct, ["NOMOVE OFF"], ["CALC ADDSYM EXACT SHELX 0.001 0.001 0.001 0.001", "END"])
        #structure_to_platon(f,struct,["NOMOVE OFF"],[])
    finally:
        if f:
            f.close()
    if os.path.exists("/tmp/platon/atom.res"):
        os.unlink("/tmp/platon/atom.res")
    out, err = platon("/tmp/platon", ["atom.spf"])
    #out, err = platon("/tmp/platon",["-n","atom.spf"])
    if err != "":
        print err
 
    #os.remove("/tmp/platon/atom.spf")

    f = False
    try:
        f = open("/tmp/platon/atom.res")
        lines = f.readlines()
        lines[-1] = "STIDY"
    finally:
        if f:
            f.close()

    f = False
    try:
        f = open("/tmp/platon/atom.res", "w")
        f.writelines(lines)
    finally:
        if f:
            f.close()
    if os.path.exists("/tmp/platon/atom.sty"):
        os.unlink("/tmp/platon/atom.sty")
    out, err = platon("/tmp/platon", ["atom.res"])
    if err != "":
        print err
    out, err = platon("/tmp/platon", ["-Y", "atom.sty"])
    if err != "":
        print err

    sgtidystruct = httk.iface.platon_if.platon_styout_to_sgstruct(StringIO(out))
    sgtidystruct.nonequiv.tags['platon_sg'] = sgtidystruct.hall_symbol
    
    return sgtidystruct.to_structure()


def structure_to_sgstructure(struct):
    #TODO: use mktmpdir here
    
    httk.basic.mkdir_p("/tmp/platon")
    f = False
    try:
        f = open("/tmp/platon/atom.spf", 'w')
        #structure_to_platon(f,struct,["NOMOVE OFF"],["CALC SHELX","END"])
        httk.iface.platon_if.structure_to_platon(f, struct, ["NOMOVE OFF"], ["CALC ADDSYM EXACT SHELX 0.001 0.001 0.001 0.001", "END"])
        #structure_to_platon(f,struct,["NOMOVE OFF"],[])
    finally:
        if f:
            f.close()
    if os.path.exists("/tmp/platon/atom.res"):
        os.unlink("/tmp/platon/atom.res")
    out, err = platon("/tmp/platon", ["atom.spf"])
    #out, err = platon("/tmp/platon",["-n","atom.spf"])
    #os.remove("/tmp/platon/atom.spf")

    f = False
    try:
        f = open("/tmp/platon/atom.res")
        lines = f.readlines()
        lines[-1] = "STIDY"
    finally:
        if f:
            f.close()

    f = False
    try:
        f = open("/tmp/platon/atom.res", "w")
        f.writelines(lines)
    finally:
        if f:
            f.close()

    if os.path.exists("/tmp/platon/atom.sty"):
        os.unlink("/tmp/platon/atom.sty")

    out, err = platon("/tmp/platon", ["atom.res"])
    out, err = platon("/tmp/platon", ["-Y", "atom.sty"])

    sgtidystruct = httk.iface.platon_if.httk.iface.platon_if.platon_styout_to_sgstruct(StringIO(out))
    sgtidystruct.refs = struct.refs
    sgtidystruct.tags = struct.tags
    
    return sgtidystruct
    
    
def cif_to_sgstructure(ioa):
    ioa = httk.IoAdapterFileReader.use(ioa)
    fin = ioa.file 
        
    #TODO: use mktmpdir here
    httk.basic.mkdir_p("/tmp/platon")
    f = False
    try:
        f = open("/tmp/platon/atom.cif", 'w')
        for line in fin:
            f.write(line)
    finally:
        if f:
            f.close()
    out, err = platon("/tmp/platon", ["-g", "atom.cif"])
 
    #os.remove("/tmp/platon/atom.spf")

    f = False
    try:
        f = open("/tmp/platon/atom.res")
        lines = f.readlines()
        lines[-1] = "STIDY"
    finally:
        if f:
            f.close()

    f = False
    try:
        f = open("/tmp/platon/atom.res", "w")
        f.writelines(lines)
    finally:
        if f:
            f.close()

    out, err = platon("/tmp/platon", ["atom.res"])

    f = False
    try:
        f = open("/tmp/platon/atom.sty")
        sgtidystruct = httk.iface.platon_if.platon_styin_to_sgstruct(f)
    finally:
        if f:
            f.close()

    ioa.close()    
    
    return sgtidystruct
    

# def cif_to_structure_broken(ioa):
#     ioa = httk.IoAdapterFileReader.use(ioa)
#     fin=ioa.file 
#         
#     #TODO: use mktmpdir here
#     httk.utils.mkdir_p("/tmp/platon")
#     f = False
#     try:
#         f = open("/tmp/platon/atom.cif",'w')
#         for line in fin:
#             f.write(line)
#     finally:
#         if f: f.close()
#     out, err = platon("/tmp/platon",["-g","atom.cif"])
#  
#     #os.remove("/tmp/platon/atom.spf")
# 
#     f = False
#     try:
#         f = open("/tmp/platon/atom.lis")
#         struct = httk.iface.platon_if.platon_lis_to_struct(f)
#     finally:
#         if f: f.close()
# 
#     ioa.close()    
#     
#     return struct
# def structure_tidy(struct):    
#     #TODO: use mktmpdir here
#     tmpdir = tempfile.mkdtemp(suffix='httk_platon')
#     f = False
#     try:
#         f = open(os.path.join(tmpdir,"atom.spf"),'w')
#         httk.iface.platon_if.structure_to_platon(f,struct,[],["STIDY","END"])
#         #structure_to_platon(f,struct,["NOMOVE OFF"],[])
#     finally:
#         if f: f.close()
#     if os.path.exists(os.path.join(tmpdir,"atom.res")):
#         os.unlink(os.path.join(tmpdir,"atom.res"))
#     out, err = platon(tmpdir,["atom.spf"])
#     #out, err = platon("/tmp/platon",["-n","atom.spf"])
#     if err != "":
#         print err
#  
#     if os.path.exists("/tmp/platon/atom.sty"):
#         os.unlink("/tmp/platon/atom.sty")
#     out, err = platon("/tmp/platon",["atom.res"])
#     if err != "":
#         print err
#     out, err = platon("/tmp/platon",["-Y","atom.sty"])
#     if err != "":
#         print err
# 
#     sgtidystruct = httk.iface.platon_if.platon_styout_to_sgstruct(StringIO(out))
#     sgtidystruct.nonequiv.tags['platon_sg'] = sgtidystruct.hall_symbol
#     
#     return sgtidystruct.to_structure()
def structure_tidy(struct):
    #TODO: use mktmpdir here
    tmpdir = tempfile.mkdtemp(prefix='ht.tmp.platon_')
    f = False
    try:
        f = open(os.path.join(tmpdir, "atom.sty"), 'w')
        httk.iface.platon_if.platon_sites_to_styin(f, struct.rc_sites, struct.rc_cell)
        #structure_to_platon(f,struct,["NOMOVE OFF"],[])
    finally:
        if f:
            f.close()

    #f = open(os.path.join(tmpdir,"atom.sty"))
    #print "PLATON INPUT:",f.read()
    #f.close()
    
    out, err, completed = platon(tmpdir, ["-Y", "atom.sty"])

    # Clean up
    try:
        os.unlink(os.path.join(tmpdir, 'atom.lis'))
    except (IOError, OSError):
        pass
    try:
        os.unlink(os.path.join(tmpdir, 'atom.sty'))
    except (IOError, OSError):
        pass
    try:
        os.rmdir(tmpdir)
    except (IOError, OSError):
        pass
    
    if err != "":
        print err
    elif completed is None:
        #print "OUT:",out
        print "Platon did not run to completion."
        return None

    tidystruct = httk.iface.platon_if.platon_styout_to_structure(StringIO.StringIO(out), based_on_struct=struct)

    return tidystruct


