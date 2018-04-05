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

import time

import httk.external.jmol
import httk.core


class JmolStructureVisualizer(object):

    def __init__(self, struct, params={}):
        self.struct = struct
        self.jmol = None
        self.params = params
        if 'bonds' not in self.params:
            self.params['bonds'] = True
        if 'extbonds' not in self.params:
            self.params['extbonds'] = True
        if 'extmetals' not in self.params:
            self.params['extmetals'] = False
            # Set to a tuple, first value = length of metal bonds, second value = cutoff distance to unit cell.
        if 'polyhedra' not in self.params:
            self.params['polyhedra'] = True
        if 'repetitions' not in self.params:
            self.params['repetitions'] = [1, 1, 1]
        if 'defaults' not in self.params:
            self.params['defaults'] = 'defaults'
        if 'angle' not in self.params:
            self.params['angle'] = '{0.5 1 0} 20.0'
        if 'bgcolor' not in self.params:
            self.params['bgcolor'] = '#F5F5F5'
        if 'unitcell' not in self.params:
            self.params['unitcell'] = None
        if 'show_unitcell' not in self.params:
            self.params['show_unitcell'] = True
        if 'extracell' not in self.params:
            self.params['extracell'] = None
        if 'show_supercell' not in self.params:
            self.params['show_supercell'] = False
        if 'perspective' not in self.params:
            self.params['perspective'] = True

    def set_defaults(self):
        self.jmol.send("""define ~anions (oxygen or nitrogen or fluorine or sulphur or chlorine or selenium or bromine or tellurium or iodine);
        color (boron) lime;
        """)
        if self.params['perspective']:
            self.jmol.send("""set perspectivedepth on;
            """)
        else:
            self.jmol.send("""set perspectivedepth off;
            """)

#     def defaults_old(self, extbonds=True, bonds=True, polyhedra=True):
#         self.jmol.send("""unitcell {1/1 1/1 1/1};
#         spacefill 25%;
#         define ~cations (lithium or beryllium or boron or carbon or nitrogen or sodium or magnesium or aluminium or silicon or phosphorus or potassium or calcium or scandium or titanium or vanadium or chromium or manganese or iron or cobalt or nickel or copper or zinc or gallium or germanium or arsenic or rubidium or strontium or yttrium or zirconium or niobium or molybdenum or technetium or ruthenium or rhodium or palladium or silver or cadmium or indium or tin or antimony or cesium or barium or hafnium or tantalum or tungsten or rhenium or osmium or iridium or platinum or gold or mercury or thallium or lead or bismuth or polonium or francium or radium or lawrencium or rutherfordium or dubnium or seaborgium or lanthanum or cerium or praseodymium or neodymium or promethium or samarium or europium or gadolinium or terbium or dysprosium or holmium or erbium or thulium or ytterbium or lutetium or actinium or thorium or protactinium or uranium or neptunium or plutonium or americium or curium or berkelium or californium or einsteinium or fermium or mendelevium or nobelium);
#         define ~anions (oxygen or nitrogen or fluorine or sulphur or chlorine or selenium or bromine or tellurium or iodine);
#         connect delete;
#         connect 0.75 2.6;
#         connect (~anions) (~anions) delete;
#         connect (~cations) (~cations) delete;
#         connect (~nobonds) (*) delete;
#         connect 0.75 2.6 (~anions) (~cations) and visible;
#         connect 1.8 (phosphorus) (oxygen or nitrogen) and visible;
#         connect 1.8 (sulphur) (oxygen or nitrogen) and visible;
#         connect 1.8 (selenium) (oxygen) and visible;
#         connect 2.2 (nitrogen) (carbon) and visible;
#         connect 2.0 (silicon) (carbon) and visible;
#         connect 2.0 (selenium) (carbon) and visible;
#         connect 1.45 (hydrogen) (carbon) and visible;
#         connect 1.45 (hydrogen) (nitrogen) and visible;
#         connect 1.45 (hydrogen) (phosphorus) and visible;
#         connect 1.80 (carbon) (carbon) and visible;
#         connect 1.45 (carbon) (hydrogen) and visible;
#         connect 1.50 (nitrogen) (nitrogen) and visible;
#         connect 0.5 1.44 (oxygen) (hydrogen) and visible;
#         connect 1.45 2.40 (oxygen) (hydrogen) and visible HBOND;
#         delete (NOT (unitcell OR connected(unitcell)));
#         polyhedra delete;
#         polyhedra ON;
#         polyhedra bonds (~cations and (connected(3) or connected(4) or connected(5) or connected(6) or connected(7) or connected(8)) and visible) distanceFactor 2.0;
#         polyhedra bonds (~cations and (connected(3) or connected(4) or connected(5) or connected(6) or connected(7) or connected(8)) and visible) distanceFactor 2.0;
#         color polyhedra translucent;
#         """)
#         
#         if extbonds == False:
#             self.jmol.send("restrict cell={2 2 2};\n")
#         if bonds == False:
#             self.jmol.send("connect (all) (all) DELETE;\n")
    
        #self.jmol.send("center visible;\n")
        #self.jmol.send("zoom 0;\n")

