import os

from httk.core import IoAdapterFilename

def load_wavefunc(ioa, ext=None, filename=None):
    """
    Load wavefunction data from a file into a wavefunction object
    """
    ioa = IoAdapterFilename.use(ioa)
    if ext is None:
        try:
            if filename is None:
                filename = ioa.filename
        except Exception:
            raise Exception("httk.httkio.load: original filename not known. Cannot open a generic file.")

        splitfilename = os.path.splitext(os.path.basename(filename))
        ext = splitfilename[1].lower()

        if (ext == '.bz2' or ext == '.gz'):
            splitfilename = os.path.splitext(splitfilename[0])
            ext = splitfilename[1]

        if ext == '':
            ext = splitfilename[0]

        if "wavecar" in splitfilename[0].lower():
            ext = '.vasp'

    if ext == '.vasp':
        import httk.iface.vasp_if
        return httk.iface.vasp_if.read_wavecar(ioa)
    else:
        raise Exception("httk.httkio.load: I do not know what to do with the file:" + filename)


def save_wavefunc(planewave_obj, ioa, ext=None, **kwargs):
    """
    Saves wavefunction data a wavefunction object into a file, with options for format conversion
    """
    ioa = IoAdapterFilename.use(ioa)
    if ext is None:
        try:
            filename = ioa.filename
        except Exception:
            raise Exception("httk.atomistic.atomisticio.wavefunction_io.save: original filename not known. Cannot open a generic file.")

        splitfilename = os.path.splitext(os.path.basename(filename))
        ext = splitfilename[1]

        if (ext == '.bz2' or ext == '.gz'):
            splitfilename = os.path.splitext(splitfilename[0])
            ext = splitfilename[1]

        if ext == '':
            ext = splitfilename[0]

        if "WAVECAR" in filename.upper():
            ext = ".vasp"
    
    if ext == '.vasp':
        import httk.iface.vasp_if
        httk.iface.vasp_if.write_wavecar(ioa, planewave_obj, **kwargs)
    else:
        raise Exception("httk.atomistic.atomisticio.wavefunction_io.save: I do not know what to do with the file:" + filename)
