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

import os

from httk.core import citation
from httk.core.basic import is_sequence
citation.add_ext_citation('Atomic Simulation Environment (ASE)', "S. R. Bahn, K. W. Jacobsen")
import httk.atomistic.data
from httk.core.httkobject import HttkPlugin, HttkPluginWrapper
from httk.atomistic import Cell

from httk import config
from httk.atomistic import Structure, UnitcellSites
import httk.iface 
from subimport import submodule_import_external
try:   
    ase_path=config.get('paths', 'ase')
except Exception:
    ase_path = None

if ase_path == "False":
    raise Exception("httk.external.ase_glue: module ase_glue imported, but ase is disabled in configuration file.")

if ase_path != None:    
    submodule_import_external(os.path.join(ase_path),'ase')
else:
    try:
        external=config.get('general', 'allow_system_libs')
    except Exception:
        external = 'yes'
    #if external == 'yes':
    #    import ase
    #else:
    #    raise Exception("httk.external.ase_glue: module ase_glue imported, but no ase configured, and package ase not found in the environment.")

from httk.iface.ase_if import *

try:
    import ase
except ImportError:
    raise ImportError("httk.external.ase_glue imported without access to the ase python library.")
import ase.io
import ase.utils.geometry
from ase.lattice.spacegroup import crystal
from ase.atoms import Atoms
from ase import version

ase_major_version = version.version.split('.')[0]
ase_minor_version = version.version.split('.')[1]

def primitive_from_conventional_cell(atoms, spacegroup=1, setting=1):
    """Returns primitive cell given an Atoms object for a conventional
    cell and it's spacegroup.
    
    Code snippet kindly posted by Jesper Friis, 
      https://listserv.fysik.dtu.dk/pipermail/ase-users/2011-January/000911.html
    """    
    sg = spacegroup.Spacegroup(spacegroup, setting)
    prim_cell = sg.scaled_primitive_cell  # Check if we need to transpose
    return ase.utils.geometry.cut(atoms, a=prim_cell[0], b=prim_cell[1], c=prim_cell[2])    
    
def structure_to_ase_atoms(struct):

    struct = Structure.use(struct)

    if struct.has_uc_repr:    
        symbollist, scaled_positions = httk.iface.ase_if.uc_structure_to_symbols_and_scaled_positions(struct)
        cell = struct.uc_basis.to_floats()
        symbols=[]
        for s in symbollist:
            if is_sequence(s):
                if len(s)==1:
                    symbols+=[s[0]]
                else:
                    symbols+=[str(s)]
            else:
                symbols+=[s]
                    
        atoms = Atoms( symbols=symbols,
                          cell=cell,
                          scaled_positions=scaled_positions,
                          pbc=True)

    elif struct.has_rc_repr:
        symbollist, scaled_positions = httk.iface.ase_if.rc_structure_to_symbols_and_scaled_positions(struct)    
        symbols=[]
        for s in symbollist:
            if is_sequence(s):
                if len(s)==1:
                    symbols+=[s[0]]
                else:
                    symbols+=[str(s)]
            else:
                symbols+=[s]
        
        spacegroup, setting = struct.spacegroup_number_and_setting
        atoms = crystal(symbols, scaled_positions, spacegroup, setting=setting, 
                        cellpar=[float(struct.rc_a), float(struct.rc_b), float(struct.rc_c), 
                                 float(struct.rc_alpha), float(struct.rc_beta), float(struct.rc_gamma)])
    else:
        raise Exception("ase_glue.structure_to_ase_atoms: structure has neither primcell, nor representative, representation.")
    
    return atoms

def ase_read_structure(f):
    ioa = httk.IoAdapterFilename.use(f)
    atoms = ase.io.read(ioa.filename)
    ioa.close()
    #atoms = primitive_from_conventional_cell(atoms)
    struct = ase_atoms_to_structure(atoms)
    return struct

