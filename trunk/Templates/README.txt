================================================================================

The High-Throughput Toolkit (httk), v$HTTKVERSION (API NOT STABLE YET)
Copyright (c) 2012-2013, Rickard Armiento

For License information see the file COPYING.

API and database design: Rickard Armiento, Peter Steneteg, Igor Mosyagin
Programming: Rickard Armiento

Contact: httk [at] openmaterialsdb.se
================================================================================
(Note: when/if updating this file, edit README.txt in Templates/)

------------
INSTALLATION
------------

For installation information see INSTALL.txt

--------------------------------
IMPORTING httk INTO YOUR PROGRAM
--------------------------------

If you are writing programs that work a lot with httk structures, etc., the
recommended way of importing this library is by using both these lines
  import httk
  from httk.core import *
This imports some very often used key identifiers into the namespace, e.g.,
Structure and Prototype, etc. All the httk subpackages are available as
subpackages off httk. E.g., you access the DBStructure class as
httk.db.DBStructure)

(This goes against the typical recommendation against 'import *', but we aim to
keep the number of identifiers exported by httk.core very small)

Httk also provides 'glue'-routines to some external python libraries and
exectuable programs, etc.  These are all submodules under httk.external and
needs to be explicitly imported. E.g., from httk.external.ase import ase imports
ase into your project (which specifically makes sure you get the same version of
ase as httk is using, which can be very helpful)

Importing from httk.external may raise exceptions if the dependences do not
exist or the corresponding path is not configured in httk.cfg.

---------------------
NAMING IN SUBPACKAGES
---------------------

The httk package is divided into subpackages. We deliberately keep function and
class names short. They may not be unique even within the httk package tree, and
may not make much sense without their corresponding package name. Hence, for
clarity in your code, it is strongly recommended that you import subpackages,
and *not* the contents of subpackages. I.e.,
  RECOMMENDED: from httk import tasks
and not this:
  NOT RECOMMENDED: from httk.tasks import *

----------------
EXAMPLE PROGRAMS
----------------
See subdirectory Examples/ for a set of numbered examples that shows some basic
usage of httk

  Examples/Makefile:
Is there just to make it possible to run 'make clean' to remove any output files
from the examples, no compilation needed for anything.
  
  Examples/structure_1.py:  
Just shows how to create a structure object

  Examples/db_import_2.py:  
Shows how to create a sqlite database with a few structures

  Examples/db_search_3.py:  
Shows how to search for a few structures in the database and print out
information about them

  Examples/db_vasp_4.py:    
Shows how to make the same search as in db_search_3, and generate vasp POSCAR
output

  Examples/db_vasp_ht_5.py: 
Shows how to generate a runs/ directory with run data useful for high-throughput
vasp runs.

  Examples/db_read_cif_6.py:
Shows how to read a cif file.  
  
------------------------------------------
OVERVIEW OF THE DESIGN OF THE CORE LIBRARY
------------------------------------------

