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
import sys

from httk.core.basic import is_sequence
from httk.core.fracvector import FracVector, FracScalar
from httk.core.mutablefracvector import MutableFracVector
from math import sqrt, acos, cos, sin, pi
from data import periodictable


def sort_coordgroups(coordgroups, individual_data):
    counts = [len(x) for x in coordgroups]
    newcoordgroups = []
    newindividual_data = []
    for group in range(len(counts)): 
        order = sorted(range(counts[group]), key=lambda x: (coordgroups[group][x][0], coordgroups[group][x][1], coordgroups[group][x][2]))
        newcoordgroups.append(coordgroups[group][order])
        if individual_data is not None:
            newindividual_data.append([individual_data[group][i] for i in order])

    if individual_data is None:
        return coordgroups.stack(newcoordgroups), newindividual_data
    else:
        return coordgroups.stack(newcoordgroups), None


def niggli_to_metric(niggli):    
    m = niggli.noms
    # Since the niggli matrix contains 2*the product of the off diagonal elements, we increase the denominator by cell.denom*2
    return FracVector(((2*m[0][0], m[1][2], m[1][1]), (m[1][2], 2*m[0][1], m[1][0]), (m[1][1], m[1][0], 2*m[0][2])), niggli.denom*2).simplify()


def metric_to_niggli(cell):
    m = cell.noms
    return FracVector(((m[0][0], m[1][1], m[2][2]), (2*m[1][2], 2*m[0][2], 2*m[0][1])), cell.denom).simplify()


def coords_and_occupancies_to_coordgroups_and_assignments(coords, occupancies):
    if len(occupancies) != len(coords):
        raise Exception("Occupations and coords needs to be of the same length.")
    if len(occupancies) == 0:
        return [], FracVector((), 1)

    coordgroups = []
    group_occupancies = []
    for i in range(len(occupancies)):
        try:
            idx = group_occupancies.index(occupancies[i])
        except ValueError:
            idx = len(group_occupancies)
            group_occupancies.append(occupancies[i])
            coordgroups.append([])
        coordgroups[idx].append(coords[i])
    return coordgroups, group_occupancies
        

def coords_to_coordgroups(coords, counts):
    coordgroups = []
    idx = 0
    for count in counts:
        coordgroups.append(coords[idx:count+idx])
        idx += count
    
    return coordgroups


def coordgroups_to_coords(coordgroups):
    coords = []
    counts = [len(x) for x in coordgroups]
    for group in coordgroups:
        for i in range(len(group)):
            coords.append(group[i])
    coords = FracVector.stack_vecs(coords)
    return coords, counts


def niggli_to_cell_old(niggli_matrix, orientation=1):
    cell = FracVector.use(niggli_matrix)
    niggli_matrix = niggli_matrix.to_floats()

    s11, s22, s33 = niggli_matrix[0][0], niggli_matrix[0][1], niggli_matrix[0][2]
    s23, s13, s12 = niggli_matrix[1][0]/2.0, niggli_matrix[1][1]/2.0, niggli_matrix[1][2]/2.0
    
    a, b, c = sqrt(s11), sqrt(s22), sqrt(s33)
    alpha_rad, beta_rad, gamma_rad = acos(s23/(b*c)), acos(s13/(c*a)), acos(s12/(a*b))

    iv = 1-cos(alpha_rad)**2-cos(beta_rad)**2-cos(gamma_rad)**2+2*cos(alpha_rad)*cos(beta_rad)*cos(gamma_rad)

    # Handle that iv may be very, very slightly < 0 by the floating point accuracy limit
    if iv > 0:
        v = sqrt(iv)
    else:
        v = 0.0

    if c*v < 1e-14:
        raise Exception("niggli_to_cell: Physically unreasonable cell, cell vectors degenerate or very close to degenerate.")

    if orientation < 0:
        cell = [[-a, 0.0, 0.0],
                [-b*cos(gamma_rad), -b*sin(gamma_rad), 0.0],
                [-c*cos(beta_rad), -c*(cos(alpha_rad)-cos(beta_rad)*cos(gamma_rad))/sin(gamma_rad), -c*v/sin(gamma_rad)]]
    else:
        cell = [[a, 0.0, 0.0],
                [b*cos(gamma_rad), b*sin(gamma_rad), 0.0],
                [c*cos(beta_rad), c*(cos(alpha_rad)-cos(beta_rad)*cos(gamma_rad))/sin(gamma_rad), c*v/sin(gamma_rad)]]

    for i in range(3):
        for j in range(3):
            cell[i][j] = round(cell[i][j], 14)
    
    return cell


