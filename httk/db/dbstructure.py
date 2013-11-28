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

from httk.core import *
from httk.core.structureutils import *
from httk.core.htdata import periodictable
from storable import Storable, storable_types
from dbfracvector import DbIntTriple

class DbReference(Storable):
    """
    Class for storing atomic assignments
    
    There is a point with this being its own table, rather than inlining site_assignmnets: now extensions can refer to one
    specific MultiAssignment by ID. 
    """
    types = storable_types('Reference', ('reference',str), index=["reference"])
    
    def __init__(self, reference, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store,reference=reference)

    @classmethod
    def use(cls, old, store=None, reuse=False):
        if isinstance(old,DbReference) and (store == None or store == old.store.store):
            return old    
        else:
            if reuse and store != None:
                p = DbReference.find_one(store, 'reference', old)                
                if p != None:
                    return p              
            return DbReference(old, store=store)


class DbPrototype(Storable):
    """
    Class for storing a prototype, i.e., a crystal structure sans atomic assignments and the overall volume
    """   

    types = storable_types('Prototype', ('hexhash',str),('prototype_formula',str),('site_count',int),
                           ('counts',[int]), ('coords_int_g',DbIntTriple), ('cell_int_g',DbIntTriple),
                           ('periodicity',int),
                           ('nonequiv_atoms_in_cell',int), ('spacegroup_number',int), 
                           ('setting',int), ('hm_symbol',str), ('hall_symbol',str), 
                           index=['hexhash','prototype_formula','site_count','periodicity','nonequiv_atoms_in_cell','spacegroup_number','setting','hm_symbol','hall_symbol']) 

    def __init__(self, hexhash, prototype_formula, site_count, counts, coords_int_g, cell_int_g,  
                 periodicity, nonequiv_atoms_in_cell, spacegroup_number, setting, hm_symbol, hall_symbol, types=None, store=None):
        """
        """                        
        # Storable init
        self.storable_init(store,hexhash=hexhash, prototype_formula=prototype_formula, site_count=site_count, counts=counts, 
                           coords_int_g=coords_int_g, cell_int_g=cell_int_g,
                           periodicity=periodicity, 
                           nonequiv_atoms_in_cell=nonequiv_atoms_in_cell, spacegroup_number=spacegroup_number,
                           setting=setting, hm_symbol=hm_symbol, hall_symbol=hall_symbol)

    @classmethod
    def use(cls, old, store=None, reuse=False):
        if isinstance(old,DbPrototype) and (store == None or store == old.store.store):
            return old    
        else:
            hexhash = old.hexhash

            if reuse and store != None:
                p = DbPrototype.find_one(store, 'hexhash', hexhash)                
                if p != None:
                    return p                

            cell_int_g = DbIntTriple.use(old.cell,store=store) 
            coords_int_g = DbIntTriple.use(old.coords,store=store) 
                            
            #dbprototype = DbPrototype(hexhash, old.prototype_formula, old.element_count, old.counts, coords_exact, cell_exact, 
            #                        old.coords, old.cell, old.periodicity, sum(old.counts), 
            #                        nonequiv_atoms_in_cell, spacegroup_number, setting, hm_symbol, hall_symbol, store=store)

            #hexhash_prototype = Prototype.create(cell=cell_int_g.to_fracvector(), coords=coords_int_g.to_fracvector(), periodicity=old.periodicity)
            #hexhash = hexhash_prototype.hexhash

            #if reuse and store != None:
            #    p = DbPrototype.find_one(store, 'hexhash', hexhash)                
            #    if p != None:
            #        return p                

            #if hexhash_prototype.meta_prototype == hexhash_prototype:
            #    db_meta_prototype = None
            #else:
            #    db_meta_prototype = DbPrototype.use(hexhash_prototype.meta_prototype, store=store, reuse=reuse)

            #refs = DbReferenceList.use(old.refs,reuse=True,store=store)

            protoformula = prototype_formula(old)
            hall_symbol = old.hall_symbol
            hm_symbol = htdata.spacegroups.spacegroup_get_hm(hall_symbol)
            spacegroup_number, setting = htdata.spacegroups.spacegroup_get_number_and_setting(hall_symbol)

            return DbPrototype(hexhash, protoformula, len(old.counts), old.counts, coords_int_g, cell_int_g,
                               old.periodicity, sum(old.counts), spacegroup_number, setting, 
                               hm_symbol, hall_symbol, store=store)
    

