=============
Sage Explorer
=============

.. image:: https://mybinder.org/badge.svg
   :target: https://mybinder.org/v2/gh/sagemath/sage-explorer/master

A `Jupyter Notebook <http://jupyter.org>`_ widget for exploring `SageMath <http://www.sagemath.org>`_ objects.


Installation
------------

Try it on binder
^^^^^^^^^^^^^^^^

`demo <https://mybinder.org/v2/gh/sagemath/sage-explorer/master?filepath=demo_sage_explorer.ipynb>`_


Local install from source
^^^^^^^^^^^^^^^^^^^^^^^^^

Download the source from the git repository::

    $ git clone https://github.com/sagemath/sage-explorer.git

Change to the root directory and run::

    $ sage -pip install --upgrade --no-index -v .

For convenience this package contains a [makefile](makefile) with this
and other often used commands. Should you wish too, you can use the
shorthand::

    $ make install

Install from PyPI
^^^^^^^^^^^^^^^^^^

Sage Explorer is distributed on PyPI.

    $ sage -pip install sage_explorer


Usage
-----

See the `demo notebook <demo_sage_explorer.ipynb>`_.

How to contribute
-----------------

The most practical process for contributions is to

# open a ticket to describe what you intend to do
# write your patch
# make a pull request

Please PR to the branch `develop` as the branch `master` holds only stable code.


Acknowledgments
---------------

.. |EULogo| image:: http://opendreamkit.org/public/logos/Flag_of_Europe.svg
    :width: 25
    :alt: EU logo

* |EULogo| This package was created under funding of the Horizon 2020 European Research Infrastructure project
  `OpenDreamKit <https://opendreamkit.org/>`_ (grant agreement `#676541 <https://opendreamkit.org>`_).

* `Nathan Carter <http://nathancarter.github.io/>`_ offered inspiring insights for the new 0.5.0 design.
