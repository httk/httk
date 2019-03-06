import httk, httk.db, shlex
from httk.atomistic import Compound
from httk.atomistic.compound import CompoundName

def execute(q,global_data,**kargs):
    output = []

    parts = shlex.split(q);

    search = global_data['store'].searcher()
    search_compound = search.variable(Compound)

    
    # TODO: this should work: 
    # search_compound_tag = search.variable(CompoundTag,parent=search_compound, subkey='compound')
    search_compound_name = search.variable(CompoundName,parent=search_compound, parentkey='Compound_id', subkey='compound_Compound_sid')

    #search.add(search_compound_tag.compound == search_compound)
    
    for part in parts:
        criterion = search_compound_name.name.like('%'+part+'%')
        criterion = criterion or search_compound.formula_symbols.is_in(part)        
        search.add(criterion)
    search.output(search_compound, 'compound')

    i = 0    
    for match, header in list(search):
        compound = match[0]
        tags = compound.get_tags()
        #names = []
        #if 'name' in tags:
        #    names += [tags['name'].value]
        #if 'names' in tags:
        #    names += [tags['names'].value]            
        #names = ' '.join(names)

        names = ", ".join([x.name for x in compound.get_names()])  
        
        i += 1     
        output += [{'index':i,
                    'id':compound.element_wyckoff_sequence, 
                    'formula':compound.formula, 
                    'anonymous_formula':compound.anonymous_formula,
                    'spacegroup':compound.spacegroup_number, 
                    'names':names}]
    
    return output