class DbPrototypeReference(Storable):
    """
    Class for storing atomic assignments
    
    There is a point with this being its own table, rather than inlining site_assignmnets: now extensions can refer to one
    specific MultiAssignment by ID. 
    """
    types = storable_types('PrototypeReference', ('prototype',DbPrototype), ('reference',DbReference), index=['prototype'])
    
    def __init__(self, prototype, reference, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store, prototype=prototype, reference=reference)

    @classmethod
    def merge(cls, prototype, refs, store=None, reuse=False):
        if refs == None:
            return None
        outresults = []
        refs = [DbReference.use(x,reuse=True, store=store) for x in refs]
        prototype = DbPrototype.use(prototype,reuse=True, store=store)
        for ref in refs:
            search = store.searcher()
            p = DbPrototypeReference.variable(search,'p')
            search.add(p.prototype == prototype)
            search.add(p.reference == ref)
            search.output(p,'object')
            results = list(search)
            if len(results) > 0:
                result = results[0]
            else:
                result = DbPrototypeReference(prototype, ref, store=store)
            
            outresults.append(result)
                       
        return outresults
        
        
class DbMultiAssignment(Storable):
    """
    Class for storing atomic assignments
    
    There is a point with this being its own table, rather than inlining site_assignmnets: now extensions can refer to one
    specific MultiAssignment by ID. 
    """
    types = storable_types('MultiAssignment', ('site_assignments',[('number',int),('ratio',float),('int_g_ratio',int)]))
    
    def __init__(self, site_assignments, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store,site_assignments=site_assignments)

    @classmethod
    def use(cls, old, store=None, reuse=False):
        if isinstance(old,DbMultiAssignment) and (store == None or store == old.store.store):
            return old    
        else:
            site_assignments = [(x[0],float(x[1]),((x[1]*1000000000).limit_resolution(1)).floor(),) for x in old]          
            return DbMultiAssignment(site_assignments, store=store)


