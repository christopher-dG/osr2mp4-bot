#!/usr/bin/env bash

cd "$(dirname $0)/.."

if [[ "$1" == "docker" ]]; then
  set -euxo pipefail
  shift 1
  export COMPOSE_PROJECT_NAME=osr2mp4-bot-test
  if [[ -f data/appendonly.aof ]]; then
    backup="$(mktemp --suffix .aof)"
    echo "Saving Redis AOF backup to $backup"
    cp data/appendonly.aof "$backup"
  fi
  mapset="$(mktemp --directory)"
  unzip -d "$mapset" assets/mapset.osz
  docker-compose up --build --detach worker
  docker cp "$mapset" osr2mp4-bot-test_worker_1:/tmp/mapset
  rm --recursive --force "$mapset"
  for file in assets/replay.osr setup.cfg test; do
    docker cp "$file" "osr2mp4-bot-test_worker_1:/tmp/$(basename $file)"
  done
  docker-compose exec -T redis redis-cli FLUSHALL
  docker-compose exec -T -u root worker sh -c 'chown 1000 $SHARE_DIR /tmp/mapset'
  set +e
  docker-compose exec -T worker bash <<EOF
    pip install pytest-cov
    mkdir \$HOME/testenv
    cd \$HOME/testenv
    cp --recursive \$HOME/src /tmp/mapset /tmp/replay.osr /tmp/test /tmp/setup.cfg .
    python -m pytest --cov src $@
EOF
  exit="$?"
  docker-compose exec -T redis rm /data/appendonly.aof
  docker-compose down
  exit "$exit"
else
  checked() {
    echo "$ $@"
    "$@"
    last="$?"
    if [ "$last" -ne 0 ]; then
      echo "$@: exit $last"
      exit=1
    fi
  }
  exit=0
  python -m pytest --cov src
  flake8 bin src test
  black --check bin src test
  mypy --strict src
  exit "$exit"
fi
