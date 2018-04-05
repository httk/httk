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
Basic help functions
"""
from fractions import Fraction

def int_to_anonymous_symbol(i):
    bigletters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    smalletters = "abcdefghijklmnopqrstuvwxyz"
    if i <= 25:
        return bigletters[i]
    high = int(i/26)-1
    low = i % 26
    return bigletters[high]+smalletters[low]


def anonymous_symbol_to_int(symb):
    bigletters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    smalletters = "abcdefghijklmnopqrstuvwxyz"
    s = 0
    N = len(symb)
    for i in range(1, N+1):
        if i < N:
            s += 26**(i-1)*(smalletters.index(symb[N-i])+1)
        else:
            s += 26**(i-1)*(bigletters.index(symb[N-i])+1)
    return s-1


def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


import re, errno, os, itertools, sys, tempfile, shutil, collections
from ioadapters import IoAdapterFileReader


def is_unary(e):
    if isinstance(e, str):
        return True
    try:
        dummy = iter(e)
        return False
    except TypeError:
        return True


def flatten(l):
    try:
        flattened = l.flatten()
    except Exception:
        for el in l:
            if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
                for sub in flatten(el):
                    yield sub
            else:
                yield el
        return
    for el in flattened:
        yield el


def parse_parexpr(string):
    """Generate parenthesized contents in string as pairs (level, contents)."""
    stack = []
    for i, c in enumerate(string):
        if c == '(':
            stack.append(i)
        elif c == ')' and stack:
            start = stack.pop()
            yield (len(stack), string[start + 1: i])


# Create and destroy temporary directories in a very safe way
def create_tmpdir():
    return tempfile.mkdtemp(".httktmp", "httktmp.")


def destroy_tmpdir(tmpdir):
    tmpdirname = os.path.dirname(tmpdir)
    segment = os.path.basename(tmpdir)[len("httktmp."):-len(".httktmp")]
    #print "DELETING:",os.path.join(tmpdirname,"httktmp."+segment+".httktmp")
    shutil.rmtree(os.path.join(tmpdirname, "httktmp."+segment+".httktmp"))


def tuple_to_str(t):
    strlist = []
    for i in t:
        if isinstance(i, tuple):
            tuplestr = "\n"
            tuplestr += tuple_to_str(i)
            #tuplestr += "\n"
            strlist.append(tuplestr)
        else:
            strlist.append(str(i))
    return " ".join(strlist)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def micro_pyawk(ioa, search, results=None, debug=False, debugfunc=None, postdebugfunc=None):
    """
    Small awk-mimicking search routine.
       
    'f' is stream object to search through.
    'search' is the "search program", a list of lists/tuples with 3 elements; i.e.,
    [[regex,test,run],[regex,test,run],...]
    'results' is a an object that your search program will have access to for storing results.

    Here regex is either as a Regex object, or a string that we compile into a Regex.
    test and run are callable objects.

    This function goes through each line in filename, and if regex matches that line *and* 
    test(results,line)==True (or test == None) we execute run(results,match), 
    where match is the match object from running Regex.match.   
    
    The default results is an empty dictionary. Passing a results object let you interact 
    with it in run() and test(). Hence, in many occasions it is thus clever to use results=self. 
    
    Returns: results
    """
    ioa = IoAdapterFileReader.use(ioa)
    f = ioa.file
    
    if results is None:
        results = {}

    # Compile strings into regexs
    for entry in search:
        if isinstance(entry[0], str):
            try:
                entry[0] = re.compile(entry[0])
            except Exception as e:
                raise Exception("Could not compile regular expression:"+entry[0]+" error: "+str(e))
            
    for line in f:
        if debug: 
            sys.stdout.write("\n" + line[:-1])
        for i in range(len(search)):
            match = search[i][0].search(line)
            if debug and match: 
                sys.stdout.write(": MATCH")
            if match and (search[i][1] is None or search[i][1](results, line)):
                if debug:
                    sys.stdout.write(": TRIGGER")
                if debugfunc is not None:
                    debugfunc(results, match)
                search[i][2](results, match)
                if postdebugfunc is not None:
                    postdebugfunc(results, match)
    if debug: 
        sys.stdout.write("\n")

    ioa.close()
    return results


def breath_first_idxs(dim=1, start=None, end=None, perm=True, negative=False):

    if start is None:
        start = (0,)*dim
    elif len(start) != dim:
        start = (start,)*dim

    if end is None:
        end = [None]*dim
    elif len(end) != dim:
        end = [end]*dim

    eles = itertools.count(start[0])

    if dim == 1:
        for e in eles:
            yield (e,)
            if end[0] is not None and e >= end[0]:
                return
   
    for e in eles:
        oeles = breath_first_idxs(dim-1, start=start[1:], end=[e]*(dim-1), perm=False)
        for oe in oeles:
            base = (e,) + oe
            if perm:
                for p in set(itertools.permutations(base)):
                    if negative:
                        nonneg = [i for i in range(len(p)) if p[i] != 0]
                        for x in itertools.chain.from_iterable(itertools.combinations(nonneg, r) for r in range(len(nonneg)+1)):
                            yield [p[i] if i in x else -p[i] for i in range(len(p))]
                    else:
                        yield p
            else:
                if negative:
                    nonneg = [i for i in range(len(p)) if p[i] != 0]
                    for x in itertools.chain.from_iterable(itertools.combinations(nonneg, r) for r in range(len(nonneg)+1)):
                        yield [p[i] if i in x else -p[i] for i in range(len(p))]
                else:
                    yield base

        if end[0] is not None and e >= end[0]:
            return


def nested_split(s, start, stop):
    parts = []
    if s[0] != start:
        return [s]
    chars = []
    n = 0
    for c in s:
        if c == start:
            if n > 0:
                chars.append(c)
            n += 1
        elif c == stop:
            n -= 1
            if n > 0:
                chars.append(c)
            elif n == 0:
                parts.append(''.join(chars).lstrip().rstrip())
                chars = []
        elif n > 0:
            chars.append(c)
    return parts


class rewindable_iterator(object):

    def __init__(self, iterator):
        self._iter = iter(iterator)
        self._rewind = False
        self._cache = None

    def __iter__(self):
        return self

    def next(self):
        if self._rewind:
            self._rewind = False
        else:
            self._cache = self._iter.next()
        return self._cache

    def rewind(self, rewindstr=None):
        if self._rewind:
            raise RuntimeError("Tried to backup more than one step.")
        elif self._cache is None:
            raise RuntimeError("Can't backup past the beginning.")
        self._rewind = True
        if rewindstr is not None:
            self._cache = rewindstr
            

def main():
    print int_to_anonymous_symbol(0)
    print anonymous_symbol_to_int("A")
    
    
    # print list(breath_first_idxs(dim=3, end=[3,3,3],negative=True))


if __name__ == "__main__":
    main()
    



