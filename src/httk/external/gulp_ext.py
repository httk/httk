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

from httk.core import citation
citation.add_ext_citation('Jmol', "Jmol: an open-source Java viewer for chemical structures in 3D. http://www.jmol.org/")

import os

from httk import config
from command import Command
import httk
import httk.iface

try:
    jmol_path = config.get('paths', 'jmol')
except Exception:
    jmol_path = None
    raise Exception("httk.external.jmol_ext imported with no jmol path set in httk.cfg")


def jmol(cwd, args, timeout=10):
    out, err, completed = Command(jmol_path, args, cwd=cwd).run(timeout)
    return out, err, completed    


def show(struct):
    tmpdir = httk.utils.create_tmpdir()
    
    f = httk.IoAdapterFilename(os.path.join(tmpdir, "atoms.gin"))
    httk.iface.gulp_if.structure_to_gulp(f, struct)
    #print "Running gulp"
    out, err, completed = gulp(tmpdir, ["atoms"], timeout=30)
    if not completed:
        raise Exception("Gulp broke:"+tmpdir)
    #print "Gulp finished",completed
    if completed:
        def get_energy(results, match):
            results['energy'] = float(match.group(1))
            
        results = httk.utils.micro_pyawk(os.path.join(tmpdir, "atoms.gout"), [
            ['^ *Total lattice energy += +([-0-9.]+) +eV', None, get_energy],
        ])
    else:
        results = {}
        
    if 'energy' in results:    
        #print "HERE:",results['energy']/struct.N
        #exit(0)
        httk.utils.destroy_tmpdir(tmpdir)
        return results['energy']/struct.N

    httk.utils.destroy_tmpdir(tmpdir)
    return None

