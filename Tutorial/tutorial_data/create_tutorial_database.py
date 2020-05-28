#!/usr/bin/env python
# This is an example program using the High-Throughput toolkit (httk)
# This program adds two (geometrically identical) structures to an sqlite database
# 
import sys, os.path, inspect, datetime, argparse, os, errno

# Workaround to allow this program to be run in a subdirectory of the httk directory even if the paths are not setup correctly.
try:
    import httk
except Exception:
    _realpath = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
    sys.path.insert(1, os.path.join(_realpath, '../..'))
    import httk

from httk.atomistic import *
import httk.db
import httk.httkio
import httk.iface
import httk.atomistic.vis

#sys.setrecursionlimit(100)


def main():
    parser = argparse.ArgumentParser(description="Creates the tutorial sqlite database file")
    parser.add_argument('-debug', action='store_true')
    parser.add_argument('file', metavar='run', nargs='*', help='filenames or directories to import')
    args = parser.parse_args()    

    debug = args.debug
    #debug = True
    process_with_isotropy = True
    process_with_tidy = True

    if process_with_isotropy:
        import httk.external.isotropy_ext

    try:
        os.remove('tutorial.sqlite')
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

    backend = httk.db.backend.Sqlite('tutorial.sqlite')
    store = httk.db.store.SqlStore(backend)

    # This is good practice if you are going to add several things to the database, nothing is written to the database until 'commit' is called.
    # (Special case: if the database is completely newly created, some database engines commit data)
    store.delay_commit()

    codeobj = httk.Code.create("create_tutorial_database", '1.0', refs=[httk.citation.httk_reference_main])
    store.save(codeobj)  
    print("==== Name of this code:", codeobj.name)

    today = datetime.datetime.today().isoformat()
    print("==== Db import program started: "+today)
    
    if len(args.file) == 0:
        files = [os.path.join(httk.httk_root, 'Tutorial/tutorial_data')]
    else:
        files = args.file

    argcount = len(files)

    seen = {}
    for filek in range(argcount):
        f = files[filek]
            
        if not os.path.exists(f):
            print("File or dir "+f+" not found.")
            continue
        if os.path.isdir(f):
            filelist = []
            dirname = os.path.dirname(f)
            for root, dirs, files in os.walk(f):
                for file in files:
                    if file.endswith(".cif") or file.endswith(".vasp"):
                        filelist += [os.path.join(root, file)]
                # Make sure we always generate the same manifest
                        filelist = sorted(filelist)
        else:
            dirname = os.path.dirname(f)
            filelist = [f]

        for i in range(len(filelist)):
            filename = filelist[i]
            print("Filename:"+filename)
            # Uncomment for better control in how to load structures
            #if filename.endswith(".cif"):
            #    struct = httk.httkio.cif_to_struct(filename,backends=['cif2cell_reduce'])
            #elif filename.endswith(".vasp"):
            #    struct = httk.iface.vasp_if.poscar_to_structure(filename)
            struct = httk.load(filename).clean()
            print("The formula is:", struct.formula+" ("+struct.anonymous_formula+")")
            print("Volume", float(struct.uc_volume))
            print("Tags:", [str(struct.get_tag(x)) for x in struct.get_tags()])
            print("Refs:", [str(x) for x in struct.get_refs()])

            if process_with_isotropy:
                try:
                    newstruct = httk.external.isotropy_ext.struct_process_with_isotropy(struct).clean()
                    newstruct.add_tag("isotropy/findsym", "done")
                    struct = newstruct
                except Exception as e:
                    print("Isotropy failed with:"+str(e))
                    struct.add_tag("isotropy", "failed")
                    if debug:
                        raise

            if process_with_tidy:
                try:
                    newstruct = struct.tidy()
                    newstruct.add_tag("structure_tidy", "done")
                    struct = newstruct
                except Exception as e:
                    print("Structure tidy failed with:"+str(e))
                    struct.add_tag("structure_tidy", "failed")
                    if debug:
                        raise
            
            store.save(struct)            
            compound = Compound.create(base_on_structure=struct)
            store.save(compound)

            cs = CompoundStructure.create(compound, struct)
            store.save(cs)
            store.commit()            
        
    print("==== Committing changes to database.")
    store.commit()
    print("==== Commit complete.")
    
if __name__ == "__main__":
    main()