* Arrays of numbers: essentially all arrays of numbers within httk.core are
  implemented using our own vector math class, FracVector. There are many things
  that can be argued about the pros and cons of re-implementing vector math
  vs. using numpy vectors. The primary reasons for this design choice was:

      - FracVectors are exact (they are based on fractions), meaning that no
        information is ever lost about cell shapes and atomic positions, there
        is no need to handle floating-point `fussiness' with cutoffs etc. Cell
        matrices can be exactly inverted, and so on.
        
      - FracVectors are immutable (but there is a MutableFracVector). They can
        thus be used as e.g., keys in dictionaries, in sets, etc.  This lets us
        avoid certain type of difficult-to-find bugs where one by mistake
        mutates a vector that is used elsewhere. (For more info, see the
        section 'RANT ABOUT MUTABLE VS. NON-MUTABLE CLASSES' at the end of this
        document.)

      - FracVectors are implemented in pure Python, making the core part of httk
        a pure Python library = very easy to install and get up and running

      - FracVectors are easy to convert to floating point arrays when high speed
        is needed (the opposite conversion is not as easy, requires cutoffs, and
        will generally not give the exact same results between different
        computers due to differences in floating point processing.)

* Basic structural classes: we implement our own, rather than using a
  'structure' class of another library (e.g., 'Atoms' from ASE).  This way we
  avoid dependencies, but most importantly, our structure classes generally
  avoid floating point numbers (see discussion about FracVector above), We
  provide in the 'iface' module conversions to many other structure types in
  other libraries.

  In httk the Structure information is built up via the classes: Prototype,
  Structure and a python list that is an 'assignment map' A *Prototype* is the
  geometry information about a system, i.e., where atoms are, which atoms are
  identical.  A *Structure* combines a Prototype, with an assignment map and a
  cell volume. The assignment map tells 'which atom is what' in the Prototype.

-------------
CONSTRUCTORS
-------------

The python __init__ constructor is regarded as *private* throughout httk. These
constructors should be very light-weight and not sanitize or process their
arguments. The arguments to the constructor normally reflect the internal
representation of the data and changes when the internal data representation
changes as part of future development.

The public constructor should normally be an @classmethod named 'create'. The parameters
to create are meant to stay the same even when the internal representation of the
data in the class changes. We want 'create' to be as flexible as possible and
able to take data on multiple forms. A very common design pattern is that the
create method is a "swiss army knife" type creator that can take a multitude of
named arguments, and only some set of those arguments are needed to be
given. E.g., both these are valid examples of creating a new Structure object

  mystruct = Structure.create(cell=mycell, coords=mycoords, counts=mycounts)
  mystruct = Structure.create(a=my_a, b=my_b, c=my_c, alpha=my_alpha, beta=my_beta, 
    gamma=my_gamma, coords=mycoords, counts=mycounts)

Motivation for using create rather than __init__: if __init__ constructors are
used as public, one may get into serious limitations in how the internal data
representation of the class can be changed later. Also, sometimes it is
necessary to create new objects in a way that bypasses any processing of
arguments, and this becomes difficult and inelegant if __init__ is already an
established public swiss-army-knife type constructor.

----------------
THE 'USE' METHOD
----------------

Throughout httk we have another standardized @classmethod method called
'use'. It means "make a best effort to convert the object given into the class
on which we call 'use'. E.g., 
  duck = Duck.use(ducklike) 
tries to convert ducklike into a Duck, if it is not *already* of type Duck, in
which case it is just returned unmodified. The primary difference between 'use'
and 'create' is that use always only take one argument (an object we think is
'equivalent' with, e.g., a Duck) and that we generally try to avoid creating a
new object if we can.

To better explain the need for this, consider the class 'Structure' and the
database class 'DbStructure'. We do not want the 'db' module to leak into the
core module (e.g., there should never be any type testing against, e.g.,
DbStructure or imports from the db submodule into core.) Yet, a Structure and a
DbStructure are essentially "the same thing", so methods that expect a
'Structure' with full freedom to use an object as if it is a normal structure is
expected to work like this:

  def do_something(struct):
    struct = Structure.use(struct)
    struct.some_method(...)

This saves the need to have to stop and think "wait, is this a function that
takes a DbStructure or a Structure?" when using the functions.

One may suggest that it would be better to use object-oriented inheritance for
this functionality. However, inheritance typically does not work that great with
primitive types (e.g., functions that can take both a string as a file
reference, or a Path object, or an IOStream object). Nor does object oriented
programming give an unambiguous solution for cross-converting *between*
*sub*classes. Note the following example use of the 'use' method:

  db_struct = DbStructure() 
  numpy_stuct = NumpyStructure.use(db_struct) 
  # now use numpy_struct in a way that requires NumpyStructure specific methods 

In practice NumpyStructure and DbStructure are in different submodules and it
makes no sense to make either one inherit from the other, but they (could) both
inherit from Structure. Nevertheless, even if they do that, there is no obvious
way just from object oriented programming to know how to do the above
conversion. One can always 'upcast' DbStructure to a Structure, but the downcast
to a NumpyStructure is not trivial. Note specifically that in this case there is
a shortcut that saves time over upcast + downcast, since it is possible to
access a floating-point representation of the crystal structure directly out of
the database.

----------
IOADAPTERS
----------

For file io we use httk.core.ioadapters. References to files and output streams
can have many types, e.g., strings (i.e., a path), instances of the object Path,
instances of Stream, etc. The ioadapters help writing functions that can deal
with all these types of references to files comparably easy, without large "if
elif elif elif" forks in every such function. Lets say that you write a function
that generates some output data:

  def write_data(fio):
    fio = IoAdapterFileWriter.use(fio)    
    f = fio.file
    f.write("OUTPUT")
    fio.close()    

This allows the input argument 'fio' to be of many, many, different types. You
never really need to bother with "converting" your argument before calling
write_data. You just *choose* that you want whatever 'fio' was to be turned into
an IoAdapterFileWriter, and then you just pick out the 'file' property and use
it as a file. You never need to specifically worry about whether fio already was
an IoAdapterFileWriter, or just the filename 'output.txt', or a Path object.

----------------------
CLASSES and INTERFACES
----------------------

A design principle is to keep classes short. As a general rule: only methods
that absolutely need to work with the internal data structures of a class should
go into the class! Other "methods" should simply be written as regular functions
that take one (or more) instances of the class. Put the class in 'classname.py'
and the utility methods in 'classnameutils.py'.

The primary benefit of this is that the duck-typing of python allows us to
re-use those exact functions even with other objects that fulfill the same API
interface as the original class. This cannot be done if they are implemented as
instance methods.

However, it is ok to extend the class with convinience methods that are very
short calls into the utils class, e.g.,

  @property
  structue.normalized_formula(self):
    return normalized_formula(self)

as this helps finding the right method when calling help(object). The difference
is that the full implementation is not put into the class.

--------------------------------------------
GENERAL RECOMMENDATIONS FOR CONTRIBUTED CODE
--------------------------------------------

Rule #1: Read and follow: http://www.python.org/dev/peps/pep-0008/

Rule #2: Always organize your code in private sections and a public API. Never
   write code that depends on private sections outside the class / module / etc.
	
	It is very very easy for a large Python project to degenerate into a
	huge pile of code that has such intricate cross-dependences that it is
	almost impossible to know the implications of a seemingly small
	change. For example, do you dare changing the internal representation of
	the data in the X class?  You have to be sure no other class reaches
	into the internal data structures and make assumptions about how they
	are organized.
	
	The principle of API-oriented organization is simple:

	    - Every piece of code is either in a private section or part of the
              public API.

	    - Changes to private sections are "easy", as they should never break
              other code

	    - Changes to the public API are difficult, and should generally be
              done only by introducing a new version of the class / module /
              etc.
	
	- Every public class should be in its own file named after the class,
	  things not meant to be used outside that class should be named with a
	  prefix underscore '_'.
    
Rule #3: Always make your classes be *immutable* unless you know why you need a
    mutable class. Do not fall for the pressure of the premature optimization
    fairy and the idea that "it will be faster if I don't create a new
    instance". No one cares if you shave 10 ms of the final program execution
    time, but people will care if your program has bugs. Only optimize code
    where the speed *matters*. See longer rant in section below.

--------------------------------------------
A RANT ABOUT MUTABLE VS. NON MUTABLE CLASSES
--------------------------------------------

While immutable objects incur some overhead due to extra object creation, they
generally make programming much easier.  For mutable objects you have to learn
the internals of the implementation to understand which operations possibly may
affect another object.
	
Consider the following pseudocode for a mutable vector class,

       A = MutableVector(((1,2,3,4),(5,6,7,8)))
       B = A[0] 
       B[1] = 7 # does this also change A at the element [0,1]?!

You *cannot* *know* *the* *answer*! The answer depends on the internals of
MutableVector! However, for an UnMutableVector the answer is trivial (A never
changes!). Since no one has time to read documentation, one usually learn when
and where a MutableVector affects other vectors by trial-and-error. This leads
to bugs!

E.g., let us consider numpy (where vectors are mutable for a good reason: the
aim of numpy is to do floating point math at very high speed).  Below are some
examples of possible assignments operations that can be placed on line 2 in the
code above, and a comment that specifies whether the subsequent change of B also
changes A. Notice how the behavior is not easy to predict without reading the
numpy documentation!:

    B = A[0]            
# Yes, B becomes a reference into A, so changing B also changes A!

    B = (A.T)[0].T      
# Yes, B is still a reference into A, but with a different shape. Changing B
  also changes A!

    B = A.flatten() 
# No, flatten() is documented as "returns a copy of the array", and indeed,
changing B does not change A!

    B = A.reshape(8)[0] 
# Yes. Despite that this seem to be equivalent to flatten(), B beomces a
reference into A instead of a copy! Hence, if someone were to "clean up the code"
by replacing this with 'flatten', they change the behavior of the code!

--------------------------------------
SOURCE CODE LICENSE AND REDISTRIBUTION
--------------------------------------

The High-Throughput Toolkit uses the GNU Affero General Public License (see the
file COPYING for details), which is an open source license that allows
redistribution and re-use if the license requirements are met. (Note that this
license contains clauses that are not in the GNU Public License, and source code
from httk cannot be imported into GPL licensed projects.)

If you are redistributing httk with major changes, please edit httk/__init__.py
and change the 'version' variable to contain a personal suffix.  E.g., set
version='0.4.rickard.2'. Then run the command 'make dist'. This creates a
httk_v{VERSION}.tgz archive that can be redistributed.

-------
CONTACT
-------

Our primary point of contact is email to: httk [at] openmaterialsdb.se (where
[at] is replaced by @)

