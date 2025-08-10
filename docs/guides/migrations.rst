Gestion des migrations
======================

Pour créer une migration :

.. code-block:: bash

   make db-revision MSG="Ajout d'une table"

Pour appliquer les migrations :

.. code-block:: bash

   make db-upgrade
