# Repositorio `[staticlinux]`

Los paquetes propios de Static Linux (y los del AUR que van de serie) se
publican en un repositorio de pacman firmado. Así llegan las correcciones y
las versiones nuevas con un `sudo pacman -Syu` (o `sudo sl-ctl update`),
sin reinstalar desde una ISO.

| Paquete | Qué es |
|---|---|
| `staticlinux-base` | sl-ctl, sl-detect, sl-welcome, temas, entornos, perfiles de privacidad, ajustes de rendimiento |
| `staticlinux-keyring` | la clave pública con la que se firma todo esto |
| `staticlinux-fonts` | fuentes de la marca (Outfit, Space Grotesk) |
| `brave-origin-bin` | el navegador por defecto, compilado desde el paquete AUR de Brave |
| `paru-bin` | ayudante del AUR |
| `aylurs-gtk-shell`, `libastal-*` | la barra de Hyprland (Astal), que solo está en el AUR |

Vive en las *releases* de GitHub, en la etiqueta
[`repo`](https://github.com/KCRooty/static-linux/releases/tag/repo). No es
una versión para descargar a mano: la usa pacman.

## La clave

Todo está firmado con la **clave de Static Forge**, la misma que firma las
ISOs:

```
Static Forge (Static Linux release key) <staticforge@staticforge.me>
3E61 7ED0 6C90 C757 35C9  C45E 51D5 8FA3 5045 B8D0
```

El repositorio se declara con `SigLevel = Required`: un paquete o una base de
datos sin firma válida de esa clave no se instala.

## En una instalación nueva

El instalador lo deja todo hecho: instala `staticlinux-keyring` (que mete la
clave en el llavero de pacman) y añade esto a `/etc/pacman.conf`:

```ini
[staticlinux]
SigLevel = Required
Server = https://github.com/KCRooty/static-linux/releases/download/repo
```

## En una instalación anterior al 2026-11-14

Las ISOs de antes no traían el repositorio. Se añade a mano una vez:

```bash
curl -LO https://github.com/KCRooty/static-linux/releases/download/repo/staticlinux-keyring-2026.11.14-1-any.pkg.tar.zst
sudo pacman -U staticlinux-keyring-2026.11.14-1-any.pkg.tar.zst
pacman-key --finger 3E617ED06C90C75735C9C45E51D58FA35045B8D0   # comprueba la huella de arriba
printf '\n[staticlinux]\nSigLevel = Required\nServer = https://github.com/KCRooty/static-linux/releases/download/repo\n' \
    | sudo tee -a /etc/pacman.conf
sudo pacman -Syu
```

## Para desarrollo

```bash
packages/local-repo.sh                 # compila todo en packages/aur-cache/
packages/publish-repo.sh --dry-run     # firma y monta el repo en aur-cache/.publish
packages/publish-repo.sh               # y lo sube a la release `repo`
```

`publish-repo.sh` firma cada paquete y la base de datos con la clave de
Static Forge (la frase de paso sale de `~/.config/static-linux/gpg.env`,
nunca del repositorio). GitHub no admite `:` en los nombres de archivo, así
que los paquetes con *epoch* (`brave-origin-bin 1:…`) se suben con `.` en su
lugar; pacman descarga el nombre que figura en la base de datos, así que da
igual. `staticlinux-base` lleva fecha y hora como versión, para que dos
compilaciones del mismo día sigan siendo una actualización.