def niggli_to_basis(niggli_matrix, orientation=1):
    #cell = FracVector.use(niggli_matrix)
    niggli_matrix = niggli_matrix.to_floats()

    s11, s22, s33 = niggli_matrix[0][0], niggli_matrix[0][1], niggli_matrix[0][2]
    s23, s13, s12 = niggli_matrix[1][0]/2.0, niggli_matrix[1][1]/2.0, niggli_matrix[1][2]/2.0
    
    a, b, c = sqrt(s11), sqrt(s22), sqrt(s33)
    alpha_rad, beta_rad, gamma_rad = acos(s23/(b*c)), acos(s13/(c*a)), acos(s12/(a*b))

    iv = 1-cos(alpha_rad)**2-cos(beta_rad)**2-cos(gamma_rad)**2+2*cos(alpha_rad)*cos(beta_rad)*cos(gamma_rad)

    # Handle that iv may be very, very slightly < 0 by the floating point accuracy limit
    if iv > 0:
        v = sqrt(iv)
    else:
        v = 0.0

    if c*v < 1e-14:
        raise Exception("niggli_to_cell: Physically unreasonable cell, cell vectors degenerate or very close to degenerate.")

    if orientation < 0:
        basis = [[-a, 0.0, 0.0],
                 [-b*cos(gamma_rad), -b*sin(gamma_rad), 0.0],
                 [-c*cos(beta_rad), -c*(cos(alpha_rad)-cos(beta_rad)*cos(gamma_rad))/sin(gamma_rad), -c*v/sin(gamma_rad)]]
    else:
        basis = [[a, 0.0, 0.0],
                 [b*cos(gamma_rad), b*sin(gamma_rad), 0.0],
                 [c*cos(beta_rad), c*(cos(alpha_rad)-cos(beta_rad)*cos(gamma_rad))/sin(gamma_rad), c*v/sin(gamma_rad)]]

    for i in range(3):
        for j in range(3):
            basis[i][j] = round(basis[i][j], 14)
    
    return basis


def basis_to_niggli(basis):
    basis = FracVector.use(basis)
    
    A = basis.noms
    det = basis.det()
    if det == 0:
        raise Exception("basis_to_niggli: singular cell matrix.")

    if det > 0:
        orientation = 1
    else:
        orientation = -1

    s11 = A[0][0]*A[0][0]+A[0][1]*A[0][1]+A[0][2]*A[0][2]
    s22 = A[1][0]*A[1][0]+A[1][1]*A[1][1]+A[1][2]*A[1][2]
    s33 = A[2][0]*A[2][0]+A[2][1]*A[2][1]+A[2][2]*A[2][2]

    s23 = A[1][0]*A[2][0]+A[1][1]*A[2][1]+A[1][2]*A[2][2]
    s13 = A[0][0]*A[2][0]+A[0][1]*A[2][1]+A[0][2]*A[2][2]
    s12 = A[0][0]*A[1][0]+A[0][1]*A[1][1]+A[0][2]*A[1][2]

    new = FracVector.create(((s11, s22, s33), (2*s23, 2*s13, 2*s12)), denom=basis.denom**2).simplify()
    return new, orientation


def basis_determinant(basis):
    try:
        return basis.det()
    except AttributeError:
        C = basis
        det = C[0][0]*C[1][1]*C[2][2] + C[0][1]*C[1][2]*C[2][0] + C[0][2]*C[1][0]*C[2][1] - C[0][2]*C[1][1]*C[2][0] - C[0][1]*C[1][0]*C[2][2] - C[0][0]*C[1][2]*C[2][1]
        return det


def basis_vol_to_scale(basis, vol):
    det = float(basis_determinant(basis))
    if abs(det) < 1e-12:
        raise Exception("basis_to_niggli: Too singular cell matrix.")
    return (float(vol)/(abs(det)))**(1.0/3.0) 


def basis_scale_to_vol(basis, scale):
    det = float(basis_determinant(basis))
    if abs(det) < 1e-12:
        raise Exception("basis_to_niggli: Too singular cell matrix.")
    return (((scale)**3)*(abs(det)))


