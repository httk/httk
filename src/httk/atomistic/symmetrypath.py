from httk.core.httkobject import HttkObject

class SymmetryPath(HttkObject):
    def __init__(self,
                 common_subgroup_number=None,
                 start_space_groups=None,
                 start_orig=None,
                 start_sym=None,
                 start_common_struct=None,
                 start_intermediate_structs=None,
                 end_space_groups=None,
                 end_orig=None,
                 end_sym=None,
                 end_common_struct=None,
                 end_intermediate_structs=None,
                 interpolations=[]):
        self._common_subgroup_number=common_subgroup_number
        self._start_space_groups=start_space_groups
        self._start_orig=start_orig
        self._start_sym=start_sym
        self._start_common_struct=start_common_struct
        self._start_intermediate_structs=start_intermediate_structs
        self._end_space_groups=end_space_groups
        self._end_orig=end_orig
        self._end_sym=end_sym
        self._end_common_struct=end_common_struct
        self._end_intermediate_structs=end_intermediate_structs
        self._interpolations=interpolations

    def __str__(self):
        return_str = ""
        return_str += "Space group number: "+str(self._common_subgroup_number)+"\n\n"
        return_str += "Start structure (symmetrized):\n"
        return_str += str(self._start_sym)+"\n"
        return_str += "End structure (symmetrized):\n"
        return_str += str(self._end_sym)+"\n"
        return_str += "Interpolations:\n\n"
        for x in self._interpolations:
            return_str += str(x)
        return return_str
    
    def write_to_folder(self, folder_prefix):
        pass