.. httk documentation master file, created by
   sphinx-quickstart on Tue Mar  3 23:23:25 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:tocdepth: 2
   
.. comment image:: _static/httk.png
   :width: 300 px
   :alt: httk
   :align: center

The High-Throughput Toolkit (*httk*)
====================================

This website documents the High-Throughput Toolkit (*httk*). Looking for the Open Materials Database? It is at: http://openmaterialsdb.se

About the High-Throughput Toolkit
---------------------------------

The High-Throughput Toolkit (*httk*) is a toolkit for:

- Preparing and running calculations.
- Analyzing the results.
- Store the results and outcome in a global and/or in a personalized database.

*httk* is an independent implementation of the database-centric high-throughput methodology
pioneered by Ceder et al., and others. [see, e.g., Comp. Mat. Sci. 50, 2295 (2011)].
*httk* is presently targeted at atomistic calculations in materials science and electronic
structure, but aims to be extended into a library useful also outside those areas.

.. raw:: html
   :file: generated/httk_overview.html

.. include:: ../../README.rst
   :start-after: structure, but aims to be extended into a library useful also outside those areas.
   :end-before: More info and help

More info and help
------------------

For more details on installation options refer to :doc:`install`.
  
User's guide: see :doc:`users_guide`.

Workflows: for more details on how high-throughput computational workflows are
executed via the runmanager.sh program, see :doc:`runmanager_details`.
This may be useful if you plan to design your own workflows using *httk*.

Developing / contributing to *httk*: see :doc:`developers_guide`

.. raw:: html

   For API documentation, see:  <a class="reference internal" href="httk_base.html">outline of the httk API.</a>

Contributors
------------

For a more complete list of contributors and contributions, see :doc:`contributors`.

Acknowledgements
----------------

*httk* has kindly been funded in part by:
   * The Swedish Research Council (VR) Grant No. 621-2011-4249

   * The Linnaeus Environment at Linköping on Nanoscale Functional
     Materials (LiLi-NFM) funded by the Swedish Research Council (VR).

License and redistribution
--------------------------

The High-Throughput Toolkit uses the GNU Affero General Public
License, which is an open source license that allows redistribution
and re-use if the license requirements are met. (Note that this
license contains clauses that are not in the GNU Public License, and
source code from httk thus cannot be imported into GPL licensed
projects.)

The full license text is present in :doc:`copying`.

Contact
-------

Our primary point of contact is email to: httk [at] openmaterialsdb.se
(where [at] is replaced by @)

	      
Full API reference
------------------
* :doc:`httk_base`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :maxdepth: 1
   :hidden:

   copying
   developers_guide
   httk_base
   install
   mod_httk
   mod_httk_atomistic
   publications
   runmanager_details
   users_guide
   contributors   

