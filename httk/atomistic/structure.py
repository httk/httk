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
import math

from httk.core.httkobject import HttkObject, HttkPluginPlaceholder, httk_typed_property, httk_typed_property_resolve, httk_typed_property_delayed, httk_typed_init
from httk.core.reference import Reference
from httk.core import FracScalar
from httk.core.basic import breath_first_idxs
from cell import Cell
from assignments import Assignments
from sites import Sites
from unitcellsites import UnitcellSites
from representativesites import RepresentativeSites
from data import spacegroups
from structureutils import *
from spacegroup import Spacegroup
from scalelessstructure import ScalelessStructure

class Structure(ScalelessStructure):
    """
    A Structure represents N sites of, e.g., atoms or ions, in any periodic or non-periodic arrangement. 
    The structure object is meant to be immutable and assumes that no internal variables are changed after its creation. 
    All methods that 'changes' the object creates and returns a new, updated, structure object.
    
    Naming conventions in this class (and elsewhere in httk.atomistic):

    For cells:
        cell = an abstract name for any reasonable representation of a 'cell' that defines 
               the basis vectors used for representing the structure. When a 'cell' is returned,
               it is an object of type Cell

        basis = a 3x3 sequence-type with (in rows) the three basis vectors (for a periodic system, defining the unit cell, and defines the unit of repetition for the periodic dimensions)

        lengths_and_angles = (a,b,c,alpha,beta,gamma): the basis vector lengths and angles

        niggli_matrix = ((v1*v1, v2*v2, v3*v3),(2*v2*v3, 2*v1*v3, 2*v2*v3)) where v1, v2, v3 are the vectors forming the basis

        metric = ((v1*v1,v1*v2,v1*v3),(v2*v1,v2*v2,v2*v3),(v3*v1,v3*v2,v3*v3))

    For sites:
        These following prefixes are used to describe types of site specifications:
            representative cell/rc = only representative atoms are given, which are then to be 
            repeated by structure symmetry group to give all sites

            unit cell/uc = all atoms in unitcell
            
            reduced = coordinates given in cell vectors
            
            cartesian = coordinates given as direct cartesian coordinates

        sites = used as an abstract name for any sensible representation of a list of coordinates and a cell,
                when a 'sites' is returned, it is an object of type Sites 
                  
        counts = number of atoms of each type (one per entry in assignments)
      
        coordgroups = coordinates represented as a 3-level-list of coordinates, e.g. 
        [[[0,0,0],[0.5,0.5,0.5]],[[0.25,0.25,0.25]]] where level-1 list = groups: one group for each equivalent atom

        counts and coords = one list with the number of atoms of each type (one per entry in assignments)
        and a 2-level list of coordinates.

    For assignments of atoms, etc. to sites:
        assignments = abstract name for any representation of assignment of atoms.
        When returned, will be object of type Assignment.

        atomic_numbers = a sequence of integers for the atomic number of each species

        occupations = a sequence where the assignments are *repeated* for each coordinate as needed 
        (prefixed with uc or rc depending on which coordinates)

    For cell scaling:
        scaling = abstract name for any representation of cell scaling
        
        scale = multiply all basis vectors with this number

        volume = rescaling the cell such that it takes this volume

    For periodicity:
        periodicity = abstract name of a representation of periodicity

        pbc = 'periodic boundary conditions' = sequence of True and False for which basis vectors are periodic / non-periodic

        nonperiodic_vecs = integer, number of basis vectors, counted from the first, which are non-periodic

    For spacegroup:
        spacegroup = abstract name for any spacegroup representation. When returned, is of type Spacegroup.

        hall_symbol = specifically the hall_symbol string representation of the spacegroup      
   
    """
    
    #TODO: When httk internally handles symmetry replication, consider removing UnitcellSites from here    
    @httk_typed_init({'assignments':Assignments, 'rc_sites':RepresentativeSites, 
                 'rc_cell':Cell},
                 index=['assignments','rc_sites','rc_cell'])    
    def __init__(self, assignments, rc_sites = None, uc_sites = None, rc_cell=None, uc_cell=None):
        """
        Private constructor, as per httk coding guidelines. Use Structure.create instead.
        """
        super(Structure,self).__init__(assignments = assignments, rc_sites = rc_sites, uc_sites = uc_sites)

        self._rc_cell = rc_cell
        self._uc_cell = uc_cell

        self._tags = None
        self._refs = None

        self._codependent_callbacks = []
        self._codependent_data = []
        self._codependent_info = [{'class':StructureTag,'column':'structure','add_method':'add_tags'},
                                  {'class':StructureRef,'column':'structure','add_method':'add_refs'}]
        
    @classmethod
    def create(cls,
               structure = None,

               uc_cell=None, uc_basis=None, uc_lengths =None, 
               uc_angles = None, uc_niggli_matrix=None, uc_metric=None, 
               uc_a=None, uc_b=None, uc_c=None, 
               uc_alpha=None, uc_beta=None, uc_gamma=None,
               uc_sites = None, 
               uc_reduced_coordgroups = None, uc_cartesian_coordgroups = None,  
               uc_reduced_coords = None, uc_cartesian_coords = None,  
               uc_reduced_occupationscoords = None, uc_cartesian_occupationscoords = None,  
               uc_occupancies=None, uc_counts=None,
               uc_scale=None, uc_scaling=None, uc_volume=None, 

               rc_cell=None, rc_basis=None, rc_lengths =None, 
               rc_angles = None, rc_niggli_matrix=None, rc_metric=None, 
               rc_a=None, rc_b=None, rc_c=None, 
               rc_alpha=None, rc_beta=None, rc_gamma=None,
               rc_sites = None, 
               rc_reduced_coordgroups = None, rc_cartesian_coordgroups = None,
               rc_reduced_coords = None, rc_cartesian_coords = None,  
               rc_reduced_occupationscoords = None, rc_cartesian_occupationscoords = None,  
               rc_occupancies=None, rc_counts=None, 
               wyckoff_symbols = None,
               spacegroup=None, hall_symbol = None, spacegroupnumber=None, setting=None,
               rc_scale=None, rc_scaling=None, rc_volume=None, 
               
               assignments=None, 
               
               periodicity = None, nonperiodic_vecs = None, 
               refs=None, tags=None):
        """
        A Structure represents N sites of, e.g., atoms or ions, in any periodic or non-periodic arrangement. 

        This is a swiss-army-type constructor that allows a selection between a large number of optional arguments.    

        To create a new structure, three primary components are:
           - cell: defines the basis vectors in which reduced coordinates are expressed, and the 
                   unit of repetition (*if* the structure has any periodicity - see the 'periodicity' parameter)
           - assignments: a list of 'things' (atoms, ions, etc.) that goes on the sites in the structure
           - sites: a sensible representation of location / coordinates of the sites.
           
           However, two options exists for representing the sites; either as only giving the representative sites, which when the 
           symmetry operations of the spacegroup are applied generates all sites, or, simply giving the primcell set of sites.
           Since conversion between these are computationally expensive and only strictly 'approximate'. Hence, sites is divided
           accordingly into rc_sites and uc_sites keeping track of the two representations.

         Input:

           - ONE OF: 'cell'; 'basis', 'length_and_angles'; 'niggli_matrix'; 'metric'; all of: a,b,c, alpha, beta, gamma. 
             (cell requires a Cell object or a very specific format, so unless you know what you are doing, use one of the others.)

           - ONE OF: 'assignments', 'atomic_numbers', 'occupancies'
             (assignments requires an Assignments object or a sequence.), occupations repeats similar site assignments as needed
           
           - ONE OF: 'rc_sites', 'uc_sites', 'rc_coords' (IF rc_occupations OR rc_counts are also given), 
             'uc_coords' (IF uc_occupations OR uc_counts are also given)
             'A_B_C', where A=representative or primcell, B=reduced or cartesian, C=coordgroups, coords, or occupationscoords
             
             Notes: 

                  - occupationscoords may differ to coords by *order*, since giving occupations as, e.g., ['H','O','H'] requires
                    a re-ordering of coordinates to the format of counts+coords as (2,1), ['H','O']. 

                  - rc_sites and uc_sites requires a Sites object or a very specific format, so unless you know what you are doing, 
                    use one of the others.)
           
           - ONE OF: 'spacegroup' or 'hall_symbol', or neither (in which case spacegroup is regarded as unknown)                

           - ONE OF: scale or volume: 
             scale = multiply the basis vectors with this scaling factor, 
             volume = rescale the cell into this volume (overrides 'scale' if both are given)

           - ONE OF periodicity or nonperiodic_vecs
           
        See help(Structure) for more information on the data format of all these data representations.
        """                  
        args = dict(locals())  
        del args['cls'],args['rc_scale'],args['rc_scaling'],args['rc_volume']
        del args['uc_scale'],args['uc_scaling'],args['uc_volume']
        del args['rc_cell'], args['uc_cell']

        del args['uc_cartesian_coordgroups'], args['uc_cartesian_coords'], args['uc_cartesian_occupationscoords']  
        del args['rc_cartesian_coordgroups'], args['rc_cartesian_coords'], args['rc_cartesian_occupationscoords']  
        
        if isinstance(structure,Structure):
            return structure

        if isinstance(structure,ScalelessStructure):
            slstruct = structure
        else:
            slstruct = None

        if isinstance(uc_cell,Cell):
            uc_cell = uc_cell
        else:
            try:                        
                uc_cell = Cell.create(cell=uc_cell, basis=uc_basis, metric=uc_metric, 
                                      niggli_matrix=uc_niggli_matrix, 
                                      a=uc_a, b=uc_b, c=uc_c, 
                                      alpha=uc_alpha, beta=uc_beta, gamma=uc_gamma,
                                      lengths = uc_lengths, angles=uc_angles, 
                                      scale=uc_scale, scaling=uc_scaling, volume=uc_volume)
            except Exception:
                uc_cell = None

        if isinstance(rc_cell,Cell):
            rc_cell = rc_cell
        else:                        
            try:                        
                rc_cell = Cell.create(cell=rc_cell, basis=rc_basis, metric=rc_metric, 
                                      niggli_matrix=rc_niggli_matrix, 
                                      a=rc_a, b=rc_b, c=rc_c, 
                                      alpha=rc_alpha, beta=rc_beta, gamma=rc_gamma,
                                      lengths = rc_lengths, angles=rc_angles, 
                                      scale=rc_scale, scaling=rc_scaling, volume=rc_volume)
            except Exception:
                rc_cell = None

        if uc_sites == None and uc_reduced_coordgroups == None and \
               uc_reduced_coords == None and uc_reduced_occupationscoords == None:
            # Cartesian coordinate input must be handled here in structure since scalelessstructure knows nothing about cartesian coordinates...
            if uc_cartesian_coordgroups == None and uc_cartesian_coords == None and \
                    uc_occupancies != None and uc_cartesian_occupationscoords != None:
                assignments, uc_cartesian_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(uc_cartesian_occupationscoords,uc_occupancies)
             
            if uc_cartesian_coords != None and uc_cartesian_coordgroups == None:
                uc_cartesian_coordgroups = coords_and_counts_to_coordgroups(uc_cartesian_coords, uc_counts)

            if uc_cell != None: 
                uc_reduced_coordgroups = coordgroups_cartesian_to_reduced(uc_cartesian_coordgroups,uc_cell)
                args['uc_reduced_coordgroups'] = uc_reduced_coordgroups

        if rc_sites == None and rc_reduced_coordgroups == None and \
               rc_reduced_coords == None and rc_reduced_occupationscoords == None:
            # Cartesian coordinate input must be handled here in structure since scalelessstructure knows nothing about cartesian coordinates...
            if rc_cartesian_coordgroups == None and rc_cartesian_coords == None and \
                    rc_occupancies != None and rc_cartesian_occupationscoords != None:
                assignments, rc_cartesian_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(rc_cartesian_occupationscoords,rc_occupancies)
             
            if rc_cartesian_coords != None and rc_cartesian_coordgroups == None:
                rc_cartesian_coordgroups = coords_and_counts_to_coordgroups(rc_cartesian_coords, rc_counts)

            if rc_cell != None:  
                rc_reduced_coordgroups = coordgroups_cartesian_to_reduced(rc_cartesian_coordgroups,rc_cell)
                args['rc_reduced_coordgroups'] = rc_reduced_coordgroups

        if slstruct == None:
            slstruct = super(Structure,cls).create(**args)

        rc_sites=None
        uc_sites=None
        if slstruct.has_rc_repr:
            rc_sites = slstruct.rc_sites
        if slstruct.has_uc_repr:
            uc_sites = slstruct.uc_sites
        
        if uc_cell == None and rc_cell == None:
            rc_cells = slstruct.get_rc_cells()
            if len(rc_cells>0):
                rc_cell = rc_cells[0]
                            
        new = cls(slstruct.assignments, rc_sites, uc_sites, uc_cell=uc_cell, rc_cell=rc_cell)
        new.add_tags(slstruct.get_tags())
        new.add_refs(slstruct.get_refs())

        return new

    @httk_typed_property(UnitcellSites)
    def uc_sites(self):
        if self._uc_sites == None:
            self._uc_sites, cell = coordgroups_reduced_rc_to_unitcellsites(self.rc_sites.reduced_coordgroups, self.rc_cell.basis, self.hall_symbol)
            self._uc_cell = cell
        return self._uc_sites

    @httk_typed_property(Cell)
    def uc_cell(self):
        if self._uc_cell == None:
            # Trigger filling of cell, which should populate self._uc_cell
            self.fill_cell()
        return self._uc_cell
 
    @property
    def rc_cell(self):
        if self._rc_cell == None:
            # Trigger symmetry finding, which should populate self._rc_cell
            self.find_symetry()
        return self._rc_cell

    @property
    def rc_sites(self):
        if self._rc_sites == None:
            #sys.stderr.write("Warning: need to run symmetry finder. This may take a while.\n")
            newstructure = structure_reduced_uc_to_representative(self)
            self._rc_sites = newstructure.rc_sites
            self._rc_cell = newstructure.rc_cell
        return self._rc_sites

    @property
    def uc_cartesian_occupationscoords(self):
        raise Exception("Structure.uc_cartesian_occupationscoords: not implemented")
        return 

    @property
    def rc_cartesian_coordgroups(self):
        return self.rc_sites.get_cartesian_coordgroups(self.rc_cell)

    @property
    def uc_cartesian_coordgroups(self):
        return self.uc_sites.get_cartesian_coordgroups(self.uc_cell)

    @property
    def rc_cartesian_coords(self):
        return self.rc_sites.get_cartesian_coords(self.rc_cell)

    @property
    def uc_cartesian_coords(self):
        return self.uc_sites.get_cartesian_coords(self.uc_cell)

    @property
    def uc_lengths_and_angles(self):
        return [self.uc_a,self.uc_b,self.uc_c,self.uc_alpha,self.uc_beta,self.uc_gamma]

    @property
    def rc_lengths_and_angles(self):
        return [self.rc_a,self.rc_b,self.rc_c,self.rc_alpha,self.rc_beta,self.rc_gamma]

    @httk_typed_property(float)
    def uc_a(self):
        return self.uc_cell.a

    @httk_typed_property(float)
    def uc_b(self):
        return self.uc_cell.b

    @httk_typed_property(float)
    def uc_c(self):
        return self.uc_cell.c

    @httk_typed_property(float)
    def rc_a(self):
        return self.rc_cell.a

    @httk_typed_property(float)
    def rc_b(self):
        return self.rc_cell.b

    @httk_typed_property(float)
    def rc_c(self):
        return self.rc_cell.c

    @httk_typed_property(float)
    def uc_alpha(self):
        return self.uc_cell.alpha

    @httk_typed_property(float)
    def uc_beta(self):
        return self.uc_cell.beta

    @httk_typed_property(float)
    def uc_gamma(self):
        return self.uc_cell.gamma

    @httk_typed_property(float)
    def rc_alpha(self):
        return self.rc_cell.alpha

    @httk_typed_property(float)
    def rc_beta(self):
        return self.rc_cell.beta

    @httk_typed_property(float)
    def rc_gamma(self):
        return self.rc_cell.gamma

    @property
    def rc_basis(self):
        return self.rc_cell.basis

    @property
    def uc_basis(self):
        return self.uc_cell.basis

    @httk_typed_property(float)
    def uc_volume(self):
        return self.uc_cell.volume

    @httk_typed_property(float)
    def rc_volume(self):
        return self.rc_cell.volume

    @httk_typed_property(int)
    def uc_cell_orientation(self):
        return self.uc_cell.orientation
    
    @httk_typed_property(int)
    def rc_cell_orientation(self):
        return self.rc_cell.orientation

    @httk_typed_property((bool,1,3))
    def pbc(self):
        if self.has_rc_repr:
            return self.rc_sites.pbc
        else:
            return self.uc_sites.pbc

    def build_supercell(self,transformation,max_search_cells=20, max_atoms=1000):

        transformation=FracVector.use(transformation).simplify()
        if transformation.denom != 1:
            raise Exception("Structure.build_supercell requires integer transformation matrix")
        
        old_cell = self.uc_cell
        new_cell = Cell.create(basis=transformation*old_cell.basis)
        conversion_matrix = (old_cell.basis*new_cell.inv).simplify()

        volume_ratio = abs((new_cell.basis.det()/abs(old_cell.basis.det()))).simplify()
        seek_counts = [int((volume_ratio*x).simplify()) for x in self.uc_counts]
        total_seek_counts = sum(seek_counts)
        if total_seek_counts > max_atoms:
            raise Exception("Structure.build_supercell: more than "+str(max_atoms)+" needed. Change limit with max_atoms parameter.")
    
        #if max_search_cells != None and maxvec[0]*maxvec[1]*maxvec[2] > max_search_cells:
        #    raise Exception("Very obtuse angles in cell, to search over all possible lattice vectors will take a very long time. To force, set max_search_cells = None when calling find_prototypeid()")
             
        ### Collect coordinate list of all sites inside the new cell
        coordgroups = self.uc_reduced_coordgroups
        extendedcoordgroups = [[] for x in range(len(coordgroups))]

        if max_search_cells != None:
            max_search = [max_search_cells,max_search_cells,max_search_cells]
        else:
            max_search = None

        for offset in breath_first_idxs(dim=3, end=max_search, negative=True):
            #print "X",offset, seek_counts
            for idx in range(len(coordgroups)):
                coordgroup = coordgroups[idx]
                newcoordgroup = coordgroup+FracVector([offset]*len(coordgroup))
                new_reduced = newcoordgroup*conversion_matrix
                #print "NEW:",FracVector.use(new_reduced).to_floats(),
                new_reduced = [x for x in new_reduced if x[0]>=0 and x[1]>=0 and x[2]>=0 and x[0]<1 and x[1]<1 and x[2]<1]
                extendedcoordgroups[idx] += new_reduced
                c = len(new_reduced)
                seek_counts[idx] -= c
                total_seek_counts-= c
                #print "ADD",str(c)
                if seek_counts[idx] < 0:
                    #print "X",offset, seek_counts
                    raise Exception("Structure.build_supercell safety check error, internal error: too many atoms in supercell.")
            if total_seek_counts == 0:
                break
        else:
            raise Exception("Very obtuse angles in cell, to search over all possible lattice vectors will take a very long time. To force, set max_search_cells = None when calling find_prototypeid()")

        return self.create(uc_reduced_coordgroups=extendedcoordgroups, uc_basis=new_cell.basis, assignments=self.assignments)


    # TODO: The building of supercells should be moved elsewhere and not be part of this class
    def build_supercell_old(self,transformation,max_search_cells=1000):
        ### New basis matrix, note: works in units of old_cell.scale to avoid floating point errors
        #print "BUILD SUPERCELL",self.uc_sites.cell.basis.to_floats(), repetitions

        transformation=FracVector.use(transformation).simplify()
        if transformation.denom != 1:
            raise Exception("Structure.build_supercell requires integer transformation matrix")
        
        old_cell = self.uc_sites.cell.get_normalized()
        new_cell = Cell.create(basis=transformation*old_cell.basis)
        #conversion_matrix = (new_cell.inv*old_cell.basis).T().simplify()
        conversion_matrix = (old_cell.basis*new_cell.inv).T().simplify()

        volume_ratio = (new_cell.basis.det()/abs(old_cell.basis.det())).simplify()

        # Generate the reduced (old cell) coordinates of each corner in the new cell
        # This determines how far we must loop the old cell to cover all these corners  
        nb = new_cell.basis
        corners = FracVector.create([(0,0,0),nb[0],nb[1],nb[2],nb[0]+nb[1],nb[0]+nb[2],nb[1]+nb[2],nb[0]+nb[1]+nb[2]])
        reduced_corners = corners*(old_cell.basis.inv().T())
        
        maxvec = [int(reduced_corners[:,0].max())+2,int(reduced_corners[:,1].max())+2,int(reduced_corners[:,2].max())+2]
        minvec = [int(reduced_corners[:,0].min())-2,int(reduced_corners[:,1].min())-2,int(reduced_corners[:,2].min())-2]
    
        if max_search_cells != None and maxvec[0]*maxvec[1]*maxvec[2] > max_search_cells:
            raise Exception("Very obtuse angles in cell, to search over all possible lattice vectors will take a very long time. To force, set max_search_cells = None when calling find_prototypeid()")
             
        ### Collect coordinate list of all sites inside the new cell
        coordgroups = self.uc_reduced_coordgroups
        extendedcoordgroups = [[] for x in range(len(coordgroups))]
        for idx in range(len(coordgroups)):
            coordgroup = coordgroups[idx]
            for i in range(minvec[0],maxvec[0]):
                for j in range(minvec[1],maxvec[1]):
                    for k in range(minvec[2],maxvec[2]):
                        newcoordgroup = coordgroup+FracVector(((i,j,k),)*len(coordgroup))
                        new_reduced = newcoordgroup*conversion_matrix
                        new_reduced = [x for x in new_reduced if x[0]>=0 and x[1]>=0 and x[2]>=0 and x[0]<1 and x[1]<1 and x[2]<1]
                        extendedcoordgroups[idx] += new_reduced

        # Safety check for avoiding bugs that change the ratio of atoms
        new_counts = [len(x) for x in extendedcoordgroups]
        for i in range(len(self.uc_counts)):
            if volume_ratio*self.uc_counts[i] != new_counts[i]:
                print "Volume ratio:",float(volume_ratio), volume_ratio
                print "Extended coord groups:",FracVector.create(extendedcoordgroups).to_floats()
                print "Old counts:",self.uc_counts,self.assignments.symbols
                print "New counts:",new_counts,self.assignments.symbols
                #raise Exception("Structure.build_supercell safety check failure. Volume changed by factor "+str(float(volume_ratio))+", but atoms in group "+str(i)+" changed by "+str(float(new_counts[i])/float(self.uc_counts[i])))
        
        return self.create(uc_reduced_coordgroups=extendedcoordgroups, basis=new_cell.basis, assignments=self.assignments, cell=self.uc_cell)

    def build_cubic_supercell(self,tolerance=None,max_search_cells=1000):
        if tolerance == None:
            prim_cell = self.uc_cell.basis            
            inv = prim_cell.inv().simplify()
            transformation = (inv*inv.denom).simplify()
        else:            
            maxtol=max(int(FracVector.use(tolerance)),2)
            bestlen = None
            bestortho = None
            besttrans = None
            #TODO: This loop may be possible to do with fewer iterations, since I suppose the only thing that
            #matter is the prime factors?
            for tol in range(1,maxtol):
                prim_cell =  self.uc_cell.basis        
                approxinv = prim_cell.inv().set_denominator(tol).simplify()
                if approxinv[0]==[0,0,0] or approxinv[1]==[0,0,0] or approxinv[2]==[0,0,0]:
                    continue
                transformation = (approxinv*approxinv.denom).simplify()
                cell = Cell.create(transformation*prim_cell)
                ortho = (abs(cell.niggli_matrix[1][0])+abs(cell.niggli_matrix[1][1])+abs(cell.niggli_matrix[1][2])).simplify()
                equallen = abs(cell.niggli_matrix[0][0]-cell.niggli_matrix[0][1]) + abs(cell.niggli_matrix[0][0]-cell.niggli_matrix[0][2]) 
                if ortho==0 and equallen==0:
                    # Already perfectly cubic, use this
                    besttrans=transformation
                    break
                if bestlen == None or not (bestortho < ortho and bestlen < equallen):
                    bestlen=equallen
                    bestortho=ortho
                    besttrans=transformation

            transformation = besttrans
       
        #print "Running transformation with:",transformation     
        return self.build_supercell(transformation,max_search_cells=max_search_cells)

    def build_orthogonal_supercell(self,tolerance=None,max_search_cells=1000,ortho=[True,True,True]):
        transformation = self.orthogonal_supercell_transformation(tolerance,max_search_cells,ortho)
        #print "Running transformation with:",transformation     
        return self.build_supercell(transformation,max_search_cells=max_search_cells)

    def orthogonal_supercell_transformation(self,tolerance=None,max_search_cells=1000,ortho=[True,True,True]):
        # TODO: How to solve for exact orthogonal cell?
        if tolerance == None:
            prim_cell = self.uc_cell.basis         
            print "Starting cell:",prim_cell
            inv = prim_cell.inv().simplify()
            if ortho[0]:
                row0 = (inv[0]/max(inv[0])).simplify()
            else:
                row0 = [1,0,0]
            if ortho[1]:
                row1 = (inv[1]/max(inv[1])).simplify()
            else:
                row1 = [0,1,0]
            if ortho[2]:
                row2 = (inv[2]/max(inv[2])).simplify()
            else:
                row2 = [0,0,1]
            transformation = FracVector.create([row0*row0.denom,row1*row1.denom,row2*row2.denom])
        else:            
            maxtol=max(int(FracVector.use(tolerance)),2)
            bestval = None
            besttrans = None
            for tol in range(1,maxtol):
                prim_cell = self.uc_cell.basis   
                inv = prim_cell.inv().set_denominator(tol).simplify()
                if inv[0]==[0,0,0] or inv[1]==[0,0,0] or inv[2]==[0,0,0]:
                    continue
                absinv = abs(inv)
                if ortho[0]:
                    row0 = (inv[0]/max(absinv[0])).simplify()
                else:
                    row0 = [1,0,0]
                if ortho[1]:
                    row1 = (inv[1]/max(absinv[1])).simplify()
                else:
                    row1 = [0,1,0]
                if ortho[2]:
                    row2 = (inv[2]/max(absinv[2])).simplify()
                else:
                    row2 = [0,0,1]
                transformation = FracVector.create([row0*row0.denom,row1*row1.denom,row2*row2.denom])
                cell = Cell.create(transformation*prim_cell)
                maxval = (abs(cell.niggli_matrix[1][0])+abs(cell.niggli_matrix[1][1])+abs(cell.niggli_matrix[1][2])).simplify()
                if maxval == 0:
                    besttrans=transformation
                    break
                if bestval == None or maxval < bestval:
                    bestval=maxval
                    besttrans=transformation
            transformation = besttrans
       
        return transformation

    def clean(self):        
        rc_sites = self.rc_sites.clean()
        uc_sites = self.uc_sites.clean()
        uc_cell = self.uc_cell.clean()
        rc_cell = self.rc_cell.clean()

        new = self.__class__(self.assignments, rc_sites, uc_sites, uc_cell=uc_cell, rc_cell=rc_cell)
        new.add_tags(self.get_tags())
        new.add_refs(self.get_refs())               
        return new

    def _fill_codependent_data(self):
        self._tags = {}
        self._refs = []
        for x in self._codependent_callbacks:
            x(self)            

    def add_tag(self,tag,val):
        if self._tags == None:
            self._fill_codependent_data()
        new = StructureTag(self,tag,val)
        self._tags[tag]=new
        self._codependent_data += [new]

    def add_tags(self,tags):
        for tag in tags:
            if isinstance(tags,dict):
                tagdata = tags[tag]
            else:
                tagdata = tag
            if isinstance(tagdata,StructureTag):
                self.add_tag(tagdata.tag,tagdata.value)
            else:
                self.add_tag(tag,tagdata)

    def get_tags(self):
        if self._tags == None:
            self._fill_codependent_data()
        return self._tags

    def get_tag(self,tag):
        if self._tags == None:
            self._fill_codependent_data()
        return self._tags[tag]

    def get_refs(self):
        if self._refs == None:
            self._fill_codependent_data()
        return self._refs

    def add_ref(self,ref):        
        if self._refs == None:
            self._fill_codependent_data()
        if isinstance(ref,StructureRef):
            refobj = ref.reference
        else:
            refobj = Reference.use(ref)
        new = StructureRef(self,refobj)
        self._refs += [new]
        self._codependent_data += [new]

    def add_refs(self,refs):
        for ref in refs:
            self.add_ref(ref)



