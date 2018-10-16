Tutoriel MRS
~~~~~~~~~~~~

Ce chapitre décrit les diverses manières d'exécuter un
serveur HTTP avec le site MRS. Peut être utilisé soit à des
fins de développement d'intégration via iframe, soit pour
contribuer au code source.

La solution la plus simple est d'utiliser docker, que nous utiliserons dans ce
tutoriel.

.. note:: Si vous ne souhaitez pas utiliser docker vous pouvez vous
          referer au ``Dockerfile`` situé à la racine du code source pour
          configurer votre environnement de developpement manuellement, ainsi
          qu'au fichier ``config.yml`` dans le dossier ``.circleci`` pour voir
          les commandes utilisées dans la pipeline de test.

Démarrer MRS: Container éphémère
================================

On peut démarrer le serveur avec seulement une commande::

    docker run -e DEBUG=1 --rm -p 8000:8000 -it betagouv/mrs:master mrs dev 0:8000

On peut ensuite ouvrir l'URL ``http://localhost:8000`` pour accéder au site.

Pour éviter de démarrer le projet en mode développement ce qui causerait de
certains problèmes de sécurité, l'option ``-e`` exécute l'image dans un
container avec la variable d'environnement ``DEBUG`` à ``1`` ce qui équivaut à
``True`` une fois casté en booléen.

L'option ``--rm`` efface le container automatiquement après exit de la
commande, nous verrons d'autres possibilités dans la section suivante.

L'option ``-p`` utilisée ici permet d'exposer le port 8000 du container au
port 8000 de l'hôte.

Les options ``--interactive`` et ``--tty``, abrégées en ``-it`` permettent au
container de démarrer avec le support du standard input ainsi qu'une émulation
de tty. Sans ces options impossible d'utiliser une commande interactive.

L'image utilisée ici est ``betagouv/mrs`` avec le tag ``master`` qui correspond
à la branche ``master`` du code source, qui est soit déjà utilisée en
production, soit en cours de validation chez nous sur l'environnement de
pré production: c'est la branche de base.

La commande par défaut de l'image exécute un serveur uwsgi utilisé en
production. Ici, nous surchargeons la commande par défaut en exécutant la
commande qui démarre un serveur de développement, ``mrs dev``, avec comme
argument ``0:8000`` pour qu'il écoute sur le port 8000 de toute interface du
container.

.. note:: La commande ``mrs`` execute la commande django ``manage.py``.

Démarrer MRS: Container persistent
==================================

Pour hacker sur MRS, nous recommandons de démarrer l'image sur un container
persistent::

    docker run -e DEBUG=1 --name mrs -d -p 8000:8000 -it betagouv/mrs:master mrs dev 0:8000

Par rapport à la commande ci-dessus, non seulement sans l'option ``--rm`` mais
également avec l'option ``--name mrs`` en plus permet de donner un nom au
container afin d'y référer dans d'autres commandes, mais également avec
l'option ``-d`` pour démarrer le container en tache de fond.

On peut le voir tourner avec la commande ``docker ps``::

    $ docker ps
    CONTAINER ID        IMAGE                 COMMAND             CREATED             STATUS              PORTS                              NAMES
    954e922c3fd8        betagouv/mrs:master   "mrs dev 0:8000"    44 minutes ago      Up 15 seconds       6789/tcp, 0.0.0.0:8000->8000/tcp   mrs

On peut ensuite exécuter différentes opérations sur le container mrs, par
exemple:

- ``docker start mrs``
- ``docker stop mrs``
- ``docker restart mrs``
- ``docker rm mrs``
- ``docker inspect mrs``

On peut ainsi rentrer dans le container avec ``docker exec``::

    docker exec -it mrs bash

Ou encore directement créer un nouveau super utilisateur en base de données
avec la commande ``mrs createsuperuser`` ce qui permettra de s'authentifier
pour accéder à l'interface d'administration sur l'url ``/admin``::

    docker exec -it mrs mrs createsuperuser

Ci-dessus, on exécute donc avec standard input et tty, sur le container
``mrs``, la commande ``mrs createsuperuser``.

.. note:: toute modification faite dans le container n'est pas sauvegardée
          dans l'image, donc si vous effacez le container avec ``docker rm`` et
          que vous en re-creez un à partir de l'image avec ``docker run``, il
          faudra re-creer votre utilisateur.

Hacker MRS: monter sa branche de code dans le container
=======================================================

