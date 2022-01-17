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

import httk
from httk.core.httkobject import HttkObject, httk_typed_init, httk_typed_property
from httk.atomistic import Structure
from httk.core import FracVector
from httk.atomistic.results.utils import ElasticTensor


class Result_ElasticResult(httk.Result):
    """
    X_V = Voigt average
    X_R = Reuss average
    X_VRH = Hill average
    K_X = Bulk modulus
    G_X = Shear modulus
    mu_VRH = Poisson's ratio
    E_VRH = Young's modulus
    """
    @httk.httk_typed_init({
        'total_energy': float,
        'computation': httk.Computation,
        'initial_structure': Structure,
        'structure': Structure,
        'temperature': float,
        'elastic_tensor': ElasticTensor,
        'elastic_tensor_nosym': ElasticTensor,
        'compliance_tensor': ElasticTensor,
        'K_V': int,
        'K_R': int,
        'K_VRH': int,
        'G_V': int,
        'G_R': int,
        'G_VRH': int,
        'mu_VRH': float,
        'E_VRH': int,
        'mechanically_stable': bool,
        'mechanically_stable_with_tolerance': bool,
        'atomic_relaxations': bool,
        'walltimes': str,
        'rundir': str,
        'material_id': str,
        'version': str,
        'encut': float,
        'nkpts': int,
        'pseudopots': str,
        'incar': str,
        'kpoints': str,
        'contcar': str
        })
    def __init__(self,
            total_energy,
            computation,
            initial_structure,
            structure,
            temperature,
            elastic_tensor,
            elastic_tensor_nosym,
            compliance_tensor,
            K_V,
            K_R,
            K_VRH,
            G_V,
            G_R,
            G_VRH,
            mu_VRH,
            E_VRH,
            mechanically_stable,
            mechanically_stable_with_tolerance,
            atomic_relaxations,
            walltimes,
            rundir,
            material_id,
            version,
            encut,
            nkpts,
            pseudopots,
            incar,
            kpoints,
            contcar
            ):
        self.total_energy = total_energy
        self.computation = computation
        self.initial_structure = initial_structure
        self.structure = structure
        self.temperature = temperature
        self.elastic_tensor = elastic_tensor
        self.elastic_tensor_nosym = elastic_tensor_nosym
        self.compliance_tensor = compliance_tensor
        self.K_V = K_V
        self.K_R = K_R
        self.K_VRH = K_VRH
        self.G_V = G_V
        self.G_R = G_R
        self.G_VRH = G_VRH
        self.mu_VRH = mu_VRH
        self.E_VRH = E_VRH
        self.mechanically_stable = mechanically_stable
        self.mechanically_stable_with_tolerance = mechanically_stable_with_tolerance
        self.atomic_relaxations = atomic_relaxations
        self.walltimes = walltimes
        self.rundir = rundir
        self.material_id = material_id
        self.version = version
        self.encut = encut
        self.nkpts = nkpts
        self.pseudopots = pseudopots
        self.incar = incar
        self.kpoints = kpoints
        self.contcar = contcar
