import os, sys
import shutil
import subprocess
import json
import zipfile
import atexit
import signal

try:
    from pymatgen import MPRester
except:
    from pymatgen.ext.matproj import MPRester
import httk.task
import httk.external.pymatgen_glue
from httk.external.pymatgen_glue import pmg_struct_to_structure

# NOTE: Runs and template directories are deleted at exit, or otherwise
# unittests and py.test try to run the Python scripts that are inside.
# Comment out the atexit/signal lines below to keep the folders.

def handle_exit():
    shutil.rmtree('template', ignore_errors=True)
    shutil.rmtree('Runs', ignore_errors=True)

atexit.register(handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

shutil.rmtree('Runs', ignore_errors=True)
zip = zipfile.ZipFile('template.zip')
zip.extractall()

relax_flag = 'True'
symmetry = 'hexagonal'

try:
    api_key = os.environ['MATPROJ_API_KEY']
except KeyError:
    api_key = None
    print("Materials Project API key is needed.\n" +
          "Edit this script or create an environment variable\n" +
          "`export MATPROJ_API_KEY=XXX`.")

if api_key is not None:
    with MPRester(api_key) as m:
        data = m.query(criteria={"task_id": "mp-46"},
                properties=["structure"]
                )

    for entry in data:
        struct_pmg = entry.get("structure")
        struct = pmg_struct_to_structure(struct_pmg)
        # Find primitive cell using FINDSYM or spglib:
        # struct = struct.find_symmetry()

        struct.add_tag('atomic_relaxations', relax_flag)
        struct.add_tag('symmetry', symmetry)

        try:
            dir = httk.task.create_batch_task("Runs/", "template",
                    {"structure": struct},
                    name=struct.hexhash, overwrite_head_dir=True)
            print("Generated run for: {} in {}".format(struct.formula, dir))

            # Put in symmetry and projection flags
            cmd = "sed -i 's/SYMMETRY_PLACEHOLDER/{}/' {}/settings.elastic".format(symmetry, dir)
            p = subprocess.Popen(cmd, shell=True,
                    stdout=subprocess.PIPE).stdout.read().decode()
            cmd = "sed -i 's/PROJECTION_PLACEHOLDER/False/' {}/settings.elastic".format(dir)
            p = subprocess.Popen(cmd, shell=True,
                    stdout=subprocess.PIPE).stdout.read().decode()
            # Edit VASP INCAR settings depending on the relax_flag:
            if relax_flag == 'True':
                cmd = "sed -i 's/ISIF=6/ISIF=3/' {}/INCAR.prerelax".format(dir)
                p = subprocess.Popen(cmd, shell=True,
                        stdout=subprocess.PIPE).stdout.read().decode()
                cmd = "sed -i 's/ISIF=6/ISIF=3/' {}/INCAR.relax".format(dir)
                p = subprocess.Popen(cmd, shell=True,
                        stdout=subprocess.PIPE).stdout.read().decode()
                cmd = "sed -i 's/ISIF=6/ISIF=2/' {}/INCAR.elastic".format(dir)
                p = subprocess.Popen(cmd, shell=True,
                        stdout=subprocess.PIPE).stdout.read().decode()
                cmd = "sed -i 's/NSW=0/NSW=40/' {}/INCAR.elastic".format(dir)
                p = subprocess.Popen(cmd, shell=True,
                        stdout=subprocess.PIPE).stdout.read().decode()

        except Exception as e:
            raise
            print(e)
            pass

