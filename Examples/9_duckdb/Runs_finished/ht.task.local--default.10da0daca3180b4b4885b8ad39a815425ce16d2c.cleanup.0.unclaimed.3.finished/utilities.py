import sys
import numpy as np
import configparser


def elastic_config():
    config = configparser.ConfigParser()
    config.read("../settings.elastic")
    # The type of symmetry
    try:
        sym = config["elastic"]["symmetry"].lstrip()
    except:
        sym = "cubic"

    # Use projection technique, i.e. to obtain cubic elastic
    # constants for non-cubic crystals, such as SQS supercells.
    try:
        project = eval(config["elastic"]["projection"])
    except:
        project = False

    # Delta values:
    tmp = config["elastic"]["delta"].lstrip().split("\n")
    deltas = []
    for line in tmp:
        line = line.split()
        deltas.append([float(x) for x in line])

    # Distortions in Voigt notation:
    distortions = []
    tmp = config["elastic"]["distortions"].lstrip().split("\n")
    for line in tmp:
        line = line.split()
        distortions.append([float(x) for x in line])

    # Generate the additional distortions, if projection is used:
    # For cubic systems, the projected elastic constants are
    # an average of elastic constants calculated along the different
    # permutations of the xyz-axes: xyz -> yzx -> zxy.
    # In terms of Voigt notation, the additional distortions along the two
    # other axes are:
    # 1 2 3 4 5 6 -> 2 3 1 5 6 4 (xyz -> yzx),
    # 1 2 3 4 5 6 -> 3 1 2 6 4 5 (xyz -> zxy).
    # Also, check if the new distortion was already included in the set of
    # distortions.
    if project:
        if sym == "cubic":
            new_distortions = []
            new_deltas = []
            for d, delta in zip(distortions, deltas):
                new_distortions.append(d)
                new_deltas.append(delta)
                xyz_to_yzx = [d[1], d[2], d[0], d[4], d[5], d[3]]
                xyz_to_zxy = [d[2], d[0], d[1], d[5], d[3], d[4]]
                for new_d in (xyz_to_yzx, xyz_to_zxy):
                    include_new_d = True
                    for dd in distortions:
                        if vectors_are_same(dd, new_d):
                            # print(dd)
                            # print(new_d)
                            # print("vectors are same!")
                            # print()
                            include_new_d = False
                            break
                    if include_new_d:
                        new_distortions.append(new_d)
                        new_deltas.append(delta)
        else:
            raise NotImplementedError("Projection technique only implemented for cubic systems!")

        distortions = new_distortions
        deltas = new_deltas

    return sym, deltas, distortions, project

def vectors_are_same(v1, v2):
    """Check whether all elements of two vectors are the same,
    within some tolerance."""
    tol = 1e-5
    max_diff = np.max(np.abs(np.array(v1) - np.array(v2)))
    if max_diff > tol:
        return False
    else:
        return True

def get_dist_matrix(array):
    return np.array([
        [1+array[0], array[5]/2, array[4]/2],
        [array[5]/2, 1+array[1], array[3]/2],
        [array[4]/2, array[3]/2, 1+array[2]]
    ])

def distort(dist_mat, mat):
    """Apply distortion matrix"""
    array = np.array(mat)
    for i in range(len(mat)):
        array[i, :] = np.array([np.sum(dist_mat[0, :]*mat[i, :]),
                                np.sum(dist_mat[1, :]*mat[i, :]),
                                np.sum(dist_mat[2, :]*mat[i, :])])
    return array

def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.

    :param axis:
    :type axis:
    :param theta:
    :type theta:
    """
    axis = np.asarray(axis)
    theta = np.asarray(theta)
    axis = axis/np.linalg.norm(axis)
    a = np.cos(theta/2.0)
    b, c, d = -axis*np.sin(theta/2.0)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d
    return np.array([[aa+bb-cc-dd, 2*(bc+ad), 2*(bd-ac)],
                     [2*(bc-ad), aa+cc-bb-dd, 2*(cd+ab)],
                     [2*(bd+ac), 2*(cd-ab), aa+dd-bb-cc]])

# def rotate_dist_matrix(m, from_axis=1, to_axis=1):

