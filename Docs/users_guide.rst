================================================================================
*httk* Users' Guide
================================================================================
.. raw:: text
   :file: generated/header.txt


Introduction
------------

The High-Throughput Toolkit (httk) is a toolkit for preparing and
running calculations, analyzing the results, and store them in a
global and/or in a personalized database. The word 'high-throughput'
refers to the practice of executing a vast number of computational
tasks on a supercomputer cluster, in which case proper automatization
of all steps is critically important. Httk is presently targeted at atomistic calculations in materials science and electronic structure, but aims to be extended into a library useful also outside those areas.

.. raw:: html

  <p>This file is the users' guide. It covers different aspects of the
  functionality provided by httk. For help on other topics, see
  the <a class="reference internal" href="index.html"><em>front page</em></a>.
  </p><p>
  For an even quicker introduction, look through the overview presentation
  on that page.
  </p>

.. raw:: text

  This file is the users' guide. It covers different aspects of the
  functionality provided by httk. For help on other topics, see
  the file README.txt

  For an even quicker introduction, see the presentation
  in the file httk_overview.pdf


Importing the httk python library into your program 
-----------------------------------------------------------------

The easiest way to import the python library if you do atomistic
calculations is::

  from httk import *
  from httk.atomistic import *

This imports some very often used identifiers into the namespace of
your program, e.g., Structure for atomic structures. If you want to
avoid wild imports (`from X import *`) you can of course instead do::

  import httk
  import httk.atomistic

(Note the need to separately import the atomistic sub-library; it is
not imported automatically by import.httk)

To avoid dependences on libraries that you may not have installed,
httk implements somewhat unusual 'plugin'-type extensions to its core
classes. For example, you can enable visualization of atomic
structures, which requires jmol to be installed, by the following::

  from httk import *
  from httk.atomistic import *
  import httk.atomistic.vis

This adds new visualization calls to the Structure class which can be
called, e.g., as::

  mystructure.vis.show()

(Note: if you forget to do 'import httk.atomistic.vis', httk informs
you about the need to add this import.)

Example programs
----------------

It may be easiest to learn the use of httk by example. There are three
such resources available. The presentation httk_overview.pdf shows
working code snippets that can be copy+pasted. There are short
examples under Examples. Then there is a step-by-step tutorial under
Tutorial/ that is intended to showcase the httk features in a natural
progressing order.


Interfacing with other software
-------------------------------

Interfacing with python libraries
..................................

A common need is to use functionality provided by other python
libraries outside the standard libraries.  Httk tries to help with
this. It provides 'glue' modules that lets you import exactly the
version you want.

To use the ase python library (Atomic Simulation Environment)
together with httk, you typically want to do::

  import httk.external.ase_glue
  import ase

The first line imports the httk 'glue' module. It includes helper
functionality that makes httk and ase work together.  But, it also
sets up your python environment so that at the next line 'import ase'
actually imports the version of ase that you have configured httk to
use. This can, for example, be a specific version in your home
directory (which can help avoid an older version provided system-wide
on the computational cluster you are using). All you need to do is
edit httk.cfg in the main httk directory and set the path to where you
have placed the ase library (e.g., in your home directory).


Interact with other programs
............................

Similar to the interface to other python libraries, httk helps you
call other (non-python) software packages.

For example, the following code::

  import httk.external.jmol

gives you access to routines for running and interacting with jmol.

Note that subpackages of httk.external raise an exception if you try
to import them and the relevant software is missing.


Interface packages
..................

httk also provides 'light' versions of its interface to other software
under httk.iface.*. These packages DO NOT require the corresponding
software to be installed. This usually includes things such as writing
correctly formatted files, etc.


More details on the httk python library
---------------------------------------

This section covers some design decisions of httk that it may be
useful to take note of.


Creating new httk objects
.........................

The python default constructor (the '__init__' constructor) that is
called when simply doing::

  struct = Structure(arg1, arg2, ...)

should almost *never* be used with httk objects, for several
reasons. Perhaps the most important is that it is going to change
between version of httk (for more explanation, see the developers'
guide).

Instead, almost all httk objects provide a classmethod named
`*.create` for this purpose instead. I.e., ::

  struct = Structure.create(arg1, arg2, ...)


A note about object mutation
............................

Most httk objects assume they stay unaltered after creation (unless
clearly spelled out, e.g., 'MutableFracVector'). Hence, methods
'altering' an object normally return a *new copy* of the object with
the alterations made. This comes with a number of benefits:

 - They can be used as keys in dictionaries

 - Less risk for bugs as one part of code alters an object that
   happens to also be stored and used somewhere else.

 - The API becomes more clear, you do not have to wonder if the object
   itself may be altered by calling a method (it never is.)

