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
"""
Basic geometry helper functions
"""
from __future__ import division
from vectors import FracVector
from vectors import MutableFracVector
 

def is_point_inside_cell(cell, point):
    """
    Checks if a given triple-vector is inside the cell given by the basis matrix in cell
    """
    p1 = FracVector((0, 0, 0))
    p2 = cell[0]
    p3 = cell[1]
    p4 = cell[0]+cell[1]
    p5 = cell[2]
    p6 = cell[0]+cell[2]
    p7 = cell[1]+cell[2]
    p8 = cell[0]+cell[1]+cell[2]
 
    tetras = [None]*6    
    tetras[0] = [p1, p2, p3, p6]
    tetras[1] = [p2, p3, p4, p6]
    tetras[2] = [p3, p4, p6, p8]
    tetras[3] = [p3, p6, p7, p8]
    tetras[4] = [p3, p5, p6, p7]
    tetras[5] = [p1, p3, p5, p6]
 
    for tetra in tetras:
        if is_point_inside_tetra(tetra, point):
            return True
    return False
 

def is_point_inside_tetra(tetra, point):
    """
    Checks if a point is inside the tretrahedra spanned by the coordinates in tetra
    """
    D0 = FracVector(((tetra[0][0], tetra[0][1], tetra[0][2], 1), (tetra[1][0], tetra[1][1], tetra[1][2], 1), (tetra[2][0], tetra[2][1], tetra[2][2], 1), (tetra[3][0], tetra[3][1], tetra[3][2], 1)))
    D1 = FracVector(((point[0], point[1], point[2], 1), (tetra[1][0], tetra[1][1], tetra[1][2], 1), (tetra[2][0], tetra[2][1], tetra[2][2], 1), (tetra[3][0], tetra[3][1], tetra[3][2], 1)))
    D2 = FracVector(((tetra[0][0], tetra[0][1], tetra[0][2], 1), (point[0], point[1], point[2], 1), (tetra[2][0], tetra[2][1], tetra[2][2], 1), (tetra[3][0], tetra[3][1], tetra[3][2], 1)))
    D3 = FracVector(((tetra[0][0], tetra[0][1], tetra[0][2], 1), (tetra[1][0], tetra[1][1], tetra[1][2], 1), (point[0], point[1], point[2], 1), (tetra[3][0], tetra[3][1], tetra[3][2], 1)))
    D4 = FracVector(((tetra[0][0], tetra[0][1], tetra[0][2], 1), (tetra[1][0], tetra[1][1], tetra[1][2], 1), (tetra[2][0], tetra[2][1], tetra[2][2], 1), (point[0], point[1], point[2], 1)))
    d0 = D0.det()
    if d0 < 0:
        s0 = -1
    else:
        s0 = 1
    d1 = D1.det()
    d2 = D2.det()
    d3 = D3.det()
    d4 = D4.det()
 
    if abs(d0) == 0:
        return False
     
    if (d1.sign() == s0 or d1 == 0) and (d2.sign() == s0 or d2 == 0) and (d3.sign() == s0 or d3 == 0) and (d4.sign() == s0 or d4 == 0):
        return True
     
    return False
 

def is_any_part_of_cube_inside_cell(cell, midpoint, side):
    """
    Checks if any part of a cube is inside the cell spanned by the vectors in cell
    """
    ps = [midpoint+FracVector((x, y, z))*side for x in [-1, 1] for y in [-1, 1] for z in [-1, 1]]      
    for p in ps:
        if is_point_inside_cell(cell, p):
            return True
    return False

 
def hull_z(points, zs):
    """
    points: a list of points=(x,y,..) with zs= a list of z values;
    a convex half-hull is constructed over negative z-values
    
    returns data on the following format.::

      {
        'hull_points': indices in points list for points that make up the convex hull, 
         'interior_points':indices for points in the interior, 
         'interior_zs':interior_zs
         'zs_on_hull': hull z values for each point (for points on the hull, the value of the hull if this point is excluded)
         'closest_points': list of best linear combination of other points for each point 
         'closest_weights': weights of best linear combination of other points for each point 
      }

    where hull_points and interior_points are lists of the points on the hull and inside the hull.
    and
    
       hull_zs is a list of z-values that the hull *would have* at that point, had this point not been included.
       interior_zs is a list of z-values that the hull has at the interior points.

    """
    hull_points = []
    non_hull_points = []
    hull_distances = []
    closest_points = []
    closest_weights = [] 
    
    zvalues = len(zs)
    coeffs = len(points[0])
    #print "zvalues",zvalues
    #print "coeffs",coeffs
    for i in range(zvalues):
        #print "SEND IN",[zs[j] for j in range(zvalues) if j != i]
        a = FracVector.create([zs[j] for j in range(zvalues) if j != i])
        b = [None]*coeffs
        c = [None]*coeffs
        includepoints = [j for j in range(len(points)) if i != j]

        for j in range(coeffs):
            b[j] = FracVector.create([points[x][j] for x in includepoints])
            c[j] = points[i][j]

#         if i == 0:
#             print "A",a.to_floats()
#             print "B",[x.to_floats() for x in b]
#             print "C",c

        solution = simplex_le_solver(a, b, c)        
        val = solution[0]

