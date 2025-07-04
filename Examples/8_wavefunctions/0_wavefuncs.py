import httk
from httk.atomistic.wavefunction import PlaneWaveFunctions

script_path = __file__.rsplit('/', 1)[0]  # Get the directory of the current script
wav_path = script_path + "/../example_resources/wavefunctions/"

## Read the wavefunction data from a WAVECAR file
wobj_std = httk.load(wav_path + "WAVECAR.std") # read standard format WAVECAR
wobj_std2 = httk.load(wav_path + "WAVECAR.std_G") # read another standard format WAVECAR (identified automatically by httk)

wobj_gam = httk.load(wav_path + "WAVECAR.gam") # read gamma-point WAVECAR (identified automatically by httk)


## Print bands and occupations at first k-point
for wav in [wobj_std, wobj_std2, wobj_gam]:
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