It also comes with a drawback

 - Code making, say, a series of alterations of an object may becomes more bulky to write.

It is the intention to provide mutable versions where this drawback is
of significance. Right now, this more or less only applies to the
existence of a MutableFracVector vs the regular FracVector.


Object conversion with the 'use' method
.......................................

Almost all httk classes contains a `*.use()` method for helping with
object type conversion. Lets say that you get a Structure object
'structure' which represents structure data fetched out of the
database, but you want to have a UnitcellStructure instead, simply do
this::

  unitcellstruct = UnitcellStructure.use(structure)
  

I/O in httk
...........

All I/O in the httk library uses our own framework of IOAdapters
classes. This is usually not something you need to worry about; any
routine that takes as a parameter an "IOAdapter" 'ioa' will accept a
filename or any form of python streaming object in its place.  (You
may want to check the IOAdapter chapter of the developers' guide to
see how this is done in practice, as the IOAdapters may be helpful
also in your own routines.)


The httk taskmanager toolset
----------------------------

Apart from the python library, httk also comprises a toolset for
executing computational tasks on computer clusters.  To avoid issues
with incompatible version, this part of httk is mostly written in bash
rather than python.  If things are working as they should, this is not
something you should need to worry about, you can still script your
runs in python, or any other language you prefer.


Setting up a computational 'project'
....................................

You should first setup a 'top' working directory for your project. Use
'cd' to go to this directory and then run::

  httk-project-setup project_name

Configuring 'computers'
.......................

Supercomputer clusters, as well as other computers that you are going
to execute runs on can now be setup by the command httk-computer-setup
this allows you to configure settings for how to transport runs to
this computer and run them there.

After you have configured the computer you also need to run::

  httk-computer-install

to copy necessary httk files to this computer and "prepare it" for
executing runs.


Sending tasks to a computer and running them
............................................

For this to work you need to have created batch tasks on the right
format. For this, please consider closely Step6 of the httk tutorial.

Once you have a directory with runs, execute::

  httk-tasks-send-to-computer <computer name>

and the runs will be copied over. They will not yet be started.

All execution of tasks is done via the taskmanager.sh process, which
now needs to be started on the computer. Run::

  httk-tasks-start-taskmanager <computer name>

and it will start up.

You can monitor the status of your compute runs by::

  httk-tasks-status <computer name>

And as soon as one or more of the runs have finished, you can fetch
them back with::

  httk-tasks-receive-from-computer <computer name>

This concludes what you need for 'simple' use of the task
system. However, for advanced use, you will need to better understand
precisely how the taskmanager.sh process operates. This information is
present in a separate text: RUNMANAGER_DETAILS.txt.


If you want; how to submit your results to a public database
............................................................

httk includes tools that, if you want to, makes it easy to submit a
project directory so that your data can be made available and 
searchable in a public database. The normal case would be the 
Open Materials Database (http://openmaterialsdb.se), run by the 
same people involved with the httk framework.

First, if you have not yet setup a project directory, do so. I.e.,
collect all the files that you wish to be part of the submission and do::

  httk-project-setup project_name

This creates a subdirectory `ht_project` in this directory. You must now use a text editor and edit three files in this directory:
  
  1. Edit `ht_project/config` and set `description=A good description of your poject`.
  
  2. Edit `ht_project/license` and write clearly what license you place the data under. For submissions to the Open Materials Database we normally ask for the data to be placed either under a creative commons attribution license, or the public domain. (This can be negotiated, contact the omdb team at contact [at] openmaterialsdb.se.) See http://openmaterialsdb.se/contributorinfo.html for the latest info.

  3. Optional: edit `ht_project/references` and insert, one per line, any citations to papers, etc., that you want to associate with this project.

Once your project is setup correctly, you simply have to have the project
directory as your current working directory and execute::

  httk-project-submit 

(or httk-project-submit <website> if you want to submit somewhere
else than the *Open* *Materials* *Database*.)

After a series of question and a cryptographic signing of your
project files, your files will be submitted to the database.

Note that submitted results are not directly and automatically 
processed. There is a certain level of manual 
examination by us to make sure the upload makes sense before we
add it to the database.

Furthermore, you can edit the file ht.project/references to add or remove publications even after your result has been submitted. To re-submit updated references, issue the command::

  httk-project-submit-update-references

Finally, should you change your mind about the data being published, you can issue the command::

  httk-project-submit-withdraw

Which will lead to the result eventually being pulled from our data (however, also here some manual work is involved, so the result will not be intimidate.)



