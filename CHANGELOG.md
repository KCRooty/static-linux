# Cambios

Notas de desarrollo de Static Linux. Las versiones largas, con capturas, están
en el blog: [staticforge.me/linux/blog](https://staticforge.me/linux/blog/).
Aún no hay ISO pública: todo se construye desde este repositorio.

## Sin publicar · 18 idiomas, y rendimiento de serie

### Nuevo
- **Static Linux en 18 idiomas**: español (el original), inglés, catalán,
  euskera, gallego, francés, alemán, italiano, portugués, portugués de
  Brasil, neerlandés, polaco, ruso, ucraniano, turco, japonés, coreano y
  chino simplificado. Se traducen el instalador (páginas, presentación y
  pasos), sl-welcome, sl-quick, la guía de atajos de Hyprland, las capturas,
  la barra de Hyprland, `sl-ctl`, `sl-game`, temas, catálogo, lanzadores, la
  pantalla de bloqueo y la contraseña del disco al arrancar. Sin traducción,
  inglés. Todo con gettext, en `i18n/` ([wiki](docs/wiki/idiomas.md)).
- **Rendimiento y estabilidad de serie**, a partir de la guía de gaming de
  CachyOS (`rendimiento/`, [wiki](docs/wiki/rendimiento.md)):
  - zram por fin activo: la mitad de la RAM (8 GB como mucho), zstd y
    ajustes de memoria pensados para ella. Con menos de 4 GB de RAM se añade
    un swapfile de 2 GB por debajo (salvo en btrfs).
  - Planificador de disco según el tipo (NVMe, SSD, disco duro), escritura a
    disco en bloques pequeños para que una copia grande no congele el
    escritorio, red con BBR, sin watchdogs y sin frenar los split locks.
  - earlyoom activo y configurado: cierra lo más grande antes de que el
    escritorio se congele, nunca la sesión ni el audio.
  - journal limitado a 256 MB, caché de paquetes que se limpia sola
    (`paccache.timer`), caché de shaders de 12 GB y makepkg con todos los
    núcleos.
  - power-profiles-daemon en `base.list`.
  - **Sabor Gaming:** planificador de CPU `scx_lavd` (sched_ext) desde el
    primer arranque, y **`sl-game %command%`** en Steam pone la máquina en
    `performance` (y lavd en modo Gaming) solo mientras el juego está
    abierto.
- **`sl-ctl perf`**: estado del rendimiento, `perf profile` (perfil de
  energía) y `perf scheduler` (planificador de CPU u `off`). `sl-ctl` habla
  ya el idioma del sistema.
- Nuevos tweaks reversibles `split-lock` y `watchdog`, para deshacer esos dos
  ajustes.

### Cambios
- Quitados los tweaks `swappiness-10` (iba en contra de zram) y `hdd-bfq`
  (ya va de serie para cada tipo de disco).
- Texto del perfil de privacidad básico más claro, también en la wiki.

### Problemas conocidos
- Las alertas de i3 y sway siguen en español.
- Probado en una VM instalando el paquete (zram, sysctl, earlyoom, perfiles,
  lavd con `sl-game`); falta una instalación completa desde la ISO con el
  sabor Gaming.

## 2026-11-13 · Los temas, en todos los escritorios y en el arranque

### Nuevo
- **Estilo `estante` y tema Nube.** Un escritorio de lanzador y estante en
  XFCE: barra abajo de 48 px con un lanzador redondo (búsqueda arriba y apps
  en cuadrícula), las apps fijadas y abiertas al centro
  (`xfce4-docklike-plugin`) y una píldora con la hora que abre **sl-quick**,
  los ajustes rápidos: cerrar sesión, apagar, bloquear, ajustes, Wi‑Fi,
  Bluetooth, No molestar, Luz nocturna, captura, volumen, brillo y batería.
  Ventanas planas con esquinas de 12 px. Nube es el primer tema que lo usa:
  claro, Roboto, fondo de nubes dibujado por código. `xfce.list` suma
  `xfce4-docklike-plugin` y `ttf-roboto`.
- Con `estante`, el escritorio también se comporta como el estilo: avisos
  abajo a la derecha, escritorio sin iconos y **Alt+[ / Alt+]** para ajustar
  la ventana a la mitad izquierda o derecha (**Alt+=** maximiza). Al cambiar
  a otro estilo se quitan y vuelven los valores de XFCE. Los ajustes rápidos
  tienen esquinas redondeadas cuando hay compositor.
- **KDE Plasma, Hyprland y Openbox siguen el tema.** `sl-theme` escribe cada
  pieza solo si su programa está instalado (columna nueva en
  `templates/MANIFEST`): esquema de color y Konsole en Plasma; bordes,
  hyprpaper, hyprlock y barra en Hyprland; tema de ventanas, tint2, jgmenu,
  dunst, LXTerminal y fondo en Openbox. Los `install.sh` de esos entornos ya
  no usan los acentos viejos.
- **Cinco escritorios nuevos en el instalador: GNOME, Cinnamon, i3, bspwm y
  sway**, cada uno con su lista de paquetes, su `install.sh` (lógica común en
  `entornos/common/deploy.sh`) y su tarjeta. Los 9 temas también llegan a
  ellos: en GNOME y Cinnamon, modo claro/oscuro, acento, tipografías y fondo
  por gsettings (también en `/etc/skel`, vía dconf); en Cinnamon, además, un
  tema de panel propio generado desde la paleta. En i3, sway y bspwm, colores
  de bordes, barra (i3bar, waybar o polybar), rofi, mako y fondo, con
  plantillas nuevas en `templates/tiling/`. Se recargan sin cerrar sesión.
  GNOME trae GDM y el instalador lo prefiere cuando está.
- Hyprland: si hyprpaper falla (pasa en máquinas virtuales sin GPU), el fondo
  lo pone swaybg.
- **Arranque e inicio de sesión con el tema:** `sl-theme <id> --system` pinta
  LightDM (o el fondo de SDDM), el menú de GRUB y una pantalla de Plymouth
  propia con la petición de contraseña de LUKS. El instalador lo ejecuta
  antes de generar el initramfs, y `sudo sl-ctl theme` lo repite al cambiar
  de tema. `base.list` suma `plymouth`.
- Con la sesión abierta, Openbox, tint2, dunst, Hyprland y Plasma recargan
  el tema sin cerrar sesión.
- **Sesión en vivo con escritorio.** La ISO arranca en XFCE con el tema Ámbar
  y en español; el instalador se abre solo encima y, si lo cierras, vuelve
  desde el menú con **Instalar Static Linux**. El tema y el idioma se generan
  al construir la ISO, así que el arranque no espera.
- La cabecera de sl-welcome usa los colores del tema activo.

### Arreglos
- **Temas probados en Openbox, KDE Plasma y Hyprland** (VM, 2026-11-13): fondo,
  paleta de ventanas, barra y apps siguen al tema, también al cambiarlo en
  vivo. Arreglos que salieron:
  - Hyprland 0.57 ya no conoce `misc.vfr`: la config daba error al entrar.
  - hyprpaper revienta en GPUs virtuales o por software: si falla, el fondo
    lo pone `swaybg` (nuevo en las listas de Hyprland). `theme.lua` lleva
    ahora la ruta del fondo.
  - Al cambiar de tema en vivo, `sl-theme` no encontraba la sesión de
    Hyprland (el compositor no exporta `HYPRLAND_INSTANCE_SIGNATURE` ni
    `WAYLAND_DISPLAY` a sí mismo): ahora los saca de `$XDG_RUNTIME_DIR`.
  - Las apps libadwaita (Nautilus, Loupe…) se quedaban siempre claras:
    `sl-theme` escribe `org.gnome.desktop.interface` (modo claro/oscuro,
    tema GTK, iconos, fuentes) en la sesión o, sin sesión, directamente en
    `~/.config/dconf/user` (también con `--skel`). Las ventanas ya abiertas
    lo cogen al reabrirlas.
- **El tema elegido en el instalador ya se ve en el usuario nuevo.** El skel
  trae `xsettings.xml` y `xfwm4.xml` con Adwaita-dark y la decoración vieja,
  y `sl-theme` solo los cambiaba con `xfconf-query`, que en el chroot del
  instalador no existe: un tema claro como Nube salía con GTK oscuro y sin
  sus ventanas. Ahora escribe esas claves (tema GTK, iconos, fuentes,
  decoración y botones) también en los ficheros. Probado instalando la ISO
  del 2026-11-13 en QEMU con Nube.
- kitty no cargaba los colores del tema: faltaba el `include` en
  `kitty.conf`.
- LXTerminal ignoraba su paleta (faltaba `color_preset=Custom`).
- El menú de GRUB decía "Static Linux Linux".
- La barra de Hyprland usaba colores (`@sl_bg`, `@sl_text`) que el tema no
  definía.
- XFCE podía arrancar con su fondo de serie: el script que pone el fondo del
  tema corría antes de que el escritorio estuviera listo. Ahora lo espera.

### Problemas conocidos
- Los estilos (`minimal`, `aero`, `ventanas`, `estante`) solo dan forma a
  XFCE; el resto de escritorios coge la paleta y el fondo del tema.
- sway arranca con el teclado en español fijo (`config` de sway).
- En Cinnamon, los botones de bloquear y cerrar sesión del menú siguen
  oscuros con temas claros.
- GNOME, Cinnamon, i3, bspwm y sway aún no se han probado en una instalación
  completa desde la ISO, solo instalando los paquetes en una VM.

## 2026-11-12 · Temas, estilos y el código, abierto

### Nuevo
- **Temas = fondo + paleta.** Ocho temas: Ámbar (por defecto), Papel, Nórdico,
  Bosque, Sakura, Violeta, Aero y Ventanas. `branding/themes/<id>/theme.conf`.
- **`sl-theme`**: un solo motor para GTK 3/4, xfwm4 (dibujado con antialias),
  iconos Papirus con carpetas del color del tema, xsettings, panel de XFCE,
  xfce4-terminal, kitty, fastfetch, cava y fondo. Backup de todo lo que toca.
- **Tres estilos**: `minimal`, `aero` (brillo, botones cápsula, barra abajo) y
  `ventanas` (plana, botones de 46 px, apps centradas). El panel se reconstruye
  en caliente al cambiar de estilo.
- **Instalador**: página **Tema** con capturas reales; el job `tema-apply`
  aplica el tema al usuario y a `/etc/skel` y escribe `/etc/static-linux/theme`.
- **sl-welcome**: Apariencia es un selector de temas; el catálogo estrena la
  sección **Static Forge** con KC Downloader 3.0.1 (`packages/sf/`).
- **`sl-ctl theme`** para listar y aplicar temas.
- `staticlinux-base` instala los temas y `/usr/bin/sl-theme`; `base.list` suma
  adw-gtk-theme, papirus-icon-theme, inter-font, noto-fonts y cava.
- Código público con la historia completa; la wiki se publica en
  [staticforge.me/static-linux](https://staticforge.me/static-linux/).

### Arreglos
- DNS cifrado: las consultas no pasaban por dnscrypt-proxy. Ahora sí, desde el
  primer arranque.
- Las copias de seguridad de `sl-theme` creadas como root ahora son del usuario
  (antes impedían cambiar de tema después).
- `iso/build.sh` limpia `/etc/calamares` antes de copiar (quedaban módulos viejos).

### Problemas conocidos
- Los temas solo cubren XFCE. KDE, Hyprland y Openbox usan aún los acentos.
- LightDM, Plymouth y GRUB no siguen el tema.
- Las apps abiertas cambian de aspecto al reabrirlas.
- La sesión en vivo no tiene escritorio: abre directamente el instalador.
- El fondo de Violeta es provisional.

## 2026-10-23 · Instalador pulido, KDE Plasma y Hyprland 0.56
- KDE Plasma como entorno elegible; Hyprland actualizado a la sintaxis de 0.56.
- Instalador en español, a pantalla completa y con escalado HiDPI.
- Brave Origin preinstalado, tecla Super para el menú, códecs multimedia.
- Fondos 4K; páginas de estilo, sabores y catálogo en el instalador.
- Arreglos de la primera instalación completa.

## 2026-10-11 · La primera ISO que instala de principio a fin
- `iso/build.sh` construye una ISO de 1,7 GB que arranca en UEFI e instala en
  QEMU/KVM: ext4, XFCE, perfil de privacidad básico, GRUB, LightDM y sl-welcome.

## 2026-09-21 · Bienvenida, instalador y más entornos
- sl-welcome (GTK4/libadwaita), secuencia completa de Calamares, Openbox e
  Hyprland+Astal, el paquete `staticlinux-base` y la wiki en MkDocs.

## 2026-09-10 · Arranca Static Linux
- `sl-detect` (hardware → entorno, sistema de archivos y kernel), XFCE con tema
  propio y diez acentos de color.
