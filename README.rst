mrs: Mes Remboursements Simplifiés
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ceci est le projet de simplification de remboursements.

Contribuer
==========

Installer
---------

Cloner le dépot, et puis dans le dossier du repo executer::

    # Installer/mettre à jour code et librairies JS
    npm install

    # Installer/mettre à jour code et librairies Python
    pip install -U --user -e .

    # Ajouter le pip user bin dans path, example:
    echo 'export PATH=$HOME/.local/bin:$PATH' > ~/.bashrc

    # Mettre à jour la db / créer un user / démarrer le serveur de dev
    mrs dev

Mettre à jour
-------------

Après une mise à jour de votre copie du code::

    # Par example avec
    git fetch; git stash && git reset --hard origin/master && git stash apply

    # Mettre à jour les librairies JS
    npm install

    # Mettre à jour les librairies Python
    pip install -U --user -e .

    # Eventuellement éffacer la base de données
    rm -rf src/db.sqlite

    # Migrations DB, JS, et serveur de test
    mrs dev

Tester
------

Executer les tests contre Django 2.0 avec la commande suivante::

    tox -e py36-dj20

Executer l'analyse du code::

    tox -e qa

Ressources
==========

- https://codecov.io/gh/sgmap/mrs Code coverage
- https://circleci.com/gh/sgmap/mrs CI
