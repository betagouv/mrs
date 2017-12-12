#!/bin/bash -eux
pip install --user ansible
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keyscan $INFRA_REPOSITORY_HOST >> ~/.ssh/known_hosts
ssh-keyscan $DEPLOY_HOST >> ~/.ssh/known_hosts
chmod 600 ~/.ssh/known_hosts

if [ ! -d ~/.local/infra ]; then
    git clone --recursive $INFRA_REPOSITORY ~/.local/infra
    cd ~/.local/infra
else
    cd ~/.local/infra
    git fetch
    git reset --hard origin/master
    git submodule update --init
fi

set +x  # silence password from output at all cost
echo $VAULT_PASSWORD > .vault &> /dev/null
set -x

export ANSIBLE_VAULT_PASSWORD_FILE=.vault
~/.local/bin/ansible-playbook --tags update -u deploy -i inventory -e prefix=mrs -e image=betagouv/mrs:$CIRCLE_SHA1 -e instance=$CIRCLE_STAGE playbooks/django.yml