class DbStructure(Storable):
    """
    Non-periodic or periodic arrangement of atoms in space. 
    """   
    types = storable_types('Structure',
                           ('hexhash',str),('formula',str), ('element_count',int),
                           ('formula_parts',[('symbol',str),('number',int),('float_count',float),('count_int_g',int)]), 
                           ('abstract_formula',str),('atoms_in_cell',int),
                           ('sgprototype',DbPrototype),('sgprototype_assignments',[int]),('sgprototype_multi_assignments',[DbMultiAssignment]),
                           ('float_cell',(0,3)),('float_coords',(0,3)), 
                           ('counts',[int]), ('assignments',[int]), ('multi_assignments',[DbMultiAssignment]),
                           ('extended',int), ('extension_list',[str]), 
                           ('periodicity',int), 
                           ('float_volume',float),('volume_int_g',int),
                           ('tags',[('key',str),('val',str)]),index=['hexhash','formula','element_count',
                            'abstract_formula','atoms_in_cell','extended','periodicity','float_volume'])
    
    def __init__(self, hexhash, formula, element_count, formula_parts, abstract_formula, atoms_in_cell, sgprototype, sgprototype_assignments, sgprototype_multi_assignments, float_cell, 
                 float_coords, counts, assignments,multi_assignments,
                 extended, extension_list, periodicity, float_volume, volume_int_g, tags, types=None, store=None):
        """
        """                  
        self.storable_init(store,hexhash=hexhash, formula=formula, element_count=element_count, formula_parts=formula_parts, abstract_formula=abstract_formula, atoms_in_cell=atoms_in_cell,
                           sgprototype=sgprototype,sgprototype_assignments=sgprototype_assignments, sgprototype_multi_assignments=sgprototype_multi_assignments, 
                           float_cell=float_cell, 
                           float_coords=float_coords, counts=counts, assignments=assignments,multi_assignments=multi_assignments,
                           extended=extended, extension_list=extension_list, periodicity=periodicity,
                           float_volume=float_volume, volume_int_g = volume_int_g, tags=tags)

    @property
    def cell(self):
        newcell = self.sgprototype.cell_int_g.to_fracvector()
        return newcell

    def to_Structure(self):
        # TODO: WARNING, presently this routine does not handle multi_assignments correctly. 
        unique_coords = self.sgprototype.coords_int_g.to_fracvector()
        unique_counts = self.sgprototype.counts
        structure = Structure.create(cell=self.cell, coords = unique_coords, counts=unique_counts, assignments=self.sgprototype_assignments, volume = self.vol, hall_symbol = self.sgprototype.hall_symbol)
        # TODO: I'm not sure if this is a good idea - reading the non-accurate floatingpoint data from the database into the p1structure, 
        # or if it eventually is better to just re-generate it via our Structure implementation. However, *presently* the ASE 
        # structure -> p1structure routines have major problems actually doing this conversion correctly for all inputs, so *presently*
        # I think this is the best we can do.
        p1structure = Structure.create(cell=self.cell, coords = self.float_coords, counts=self.counts, assignments=self.assignments, volume = self.vol, hall_symbol = 'P 1')
        structure.set_p1structure(p1structure)
        return structure

        #return Structure(cell = self.cell, coordgroups=self.coordgroups, spacegroup=self.hall_symbol)

    #@property
    #def coordgroups(self):
    #    return self._to_Structure().coordgroups
    #    unique_coords = self.sgprototype.coords_int_g.to_fracvector()
    #    unique_counts = self.sgprototype.counts
    #    sgstructure = Structure.create(cell=self.cell, coords = unique_coords, counts=unique_counts, assignments=self.sgprototype_assignments, volume = self.vol, hall_symbol = self.sgprototype.hall_symbol)
    #    structure = sgstructure.to_structure()
        # TODO: this is sort of a debug thing, lets verify that the coordinates are the same, and raise an exception if they are not
        #float_coords = FracVector.create(self.float_coords)
        #if len(float_coords) != len(structure.coords):
        #    raise Exception("Data consistency error, sgprototype -> structure conversion gives different number of coordinates than stored for structure, "+str(len(float_coords))+" vs "+str(len(structure.coords)))
        
        #for i in range(len(float_coords)):
        #    if(float_coords[i]-structure.coords[i]).lengthsqr().to_float()>1e-10:
        #        raise Exception("Data consistency error, sgprototype -> structure conversion gives different coordinates than stored for structure.")
        #for coord in structure.coords:
        #    print coord 
        #
        #return structure.coordgroups

    @property
    def vol(self):
        return FracVector.create(self.volume_int_g,1000000000)

    #@property
    #def sgstructure(self):
    #    unique_coords = self.sgprototype.coords_int_g.to_fracvector()
    #    unique_counts = self.sgprototype.counts        
    #    return SgStructure.create(cell=self.cell, coords = unique_coords, counts=unique_counts, assignments=self.sgprototype_assignments, volume = self.vol, hall_symbol = self.sgprototype.hall_symbol)
        
    @classmethod
    def use(cls, old, store=None, reuse=False):
        """
        reuse: set to True to search and find an old structure that is equivalent to the current structure, rather than creating a new one
        """
        if isinstance(old,DbStructure) and (store == None or store == old.store.store):
            return old
        else:
            hexhash = old.hexhash
            if reuse and store != None:
                p = DbStructure.find_one(store, 'hexhash', hexhash)
                if p != None:
                    return p

            old = Structure.use(old)
        
            tag_list = tuple(old.tags.items())

            #try:
            #    sgstruct = SgStructure.use(old)
            #    sgprototype = Prototype(old.cell, sgstruct.nonequiv.counts, sgstruct.nonequiv.coords,refs=sgstruct.refs, sgstruct=sgstruct)                        
            #except Exception as e:
            #    raise Exception("Could not determine spacegroup, etc. due to error:"+str(e))
            #    #prototype = Prototype(old.cell, old.counts, old.coords)       
                 
            dbsgprototype = DbPrototype.use(old.sgprototype, store=store, reuse=reuse)
            DbPrototypeReference.merge(dbsgprototype,old.refs, store=store, reuse=False)
            prototype_assignments = old.sgassignments

            #cell_exact = DbIntTriple.use(old.cell,store=store) 
            #coords_exact = DbIntTriple.use(old.coords,store=store) 

            #dbprototype = DbPrototype(hexhash, old.prototype_formula, old.element_count, old.counts, coords_exact, cell_exact, 
            #                        old.coords, old.cell, old.periodicity, sum(old.counts), 
            #                        nonequiv_atoms_in_cell, spacegroup_number, setting, hm_symbol, hall_symbol, store=store)

            volume_int_g = (old.volume*1000000000).floor()

            formula_parts = old.normalized_formula_parts
                 
            formula_parts_list = [(x[0],periodictable.atomic_number(x[0]),float(x[1]),(x[1]*1000000000).floor()) for x in formula_parts.items()]
            #formula_parts = []

            # Make sure hexhash is the same as you would get if you read back the structure that is being stored         
            
            #print "WEERDS:",self.coordgroups,self.multi_assignments
            #TODO: Think about whether this is needed or not!  
            #hexhash_struct = Structure.create(cell=dbsgprototype.cell_int_g.to_fracvector(),coords=dbsgprototype.coords_int_g.to_fracvector(), volume=FracVector.create(volume_int_g,1000000000),counts=old.counts,assignments=old.multi_assignments,hall_symbol=sgstruct.hall_symbol)
            #hexhash = hexhash_struct.hexhash

            #if reuse and store != None:
            #    p = DbStructure.find_one(store, 'hexhash', hexhash)
            #    if p != None:                    
            #        # seems there is a risk to leak database entries for prototype and assignments here, but
            #        # if this structure really has been added before, the db object creation should have returned
            #        # already existing rows. 
            #        return p
                
            dbmass = []     
            for site_assignment in old.p1structure.multi_assignments:
                dbmass.append(DbMultiAssignment.use(site_assignment,store=store))

            dbprotomass = []
            for site_assignment in old.multi_assignments:
                dbprotomass.append(DbMultiAssignment.use(site_assignment,store=store))
            
            createdstructure=DbStructure(hexhash, old.formula, old.element_count, formula_parts_list, old.abstract_formula, old.N, dbsgprototype, 
                 prototype_assignments, dbprotomass, old.cell.to_floats(), 
                 old.p1coords.to_floats(), old.p1counts, old.p1assignments, dbmass,
                 old.extended, list(old.extensions), old.sgprototype.periodicity, float(old.volume), volume_int_g, tag_list, store=store)

            newrefs = DbStructureReference.merge(createdstructure, old.refs, store=store, reuse=True)
            
            return createdstructure;
            
    @classmethod
    def create(cls, **keys):
        store = keys.pop('store', None)
        reuse = keys.pop('reuse', False)
        struct = Structure.create(**keys)
        return cls.use(struct,store=store,reuse=reuse)


