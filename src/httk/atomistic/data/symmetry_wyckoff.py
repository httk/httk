"""
__author__ = "Abhijith S Parackal"
__date__ =   2013/05/10
__email__ = "abhpa50@liu.se"
"""

import json
from dataclasses import dataclass
from numpy.typing import ArrayLike
from os.path import abspath, dirname, join
from typing import List, Generator, Union
import numpy as np


@dataclass
class WyckoffPosition:
    """
    A lightweight container to hold a wyckoff position. The TinySpaceGroup class holds a list of these objects.

    Parameters
    ----------
    letter : str
        The wyckoff_letters of the wyckoff position
    multiplicity : int
        The multiplicity of the wyckoff position
    hasfreedom : List[bool]
        A list of three booleans indicating whether the wyckoff position has freedom along the three lattice vectors
    affine : ArrayLike
        A 3x4 affine matrix that transforms the wyckoff position to the origin

    """

    def __init__(
        self, letter: str, multiplicity: int, hasfreedom: List[bool], affine: ArrayLike
    ):

        self.letter = letter
        self.multiplicity = multiplicity
        self.hasfreedom = hasfreedom
        self.affine = np.array(affine)

    def __repr__(self):
        return f"wyckoff_letters {self.multiplicity}{self.letter} with freedom {self.hasfreedom}"

    def __len__(self):
        return len(self.affine)

    def affinedot(self, coordinate: ArrayLike) -> ArrayLike:
        # Created by abhpa50@liu
        """
        Apply the affine transformation to the given coordinate. returns all the images of the coordinate (multiplicity)

        Parameters
        ----------
        coordinate : ArrayLike
            fractional coordinate of the representative atom of shape (3,)

        Returns
        -------
        ArrayLike
            The transformed coordinates of shape (multiplicity, 3)

        """
        coordinate = np.concatenate([coordinate, [1]])
        #return np.mod(np.dot(self.affine, coordinate)[..., :3], 1.0)
        return np.dot(self.affine, coordinate)[..., :3]


class Spacegroup:
    """A light-weight container to hold a spacegroup. The TinySpaceGroup class holds a list of WyckoffPosition objects.

    Parameters
    ----------
    spgp : int
        The spacegroup number

    Examples
    ---------
    >>> spg = Spacegroup(225)
    >>> spg['a'] # get the wyckoff position with wyckoff_letters 'a'
    wyckoff_letters 4a with freedom [False, False, False]
    >>> spg[0] # get the wyckoff position with index 0
    wyckoff_letters 4a with freedom [False, False, False]
    """

    _dataset = None

    def __init__(self, spgp: int) -> None:

        if not Spacegroup._dataset:
            module_dir = dirname(abspath(__file__))
            spgpinfo = join(module_dir, "spgpinfo")
            with open(spgpinfo, "r") as file:
                Spacegroup._dataset = json.load(file)

        self.spgp = spgp
        self.data = Spacegroup._dataset[str(spgp)]
        self.symbol: str = self.data["symbol"]
        wyckoff: List[WyckoffPosition] = []
        let: List[str] = []
        for key, val in list(self.data.items())[1:]:
            let.append(key)
            wyckoff.append(WyckoffPosition(key, **val))
        self.wyckoff = tuple(wyckoff)
        self.wyckoff_letters = tuple(let)

    @property
    def crystal_system(self) -> str:
        """The crystal system of the spacegroup"""
        if self.spgp <= 2:
            return "triclinic"
        elif self.spgp <= 15:
            return "monoclinic"
        elif self.spgp <= 74:
            return "orthorhombic"
        elif self.spgp <= 142:
            return "tetragonal"
        elif self.spgp <= 167:
            return "trigonal"
        elif self.spgp <= 194:
            return "hexagonal"
        else:
            return "cubic"

    def __repr__(self):
        a = f"Spacegroup no: {self.spgp}, symbol: {self.symbol} \n"
        for e in self:
            a = a + e.__repr__() + "\n"
        return a

    def __iter__(self) -> Generator[WyckoffPosition, None, None]:
        yield from self.wyckoff

    def __getitem__(self, idx: Union[str, int]):
        """Get the wyckoff position with the given wyckoff_letters or index

        Parameters
        ----------
        idx : Union[str, int]
            The wyckoff_letters or index of the wyckoff position

        Returns
        -------
        WyckoffPosition
            The wyckoff position

        """
        if isinstance(idx, str):
            return self.wyckoff[self.wyckoff_letters.index(idx)]
        return self.wyckoff[idx]

    def __len__(self):
        return len(self.wyckoff)

