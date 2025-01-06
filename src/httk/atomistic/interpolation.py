from httk.core.httkobject import HttkObject
from os.path import join, isdir
from os import makedirs

class Interpolation(HttkObject):
    def __init__(self,
                 space_number=None,
                 collision_detection_level=None,
                 structs_with_collision=None,
                 interpolated_structs=None,
                 dist_per_atom=None,
                 total_dist=None):
        self._space_number = space_number
        self._collision_detection_level = collision_detection_level
        self._structs_with_collision = structs_with_collision
        self._interpolated_structs = interpolated_structs
        self._dist_per_atom = dist_per_atom
        self._total_dist = total_dist

    def __str__(self):
        return_str = ""
        return_str += "Space group number: "+str(self._space_number)+"\n"
        return_str += "Collision detection level:"+str(self._collision_detection_level)+"\n"
        return_str += "Total distance moved:"+"{:.3f}".format(self._total_dist)+"\n"
        return_str += "Number of species:"+"{:.3f}".format(self._interpolated_structs[0]._num_of_atoms)+"\n"
        return_str += "Distance moved per atom:"+"{:.3f}".format(self._dist_per_atom)+"\n"
        return return_str

    def write_to_folder(self, folder_name, prefix=""):
        if not isdir(folder_name):
            makedirs(folder_name)
        i = 0
        while i < len(self._interpolated_structs):
            self._interpolated_structs[i].write_to_poscar(output_name=join(folder_name, prefix+str(i)+".poscar"))
            i += 1
        with open(join(folder_name, "info.txt"), "w") as f:
            f.write(str(self)+"Structs with collision: "+", ".join([str(x) for x in self._structs_with_collision])+"\n")