=====================================================================
*httk* Installation Instructions
=====================================================================
.. raw:: text
   :file: header.tpl

Installation
------------

There are a few alternative ways to download and install *httk*. Httk
presently consists of a python library and a few programs. If you just
want access to use the python library, and do not need the external
programs, the install is very easy.

Note: for *httk* version 2.0 we will go over to a single program
('python endpoint') ``httk``, for which the pip install step should be
sufficient to get a full install.

(There are also separate instructions below for advanced users that
want to do a direct manual install without the Python pip installed.)


Alternative 1: Install via pip to just access the python library
*****************************************************************

1. You need Python 2.7 and access to pip in your terminal
   window. (You can get Python and pip, e.g., by installing the Python 2.7 version
   of Anaconda, https://www.anaconda.com/download, which should give you
   all you need on Linux, macOS and Windows.)

2. Issue in your terminal window::

     pip install httk

   If you at a later point want to upgrade your installation, just
   issue::

     pip install httk --upgrade

You should now be able to simply do ``import httk`` in your python programs to use the *httk* python library.

Alternative 2: Install via pip for python library + binaries + ability to develop *httk*
****************************************************************************************

1. In addition to Python 2.7 and pip, you also need git.
   You can get git from here: https://git-scm.com/

2. Issue in your terminal window::

     git clone https://github.com/rartino/httk
     cd httk
     pip install --editable . --user

   If you at a later point want to upgrade your installation, just go
   back to the *httk* directory and issue::

     git pull
     pip install . --upgrade --user

3. To setup the paths to the *httk* programs you also need to run::

     source /path/to/httk/init.shell

   where ``/path/to/httk`` should be the path to where you downloaded
   *httk* in the steps above. To make this permanent, please add this
   line to your shell initialization script, e.g., ~/.bashrc

You are now ready to use *httk*.

  Notes:

  * The above instructions give you access to the latest stable release of httk.
    To get the latest developer relase (which may or may not work), issue::

	 git checkout devel
	 pip install . --upgrade --user

    in your httk directory. To switch back to the stable release, do::

	 git checkout master
	 pip install . --upgrade --user

  * An alternative to installing with ``pip install`` is to just run httk out of the
    httk directory. In that case, skip the pip install step above and just append
    ``source ~/path/to/httk/init.shell`` to your shell init files,
    with ``~/path/to/httk`` replaced by the path of your httk directory.)*


Alternative 3: For experienced users: direct manual install
***********************************************************

If you are somewhat familiar with the command line in Linux, Unix,
MacOSX or cygwin, and don't want to mess with python, all you need to
do is download the archive (see:
http://httk.openmaterialsdb.se/downloads.html ) uncompress it in a
directory of your choosing, and configure your environment in your
environment init file (.bashrc or .cshrc) either by inserting ``source
/path/to/.../httk/init.shell`` or by inserting instructions that adds
the ``httk/bin`` directory to your ``PATH`` environment variable, and
the ``httk`` directory to your ``PYTHONPATH`` environment variable.

That is all that is needed. As your first test, you can try to run
``Examples/0_import_httk/0_import_httk.py``. (Please be aware that the
first time you run this command it can be rather slow, since python is
creating ``*.pyc`` files for all httk modules.)


Alternative 4: Step-by-step instructions for installation from archive
**********************************************************************

Find the latest relase download at this link: https://github.com/rartino/httk/releases/latest, and get the link to the
``httk-<version>.tgz`` archive.

Run the following in a terminal::

  mkdir -p ~/bin/python
  cd ~/bin/python
  curl -L <download link> --output httk-<version>.tgz
  tar -zxf httk-<version>.tgz
  rm -f httk-<version>.tgz

where you have to fill in <download link> and <version> according to the release page.

The archive extaction (tar -zxf) will have created a subdirectory
named after the actual version of httk that you downloaded. Check this
with the command ``ls``. Lets say you see ``httk-1.1.2``, then do the
following::

  ln -f -s httk-1.1.2 httk-latest
  source ~/bin/python/httk-latest/init.shell

If you add the very last line to your ``.bashrc`` and/or ``.cshrc``, httk will work in all new terminals you open. (Or alternatively, just add
``~/bin/python/httk-latest/bin/`` to your ``PATH`` environment variable, and
``~/bin/python/httk-latest`` to your PYTHONPATH environment varibale.) If you cannot figure out how to do this on your system, you will have to re-run ``source ~/bin/python/httk-latest/setup.shell`` every time you want to use httk.

You can now start using httk. There is no further compiling, etc. required.

As your first test, you can try to run::

  ~/bin/python/httk-latest/Examples/0_import_httk/0_import_httk.py

This program simply loads the httk library and prints out its version, if everything works. Please be aware that the first time you run this command it can be rather slow, since python is creating ``*.pyc`` files for all httk modules.


Upgrade manual installation
...........................

This assumes you have followed the step-by-step installation instructions above. To upgrade, first check what version you presently have with::

  ls ~/bin/python/

(look for the highest numbered httk-* directory)

Then find the latest relase download at this link: https://github.com/rartino/httk/releases/latest, and get the link to the
``.tar.gz`` archive.

Then do this::

  cd ~/bin/python
  rm -f httk-latest.tgz
  curl -L <download link> --output httk-<version>.tar.gz
  tar -zxf httk-<version>.tgz
  rm -f httk-<version>.tar.gz

If the new version is, e.g., v1.1.3)::

  cp httk-latest/httk.cfg httk-1.1.3/httk.cfg
  ln -f -s httk-1.1.3 ../httk-latest

This concludes the upgrade.

Download Source code
--------------------

The source code of *httk* is available at github: https://github.com/rartino/httk

An archive of the source code of the latest version can be downloaded here: https://github.com/rartino/httk/releases/latest


Windows
-------

These instructions may be expanded in the future. For now,
what you need to do is download cygwin and when aksed what software
to install, include

  wget, python

After cygwin is installed, start a cygwin terminal and follow the
instructions above.

Optional configuration
----------------------

Edit the ``httk.cfg`` file in the httk directory to configure paths to
other software that you want to use from httk. For programs (e.g.,
``isotropy``) you want the path to point at the executable. For python
libraries, you want the path setting to point at the directory you
would include in ``PYTHONPATH``, i.e., a directory that typically contains
a subdirectory with the name of the package.

Note: if you don't have certain software, don't worry, just leave the
line blank. If you have some libraries installed in the system
(e.g. 'import ase' works), then you can also leave the lines blank. If
you want to make sure *not* to use system libraries, set
allow_system_libs=no (this is useful if you are forced to work on a
machine with too old versions installed in the system)

.. raw:: html

  <p>Now, please check out the various resources mentioned in :doc:`index` and look at the Tutorial/ and/or Examples/ programs.</p>

.. raw:: text

  Now you should read relevant parts of README.txt and look at the Tutorial/ and/or Examples/ programs.
