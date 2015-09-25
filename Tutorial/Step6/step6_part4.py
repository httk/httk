#!/usr/bin/env python

import os, errno
import httk, httk.iface.vasp_if
import httk.db
from httk.atomistic import UnitcellStructure
import httk.task

try:
    os.remove('example.sqlite')
except OSError as e:
    if e.errno != errno.ENOENT:
        raise

class TotalEnergyResult(httk.Result):
    @httk.httk_typed_init({'computation':httk.Computation, 'structure':UnitcellStructure, 'total_energy':float})
    def __init__(self, computation, structure, total_energy):
        self.computation = computation
        self.structure = structure
        self.total_energy = total_energy

backend = httk.db.backend.Sqlite('example.sqlite')
store = httk.db.store.SqlStore(backend)

reader = httk.task.reader('./','Runs/','Normal VASP total energy run')

print "Storing results (please note that first store call will take some time, since the database is created)"
for rundir, computation in reader:
    struct = httk.load(os.path.join(rundir,"CONTCAR"))
    print "Reading outcar:",struct.formula
    outcar = httk.iface.vasp_if.read_outcar(os.path.join(rundir,"OUTCAR.cleaned.relax-final"))            
    total_energy_result = TotalEnergyResult(computation, struct, float(outcar.final_energy))
    store.save(total_energy_result) 
    
store.commit()
