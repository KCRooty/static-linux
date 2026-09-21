# sl-welcome

App de primer arranque. GTK4 + libadwaita (Python/PyGObject) — se abre sola
una vez por usuario (marcador en `~/.local/state/static-linux/welcome-shown`)
y también se puede relanzar con `sl-ctl welcome`.

## Por qué libadwaita

`branding/accents/apply.sh` ya escribe los colores con nombre propios de
libadwaita (`accent_color`, `accent_bg_color`, `theme_selected_bg_color`...)
en `~/.config/gtk-4.0/gtk.css` para cada acento de la paleta. Una app
libadwaita los hereda gratis — cero código específico de acento dentro de
`sl-welcome`, un solo camino de theming para todo el sistema (fastfetch,
GTK, xfwm4, terminal, greeter, fondo de pantalla y `sl-welcome`).

## Páginas

| Página | Qué hace | Privilegios |
|---|---|---|
| General | Cabecera de marca + lectura en vivo de `sl-detect --json` | Ninguno |
| Apariencia | Los 10 acentos de `branding/accents/palette.conf` | Ninguno (aplica al usuario actual) |
| Privacidad | Los 3 perfiles — ver [Privacidad](../privacidad.md) | `pkexec` |
| Catálogo | ~56 apps extra en 8 categorías, más allá del entorno elegido | `pkexec` (paquetes AUR se listan pero no se instalan aquí) |

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
