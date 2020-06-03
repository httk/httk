import httk, httk.db, shlex
from httk.atomistic import Compound
from httk.atomistic.compound import CompoundName

def execute(compound,global_data,**kargs):

    search = global_data['store'].searcher()
    search_compound = search.variable(Compound)
    search.add(search_compound.element_wyckoff_sequence == compound)

    search.output(search_compound, 'compound')

    compound = list(search)[0][0][0]
    tags = compound.get_tags()
    tags = [{'tag':tags[tag].tag , 'value':tags[tag].value} for tag in tags]

    names = ", ".join([x.name for x in compound.get_names()])

    output = {'id':compound.element_wyckoff_sequence,
              'formula':compound.formula,
              'anonymous_formula':compound.anonymous_formula,
              'spacegroup_number':compound.spacegroup_number,
              'tags':tags,
              'names':names}

    return output
