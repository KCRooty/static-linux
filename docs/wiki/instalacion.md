# Instalación

!!! warning "Nada de esto está probado en hardware real todavía"
    `installer/calamares/settings.conf` tiene la secuencia completa y
    `iso/build.sh` sabe construir la ISO, pero ninguno de los dos se ha
    corrido en una máquina Arch de verdad esta sesión (sin hardware
    disponible — ver el estado de hardware en `AGENTS.md`). La vía manual
    de abajo es la única validada en hardware real hasta ahora ([iMedia
    S2883](hardware/imedia-s2883.md)).

## Construir la ISO

```bash
sudo pacman -S archiso
cd iso
sudo ./build.sh online     # ~1 GB, necesita red al instalar
sudo ./build.sh offline    # ~4 GB, paquetes empaquetados (ver iso/README.md)
```

`calamares` es un paquete solo-AUR — `build.sh` lo comprueba al principio y
para con un mensaje claro si tu máquina de build no lo tiene en ningún repo
configurado (necesitas tu propio repo local con `calamares` compilado antes
de construir; ver `iso/README.md` para el porqué). El ISO offline hoy solo
empaqueta los paquetes en la caché de la imagen — que Calamares los use sin
red durante la instalación todavía no está resuelto, también documentado
ahí.

## Vía Calamares

`settings.conf` ya tiene la secuencia completa: `sl-detect` (detecta
hardware) → elegir entorno/privacidad (`packagechooser`, ver
[Sabores](sabores.md) para cómo `entorno-pkgs`/`privacidad-apply` actúan
sobre esa elección) → partición → usuarios → resumen → instalación real
(paquetes base, entorno, sabores, acento, avisos de LUKS, bootloader...).
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
