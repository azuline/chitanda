Setup
#####

From PyPI with pipx
-------------------

It is recommended that chitanda be installed with ``pipx``; however, if that is
not possible, ``pip install --user`` will also work.

.. code-block:: bash

   $ pipx install chitanda
   $ chitanda migrate  # Upgrade database to latest version.
   $ chitanda config  # See wiki for configuration instructions.

Run chitanda with the following command:

.. code-block:: bash

   $ chitanda run

From source with poetry
-----------------------

.. code-block:: bash

   $ git clone git@github.com:azuline/chitanda.git
   $ cd chitanda
   $ poetry install
   $ poetry shell
   $ chitanda migrate  # Upgrade database to latest version.
   $ chitanda config  # See wiki for configuration instructions.

Run chitanda with the following commands:

.. code-block:: bash

   $ cd chitanda  # Change to project directory.
   $ poetry run chitanda run

From source with pip
--------------------

.. code-block:: bash

   $ git clone git@github.com:azuline/chitanda.git
   $ cd chitanda
   $ python3 -m virtualenv .venv
   $ source .venv/bin/activate
   $ pip install -e .
   $ chitanda migrate  # Upgrade database to latest version.
   $ chitanda config  # See wiki for configuration instructions.

Run chitanda with the following commands:

.. code-block:: bash

   $ cd chitanda  # Change to project directory.
   $ source .venv/bin/activate
   $ chitanda run
