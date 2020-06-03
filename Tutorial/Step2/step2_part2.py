#!/usr/bin/env python
import sys

if sys.version_info[0] == 3:
    import tkinter
else:
    import Tkinter as tkinter

import httk.atomistic.vis
from httk.atomistic import Structure


def delay(text):
        root = tkinter.Tk()
        root.title("Dialog")
        frame = tkinter.Frame(root)
        frame.pack()
        tkinter.Label(frame, text="  "+text+"  \n").pack(side=tkinter.TOP)
        tkinter.Button(frame, text="  Ok  ", command=frame.quit).pack(side=tkinter.BOTTOM)
        root.mainloop()
        root.destroy()  # optional; see description below

# This tutorial program shows more advanced visualization features
# And how to generate good high-resolution figures for publication

struct = httk.load("POSCAR2")
origbasis = struct.uc_basis
# By printing the orthogonal transformation and see how it builds an orthogonal cell,
# you can then paste that into struct.build_supercell adjust manually adjust the supercell
#print((struct.orthogonal_supercell_transformation(tolerance=20)))
struct = struct.supercell.orthogonal(tolerance=20)

struct.vis.show({'bonds': True, 'extbonds': True, 'polyhedra': False, 'extmetals': False,
                 'defaults': 'publish', 'angle': '{0 0 0} 20.0', 'perspective': False,
                 'bgcolor': '#FFFFFF', 'unitcell': origbasis, 'show_supercell': True}, debug=True)
struct.vis.visualizer.jmol.send("connect radius 0.115\n")
struct.vis.visualizer.jmol.send("moveto /* time, axisAngle */ 1.0 { -879 -324 -351 86.05} /* zoom, translation */\
  308.14 0.0 0.0  /* center, rotationRadius */ {2.0274994 2.027499 6.309999} 33.509285 /* navigation center, translation, depth */\
   {0 0 0} 0 0 0 /* cameraDepth, cameraX, cameraY */  3.0 0.0 0.0;\n")
delay("Press Ok when you are happy with the view.\nThe figure will save, and jmol close automatically.")
struct.vis.visualizer.save_and_quit("highres.png", 3200, 2500)

# Helpful tip: if you open the jmol console and type: "show orientation;" you get a long string,
# looking like the one in the 'moveto' command above. If you copy-pase that into your script you can
# store a specific rotation / orientation that you like.
