# staticlinux-base

El paquete que convierte "un montón de scripts en un repo git" en una
instalación real de Arch que se identifica y se comporta como Static Linux.
Todo lo que `installer/calamares/modules/*`, `sl-ctl` y `sl-welcome` asumen
que vive en `/usr/lib/static-linux/...` sale de aquí.

## Construir

```bash
cd packages/staticlinux-base
makepkg -si
```

Sin `source=()` que descargar — empaqueta el propio monorepo tal cual, así
que hay que ejecutarlo desde dentro de un checkout.

## Qué instala

| Dónde | Qué |
|---|---|
| `/usr/lib/static-linux/` | sl-detect, sl-ctl, sl-welcome, accents, privacidad, `packages/lists/*.list`, `entornos/*/{install.sh,skel/}` |
| `/usr/share/static-linux/` | logos de fastfetch, un wallpaper por acento + el generador |
| `/usr/bin/{sl-detect,sl-ctl,sl-welcome}` | symlinks a lo anterior |
| `/usr/lib/static-linux/os-release` | identidad del sistema (ver abajo) |
| `/etc/fastfetch/config.jsonc`, `/etc/static-linux/accent` | valores por defecto — `sl-welcome`/`sl-ctl accent` los sobrescriben después |

## `/etc/os-release` sin pelearse con `filesystem`

En un Arch normal `/etc/os-release` es un symlink a `/usr/lib/os-release`,
propiedad del paquete `filesystem`. Este paquete no toca `/usr/lib/os-release`
en ningún momento — instala su propia copia en
`/usr/lib/static-linux/os-release`, y el script de instalación reapunta el
symlink `/etc/os-release` hacia ella (al desinstalar el paquete vuelve a
apuntar a `../usr/lib/os-release`). Con eso basta para que fastfetch, los
paneles "Acerca de" de GNOME/KDE, `lsb_release` y cualquier herramienta que
mire `ID_LIKE=arch` digan Static Linux correctamente. Si `/etc/os-release`
es un archivo normal hecho a mano, no se toca.

No se instala directamente en `/etc/os-release` a propósito: en un Arch de
serie esa ruta ya existe como symlink sin dueño, así que pacman da conflicto
de archivos o — con el archivo en `backup=()` — deja el nuestro como
`/etc/os-release.pacnew` y el sistema sigue diciendo "Arch Linux".

No hay `/etc/lsb-release`: esa ruta es del paquete `lsb-release` (del que
depende Steam), y al incluirla aquí instalar Steam fallaba por conflicto de
archivos. `lsb_release` lee `os-release`, así que dice Static Linux igual.

## Por qué dos jerarquías (`/usr/lib/` vs `/usr/share/`)

`/usr/lib/static-linux/` es para lo operativo — scripts, reglas, listas de
paquetes, dotfiles. `/usr/share/static-linux/` es para los assets
compartidos e independientes de arquitectura — wallpapers, logos de
fastfetch. Es la separación estándar de FHS, y `branding/accents/apply.sh`
ya la sigue: primero intenta `/usr/share/static-linux/wallpapers` (instalado)
y solo si no existe cae al checkout de git en modo desarrollo — el mismo
patrón "ruta instalada, si no, relativa al repo" que usan `sl-ctl.py` y
`sl-welcome/src/paths.py`.
