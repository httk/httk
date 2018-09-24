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


from httk.core import HttkPlugin, HttkPluginWrapper, FracVector, breath_first_idxs 
from unitcellstructure import UnitcellStructure
from structure import Structure

from cell import Cell

# TODO: The building of supercells should be moved elsewhere and not be part of this class


def build_supercell_old(structure, transformation, max_search_cells=1000):
    ### New basis matrix, note: works in units of old_cell.scale to avoid floating point errors
    #print "BUILD SUPERCELL",structure.uc_sites.cell.basis.to_floats(), repetitions

    transformation = FracVector.use(transformation).simplify()
    if transformation.denom != 1:
        raise Exception("Structure.build_supercell requires integer transformation matrix")
    
    old_cell = structure.uc_sites.cell.get_normalized_longestvec()
    new_cell = Cell.create(basis=transformation*old_cell.basis)
    #conversion_matrix = (new_cell.inv*old_cell.basis).T().simplify()
    conversion_matrix = (old_cell.basis*new_cell.inv).T().simplify()

    volume_ratio = (new_cell.basis.det()/abs(old_cell.basis.det())).simplify()

    # Generate the reduced (old cell) coordinates of each corner in the new cell
    # This determines how far we must loop the old cell to cover all these corners  
    nb = new_cell.basis
    corners = FracVector.create([(0, 0, 0), nb[0], nb[1], nb[2], nb[0]+nb[1], nb[0]+nb[2], nb[1]+nb[2], nb[0]+nb[1]+nb[2]])
    reduced_corners = corners*(old_cell.basis.inv().T())
    
    maxvec = [int(reduced_corners[:, 0].max())+2, int(reduced_corners[:, 1].max())+2, int(reduced_corners[:, 2].max())+2]
    minvec = [int(reduced_corners[:, 0].min())-2, int(reduced_corners[:, 1].min())-2, int(reduced_corners[:, 2].min())-2]

    if max_search_cells is not None and maxvec[0]*maxvec[1]*maxvec[2] > max_search_cells:
        raise Exception("Very obtuse angles in cell, to search over all possible lattice vectors will take a very long time. To force, set max_search_cells = None when calling find_prototypeid()")
         
    ### Collect coordinate list of all sites inside the new cell
    coordgroups = structure.uc_reduced_coordgroups
    extendedcoordgroups = [[] for x in range(len(coordgroups))]
    for idx in range(len(coordgroups)):
        coordgroup = coordgroups[idx]
        for i in range(minvec[0], maxvec[0]):
            for j in range(minvec[1], maxvec[1]):
                for k in range(minvec[2], maxvec[2]):
                    newcoordgroup = coordgroup+FracVector(((i, j, k),)*len(coordgroup))
                    new_reduced = newcoordgroup*conversion_matrix
                    new_reduced = [x for x in new_reduced if x[0] >= 0 and x[1] >= 0 and x[2] >= 0 and x[0] < 1 and x[1] < 1 and x[2] < 1]
                    extendedcoordgroups[idx] += new_reduced

    # Safety check for avoiding bugs that change the ratio of atoms
    new_counts = [len(x) for x in extendedcoordgroups]
    for i in range(len(structure.uc_counts)):
        if volume_ratio*structure.uc_counts[i] != new_counts[i]:
            print "Volume ratio:", float(volume_ratio), volume_ratio
            print "Extended coord groups:", FracVector.create(extendedcoordgroups).to_floats()
            print "Old counts:", structure.uc_counts, structure.assignments.symbols
            print "New counts:", new_counts, structure.assignments.symbols
            #raise Exception("Structure.build_supercell safety check failure. Volume changed by factor "+str(float(volume_ratio))+", but atoms in group "+str(i)+" changed by "+str(float(new_counts[i])/float(structure.uc_counts[i])))
    
    return structure.create(uc_reduced_coordgroups=extendedcoordgroups, basis=new_cell.basis, assignments=structure.assignments, cell=structure.uc_cell)

def build_cubic_supercell(structure, tolerance=None, max_search_cells=1000):
    transformation = cubic_supercell_transformation(structure=structure, tolerance=tolerance)
    #print "Running transformation with:",transformation     
    return structure.transform(transformation, max_search_cells=max_search_cells)

