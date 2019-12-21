Tutoriel MRS
~~~~~~~~~~~~

Ce chapitre décrit les diverses manières d'exécuter un serveur HTTP avec le
site MRS. Peut être utilisé soit à des fins de développement d'intégration via
iframe, soit pour contribuer au code source.

Deux manières de faire:

- avec docker-compose qui facilite le déploiement: on obtient un site qui
  tourne plus rapidement, mais on est plus contraint dès qu'il s'agit de faire
  des choses assez poussées telles qu'executer les tests unitaires ou certains
  helpers tels que `./do py.testrewrite`.
- en local, à l'ancienne, necessite un peu plus de setup manuelle, probablement
  un peu plus difficile si on a pas l'habitude, mais permet une exploitation
  complête des fonctionnalitées prévues pour les developpeurs.

Démarrer MRS en local avec docker-compose
=========================================

On peut démarrer le serveur avec seulement une commande::

    docker-compose up

Ensuite, pour aller dans l'interface d'administration sur `localhost:8000`, se
connecter avec l'utilisateur `test` et le mot de passe `test1234`.

Hacker MRS tout faire en local
===============================

Il suffit d'une toolchain nodejs et python normale a jour sur son système, avec
un utilisateur qui a les droits de création sur postgres, par exemple::

    sudo apt install postgresql
    sudo systemctl start postgresql
    sudo -u postgres createuser -drs $USER
    sudo -u postgres createdb -O $USER -E UTF8 mrs

JavaScript
----------

Installer le paquetage Node ``yarn`` par exemple avec ``sudo npm install -g
yarn``, puis et exécuter a la racine du code source qui contient
``package.json``:

- ``yarn install`` pour installer les dépendances dans le dossier
  ``node_modules``, et compiler les bundles webpack,
- ``yarn test`` pour exécuter les tests,

Python
------

Vous pouvez installer MRS et les dépendances dans ``~/.local`` avec ``pip
install --user -e /chemin/vers/mrs``, ensuite vous pouvez exécuter la commande::

    PATH=~/.local/bin:$PATH DB_ENGINE=django.db.backends.postgresql DB_NAME=mrs mrs dev

Cela exécutera un serveur de développement sur ``localhost:8000`` ainsi qu'un
watcher webpack, il faut donc que la commande ``yarn install`` décrite
ci-dessus fonctionne.

Jeu de data de tests
--------------------

Nous maintenons un jeu de data utilises par les tests d'acceptance dans
``src/mrs/tests/data.json``. Il est censé contenir un minimum de data pour
activer un max de use-case.

On dispose de plusieurs fonctions dans le script ``./do`` à la racine du repo:

- ``./do db.reset`` éfface et re-créée la base de donnée
- ``./do db.reload`` idem mais charge les données de test
- ``./do db.load`` charge juste les données de test
- ``./do db.dump`` écrit le fichier de données de tests à partir de la base de
  données

Cela impactera certains tests, voir section suivante.

Tests
-----

Le script ``./do`` contient également des commandes de test:

- ``./do py.test`` execute les tests pythons
- ``./do py.testrewrite`` re-écrit les fichiers de tests auto-générés
- ``./do py.qa`` execute le linter de code
