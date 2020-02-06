Opérations
~~~~~~~~~~

Ce chapitre vise les DevOps en vue de maintenir un deploiement de MRS
automatisé, comme c'est le cas pour la production, staging, ecole, ainsi que
pour les deploiements de dev ephemeres faits a partir des branches.

Ce chapitre a donc vocation d'expliquer tous les types de déploiements
possibles ainsi que les opérations courantes, plutot dans la pratique tel un
"cookbook" qu'un document expliquant les concepts et les pourquois, sujet
traité globallement dans un article sur l'`eXtreme DevOps et le hacking
d'operations avec ansible/bigsudo/docker/compose
<https://blog.yourlabs.org/posts/2020-02-08-bigsudo-extreme-devops-hacking-operations/>`_
ainsi que la `distribution de roles Ansible yourlabs
<https://galaxy.ansible.com/yourlabs/>`.

Architecture systeme
====================

Utilisateurs
------------

Il est consideré que vous avez un accès avec le meme nom d'utilisateur, sudo
sans mot de passe et une authentification SSH par clef, vous pouvez vous en
assurrer avec la commande suivante que j'utilise::

    bigsudo yourlabs.ssh @host

Vous pouvez m'ajouter en root sur un serveur en recuperant ma clef ssh sur
github.com/jpic.keys et m'ajouter en root si vous avez besoin d'aide ou alors
ajoutez moi avec la commande suivante::

    bigsudo yourlabs.ssh adduser usergroups=sudo username=jpic

Partitions
----------

``/home``
    Les données persistentes des utilisateurs comme des instances MRS deployées
    sur le serveur.

``/home/nomdinstance``
    Données persistentes d'une instance de MRS, exemple:
    ``/home/mrs-production:`` pour la prod sur le serveur de prod

``/var/lib/docker``
    Docker est vraiment lent si il ne peut pas exploiter le CoW, mounter une
    partition btrfs sur ce dossier le rend effectivement plus rapide.

``/mnt/backup``
    Sur le serveur de prod, un espace sur un autre RAID pour stocker les
    backups.

Services
--------

Les docker-composes contiennent les annotations necessaires pour que Traefik
saches generer les certificats HTTPS et router les domaines vers le container
Django/uWSGI.

Exemple de commande qui installe traefik (ainsi que docker et un firewall)::

    bigsudo yourlabs.traefik @host

Vous avez accès aux instances de NetData et de Prometheus pour acceder au
monitoring en passant par netdata.fqdn ou prometheus.fqdn (remplacez fqdn par
le nom de domaine complet du serveur). Exemple de commande pour installer
netdata et prometheus::

    bigsudo yourlabs.netdata @host

Notez que NetData est configuré pour alerter l'equipe via un webhook Slack
(ChatOps) dans ``/etc/ansible/facts.d/yourlabs_netdata.fact``.

Architecture MRS
================

Compose
-------

Docker-compose prefixe les containers et volume d'une installation a partir
d'un prefixe. Pour docker-compose, les containers et volumes d'une stack
partagent prefixe soit passé a compose avec ``--project-name``, soit c'est le
nom du dossier qui contient le fichier compose (comportement par defaut).

La difference entre un deploiement persistent et un deploiement de dev reside
principalement la:

- pour un env persistent (prod, staging ...), on passe un
  ``home=/home/mrs-production`` et on fusionne ``docker-compose.yml`` avec
  ``docker-compose.persist.yml``,
- pour un env ephèmere (branche dev), on passe ``project=test-$BRANCHNAME``, et
  ``yourlabs.compose`` garde automatiquement une version dans
  ``~/.yourlabs.compose/test-$BRANCHNAME/docker-compose.yml`` en vue de gerer
  l'instance plus tard.

En plus, le deploiement ephemere se fait avec l'argument ``lifetime=604800`` ce
qui cree un fichier ``~/.yourlabs.compose/test-$BRANCHNAME/removeat`` contenant
la somme de l'argument et du timestamp. ``yourlabs.compose`` installe egalement
un timer systemd pour effacer les vieux deploiements ephemeres.

Dans tous les cas, si le serveur a un load-balancer fonctionnel (deployable
avec ``bigsudo yourlabs.traefik`` ou manuellement), alors on veut aussi
fusionner ``docker-compose.traefik.yml``.

Enfin, utile pour les envs de dev et staging, on peut aussi fusionner
``docker-compose.maildev.yml`` pour avoir un serveur de mail de test.

Docker
------

Le Dockerfile de MRS construit une image de container avec webpack pour
compiler le front et uWSGI pour servir le code Python.

Persistence
-----------

Les données sont persistées dans un dossier dans ``/home`` tels que
``/home/mrs-production`` ou ``/home/mrs-staging``. On y trouve:

- ``./backup.sh``: le script pour faire une backup,
- ``./restore.sh``: le script pour restaurer une backup,
- ``./prune.sh``: le script pour appliquer la politique de retention de backup,
- ``./log``: logs django, inclus dans les backups,
- ``./postgres``: les données de postgres
- ``./spooler``: dossier de background jobs uWSGI,
- ``./restic``: dossier qui contient le repo de backups, sur le serveur de
  production c'est dans ``/mnt/backup/mrs-production/restic`` pour eviter de
  stimuler une copie de la DB sur les disques de runtime.