def niggli_vol_to_scale(niggli_matrix, vol):
    niggli_matrix = FracVector.use(niggli_matrix)
    metric = niggli_to_metric(niggli_matrix)
    volsqr = metric.det()
    if volsqr == 0:
        raise Exception("niggli_vol_to_scale: singular cell matrix.")
    det = sqrt(float(volsqr))
    return (float(vol)/det)**(1.0/3.0) 


def niggli_scale_to_vol(niggli_matrix, scale):
    niggli_matrix = FracVector.use(niggli_matrix)
    metric = niggli_to_metric(niggli_matrix)
    volsqr = metric.det()
    if volsqr == 0:
        raise Exception("niggli_vol_to_scale: singular cell matrix.")
    det = sqrt(float(volsqr))
    if abs(det) < 1e-12:
        raise Exception("niggli_scale_to_vol: singular cell matrix.")
    return (((scale)**3)*det)


def niggli_to_lengths_angles(niggli_matrix):
        
    s11, s22, s33 = niggli_matrix[0][0], niggli_matrix[0][1], niggli_matrix[0][2]
    s23, s13, s12 = niggli_matrix[1][0]/2.0, niggli_matrix[1][1]/2.0, niggli_matrix[1][2]/2.0
    
    a, b, c = sqrt(s11), sqrt(s22), sqrt(s33)
    alpha, beta, gamma = acos(s23/(b*c))*180/pi, acos(s13/(c*a))*180/pi, acos(s12/(a*b))*180/pi
        
    return [a, b, c], [alpha, beta, gamma]


def lengths_angles_to_niggli(lengths, angles):
    niggli_matrix = [[None, None, None], [None, None, None]]

    niggli_matrix[0][0] = lengths[0]*lengths[0]
    niggli_matrix[0][1] = lengths[1]*lengths[1]
    niggli_matrix[0][2] = lengths[2]*lengths[2]

    niggli_matrix[1][0] = 2.0*lengths[1]*lengths[2]*cos(angles[0]*pi/180)
    niggli_matrix[1][1] = 2.0*lengths[0]*lengths[2]*cos(angles[1]*pi/180)
    niggli_matrix[1][2] = 2.0*lengths[0]*lengths[1]*cos(angles[2]*pi/180)

    return niggli_matrix


def cartesian_to_reduced(cell, coordgroups):
    cell = FracVector.use(cell)
    cellinv = cell.inv()

    newcoordgroups = []

    for coordgroup in coordgroups:
        newcoordgroup = coordgroup*cellinv
        newcoordgroups.append(newcoordgroup)

    return newcoordgroups


def structure_to_p1structure(struct, backends=['ase']):
    for backend in backends:
        if backend == 'ase':
            try:
                from httk.external import ase_ext        
                return ase_ext.structure_to_p1structure(struct)
            except ImportError:
                raise
                pass
    raise Exception("structure_to_p1structure: None of the available backends available.")


def structure_to_sgstructure(struct, backends=['platon']):
    for backend in backends:
        if backend == 'platon':
            try:
                from httk.external import platon        
                return platon.structure_to_sgstructure(struct)
            except ImportError:
                pass
    raise Exception("structure_to_sgstructure: None of the available backends available.")


def reduced_to_cartesian(cell, coordgroups):
    cell = FracVector.use(cell)

    newcoordgroups = []

    for coordgroup in coordgroups:
        newcoordgroup = coordgroup*cell
        newcoordgroups.append(newcoordgroup)

    return newcoordgroups


def normalized_formula_parts(assignments, ratios, counts):    
        
    formula = {}
    alloccs = {}
    maxc = 0
    for i in range(len(counts)):
        assignment = assignments[i]
        ratio = ratios[i]
        if is_sequence(assignment):
            if len(assignment) == 1:
                assignment = assignment[0]
                ratio = ratio[0]
                occ = ratio
            else:
                assignment = tuple([(x, FracVector.use(y)) for x, y in zip(assignment, ratio)])
                occ = 1
        else:
            occ = ratio
        if not assignment in formula:
            formula[assignment] = FracVector.create(0)
            alloccs[assignment] = FracVector.create(0)
        formula[assignment] += FracVector.create(occ*counts[i])
        alloccs[assignment] += FracVector.create(counts[i])
        if alloccs[assignment] > maxc:
            maxc = alloccs[assignment]

    alloccs = FracVector.create(alloccs.values())
    alloccs = (alloccs/maxc).simplify()        

    for symbol in formula.keys():
        formula[symbol] = (formula[symbol]*alloccs.denom/maxc).simplify()         
    #    if abs(value-int(value))<1e-6:
    #        formula[symbol] = int(value) 
    #    elif int(100*(value-(int(value)))) > 1:
    #        formula[symbol] = float("%d.%.2e" % (value, 100*(value-(int(value))))) 
    #    else:
    #        formula[symbol] = float("%d" % (value,))

    return formula


