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
from httk.atomistic import Structure
from httk.core import FracVector
from httk.atomistic.results.utils import ElasticTensorFloat
from httk.atomistic.results.utils import ThirdOrderElasticTensor
from httk.atomistic.results.utils import PlaneDependentTensor

class Result_AIMDResult(httk.Result):
    """
    TODO: document the variables here
    """
    @httk.httk_typed_init({
        'total_energy': float,
        'computation': httk.Computation,
        'formula': str,
        'temperature': float,
        'VEC': float,
        'elastic_tensor': ElasticTensorFloat,
        'compliance_tensor': ElasticTensorFloat,
        'third_order_elastic_tensor': ThirdOrderElasticTensor,
        'ultimate_tensile_strain': PlaneDependentTensor,
        'ultimate_shear_strain': PlaneDependentTensor,
        'ultimate_tensile_strength': PlaneDependentTensor,
        'ultimate_shear_strength': PlaneDependentTensor,
        'tensile_toughness': PlaneDependentTensor,
        'tensile_resilience': PlaneDependentTensor,
        'tensile_elastic_strain_limit': PlaneDependentTensor,
        'tensile_plastic_strain_range': PlaneDependentTensor,
        'tensile_fracture_strain': PlaneDependentTensor,
        'tensile_plastic_energy_density': PlaneDependentTensor,
        'slip_induced_plasticity_at_crack_tips': PlaneDependentTensor,
        'shear_modulus_tensor': PlaneDependentTensor,
        'Gv': float,
        'B': float,
        'Ev': float,
        'G_over_B': float,
        # 'material_id': str,
        })
    def __init__(self,
        total_energy,
        computation,
        formula,
        temperature,
        VEC,
        elastic_tensor,
        compliance_tensor,
        third_order_elastic_tensor,
        ultimate_tensile_strain,
        ultimate_shear_strain,
        ultimate_tensile_strength,
        ultimate_shear_strength,
        tensile_toughness,
        tensile_resilience,
        tensile_elastic_strain_limit,
        tensile_plastic_strain_range,
        tensile_fracture_strain,
        tensile_plastic_energy_density,
        slip_induced_plasticity_at_crack_tips,
        shear_modulus_tensor,
        Gv,
        B,
        Ev,
        G_over_B,
        # material_id,
            ):
        self.total_energy = total_energy
        self.computation = computation
        self.formula = formula
        self.temperature = temperature
        self.VEC = VEC
        self.elastic_tensor = elastic_tensor
        self.compliance_tensor = compliance_tensor
        self.third_order_elastic_tensor = third_order_elastic_tensor
        self.ultimate_tensile_strain = ultimate_tensile_strain
        self.ultimate_shear_strain = ultimate_shear_strain
        self.ultimate_tensile_strength = ultimate_tensile_strength
        self.ultimate_shear_strength = ultimate_shear_strength
        self.tensile_toughness = tensile_toughness
        self.tensile_resilience = tensile_resilience
        self.tensile_elastic_strain_limit = tensile_elastic_strain_limit
        self.tensile_plastic_strain_range = tensile_plastic_strain_range
        self.tensile_fracture_strain = tensile_fracture_strain
        self.tensile_plastic_energy_density = tensile_plastic_energy_density
        self.slip_induced_plasticity_at_crack_tips = slip_induced_plasticity_at_crack_tips
        self.shear_modulus_tensor = shear_modulus_tensor
        self.Gv = Gv
        self.B = B
        self.Ev = Ev
        self.G_over_B = G_over_B
        # self.material_id = material_id
