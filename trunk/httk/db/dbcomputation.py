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

import time, datetime

import httk
from httk.core import *
from httk.core.htdata import periodictable
from storable import Storable, storable_types
from dbstructure import DbStructure, DbReference

class DbSignatureKey(Storable):
    """
    Class for storing a prototype, i.e., a crystal structure sans atomic assignments and the overall volume
    """   
    types = storable_types('SignatureKey',('keyid',str),('keydata',str),('description',str),index=["keyid"])
    
    def __init__(self, codename, version, reference, types=None, store=None):
        """
        """                
        # Storable init        
        self.storable_init(store,codename=codename, version=version, reference=reference)

class DbSignature(Storable):
    """
    Class for storing a prototype, i.e., a crystal structure sans atomic assignments and the overall volume
    """   
    types = storable_types('Signature',('signature_data',str),('key',DbSignatureKey), index=["key"])
    
    def __init__(self, codename, version, reference, types=None, store=None):
        """
        """                
        # Storable init        
        self.storable_init(store,codename=codename, version=version, reference=reference)

class DbCode(Storable):
    """
    Class for storing a prototype, i.e., a crystal structure sans atomic assignments and the overall volume
    """   
    types = storable_types('Code',('name',str),('version',str),index=["name","version"])
    
    def __init__(self, name, version, types=None, store=None):
        """
        """                
        # Storable init        
        self.storable_init(store,name=name, version=version)

class DbCodeReference(Storable):
    """
    Class for storing atomic assignments
    
    There is a point with this being its own table, rather than inlining site_assignmnets: now extensions can refer to one
    specific MultiAssignment by ID. 
    """
    types = storable_types('CodeReference', ('code',DbCode), ('reference',DbReference),index=['code'])
    
    def __init__(self, code, reference, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store, code=code, reference=reference)

    @classmethod
    def merge(cls, code, refs, store=None, reuse=False):
        outresults = []
        refs = [DbReference.use(x,reuse=True, store=store) for x in refs]
        #code = DbCode.use(code,reuse=True, store=store)
        for ref in refs:
            search = store.searcher()
            p = DbCodeReference.variable(search,'p')
            search.add(p.code == code)
            search.add(p.reference == ref)
            search.output(p,'object')
            results = list(search)
            if len(results) > 0:
                result = results[0]
            else:
                result = DbCodeReference(code, ref, store=store)
            
            outresults.append(result)
                       
        return outresults

class DbComputation(Storable):
    """
    Class for storing a prototype, i.e., a crystal structure sans atomic assignments and the overall volume
    """   
    
    def __init__(self, computation_date, added_date, compound, code, manifest_hexhash, input_hexhash, related, tags, signature, store=None):
        """
        """                
        # Storable init        
        self.storable_init(store,computation_date=computation_date, added_date=added_date, 
                           compound=compound, code=code, manifest_hexhash=manifest_hexhash, input_hexhash=input_hexhash, 
                           related=related, tags=tags, signature=signature)

    @classmethod
    def create(cls,date=None,compound=None, code=None, manifest_hexhash=None, input_hexhash=None, related=None, tags=None, signature=None, store=None):
        added_date = datetime.datetime.today().isoformat()
        if compound != None:
            compound = httk.db.DbCompound.use(compound, store=store)
        if date == None:
            date = added_date
        try:
            date.isoformat()
        except AttributeError as e:
            pass
        #if refs != None:
        #    refs = DbReferenceList.use(refs,reuse=True,store=store)
        return DbComputation(date,added_date,compound,code,manifest_hexhash, input_hexhash, related, tuple(tags.items()), signature, store)

    @classmethod
    def use(cls, old, store=None, reuse=False):
        if isinstance(old,DbComputation) and (store == None or store == old.store.store):
            return old    
        else:
            return DbComputation(old.computation_date, old.added_date, old.compound, old.code, old.manifest_hexhash, old.input_hexhash, old.related, old.tags, old.signature, old.refs, store=store)


class DbComputationReference(Storable):
    """
    Class for storing atomic assignments
    
    There is a point with this being its own table, rather than inlining site_assignmnets: now extensions can refer to one
    specific MultiAssignment by ID. 
    """
    types = storable_types('ComputationReference', ('computation',DbComputation), ('reference',DbReference), index=['computation'])
    
    def __init__(self, computation, reference, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store, computation=computation, reference=reference)

    @classmethod
    def merge(cls, computation, refs, store=None, reuse=False):
        outresults = []
        refs = [DbReference.use(x,reuse=True, store=store) for x in refs]
        compound = DbComputation.use(computation,reuse=True, store=store)
        for ref in refs:
            search = store.searcher()
            p = DbComputationReference.variable(search,'p')
            search.add(p.computation == computation)
            search.add(p.reference == ref)
            search.output(p,'object')
            results = list(search)
            if len(results) > 0:
                result = results[0]
            else:
                result = DbComputationReference(compound, ref, store=store)
            
            outresults.append(result)
                       
        return outresults


