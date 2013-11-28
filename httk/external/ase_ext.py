# 
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2013 Rickard Armiento
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

import os

from httk.core import citation
citation.add_ext_citation('Atomic Simulation Environment (ASE)', "S. R. Bahn, K. W. Jacobsen")

from httk import config
from command import Command
from subimport import submodule_import_external
import httk
try:   
    ase_path=config.get('paths', 'ase')
except Exception:
    ase_path = None

if ase_path != None:    
    ase = submodule_import_external(os.path.join(ase_path),'ase')
else:
    try:
        external=config.get('general', 'allow_system_libs')
    except Exception:
        external = 'yes'
    if external == 'yes':
        import ase
    else:
        raise Exception("httk.external.ase_ext imported, but could not access ase.")
    
import ase.io
from ase.lattice import spacegroup
from ase.lattice.spacegroup import crystal
from ase.atoms import Atoms

def spacegroup_size(symbol):
    sg = spacegroup.Spacegroup(symbol)
    return len(sg.get_symop())
    
def primitive_from_conventional_cell(atoms, spacegroup=1, setting=1):
    """Returns primitive cell given an Atoms object for a conventional
    cell and it's spacegroup.
    
    Kindly provided by Jesper Friis, 
      https://listserv.fysik.dtu.dk/pipermail/ase-users/2011-January/000911.html
    """    
    from ase.lattice.spacegroup import Spacegroup
    from ase.utils.geometry  import cut
    sg = Spacegroup(spacegroup, setting)
    prim_cell = sg.scaled_primitive_cell  # Check if we need to transpose
    return cut(atoms, a=prim_cell[0], b=prim_cell[1], c=prim_cell[2])    
    
def structure_to_ase_atoms(struct):
    symbols, scaled_positions = httk.iface.ase_if.structure_to_symbols_and_scaled_positions(struct)
    cell = struct.cell.to_floats()
    
    atoms = Atoms( symbols=symbols,
                      cell=cell,
                      scaled_positions=scaled_positions,
                      pbc=True)

    return atoms


def structure_to_p1structure(sgstruct, primitive=False):
    #print "SGSTRUCTURE TO STRUCTURE:",sgstruct.nonequiv.assignments,sgstruct.nonequiv.coordgroups.to_floats(),sgstruct.nonequiv.cell.to_floats()
    
    symbols, scaled_positions = httk.iface.ase_if.structure_to_symbols_and_scaled_positions(sgstruct)    
    #print "HERE:",symbols,scaled_positions.to_floats(),primitive
    #spacegroup = sgstruct.hm_symbol.split(":")[0]
    #setting = sgstruct.setting
    spacegroup, setting = sgstruct.spacegroup_number_and_setting
    ase_cryst = crystal(symbols, scaled_positions, spacegroup, setting=setting, 
                        cellpar=[sgstruct.a, sgstruct.b, sgstruct.c, 
                                 sgstruct.alpha, sgstruct.beta, sgstruct.gamma])
    if primitive:
        ase_cryst = primitive_from_conventional_cell(ase_cryst, spacegroup=sgstruct.spacegroup)
    newstruct = httk.iface.ase_if.ase_atoms_to_structure(ase_cryst,hall_symbol='P 1')
    newstruct.tags = sgstruct.tags
    newstruct.refs = sgstruct.refs
    #print "SGSTRUCTURE TO STRUCTURE NEW:",newstruct.assignments,newstruct.coordgroups.to_floats(),newstruct.cell.to_floats()
    return newstruct.round()

def ase_read(f):
    ioa = httk.IoAdapterFilename.use(f)
    atoms = ase.io.read(ioa.filename)
    ioa.close()
    atoms = primitive_from_conventional_cell(atoms)
    struct = httk.iface.ase_if.ase_atoms_to_structure(atoms)
    return struct

