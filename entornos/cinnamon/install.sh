#!/bin/bash
# Static Linux — deploy cinnamon (dotfiles + active theme). See ../common/deploy.sh.
set -uo pipefail
ENV_NAME=cinnamon
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON=/usr/lib/static-linux/entornos/common/deploy.sh
[[ -f "$COMMON" ]] || COMMON="$HERE/../common/deploy.sh"
# shellcheck source=../common/deploy.sh
. "$COMMON"
deploy "$@"
