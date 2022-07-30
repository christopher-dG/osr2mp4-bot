#!/usr/bin/env bash

cd "$(dirname $0)/.."
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
