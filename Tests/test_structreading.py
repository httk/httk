#!/usr/bin/env python
#!/usr/bin/env python
import sys, os, unittest, subprocess, argparse, difflib
from itertools import izip_longest
from contextlib import contextmanager
from StringIO import StringIO

import httk
from timeit import itertools

logdata = []

def run(command,args=[]):
    global logdata
    
    logdata += ['Try to run: ' + command]
    p = subprocess.Popen([command] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()
    
class TestStructreading(unittest.TestCase):

    def assert_equal_rows(self, orig, new):
        if orig != new:
            message = ''.join(difflib.ndiff(orig.splitlines(True),new.splitlines(True)))
            self.fail("Multi-line strings are unequal:\n" + message)            

    def assert_numeric_data(self, orig, new):
        group = 0
        midgroup = 0        
        subgroup = 0
        line = -1
        sizes = []
        emptylinecount = 0
        orig_set = [[]]
        new_set = [[]]
        orig_basis = [[]]
        new_basis = [[]]
        #message = ''.join(difflib.ndiff(orig.splitlines(True),new.splitlines(True)))
        message = ''
        
        for orig_line, new_line in izip_longest(orig.splitlines(),new.splitlines()):
            if orig_line == "" and new_line == "":
                emptylinecount += 1
                if emptylinecount == 2:
                    if group == 2:
                        del orig_basis[-1]
                        del new_basis[-1]
                    group += 1
                    subgroup = 0
                    midgroup = 0
                    line = -1                    
                    orig_set = [[[]]]
                    new_set = [[[]]]                    
                    continue                    
                subgroup += 1
                if group == 2:
                    orig_basis.append([])
                    new_basis.append([])
                elif group == 3:
                    orig_set[midgroup] += [[]]
                    new_set[midgroup] += [[]]
                continue
            line += 1
            emptylinecount = 0
            self.assertTrue(orig_line is not None, "Verification file missing line:"+new_line+"\nFull diff:\n"+message)
            self.assertTrue(new_line is not None, "New version missing line:"+orig_line+"\nFull diff:\n"+message)
            for orig_datum, new_datum in izip_longest(orig_line.split(),new_line.split()):
                self.assertTrue(orig_datum is not None, "Verification file missing datum: "+new_datum+"\nFull diff:\n"+message)
                self.assertTrue(new_datum is not None, "New version missing datum:"+orig_datum+"\nFull diff:\n"+message)
                if group == 1:
                    sizes.append(int(orig_datum))
                if group == 2:
                    # Basis vecs can be returned in any order...
                    try:
                        orig_basis[-1].append(float(orig_datum))
                        new_basis[-1].append(float(new_datum))
                    except ValueError as e:
                        self.assertTrue(False,"Coordinate values not floats: misformatted output:"+orig_datum+" vs "+new_datum)
                elif group == 3:
                    # Coordinates can be returned in any order...
                    if len(orig_set[-1]) == sizes[midgroup]+1:
                        del orig_set[-1][-1]
                        del new_set[-1][-1]
                        midgroup += 1
                        orig_set.append([[]])
                        new_set.append([[]])
                    try:
                        orig_set[-1][-1].append(float(orig_datum))
                        new_set[-1][-1].append(float(new_datum))
                    except ValueError as e:
                        self.assertTrue(False,"Coordinate values not floats: misformatted output:"+orig_datum+" vs "+new_datum)
                else:
                    try:
                        orig_int = int(orig_datum)
                        new_int = int(new_datum)
                    except ValueError as e:
                        try:
                            orig_float = float(orig_datum)
                            new_float = float(new_datum)
                        except ValueError as e:
                            self.assertTrue(orig_datum == new_datum, "Comparing strings:"+orig_datum+" != "+new_datum+"\nFull diff:\n"+message)
                        else:
                            self.assertAlmostEqual(orig_float,new_float, 5, "Comparing floats:"+orig_datum+" != "+new_datum+"\nFull diff:\n"+message)                         
                    else:
                        self.assertEqual(orig_int, new_int, "Comparing ints:"+orig_datum+" != "+new_datum+"\nFull diff:\n"+message)
                        
        def check_permut(orig_set, new_set, coord_permuts=[0,1,2]):
            self.assertEqual(len(orig_set),len(new_set),"Not equal amount of coordinates in this group.")
            for orig_line,new_line in zip(orig_set,new_set):
                self.assertEqual(len(orig_line),len(new_line),"Not equal amount of coordinate values, misformed data.")
                for orig_datum, new_datum in zip(orig_line, [new_line[x] for x in coord_permuts]):
                    if round(abs(orig_datum - new_datum), 4) != 0:
                        return False, (abs(orig_datum - new_datum), orig_datum, new_datum)
            return True, None

        def check_group(orig_group, new_group, coord_permuts):
            smallest_error = None
            orig_group.sort()
            new_group.sort()
            pc = 0
            permut = itertools.permutations(new_group)
            for p in permut:   
                pc += 1
                self.assertEqual(len(orig_group),len(p),"Not equal amount of coordinate groups.")
                check, err = check_permut(orig_group, p, coord_permuts)
                if check:
                    print "Found match after considering",pc,"permutations."
                    #print orig_group
                    #print p
                    #print "------------------------------------------------"
                    return True, None
                else:
                    if smallest_error is None or err[0] < smallest_error[0]:
                        smallest_error = err
            return False, smallest_error

        del orig_set[-1]
        del new_set[-1]

        self.assertEqual(len(orig_basis),len(new_basis),"Unequal amount of basis vectors, misformed output.")        
        x_permuts = itertools.permutations(range(len(new_basis)))
        smallest_error = None
        for xp in x_permuts:
            y_permuts = itertools.permutations(range(len(new_basis)))
            for yp in y_permuts:
                check, err = check_permut(orig_basis, [[new_basis[x][y] for y in yp] for x in xp])
                if check:
                    coord_x_permuts = xp
                    coord_y_permuts = yp
                    break
                if smallest_error is None or err[0] < smallest_error[0]:
                    smallest_error = err
            else:
                continue
            break
        else:
            self.assertTrue(False,"Basis vectors not equal (despite considering all permutations)\n"+str(orig_basis)+'\nvs\n'+str(new_basis)+"\nSmallest error:"+str(smallest_error))                    
        coord_permuts = [coord_x_permuts[x] for x in coord_y_permuts]

        for orig_group,new_group in zip(orig_set,new_set):
            check, err = check_group(orig_group, new_group, coord_permuts)
            if not check:
                self.assertTrue(False,"Coordinates not equal (despite considering all permutations), smallest error:"+str(err))                    
                break
                                
            # Coordinates can be returned in any order...
                
    
    def test_read_all_spacegroups(self):
        compdir = 'structreading_data'
        topdir = '../Tutorial/tutorial_data'
        reldir = 'all_spacegroups/cifs/'

        def print_num_matrix(l):
            outstr = ""
            for i in l:
                if isinstance(i, list):
                    outstr += print_num_matrix(i)
                    outstr += "\n"
                else:
                    outstr += str(i) + "\n"
            return outstr

        structdir = os.path.join(topdir,reldir)

        for subdir, dirs, files in os.walk(structdir):
            for f in files:
                if f.endswith('.cif'):
                    print "TESTING:",f

                    reldir = os.path.relpath(subdir, topdir)
                    ff = os.path.join(subdir, f)
                    relf = os.path.join(reldir,f+'.check')
                    struct = httk.load(ff)
                    #if not os.path.exists(reldir):
                    #    os.makedirs(reldir)
                    if struct.assignments.ratios != [1]*len(struct.assignments.ratios):
                        print "Disordered structure, skipping"
                        continue
                    
                    if f in [ '70.cif', '26.cif', '190.cif']:
                        print "Skipping structure incorrectly read by cif2cell"
                        continue
                    #if f == '184.cif' or f == '119.cif' or f == '217.cif' or f == '200.cif':
                    #    # For some reason cif2cell has a different orientation here
                    #    continue


                    of = open('structreading.tmp',"w") 
                    #of.write(" ".join(struct.uc_formula_symbols)+"\n")
                    #of.write(" ".join([str(x) for x in struct.pc.uc_counts])+"\n")
                    #of.write(print_num_matrix(struct.pc.uc_cell.basis.to_floats()))
                    #of.write(print_num_matrix(struct.pc.uc_reduced_coords.to_floats()))
                    of.write(" ".join(struct.uc_formula_symbols)+"\n\n\n")
                    of.write(" ".join([str(x) for x in struct.uc_counts])+"\n\n\n")
                    of.write(print_num_matrix(struct.uc_cell.basis.to_floats()))
                    of.write("\n")
                    of.write(print_num_matrix(struct.uc_reduced_coords.to_floats()))

                    of.close()

                    compf = os.path.join(compdir,relf)

                    f = open(compf)
                    s1 = f.read()
                    f.close()

                    f = open('structreading.tmp')
                    s2 = f.read()
                    f.close()
                    
                    self.assert_numeric_data(s1,s2)
                    #self.assertTrue(filecmp.cmp(compf, 'structreading.tmp'))


#############################################################################

            
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Structure reading tests")
    ap.add_argument("--debug", help = 'Debug output', action='store_true')
    args, leftovers = ap.parse_known_args()
    
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestStructreading)
        unittest.TextTestRunner(verbosity=2).run(suite)        
    finally:
        if args.debug:
            print("") 
            print("Loginfo:")
            print(logdata)




            
#print("Formula:", struct.formula)
#print("Volume:", float(struct.uc_volume))
#print("Assignments", struct.uc_formula_symbols)
#print("Counts:", struct.uc_counts)
#print("Coords", struct.uc_reduced_coords)
