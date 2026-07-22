# -*- coding: utf-8 -*-
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2022 Henrik Levämäki
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
from httk.core import Computation, Code, Signature, SignatureKey
from httk.atomistic.representativesites import RepresentativeSites
from httk.atomistic import Assignments, Cell
from httk.atomistic import Structure
from httk.atomistic.results.utils import ElasticTensor
from httk.atomistic.results.utils import MethodDescriptions, Method
from httk.atomistic.results.utils import InitialStructure, MaterialId
from httk.atomistic.assignments import Assignments
from httk.core.reference import Reference, Author

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
        'initial_structure': InitialStructure,
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
        'rundir': str,
        'method_descriptions': MethodDescriptions,
        'material_id': MaterialId,
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
        rundir,
        method_descriptions,
        material_id,
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
        self.rundir = rundir
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
                    new_editors.append(Author.create(e.last_name, e.given_names))
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

        return Result_ElasticResult(
            total_energy = other.total_energy,
            computation = new_computation,
            initial_structure = new_initial_structure,
            structure = new_structure,
            temperature = other.temperature,
            elastic_tensor = ElasticTensor(other.elastic_tensor._matrix, other.elastic_tensor._nan_mask),
            elastic_tensor_nosym = ElasticTensor(other.elastic_tensor_nosym._matrix, other.elastic_tensor_nosym._nan_mask),
            compliance_tensor = ElasticTensor(other.compliance_tensor._matrix, other.compliance_tensor._nan_mask),
            K_V = other.K_V,
            K_R = other.K_R,
            K_VRH = other.K_VRH,
            G_V = other.G_V,
            G_R = other.G_R,
            G_VRH = other.G_VRH,
            mu_VRH = other.mu_VRH,
            E_VRH = other.E_VRH,
            mechanically_stable = other.mechanically_stable,
            mechanically_stable_with_tolerance = other.mechanically_stable_with_tolerance,
            atomic_relaxations = other.atomic_relaxations,
            rundir = other.rundir,
            method_descriptions = new_method_descriptions,
            material_id = MaterialId(new_computation.manifest_hash),
        )
