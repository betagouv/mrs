#!/bin/bash -eux
pip install --user ansible
mkdir -p ~/.ssh && chmod 700 ~/.ssh
for host in $KEYSCAN_HOSTS; do
    ssh-keyscan $host  >> ~/.ssh/known_hosts
done
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
git status

set +x  # silence password from output
echo $VAULT_PASSWORD > .vault
set -x

# Please forgive the horror you are going to see but I cannot refactor this
# until I have recovered from RSI
if [ $CIRCLE_STAGE = 'production' ]; then
    host=mrs-prod
else
    host=mrs
fi

export ANSIBLE_VAULT_PASSWORD_FILE=.vault
~/.local/bin/ansible-playbook --tags update -u deploy -i inventory -l $host -e prefix=mrs -e image=betagouv/mrs:$CIRCLE_SHA1 -e instance=$CIRCLE_STAGE playbooks/django.yml