def main():
    print "Test"

#     def httk_typed_property(t):
#         def wrapfactory(func):
#             func.property_type = lambda: t
#             return property(func)
#         return wrapfactory
# 
#     def httk_typed_property_delayed(t):
#         def wrapfactory(func):
#             func.property_type = t
#             return property(func)
#         return wrapfactory
# 
#     def check_returntype(obj,propname):
#         for obj in [obj]+obj.__class__.mro():
#             if propname in obj.__dict__:
#                 return obj.__dict__[propname].fget.property_type()
#         raise AttributeError

#     class Horse:
#         pass
# 
#     class Gurk(object):
#         @httk_typed_property(Horse)
#         def number_seven(self):        
#             return 7
# 
#     test = Gurk()
#     print test.number_seven
#     print httk_typed_property_resolve(test,'number_seven')()
    
    #from httk.core.fracvector import FracVector

    #class StructureGurkPlugin(object):

    #    name = 'gurk'
                
    #    def __init__(self, struct):
    #        self.struct = struct

    #    def print_gurk(self):
    #        print "HERE:",self.struct

    #Structure.add_plugin(StructureGurkPlugin)
    
    #coords = FracVector.create([[2,3,5],[3,5,4],[4,6,7]])
    #cell = FracVector.create([[1,1,0],[1,0,1],[0,1,1]])
    #assignments = [2,5]
    #counts = [2,1]
    #a = Structure.create_from_counts_coords(cell, assignments, counts, coords)
    
    #print(a)
    #a.gurk.print_gurk()    

    #easya = a.to_EasyStructure()
    #print(easya)

