#!/bin/bash
# Static Linux — Privacy profile: Basic
# Baseline day-0 defaults + UFW + MAC randomization. Kernel: linux-zen.
#
# Reversible: originals are copied to /var/backups/static-linux/privacy/
# before any change. `sl-ctl privacy --profile <other>` re-runs the target
# profile; a full revert restores from that backup tree.

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../scripts/lib.sh
source "$HERE/../scripts/lib.sh"

sl_require_root
sl_log "=== Applying privacy profile: Basic ==="

sl_apply_baseline

# Coming back from Improved/Maximum: AppArmor out of the kernel command line
# and its service off (the profiles stay installed, unused).
sl_apparmor_cmdline off
systemctl disable apparmor.service >/dev/null 2>&1 || true

sl_record_profile "basic"
sl_log "Basic profile applied. Reboot recommended (kernel/journald changes)."
