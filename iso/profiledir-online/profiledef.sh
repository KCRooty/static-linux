#!/usr/bin/env bash
# shellcheck disable=SC2034
# Static Linux — archiso profile metadata (online ISO).
# airootfs/, efiboot/, syslinux/, grub/ and pacman.conf are NOT here — they're
# assembled by ../build.sh at build time (see its header comment for why).

iso_name="static-linux"
iso_label="STATICLINUX_ONLINE_$(date +%Y%m)"
iso_publisher="Static Forge <https://github.com/KCRooty/static-linux>"
iso_application="Static Linux — online install medium (fast. private. yours.)"
iso_version="$(date +%Y.%m.%d)"
install_dir="staticlinux"
buildmodes=('iso')
bootmodes=(
    'bios.syslinux.mbr' 'bios.syslinux.eltorito'
    'uefi-x64.systemd-boot.esp' 'uefi-x64.systemd-boot.eltorito'
)
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '19')
file_permissions=(
    ["/etc/shadow"]="0:0:400"
    ["/root"]="0:0:750"
    ["/root/.bash_profile"]="0:0:644"
    ["/root/.xinitrc"]="0:0:755"
)
