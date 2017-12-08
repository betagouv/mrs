#!/bin/bash -eux
pip install --user ansible
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keyscan $INFRA_REPOSITORY_HOST >> ~/.ssh/known_hosts
ssh-keyscan $DEPLOY_HOST >> ~/.ssh/known_hosts
chmod 600 ~/.ssh/known_hosts

git clone --recursive $INFRA_REPOSITORY infra
cd infra
echo $VAULT_PASSWORD > .vault
export ANSIBLE_VAULT_PASSWORD_FILE=.vault
~/.local/bin/ansible-playbook -u deploy -i inventory -e image=betagouv/mrs:$CIRCLE_SHA1 -e instance=$CIRCLE_STAGE playbooks/mrs.yml
