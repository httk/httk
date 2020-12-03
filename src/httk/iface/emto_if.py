import os
import numpy as np
import httk
from httk.core import *
from pyemto.examples.emto_input_generator import EMTO

def structure_to_inputfiles(f, struct, comment=None, primitive_cell=True):
    if comment is None:
        comment = structure_to_comment(struct)
    if primitive_cell:
        basis = struct.pc.uc_basis
        coords = struct.pc.uc_reduced_coords
        vol = struct.pc.uc_volume
        counts = struct.pc.uc_counts
    else:
        basis = struct.uc_basis
        coords = struct.uc_reduced_coords
        vol = struct.uc_volume
        counts = struct.uc_counts

    species = []
    for s, c in zip(struct.symbols, counts):
        for _ in range(c):
            species.append(s)

    emtopath = os.getcwd()
    latpath = emtopath
    input_creator = EMTO(folder=emtopath,
                         EMTOdir='/home/hpleva/emtox-2014')

    input_creator.prepare_input_files(
        latpath=latpath,
        prims=basis.to_floats(),
        basis=coords.to_floats(),
        species=species,
        coords_are_cartesian=False,
        find_primitive=True,
        )

    sws_range = np.array([2.5])
    input_creator.write_bmdl_kstr_shape_input()
    input_creator.write_kgrn_kfcd_swsrange(sws=sws_range)

def structure_to_comment(struct):
    tags = struct.get_tags().values()
    if len(tags) > 0:
        tagstr = " tags: " + ", ".join([tag.tag+":"+tag.value for tag in tags])
    else:
        tagstr = ""
    if struct.has_rc_repr and struct.has_uc_repr:
        return struct.formula + " " + struct.hexhash + tagstr
    else:
        return struct.formula + " " + tagstr
