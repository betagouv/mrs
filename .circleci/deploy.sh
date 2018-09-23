#!/bin/bash -eux
mkdir -p ~/.ssh && chmod 700 ~/.ssh
for host in $KEYSCAN_HOSTS; do
    ssh-keyscan $host  >> ~/.ssh/known_hosts
done
chmod 600 ~/.ssh/*

if [ ! -d .infra ]; then
    git clone --recursive $INFRA_REPOSITORY ~/.infra
    cd ~/.infra
else
    cd ~/.infra
    git fetch
    git reset --hard origin/master
    git submodule update --init
fi
git status

set +x  # silence password from output
echo $SSH_PRIVKEY > ~/.ssh/id_rsa
echo $VAULT_PASSWORD > .vault
set -x

export ANSIBLE_VAULT_PASSWORD_FILE=.vault
export ANSIBLE_STDOUT_CALLBACK=debug
ansible-playbook \
    --tags update \
    --user deploy \
    --inventory inventory.yml \
    -e image=betagouv/mrs:gitlab \
    -e prefix=mrs \
    -e instance=$CI_ENVIRONMENT_SLUG \
    -v playbooks/django.yml
