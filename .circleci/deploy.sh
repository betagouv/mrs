#!/bin/bash -eux
mkdir -p ~/.ssh && chmod 700 ~/.ssh
for host in $KEYSCAN_HOSTS; do
    ssh-keyscan $host  >> ~/.ssh/known_hosts
done

set +x  # silence password from output
echo $VAULT_PASSWORD > .vault
set -x

chmod 600 ~/.ssh/*

mkdir -p .infra && cd .infra
for i in playbooks inventory; do
    if [ ! -d $i ]; then
        git clone $INFRA_REPOSITORIES/${i}.git &
    else
        pushd $i
        git fetch
        git reset --hard origin/master
        popd
    fi
done

export ANSIBLE_VAULT_PASSWORD_FILE=.vault
export ANSIBLE_STDOUT_CALLBACK=debug
ansible-playbook \
    --tags update \
    --user deploy \
    --inventory inventory/inventory.yml \
    -e image=betagouv/mrs:gitlab \
    -e prefix=mrs \
    -e instance=$CI_ENVIRONMENT_SLUG \
    -v playbooks/django.yml