Pour hacker MRS, rien de tel que de démarrer le container avec un bind mount du
dossier::

    git clone https://github.com/betagouv/mrs
    docker run -v $(pwd)/mrs/src:/code/src -e DEBUG=1 --name mrs -d -p 8000:8000 -it betagouv/mrs:master mrs dev 0:8000

Ainsi, toute modification faite dans le code source sera visible dans le
container, et le serveur de développement devrait recharger le python, et toute
modification de fichier JS, JSX ou SCSS causera une re compilation des bundles
par le watcher webpack.

.. danger:: Attention cependant, la base de données SQLite de développement se
            trouve dans le dossier ``mrs/src/db.sqlite3``, vous pouvez aussi
            bien l'effacer et redémarrer le container lorsque vous souhaitez
            repartir à zéro.

Hacker MRS: tout faire en local
===============================

Autrement, il suffit d'une toolchain nodejs et python normale a jour sur son
système, avec un utilisateur qui a les droits de création sur postgres.

JavaScript
----------

Installer le paquetage Node ``yarn`` avec ``sudo npm install -g yarn``, puis
et exécuter a la racine du code source qui contient ``package.json``:

- ``yarn install`` pour installer les dépendances dans le dossier
  ``node_modules``, et compiler les bundles webpack,
- ``yarn test`` pour exécuter les tests,
- ``yarn run lint`` pour exécuter le linter.

Python
------

Vous pouvez installer MRS et les dépendances dans ``~/.local`` avec ``pip
install --user -e /chemin/vers/mrs``, ensuite vous pouvez exécuter la commande::

    PATH=~/.local/bin:$PATH mrs dev

Cela exécutera un serveur de développement sur ``localhost:8000`` ainsi qu'un
watcher webpack, il faut donc que la commande ``yarn install`` décrite
ci-dessus fonctionne.

.. danger:: Aussi, cela effectuera automatiquement les migrations de database.
            En dev, c'est un fichier ``db.sqlite3`` dans le dossier ``src``.
            N'hésitez pas a l'effacer et a relancer la commande pour le recréer
            en cas de problème avec la DB.

Postgres
--------

Les tests ont besoin d'une base de données Postgres (notamment pour les jsonfields).

Pour que votre utilisateur shell ait les droits de création et de
suppression de tables pendant les tests::

    sudo -u postgres -drs $USER
    # -d: l'utilisateur a le droit de créer des BDs
    # -r: il peut créer des rôles
    # -s: superutilisateur
    # $USER doit etre votre username PAM

et tant qu'on y est::

    sudo -u postgres createdb --owner $USER -E utf8 mrs

(et si besoin, voyez ``dropuser``).

Jeu de data de tests
--------------------

Nous maintenons un jeu de data utilises par les tests d'acceptance dans
src/mrs/tests/data.json. Il est cense contenir un minimum de data pour activer
un max de use-case.

Pour charger en DB::

    export DB_ENGINE=django.db.backends.postgresql DB_NAME=mrs DEBUG=1 DJANGO_SETTINGS_MODULE=mrs.settings
    sudo -u postgres dropdb mrs
    sudo -u postgres createdb -E utf8 -O $USER mrs
    mrs migrate
    clilabs +django:delete contenttypes.ContentType
    mrs loaddata src/mrs/tests/data.json

Pour sauvegarder la db dans le fichier de data, on veut grosso modo mettre a
jour les memes modeles, rien de plus facile avec une incantation shell::

    mrs dumpdata --indent=4 $(grep model src/mrs/tests/data.json  | sort -u | sed 's/.*model": "\([^"]*\)",*/\1/') > src/mrs/tests/data.json

Tests
-----

Pour tester le Python, installer le paquetage Python ``tox`` avec ``pip install
--user tox``.

Créer la base de données de test postgres ``mrs_test``, puis lancez
les migrations (``mrs migrate``) en spécifiant bien le nom de la BD et
le type de la BD en variables d'environnements: ``DB_NAME=mrs_test
DB_ENGINE=django.db.backends.postgresql`` (voir le fichier ``tox.ini``).

Enfin, exécuter à la racine du code source qui contient
``tox.ini``:

- ``PATH=~/.local/bin:$PATH tox -e qa`` pour lancer l'analyse statique
- ``PATH=~/.local/bin:$PATH tox -e py36-dj20`` pour exécuter les tests dans un
  environnement python 3.6 avec Django 2.0.

Tox fera le baby sitting des environnements dans le dossier ``.tox``, par
exemple dans le dossier ``.tox/py36-dj20``  l'environnement ``-e py36-dj20``.

En outre, les tests exécutés par notre pipeline sont définis dans
``.circleci/config.yml``.