def normalized_formula(assignments, ratios, counts):
    formula = normalized_formula_parts(assignments, ratios, counts)

    normalized_formula = ""
    for key in sorted(formula.iterkeys()):
        if is_sequence(formula[key]):
            totval = sum(formula[key])
        else:
            totval = formula[key]
        totval = totval.set_denominator(100).simplify()
        if totval.denom == 1:
            if totval == 1:
                if is_sequence(key):
                    normalized_formula += "(" 
                    for subkey in key:
                        if is_sequence(subkey):
#                           normalized_formula += "".join([("%s%d.%02d"%(x[0],x[1].floor(),(x[1]-x[1].floor())*100.floor())) for x in subkey]) 
                            normalized_formula += "%s%d.%02d" % (subkey[0], subkey[1].floor(), ((subkey[1]-subkey[1].floor())*100).floor()) 
                        else:
                            normalized_formula += "%s" % (subkey,)
                    normalized_formula += ")" 
                else:
                    normalized_formula += "%s" % (key,)
            #if is_sequence(xval):
            #    totval = sum(xval)
            #else:
            #    totval = xval
                #if len(xval)>1:
                    #normalized_formula += "%s" % (key,) + "(" + ",".join([("%d" % x.floor()) for x in xval]) + ")"
                #else:
                #    normalized_formula += "%s%d" % (key, xval[0].floor())
            else:
                if is_sequence(key):
                    normalized_formula += "(" 
                    for subkey in key:
                        if is_sequence(subkey):
#                           normalized_formula += "".join([("%s%d.%02d"%(x[0],x[1].floor(),(x[1]-x[1].floor())*100.floor())) for x in subkey]) 
                            normalized_formula += "%s%d.%02d" % (subkey[0], subkey[1].floor(), ((subkey[1]-subkey[1].floor())*100).floor())
                        else:
                            normalized_formula += "%s" % (subkey,)
                    normalized_formula += ")%d" % (totval,)
                                        
#                    normalized_formula += "(" + "".join(["%s%d" % (x,y.floor()) for x,y in zip(key,totval)]) + ")"
                else:
                    normalized_formula += "%s%d" % (key, totval.floor())
        else:
                #if len(xval)>1:
                #    normalized_formula += "(" + ",".join([("%d.%02d" % (x.floor(),((x-x.floor())*100).floor())) for x in xval]) + ")"
                #else:
                #    normalized_formula += "%s%d.%02d" % (key, xval[0].floor(),((xval[0]-xval[0].floor())*100).floor())
            #else:
            #normalized_formula += "%s%d.%02d" % (key, xval.floor(),((xval-xval.floor())*100).floor())
            if is_sequence(key):
                normalized_formula += "(" 
                for subkey in key:
                    if is_sequence(subkey):
#                       normalized_formula += "".join([("%s%d.%02d"%(x[0],x[1].floor(),(x[1]-x[1].floor())*100.floor())) for x in subkey]) 
                        normalized_formula += "%s%d.%02d" % (subkey[0], subkey[1].floor(), ((subkey[1]-subkey[1].floor())*100).floor()) 
                    else:
                        normalized_formula += "%s" % (subkey,)
                normalized_formula += ")%d.%02d" % (totval, ((totval-totval.floor())*100).floor())
#                normalized_formula += "("+ "".join(["%s%d.%02d" % (x, y.floor(),((y-y.floor())*100).floor()) for x,y in zip(key,totval)]) + ")"
            else:
                normalized_formula += "%s%d.%02d" % (key, totval.floor(), ((totval-totval.floor())*100).floor())

    return normalized_formula


def abstract_symbol(count):
    if count < 27:
        return chr(64+count)
    my = (count-1) % 26
    rec = (count-1) // 26
    return abstract_symbol(rec)+chr(97+my)


