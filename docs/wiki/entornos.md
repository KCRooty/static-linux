# Entornos de escritorio

`sl-detect` recomienda uno de los cuatro primeros según el hardware (KDE Plasma
se elige a mano) — ver
[Requisitos de hardware](hardware/requisitos.md) para la tabla de
decisión completa. Cada uno vive en `entornos/<nombre>/`, con su propio
`install.sh --home|--skel` idempotente (con backup automático).

| Entorno | RAM | Display | Estado |
|---|---|---|---|
| [`hyprland-astal-full`](https://github.com/KCRooty/static-linux/tree/main/entornos/hyprland-astal-full) | ≥ 4 GB | Wayland | Escrito, sin probar en hardware real |
| [`hyprland-astal-lite`](https://github.com/KCRooty/static-linux/tree/main/entornos/hyprland-astal-lite) | 2-4 GB | Wayland | Escrito, sin probar en hardware real |
| [`xfce-themed`](https://github.com/KCRooty/static-linux/tree/main/entornos/xfce-themed) | ≥ 1 GB | Xorg | **Validado en el iMedia S2883** |
| [`openbox-minimal`](https://github.com/KCRooty/static-linux/tree/main/entornos/openbox-minimal) | ≥ 512 MB | Xorg | Escrito, sin probar en hardware real |
| [`kde-plasma`](https://github.com/KCRooty/static-linux/tree/main/entornos/kde-plasma) | ≥ 4 GB | Wayland | Nuevo (2026-10) |
| [`gnome`](https://github.com/KCRooty/static-linux/tree/main/entornos/gnome) | ≥ 4 GB | Wayland | Nuevo (2026-11), probado en VM |
| [`cinnamon`](https://github.com/KCRooty/static-linux/tree/main/entornos/cinnamon) | ≥ 2 GB | Xorg | Nuevo (2026-11), probado en VM |
| [`i3`](https://github.com/KCRooty/static-linux/tree/main/entornos/i3) | ≥ 1 GB | Xorg | Nuevo (2026-11), probado en VM |
| [`bspwm`](https://github.com/KCRooty/static-linux/tree/main/entornos/bspwm) | ≥ 1 GB | Xorg | Nuevo (2026-11), probado en VM |
| [`sway`](https://github.com/KCRooty/static-linux/tree/main/entornos/sway) | ≥ 1 GB | Wayland | Nuevo (2026-11), probado en VM |

KDE Plasma, GNOME, Cinnamon, i3, bspwm y sway se eligen a mano en el
instalador; `sl-detect` no los recomienda.

`xfce-themed` es el único que se ha visto arrancar en una máquina real hasta
ahora — ver la [referencia del iMedia S2883](hardware/imedia-s2883.md).

## Hyprland + Astal (full / lite)

Hyprland ≥ 0.56 se configura en **Lua**. La configuración de Static Linux
(atajos, aspecto, arranque, reglas) vive en
`/usr/share/static-linux/hypr/static.lua` y se actualiza con el sistema; tu
`~/.config/hypr/hyprland.lua` solo elige el nivel (`full` o `lite`), la carga y
deja sitio para tus cambios, que mandan sobre los de serie.

- **Barra** propia con [Astal](https://aylur.github.io/astal/) (`~/.config/ags/`,
  TypeScript + GTK4): lanzador, escritorios, reloj con calendario, bandeja,
  wifi, volumen, batería y menú de apagado. Sigue el acento activo.
- **Guía de atajos:** se abre sola en el primer inicio de sesión y con
  **Super + F1**. Lee los atajos en vivo de Hyprland, así que siempre coincide
  con tu configuración (los tuyos también salen si les pones `description`).
- El teclado sigue la distribución elegida en el instalador; los bordes y la
  pantalla de bloqueo, el acento.
- `full`: blur, sombras y animaciones. `lite`: plano y con animaciones
  mínimas, para 2-4 GB.

Astal solo existe en el AUR (paquetes `-git`); la ISO lo trae ya compilado
en su repositorio local, así que la barra funciona desde el primer arranque.

## XFCE temático

El único entorno validado en hardware real. Panel, xfwm4, terminal,
greeter de LightDM y el overlay de acento GTK — todo con marca Static Forge
(tipografías Outfit/Space Grotesk/JetBrains Mono, acento configurable).

## Openbox minimal

Nivel 512 MB. Sin `lxsession` (un demonio menos residente), sin compositor
por defecto (`picom` está listado pero no se arranca —
`>500 MB de RAM en reposo = bug de diseño`, docs/PROYECTO.md). tint2 + jgmenu en
vez de un panel completo.

## KDE Plasma

Plasma 6 completo (Wayland), con Breeze oscuro, iconos Papirus, las fuentes de
la marca y el acento de Static Linux aplicado en el primer inicio de sesión
(fondo + color de acento con las herramientas de Plasma). Es el entorno más
pesado (~700-900 MB en reposo), por eso `sl-detect` nunca lo recomienda: está
para quien quiera un escritorio completo y familiar.

## GNOME

GNOME de serie (Wayland) con GDM, que el instalador prefiere cuando está
instalado (la pantalla de bloqueo de GNOME lo necesita). El tema pone modo
claro u oscuro, el acento de GNOME más parecido al del tema, fuentes,
iconos Papirus y fondo.

## Cinnamon

El escritorio clásico: barra abajo y menú de inicio. Además de lo que recibe
GNOME, `sl-theme` genera un tema de panel (`~/.local/share/themes/StaticLinux/cinnamon`)
recoloreando el de serie con la paleta del tema.

## i3, bspwm y sway (mosaico)

Tres gestores de ventanas en mosaico para quien vive en el teclado. Los tres
arrancan con **Super + Intro** (terminal), **Super + Espacio** o **Super + D** (rofi)
y **Super + Q** (cerrar ventana); el resto de atajos está en su
`config` (en sxhkd para bspwm). Barra: i3bar + i3status en i3, polybar en
bspwm, waybar en sway. Tus cambios van en `config.d/` (i3 y sway), que se
carga al final y no se sobrescribe.

## Capturas de pantalla

En todos los entornos, **Super + Shift + S** selecciona una zona de la pantalla
y la guarda en `Imágenes/Capturas` *y* la copia al portapapeles, sin menús —
como en Windows. Lo hace `sl-screenshot`, que usa la herramienta de cada
sesión (maim en X11, grim en Hyprland, Spectacle en KDE).

## Cualquier pantalla

Static Linux se adapta a la pantalla en la que se instala, de 800×600 a 4K:

- El instalador ocupa toda la pantalla y se escala según la densidad real del
  monitor (`sl-display-scale`: píxeles entre el tamaño físico que informa la
  pantalla) — 1×, 1,25×, 1,5× o 2×.
- Ese valor pasa al sistema instalado (`/etc/static-linux/display-scale`): el
  login lo aplica desde el primer arranque, y XFCE/Openbox en el primer inicio
  de sesión. Hyprland y KDE escalan solos por monitor.
- Los fondos son 4K y se recortan a cualquier proporción; las ventanas propias
  (`sl-welcome`, la guía de Hyprland) se encogen en pantallas pequeñas.

## Temas en todos los entornos

`sl-theme` pinta los nueve escritorios con el mismo tema: ver
[Temas y estilos](temas.md) para lo que recibe cada uno. Lo que **no**
cubre todavía:

- Los **estilos** (minimal, aero, ventanas, estante) solo cambian la forma de
  XFCE; los demás escritorios cogen la paleta y el fondo.
- En Cinnamon, los botones de bloquear y cerrar sesión del menú siguen
  oscuros con temas claros.
