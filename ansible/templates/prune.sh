#!/bin/bash -eux
pushd {{ home }}
export RESTIC_PASSWORD_FILE=.restic_password
export RESTIC_REPOSITORY={{ lookup('env', 'RESTIC_REPOSITORY') or home + '/restic' }}
restic forget --keep-last 7 --keep-daily 7 --keep-weekly 5 --keep-monthly 12 --keep-yearly 75
restic prune
restic rebuild-index
restic check