#     def defaults(self):
#         self.jmol.send("""unitcell {1/1 1/1 1/1};
#         connect delete;
#         define ~anions (oxygen or nitrogen or fluorine or sulphur or chlorine or selenium or bromine or tellurium or iodine);
#         connect 0.75 2.6 (~anions) (NOT ~anions);
#         connect 1.8 (phosphorus) (oxygen or nitrogen);
#         connect 1.8 (sulphur) (oxygen or nitrogen);
#         connect 1.8 (selenium) (oxygen);
#         connect 2.2 (nitrogen) (carbon);
#         connect 2.0 (silicon) (carbon);
#         connect 2.0 (selenium) (carbon);
#         connect 1.45 (hydrogen) (carbon);
#         connect 1.45 (hydrogen) (nitrogen);
#         connect 1.45 (hydrogen) (phosphorus);
#         connect 1.80 (carbon) (carbon);
#         connect 1.45 (carbon) (hydrogen);
#         connect 1.50 (nitrogen) (nitrogen);
#         connect 2.0 (boron) (boron);
#         connect 0.5 1.44 (oxygen) (hydrogen);
#         connect 1.45 2.40 (oxygen) (hydrogen) HBOND;
#         delete (NOT (unitcell OR connected(unitcell)));
#         polyhedra delete;
#         polyhedra ON;
#         polyhedra BONDS (NOT ~anions); 
#         color polyhedra translucent;
#         """)
# 
#         #polyhedra bonds (NOT ~anions and (connected(3) or connected(4) or connected(5) or connected(6) or connected(7) or connected(8)) and visible) distanceFactor 2.0;
#         if self.params['polyhedra'] == False:
#             self.jmol.send("polyhedra OFF;\n")
#         if self.params['extbonds'] == False:
#             self.jmol.send("restrict cell={2 2 2};\n")
#         if self.params['bonds'] == False:
#             self.jmol.send("connect (all) (all) DELETE;\n")
#     
#         self.jmol.send("center visible;\n")
#         #self.jmol.send("rotate BEST;\n")
#         self.jmol.send("rotate AXISANGLE "+ self.params['angle']+";\n")
#         self.jmol.send("zoom 0;\n")

    def connections(self):
        self.jmol.send("""connect delete;
        define ~anions (oxygen or nitrogen or fluorine or sulphur or chlorine or selenium or bromine or tellurium or iodine);
        define ~metals (Lithium or Sodium or Potassium or Rubidium or Cesium or Francium or Beryllium or 
        Magnesium or Calcium or Strontium or Barium or Radium or Aluminum or Gallium or Indium or Tin or 
        Thallium or Lead or Bismuth or Scandium or Titanium or Vanadium or Chromium or Manganese or Iron or 
        Cobalt or Nickel or Copper or Zinc or Yttrium or Zirconium or Niobium or Molybdenum or Technetium or 
        Ruthenium or Rhodium or Palladium or Silver or Cadmium or Lanthanum or Hafnium or Tantalum or 
        Tungsten or Rhenium or Osmium or Iridium or Platinum or Gold or Mercury or Actinium or 
        Rutherfordium or Dubnium or Seaborgium or Bohrium or Hassium or Meitnerium or Darmstadtium or 
        Roentgenium or Copernicium or Cerium or Praseodymium or Neodymium or Promethium or Samarium or 
        Europium or Gadolinium or Terbium or Dysprosium or Holmium or Erbium or Thulium or Ytterbium or 
        Lutetium or Thorium or Protactinium or Uranium or Neptunium or Plutonium or Americium or Curium or 
        Berkelium or Californium or Einsteinium or Fermium or Mendelevium or Nobelium or Lawrencium);
        connect 0.75 2.6 (~anions) (NOT ~anions);
        connect 1.8 (phosphorus) (oxygen or nitrogen);
        connect 1.8 (sulphur) (oxygen or nitrogen);
        connect 1.8 (selenium) (oxygen);
        connect 2.2 (nitrogen) (carbon);
        connect 2.0 (silicon) (carbon);
        connect 2.0 (selenium) (carbon);
        connect 1.45 (hydrogen) (carbon);
        connect 1.45 (hydrogen) (nitrogen);
        connect 1.45 (hydrogen) (phosphorus);
        connect 1.80 (carbon) (carbon);
        connect 1.45 (carbon) (hydrogen);
        connect 1.50 (nitrogen) (nitrogen);
        connect 2.0 (boron) (boron);
        connect 0.5 1.44 (oxygen) (hydrogen);
        connect 1.45 2.40 (oxygen) (hydrogen) HBOND;
        """)
        #connect 3.1 (~metals) (~metals);

    def preconnect(self):
        self.connections()
        self.jmol.send("connect "+str(self.params['extmetals'][0])+" (~metals) (~metals);")

    def postconnect(self):
        self.connections()

    def defaults_publish(self):
        self.jmol.send("hide all;\nunitcell off;\nset displayCellParameters FALSE;\naxes off;\nfrank off;\n")
        self.set_defaults()
        self.jmol.send("translate {-1/1 -1/1 -1/1};")
        #self.jmol.send("unitcell {1/1 1/1 1/1};")
        if self.params['extmetals']:
            self.preconnect()
        else:
            self.postconnect()
        self.jmol.send("""
        delete (NOT (unitcell OR connected(unitcell)));
        """)
        if self.params['extmetals']:
            self.postconnect()
            self.jmol.send("delete (NOT (unitcell OR connected(unitcell) OR within("+str(self.params['extmetals'][1])+",unitcell)));")

        self.jmol.send("""
        polyhedra delete;
        polyhedra ON;
        polyhedra BONDS (NOT ~anions); 
        color polyhedra translucent;
        unitcell off;
        """)

        if self.params['polyhedra'] == False:
            self.jmol.send("polyhedra OFF;\n")
        if self.params['extbonds'] == False:
            self.jmol.send("restrict cell={1 1 1};\n")
        if self.params['bonds'] == False:
            self.jmol.send("connect (all) (all) DELETE;\n")

        if self.params['show_unitcell']:
    
            if self.params['unitcell'] is None:
                if self.struct.has_rc_repr:
                    basis = self.struct.rc_basis
                elif self.struct.has_uc_repr:
                    basis = self.struct.uc_basis
            else:
                basis = self.params['unitcell']
    
            origin = (0*(basis[0] + 0*basis[1] + 0*basis[2]))
            newbasis = []
            newbasis += [((origin + basis[0])).to_floats()]
            newbasis += [((origin + basis[1])).to_floats()]
            newbasis += [((origin + basis[2])).to_floats()]
            origin = origin.to_floats()
    
            #newbasis = [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]
            
            unitcellstr = "unitcell [ "
            unitcellstr += "{" + str(origin[0])+" "+str(origin[1])+" "+str(origin[2])+"} "
            unitcellstrs = []
            for i in range(3):
                unitcellstrs += ["{"+str(newbasis[i][0])+" "+str(newbasis[i][1])+" "+str(newbasis[i][2])+"}"]
            unitcellstr += ", ".join(unitcellstrs)+" ];\n"
            jmol_version = httk.external.jmol.jmol_version.split('.')
            if (int(jmol_version[0]) == 14 and int(jmol_version[1]) == 0 and int(jmol_version[1]) == 13):
                # This happened to be the jmol version I had installed when I first programmed this part,
                # so it seemed relevant to add this bug workaround...
                unitcellstr += "unitcell {1 1 1};\n"
            else:
                unitcellstr += "unitcell {0 0 0};\n"
            unitcellstr += "unitcell on;\nunitcell 0.025;\n"
    
            self.jmol.send(unitcellstr)

        if self.params['extracell']:
            basis = self.params['extracell']                       
            origin = (0*(basis[0] + 0*basis[1] + 0*basis[2]))
            p = [origin, basis[0], basis[1], basis[2], basis[0]+basis[1], basis[0]+basis[2], basis[1]+basis[2], basis[0]+basis[1]+basis[2]]            
            edges = ((0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (3, 5), (3, 6), (2, 6), (2, 4), (4, 7), (6, 7), (5, 7))
            for i, edge in enumerate(edges, start=1):
                line = (p[edge[0]].to_floats()) + (p[edge[1]].to_floats())                 
                self.jmol.send("draw line_ec_"+str(i)+" {%f %f %f} {%f %f %f} DIAMETER 0.06;\n" % tuple(line))

        if self.params['show_supercell']:
            if self.struct.has_rc_repr:
                basis = self.struct.rc_basis
            elif self.struct.has_uc_repr:
                basis = self.struct.uc_basis
            origin = (0*(basis[0] + 0*basis[1] + 0*basis[2]))
            p = [origin, basis[0], basis[1], basis[2], basis[0]+basis[1], basis[0]+basis[2], basis[1]+basis[2], basis[0]+basis[1]+basis[2]]            
            edges = ((0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (3, 5), (3, 6), (2, 6), (2, 4), (4, 7), (6, 7), (5, 7))
            for i, edge in enumerate(edges, start=1):
                line = (p[edge[0]].to_floats()) + (p[edge[1]].to_floats())                 
                self.jmol.send("draw line_sc_"+str(i)+" {%f %f %f} {%f %f %f} DIAMETER 0.06 COLOR blue;\n" % tuple(line))
                            
        #axis off;

        #polyhedra bonds (NOT ~anions and (connected(3) or connected(4) or connected(5) or connected(6) or connected(7) or connected(8)) and visible) distanceFactor 2.0;
    
        self.jmol.send("rotate BEST;\n")
        self.jmol.send("display all;\n")
        self.jmol.send("center visible;\n")
        #self.jmol.send("rotate AXISANGLE {0.5 1 0} 20.0;\n")
        self.jmol.send("zoom 0;\n")

    def extbonds(self, on):
        if self.jmol is not None:
            self._extbonds = on
            self.initialize()

    def polyhedra(self, on):
        if self.jmol is not None:
            self._polyhedra = on
            self.initialize()

    def bonds(self, on):
        if self.jmol is not None:
            self._bonds = on
            self.initialize()

    def repeat(self, repetitions):
        if self.jmol is not None:
            self._repetitios = repetitions
            self.initialize()

    def initialize(self):
        if self.jmol is not None:
            bgcolorstr = self.params['bgcolor']
            self.jmol.send("zap;\n")
            self.jmol.send("background '"+bgcolorstr+"';\n")
            #self.jmol.send("background '"+bgcolorstr+"';\n")

    def refresh(self):
        if self.jmol is not None:
            self.initialize()
            httk.external.jmol.structure_to_jmol(self.jmol.stdin, self.struct, copies=[4, 4, 4], repeat=self.params['repetitions'])
            if self.params['defaults'] == 'publish':
                self.defaults_publish() 
            else:
                self.defaults_publish() 

    def save_and_quit(self, filename, resx=3200, resy=2500):
        self.jmol.send('write image '+str(resx)+' '+str(resy)+' "'+filename+'";exitJmol;\n')
        self.jmol.wait_finish()
        self.jmol = None
                 
    def show(self, repeat=None):
        if self.jmol is None:
            self.jmol = httk.external.jmol.start()
        self.refresh()

    def stop(self):
        if self.jmol is not None:
            self.jmol.stop()
            self.jmol = None

    def wait(self):
        if self.jmol is not None:
            self.jmol.wait_finish()

    def rotate(self, angle):
        self.jmol.send("rotate x "+str(angle[0])+"; rotate z "+str(angle[1])+"; rotate y "+str(angle[2])+";\n")

    def spin(self, on=True):
        if self.jmol is not None:
            if on:
                self.jmol.send("spin on;\n")
            else:
                self.jmol.send("spin off;\n")
    
    
