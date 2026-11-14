# Instalación

!!! note "Probado en máquinas virtuales"
    La ISO se instala de principio a fin en QEMU/KVM (UEFI), con y sin
    conexión. En hardware real solo se ha probado la vía manual del final
    ([iMedia S2883](hardware/imedia-s2883.md)); la prueba con la ISO en
    otro equipo está pendiente.

## Conseguir la ISO

Descárgala desde [staticforge.me/linux/descargar](https://staticforge.me/linux/descargar/)
o constrúyela: [Construir la ISO](iso.md). Grábala en un USB con
`dd`, Ventoy, balenaEtcher o Rufus (modo DD) y arranca desde él con UEFI y
Secure Boot apagado.

La ISO **universal** instala sin conexión: el sistema base, el escritorio,
el kernel y el perfil de privacidad van dentro. Los sabores necesitan red;
si no la hay, se añaden después con `sudo sl-ctl flavor add pending`.

## Vía Calamares

`settings.conf` ya tiene la secuencia completa: `sl-detect` (detecta
hardware) → elegir entorno/privacidad (`packagechooser`, ver
[Sabores](sabores.md) para cómo `entorno-pkgs`/`privacidad-apply` actúan
sobre esa elección) → partición → usuarios → resumen → instalación real
(paquetes base, entorno, sabores, tema, avisos de LUKS, bootloader...). La
página **Tema** enseña capturas reales de los ocho [temas](temas.md); el
elegido se aplica al usuario y a `/etc/skel`.
`installer/calamares/branding/staticlinux/branding.desc` todavía no tiene
un logo real (Core hace su propio diseño).

## Vía manual (la única validada en hardware real)

1. Arranca el live ISO de Arch (o el de Static Linux una vez probado).
2. Particiona: EFI (512 MB, FAT32) + raíz. `sl-detect` recomienda EXT4 en
   HDD, BTRFS en SSD con ≥4 GB de RAM.
3. `pacstrap` con `packages/lists/base.list` (quita las líneas `(AUR)`
   primero — esas se instalan con `paru` después del primer arranque).
4. `arch-chroot`, genera fstab, configura bootloader (GRUB — copia siempre
   `grubx64.efi` a `/EFI/BOOT/BOOTX64.EFI` como fallback, algunos firmwares
   UEFI limitados lo necesitan).
5. Si la RAM es < 4 GB, crea un swapfile de 2 GB y añádelo a `/etc/fstab`
   ANTES de compilar nada pesado (paru compilando Rust se puede comer toda
   la RAM sin él).
6. Instala el entorno elegido:
   ```bash
   sudo pacman -S --needed - < packages/lists/xfce.list   # o el que toque
   entornos/xfce-themed/install.sh --home
   ```
7. Arranca `paru` (compilado desde AUR) e instala las líneas `(AUR)` que
   quitaste en el paso 3.

## Después de instalar

`sl-welcome` se abre solo en el primer arranque (una vez por usuario) —
apariencia, perfil de privacidad y catálogo de apps extra desde ahí. Ver
[sl-welcome](herramientas/sl-welcome.md) y [sl-ctl](herramientas/sl-ctl.md)
para todo lo que se puede tocar después.
