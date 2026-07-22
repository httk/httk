import httk
import os
from httk.iface.vasp_if import write_wavecar

resource_path = __file__.rsplit('/', 1)[0] + "/../example_resources/wavefunctions/"

wobj_std = httk.load(resource_path + "WAVECAR.std_G")  # read standard format WAVECAR, our starting point for writing a new WAVECAR

# Create a new PlaneWaveFunctions object with only occupied bands (to the degree possible for variation between k-points)
# find the highest occupied band for each k-point and spin
highest_band = max([max([band  for band in range(wobj_std.nbands) if wobj_std.occupation(spin+1, k+1, band+1) > 0])
                    for k in range(wobj_std.nkpts) for spin in range(wobj_std.nspins)])
bands_to_keep = list(range(1,highest_band + 1))

# Create a new PlaneWaveFunctions object with only the occupied bands and the first k-point, and only the first spin channel (up)
# writes the wavefunction object copy into memory, not to a file
new_wobj = wobj_std.copy(bands=bands_to_keep, ikpts=[1], spins=[1])

# writes the wavefunction object copy into the file system and only caches fetched data
new_wobj_file = wobj_std.copy(bands=bands_to_keep, ikpts=[1], spins=[1], file_ref="WAVECAR.std_copy")

# same effect can be achieved with the explicit write method
write_wavecar("WAVECAR.std_copy2", wobj_std, bands=bands_to_keep, ikpts=[1], spins=[1])
new_wobj_explicitfile = httk.load("WAVECAR.std_copy2")  # load the file to check if it was written correctly



# Print the new object information
## Print bands and occupations at first k-point
for wav in [new_wobj, new_wobj_file, new_wobj_explicitfile]:
    if wav.is_gamma:
        label = "Gamma-point WAVECAR"
    else:
        label = "Standard WAVECAR"

    # Print header information
    print(label + ":")
    print("  Number of spins:", wav.nspins)
    print("  Number of k-points:", wav.nkpts)
    print("  Number of bands:", wav.nbands)
    print("  Number of planewaves:", wav.nplanewaves)
    print("  Energy cutoff:", wav.encut.to_float(), "eV")
    print("  Gamma-format:", wav.is_gamma)
    print("  ")

    # Print energies and occupations for each band at the first k-point
    for k_ind in range(wav.nkpts):
        print("K-point index {}: {} {} {}".format(k_ind + 1, *wav.kpoints[k_ind]))
        k_ind = 0 # first k-point
        print("{:^5s}\t{:^10s}\t{:^8s}".format("Band", "Energy", "Occup."))
        for band in range(wav.nbands):
            row_entry = [band]
            format_str = "{:^5d}\t"
            for spin in range(wav.nspins):
                row_entry.extend([wav.eigenval(spin + 1, k_ind + 1, band + 1), wav.occupation(spin + 1, k_ind + 1, band + 1)])
                format_str += "{:>10.6f}\t{:>8.6f}\t"
            print(format_str.format(*row_entry))
        print("  ")



# cleanup
del new_wobj_file # remove the object from memory
os.remove("WAVECAR.std_copy")  # remove the file created by the copy method
os.remove("WAVECAR.std_copy2")  # remove the file created by the write method