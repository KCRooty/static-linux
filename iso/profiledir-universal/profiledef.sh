#!/usr/bin/env bash
# shellcheck disable=SC2034
# Static Linux — archiso profile metadata (universal ISO: installs with or without a network).
# airootfs/, efiboot/, syslinux/, grub/ and pacman.conf are NOT here — they're
# assembled by ../build.sh at build time (see its header comment for why).

iso_name="static-linux"
iso_label="STATICLINUX_$(date +%Y%m)"
iso_publisher="Static Forge <https://github.com/KCRooty/static-linux>"
iso_application="Static Linux — universal install medium (fast. private. yours.)"
iso_version="${SL_ISO_VERSION:-$(date +%Y.%m.%d)}"
install_dir="staticlinux"
buildmodes=('iso')
bootmodes=('bios.syslinux' 'uefi.systemd-boot')
arch="x86_64"
# Quiet boot: without this the screen between the boot menu and the
# installer is archiso's initramfs log (":: running hook [archiso]",
# "systemd-udevd version …-arch") — reads as an Arch installer, not ours.
# copytoram=n: the image carries ~2.6 GB of packages for offline installs;
# copying it all to RAM would rule out 2-4 GB machines for no gain.
kernel_params_x86_64="quiet loglevel=3 copytoram=n"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '15')
file_permissions=(
    ["/etc/shadow"]="0:0:400"
    ["/root"]="0:0:750"
    ["/root/.bash_profile"]="0:0:644"
    ["/root/.xinitrc"]="0:0:755"
    ["/usr/local/bin/sl-live-install"]="0:0:755"
    ["/usr/local/lib/static-linux-live/setup.sh"]="0:0:755"
)