#         if i == 0:
#             print "VAL",val
#             print "SOL",solution[1]
#             print "MAPPED SOL",[(solution[1][i],includepoints[i]) for i in range(len(solution[1]))]
#         
        closest = solution[1]
        thisclosestpoints = []
        thisclosestweights = []
        for j in range(len(closest)):
            sol = closest[j]
            if sol != 0:
                thisclosestpoints += [includepoints[j]]
                thisclosestweights += [sol]
                #print "I AM",i,"I disolve into:",includepoints[j],"*",float(sol),"(",j,")"

        closest_points += [thisclosestpoints]
        closest_weights += [thisclosestweights]
        hull_distances += [zs[i] - val]
        
        if zs[i] <= val:
            hull_points += [i]
        else:
            non_hull_points += [i]

    return {'hull_indices': hull_points, 
            'interior_indices': non_hull_points, 
            'hull_distances': hull_distances, 
            'competing_indices': closest_points, 
            'competing_weights': closest_weights,
            }
 
# http://en.literateprograms.org/Quickhull_(Python,_arrays)


def numpy_quickhull_2d(sample):
    import numpy as np
    link = lambda a, b: np.concatenate((a, b[1:]))
    edge = lambda a, b: np.concatenate(([a], [b]))

    def dome(sample, base): 
        h, t = base
        dists = np.dot(sample-h, np.dot(((0, -1), (1, 0)), (t-h)))
        outer = np.repeat(sample, dists > 0, 0)

        if len(outer):
            pivot = sample[np.argmax(dists)]
            return link(dome(outer, edge(h, pivot)),
                        dome(outer, edge(pivot, t)))
        else:
            return base
    if len(sample) > 2:
        axis = sample[:, 0]
        base = np.take(sample, [np.argmin(axis), np.argmax(axis)], 0)
        return link(dome(sample, base),
                    dome(sample, base[::-1]))
    else:
        return sample
    

# TODO: Speed up. Is FracVector really needed? Can we make a pure integer version?
def simplex_le_solver(a, b, c):
    """
    Minimizie func = a[0]*x + a[1]*y + a[2]*z + ...
    With constraints::
    
        b[0,0]x + b[0,1]y + b[0,2]z + ... <= c[0]
        b[1,0]x + b[1,1]y + b[1,2]z + ... <= c[1]
        ...
        x,y,z, ... >= 0
        
    Algorithm adapted from 'taw9', http://taw9.hubpages.com/hub/Simplex-Algorithm-in-Python
    
    """
    Na = len(a)
    Nc = len(c)
    obj = a.get_insert(0, 1)
    M = []
    for i in range(Nc):
        obj = obj.get_append(0)
        ident = [0]*Nc
        ident[i] = 1
        M += [b[i].get_insert(0, 0).get_extend(ident).get_append(c[i])]
    M = MutableFracVector.create(M)    
    obj = obj.get_append(0)
    base = range(Na, Na+Nc)
        
    while not min(obj[1:-1]) >= 0:        
        pivot_col = obj[1:-1].argmin() + 1
        rhs = M[:, -1]
        lhs = M[:, pivot_col]
        
        nonzero = [i for i in range(len(rhs)) if lhs[i] != 0]
        pivot_row = min(nonzero, key=lambda i: rhs[i]/lhs[i])

        M[pivot_row] = (M[pivot_row]/(M[pivot_row][pivot_col])).simplify()
        for i in range(Nc):
            if i == pivot_row: 
                continue
            M[i] = (M[i] - M[i][pivot_col]*M[pivot_row]).simplify()
        obj = (obj - obj[pivot_col]*M[pivot_row]).simplify()
        base[pivot_row] = pivot_col-1

    solution = [0]*Na
    for j in range(Nc):
        if obj[base[j]+1] == 0 and base[j] < Na:
            solution[base[j]] = M[j][-1].simplify()
    
    return FracVector.create(-obj[-1]), FracVector.create(solution)
    

if __name__ == '__main__':

    a = FracVector.create([-3, -2])
    b = FracVector.create([[2, 1], [2, 3], [3, 1]])
    c = FracVector.create([18, 42, 24])

    print simplex_le_solver(a, b, c)

    exit(0)

    from pylab import *

    xsample = FracVector.random((5, 1), 0, 100, 100)
    xsample = FracVector.create([[x[0], 1-x[0]] for x in xsample] + [[1, 0]] + [[0, 1]])
    ysample = (-1*FracVector.random((5,), 0, 100, 100)).get_extend([0, 0])

    hull = hull_z(xsample, ysample)
  
    hull_points = xsample[hull['hull_points']]
    hull_zs = ysample[hull['hull_points']]
  
    reidx = sorted(range(len(hull_points)), key=lambda el: hull_points[el][0])
    hull_points = [hull_points[i] for i in reidx]
    hull_zs = [hull_zs[i] for i in reidx]
 
    xvals = [x[0] for x in xsample]
    yvals = ysample
     
    scatter(xvals, yvals, s=80, marker="x")
    oldx = hull_points[0][0]
    oldy = hull_zs[0]
    for i in range(1, len(hull_points)):
        x = hull_points[i][0]
        y = hull_zs[i]
        plot([oldx, x], [oldy, y], color='k', linestyle='-', linewidth=2)
        oldx = x
        oldy = y    
    show()    