class DbCompound(Storable):
    """
    """   
    types = storable_types('Compound', ('hexhash',str), ('source_computation',DbComputation), ('name',str),
                           ('names',[str]),('basic_structure',DbStructure), ('formula',str), ('abstract_formula',str), ('formula_parts',[('element',int),('count',int)]),
                           ('element_count',int),('spacegroup_number',int),
                           ('tags',[('key',str),('val',str)]), 
                           ('extended',int), ('extensions',[str]), ('periodicity',int), 
                           index=['hexhash','source_computation','name','basic_structure','formula','abstract_formula',
                                  'element_count','spacegroup_number','extended','periodicity','disordered','periodicity'])
    
    def __init__(self, hexhash, source_computation, name, names, basic_structure, formula, 
                 abstract_formula, formula_parts, element_count,  
                 spacegroup_number, tags, extended, extensions, periodicity, store=None):
        """
        """                
        
        # Storable init        
        self.storable_init(store, hexhash=hexhash, source_computation=source_computation, name=name, names=names, basic_structure=basic_structure, formula=formula, 
                           formula_parts=formula_parts, abstract_formula=abstract_formula, element_count=element_count, 
                 spacegroup_number=spacegroup_number, tags=tags, extended=extended, extensions=extensions, periodicity=periodicity)
    
    @classmethod
    def use(cls, old, store=None, reuse=False):
        if isinstance(old,DbCompound) and (store == None or store == old.store.store):
            return old    
        else:
            old = Compound.use(old)
            
            hexhash = old.hexhash
            if reuse and store != None:
                p = DbCompound.find_one(store, 'hexhash', hexhash)                
                if p != None:
                    return p
            
            basic_structure = DbStructure.use(old.basic_structure,store=store, reuse=reuse)

            source_computation = DbComputation.use(old.source_computation,store=store, reuse=reuse)

            if old.extended:
                extended = 1
            else:
                extended = 0

            if old.extensions == []:
                extensions = None
            else:
                extensions = old.extensions

            tags = tuple(old.tags.items())

            formula_parts = [(x[0],float(x[1]),(x[1]*1000000000).floor()) for x in old.formula_parts.items()]

            test = Compound.create(source_computation,basic_structure)
            hexhash = test.hexhash
            if reuse and store != None:
                p = DbCompound.find_one(store, 'hexhash', hexhash)                
                if p != None:
                    return p

            #if old.refs != None:
            #    old.refs = DbReferenceList.use(old.refs,reuse=True,store=store)
               
            dbcompound = DbCompound(hexhash, source_computation, old.name, old.names, basic_structure, 
                              old.formula, old.abstract_formula, formula_parts, 
                              old.element_count, 
                              old.spacegroup_number, tags, extended, extensions, periodicity=0, store=store)

            #newrefs = DbCompoundReference.merge(dbcompound, basic_structure.refs, store=store, reuse=True)

            return dbcompound

# For self-referential type declarations the type variable must be set after class declaration.
DbComputation.types = storable_types('Computation', ('computation_date',str), ('added_date',str), 
                           ('compound',DbCompound), ('code',DbCode), ('manifest_hexhash',str), ('input_hexhash',str),
                           ('related',[DbComputation]),('tags',[('key',str),('val',str)]),
                           ('signature',[DbSignature]),index=['computation_date','structure','code'])

class DbCompoundReference(Storable):
    """
    Class for storing atomic assignments
    
    There is a point with this being its own table, rather than inside the Compound table: now we can add references after a DbCompound is already in place.
    """
    types = storable_types('CompoundReference', ('compound',DbCompound), ('reference',DbReference), index=['compound'])
    
    def __init__(self, compound, reference, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store, compound=compound, reference=reference)

    @classmethod
    def merge(cls, compound, refs, store=None, reuse=False):
        outresults = []
        refs = [DbReference.use(x,reuse=True, store=store) for x in refs]
        compound = DbCompound.use(compound,reuse=True, store=store)
        for ref in refs:
            search = store.searcher()
            p = DbCompoundReference.variable(search,'p')
            search.add(p.compound == compound)
            search.add(p.reference == ref)
            search.output(p,'object')
            results = list(search)
            if len(results) > 0:
                result = results[0]
            else:
                result = DbCompoundReference(compound, ref, store=store)
            
            outresults.append(result)
                       
        return outresults

class DbCompoundDuplicateStructures(Storable):
    """
    Class for keeping track of duplicate structures for a Compound
    
    There is a point with this being its own table, rather than inside the Compound table: now we can add duplicates after a DbCompound is already in place.

    """
    types = storable_types('CompoundDuplicateStructures', ('compound',DbCompound), ('structure',DbStructure), index=['compound','structure'])
    
    def __init__(self, compound, struct, types=None, store=None):
        """
        """
        # Storable init        
        self.storable_init(store, compound=compound, structure=struct)

    @classmethod
    def merge(cls, compound, structures, store=None, reuse=False):
        outresults = []
        structures = [DbStructure.use(x,reuse=True, store=store) for x in structures]
        dbcompound = DbCompound.use(compound,reuse=True, store=store)
        for dbstructure in structures:
            search = store.searcher()
            p = DbCompoundDuplicateStructures.variable(search,'p')
            search.add(p.compound == dbcompound)
            search.add(p.structure == dbstructure)
            search.output(p,'object')
            results = list(search)
            if len(results) > 0:
                result = results[0]
            else:
                result = DbCompoundDuplicateStructures(dbcompound, dbstructure, store=store)
            
            outresults.append(result)
                       
        return outresults
