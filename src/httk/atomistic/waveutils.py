import numpy as np

def compare_wavefuncs(wobj1, wobj2, spin1, kind1, band1, spin2, kind2, band2):
    """
    Performs the wavefunction overlap of two wavefunctions from given planewave objects.
    
    Input:
    obj1, wobj2: PlaneWaveObjects wrapping the wavefunction data
    spin1, spin2: spin index of the wavefunction, in respective objects (from 1)
    kind1, kind2: kind index of the wavefunction, in respective objects (from 1)
    band1, band2: band index of the wavefunction, in respective objects (from 1)
   
    Output:
    similarity: the absolute value of the overlap integral
    phase: the phase of the overlap integral (in degrees)
    overlap: the overlap integral itself
    """
    func1 = wobj1.get_wavr(spin1, kind1, band1)
    func2 = wobj2.get_wavr(spin2, kind2, band2)

    overlap = np.sum(np.conjugate(func1) * func2)
    similarity = np.abs(overlap)
    phase = np.angle(similarity, deg=True)

    return similarity, phase, overlap

#def dipole_moment(wobj1, wobj2, s1, k1, b1, s2, k2, b2):
#
#    phi1 = wobj1.get_coeffs(s1, k1, b1)
#    phi2 = wobj2.get_coeffs(s2, k2, b2)


