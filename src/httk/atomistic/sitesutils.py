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

import fractions

from httk.core import FracVector, MutableFracVector
from httk.core.basic import is_sequence
import spacegrouputils


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

# TODO: Cleanup formula generation


def normalized_formula_parts(assignments, ratios, counts):    
        
    formula = {}
    alloccs = {}
    maxc = 0
    for i in range(len(counts)):
        assignment = assignments[i]
        ratio = ratios[i]
        if not assignment in formula:
            formula[assignment] = FracVector.create(0)
            alloccs[assignment] = FracVector.create(0)
        occ = ratio
        formula[assignment] += occ*counts[i]
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


def abstract_symbol(count):
    if count < 27:
        return chr(64+count)
    my = (count-1) % 26
    rec = (count-1) // 26
    return abstract_symbol(rec)+chr(97+my)


def anonymous_formula(filled_counts):
    
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


def coords_reduced_to_cartesian(cell, coords):
    cell = FracVector.use(cell)
    newcoords = coords*cell
    return newcoords


def coordgroups_reduced_to_cartesian(cell, coordgroups):
    cell = FracVector.use(cell)

    newcoordgroups = []

    for coordgroup in coordgroups:
        newcoordgroup = coordgroup*cell
        newcoordgroups.append(newcoordgroup)

    return newcoordgroups


def periodicity_to_pbc(periodicity):
    if is_sequence(periodicity):
        pbc = [bool(x) for x in periodicity]
    else:
        pbc = [False]*periodicity + [True]*(3-periodicity)
    return pbc


def pbc_to_nonperiodic_vecs(pbc):
    nonperiodic_vecs = sum(pbc)
    if (pbc[0] and not (pbc[1] or pbc[2])) or (pbc[1] and not pbc[2]):
        raise Exception("cellutils pbc_to_nonperiodic_vecs: cannot represent as nonperiodic vecs, need non-periodic vecs before periodic ones.")
    return nonperiodic_vecs


def structure_reduced_coordgroups_to_representative(coordgroups, cell, spacegroup, backends=['isotropy']):
    for backend in backends:
        if backend == 'isotropy':
            try:
                from httk.external import isotropy_ext
                return isotropy_ext.uc_reduced_coordgroups_process_with_isotropy(coordgroups, cell, spacegroup, get_wyckoff=True)
            except ImportError:
                raise 
                pass
    raise Exception("structure_reduced_coordgroups_to_representative: None of the available backends available.")


def sites_tidy(sites, backends=['platon']):
    for backend in backends:
        if backend == 'platon':
            try:
                from httk.external import platon_ext        
                return platon_ext.sites_tidy(sites)
            except ImportError:
                raise
                pass
    raise Exception("structure_tidy: None of the available backends available.")


def coordgroups_reduced_to_unitcell(coordgroups, hall_symbol, eps=fractions.Fraction(1,1000)):
    symops = spacegrouputils.get_symops(hall_symbol)
    newcoordgroups = []
    for coordgroup in coordgroups:
        newcoordgroup = []
        for symop in symops:
            rotcoords = coordgroup*(symop[0].T())
            for coord in rotcoords:
                finalcoord = (coord+symop[1]).normalize()
                if finalcoord not in newcoordgroup:
                    for checkcoord in newcoordgroup:
                        if (checkcoord-finalcoord).normalize_half().lengthsqr() < eps:
                            break
                    else:
                        newcoordgroup += [finalcoord]
        newcoordgroup = sorted(newcoordgroup, key=lambda x: (x[0], x[1], x[2]))
        newcoordgroups += [newcoordgroup]
    return newcoordgroups


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




    
