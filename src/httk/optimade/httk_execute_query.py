#!/usr/bin/env python
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2020 Rickard Armiento
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

from httk.optimade.optimade_filter_to_httk import optimade_filter_to_httk

_field_map = {
    'Structure': {
        'type': lambda x,y: "structures",
        'id': lambda x,y: x.db.sid,
        'structure_features': lambda x,y: [],
        'lattice_vectors': lambda x,y: x.uc_basis.to_floats(),
        'elements': lambda x,y: sorted(list(set(x.formula_symbols))),
        'nelements': lambda x,y: x.number_of_elements,
        'chemical_formula_descriptive': lambda x,y: x.formula,
        'dimension_types': lambda x,y: [1 if el else 0 for el in [True, True, True]],
        'nperiodic_dimensions': lambda x,y: list([True, True, True]).count(True),
        #TODO: Sort out what is wrong with x.pbc
    }
}

class HttkResults(object):
    def __init__(self, searcher, response_fields, unknown_response_fields, limit, offset):
        self.searcher = searcher
        self.cur = iter(searcher)
        self.limit = limit
        self.response_fields = response_fields
        self.unknown_response_fields = unknown_response_fields
        self._count = 0
        self.offset = offset
        self.more_data_available = True

    def count(self):
        return self.searcher.count()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            while self.offset > 0:
                next(self.cur)
                self.offset -= 1
            row = next(self.cur)[0][0]
            result = dict()
            for field in self.unknown_response_fields:
                result[field] = None
            for field in self.response_fields:
                if field in _field_map[type(row).__name__]:
                    result[field] = _field_map[type(row).__name__][field](row, field)
                elif field.startswith(httk_recognized_prefixes):
                    for prefix in httk_recognized_prefixes:
                        if field.startswith(prefix):
                            field = field[len(prefix):]
                            break
                    result[field]=getattr(row,field)
                else:
                    raise Exception("Unexpected field requested:"+str(field))
        except StopIteration:
            self.more_data_available = False
            self.cur.close()
            self.cur = None
            raise StopIteration

        if self.limit is not None and self._count == self.limit:
            self.more_data_available = True
            self.cur.close()
            self.cur = None
            raise StopIteration

        self._count += 1

        return result

    def __del__(self):
        if self.cur is not None:
            self.cur.close()

    # Python 2 compability
    def next(self):
        return self.__next__()

def httk_execute_query(store, entries, response_fields, unknown_response_fields, response_limit, response_offset, optimade_filter_ast=None, debug=False):

    searcher = store.searcher()

    searcher =  optimade_filter_to_httk(optimade_filter_ast, entries, searcher)

    return HttkResults(searcher, response_fields, unknown_response_fields, response_limit, response_offset)

if __name__ == "__main__":

    import os, sys
    from pprint import pprint
    from parse_optimade_filter import parse_optimade_filter

    import httk, httk.db

    backend = httk.db.backend.Sqlite('../../../Tutorial/tutorial_data/tutorial.sqlite')
    store = httk.db.store.SqlStore(backend)

    # This represents the query being received (later to be received via a web URL query)
    tables = ["structures"]
    response_fields = ["id", "formula", "elements"]

    if len(sys.argv) >= 2:
        input_string = sys.argv[1]
    else:
        input_string ='nelements=3'
        #input_string ='elements HAS ALL "Ga","Ti" AND (nelements=3 OR nelements=2)'

    filter_ast = parse_optimade_filter(input_string, verbosity=0)

    sys.stdout.write("==== FILTER STRING PARSE RESULT:\n")
    pprint(filter_ast)
    sys.stdout.write("====\n")

    filter_ast = parse_optimade_filter(input_string)

    response_limit = 50
    response_offset = 0

    result = httk_execute_query(store, tables, response_fields, response_limit, response_offset, filter_ast, debug=True)

    print("==== END RESULT")
    for l in result:
        print(l)
    print("===============")

    #print("==== END RESULT")
    #for match, header in result:
    #    print(match[0].formula)
    #print("===============")
