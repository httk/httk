#!/usr/bin/env python
import os
import sys

# This assumes you have put this script in your httk/bin directory,
# You can override it below
PATH_TO_HTTK_BIN_DIR=os.path.dirname(os.path.realpath(__file__))

# No need to configure this if you have httk correctly installed
# Example:
#PATH_TO_HTTK_BIN_DIR="/home/test/Local/httk/bin"

if sys.version_info[0] == 2:
    from Tkinter import *
    import Tkinter as tki
else:
    from tkinter import *
    import tkinter as tki
from subprocess import call

class TextDialog(object):
    def __init__(self, text):
        self.root = top = self.top = Tk()
        Label(top, text=text).pack()
        self.e = Entry(top)
        self.e.pack(padx=5)
        b = Button(top, text="OK", command=self.ok)
        b.pack(pady=5)

    def ok(self):
        self.value = self.e.get()
        self.top.destroy()


class TextboxDialog(object):

    def __init__(self):
        root = self.root = Tk()

        DIR=os.getcwd()
        name=os.path.basename(DIR)

        Label(root, text="Path to project").pack()
        self.pe = Entry(root,width=40)
        self.pe.insert(END,DIR)
        self.pe.pack(padx=5)

        Label(root, text="Project name").pack()
        self.e = Entry(root,width=40)
        self.e.insert(END,name)
        self.e.pack(padx=5)

        Label(root, text="Project description").pack()

    # create a Frame for the Text and Scrollbar
        txt_frm = tki.Frame(root, width=600, height=300)
        txt_frm.pack(fill="both", expand=True)
        # ensure a consistent GUI size
        txt_frm.grid_propagate(False)
        # implement stretchability
        txt_frm.grid_rowconfigure(0, weight=1)
        txt_frm.grid_columnconfigure(0, weight=1)

    # create a Text widget
        self.txt = tki.Text(txt_frm, borderwidth=3, relief="sunken")
        self.txt.config(font=("consolas", 12), undo=True, wrap='word')
        self.txt.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    # create a Scrollbar and associate it with txt
        scrollb = tki.Scrollbar(txt_frm, command=self.txt.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.txt['yscrollcommand'] = scrollb.set

        Label(root, text="References (one per line)").pack()

    # create a Frame for the Text and Scrollbar
        reftxt_frm = tki.Frame(root, width=600, height=300)
        reftxt_frm.pack(fill="both", expand=True)
        # ensure a consistent GUI size
        reftxt_frm.grid_propagate(False)
        # implement stretchability
        reftxt_frm.grid_rowconfigure(0, weight=1)
        reftxt_frm.grid_columnconfigure(0, weight=1)

    # create a Text widget
        self.reftxt = tki.Text(reftxt_frm, borderwidth=3, relief="sunken")
        self.reftxt.config(font=("consolas", 12), undo=True, wrap='word')
        self.reftxt.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    # create a Scrollbar and associate it with reftxt
        scrollb = tki.Scrollbar(reftxt_frm, command=self.reftxt.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.reftxt['yscrollcommand'] = scrollb.set

        b = Button(root, text="OK", command=self.ok)
        b.pack(pady=5)


    def ok(self):
        self.path = self.pe.get()
        self.name = self.e.get()
        self.description = self.txt.get("1.0",END)
        self.references = self.reftxt.get("1.0",END)
        self.root.destroy()

#root = Tk()

d = TextboxDialog()
d.root.wait_window(d.root)
project_path=d.path
project_name=d.name
project_description=d.description.replace("\n","\n  ")
references=d.references

if os.path.exists(os.path.join(project_path,"ht.project")):
    print("This is already a httk project.")
    print("Either remove ht.project in the directory and re-run this script,")
    print("or simply go to the directory and run httk-submit")
    exit(0)

#d = TextboxDialog("Description of project")
#d.root.wait_window(d.root)
#project_description=d.value

try:
    returncode = call(["httk-project-setup", project_name])
    if returncode != 0:
        print("Error returned. Stopping")
        exit(0)
except OSError:
    returncode = call([os.path.join(PATH_TO_HTTK_BIN_DIR,"httk-project-setup"), project_name])
    if returncode != 0:
        print("Error returned. Stopping")
        exit(0)

with open("ht.project/config", "w") as w:
    w.write("""\
[main]
project_name=%s
excludes=[POTCAR],[POTCAR\.*],[.*~]
description=%s
    """%(project_name, project_description))

with open("ht.project/references", "w") as w:
    w.write(references)

try:
    returncode = call(["httk-project-submit"])
    if returncode != 0:
        print("Error returned. Stopping")
        exit(0)
except OSError:
    returncode = call([os.path.join(PATH_TO_HTTK_BIN_DIR,"httk-project-submit")])
    if returncode != 0:
        print("Error returned. Stopping")
        exit(0)
