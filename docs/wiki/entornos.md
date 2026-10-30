# Entornos de escritorio

`sl-detect` recomienda uno de los cuatro según el hardware — ver
[Requisitos de hardware](hardware/requisitos.md) para la tabla de
decisión completa. Cada uno vive en `entornos/<nombre>/`, con su propio
`install.sh --home|--skel` idempotente (con backup automático).

| Entorno | RAM | Display | Estado |
|---|---|---|---|
| [`hyprland-astal-full`](https://github.com/KCRooty/static-linux/tree/main/entornos/hyprland-astal-full) | ≥ 4 GB | Wayland | Escrito, sin probar en hardware real |
| [`hyprland-astal-lite`](https://github.com/KCRooty/static-linux/tree/main/entornos/hyprland-astal-lite) | 2-4 GB | Wayland | Escrito, sin probar en hardware real |
| [`xfce-themed`](https://github.com/KCRooty/static-linux/tree/main/entornos/xfce-themed) | ≥ 1 GB | Xorg | **Validado en el iMedia S2883** |
| [`openbox-minimal`](https://github.com/KCRooty/static-linux/tree/main/entornos/openbox-minimal) | ≥ 512 MB | Xorg | Escrito, sin probar en hardware real |

`xfce-themed` es el único que se ha visto arrancar en una máquina real hasta
ahora — ver la [referencia del iMedia S2883](hardware/imedia-s2883.md).

## Hyprland + Astal (full / lite)

Compositor Hyprland, shell propio en `~/.config/ags/` con
[Astal](https://aylur.github.io/astal/) (TypeScript, GTK4) — una barra con
workspaces, título de la ventana activa y reloj. La barra lee los mismos
colores con nombre que `branding/accents/apply.sh` escribe para GTK, así que
sigue el acento activo sin código adicional.

`full` lleva blur, sombras y animaciones completas (pensado para GPUs
Wayland-capables con ≥4 GB). `lite` es el mismo shell con esos efectos
apagados — mismo código de Astal, `hyprland.conf` más ligero.

## XFCE temático

El único entorno validado en hardware real. Panel, xfwm4, terminal,
greeter de LightDM y el overlay de acento GTK — todo con marca Static Forge
(tipografías Outfit/Space Grotesk/JetBrains Mono, acento configurable).

## Openbox minimal

Nivel 512 MB. Sin `lxsession` (un demonio menos residente), sin compositor
por defecto (`picom` está listado pero no se arranca —
`>500 MB de RAM en reposo = bug de diseño`, AGENTS.md). tint2 + jgmenu en
vez de un panel completo.

## Theming compartido, con huecos conocidos

`branding/accents/apply.sh` cubre fastfetch, GTK 3/4, la ventana de LightDM
y el fondo de pantalla en los cuatro entornos. Lo que **no** cubre todavía,
por entorno:

- **Openbox**: el borde de ventana de `rc.xml` no sigue el acento (tema fijo
  por ahora — necesitaría un tema Openbox propio con variantes por acento,
  como `xfwm4-themerc.in` para XFCE).
- **Hyprland/Astal**: la barra de Astal sí sigue el acento (lee el mismo
  `gtk.css`), pero el color de borde de `hyprland.conf` es fijo.

Ninguno de los dos es difícil de resolver — solo no estaba hecho todavía.
