================================================================================
*httk* Developers' Guide
================================================================================
.. raw:: text
   :file: header.tpl

Introduction
-------------

.. raw:: html

  <p>This file is the developers' guide for adding to / changing the
  functionality of the httk toolset and python library. For other
  topics the <a class="reference internal" href="index.html">
  <em>front page</em></a>.
  </p>

.. raw:: text

  This file is the developers' guide for adding to / changing the
  functionality of the httk toolset and python library. For other
  topics, see the file README.txt

You likely want to have read the users' guide before reading this.

Short points for experienced developers
---------------------------------------
* Follow PEP8, except --ignore=E226,E265,E266,E401,E402,E501,W291,W293,W391

* Favor unmutable classes over mutable ones

* For arrays of numbers, use core/FracVector unless you have a reason

* Constructors are generally considered private, use a create(...) static method instead. 

* Type conversion should be handled with use(other) methods

* File I/O should be done with the core/ioadapters classes

* Note the plugin system that comes via inheritance from HttkObject
  
Overview of the python library
------------------------------

* Arrays of numbers: essentially all arrays of numbers within
  httk.core are implemented using our own vector math class,
  FracVector. There are many things that can be argued about the pros
  and cons of re-implementing vector math vs. using numpy vectors. The
  primary reasons for this design choice was:

      - FracVectors are exact (they are based on fractions), meaning
        that no information is ever lost about cell shapes and atomic
        positions, there is no need to handle floating-point
        'fussiness' with cutoffs etc. Cell matrices can be exactly
        inverted, and so on.
        
      - FracVectors are immutable (but there is a MutableFracVector). 
        They can thus be used as e.g., keys in dictionaries, in sets, 
        etc. This lets us avoid certain type of difficult-to-find bugs 
        where one by mistake mutates a vector that is used elsewhere. 
        (For more info, see the section 'Rant about mutable vs. 
        non-mutable classes' at the end of this document.)

      - FracVectors are implemented in pure Python, making the core
        part of httk a pure Python library = very easy to install and
        get up and running

      - FracVectors are easy to convert to floating point arrays when
        high speed is needed (the opposite conversion is not as easy,
        requires cutoffs, and will generally not give the exact same
        results between different computers due to differences in
        floating point processing.)

* Basic structural classes: we implement our own, rather than using a
  'structure' class of another library (e.g., 'Atoms' from ASE).  This
  way we avoid dependencies, but most importantly, our structure
  classes generally avoid floating point numbers (see discussion about
  FracVector above). We provide via the 'httk.iface' module
  conversions to many other structure types in other libraries.


Constructors
------------

The python __init__ constructor is regarded as *private* throughout
httk. These constructors should be very light-weight and not sanitize
or process their arguments. The arguments to the constructor normally
reflect the internal representation of the data and changes when the
internal data representation changes as part of future development.

The public constructor should normally be an @classmethod named
'create'. The parameters to create are meant to stay the same even
when the internal representation of the data in the class changes. We
want 'create' to be as flexible as possible and able to take data on
multiple forms. A very common design pattern is that the create method
is a "swiss army knife" type creator that can take a multitude of
named arguments, and only some set of those arguments are needed to be
given. E.g., both these are valid examples of creating a new Structure
object::

  mystruct = Structure.create(cell=mycell, coords=mycoords, counts=mycounts)
  mystruct = Structure.create(a=my_a, b=my_b, c=my_c, alpha=my_alpha, beta=my_beta, gamma=my_gamma, coords=mycoords, counts=mycounts)

Motivation for using create rather than __init__: if __init__
constructors are used as public, one may get into serious limitations
in how the internal data representation of the class can be changed
later. Also, sometimes it is necessary to create new objects in a way
that bypasses any processing of arguments, and this becomes difficult
and inelegant if __init__ is already an established public
swiss-army-knife type constructor.


The 'use' method
----------------

Throughout httk we have another standardized @classmethod method
called 'use'. It means "make a best effort to convert the object given
into the class on which we call 'use'. E.g., ::

  duck = Duck.use(ducklike) 

tries to convert ducklike into a Duck, if it is not *already* of type
Duck, in which case it is just returned unmodified. The primary
difference between 'use' and 'create' is that use always only take one
argument (an object we think is 'equivalent' with, e.g., a Duck) and
that we generally try to avoid creating a new object if we can.

To better explain the need for this, consider the class 'Structure'
and the database class 'DbStructure'. We do not want the 'db' module
to leak into the core module (e.g., there should never be any type
testing against, e.g., DbStructure or imports from the db submodule
into core.) Yet, a Structure and a DbStructure are essentially "the
same thing", so methods that expect a 'Structure' with full freedom to
use an object as if it is a normal structure is expected to work like
this::

  def do_something(struct):
    struct = Structure.use(struct)
    struct.some_method(...)

This saves the need to have to stop and think "wait, is this a
function that takes a UnitcellStructure or a Structure?" when using
the functions.

One may suggest that it would be better to use object-oriented
inheritance for this functionality. However, inheritance typically
does not work that great with primitive types (e.g., functions that
can take both a string as a file reference, or a Path object, or an
IOStream object). Nor does object oriented programming give an
unambiguous solution for cross-converting *between* *subclasses*. Note
the following example of the 'use' method::

  uc_struct = UnitcellStructure() 
  numpy_stuct = NumpyStructure.use(uc_struct) 
  # now use numpy_struct in a way that requires NumpyStructure specific methods 

(Note that there is not yet any NumpyStructure in httk, but will
probably be in the future.) In practice NumpyStructure and
UnitcellStructure are in different submodules and it makes no sense to
make either one inherit from the other, but they (could) both inherit
from a common superclass (e.g. 'AbstractStructure'). Nevertheless,
even if they do that, there is no obvious way just from object
oriented programming to know how to do the above conversion. One could
of course 'upcast' UnitcellStructure to AbstractStructure, but the
downcast into a NumpyStructure is then not trivial. Also, there could
be great benefits in using a conversion 'shortcut' between these two
classes that saves time over upcast + a generic downcast.


I/O Adapters
------------

For file io we use httk.core.ioadapters. References to files and
output streams can have many types, e.g., strings (i.e., a path),
instances of the object Path, instances of Stream, etc. The ioadapters
help writing functions that can deal with all these types of
references to files comparably easy, without large "if elif elif elif"
forks in every such function. Lets say that you write a function that
generates some output data::

  def write_data(fio):
    fio = IoAdapterFileWriter.use(fio)    
    f = fio.file
    f.write("OUTPUT")
    fio.close()    

This allows the input argument 'fio' to be of many, many, different
types. You never really need to bother with "converting" your argument
before calling write_data. You just *choose* that you want whatever
'fio' was to be turned into an IoAdapterFileWriter, and then you just
pick out the 'file' property and use it as a file. You never need to
specifically worry about whether fio already was an
IoAdapterFileWriter, or just the filename 'output.txt', or a Path
object.


Classes and interfaces
----------------------

A design principle is to keep classes short. As a general rule: only
methods that absolutely need to work with the internal data structures
of a class should go into the class! Other "methods" should simply be
written as regular functions that take one (or more) instances of the
class. Put the class in 'classname.py' and the utility methods in
'classnameutils.py'.

The primary benefit of this is that the duck-typing of python allows
us to re-use those exact functions even with other objects that
fulfill the same API interface as the original class. This cannot be
done if they are implemented as instance methods.

However, it is ok to extend the class with convenience methods that
are very short calls into functions implemented elsewhere, e.g., ::

  @property
  structue.normalized_formula(self):
    return normalized_formula(self)

as this helps finding the right method when calling help(object). The
difference is that the full implementation is not put into the class
iself.


Plugins
-------

To avoid dependences on libraries that you may not have installed,
httk implements somewhat unusual 'plugin'-type extensions to any class
that inherits from HttkObject.

The practical outcome is that loading a module, e.g., the atomistic
visualization module, adds functionality to some objects inside
htt.atomistic. E.g., ::

  from httk import *
  from httk.atomistic import *
  import httk.atomistic.vis

This adds, e.g., Structure.vis.show() to show a structure. 

In practice this is easy to work with in your own code. We'll use a
plugin to the Structure class as example. All you need to do is:

1. create a class that inherits from httk.HttkPlugin, and which
   implements a method:: 

      plugin_init(self, struct) 

   which takes the place of the usual __init__ and gives access to the
   'hosting' structure instance.

2. add this to the corresponding HttkObject by:: 
  
      Structure.myplugin = HttkPluginWrapper(MyStructurePluginClass)

After this has happened during an import, any call on a structure
instance, e.g., ::

   struct.myplugin.hello_world()

will call the corresponding method in MyStructurePluginClass. Your
plugin can also have class methods, which gets called by::

   Structure.myplugin.classmethod()

For a concrete example, look at the structurevisualizerplugin in
httk.atomistic.vis.


General recommendations for contributed code
--------------------------------------------

Rule #1: Generally read and follow: http://www.python.org/dev/peps/pep-0008/
   You are encouraged to use the pep8 tool (either directly or via your code 
   development platform, but, use: --ignore=E401,E402,E501,W291,W293,W391,E265,E266,E226
   (See below for motivations.)

Rule #2: Always organize your code in private sections and a public
   API. Never write code that depends on private sections outside the
   class / module / etc.
	
	It is very very easy for a large Python project to degenerate
	into a huge pile of code that has such intricate
	cross-dependences that it is almost impossible to know the
	implications of a seemingly small change. For example, do you
	dare changing the internal representation of the data in the X
	class?  You have to be sure no other class reaches into the
	internal data structures and make assumptions about how they
	are organized.
	
	The principle of API-oriented organization is simple:

	    - Every piece of code is either in a private section or
              part of the public API.

	    - Changes to private sections are "easy", as they should
              never break other code

	    - Changes to the public API are difficult, and should
              generally be done only by introducing a new version of
              the class / module / etc.
	
	- Every public class should be in its own file named after the
	  class, things not meant to be used outside that class should
	  be named with a prefix underscore '_'.
    
Rule #3: Always make your classes be *immutable* unless you know why
    you need a mutable class. Do not fall for the pressure of the
    premature optimization fairy and the idea that "it will be faster
    if I don't create a new instance". No one cares if you shave 10 ms
    of the final program execution time, but people will care if your
    program has bugs. Only optimize code where speed *matters*. See
    longer rant in section below.

Motivations for/discussions about our digressions from pep8
-----------------------------------------------------------

* E226: missing whitespace around arithmetic operator: This rule as
  implemented in the pep8 tool is not consistent with the pep0008
  standard. Use spaces around arithmetic operators when it adds to
  readability.

* E265: block comment should start with '# ': We do not want to
  enforce what can go inside comment sections as they are used rather
  freely throughout the code right now. This may change in the future.

* E266: too many leading '#' for block comment: see E265

* E401: multiple imports on one line: In this code we put standard
  system libraries as a single import line to avoid the file preambles
  to become overly long. All other imports should be each on one line.

* E402: module level import not at top of file: We should generally
  strive to put all module imports at the top of the file. However, we
  need to depart from this for conditional imports, especially for our
  handling of external libraries, and, sometimes for speed
  optimization (only do slow import X if a function is run that
  absolutely needs it.)

* E501: line too long: Modern editors allow editing wide source with
  ease. *Try* to keep lines down under 100 characters, but this rule
  should be violated if significantly increased readability is
  obtained by a few even longer lines.

* W291: trailing whitespace: Between all different editors used, this
  simply generates too many warnings that makes more important pep8
  violations more difficult to see.  Once in a while we should simply
  run the files through a tool that removes trailing whitespace.

* W293: blank line contains whitespace: I genuinely disagree with this
  rule. It is not motivated by the pep0008 standard, but something
  unmotivated put in by developers of the pep8 tool.  Blank lines
  should be indented to the indentation level of the block that they
  appear in.

* W391: blank line at end of file: see W291.


A rant about mutable vs. non-mutable classes
--------------------------------------------

While immutable objects incur some overhead due to extra object
creation, they generally make programming much easier. For mutable
objects you have to learn the internals of the implementation to
understand which operations possibly may affect another object.
	
Consider the following pseudocode for a mutable vector class,::

       A = MutableVector(((1,2,3,4),(5,6,7,8)))
       B = A[0] 
       B[1] = 7 # does this also change A at the element [0,1]?!

You *cannot* *know* *the* *answer*! The answer depends on the
internals of MutableVector! However, for an UnMutableVector the answer
is trivial ('A' never changes!). Since no one has time to read
documentation, the usual programmer will learn when and where a
MutableVector affects other vectors by trial-and-error.  This leads to
bugs!

E.g., let us consider numpy (where vectors are mutable for a good
reason: the aim of numpy is to do floating point math at very high
speed). Below are some examples of possible assignments operations
that can be placed on line 2 in the code above, and a comment that
specifies whether the subsequent change of B also changes A. Notice
how the behavior is not easy to predict without reading the numpy
documentation!::

    B = A[0]            
    # Yes, B becomes a reference into A, so changing B also changes A!

    B = (A.T)[0].T      
    # Yes, B is still a reference into A, but with a different shape. 
    # Changing B also changes A!

    B = A.flatten() 
    # No, flatten() is documented as "returns a copy of the array", 
    # and indeed, changing B does not change A!

    B = A.reshape(8)[0] 
    # Yes. Despite that this seem to be equivalent to flatten(), 
    # B becomes a reference into A instead of a copy! Hence, if someone were 
    # to "clean up the code" by thinking 'flatten is much easier to read' 
    # and replacing it, they will unintentionally change the behavior of the code!


Contributing, License and Redistribution
----------------------------------------

If you extend the httk framework for yourself, please consider sending
your changes back to us. If your changes are generally useful, they
will be included in our distribution, which will make your life *much
simpler* when you want to upgrade versions.

Presently patches, bug reports, etc., are handled via email, i.e.,
just email your patches / modified source files to us. (In the future
we'll make arrange for a better way, e.g., github.)

The High-Throughput Toolkit uses the GNU Affero General Public License
(see the file LICENSE.txt for details), which is an open source license
that allows redistribution and re-use if the license requirements are
met. (Note that this license contains clauses that are not in the
usual GNU Public License, and source code from httk cannot be imported
into GPL-only licensed projects.)

If you plan on redistributing / forking httk with major changes, PLEASE edit
httk/__init__.py and change the 'version' variable to contain a
personal suffix.  E.g., set version='1.0.rickard.2'. Then run the
command 'make dist'. This creates a httk_v{VERSION}.tgz archive that
you can redistribute.


Contact
-------

Our primary point of contact is email to: httk [at] openmaterialsdb.se
(where [at] is replaced by @)

