from httk.iface.vasp_if import read_wavecar

resource_path = __file__.rsplit('/', 1)[0] + "/../example_resources/wavefunctions/"

# Read the WAVECAR file
wobj_std = read_wavecar(resource_path + "WAVECAR.std")  # read standard format WAVECAR, default settings

wobj_std2 = read_wavecar(resource_path + "WAVECAR.std_G", wavefunc_prec=128)  # read with specified precision. Not recommended as normally documented in the WAVECAR

# read gamma-point WAVECAR, providing axis of gamma-compression. Usually "x" (default) for VASP version 5-6, but can differ among compilations
wobj_gam = read_wavecar(resource_path + "WAVECAR.gam", gamma_mode="x")