def abstract_formula(filled_counts):
    
    formula = normalized_formula_parts(range(len(filled_counts)), [1]*len(filled_counts), filled_counts)

    idx = 0
    abstract_formula = ""
    
    for val in sorted(formula.items(), key=lambda x: x[1]):        
        idx += 1
        c = abstract_symbol(idx)

        xval = val[1].set_denominator(100).simplify()
        if xval.denom == 1:
            if xval == 1:
                abstract_formula += "%s" % (c,)
            else:
                abstract_formula += "%s%d" % (c, xval.floor())
        else:
            abstract_formula += "%s%d.%02d" % (c, xval.floor(), ((xval-xval.floor())*100).floor())
        
        #abstract_formula += "%s%g" % (c,val[1])
        
    return abstract_formula


def prototype_formula(proto):
    sorted_counts = sorted(proto.counts)
    fake_assignments = [((x, 1),) for x in range(len(sorted_counts))]
    formula = normalized_formula_parts(fake_assignments, sorted_counts)

    idx = 0
    abstract_formula = ""
    
    for val in sorted(formula.items(), key=lambda x: x[1]):        
        idx += 1
        c = abstract_symbol(idx)

        xval = val[1].set_denominator(100).simplify()
        if xval.denom == 1:
            if xval == 1:
                abstract_formula += "%s" % (c,)
            else:
                abstract_formula += "%s%d" % (c, xval.floor())
        else:
            abstract_formula += "%s%d.%02d" % (c, xval.floor(), ((xval-xval.floor())*100).floor())
        
        #abstract_formula += "%s%g" % (c,val[1])
        
    return abstract_formula

# def parse_assignment(assignment):    
#     if isinstance(assignment,(tuple,list)):
#         if len(assignment)>=3:
#             return FracVector.use(assignment[2])
#         return FracVector.use(assignment[1])
#     return FracVector.create(1)

#def assignments_tidy(assignments):
#    newassignments=[]
#    for assignment in assignments:
#        newassignments.append((periodictable.atomic_symbol(assignment),periodictable.atomic_number(assignment),parse_assignment(assignment),))
#    return tuple(newassignments)


def coordgroups_cartesian_to_reduced(coordgroups, basis):
    basis = FracVector.use(basis)
    cellinv = basis.inv()

    newcoordgroups = []

    for coordgroup in coordgroups:
        newcoordgroup = coordgroup*cellinv
        newcoordgroups.append(newcoordgroup)

    return newcoordgroups


def coords_and_counts_to_coordgroups(coords, counts):
    coordgroups = []
    idx = 0
    for count in counts:
        coordgroups.append(coords[idx:count+idx])
        idx += count
    
    return coordgroups


def coordgroups_and_assignments_to_coords_and_occupancies(coordgroups, assignments):
    coords = coordgroups_to_coords(coordgroups)
    occupancies = []
    for i in range(len(coordgroups)):
        occupancies += [assignments[i]]*len(coordgroups[i])
    return coords, occupancies


def structure_reduced_uc_to_representative(struct, backends=['isotropy', 'fake']):
    for backend in backends:
        if backend == 'isotropy':
            try:
                from httk.external import isotropy_ext
                sys.stderr.write("Warning: need to run symmetry finder. This may take a while.\n")
                struct = isotropy_ext.struct_process_with_isotropy(struct)
                return struct
            except ImportError:
                raise 
                pass
        if backend == 'fake':
            try:
                from httk.atomistic import Structure
                sys.stderr.write("Warning: using 'fake' symmetry finder that never finds any symmetry.\n")
                newstruct = Structure.create(
                    assignments=struct.assignments,
                                  rc_cell=struct.uc_cell,
                                  rc_reduced_coords=struct.uc_reduced_coords,
                                  rc_counts=struct.uc_counts,
                                  uc_cell=struct.uc_cell,
                                  uc_reduced_coords=struct.uc_reduced_coords, 
                                  uc_counts=struct.uc_counts,
                                  spacegroup='P 1',
                                  tags=struct.get_tags(), refs=struct.get_refs(), periodicity=struct.uc_sites.pbc)
                return newstruct
            except ImportError:
                raise 
                pass
    raise Exception("structure_to_sgstructure: None of the available backends available.")