def cubic_supercell_transformation(structure, tolerance=None, max_search_cells=1000):
    # Note: a better name for tolerance is max_extension or similar, it is not really a tolerance, it regulates the maximum number of repetitions of the primitive cell
    # in any directions to reach the soughts supercell

    if tolerance is None:
        prim_cell = structure.uc_cell.basis            
        inv = prim_cell.inv().simplify()
        transformation = (inv*inv.denom).simplify()
    else:            
        maxtol = max(int(FracVector.use(tolerance)), 2)
        bestlen = None
        bestortho = None
        besttrans = None
        #TODO: This loop may be possible to do with fewer iterations, since I suppose the only thing that
        #matter is the prime factors?
        for tol in range(1, maxtol):
            prim_cell = structure.uc_cell.basis        
            prim_cell = structure.uc_cell.basis        
            approxinv = prim_cell.inv().set_denominator(tol).simplify()
            if approxinv[0] == [0, 0, 0] or approxinv[1] == [0, 0, 0] or approxinv[2] == [0, 0, 0]:
                continue
            transformation = (approxinv*approxinv.denom).simplify()
            try:
                cell = Cell.create(basis=transformation*prim_cell)
            except Exception:
                continue
            ortho = (abs(cell.niggli_matrix[1][0])+abs(cell.niggli_matrix[1][1])+abs(cell.niggli_matrix[1][2])).simplify()
            equallen = abs(cell.niggli_matrix[0][0]-cell.niggli_matrix[0][1]) + abs(cell.niggli_matrix[0][0]-cell.niggli_matrix[0][2]) 
            if ortho == 0 and equallen == 0:
                # Already perfectly cubic, use this
                besttrans = transformation
                break
            elif bestlen is None or not (bestortho < ortho and bestlen < equallen):
                bestlen = equallen
                bestortho = ortho
                besttrans = transformation
            elif besttrans == None:
                bestlen = equallen
                bestortho = ortho
                besttrans = transformation

        transformation = besttrans

    if transformation == None:
        raise Exception("Not possible to find a cubic supercell with this limitation of number of repeated cell (increase tolerance.)")
        
    return transformation


def build_orthogonal_supercell(structure, tolerance=None, max_search_cells=1000, ortho=[True, True, True]):
    transformation = orthogonal_supercell_transformation(structure, tolerance, ortho)
    #print "Running transformation with:",transformation     
    return structure.transform(transformation, max_search_cells=max_search_cells)


def orthogonal_supercell_transformation(structure, tolerance=None, ortho=[True, True, True]):
    # TODO: How to solve for exact orthogonal cell?
    if tolerance is None:
        prim_cell = structure.uc_cell.basis         
        print "Starting cell:", prim_cell
        inv = prim_cell.inv().simplify()
        if ortho[0]:
            row0 = (inv[0]/max(inv[0])).simplify()
        else:
            row0 = [1, 0, 0]
        if ortho[1]:
            row1 = (inv[1]/max(inv[1])).simplify()
        else:
            row1 = [0, 1, 0]
        if ortho[2]:
            row2 = (inv[2]/max(inv[2])).simplify()
        else:
            row2 = [0, 0, 1]
        transformation = FracVector.create([row0*row0.denom, row1*row1.denom, row2*row2.denom])
    else:            
        maxtol = max(int(FracVector.use(tolerance)), 2)
        bestval = None
        besttrans = None
        for tol in range(1, maxtol):
            prim_cell = structure.uc_cell.basis   
            inv = prim_cell.inv().set_denominator(tol).simplify()
            if inv[0] == [0, 0, 0] or inv[1] == [0, 0, 0] or inv[2] == [0, 0, 0]:
                continue
            absinv = abs(inv)
            if ortho[0]:
                row0 = (inv[0]/max(absinv[0])).simplify()
            else:
                row0 = [1, 0, 0]
            if ortho[1]:
                row1 = (inv[1]/max(absinv[1])).simplify()
            else:
                row1 = [0, 1, 0]
            if ortho[2]:
                row2 = (inv[2]/max(absinv[2])).simplify()
            else:
                row2 = [0, 0, 1]
            transformation = FracVector.create([row0*row0.denom, row1*row1.denom, row2*row2.denom])
            try:
                cell = Cell.create(basis=transformation*prim_cell)
            except Exception:
                continue
            maxval = (abs(cell.niggli_matrix[1][0])+abs(cell.niggli_matrix[1][1])+abs(cell.niggli_matrix[1][2])).simplify()
            if maxval == 0:
                besttrans = transformation
                break
            if bestval is None or maxval < bestval:
                bestval = maxval
                besttrans = transformation
        transformation = besttrans

    if transformation == None:
        raise Exception("Not possible to find a othogonal supercell with this limitation of number of repeated cell (increase tolerance.)")
        
    return transformation


class StructureSupercellPlugin(HttkPlugin):
                
    def plugin_init(self, struct):
        self.struct = Structure.use(struct)

    def general(self, transformation, max_search_cells=20, max_atoms=1000):
        return self.struct.transformation(transformation, max_search_cells=20, max_atoms=1000)   

    def cubic(self, tolerance=None, max_search_cells=1000):
        return build_cubic_supercell(self.struct, tolerance=tolerance, max_search_cells=max_search_cells)

    def orthogonal(self, tolerance=None, max_search_cells=1000):
        return build_orthogonal_supercell(self.struct, tolerance=tolerance, max_search_cells=max_search_cells)
      
Structure.supercell = HttkPluginWrapper(StructureSupercellPlugin)
UnitcellStructure.supercell = HttkPluginWrapper(StructureSupercellPlugin)


