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

# Method from A. R. Akbarzadeh, V. Ozolins, and C. Wolverton
# First-Principles Determination of Multicomponent Hydride Phase Diagrams: Application to the Li-Mg-N-H System+
# http://onlinelibrary.wiley.com/doi/10.1002/adma.200700843/abstract
import sys

from httk.core.geometry import hull_z
from httk.core.httkobject import HttkPluginPlaceholder
from httk.core import FracVector


class PhaseDiagram(object):

    """
    """

    def __init__(self):
        self.seen_symbols = {}
        self.phases = []
        self.other_phases = []
        self.energies = []
        self.ids = []
        self.other_ids = []

        self._reset()

    def _reset(self):
        self._hull_indices = None
        self._competing_indices = None
        self._hull_competing_indices = None
        self._hull_distances = None
        self._coordsys = None        
        self._cache_hull = None    
        self._cache_overhull = None
        self._phase_lines = None    
        
    @classmethod
    def create(cls):
        return cls()

    def add_phase(self, symbols, counts, id, energy):
        """
        Handles energy=None, for a phase we don't know the energy of.
        """
        counts = FracVector.use(counts)
        phase = {}
        for i in range(len(symbols)):
            symbol = symbols[i]
            if symbol in phase:
                phase[symbol] += counts[i]
            else:
                phase[symbol] = counts[i]
            self.seen_symbols[symbol] = True
        if energy is not None:
            self.phases += [phase]
            self.energies += [energy]
            self.ids += [id]
        else:
            self.other_phases += [phase]
            self.other_ids += [id]

        # Clear out so things get reevaluated
        self._reset()

    def set_hull_data(self, hull_indices, competing_indices, hull_competing_indices,
                      hull_distances, coord_system, phase_lines):
        self._hull_indices = hull_indices
        self._competing_indices = competing_indices
        self._hull_competing_indices = hull_competing_indices
        self._hull_distances = hull_distances
        self._coord_system = coord_system
        self._phase_lines = phase_lines
        
    @property
    def hull_indices(self):
        if self._hull_indices is None:
            self._hull_indices = self._hull()['hull_indices']
        return self._hull_indices
        
    @property
    def competing_indices(self):
        if self._competing_indices is None:
            self._competing_indices = self._hull()['competing_indices']
        return self._competing_indices

    @property
    def hull_competing_indices(self):
        if self._hull_competing_indices is None:
            self._hull_competing_indices = self._overhull()['competing_indices']
        return self._hull_competing_indices
    
    @property
    def hull_distances(self):
        if self._hull_distances is None:
            self._hull_distances = self._hull()['hull_distances']
        return self._hull_distances

    @property
    def coord_system(self):
        if self._coordsys is None:
            self._coordsys = self.seen_symbols.keys()
        return self._coordsys

    @property
    def phase_lines(self):
    # TODO: This does not give all phase lines, add code!
        if self._phase_lines is None:
            hull_points = self.hull_indices
            closest = self.hull_competing_indices
            lines = {}
            for i in range(len(hull_points)):
                for j in closest[i]:
                    lines[(i, j)] = True
            self._phase_lines = lines.keys()
        return self._phase_lines
        
    def _hull(self):
        if self._cache_hull is None:
            sys.stderr.write("Warning: calculating convex hull, this may take some time.\n")
            symbols = self.coord_system
            phaselist = []
            for phase in self.phases:
                phaselist += [[phase[symbol] if symbol in phase else 0 for symbol in symbols]]
            self._cache_hull = hull_z(phaselist, self.energies)
        return self._cache_hull 

    def _overhull(self):
        if self._cache_overhull is None:
            hull_phases = [self.phases[x] for x in self.hull_indices]
            energies = [self.energies[x] for x in self.hull_indices]
            sys.stderr.write("Warning: calculating convex hull, this may take some time.\n")
            symbols = self.coord_system
            phaselist = []
            for phase in hull_phases:
                phaselist += [[phase[symbol] if symbol in phase else 0 for symbol in symbols]]
            self._cache_overhull = hull_z(phaselist, energies)
        return self._cache_overhull
        
    def hull_points(self):
        return [self.phases[x] for x in self.hull_indices], [self.ids[x] for x in self.hull_indices]
        
    def hull_competing_phase_lines(self):
        hull_points = self.hull_indices
        closest = self.hull_competing_indices
        lines = {}
        for i in range(len(hull_points)):
            for j in closest[i]:
                lines[(i, j)] = True
        return lines.keys()
        
    def hull_to_interior_competing_phase_lines(self):
        hull_points = self.hull_indicies
        closest = self.hull_competing_indices
        lines = {}
        for i in range(len(hull_points)):
            point = hull_points[i]
            for point2 in closest[point]:
                lines[(point, point2)] = True
        return lines.keys()

    def interior_competing_phase_lines(self):
        all_points = range(len(self.phases))
        hull_points = self.hull_indices
        closest = self.competing_indices
        lines = {}
        for i in range(len(all_points)):
            if i in hull_points:
                continue
            for j in closest[i]:
                lines[(i, j)] = True
        return lines.keys()

