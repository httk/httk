import os, sys
import subprocess
import json
try:
    from pymatgen import MPRester
except:
    from pymatgen.ext.matproj import MPRester
import httk.task
import httk.external.pymatgen_glue
from httk.external.pymatgen_glue import pmg_struct_to_structure

properties=[
    "material_id", "unit_cell_formula", "final_energy",
    "icsd_id", "structure", "volume", "elasticity",
    "spacegroup", "formula", "pretty_formula",
    "formula_anonymous", "composition"
]

api_key = os.environ['MATPROJ_API_KEY']
with MPRester(api_key) as m:
    data = m.query(criteria={"task_id": "mp-46"},
            properties=properties
            )

relax_flag = 'True'
symmetry = 'hexagonal'

info_dict = {}
for entry in data:
    struct_pmg = entry.get("structure")
    struct = pmg_struct_to_structure(struct_pmg)
    # Find primitive cell using spglib:
    struct = struct.find_symmetry()

    struct.add_tag('atomic_relaxations', relax_flag)
    struct.add_tag('symmetry', symmetry)

    print(struct)

    info_dict['atomic_relaxations'] = relax_flag
    info_dict['symmetry'] = symmetry
    info_dict['struct_hash'] = struct.hexhash

    try:
        dir = httk.task.create_batch_task("Runs/", "template",
                {"structure": struct},
                name=struct.hexhash, overwrite_head_dir=True)
        print(f"Generated run for: {struct.formula} in {dir}")

        # Put in symmetry and projection flags
        cmd = f"sed -i 's/SYMMETRY_PLACEHOLDER/{symmetry}/' {dir}/settings.elastic"
        p = subprocess.Popen(cmd, shell=True,
                stdout=subprocess.PIPE).stdout.read().decode()
        cmd = f"sed -i 's/PROJECTION_PLACEHOLDER/False/' {dir}/settings.elastic"
        p = subprocess.Popen(cmd, shell=True,
                stdout=subprocess.PIPE).stdout.read().decode()
        # Edit VASP INCAR settings depending on the relax_flag:
        if relax_flag == 'True':
            cmd = f"sed -i 's/ISIF=6/ISIF=3/' {dir}/INCAR.prerelax"
            p = subprocess.Popen(cmd, shell=True,
                    stdout=subprocess.PIPE).stdout.read().decode()
            cmd = f"sed -i 's/ISIF=6/ISIF=3/' {dir}/INCAR.relax"
            p = subprocess.Popen(cmd, shell=True,
                    stdout=subprocess.PIPE).stdout.read().decode()
            cmd = f"sed -i 's/ISIF=6/ISIF=2/' {dir}/INCAR.elastic"
            p = subprocess.Popen(cmd, shell=True,
                    stdout=subprocess.PIPE).stdout.read().decode()
            cmd = f"sed -i 's/NSW=0/NSW=40/' {dir}/INCAR.elastic"
            p = subprocess.Popen(cmd, shell=True,
                    stdout=subprocess.PIPE).stdout.read().decode()

        # Store some extra information about the job
        with open(f"{dir}/job_info.json", "w") as f:
            json.dump(info_dict, f, indent=4)

    except Exception as e:
        raise
        print(e)
        pass

