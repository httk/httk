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

from numpy import *
from numpy.linalg import norm, inv
#from external.spacegroup import Spacegroup
from httk.core import ioadapters
from httk.atomistic import Structure
import sys
#from matsci.structure import structure


def readstruct(ioa, struct, importers=None):

    fileadapter = ioadapters.IoAdapterFileReader(ioa)

    if fileadapter.ext == 'structure':
        struct.parse(fileadapter)

    if importers is None:
        try_importers = ['ase', 'openbabel']
    else:
        try_importers = importers

    for importer in try_importers:
        
        if importer == 'ase':
            try:
                import ase.io
                atoms = ase.io.read(fileadapter.filename_open_workaround())
                species = atoms.get_atomic_numbers()
                coords = atoms.get_positions()
                basis = atoms.get_cell()
                return Structure(basis=basis, coords=coords, species=species)
            except:
                if importers is not None:
                    info = sys.exc_info()
                    raise Exception("Error while trying ase importer: "+str(info[1])), None, info[2]
    
        elif importer == 'openbabel':
            try:
                import openbabel
    
                file = fileadapter.file
                filename = fileadapter.filename
        
                # Use babel to read data from file
                obConversion = openbabel.OBConversion()
                obConversion.SetInAndOutFormats(obConversion.FormatFromExt(fileadapter.filename), obConversion.FindFormat("pdb"))
    
                obmol = openbabel.OBMol()    
                obConversion.ReadString(obmol, file.read())
                unitcell = openbabel.toUnitCell(obmol.GetData(openbabel.UnitCell))            
                unitcell.FillUnitCell(obmol)
    
                basisvecs = unitcell.GetCellVectors()
                basis = array([[basisvecs[0].GetX(), basisvecs[0].GetY(), basisvecs[0].GetZ()],
                               [basisvecs[1].GetX(), basisvecs[1].GetY(), basisvecs[1].GetZ()],
                               [basisvecs[2].GetX(), basisvecs[2].GetY(), basisvecs[2].GetZ()]])

                coords = []  
                species = []              
                for obatom in openbabel.OBMolAtomIter(obmol):
                    cart = openbabel.vector3(obatom.GetX(), obatom.GetY(), obatom.GetZ())
                    coords.append([cart.GetX(), cart.GetY(), cart.GetZ()])
                    species.append(obatom.GetAtomicNum())

                return Structure(basis=basis, coords=coords, species=species)

            except:        
                if importers is not None:
                    info = sys.exc_info()
                    raise Exception("Error while trying openbabel importer: "+str(info[1])), None, info[2]

    raise Exception("Could not figure out a way to read structure")
    return None

    #struct = structure.Structure()

    #fileadapter = ioutils.fileadapter(file_or_filename)
    #file = fileadapter.file
    #filename = fileadapter.filename
    
    # Use babel to read data from file
    #obConversion = openbabel.OBConversion()
    #obConversion.SetInAndOutFormats(obConversion.FormatFromExt(fileadapter.filename), obConversion.FindFormat("pdb"))
    #obmol = openbabel.OBMol()    
    #obConversion.ReadString(obmol, file.read())
    #unitcell = openbabel.toUnitCell(obmol.GetData(openbabel.UnitCell))
    #unitcell.FillUnitCell(obmol)

    #basisvecs = unitcell.GetCellVectors()
    #basis = array([[basisvecs[0].GetX(),basisvecs[0].GetY(),basisvecs[0].GetZ()],
    #               [basisvecs[1].GetX(),basisvecs[1].GetY(),basisvecs[1].GetZ()],
    #               [basisvecs[2].GetX(),basisvecs[2].GetY(),basisvecs[2].GetZ()]])
    #invbasis = inv(transpose(basis))
    #print "BASIS",basis

    #for obatom in openbabel.OBMolAtomIter(obmol):
        #cart = openbabel.vector3(obatom.GetX(),obatom.GetY(),obatom.GetZ())
        #frac = unitcell.CartesianToFractional(cart)
        #sites.append([frac.GetX(),frac.GetY(),frac.GetZ()])
    #    print "X",[obatom.GetX(),obatom.GetY(),obatom.GetZ()]
    
    #spacegroupnumber = unitcell.GetSpaceGroupNumber()    
    #sg = Spacegroup(spacegroupnumber)
    #primitive_cell = sg.scaled_primitive_cell
    #sites = []
    #occs = []

    ### Copy the structure to a new structure so we can change the unitcell
    #obmolout = openbabel.OBMol()
    #for obatom in openbabel.OBMolAtomIter(obmol):
    #    a = obmolout.NewAtom()
    #    a.SetAtomicNum(obatom.GetAtomicNum())   # carbon atom
    #    a.SetVector(obatom.GetX(),obatom.GetY(),obatom.GetZ()) # coordinates

    #unitcellout = openbabel.OBUnitCell()
    #unitcellout.SetSpaceGroup(unitcell.GetSpaceGroupNumber())
    #unitcellout.SetData(openbabel.vector3(primitive_cell[0,0],primitive_cell[0,1],primitive_cell[0,2]),
    #                    openbabel.vector3(primitive_cell[1,0],primitive_cell[1,1],primitive_cell[1,2]),
    #                    openbabel.vector3(primitive_cell[2,0],primitive_cell[2,1],primitive_cell[2,2]))

    #obmolout.CloneData(unitcellout)
    #unitcellout.FillUnitCell(obmolout)
    
    #for obatomout in openbabel.OBMolAtomIter(obmolout):
    #    #cart = openbabel.vector3(obatom.GetX(),obatom.GetY(),obatom.GetZ())
    #    #frac = unitcell.CartesianToFractional(cart)
    #    #sites.append([frac.GetX(),frac.GetY(),frac.GetZ()])
    #    print "Y",[obatomout.GetX(),obatomout.GetY(),obatomout.GetZ()]

    ##print "Y",unitcell.CartesianToFractional(openbabel.double_array([obatom.GetX(),obatom.GetY(),obatom.GetZ()]))
    #basisvecs = unitcell.GetCellVectors()
    #basis = array([[basisvecs[0].GetX(),basisvecs[0].GetY(),basisvecs[0].GetZ()],
    #               [basisvecs[1].GetX(),basisvecs[1].GetY(),basisvecs[1].GetZ()],
    #               [basisvecs[2].GetX(),basisvecs[2].GetY(),basisvecs[2].GetZ()]])

    #invbasis = inv(transpose(basis))
    
    #print unitcell.GetAlpha(), unitcell.GetSpaceGroup()

    #for obatom in openbabel.OBMolAtomIter(obmol):
        #cart = openbabel.vector3(obatom.GetX(),obatom.GetY(),obatom.GetZ())
        #frac = unitcell.CartesianToFractional(cart)
        #sites.append([frac.GetX(),frac.GetY(),frac.GetZ()])
        #print [obatom.GetX(),obatom.GetY(),obatom.GetZ()]
        
    #    sites.append([obatom.GetX(),obatom.GetY(),obatom.GetZ()])
    #    occs.append(obatom.GetAtomicNum())

    #sites = transpose(dot(invbasis,transpose(sites)))
        
    ##invpc = linalg.inv(primitive_cell)
    ##invpc = transpose(primitive_cell)
    ##sites = transpose(dot(invpc,transpose(sites)))
    ##invpc = transpose(linalg.inv(primitive_cell))
    ##sites2 = transpose(dot(invpc,transpose(sites)))

    ##for i in range(len(sites2)):
    ##    print "%.6f    %.6f    %.6f   %s" % (sites2[i][0],sites2[i][1],sites2[i][2],occs[i])
    
    #sites = array(sites)
    #symsites, kinds = sg.equivalent_sites(sites)
    ##symsites, kinds = (sites, range(len(occs)))

    #for i in range(len(symsites)):
    #    print "X",symsites[i],kinds[i]

    ##invpc = transpose(primitive_cell)
    ##symsites = transpose(dot(invpc,transpose(symsites)))

    #filteredsites = []
    #filteredoccs = []
    #for i in range(len(symsites)):
    #    if is_inside_parallellepiped(primitive_cell,symsites[i]):
    #        # The only thing that remains is that we can have equivalent atoms on the border
    #        for j in range(len(filteredsites)):
    #            for offset in []:
    #                if (symsites[i]-filteredsites[j]+)

    #        filteredsites.append(symsites[i])
    #        filteredoccs.append(occs[kinds[i]])

    #print obmol.GetFormula()+" ("+obmol.GetTitle()+") SG:"+ str(unitcell.GetSpaceGroupNumber())

    ##print "%.6f    %.6f    %.6f" % (newcell.GetA(),newcell.GetB(),newcell.GetC())
    ##print "%.6f    %.6f    %.6f" % (newcell.GetAlpha(),newcell.GetBeta(),newcell.GetGamma())

    ##print "%.6f    %.6f    %.6f" % (vectors[0].GetX(),vectors[0].GetY(),vectors[0].GetZ())
    ##print "%.6f    %.6f    %.6f" % (vectors[1].GetX(),vectors[1].GetY(),vectors[1].GetZ())
    ##print "%.6f    %.6f    %.6f" % (vectors[2].GetX(),vectors[2].GetY(),vectors[2].GetZ())

    #print "%.6f    %.6f    %.6f" % (primitive_cell[0,0],primitive_cell[0,1],primitive_cell[0,2])
    #print "%.6f    %.6f    %.6f" % (primitive_cell[1,0],primitive_cell[1,1],primitive_cell[1,2])
    #print "%.6f    %.6f    %.6f" % (primitive_cell[2,0],primitive_cell[2,1],primitive_cell[2,2])

    #for i in range(len(filteredsites)):
    #    print "%.6f    %.6f    %.6f   %s" % (filteredsites[i][0],filteredsites[i][1],filteredsites[i][2],filteredoccs[i])

    ##for i in range(len(symsites)):
    ##    print "%.6f    %.6f    %.6f   %s" % (symsites[i][0],symsites[i][1],symsites[i][2],symoccs[i])

    ##for obatom in openbabel.OBMolAtomIter(obmol):
    ##    obatom.GetAtomicNum()
    ##for obatom in openbabel.OBMolAtomIter(obmol):
    ##    v = openbabel.vector3(obatom.GetX(),obatom.GetY(),obatom.GetZ())
    ##    fv = newcell.CartesianToFractional(v)
    ##    print "%.6f    %.6f    %.6f" % (fv.GetX(),fv.GetY(),fv.GetZ())
    ##    #print "%.6f    %.6f    %.6f" % (obatom.GetX(),obatom.GetY(),obatom.GetZ())


## Needed because of bug (?) in openbabel, which does not seem to be able to reproduce the correct textual spacegroup
