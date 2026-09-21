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
| `/etc/os-release`, `/etc/lsb-release` | identidad del sistema (ver abajo) |
| `/etc/fastfetch/config.jsonc`, `/etc/static-linux/accent` | valores por defecto — `sl-welcome`/`sl-ctl accent` los sobrescriben después |

## `/etc/os-release` sin pelearse con `filesystem`

En un Arch normal `/etc/os-release` es un symlink a `/usr/lib/os-release`,
propiedad del paquete `filesystem`. Este paquete no toca `/usr/lib/os-release`
en ningún momento — instala `/etc/os-release` y `/etc/lsb-release` como
archivos normales en esa ruta exacta, reemplazando el symlink. Nadie más es
dueño de esa ruta literal, así que no hay conflicto de `conflicts`/`provides`
con `filesystem`, y como la mayoría de lectores de `/etc/os-release` miran
primero ahí antes que en `/usr/lib/`, con eso basta para que fastfetch, los
paneles "Acerca de" de GNOME/KDE, `lsb_release` y cualquier herramienta que
mire `ID_LIKE=arch` digan Static Linux correctamente. Ambos archivos están en
`backup=()`, así que una actualización futura del paquete deja un `.pacnew`
en vez de pisar un cambio hecho a mano.

## Por qué dos jerarquías (`/usr/lib/` vs `/usr/share/`)

`/usr/lib/static-linux/` es para lo operativo — scripts, reglas, listas de
paquetes, dotfiles. `/usr/share/static-linux/` es para los assets
compartidos e independientes de arquitectura — wallpapers, logos de
fastfetch. Es la separación estándar de FHS, y `branding/accents/apply.sh`
ya la sigue: primero intenta `/usr/share/static-linux/wallpapers` (instalado)
y solo si no existe cae al checkout de git en modo desarrollo — el mismo
patrón "ruta instalada, si no, relativa al repo" que usan `sl-ctl.py` y
`sl-welcome/src/paths.py`.
