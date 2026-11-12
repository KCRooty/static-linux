# sl-welcome

App de primer arranque. GTK4 + libadwaita (Python/PyGObject) — se abre sola
una vez por usuario (marcador en `~/.local/state/static-linux/welcome-shown`)
y también se puede relanzar con `sl-ctl welcome`.

## Por qué libadwaita

`sl-theme` escribe los colores con nombre de libadwaita (`accent_color`,
`accent_bg_color`, `window_bg_color`...) en `~/.config/gtk-4.0/gtk.css`. Una
app libadwaita los hereda gratis: `sl-welcome` no lleva código de temas
propio y se ve con la paleta del [tema](../temas.md) activo.

## Páginas

| Página | Qué hace | Privilegios |
|---|---|---|
| General | Cabecera de marca + lectura en vivo de `sl-detect --json` | Ninguno |
| Apariencia | Selector de [temas](../temas.md) con su vista previa; ejecuta `sl-theme <id>` | Ninguno (aplica al usuario actual) |
| Privacidad | Los 3 perfiles — ver [Privacidad](../privacidad.md) | `pkexec` |
| Catálogo | Apps de Static Forge y ~56 apps extra en 8 categorías | `pkexec` (paquetes AUR se listan pero no se instalan aquí) |

## Por qué un wrapper de pkexec dedicado

`data/apply-profile` es un script diminuto que valida su argumento antes de
ejecutar el `apply.sh` del perfil correspondiente. La política de polkit
(`data/dev.staticforge.welcome.policy`) apunta
`org.freedesktop.policykit.exec.path` a ese archivo exacto — no a
`/usr/bin/bash` — para que el mensaje amigable de "aplicar perfil de
privacidad" de `sl-welcome` no aparezca en cualquier otro `pkexec bash` del
sistema. La instalación de paquetes del catálogo va directa por
`pkexec pacman`, que ya es lo bastante precisa por sí sola.

## Catálogo de apps

`sl-welcome/catalog/*.yaml`, una categoría por archivo:

```yaml
category: "Nombre visible"
apps:
  - id: id-unico
    name: Nombre mostrado
    desc: Una frase, en español.
    pkg: nombre-del-paquete
    aur: true   # solo si viene del AUR (si no, se omite)
```

Los paquetes con `aur: true` aparecen en la lista pero sin checkbox —
`pacman` no puede compilar AUR como root durante una instalación
automatizada, así que la fila indica el `paru -S <pkg>` a mano.

## Sección Static Forge

`catalog/00-static-forge.yaml` va primero y lista el software del estudio.
Hoy trae **KC Downloader** (3.0.1). Sus filas usan `sf: <paquete>` en vez de
`pkg:`: el PKGBUILD vive en `packages/sf/<paquete>/` (se instala en
`/usr/lib/static-linux/packages/sf/`) y `sl-welcome` lo construye con
`makepkg -si` en una terminal, como usuario normal.

```yaml
  - id: kc-downloader
    name: KC Downloader
    desc: Descarga de YouTube, YouTube Music, Spotify y Pinterest, hecho en el estudio.
    sf: kc-downloader-bin
```