class DbStructureReference(Storable):
    """
    Class for storing atomic assignments
    
    There is a point with this being its own table, rather than inlining site_assignmnets: now extensions can refer to one
    specific MultiAssignment by ID. 
    """
    types = storable_types('StructureReference', ('structure',DbStructure), ('reference',DbReference),index=['structure'])
    
    def __init__(self, structure, reference, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store, structure=structure, reference=reference)

    @classmethod
    def merge(cls, structure, refs, store=None, reuse=False):
        if refs == None:
            return None
        outresults = []        
        refs = [DbReference.use(x,reuse=True, store=store) for x in refs]
        structure = DbStructure.use(structure,reuse=True, store=store)
        for ref in refs:
            search = store.searcher()
            p = DbStructureReference.variable(search,'p')
            search.add(p.structure == structure)
            search.add(p.reference == ref)
            search.output(p,'object')
            results = list(search)
            if len(results) > 0:
                result = results[0]
            else:
                result = DbStructureReference(structure, ref, store=store)
            
            outresults.append(result)
                       
        return outresults


class DbStructureExtensionIsotope(Storable):
    """
    Class for storing atomic assignments
    """
    types = storable_types('StructureExtensionDisordered', ('referenced_assignment',DbMultiAssignment), 
                           ('symbol',int),('number',int),('protons',int))
    
    def __init__(self, hexhash, assignments, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store,hexhash=hexhash, assignments=assignments)

    @classmethod
    def use(cls, old, store=None, reuse=False):
        if isinstance(old,DbStructureExtensionIsotope) and (store == None or store == old.store.store):
            return old    
        else:
            hexhash = old.hexhash
            if reuse and store != None:
                p = DbStructureExtensionIsotope.find_one(store, 'hexhash', hexhash)                
                if p != None:
                    return p                

            assignments = [(x[0],x[1],float(x[2]),((x[2]*1000000000).limit_resolution(1)).floor(),) for x in old.assignments]

            hexhash_assingmnets = AssignmentMap.create(assignments=assignments)
            hexhash = hexhash_assingmnets.hexhash
            if reuse and store != None:
                p = DbStructureExtensionIsotope.find_one(store, 'hexhash', hexhash)                
                if p != None:
                    return p                
            
            return DbStructureExtensionIsotope(hexhash, assignments, store=store)


