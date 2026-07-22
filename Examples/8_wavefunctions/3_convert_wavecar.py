import httk
from httk.iface.vasp_if import write_wavecar
from httk.atomistic.wavefunctionutils import compare_wavefuncs
import os
import glob

dir_path = __file__.rsplit('/', 1)[0] + "/"
resource_path = __file__.rsplit('/', 1)[0] + "/../example_resources/wavefunctions/"

wobj_gam = httk.load(resource_path + "WAVECAR.gam") # Gamma-point WAVECAR

wobj_std = httk.load(resource_path + "WAVECAR.std_G") # Standard WAVECAR with Gamma point included
wobj_std2 = httk.load(resource_path + "WAVECAR.std") # WAVECAR which does not contain the Gamma point

# WAVECARs can exist in a gamma-compressed format when only containing the Gamma point
# By symmetry, coefficients phi_k = phi_(-k) at the gamma point, so only half the g-vector sphere has to be saved to file
# The gamma-format WAVECARs are written by the VASP-gamma binary, and are mutually incompatible with the standard VASP binary

# It is possible in httk to convert a gamma-format WAVECAR to a standard WAVECAR, which can then be used in VASP
# It is also possible (but possibly lossy) to convert a standard WAVECAR to a gamma-format WAVECAR when only including the Gamma point

write_wavecar("WAVECAR.std_from_gam", wobj_gam, format="std")  # convert gamma-format WAVECAR to standard WAVECAR
wobj_std_converted = httk.load("WAVECAR.std_from_gam")

# convert standard WAVECAR to gamma-format WAVECAR
# But make sure to only write the Gamma point, otherwise it will fail
write_wavecar("WAVECAR.gam_from_std", wobj_std, format="gamma", ikpts=[1])  
wobj_gam_converted = httk.load("WAVECAR.gam_from_std")

try:
    write_wavecar("WAVECAR.gam_from_std2", wobj_std2, format="gamma")  # but cannot convert if the WAVECAR does not contain the Gamma point
except AssertionError as e:
    print("Failure converting WAVECAR.std to Gamma:", e)
    print("This is expected behavior.")

print("Checking file sizes of the original and converted WAVECARs:")
for fname in glob.glob(resource_path + "/WAVECAR.*"):
    size = os.path.getsize(fname)
    print("%s: %.4f MB" % (fname, size / 1024**2))

for fname in glob.glob(dir_path + "WAVECAR.*"):
    size = os.path.getsize(fname)
    print("%s: %.4f MB" % (fname, size / 1024**2))

print("")

print("Testing the wavefunction conversion precision:")
# Compare the original and converted WAVECAR wavefunctions
pairs = [(wobj_gam, wobj_std_converted), (wobj_std, wobj_gam_converted)]
for w1, w2 in pairs:
    for s in range(wobj_gam.nspins):
        for b in range(wobj_gam.nbands):
            similarity, phase, overlap = compare_wavefuncs(
                w1, w2, s + 1, 1, b + 1, s + 1, 1, b + 1
            )
            assert 1 - similarity < 1e-5, "Wavefunction comparison failed: similarity too low for ({},{}): {}, {}, {}".format(s,b,similarity, phase, overlap)
            print("Wavefunction "+str(s+1)+" "+str(b+1)+" OK!")
print("Converted wavefunctions have (absolute) identity overlaps to tested precision!")



