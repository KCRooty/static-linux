# Construir la ISO

```bash
sudo pacman -S --needed archiso git base-devel
packages/local-repo.sh               # paquetes propios, como usuario normal
sudo iso/build.sh universal          # ~4,5 GB, instala con o sin red
sudo iso/build.sh online             # ~2 GB, descarga todo al instalar
```

La ISO sale en `iso/out/`. Hacen falta unos 25 GB libres para la universal
(paquetes descargados, el directorio de trabajo de archiso y la ISO).

## Universal u online

| | Universal | Online |
|---|---|---|
| Tamaño | ~4,5 GB | ~2 GB |
| Sin conexión | instala base, cualquier escritorio, los tres kernels y el perfil de privacidad | no instala |
| Con conexión | instala lo mismo desde la ISO, pone el sistema al día (`pacman -Syu`) y añade los sabores | descarga todo |
| Sabores | con red al instalar, o después con `sudo sl-ctl flavor add pending` | con red al instalar |

La que se publica es la **universal**: sirve en cualquier situación. La
online queda para pruebas rápidas.

### Qué lleva dentro la universal

`build.sh` descarga, contra una base de datos de pacman vacía (así llegan
todas las dependencias), todo lo que el instalador puede pedir:

- `base.list` + `sin-escritorio.list` (consola) + `privacy-*.list`
- cada escritorio (`xfce.list`, `kde.list`, …), en una llamada por
  escritorio porque algunas listas chocan entre sí
- `linux-lts`, `linux-zen` y `linux-hardened`, con sus cabeceras

Queda como repositorio `staticlinux-offline` en `/opt/staticlinux-offline`
de la imagen (1.300 paquetes, 2,6 GB el 2026-11-14). Los sabores no van: la
ISO doblaría su tamaño y varios necesitan Flathub igualmente.

El arranque lleva `copytoram=n`: la imagen no se copia entera a la RAM, así
que también arranca en equipos de 2 GB.

### Cómo instala sin red

Lo hace `installer/calamares/lib/slinstall.py`, que comparten los trabajos
del instalador:

- **basepkgs**: `pacstrap -C` con un `pacman.conf` que solo conoce los dos
  repositorios de la ISO (`staticlinux-offline` y `staticlinux-local`).
- **entorno-pkgs** y **privacidad-apply**: montan esos repositorios dentro
  del sistema nuevo e instalan solo desde ellos, para no mezclar la foto de
  la ISO con paquetes más nuevos de los mirrors a mitad de instalación.
- **sabores**: con red, primero `pacman -Syu` y después los sabores desde
  los mirrors; sin red, los apunta en `/etc/static-linux/pending-flavors`.
- Al final se borran de `/var/cache/pacman/pkg` las copias de lo que vino de
  la ISO (~1,5 GB que no hacen falta).

La comprobación de red tiene un tope de 6 segundos, y la página de
bienvenida avisa de que no hay conexión pero deja seguir.

## Cómo se monta la imagen

`iso/build.sh` monta el `airootfs/` de la sesión en vivo en cada build
(nada de esto se guarda en el repositorio):

1. La fontanería de archiso (hooks del initramfs, llavero de pacman…) y la
   cadena de arranque (`efiboot/`, `syslinux/`, `grub/`, `pacman.conf`), tal
   cual del perfil `releng` del paquete `archiso`, con los menús renombrados
   a Static Linux.
2. El escritorio en vivo: el `skel` de XFCE con el tema Ámbar y
   `iso/airootfs-common/` encima (autologin, `sl-live-install`).
3. `installer/calamares/` en `/etc/calamares/`, con la fecha de la ISO como
   versión.
4. El repositorio local (`packages/aur-cache/`) en `/opt/staticlinux-repo`:
   `calamares`, `staticlinux-base`, Brave Origin, paru y Astal no están en
   los repositorios oficiales.

`calamares` solo está en el AUR, y el paquete del AUR no trae los trabajos
en Python que usa este instalador: se compila con
`packages/calamares/PKGBUILD` dentro de `local-repo.sh`.

## Builds de desarrollo

`--dev-ssh-key CLAVE.pub` añade SSH de root con esa clave a la sesión en
vivo, para manejar el instalador desde la máquina de build (QEMU). **Una ISO
así no se distribuye nunca.**

## Publicar

1. `sudo iso/build.sh universal` (sin `--dev-ssh-key`).
2. Suma y firma con la clave de Static Forge:
   `sha256sum ISO > ISO.sha256` y `gpg --detach-sign --armor ISO` (deja
   `ISO.asc`; se publica también como `ISO.sig`).
3. Subir los tres archivos a SourceForge y a los demás espejos.
4. Nota de la versión: cambios, arreglos y problemas conocidos.
