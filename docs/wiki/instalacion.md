# Instalación

!!! warning "Instalador Calamares — en desarrollo"
    El instalador gráfico (Calamares) todavía no está completo — varios de
    sus módulos (`entorno`, `privacidad`) son stubs, y `sabores`/`luks` son
    jobs funcionales pero sin página de selección todavía. Hasta que esté
    terminado, la vía probada es la instalación manual descrita abajo, que
    es exactamente como se validó Static Linux en el
    [iMedia S2883](hardware/imedia-s2883.md).

## Vía manual (la que ya funciona)

1. Arranca el live ISO de Arch (o el de Static Linux cuando exista la
   Fase 3 — ver `docs/PROYECTO.md`).
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

## Vía Calamares (cuando esté lista)

`installer/calamares/` ya tiene los jobs de `sl-detect` (detecta hardware y
publica el resultado) y `accent` (aplica el color elegido). `sabores` y
`luks` están escritos (ver [Sabores](sabores.md)) pero todavía sin una
página de selección — de momento se activan pasando
`globalStorage["slSabores"]` a mano o vía un `settings.conf` de automatización.

## Después de instalar

`sl-welcome` se abre solo en el primer arranque (una vez por usuario) —
apariencia, perfil de privacidad y catálogo de apps extra desde ahí. Ver
[sl-welcome](herramientas/sl-welcome.md) y [sl-ctl](herramientas/sl-ctl.md)
para todo lo que se puede tocar después.
