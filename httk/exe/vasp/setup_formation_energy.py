import os, glob, shutil

import httk
from httk.iface import vasp_if
from httk.core.htdata import periodictable

# The idea of marking specific ions as high spin (magions) and some for trying both low and high spin (dualmag) comes from
# Anubhav Jain, et al., Computational Materials Science 50 (2011) 2295
magions = ['Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','La','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Th','Pa','U']
dualmag = {'O':['Co'], 'S':['Mn','Fe','Cr','Co']}

def is_dualmagnetic(ion,ionlist):
    for i in range(len(ionlist)):
        if dualmag.has_key(ionlist[i]):
            if ion in dualmag[ionlist[i]]:
                return True
    return False

def magnetization_recurse(basemags,dualmags,high,low):
    if len(dualmags) == 0:
        return [basemags]
    
    index = dualmags.pop()
    basemags[index] = high
    hi_list = magnetization_recurse(list(basemags),list(dualmags),high,low)
    basemags[index] = low
    low_list = magnetization_recurse(list(basemags),list(dualmags),high,low)

    return hi_list + low_list
    

def get_magnetizations(ionlist,high,low):
    basemags = []
    dualmags = []
    count = 0
    for i in range(len(ionlist)):
        if is_dualmagnetic(ionlist[i],ionlist):
            basemags.append(None)
            dualmags.append(i)
        else:
            if ionlist[i] in magions:
                basemags.append(high)
            else:
                basemags.append(low)
                
    return magnetization_recurse(basemags,dualmags,high,low)
    
def get_magmom(symbol):
    return 8

def copy_template(dirtemplate, dirname, templatename):
    template = os.path.join(dirname,"ht.template."+templatename)
    if os.path.exists(template):
        raise Exception("Template dir already exists.")
    shutil.copytree(dirtemplate, template, True)

# def instantiate(dirname,templatename,name,data={}):
#     """
#     Compounds is a list of tuples (name, compound) (it is not a dictionary since order is important to determine the proper name
#     of the template.)
#     Extra is a dictionary of extra information to write into init.py
#     """
#     #if not isinstance(compounds, list): compounds=[('c', compounds)]
# 
#     #compoundsdict={}
#     #for entry in compounds:
#     #    compoundsdict[entry[0]] = entry[1]
#     
#     templatepath = os.path.join(dirname,"ht.template."+templatename)
#     
#     if not os.path.exists(templatepath):
#         raise(Exception("Missing template: template."+templatename))        
# 
#     if glob.glob(os.path.join(dirname,'ht.run.'+name+"*")) != []:
#         raise(Exception("Run already exists: ht.run."+name))
#         
#     rundirname = os.path.join(dirname,'ht.run.'+name+".setup")
#     os.mkdir(rundirname)
#     
#     for filename in os.listdir(templatepath):
#         os.symlink(os.path.join('..','ht.template.'+templatename,filename),os.path.join(rundirname,filename))
#     
#     with open(os.path.join(rundirname,'data'), 'w') as f:
#         #print >>f, "import os"
#         #print >>f, ""
#         print >>f, "name = "+repr(name)
#         print >>f, ""
#         #for c in compounds:
#         #    print >>f, c[0]+" = "+repr(c[1])
#         #print >>f, ""
#         for datum in data:
#             print >>f, datum + " = "+repr(data[datum])
#         print >>f, ""
# 
#     if os.path.exists(os.path.join(rundirname,'setup')):
#         oldpath = os.getcwd()
#         os.chdir(rundirname)        
#         try:
#             execfile('template_init.py', data)
#         finally:
#             os.chdir(oldpath)
# 
# #        print >>f, "if os.path.exists('template_init.py'):"
# #        print >>f, "    execfile('template_init.py')"
# #    with open('run.'+name+'/run.sh', 'w') as f:
# #        f.write("""#!/bin/bash
# #
# #/share/apps/scripts/Python/QuestMaster.py vasp ~/Local.$(cat ./queue)/pvasp5
# #""")
# #    os.chmod('run.'+name+'/run.sh', stat.S_IRWXU | (stat.S_IRWXG & ~stat.S_IWGRP) | (stat.S_IRWXO & ~stat.S_IWOTH))