class StructureTag(HttkObject):                               
    @httk_typed_init({'structure':Structure,'tag':str,'value':str},index=['structure', 'tag', 'value'],skip=['hexhash'])    
    def __init__(self, structure, tag, value):
        super(StructureTag,self).__init__()
        self.tag = tag
        self.structure = structure
        self.value = value

    def __str__(self):
        return "(Tag) "+self.tag+": "+self.value+""

class StructureRef(HttkObject):
    @httk_typed_init({'structure':Structure,'reference':Reference},index=['structure', 'reference'],skip=['hexhash'])        
    def __init__(self, structure, reference):
        super(StructureRef,self).__init__()
        self.structure = structure
        self.reference = reference

    def __str__(self):
        return str(self.reference)

        
if __name__ == "__main__":
    main()
    
    
#         if isinstance(structure,ScalelessStructure):
#             rc_sites=None
#             uc_sites=None
#             if structure.has_rc_repr:
#                 rc_sites = structure.rc_sites
#             if structure.has_uc_repr:
#                 uc_sites = structure.uc_sites
#             return cls(structure.assignments, rc_sites = rc_sites, uc_sites = uc_sites)
#         
#         if isinstance(spacegroup,Spacegroup):
#             hall_symbol = spacegroup.hall_symbol
#         else:
#             try:
#                 spacegroupobj = Spacegroup.create(spacegroup=spacegroup, hall_symbol=hall_symbol, spacegroupnumber=spacegroupnumber, setting=setting) 
#                 hall_symbol = spacegroupobj.hall_symbol
#             except Exception as spacegroup_exception:
#                 spacegroupobj = None                
#                 hall_symbol = None
# 
#         if isinstance(uc_sites,UnitcellSites):
#             uc_sites = uc_sites
#         if isinstance(uc_sites,Sites):
#             uc_sites = UnitcellSites.use(uc_sites)
#         else:
#             if uc_reduced_coordgroups == None and uc_cartesian_coordgroups == None and \
#                     uc_reduced_coords == None and uc_cartesian_coords == None and \
#                     uc_occupancies != None:
#                     # Structure created by occupationscoords and occupations, this is a slightly tricky representation
#                 if uc_reduced_occupationscoords != None:
#                     assignments, uc_reduced_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(uc_reduced_occupationscoords,uc_occupancies)
#                 elif uc_cartesian_occupationscoords != None:
#                     assignments, uc_cartesian_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(uc_cartesian_occupationscoords,uc_occupancies)
#             
#             if uc_reduced_coordgroups != None or uc_cartesian_coordgroups != None or \
#                     uc_reduced_coords != None or uc_cartesian_coords != None:
# 
#                 if isinstance(uc_cellshape,CellShape):
#                     uc_cellshapeobj = uc_cellshape
#                 else:                        
#                     uc_cellshapeobj = CellShape.create(cellshape=uc_cellshape, basis=uc_basis, metric=uc_metric, 
#                                           niggli_matrix=uc_niggli_matrix, 
#                                           a=uc_a, b=uc_b, c=uc_c, 
#                                           alpha=uc_alpha, beta=uc_beta, gamma=uc_gamma,
#                                           lengths = uc_lengths, angles=uc_angles)
# 
#                 if uc_cartesian_coords != None and uc_cartesian_coordgroups == None:
#                     uc_cartesian_coordgroups = coords_and_counts_to_coordgroups(uc_cartesian_coords, uc_counts)
# 
#                 if uc_cartesian_coordgroups != None and uc_reduced_coordgroups == None:
#                     uc_reduced_coordgroups = coordgroups_cartesian_to_reduced(uc_cartesian_coordgroups,uc_orig_cell)
#                                 
#                 uc_sites = UnitcellSites.create(reduced_coordgroups=uc_reduced_coordgroups, 
#                                                reduced_coords=uc_reduced_coords, 
#                                                counts=uc_counts, 
#                                                cellshape=uc_cellshapeobj, periodicity=periodicity, occupancies=uc_occupancies)
#             else:
#                 uc_sites = None
# 
#         if isinstance(rc_sites,RepresentativeSites):
#             rc_sites = rc_sites
#         if isinstance(rc_sites,Sites):
#             rc_sites = RepresentativeSites.use(rc_sites)
#         else:
#             if rc_reduced_coordgroups == None and rc_cartesian_coordgroups == None and \
#                     rc_reduced_coords == None and rc_cartesian_coords == None and \
#                     rc_occupancies != None:
#                     # Structure created by occupationscoords and occupations, this is a slightly tricky representation
#                 if rc_reduced_occupationscoords != None:     
#                     assignments, rc_reduced_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(rc_reduced_occupationscoords,rc_occupancies)
#                 elif rc_cartesian_occupationscoords != None:
#                     assignments, rc_cartesian_coordgroups = occupations_and_coords_to_assignments_and_coordgroups(rc_cartesian_occupationscoords,rc_occupancies)
# 
#             if rc_reduced_coordgroups != None or rc_cartesian_coordgroups != None or \
#                     rc_reduced_coords != None or rc_cartesian_coords != None:
#                 
#                 if isinstance(rc_cellshape,CellShape):
#                     rc_cellshapeobj = rc_cellshape
#                 else:                        
#                     rc_cellshapeobj = Cell.create(cellshape=rc_cellshape, basis=rc_basis, metric=rc_metric, 
#                                           niggli_matrix=rc_niggli_matrix, 
#                                           a=rc_a, b=rc_b, c=rc_c, 
#                                           alpha=rc_alpha, beta=rc_beta, gamma=rc_gamma,
#                                           lengths = rc_lengths, angles=rc_angles)
#                                     
#                 if rc_cartesian_coords != None and rc_cartesian_coordgroups == None:
#                     rc_cartesian_coordgroups = coords_and_counts_to_coordgroups(rc_cartesian_coords, rc_counts)
# 
#                 if rc_cartesian_coordgroups != None and rc_reduced_coordgroups == None:
#                     rc_reduced_coordgroups = coordgroups_cartesian_to_reduced(rc_cartesian_coordgroups,rc_orig_cell)                
#                                 
#                 rc_sites = RepresentativeSites.create(reduced_coordgroups=rc_reduced_coordgroups, 
#                                                reduced_coords=rc_reduced_coords, 
#                                                counts=rc_counts,
#                                                cellshape=rc_cellshapeobj,hall_symbol=hall_symbol, periodicity=periodicity, wyckoff_symbols=wyckoff_symbols,
#                                                occupancies=rc_occupancies)
#             else:
#                 rc_sites = None
#             
#         if rc_sites == None and uc_sites == None:
#             raise Exception("Structure.create: neither representative, nor primcell, sites specification valid.")
# 
#         if assignments != None:
#             if isinstance(assignments,Assignments):
#                 assignments = assignments
#             else:
#                 assignments = Assignments.create(assignments=assignments)
# 
#         if uc_sites == None and hall_symbol == None:
#             raise Exception("Structure.create: cannot create structure from only representative sites with no spacegroup information. Error was:"+str(spacegroup_exception))
# 
#         new = cls(assignments, rc_sites, uc_sites)
#         if tags!=None:
#             new.add_tags(tags)
#         if refs!=None:
#             new.add_refs(refs)               
#         return new
