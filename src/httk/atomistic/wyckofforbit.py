from httk.core.httkobject import HttkObject
import numpy as np
from httk.atomistic.data.symmetry_wyckoff import Spacegroup

class WyckoffOrbit(HttkObject):
    def __init__(self,
                 space_number=None,
                 letter=None,
                 specie_name=None,
                 multiplicity=None,
                 basis=None,
                 freedom_degr=None,
                 possible_bases=None,):
        self._space_number = space_number
        self._letter = letter
        self._specie_name = specie_name
        self._multiplicity = multiplicity
        self._basis = basis
        self._freedom_degr = freedom_degr
        self._possible_bases = possible_bases

    def __str__(self):
        return_str = ""
        return_str += str(self._specie_name)+"\t"
        return_str += str(self._letter)+"\t"
        return_str += str(self._multiplicity)+"\t"
        return_str += ", ".join(str(x)[0] for x in self._freedom_degr)+"\t\t"
        return_str += ", ".join(str(round(x, 2)) for x in self._basis)+"\n"
        return return_str

    def __copy__(self):
        new_freedom_degr = []
        for bool_val in self._freedom_degr:
            new_freedom_degr.append(bool_val)
        new_basis = []
        for basis_val in self._basis:
            new_basis.append(basis_val)
        new_possible_bases = []
        for possible_basis in self._possible_bases:
            new_possible_basis = []
            for basis_val in possible_basis:
                new_possible_basis.append(basis_val)
            new_possible_bases.append(new_possible_basis)
        new_wyckoff = WyckoffOrbit(space_number=self._space_number,
                                   letter=self._letter,
                                   specie_name=self._specie_name,
                                   multiplicity=self._multiplicity,
                                   basis=new_basis,
                                   freedom_degr=new_freedom_degr,
                                   possible_bases=new_possible_bases)
        return new_wyckoff
    
    @classmethod
    def create_from_sites(cls, space_number, letter, fractional_sites):
        s = Spacegroup(space_number)
        try:
            degr_freedom = repr(s[letter])
        except Exception as e:
            print(e)
            print(space_number)
            print(letter)
            print(fractional_sites)
        degr_freedom = degr_freedom[degr_freedom.find("["):]
        degr_freedom = [x.strip() == "True" for x in degr_freedom.strip("[]").split(",")]
        possible_bases = []
        for coordinate in fractional_sites:
            candidate_pos = s[letter].affinedot(coordinate)
            if len(candidate_pos) != len(fractional_sites):
                print("not all fractional sites given")
            found_match = True
            for pos_1 in fractional_sites:
                found_match = False
                for pos_2 in candidate_pos:
                    if (np.round(pos_1, 8) == np.round(pos_2, 8)).all():
                        found_match = True
                        break
                if not found_match:
                    break
            if found_match:
                possible_bases.append(coordinate)
        return cls(space_number=space_number,
                   letter=letter,
                   specie_name=None,
                   multiplicity=len(fractional_sites),
                   basis=possible_bases[0],
                   freedom_degr=degr_freedom,
                   possible_bases=possible_bases)
    
    def push_coords_to_unit(self):
        self._basis = np.mod(self._basis, 1.0)
        new_possible_bases = []
        for possible_basis in self._possible_bases:
            new_possible_bases.append(np.mod(possible_basis, 1.0))
        self._possible_bases = new_possible_bases

    def change_basis(self, new_basis):
        for possible_basis in self._possible_bases:
            if np.round(new_basis, 8) == np.round(possible_basis, 8):
                self._basis = possible_basis
                return True
        return False
    
    def get_pos_from_wyckoff(self, other_basis=None, move_to_unit=True, species=None):
        s = Spacegroup(self._space_number)
        if other_basis is not None:
            if move_to_unit:
                positions = np.mod(np.round(s[self._letter].affinedot(other_basis), 8), 1.0)
            else:
                positions = np.round(s[self._letter].affinedot(other_basis), 8)
        else:
            if move_to_unit:
                positions = np.mod(np.round(s[self._letter].affinedot(self._basis), 8), 1.0)
            else:
                positions = np.round(s[self._letter].affinedot(self._basis), 8)
        if species:
            for specie in species:
                if specie["name"] == self._specie_name:
                    species_sites=[specie["chemical_symbols"][0]] * len(positions)
                    species_sites_numbers=[specie["atomic_numbers"][0]] * len(positions)
                    return positions, species_sites, species_sites_numbers
        else:
            return positions

    def set_new_basis(self, new_basis):
        new_basis = np.round(new_basis, 8)
        all_pos = self.get_pos_from_wyckoff(self, other_basis=new_basis, move_to_unit=False)
        possible_bases = []
        for candidate in all_pos:
            new_candidates = self.get_pos_from_wyckoff(self, other_basis=candidate, move_to_unit=False)
            found_match = True
            for pos_1 in all_pos:
                found_match = False
                for pos_2 in new_candidates:
                    if (np.round(pos_1, 8) == np.round(pos_2, 8)).all():
                        found_match = True
                        break
                if not found_match:
                    break
            if found_match:
                possible_bases.append(candidate)
        self._basis = new_basis
        self._possible_bases = possible_bases

    def __eq__(self, other):
        return (self._space_number == other._space_number and
                self._letter == other._letter and
                self._specie_name == other._specie_name and
                self._multiplicity == other._multiplicity)
    
    def __ne__(self, other):
        return (self._space_number != other._space_number or
                self._letter != other._letter or
                self._specie_name != other._specie_name or
                self._multiplicity != other._multiplicity)
    
    def __lt__(self, other):
        if self._space_number == other._space_number:
            if self._letter == other._letter:
                return self._specie_name < other._specie_name
            else:
                return self._letter < other._letter
        else:
            return self._space_number < other._space_number
    
    def __gt__(self, other):
        if self._space_number == other._space_number:
            if self._letter == other._letter:
                return self._specie_name > other._specie_name
            else:
                return self._letter > other._letter
        else:
            return self._space_number > other._space_number