mrs: Mes Remboursements Simplifiés
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ceci est le projet de simplification de remboursements.

Contribuer
==========

Cloner le dépot, et puis dans le dossier du repo executer::

    # Installer/mettre à jour code et librairies JS
    npm install

    # Installer/mettre à jour code et librairies Python
    pip install -U --user -e .

    # Ajouter le pip user bin dans path, example:
    echo 'export PATH=$HOME/.local/bin:$PATH' > ~/.bashrc

    # Mettre à jour la db / créer un user / démarrer le serveur de dev
    DEBUG=1 mrs dev

Tester
======

Executer les tests contre Django 2.0 avec la commande suivante::

    tox -e py36-dj20

Executer l'analyse du code::

    tox -e qa

Ressources
==========

- https://codecov.io/gh/sgmap/mrs Code coverage
- https://circleci.com/gh/sgmap/mrs CI