def coordgroups_reduced_rc_to_unitcellsites(coordgroups,basis,hall_symbol,reduce=False):
    # Just fake representative assignments for the coordgroups
    assignments = range(1,len(coordgroups)+1)
    struct = Structure.create(rc_cell=basis, assignments=assignments, rc_reduced_coordgroups=coordgroups, hall_symbol=hall_symbol)
    rescale = 1

    atoms = structure_to_ase_atoms(struct)
    if reduce:
        beforevol = FracScalar.create(atoms.get_volume())
        spacegroup, setting = httk.atomistic.data.spacegroups.spacegroup_get_number_and_setting(hall_symbol)
        atoms = primitive_from_conventional_cell(atoms,spacegroup,setting)
        aftervol = FracScalar.create(atoms.get_volume())
        rescale = (rescale*aftervol/beforevol).simplify()

    atomic_symbols = atoms.get_chemical_symbols()
    coords = atoms.get_scaled_positions()
    cell = atoms.get_cell()
    sites = UnitcellSites.create(cell=cell, occupancies=atomic_symbols, reduced_coords=coords, periodicity = atoms.pbc)
    cell = Cell(basis=cell)
    
    return sites, cell

def ase_atoms_to_structure(atoms,hall_symbol):
    #occupancies = [periodictable.atomic_number(x) for x in atoms.get_chemical_symbols()]
    atomic_symbols = atoms.get_chemical_symbols()
    #counts = [1]*len(assignments)
    coords = atoms.get_scaled_positions()
    cell = atoms.get_cell()
    if hall_symbol == None:
        struct = Structure.create(uc_basis=cell, uc_occupancies=atomic_symbols, uc_reduced_occupationscoords=coords, periodicity = atoms.pbc)
    else:
        struct = Structure.create(rc_basis=cell, rc_occupancies=atomic_symbols, rc_reduced_occupationscoords=coords, periodicity = atoms.pbc, hall_symbol=hall_symbol)
    return struct


def ase_write_struct(struct,ioa,format=None):
    ioa = IoAdapterFileWriter.use(ioa)
    aseatoms = structure_to_ase_atoms(struct)
    ase.io.write(ioa.file,aseatoms,format=format)

class StructureAsePlugin(HttkPlugin):

    name = 'ase'
            
    def plugin_init(self, struct):
        self.struct = struct

    def to_Atoms(self):
        return structure_to_ase_atoms(self.struct)

    @classmethod
    def from_Atoms(cls,atoms):
        return ase_atoms_to_structure(atoms,None)

Structure.ase = HttkPluginWrapper(StructureAsePlugin)

# def structure_to_p1structure(sgstruct, primitive=False):
#     #print "SGSTRUCTURE TO STRUCTURE:",sgstruct.nonequiv.assignments,sgstruct.nonequiv.coordgroups.to_floats(),sgstruct.nonequiv.cell.to_floats()
#     
#     symbols, scaled_positions = httk.iface.ase_if.rc_structure_to_symbols_and_scaled_positions(sgstruct)    
#     #print "HERE:",symbols,scaled_positions.to_floats(),primitive
#     #spacegroup = sgstruct.hm_symbol.split(":")[0]
#     #setting = sgstruct.setting
#     spacegroup, setting = sgstruct.spacegroup_number_and_setting
#     ase_cryst = crystal(symbols, scaled_positions, spacegroup, setting=setting, 
#                         cellpar=[sgstruct.a, sgstruct.b, sgstruct.c, 
#                                  sgstruct.alpha, sgstruct.beta, sgstruct.gamma])
#     if primitive:
#         ase_cryst = primitive_from_conventional_cell(ase_cryst, spacegroup=sgstruct.spacegroup)
#     newstruct = httk.iface.ase_if.ase_atoms_to_structure(ase_cryst,hall_symbol='P 1')
#     newstruct.tags = sgstruct.tags
#     newstruct.refs = sgstruct.refs
#     #print "SGSTRUCTURE TO STRUCTURE NEW:",newstruct.assignments,newstruct.coordgroups.to_floats(),newstruct.cell.to_floats()
#     return newstruct.normalize()

# def coordgroups_reduced_rc_to_primcell(coordgroups,basis,hall_symbol):
#     assignments = range(1,len(coordgroups)+1)
#     struct = Structure.create(cell=basis, assignments=assignments, rc_reduced_coordgroups=coordgroups, hall_symbol=hall_symbol)
#     p1structure = structure_to_p1structure(struct)
#     return p1structure.uc_reduced_coordgroups