#         closest = self.hull['closest_points']
#         hull_points = self.hull['hull_points']
#         lines = {}
#         for i in range(len(hull_points)):
#             point = hull_points[i]
#             points_to_check = closest[point]
#             done_points = []
#             while len(points_to_check)>0:
#                 point2 = points_to_check.pop()
#                 print "CHECKING:",point2
#                 if point2 == point:
#                     continue
#                 if point2 in done_points:
#                     continue
#                 if point2 in hull_points:
#                     j = hull_points.index(point2)
#                     l1 = (i,j)
#                     l2 = (j,i)
#                     if not (l1 in lines or l2 in lines):
#                         lines[l1]=True
#                 else:                    
#                     done_points += [point2]
#                     points_to_check += closest[point2]
#         return lines.keys()
    def hull_point_coords(self):
        coordsys = self.coord_system
        phases = [self.phases[x] for x in self.hull_indices]
        ids = [self.ids[x] for x in self.hull_indices]
        phasecoords = []
        for phase in phases:
            tot = sum([phase[symbol] for symbol in phase])
            phasecoords += [[phase[symbol]/tot if symbol in phase else 0 for symbol in coordsys]]
        
        return phasecoords, ids

    def interior_point_coords(self):
        coordsys = self.coord_system
        phases = self.phases
        ids = self.ids
        phasecoords = []
        for i in range(len(phases)):
            if not i in self.hull_indices:
                phase = phases[i]
                tot = sum([phase[symbol] for symbol in phase])
                phasecoords += [[phase[symbol]/tot if symbol in phase else 0 for symbol in coordsys]]
        
        return phasecoords, ids

    def other_point_coords(self):
        coordsys = self.coord_system
        phases = self.other_phases
        ids = self.other_ids
        phasecoords = []
        for phase in phases:
            tot = sum([phase[symbol] for symbol in phase])
            phasecoords += [[phase[symbol]/tot if symbol in phase else 0 for symbol in coordsys]]
        
        return phasecoords, ids

    def coords(self):
        coordsys = self.coord_system
        phases = self.phases
        ids = self.ids
        phasecoords = []
        for phase in phases:
            tot = sum([phase[symbol] for symbol in phase])
            phasecoords += [[phase[symbol]/tot if symbol in phase else 0 for symbol in coordsys]]
        
        return phasecoords, ids

    def line_coords(self):
        phasecoords, ids = self.point_coords()
        lines = self.hull_lines()
        linecoords = []
        for line in lines:
            linecoords += [[phasecoords[line[0]], phasecoords[line[1]]]]
        
        return linecoords
        
    vis = HttkPluginPlaceholder("import httk.analysis.matsci.vis")
    
