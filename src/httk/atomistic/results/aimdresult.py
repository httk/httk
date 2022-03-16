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
from httk.atomistic.representativesites import RepresentativeSites
from httk.core import Computation, Code, Signature, SignatureKey
from httk.atomistic import Assignments, Cell
from httk.atomistic.results.utils import ElasticTensor, MaterialId
from httk.atomistic.results.utils import ThirdOrderElasticTensor
from httk.atomistic.results.utils import PlaneDependentTensor
from httk.atomistic.results.utils import InitialStructure
from httk.atomistic.results.utils import MethodDescriptions, Method
from httk.core.reference import Reference, Author

class Result_AIMDResult(httk.Result):
    """
    TODO: document the variables here
    """
    @httk.httk_typed_init({
        'total_energy': float,
        'computation': httk.Computation,
        'initial_structure': InitialStructure,
        'structure': Structure,
        'temperature': float,
        'VEC': float,
        'elastic_tensor': ElasticTensor,
        'compliance_tensor': ElasticTensor,
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
        'K_VRH': float,
        'G_VRH': float,
        'E_VRH': float,
        'G_over_B': float,
        'method_descriptions': MethodDescriptions,
        'material_id': MaterialId,
        })
    def __init__(self,
        total_energy,
        computation,
        initial_structure,
        structure,
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
        K_VRH,
        G_VRH,
        E_VRH,
        G_over_B,
        method_descriptions,
        material_id,
        ):
        self.total_energy = total_energy
        self.computation = computation
        self.initial_structure = initial_structure
        self.structure = structure
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
        self.K_VRH = K_VRH
        self.G_VRH = G_VRH
        self.E_VRH = E_VRH
        self.G_over_B = G_over_B
        self.method_descriptions = method_descriptions
        self.material_id = material_id

    @classmethod
    def new_from(cls, other):
        ########################################################################
        # Computation
        ########################################################################
        new_code = Code.create(
            name = other.computation.code.name,
            version = other.computation.code.version,
        )
        code_tags = other.computation.code.get_tags()
        if code_tags is not None and len(code_tags) > 0:
            for name, tag in code_tags.items():
                new_code.add_tag(name, tag.value)

        code_refs = other.computation.code.get_refs()
        if code_refs is not None and len(code_refs) > 0:
            for code_ref in code_refs:
                new_code.add_ref(code_ref.reference.ref)

        new_keys = []
        for key in other.computation.keys:
            new_keys.append(
                SignatureKey.create(key.keydata, key.description)
            )

        new_signatures = []
        for signature in other.computation.signatures:
            new_key = SignatureKey.create(signature.key.keydata,
                                   signature.key.description)
            new_signatures.append(
                Signature.create(signature.signature_data, new_key)
            )

        new_computation = Computation.create(
            other.computation.computation_date,
            other.computation.description,
            new_code,
            other.computation.manifest_hash,
            new_signatures,
            new_keys,
            other.computation.project_counter,
            other.computation.relpath,
            other.computation.added_date)

        comp_tags = other.computation.get_tags()
        if comp_tags is not None and len(comp_tags) > 0:
            for name, tag in comp_tags.items():
                new_computation.add_tag(name, tag.value)

        comp_refs = other.computation.get_refs()
        if comp_refs is not None and len(comp_refs) > 0:
            for comp_ref in comp_refs:
                new_computation.add_ref(comp_ref.reference.ref)

        # comp_projects = other.computation.get_projects()
        # if comp_projects is not None and len(comp_projects) > 0:
        #     for name, tag
        #     new_computation.add_projects(other.computation.get_projects())

        ########################################################################
        # InitialStructure
        ########################################################################
        new_initial_assignments = Assignments.create(other.initial_structure.assignments.atomic_numbers)
        new_initial_rc_sites = RepresentativeSites.create(
            reduced_coordgroups=other.initial_structure.rc_sites.reduced_coordgroups,
            hall_symbol=other.initial_structure.rc_sites.hall_symbol
        )
        new_initial_rc_cell = Cell.create(
            basis=other.initial_structure.rc_cell.basis,
            lattice_system=other.initial_structure.rc_cell.lattice_system
        )
        new_initial_structure = InitialStructure.create(
            new_initial_assignments,
            new_initial_rc_sites,
            new_initial_rc_cell
        )

        initial_structure_tags = other.initial_structure.get_tags()
        if initial_structure_tags is not None and len(initial_structure_tags) > 0:
            for name, tag in initial_structure_tags.items():
                new_initial_structure.add_tag(name, tag.value)

        initial_structure_refs = other.initial_structure.get_refs()
        if initial_structure_refs is not None and len(initial_structure_refs) > 0:
            for initial_structure_ref in initial_structure_refs:
                new_initial_structure.add_ref(initial_structure_ref.reference.ref)

        ########################################################################
        # Structure
        ########################################################################
        new_assignments = Assignments.create(other.structure.assignments.atomic_numbers)
        new_rc_sites = RepresentativeSites.create(
            reduced_coordgroups=other.structure.rc_sites.reduced_coordgroups,
            hall_symbol=other.structure.rc_sites.hall_symbol
        )
        new_rc_cell = Cell.create(
            basis=other.structure.rc_cell.basis,
            lattice_system=other.structure.rc_cell.lattice_system
        )
        new_structure = Structure(
            new_assignments,
            new_rc_sites,
            new_rc_cell
        )

        structure_tags = other.structure.get_tags()
        if structure_tags is not None and len(structure_tags) > 0:
            for name, tag in structure_tags.items():
                new_structure.add_tag(name, tag.value)

        structure_refs = other.structure.get_refs()
        if structure_refs is not None and len(structure_refs) > 0:
            for structure_ref in structure_refs:
                new_structure.add_ref(structure_ref.reference.ref)

        ########################################################################
        # Method descriptions
        ########################################################################
        new_methods = []
        for m in other.method_descriptions.methods:
            new_references = []
            for r in m.references:
                new_authors = []
                for a in r.authors:
                    new_authors.append(Author.create(a.last_name, a.given_names))
                new_editors = []
                for e in r.editors:
                    new_editors.append(Author.create(a.last_name, a.given_names))
                new_references.append(
                    Reference(
                        ref=r.ref, authors=new_authors, editors=new_editors,
                        journal=r.journal, journal_issue=r.journal_issue,
                        journal_volume=r.journal_volume,
                        page_first=r.page_first, page_last=r.page_last,
                        title=r.title, year=r.year,
                        book_publisher=r.book_publisher,
                        book_publisher_city=r.book_publisher_city,
                        book_title=r.book_title
                    )
                )
            new_method = Method(
                name=m.name,
                description=m.description,
                references=new_references
            )
            new_methods.append(new_method)
        new_method_descriptions = MethodDescriptions(new_methods)

        return Result_AIMDResult(
            total_energy = other.total_energy,
            computation = new_computation,
            initial_structure = new_initial_structure,
            structure = new_structure,
            temperature = other.temperature,
            VEC = other.VEC,
            elastic_tensor = ElasticTensor(other.elastic_tensor._matrix, other.elastic_tensor._nan_mask),
            compliance_tensor = ElasticTensor(other.compliance_tensor._matrix, other.compliance_tensor._nan_mask),
            third_order_elastic_tensor = ThirdOrderElasticTensor(
                other.third_order_elastic_tensor._matrix,
                other.third_order_elastic_tensor._nan_mask,
                other.third_order_elastic_tensor._shape,
            ),
            ultimate_tensile_strain = PlaneDependentTensor(
                other.ultimate_tensile_strain._matrix,
                other.ultimate_tensile_strain._nan_mask,
                other.ultimate_tensile_strain._shape,
            ),
            ultimate_shear_strain = PlaneDependentTensor(
                other.ultimate_shear_strain._matrix,
                other.ultimate_shear_strain._nan_mask,
                other.ultimate_shear_strain._shape,
            ),
            ultimate_tensile_strength = PlaneDependentTensor(
                other.ultimate_tensile_strength._matrix,
                other.ultimate_tensile_strength._nan_mask,
                other.ultimate_tensile_strength._shape,
            ),
            ultimate_shear_strength = PlaneDependentTensor(
                other.ultimate_shear_strength._matrix,
                other.ultimate_shear_strength._nan_mask,
                other.ultimate_shear_strength._shape,
            ),
            tensile_toughness = PlaneDependentTensor(
                other.tensile_toughness._matrix,
                other.tensile_toughness._nan_mask,
                other.tensile_toughness._shape,
            ),
            tensile_resilience = PlaneDependentTensor(
                other.tensile_resilience._matrix,
                other.tensile_resilience._nan_mask,
                other.tensile_resilience._shape,
            ),
            tensile_elastic_strain_limit = PlaneDependentTensor(
                other.tensile_elastic_strain_limit._matrix,
                other.tensile_elastic_strain_limit._nan_mask,
                other.tensile_elastic_strain_limit._shape,
            ),
            tensile_plastic_strain_range = PlaneDependentTensor(
                other.tensile_plastic_strain_range._matrix,
                other.tensile_plastic_strain_range._nan_mask,
                other.tensile_plastic_strain_range._shape,
            ),
            tensile_fracture_strain = PlaneDependentTensor(
                other.tensile_fracture_strain._matrix,
                other.tensile_fracture_strain._nan_mask,
                other.tensile_fracture_strain._shape,
            ),
            tensile_plastic_energy_density = PlaneDependentTensor(
                other.tensile_plastic_energy_density._matrix,
                other.tensile_plastic_energy_density._nan_mask,
                other.tensile_plastic_energy_density._shape,
            ),
            slip_induced_plasticity_at_crack_tips = PlaneDependentTensor(
                other.slip_induced_plasticity_at_crack_tips._matrix,
                other.slip_induced_plasticity_at_crack_tips._nan_mask,
                other.slip_induced_plasticity_at_crack_tips._shape,
            ),
            shear_modulus_tensor = PlaneDependentTensor(
                other.shear_modulus_tensor._matrix,
                other.shear_modulus_tensor._nan_mask,
                other.shear_modulus_tensor._shape,
            ),
            K_VRH = other.K_VRH,
            G_VRH = other.G_VRH,
            E_VRH = other.E_VRH,
            G_over_B = other.G_over_B,
            method_descriptions = new_method_descriptions,
            material_id = MaterialId(new_computation.manifest_hash),
        )