def coordgroups_reduced_uc_to_representative(coordgroups, basis, backends=['isotropy']):
    sys.stderr.write("WARNING: coordgroups_reduced_uc_to_representative: running untested code...\n")
    for backend in backends:
        if backend == 'isotropy':
            try:
                from httk.external import isotropy_ext
                struct = isotropy_ext.uc_reduced_coordgroups_process_with_isotropy(coordgroups, basis)
                return struct
            except ImportError:
                raise 
                pass
        #if backend ==  'platon':
        #    try:
        #        from httk.external import platon_ext        
        #        return platon_ext.coordgroups_reduced_uc_to_representative(coordgroups, basis, hall_symbol)
        #    except ImportError:
        #        raise 
        #        pass
    raise Exception("structure_to_sgstructure: None of the available backends available.")


def coordgroups_reduced_rc_to_unitcellsites(coordgroups, basis, hall_symbol, backends=['cif2cell', 'ase']):
    # TODO: Make own, or use cif2cell to generate reduced unitcell
    if hall_symbol == 'P 1':
        return coordgroups, FracScalar(1)

    for backend in backends:
        if backend == 'cif2cell':
            try:
                from httk.external import cif2cell_ext        
                return cif2cell_ext.coordgroups_reduced_rc_to_unitcellsites(coordgroups, basis, hall_symbol)
            except ImportError:
                raise
                pass
        if backend == 'ase':
            try:
                from httk.external import ase_glue        
                return ase_glue.coordgroups_reduced_rc_to_unitcellsites(coordgroups, basis, hall_symbol)
            except ImportError:
                raise
                pass
    raise Exception("structure_to_p1structure: None of the available backends available.")


def coordswap(fromidx, toidx, cell, coordgroups):
    new_coordgroups = []
    for group in coordgroups:
        coords = MutableFracVector.from_FracVector(group)
        rows = coords[:, toidx]
        coords[:, toidx] = coords[:, fromidx]
        coords[:, fromidx] = rows        
        new_coordgroups.append(coords.to_FracVector())
    coordgroups = FracVector.create(new_coordgroups)
    
    cell = MutableFracVector.from_FracVector(cell)
    row = cell[toidx]
    cell[toidx] = cell[fromidx]
    cell[fromidx] = row
    cell = cell.to_FracVector()

    return (cell, coordgroups)


def clean_coordgroups_and_assignments(coordgroups, assignments):
    if len(assignments) != len(coordgroups):
        raise Exception("Occupations and coords needs to be of the same length.")
    if len(assignments) == 0:
        return [], FracVector((), 1)

    new_coordgroups = []
    new_assignments = []
    for i in range(len(assignments)):
        for j in range(len(new_assignments)):
            if assignments[i] == new_assignments[j]:
                idx = j 
                new_coordgroups[idx] = FracVector.chain_vecs([new_coordgroups[idx], coordgroups[i]])
                break
        else:
            new_coordgroups.append(coordgroups[i])
            new_assignments.append(assignments[i])
            idx = len(coordgroups)-1
    return new_coordgroups, new_assignments


def occupations_and_coords_to_assignments_and_coordgroups(occupationscoords, occupations):
    if len(occupationscoords) == 0:
        return [], FracVector((), 1)

    occupationscoords = FracVector.use(occupationscoords)

    new_coordgroups = []
    new_assignments = []
    for i in range(len(occupations)):
        for j in range(len(new_assignments)):
            if occupations[i] == new_assignments[j]:
                new_coordgroups[j].append(occupationscoords[i])
                break
        else:
            new_coordgroups.append([occupationscoords[i]])
            new_assignments.append(occupations[i])
    new_coordgroups = FracVector.create(new_coordgroups)
    return new_assignments, new_coordgroups


def coordgroups_and_assignments_to_symbols(coordgroups, assignmentobj):
    """
    Return a list of atomic symbols, repeated as needed 
    """
    symbols = []
    for i in range(len(coordgroups)):
        name = assignmentobj.symbols[i]
        symbols += [name]*len(coordgroups[i])

    return symbols


def structure_tidy(struct, backends=['platon']):
    for backend in backends:
        if backend == 'platon':
            try:
                from httk.external import platon_ext        
                return platon_ext.structure_tidy(struct)
            except ImportError:
                raise
                pass
    raise Exception("structure_tidy: None of the available backends available.")


def main():
    cell = FracVector.create([[1, 1, 0], [1, 0, 1], [0, 1, 1]])
    coordgroups = FracVector.create([[[2, 3, 5], [3, 5, 4]], [[4, 6, 7]]])
    assignments = [2, 5]

    print cell, coordgroups
    cell, coordgroups = coordswap(0, 2, cell, coordgroups)
    print cell, coordgroups
    
    pass

if __name__ == "__main__":
    main()








    