Cron
----

systemd.timer est utilisé en guise de cron, MRS en deploie pour chaque instance
persistente (voir section suivante "Compose"):

- nomdinstance-backup: execute une backup de nuit
- nomdinstance-prune: execute la politique de retention de backups

Operations courantes
====================

Il faut un acces sudo sans mot de passe sur l'un des serveurs pour pouvoir
effectuer l'une de ces operations.

Ajouter un utilisateur sudo
---------------------------

Pour ajouter un utilisateur en sudo sans mot de passe, avec son nom
d'utilisateur github, et la clef ssh publique correspondante a cet utilisateur
sur github::

    bigsudo yourlabs.ssh adduser usergroups=sudo username=github_username @mrs.beta.gouv.fr @staging.mrs.beta.gouv.fr

Pour choisir un nom d'utilisateur ou clef qui n'est pas sur github::

    bigsudo yourlabs.ssh adduser usergroups=sudo username=your_username key=https://gitlab.com/your_gitlab_username.keys @mrs.beta.gouv.fr @staging.mrs.beta.gouv.fr

Après vous pouvez bien entendu le faire manuellement a l'ancienne, mais perso
je trouve cette maniere plus rapide car elle encapsule des operations autrement
repetitives.

Envoyer un mail de test
-----------------------

Typiquement pour tester la configuration du serveur de mail::

    docker-compose exec django mrs sendtestemail

Copier les données de prod en staging
-------------------------------------

Cette opération se passe en deux temps:

- la copie des données d'une base de données à l'autre à travers ssh
- l'execution du script d'anonymisation des données, car staging n'a pas
  vocation d'etre particulierement protegée

::

    ssh -A staging.mrs.beta.gouv.fr

Developpement
=============

Local
-----

Pour executer la meme operation de deploiement et d'installation de prod en
local, en vue de la bidouiller, sans le load-balancer.

Du coup, on va pas mal tordre l'execution qui est faite en CI dans cet
objectif::

    export LFTP_DSN=ftp://localhost
    export RESTIC_PASSWORD=lol
    export RESTIC_REPOSITORY=/tmp/backup/mrs-production-restic
    export POSTGRES_BACKUP=/tmp/backup/mrs-production-postgres
    export SECRET_KEY=notsecret
    export BASICAUTH_DISABLE=1
    export HOST=localhost:8000
    export ALLOWED_HOSTS=127.0.0.1,localhost
    bigsudo ansible/deploy.yml home=/tmp/testmrs compose_django_ports='["8000:8000"]' compose_django_build= compose_django_image=betagouv/mrs:master compose=docker-compose.yml,docker-compose.persist.yml

``LFTP_DSN``
    Le DSN de connection a passer a LFTP pour qu'il upload les backups chiffrées

``RESTIC_PASSWORD``
    Le mot de passe de chiffrement de backups

``RESTIC_REPOSITORY``
    Le chemin vers le repo de backups

``POSTGRES_BACKUP``
    Le chemin dans lequel postgres doit dumper ses data

``SECRET_KEY``
    La clef secrete avec laquelle les mots de passes sont chiffrés

``ALLOWED_HOSTS``
    La liste des hostnames que le serveur est censé accepter. Toute requete
    recue par le serveur dont le host name ne correspond pas prendra direct une
    403.

``HOST``
    Le host que le healthcheck doit verifier.

``BASICAUTH_DISABLE``
    Desactiver le HTTP Basic Auth sur ce deploiement, a noter que le Basic Auth
    se base sur les utilisateurs en base de données.

``bigsudo``
    Le generateur de ligne de commandes Ansible, a installer avec pip

``ansible/deploy.yml``
    C'est le script de deploiement en ansible

``home=/tmp/testmrs``
    Que le deploiement persiste dans ce dossier (en prod: /home/mrs-production)

``compose_django_ports='["8000:8000"]'``
    Cela permet au deploiement d'etre utilisable sans load balancer en
    l'exposant sur le port 8000 de localhost

``compose_django_build=``
    Annule la configuration de build: on ne veut pas qu'il essaye de builder en production

``compose_django_image=betagouv/mrs:master``
    Image a deployer: vu qu'on ne veut pas la builder en prod

``compose=docker-compose.yml,docker-compose.persist.yml``
    Liste des fichiers compose a fusionner pour la configuration finale de ce deploiement

Vagrant
-------

Vagrant necessite VirtualBox, c'est une alternative au developpement local qui
permet d'avoir la meme version que centos sur les serveurs, et vous permet de
tester sans ajouter des crons inutiles sur votre systeme local grace a
l'isolation d'une machine virtuelle.

Pour alleger le workflow de commandes, des raccourcis sont mis dans le script
``./do`` a la racine du repo:

- ``./do vagrant apply`` enchaine un destroy et un up
- ``./do vagrant up`` fait un up et puis genere la config ssh dans ``./.vagrant-ssh``
- ``./do vagrant bigsudo`` se substitue a ``bigsudo`` et passe
  ``./.vagrant-ssh`` en argument ansible et vise bien la VM default

Examples::

    ./do vagrant bigsudo yourlabs.traefik -v
    ./do vagrant bigsudo ansible/deploy.yml