# def get_potcar(struct):
#     struct = httk.core.Structure.use(struct)
#     vasp_if.structure_to_poscar(os.path.join(basedir,"POSCAR"), struct)
#     vasp_if.write_generic_kpoints_file(os.path.join(basedir,"KPOINTS"))
#    
#     c = PropertiesObject()
#    
#     # Setup POTCAR 
#     ioa = httk.IoAdapterFileWriter(os.path.join(rundir,"POTCAR"))
#     f = ioa.file
#     spieces_counts=[]
#     magmoms=[]
#     for i in range(len(struct.assignments)):
#         assignment = struct.assignments[i]
#         count = struct.counts[i]
#         symbol = periodictable.atomic_symbol(assignment)
#         f.write(vasp_if.get_pseudopotential(symbol))
#         spieces_counts.append(count)
#         magmoms.append(str(count)+"*"+str(get_magmom(symbol)))
# 
#     c.VASP_SPIECES_COUNTS=" ".join(map(str,spieces_counts))
#     c.VASP_MAGMOM=" ".join(map(str,magmoms))
# 
#     ioa.close()

    #vasp_if.write_generic_incar_file(os.path.join(basedir,"INCAR.relax"),struct.assignments,struct.counts,{''})    
    #vasp_if.write_generic_incar_file(os.path.join(rundir,"INCAR.final"),struct.assignments,struct.counts)




# def setup_formation_energy(dirname, struct):
#     struct = httk.core.Structure.use(struct)
#     print "==== Preparing setup for:",struct.formula
#     rundir = os.path.join(dirname,"ht.run.formenrg."+struct.formula+"."+struct.hexhash+".setup")
#     basedir = os.path.join(rundir,"BASE")
#     #if os.path.exists(rundir):
#     #    raise Exception("Path already exists.")
#     httk.mkdir_p(rundir)
#     vasp_if.structure_to_poscar(os.path.join(basedir,"POSCAR"), struct)
#     vasp_if.write_generic_kpoints_file(os.path.join(basedir,"KPOINTS"))
#    
#     c = PropertiesObject()
#    
#     # Setup POTCAR 
#     ioa = httk.IoAdapterFileWriter(os.path.join(rundir,"POTCAR"))
#     f = ioa.file
#     spieces_counts=[]
#     magmoms=[]
#     for i in range(len(struct.assignments)):
#         assignment = struct.assignments[i]
#         count = struct.counts[i]
#         symbol = periodictable.atomic_symbol(assignment)
#         f.write(vasp_if.get_pseudopotential(symbol))
#         spieces_counts.append(count)
#         magmoms.append(str(count)+"*"+str(get_magmom(symbol)))
# 
#     c.VASP_SPIECES_COUNTS=" ".join(map(str,spieces_counts))
#     c.VASP_MAGMOM=" ".join(map(str,magmoms))
# 
#     ioa.close()
# 
#     #vasp_if.write_generic_incar_file(os.path.join(basedir,"INCAR.relax"),struct.assignments,struct.counts,{''})    
#     #vasp_if.write_generic_incar_file(os.path.join(rundir,"INCAR.final"),struct.assignments,struct.counts)

def instantiate_step1(dirname,templatename,name):
    """
    Compounds is a list of tuples (name, compound) (it is not a dictionary since order is important to determine the proper name
    of the template.)
    Extra is a dictionary of extra information to write into init.py
    """
    
    templatepath = os.path.join(dirname,"ht.template."+templatename)
    
    if not os.path.exists(templatepath):
        raise(Exception("Missing template: template."+templatename))        

    if glob.glob(os.path.join(dirname,'ht.run.'+name+"*")) != []:
        raise(Exception("Run already exists: ht.run."+name))
        
    rundirname = os.path.join(dirname,'ht.run.'+name+".setup")
    os.mkdir(rundirname)
    
    for filename in os.listdir(templatepath):
        os.symlink(os.path.join('..','ht.template.'+templatename,filename),os.path.join(rundirname,filename))
    
    return rundirname

def instantiate_step2(dirname,name, data={}):
    """
    Compounds is a list of tuples (name, compound) (it is not a dictionary since order is important to determine the proper name
    of the template.)
    Extra is a dictionary of extra information to write into init.py
    """

    with open(os.path.join(dirname,'data'), 'w') as f:
        #print >>f, "import os"
        #print >>f, ""
        print >>f, "name = "+repr(name)
        print >>f, ""
        #for c in compounds:
        #    print >>f, c[0]+" = "+repr(c[1])
        #print >>f, ""
        for datum in data:
            print >>f, datum + " = "+repr(data[datum])
        print >>f, ""
    
    if os.path.exists(os.path.join(dirname,'setup')):
        oldpath = os.getcwd()
        os.chdir(dirname)        
        try:
            execfile('setup')
        finally:
            os.chdir(oldpath)

#        print >>f, "if os.path.exists('template_init.py'):"
#        print >>f, "    execfile('template_init.py')"
#    with open('run.'+name+'/run.sh', 'w') as f:
#        f.write("""#!/bin/bash
#
#/share/apps/scripts/Python/QuestMaster.py vasp ~/Local.$(cat ./queue)/pvasp5
#""")
#    os.chmod('run.'+name+'/run.sh', stat.S_IRWXU | (stat.S_IRWXG & ~stat.S_IWGRP) | (stat.S_IRWXO & ~stat.S_IWOTH))
