from httk.atomistic.cell import Cell

from httk.core.basic import *
from httk.core.vectors import FracVector, FracScalar
from httk.core.httkobject import HttkObject, HttkPluginPlaceholder, httk_typed_property, httk_typed_property_resolve, httk_typed_property_delayed, httk_typed_init

import math
from scipy import fft
import numpy as np
from copy import deepcopy
from collections import defaultdict
import struct

# constants used in VASP
AUtoA    = FracScalar.create(0.529177249)  # 1 a.u. in Angstrom
RYtoEV   = FracScalar.create(13.605826)    # 1 Ry in eV
kinE_prefactor = RYtoEV * AUtoA**2         # equivalent to hbar**2/(2*m_e)
PI       = FracScalar.create(3.141592653589793238)

def gen_kgrid(grid_size, gamma, gamma_half='x'):
    """
    Generates the (rectangular) kgrid containing all states fulfilling G**2 / 2 < ENCUT
    """
    fx,fy,fz = [np.arange(grid_size[i]) - grid_size[i]//2 for i in range(3)]
    if gamma:
        if gamma_half == 'x':
            # generate only upper half of x-grid, but on border keep half of y-plane and half of z-line
            fx = fx[fx >= 0]
            filter_func = lambda k: (k[:,0] > 0) | ((k[:,0] == 0) & (k[:,1] > 0)) | ((k[:,0] == 0) & (k[:,1] == 0) & (k[:,2] >= 0))

        elif gamma_half == 'z':
            # generate only upper half of z-grid, but on border keep half of y-plane and half of x-line
            fz = fz[fz >= 0]
            filter_func = lambda k: (k[:,2] > 0) | ((k[:,2] == 0) & (k[:,1] > 0)) | ((k[:,2] == 0) & (k[:,1] == 0) & (k[:,0] >= 0))
        else:
            raise ValueError('Unknown gamma-halving scheme provided {}'.format(gamma_half))
    else:
        filter_func = lambda k: np.ones(k.shape[0], dtype=bool)

    fxyz = np.array(np.meshgrid(fx,fy,fz)).T.reshape(-1,3)
    filter_array = filter_func(fxyz)
    kgrid = fxyz[filter_array]
    
    return kgrid

def gen_gvecs(kgrid, kvec, basis, encut):
    """
    Generates the G-vectors fullfilling the cutoff condition |k + G|**2/2 < ENCUT

    Input
    kgrid: Rectangular kgrid containing states
    kvec: Reciprocal vector for k, as a list or numpy row vector
    basis: Supercell vectors
    encut: The energy cutoff to use

    Returns numpy array of row vectors representing fulfilling G-vectors
    """
    cell = FracVector.use(basis)
    kvec = np.array(kvec)
    R_cell = np.array((2*PI*cell.reciprocal()).to_floats())
    encut = float(encut)
    E_kin = kinE_prefactor.to_float() * np.linalg.norm(np.matmul(kgrid + kvec, R_cell), axis=1)**2
    gvecs = kgrid[E_kin < encut]

    return gvecs

def to_real_wave(plane_wave, grid_size, gvecs, gamma=False, gamma_half='x'):
    """
    Fourier-transform the given plane-wave coefficients into a real-space wavefunction

    Input
    plane_wave: Plane wave coefficients (numpy array)
    gvecs: g-vectors for each coefficient
    gamma: if the wavefunction is gamma-compressed
    gamma_half: which axis of k-space gamma-compression was done along

    Output
    Numpy array with real-space wave functions. Let the calling function determine if conversion to FracVector is necessary
    """

    if gamma:
        if gamma_half == 'x':
            phi = np.zeros((grid_size[0]//2+1, grid_size[1], grid_size[2]), dtype=complex)
        elif gamma_half == 'z':
            phi = np.zeros((grid_size[0], grid_size[1], grid_size[2]//2+1), dtype=complex)
        else:
            raise ValueError('Unrecognized gamma-half argument. z or x is supported')
    else:
        phi = np.zeros(grid_size, dtype=complex)

    phi[gvec[:,0], gvec[:,1], gvec[:,2]] = plane_wave
    normalization = np.sqrt(np.prod(np.array(grid_size)))

    if gamma:
        x,y,z = [np.arange(-grid_size[i]//2, 0) for i in range(3)]
        if gamma_half == 'x':
            # fill y and z-axis for fourier transform
            x = [0]
            axis=0
        elif gamma_half == 'z':
            # fill x and y-axis for fourier transform
            z = [0]
            axis=2

        xyz = np.array(np.meshgrid(x,y,z)).T.reshape((-1,3))
        phi[xyz[:,0],xyz[:,1],xyz[:,2]] = phi[-xyz[:,0],-xyz[:,1],-xyz[:,2]].conjugate()
        phi /= np.sqrt(2)
        phi[0,0,0] *= np.sqrt(2)

        phi_real = fft.irfftn(phi, axes=axis) * normalization
        return phi_real
    else:
        return fft.ifftn(phi) * normalization

def expand_gamma_coeffs(coeffs, grid_size, gvecs, gamma_half='x'):
    wavefunction[gvecs[:,0], gvecs[:,1], gvecs[:,2]] = coeffs

    x,y,z = [np.arange(0,grid_size[i]) - grid_size[i]//2 for i in range(3)]
    if gamma_half == 'x':
        x = x[:grid_size[0]//2 + 1]
    elif gamma_half == 'z':
        z = z[:grid_size[0]//2 + 1]
    else:
        raise ValueError('Unrecognized gamma-half argument. z or x is supported')
    
    xyz = np.array(np.meshgrid(x,y,z)).T.reshape((-1,3))
    wavefunction[xyz[:,0], xyz[:,1], xyz[:,2]] = wavefunction[-xyz[:,0], -xyz[:,1], -xyz[:,2]].conjugate()
    wavefunction /= np.sqrt(2)
    wavefunction[0,0,0] *= np.sqrt(2)
    coeffs = wavefunction[gvecs[:,0], gvecs[:,1], gvecs[:,2]]
    return coeffs 

def reduce_std_coeffs(coeffs, grid_size, std_gvecs, gam_gvecs, gamma_half='x'):
    if gamma_half == 'x':
        axis=0
    elif gamma_half == 'z':
        axis=2
    else:
        raise ValueError('Unrecognized gamma-half argument. z or x is supported')
    
    real_wave = to_real_wave(coeffs, grid_size, std_gvecs, False, gamma_half)

    real_wave = np.sqrt(real_wave.real**2 + real_wave.imag**2)*np.sign(real_wav.real)
    real_wave = fft.rfftn(real_wave, axes=axis)
    real_wave *= np.sqrt(2)
    real_wave[0,0,0] /= np.sqrt(2)

    coeffs = real_wave[gam_gvecs[:,0], gam_gvecs[:,1], gam_gvecs[:,2]]
    return coeffs
    
class PlaneWaveFunctions(HttkObject):
    """
    PlaneWaveFunction is a proxy for a collection of wavefunctions contained in output files of plane-wave basis DFT codes.

    This object stores the energy, occupation and plane-wave coefficients from a calculation, contained in a wavefunction file (e.g. a VASP WAVECAR). The access to the plane-wave coefficients is done in a lazy fashion, only caching the requested orbitals at specified K-points

    In addition, it caches the k-vectors/g-vectors associated with the basis set and parameters necessary to generate these (e.g. VASP energy cutoff)

    NOTE: Currently does not support Spin-Orbit-Coupling (SOC) output formats

    NOTE: As fourier transforms and similar rely on the numpy/scipy/jax library, read-in FracVectors are in working functions converted to numpy arrays during processing
    """

    @httk_typed_init({'nkpts': int, 'nbands': int, 'nspins': int, 'encut': FracScalar, 'cell': Cell, 'kpts': FracVector, 'precision_tag': int, 'eigs': FracVector, 'occups': FracVector, 'pwcoeffs': FracVector})
    def __init__(self, file_ref=None, recpos_func=None, nkpts=None, nbands=None, nspins=None, nplws=None, encut=None, cell=None, kpts=None, kgrid_size=None, double_precision=None, eigs=None, occups=None, pwcoeffs=None, is_gamma=None, gamma_half=None, kgrid=None):
        self.file_ref = file_ref
        self.recpos_func = recpos_func
        self.nkpts = nkpts
        self.nbands = nbands
        self.nspins = nspins
        self.nplws = nplws
        self.encut = encut
        self.cell = cell
        self.kpts = kpts
        self.double_precision = double_precision
        self.eigs = eigs
        self.occups = occups
        self.pwcoeffs = pwcoeffs
        self.kgrid_size = kgrid_size
        self.is_gamma = is_gamma
        self.gamma_half = gamma_half
        self.kgrid = kgrid

    @classmethod
    def create(cls, file_wrapper = None, rec_pos_func=None, nplws=None, encut=None, cell=None, kpts=None, double_precision=None, eigs=None, occups=None, pwcoeffs=None, is_gamma=None, gamma_half='x'):
        """
        Creation function for the proxy object for wavefunctions file.
        """

        if is_gamma is not None and not isinstance(is_gamma, bool):
            raise ValueError('Invalid format of gamma boolean in wavefunction creator. Only boolean values accepted')
    
        locs = locals()
        essential_args = dict([(s, locs[s]) for s in ["encut", "cell", "kpts", "eigs", "occups"]])
        if any([arg is None for arg in essential_args.values()]):
            missing_args = []
            for key,val in essential_args.items():
                if val is None:
                    missing_args.append(key)
            raise ValueError("Invalid arguments for creation of PlaneWaveFunctions object. Missing {}. Either provide all arguments or load using file reference".format(missing_args))
        else:
            # sanitation of given arguments
            nplws = np.array(nplws, dtype=int)
            encut = FracScalar.use(encut)
            cell = Cell.use(cell)
            kpts = np.array(kpts)
            eigs = np.array(eigs)
            occups = np.array(occups)
            nspins = eigs.shape[0]
            nkpts = kpts.shape[0]
            nbands = eigs.shape[2]

            assert eigs.shape[1] == nkpts, 'Dimensions of eigenvalue array not consistent with k-point list'
            assert nplws.shape[0] == nkpts, 'List of plane-wave array size not consistent with number of k-points'
            assert eigs.shape == occups.shape, 'Dimension of eigenvalue array not consistent with occupation array'

            #G_cut^2 = E_cut^2*hbar^2/2m
            basis_norm = FracVector.create(cell.lengths)
            G_cutoff = (encut / RYtoEV).sqrt() * (basis_norm / AUtoA / (2*PI))
            kgrid_size = np.array([math.ceil(g)*2 + 1 for g in G_cutoff.to_floats()], dtype=int) # could be replaced with element-wise ceil?

            # check if wavefunction format is gamma or not
            print(kpts)
            print(nplws)
            print(encut)
            if nkpts > 1:
                is_gamma = False
                kgrid = gen_kgrid(kgrid_size, False)
            elif (kpts[0] == (0,0,0)).all():
                std_grid = gen_kgrid(kgrid_size, False, gamma_half)
                gam_grid = gen_kgrid(kgrid_size, True, gamma_half)
                std_gvecs = gen_gvecs(std_grid, (0,0,0), cell.basis, encut)
                gam_gvecs = gen_gvecs(gam_grid, (0,0,0), cell.basis, encut)
                if std_gvecs.shape[0] == nplws[0]:
                    is_gamma = False
                    kgrid = std_grid
                elif gam_gvecs.shape[0] == nplws[0]:
                    is_gamma = True
                    kgrid = gam_grid
                else:
                    raise ValueError('No. of planewaves inconsistent! Cannot determine format of wavefunctions. {} {} {}'.format(std_gvecs.shape[0], gam_gvecs.shape[0], nplws[0]))

        if file_wrapper is not None and rec_pos_func is not None and double_precision is not None:
            pwcoeffs = defaultdict(None)
            
        elif pwcoeffs is not None:
            # expect one of two formats:
                # a nested list of all wavefunctions, nested with size according to nbands, nspin, nkpts
                # a dictionary with key tuples (spin, kpt, band) containing list-like object of coeffs
            if isinstance(pwcoeffs, list) or isinstance(pwcoeffs, tuple):
                # check lengths of nested lists and turn list into dictionary
                dict_pwcoeffs = defaultdict(None)
                assert len(pwcoeffs) == nspins, 'Invalid format of given plane-wave coefficients'
                for i in range(nspins):
                    assert len(pwcoeffs[i]) == nkpts, 'Invalid format of given plane-wave coefficients'
                    for j in range(nkpts):
                        assert len(pwcoeffs[i][j]) == nbands, 'Invalid format of given plane-wave coefficients'
                        for k in range(nbands):
                            assert len(pwcoeffs[i][j][k]) == nplws[j], 'Invalid format of given plane-wave coefficients'
                            dict_pwcoeffs[(i+1,j+1,k+1)] = pwcoeffs[i][j][k]
                pwcoeffs = dict_pwcoeffs
            elif isinstance(pwcoeffs, dict):
                assert len(pwcoeffs) == nspins*nkpts*nbands, 'Invalid format of given plane-wave coefficients' 
            else:
                raise ValueError('Invalid format of given plane-wave coefficients. Do not know what to do with this type {}'.format(type(pwcoeffs)))
        else:
            raise ValueError("Invalid arguments for creation of PlaneWaveFunctions object. Either file_wrapper and function to record positions must be given, OR all coefficients directly given. file_wrapper={}, rec_pos_func={}, pwcoeffs={}".format(file_wrapper, rec_pos_func, pwcoeffs))

        return PlaneWaveFunctions(file_ref=file_wrapper, recpos_func=rec_pos_func, nkpts=nkpts, nbands=nbands, nspins=nspins, encut=encut, cell=cell, kpts=kpts, double_precision=double_precision, eigs=eigs, occups=occups, pwcoeffs=pwcoeffs, nplws=nplws, kgrid_size=kgrid_size, is_gamma=is_gamma, gamma_half=gamma_half, kgrid=kgrid)

    def get_plws(self, spin, kpt, band, cache=True):
        assert 1 <= spin <= self.nspins
        assert 1 <= kpt <= self.nkpts
        assert 1 <= band <= self.nbands

        if (spin,kpt,band) in self.pwcoeffs:
            return self.pwcoeffs[(spin,kpt,band)]
        else:
            plws = self.read_plws(spin, kpt, band)
            if cache:
                self.pwcoeffs[(spin,kpt,band)] = plws
            return plws

    def read_plws(self, spin, kpt, band):
        if self.file_ref is not None:
            file_pos = self.recpos_func(spin, kpt, band)
            self.file_ref.seek(file_pos)
            array_size = self.nplws[kpt-1]
            type_id = np.complex128 if self.double_precision else np.complex64
            coeffs = np.fromfile(self.file_ref, dtype=type_id, count=array_size)
            #coeffs = struct.unpack(type_id*2*array_size, self.file_ref.read(2*array_size))
            #coeffs = (FracVector.create([i for i in coeffs[::2]]), FracVector.create([i for i in coeffs[1::2]]))
            return coeffs
        else:
            raise ValueError('Wavefunction file reference non-existent. Failed to read file') 

    def get_gvecs(self, kpt_ind=None, kpt=None, gamma=None, gamma_half=None, cache=True):
        if kpt_ind is not None:
            assert 1 <= kpt_ind <= self.nkpts
            kpt = self.kpts[kpt_ind]

        if tuple(kpt) in self.gvecs:
            return self.gvecs[tuple(kpt)]
        
        if gamma is None:
            gamma = self.is_gamma
        elif gamma != self.is_gamma:
            cache = False
        if gamma_half is None:
            gamma_half = self.gamma_half
        elif gamma_half != self.gamma_half:
            cache = False
        
        kgrid = gen_krid(self.grid_size, gamma, gamma_half)
        gvecs = gen_gvecs(kgrid, kpt, self.cell.basis, self.encut)
            
        if cache:
            self.gvecs[tuple(kpt)] = gvecs 
        return gvecs
              


    def get_wavr(self, spin, kpt, band):
        assert 1 <= spin <= self.nspins
        assert 1 <= kpt <= self.nkpts
        assert 1 <= band <= self.nbands
        
        plane_wave = self.get_plws(spin, kpt, band)
        gvecs = self.gvec_list[kpt-1]
        real_space_wave = to_real_wave(plane_wave, self.kgrid_size, gvecs=gvecs, gamma=self.is_gamma, gamma_half=self.gamma_half)

        return real_space_wave
        #return (FracVector.create(real_space_wave.real())),
        #        FracVector.create(real_space_wave)))

    def copy(self, spins=None, kpts=None, bands=None, file_ref=None, format=None, gamma_half='x'):
        if bands is None:
            bands = np.arange(self.nbands) + 1
        else:
            assert len(bands) > 0, 'Empty band list provided'
            bands = np.array(bands)
            assert (1 <= bands & bands <= self.nbands).all(), 'Provided bands out of bounds of %d and %d' % (1, self.nbands)
        
        if kpts is None:
            kpts = np.arange(self.nkpts) + 1
        else:
            assert len(kpts) > 0, 'Empty k-point list provided'
            kpts = np.array(kpts)
            assert (1 <= kpts & kpts <= self.nkpts).all(), 'Provided kpoint indices out of bounds of %d and %d' % (1, self.nkpts)
        if format is not None:
            if format == 'gamma':
                to_gamma = True
                assert len(kpts) == 1 and np.norm(kpts[0]) == 0, 'Cannot convert to gamma format, more than gamma-point specified'
            elif format == 'std':
                to_gamma = False
            else:
                raise ValueError('Invalid wavecar format specified, only "std" and "gamma" are currently supported')
            if to_gamma != self.is_gamma:
                convert = True
        else:
            to_gamma = self.is_gamma
            convert = False
        nspins = len(spins)
        nbands = len(bands)
        nkpts = len(kpts)

        if file_ref is None:
            ### make copy in memory
            new_coeffs = {}
            new_eigs = np.zeros((nspins, nkpts, nbands))
            new_occups = np.zeros((nspins, nkpts, nbands), dtype=int)
            for s_i,s in enumerate(spins):
                for k_i,k in enumerate(kpts):
                    if convert and to_gamma:
                        std_gvecs = get_gvecs(kpt_ind=k, gamma=False)
                        gam_gvecs = get_gvecs(kpt_ind=k, gamma=True, gamma_half=gamma_half)
                    for b_i,b in enumerate(bands):
                        coeffs = self.get_plws(s, k, b, cache=False)
                        if convert:
                            if to_gamma:
                                coeffs = reduce_std_coeffs(coeffs, self.grid_size, std_gvecs, gam_gvecs, gamma_half)
                            else:
                                coeffs = expand_gamma_coeffs(coeffs, self.grid_size, gam_gvecs, self.gamma_half)
                        new_coeffs[(s_i,k_i,b_i)] = coeffs
                        new_eigs[s_i,k_i,b_i] = self.eigs[s-1,k-1,b-1]
                        new_occups[s_i,k_i,b_i] = self.occups[s-1,k-1,b-1]

            # convert to desired format

            # make new object
            new_wavefuncs = PlaneWaveFunctions.create(nkpts=nkpts, nbands=nbands, nspins=nspins, nplws=self.nplws, encut=self.encut, cell=self.cell, kpts=kpts, double_precision=self.double_precision, eigs=new_eigs, occups=new_occups, pw_coeffs=new_coeffs, is_gamma=to_gamma, gamma_half=gamma_half)

        else:
            ### Write a copy to file
            name_wrapper = IoAdapterFilename.use(file_ref)
            write_wav(name_wrapper, self, bands=bands, spins=spins, kpts=kpts, format=format, gamma_half=gamma_half)
            new_wavefuncs = open_wav(name_wrapper)
        
        return new_wavefuncs

    
