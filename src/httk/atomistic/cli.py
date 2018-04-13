import httk
from httk import cout, cerr

help_text = """
atomistic module
   visualize  Visualize an atomic structure
""".strip()

atomistic_help_text = """
The atomistic module is intended for working with atomistic simulations.

Commands available:
    visualize  Visualize an atomic structure
""".strip()

visualize_help_text = """
usage: visualize [<file> [<file2> [...]]]

Makes a best effort to interprete the files and visualize them.
""".strip()

def main(commands, args):
    cout("Atomistic module")

    if len(commands) == 0:
        commands = ['help']
    
############## HELP ####################           
    if commands[0] == "help":
        cout(atomistic_help_text)
    elif len(commands)==2 and commands[0] == "visualize" and commands[1] == "help":
        cout(visualize_help_text)

############## VISUALIZE ##############

    elif commands[0] == "visualize":
        import httk.atomistic.vis
        from httk.atomistic import Structure
        for command in commands[1:]:
            struct = httk.load(command)
            struct.vis.show()
        
#######################################
    else:
        cerr("Unknown command in atomistic module:", commands[0])
        exit(1)
       

