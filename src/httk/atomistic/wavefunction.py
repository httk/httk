from httk.atomistic.cell import Cell

from httk.core.basic import *
from httk.core.vectors import FracVector, FracScalar
from httk.core.httkobject import HttkObject, HttkPluginPlaceholder, httk_typed_property, httk_typed_property_resolve, httk_typed_property_delayed, httk_typed_init
from httk.core.ioadapters import IoAdapterFilename



import math
from scipy import fft
from copy import deepcopy
from collections import defaultdict
import numpy as np
#from numba import njit

# constants used in VASP
AUtoA    = FracScalar.create(0.529177249)  # 1 a.u. in Angstrom
RYtoEV   = FracScalar.create(13.605826)    # 1 Ry in eV
kinE_prefactor = RYtoEV * AUtoA**2         # equivalent to hbar**2/(2*m_e)
PI       = FracScalar.create(3.141592653589793238)

def gen_kgrid(grid_size, gamma, gamma_half="x"):
    """
    Generates the (rectangular) kgrid containing all k-states within the given grid size (excluding gamma-compressed states if specified).
    
    Input:
    grid_size: Size of the kgrid in each dimension (must be ueven)
    gamma: If the kgrid is gamma-compressed (True) or not (False)
    gamma_half: Which axis of k-space to use for the gamma-compression. Either "x" or "z". Only relevant if gamma is True.
    """
    # format of fft-grid is [0, 1, 2, 3... grid_size//2, -grid_size//2, ..+1,..+2,... -1]
    fx,fy,fz = [(np.arange(grid_size[i]) + grid_size[i]//2) % grid_size[i] - grid_size[i]//2 for i in range(3)]
    if gamma:
        if gamma_half == "x":
            # generate only upper half of x-grid, but on border keep half of y-plane and half of z-line
            fx = fx[fx >= 0]
            filter_func = lambda k: (k[:,0] > 0) | ((k[:,0] == 0) & (k[:,1] > 0)) | ((k[:,0] == 0) & (k[:,1] == 0) & (k[:,2] >= 0))

        elif gamma_half == "z":
            # generate only upper half of z-grid, but on border keep half of y-plane and half of x-line
            fz = fz[fz >= 0]
            filter_func = lambda k: (k[:,2] > 0) | ((k[:,2] == 0) & (k[:,1] > 0)) | ((k[:,2] == 0) & (k[:,1] == 0) & (k[:,0] >= 0))
        else:
            raise ValueError('Unknown gamma-halving scheme provided {}'.format(gamma_half))
    else:
        filter_func = lambda k: np.ones(k.shape[0], dtype=bool)

    fxyz = np.array(np.meshgrid(fz,fy,fx, indexing='ij')).reshape(3,-1).T[:,[2,1,0]]
    kgrid = fxyz[filter_func(fxyz)]
    
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

def to_real_wave(coeffs, grid_size, gvecs, gamma=False, gamma_half="x"):
    """
    Fourier-transform the given plane-wave coefficients into a real-space wavefunction

    Input
    plane_wave: Plane wave coefficients (numpy array)
    gvecs: g-vectors for each coefficient
    gamma: if the wavefunction is gamma-compressed
    gamma_half: which axis of k-space gamma-compression was done along

    Output
    Numpy array with real-space wave functions.
    """

    grid = grid_size * 2 # the grid size is twice the size of the kgrid, maybe to avoid aliasing?
    ## Allocate according to the gamma-compression if applicable
    if gamma:
        if gamma_half == "x":
            phi = np.zeros((grid[0]//2+1, grid[1], grid[2]), dtype=complex)
        elif gamma_half == "z":
            phi = np.zeros((grid[0], grid[1], grid[2]//2+1), dtype=complex)
        else:
            raise ValueError('Unrecognized gamma-half argument. "z" or "x" is supported')
    else:
        phi = np.zeros(grid, dtype=complex)

    # fill the coefficients into the buffer, with normation
    phi[gvecs[:,0], gvecs[:,1], gvecs[:,2]] = coeffs

    # perform the inverse fourier transform
    # gamma compression results in real coefficients, so use real-valued routines (and necessary axis switches)
    if gamma:
        if gamma_half == "x":
            plane_gvecs = gvecs[(gvecs[:,0] == 0)] ## do not perform a full gamma-expansion, only the ones with expansion-axis == 0, fourier transform sets the rest
            tmp = expand_gamma_wav(phi, plane_gvecs)
            grid = grid[[2,1,0]]
            tmp = np.swapaxes(phi, 0, 2)
            tmp = fft.irfftn(tmp, s=grid, norm="ortho") # fourier transform along x (switched z)
            phi = np.swapaxes(tmp, 0, 2)
        elif gamma_half == "z":
            plane_gvecs = gvecs[gvecs[:,2] == 0] ## do not perform a full gamma-expansion, only the ones with expansion-axis == 0, fourier transform sets the rest
            tmp = expand_gamma_wav(phi, plane_gvecs)
            phi = fft.irfftn(tmp, s=grid)
        phi /= np.linalg.norm(phi)
        return phi
    else:
        return fft.ifftn(phi)

def meshgrid(x,y,z):
    """
    Generates a 3D meshgrid of the given x,y,z vectors
    
    Input:
    x, y, z: 1D numpy arrays
    """
    return np.array(np.meshgrid(x,y,z)).T.reshape((-1,3))

#@njit
def expand_gamma_wav(buffer, xyz):
    """
    Reverses the gamma-compression of the buffer, by mirroring in provided g-vectors.
    
    Input:
    buffer: 3D numpy array of complex numbers, containing gamma-compressed wavefunction coefficients in the positive half-space
    xyz: list of g-vectors for the gamma-compressed (negative) half-space. A Nx3 numpy array of integers.
    """
    #print("start")
    #for i in range(xyz.shape[0]):
    #    if xyz[i,0] == 0 and xyz[i,1] == 0:
    #        print(xyz[i,:])
    buffer[-xyz[:,0], -xyz[:,1], -xyz[:,2]] = buffer[xyz[:,0], xyz[:,1], xyz[:,2]].conjugate()
    buffer /= np.sqrt(2)
    buffer[0,0,0] *= np.sqrt(2)
    return buffer
    
def expand_gamma_coeffs(coeffs, std_gvecs, gam_gvecs, buffer=None):
    """
    Expands the gamma-compressed coefficients to the full set of coefficients, using provided g-vectors.
    
    Input:
    coeffs: 3D numpy array of complex numbers, containing gamma-compressed wavefunction coefficients
    std_gvecs: g-vectors for the full set of coefficients
    gam_gvecs: g-vectors for the gamma-compressed coefficients
    (optional) buffer: buffer for intermediate full result. If None, a new buffer is allocated.
    
    Output:
    expanded_coeffs: 3D numpy array of complex numbers, containing the full set of coefficients
    
    """
    
    if buffer is None:
        # allocate a buffer for the total wavefunction coeff buffer
        nx, ny, nz = [np.max(std_gvecs[:,i]) - np.min(std_gvecs[:,i]) for i in range(3)]
        buffer = np.zeros((nx, ny, nz), dtype=np.complex128)
    buffer[gam_gvecs[:,0], gam_gvecs[:,1], gam_gvecs[:,2]] = coeffs

    buffer = expand_gamma_wav(buffer, gam_gvecs)
    return buffer[std_gvecs[:,0], std_gvecs[:,1], std_gvecs[:,2]]

def reduce_std_coeffs(coeffs, grid_size, std_gvecs, gam_gvecs, gamma_half="x"):
    """
    Performs gamma compression of the coefficients, using provided g-vectors.
    This requires for the real-space wavefunction to be real-valued, so a transformation of the wavefunction is performed while retaining the same partial density.
    However, this transformation destroyes the phase information of the wavefunction.
    
    Input:
    coeffs: 3D numpy array of complex numbers, containing the full set of coefficients
    std_gvecs: g-vectors for the full set of coefficients
    gam_gvecs: g-vectors for the gamma-compressed coefficients
    gamma_half: which axis of k-space gamma-compression is done along. Either "x" or "z"
    
    Output:
    result: 3D numpy array of complex numbers, containing the gamma-compressed coefficients
    """
    if not gamma_half == "x" and not gamma_half == "z":
        raise ValueError('Unrecognized gamma-half argument. z or x is supported')
    
    # transform the coefficients to real space
    real_wave = to_real_wave(coeffs, grid_size, std_gvecs, False, gamma_half)

    # transform the wavefunction to real-valued function, while attempting to keep the same sign, assuming the imaginary part is small
    # This transformation preserves the partial density of the wavefunction, but destroys the phase information
    real_wave = np.sqrt(real_wave.real**2 + real_wave.imag**2)*np.sign(real_wave.real)
    
    if gamma_half == "x":
        grid = grid_size[[2,1,0]]
        tmp = np.swapaxes(real_wave, 2, 0)
        tmp = fft.rfftn(tmp, s=grid)
        real_wave = np.swapaxes(tmp, 2, 0)
    elif gamma_half == "z":
        real_wave = fft.rfftn(real_wave, s=grid_size)

    real_wave *= np.sqrt(2)
    real_wave[0,0,0] /= np.sqrt(2)

    coeffs = real_wave[gam_gvecs[:,0], gam_gvecs[:,1], gam_gvecs[:,2]]
    return coeffs
    
class PlaneWaveFunctions(HttkObject):
    """
    PlaneWaveFunction is a proxy for a collection of wavefunctions contained in output files of plane-wave basis DFT codes.

    This object stores the energy, occupation and plane-wave coefficients from a calculation, contained in a wavefunction file (e.g. a VASP WAVECAR).
    The access to the plane-wave coefficients is done in a lazy fashion, only caching the requested orbitals at specified K-points

    In addition, it caches the k-vectors/g-vectors associated with the basis set and parameters necessary to generate these (e.g. VASP energy cutoff)

    NOTE: Currently does not support non-collinear (SOC) output formats

    NOTE: As fourier transforms and similar rely on the numpy/scipy/jax library, read-in FracVectors are in working functions converted to numpy arrays during processing
    """

    @httk_typed_init({'nkpts': int, 'nbands': int, 'nspins': int, 'encut': FracScalar, 'cell': Cell, 'kpts': FracVector, 'precision_tag': int, 'eigs': FracVector, 'occups': FracVector, 'pwcoeffs': FracVector})
    def __init__(self, file_ref=None, recpos_func=None, nkpts=None, nbands=None, nspins=None, nplws=None, encut=None, cell=None, kpts=None, kgrid_size=None, double_precision=None, eigs=None, occups=None, pwcoeffs=None, is_gamma=None, gamma_half=None, kgrid=None):
        self.file_ref = file_ref
        self.recpos_func = recpos_func
        self._nkpts = nkpts
        self._nbands = nbands
        self._nspins = nspins
        self._nplws = nplws
        self._encut = encut
        self.cell = cell
        self.kpts = kpts
        self.double_precision = double_precision
        self.eigs = eigs
        self.occups = occups
        self.pwcoeffs = pwcoeffs
        self.kgrid_size = kgrid_size
        self._is_gamma = is_gamma
        self._gamma_half = gamma_half
        self.kgrid = kgrid
        self.gvecs = {}

        # internal variables
        self.reorder_map = {}

    @classmethod
    def create(cls, file_wrapper = None, rec_pos_func=None, nplws=None, encut=None, cell=None, kpts=None, double_precision=None, eigs=None, occups=None, pwcoeffs=None, is_gamma=None, gamma_half="x"):
        """
        Factory function for the proxy object for wavefunctions file.
        
        Input:
        file_wrapper: File wrapper for the wavefunction file. If None, the wavefunction coefficients must be provided directly
        rec_pos_func: Function taking spin, kpoint and band indices, returning the record position in the binary file. If None, the coefficients must be provided directly
        nplws: Number of plane-waves for each k-point.
        encut: Energy cutoff for the plane-wave basis set
        cell: Cell object containing the basis vectors of the supercell
        kpts: List of k-points for the wavefunction coefficients
        double_precision: If the wavefunction coefficients are stored in double precision (True) or single precision (False)
        eigs: Eigenvalues of the wavefunctions
        occups: Occupation numbers of the wavefunctions
        pwcoeffs: Coefficients of the wavefunctions. Either a nested list of coefficients, or a dictionary with keys (spin, kpt, band) and values as list-like objects of coefficients
        is_gamma: If the wavefunction is gamma-compressed (True) or not (False). If None, the function tries to determine the format from the k-point list and the number of plane-waves
        gamma_half: If the wavefunction is gamma-compressed, which axis of k-space was used for the compression. Either "x" or "z", but defaults to "x". Only relevant if is_gamma is True.
        
        Either file_wrapper and rec_pos_func must be provided, or pwcoeffs must be provided directly. If both are provided, the pwcoeffs are ignored.
        
        """

        if is_gamma is not None and not isinstance(is_gamma, bool):
            raise ValueError('Invalid format of gamma boolean in wavefunction creator. Only boolean values accepted')
    
        locs = locals()
        essential_args = dict([(s, locs[s]) for s in ["encut", "cell", "kpts", "eigs", "occups", "nplws"]])
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
            if nkpts == 1 and (kpts[0] == np.array((0,0,0))).all():
                if not gamma_half == 'x' and not gamma_half == 'z':
                    raise ValueError("Incompatible format or value for gamma_half given")
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
            else:
                is_gamma = False
                kgrid = gen_kgrid(kgrid_size, False)

        if file_wrapper is not None and rec_pos_func is not None and double_precision is not None:
            pwcoeffs = defaultdict(None)
            
        elif pwcoeffs is not None:
            # expect one of two formats:
                # a nested list of all wavefunctions, nested with size according to nspin, nkpts, nbands, in that order
                # or
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
        """
        Getter function for the plane-wave coefficients of the wavefunction.
        The function will check if the coefficients are already cached, and if not, read them from the file.
        
        Input:
        spin: Spin index of the wavefunction (1-indexed)
        kpt: K-point index of the wavefunction (1-indexed)
        band: Band index of the wavefunction (1-indexed)
        cache: If True, the coefficients are cached in the object. If False, the coefficients are not cached and read from the file every time.
        
        Output:
        coeffs: 3D numpy array of complex numbers, containing the plane-wave coefficients of the wavefunction
        """
        assert 1 <= spin <= self._nspins
        assert 1 <= kpt <= self._nkpts
        assert 1 <= band <= self._nbands
        
        ind = (spin, kpt, band)
        if ind in self.reorder_map:
            ind = self.reorder_map[ind]

        if ind in self.pwcoeffs:
            return self.pwcoeffs[ind]
        else:
            plws = self.read_plws(*ind)
            if cache:
                self.pwcoeffs[ind] = plws
            return plws

    def read_plws(self, spin, kpt, band):
        """
        Reads the plane-wave coefficients from the stored file wrapper.
        The function will check if the file reference is valid and if the record position function is valid.
        """
        if self.file_ref is not None and self.recpos_func is not None:
            file_pos = self.recpos_func(spin, kpt, band)
            self.file_ref.seek(file_pos)
            array_size = self._nplws[kpt-1]
            type_id = np.complex128 if self.double_precision else np.complex64
            coeffs = np.fromfile(self.file_ref, dtype=type_id, count=array_size)
            return coeffs
        else:
            raise ValueError('Wavefunction file reference or record position function non-existent. Failed to read file') 

    def get_gvecs(self, kpt_ind=None, kpt=None, gamma=None, gamma_half=None, kgrid=None, cache=True):
        """
        Getter function for the g-vectors of the wavefunction.
        Can either be used to generate a new set of g-vectors, or to retrieve a cached set of g-vectors for the current object.
        
        Input:
        kpt_ind: K-point index of the wavefunction (1-indexed)
        kpt: K-point vector of the wavefunction (3D numpy array), if kpt_ind is not provided
        gamma: Whether to generate gamma-compressed g-vectors (True) or not (False). If None, use the gamma-format of the wavefunction object.
        gamma_half: Which axis of k-space to use for the gamma-compression. Either "x" or "z". Only relevant if gamma is True.
        kgrid: The k-grid to use for the generation of the g-vectors. If None, generate a new k-grid for current object.
        """
        if kpt_ind is not None:
            assert 1 <= kpt_ind <= self._nkpts
            kpt = self.kpts[kpt_ind - 1]
        
        if kpt is None:
            raise ValueError("Generation of g-vectors requires a k-point, None provided")
        
        
        if gamma is None:
            gamma = self._is_gamma
        if gamma_half is None:
            gamma_half = self._gamma_half
        
        if gamma != self._is_gamma or gamma_half != self._gamma_half or kgrid is not None:
            cache = False
        
        ### check if g-vectors are already cached
        if cache:
            immut_kpt = FracVector.create(tuple(kpt))
            if immut_kpt in self.gvecs:
                return self.gvecs[immut_kpt]
       
        if kgrid is None:
            kgrid = gen_kgrid(self.kgrid_size, gamma, gamma_half)
        gvecs = gen_gvecs(kgrid, kpt, self.cell.basis, self._encut)
            
        if cache:
            self.gvecs[immut_kpt] = gvecs 
        return gvecs

    def get_wavr(self, spin, kpt, band):
        """
        Getter function for the real-space form of the wavefunction at given indices.
        
        Input:
        spin: Spin index of the wavefunction (1-indexed)
        kpt: K-point index of the wavefunction (1-indexed)
        band: Band index of the wavefunction (1-indexed)
        
        Output:
        real_space_wave: 3D numpy array of complex numbers, containing the real-space form of the wavefunction
        """
        assert 1 <= spin <= self._nspins
        assert 1 <= kpt <= self._nkpts
        assert 1 <= band <= self._nbands
        
        plane_wave = self.get_plws(spin, kpt, band)
        gvecs = self.get_gvecs(kpt_ind=kpt)
        real_space_wave = to_real_wave(plane_wave, self.kgrid_size, gvecs=gvecs, gamma=self._is_gamma, gamma_half=self._gamma_half)

        return real_space_wave

    def rearrange(self, index_map):
        """
        Exchanges specified orbitals, exchanging band index or spin index according to given map.
        Note that orbitals cannot be exchanged between k-points, as the number of coefficients and g-vectors are k-dependent.

        Input
        index_map: Dictionary with indices of orbitals to rearrange as keys, and target indices as values, on the form (spin_i, k_i, band_i). k_i of key and value has to be the same. The map has to be one-to-one for the given indices in both directions.
        """
        assert np.all([len(key) == 3 and len(val) == 3 for key, val in index_map.items()]), "Incorrect index format, expect 3-tuple of (spin_i, k_i, band_i)"
        assert np.all([key[1] == val[1] for key,val in index_map.items()]), "Trying to interchange orbitals between k-points"
        key_set = set(index_map.keys())
        val_set = set(index_map.values())
        assert key_set == val_set, "Provided mapping not bi-directional one-to-one"

        for key,val in index_map.items():
            self.reorder_map[key] = val

    def eigenval(self, s, k, b):
        ind = (s,k,b)
        if ind in self.reorder_map:
            ind = self.reorder_map[ind]
        return self.eigs[ind[0]-1, ind[1]-1, ind[2]-1]

    def occupation(self, s, k, b):
        ind = (s,k,b)
        if ind in self.reorder_map:
            ind = self.reorder_map[ind]
        return self.occups[ind[0]-1, ind[1]-1, ind[2]-1]
    
    @property
    def nbands(self):
        """
        Returns the number of bands in the wavefunction object.
        """
        return self._nbands
    @property
    def nkpts(self):
        """
        Returns the number of k-points in the wavefunction object.
        """
        return self._nkpts
    @property
    def nspins(self):
        """
        Returns the number of spin-channels in the wavefunction object.
        """
        return self._nspins

    @property
    def is_gamma(self):
        """
        Returns whether the wavefunction is gamma-compressed or not.
        """
        return self._is_gamma
    @property
    def gamma_half(self):
        """
        Returns the axis of k-space used for gamma-compression, if the wavefunction is gamma-compressed.
        """
        if not self.is_gamma:
            return None
        else:
            return self._gamma_half
    
    @property
    def nplanewaves(self):
        """
        Returns the number of plane-waves for each k-point in the wavefunction object.
        """
        return self._nplws
    @property
    def encut(self):
        """
        Returns the energy cutoff for the plane-wave basis set.
        """
        return self._encut
    
    @property
    def kpoints(self):
        """
        Returns the k-points of the wavefunction object as fracvector array.
        """
        return self.kpts

    def copy(self, spins=None, kpts=None, bands=None, file_ref=None, format=None, gamma_half='x'):
        """
        
        """
        if bands is None:
            bands = np.arange(self._nbands) + 1
        else:
            assert len(bands) > 0, 'Empty band list provided'
            bands = np.array(bands)
            assert (1 <= bands & bands <= self._nbands).all(), 'Provided bands out of bounds of %d and %d' % (1, self._nbands)
        
        if kpts is None:
            kpts = np.arange(self._nkpts) + 1
        else:
            assert len(kpts) > 0, 'Empty k-point list provided'
            kpts = np.array(kpts)
            assert (1 <= kpts & kpts <= self._nkpts).all(), 'Provided kpoint indices out of bounds of %d and %d' % (1, self._nkpts)
        if format is not None:
            if format == 'gamma':
                to_gamma = True
                assert len(kpts) == 1 and np.norm(kpts[0]) == 0, 'Cannot convert to gamma format, more than gamma-point specified'
            elif format == 'std':
                to_gamma = False
            else:
                raise ValueError('Invalid wavecar format specified, only "std" and "gamma" are currently supported')
            if to_gamma != self._is_gamma:
                convert = True
        else:
            to_gamma = self._is_gamma
            convert = False
        nspins = len(spins)
        nbands = len(bands)
        nkpts = len(kpts)

        if file_ref is None:
            ### make copy in memory
            new_coeffs = {}
            new_eigs = self.eigs.copy()
            new_occups = np.zeros((nspins, nkpts, nbands), dtype=int)
            for s_i,s in enumerate(spins):
                for k_i,k in enumerate(kpts):
                    if convert:
                        std_gvecs = self.get_gvecs(kpt_ind=k, gamma=False)
                        gam_gvecs = self.get_gvecs(kpt_ind=k, gamma=True, gamma_half=gamma_half)

                    for b_i,b in enumerate(bands):
                        coeffs = self.get_plws(s, k, b, cache=False)
                        if convert:
                            if to_gamma:
                                coeffs = reduce_std_coeffs(coeffs, self.grid_size, std_gvecs, gam_gvecs, gamma_half)
                            else:
                                coeffs = expand_gamma_coeffs(coeffs, self.grid_size, std_gvecs, gam_gvecs, self._gamma_half)
                        new_coeffs[(s_i,k_i,b_i)] = coeffs
                        new_eigs[s_i,k_i,b_i] = self.eigenval(s,k,b)
                        new_occups[s_i,k_i,b_i] = self.occupation(s,k,b)

            # convert to desired format

            # make new object
            new_wavefuncs = PlaneWaveFunctions.create(nkpts=nkpts, nbands=nbands, nspins=nspins, nplws=self._nplws, encut=self._encut, cell=self.cell, kpts=kpts, double_precision=self.double_precision, eigs=new_eigs, occups=new_occups, pw_coeffs=new_coeffs, is_gamma=to_gamma, gamma_half=gamma_half)

        else:
            ### Write a copy to file
            from httk.iface.vasp_if import write_wavecar, read_wavecar
            name_wrapper = IoAdapterFilename.use(file_ref)
            write_wavecar(name_wrapper, self, bands=bands, spins=spins, kpts=kpts, format=format, gamma_half=gamma_half)
            new_wavefuncs = read_wavecar(name_wrapper)
        
        return new_wavefuncs

    
