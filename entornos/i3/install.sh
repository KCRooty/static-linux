#!/bin/bash
# Static Linux — deploy i3 (dotfiles + active theme). See ../common/deploy.sh.
set -uo pipefail
ENV_NAME=i3
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON=/usr/lib/static-linux/entornos/common/deploy.sh
[[ -f "$COMMON" ]] || COMMON="$HERE/../common/deploy.sh"
# shellcheck source=../common/deploy.sh
. "$COMMON"
deploy "$@"
