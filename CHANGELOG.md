# Cambios

Notas de desarrollo de Static Linux. Las versiones largas, con capturas, están
en el blog: [staticforge.me/linux/blog](https://staticforge.me/linux/blog/).
La ISO se descarga desde [staticforge.me/linux/descargar](https://staticforge.me/linux/descargar/).

## 2026.11.14.2 · Los temas, vistos en los nueve escritorios

### Arreglos
- **Cambiar de tema fallaba** en cuanto había instalado i3, sway, bspwm,
  waybar, rofi o mako (Hyprland incluido): el paquete `staticlinux-base` no
  instalaba las plantillas `tiling/` y `sl-theme` se paraba con
  `FileNotFoundError`. Afectaba a la ISO 2026.11.14.1; llega con
  `pacman -Syu`.
- GNOME: con un tema claro, Console seguía oscura (su valor por defecto es
  `night` e ignora `color-scheme`) y el texto de fastfetch no se leía.
  `sl-theme` la pone en `auto`.

### Nuevo
- **81 capturas**: los 9 temas en los 9 escritorios (XFCE, KDE Plasma,
  GNOME, Cinnamon, Hyprland, Sway, i3, bspwm y Openbox), hechas en la VM con
  cada tema aplicado y la sesión reiniciada.
  - sl-welcome enseña la del escritorio en el que estás
    (`themes/<tema>/previews/<escritorio>.jpg`; si no la hay, la de XFCE).
  - La galería de la web tiene selector de escritorio.
  - Las tarjetas del instalador siguen siendo las de XFCE: la página de
    tema de Calamares es estática y no sabe qué escritorio has elegido.

## 2026.11.14.1 · XFCE por debajo de 650 MB

### Arreglos
- **XFCE en reposo: de ~705 a ~635 MB** (VM, perfil Mejorado; ~617 MB con
  Básico), por debajo de la regla de 650 MB:
  - los plugins del panel (menú, bandeja, volumen, estante, genmon) se cargan
    dentro de `xfce4-panel` en vez de un `wrapper-2.0` por plugin (~30 MB).
    Un hook de pacman de `staticlinux-base` lo mantiene tras cada
    actualización; llega con `pacman -Syu`.
  - `sl-welcome --autostart` arrancaba GTK4/libadwaita en cada inicio de
    sesión solo para cerrarse, y eso despertaba `xdg-desktop-portal` (con
    sus backends GTK y XApp, ~20 MB) para toda la sesión. Ahora sale antes
    de cargar GTK.
- Las etiquetas de los iconos del escritorio llevan un halo del color de
  fondo del tema: en Aero, "Papelera" se perdía sobre las palmeras.
- Al cambiar de tema, Thunar (que se queda residente) se cerraba con los
  colores del tema anterior hasta reiniciar sesión: `sl-theme` lo reinicia.
- Vistas previas nuevas de Aero y Nube con sus fondos nuevos, en el
  instalador, sl-welcome y la web.

### Nuevo
- Tercer espejo: **archive.org**, con torrent (`iso/release.sh archive`).
- `sudo SL_ISO_VERSION=2026.11.14.1 iso/build.sh universal`: una segunda
  ISO el mismo día sin pisar el nombre de la primera.

## 2026.11.14 · La primera ISO pública de prueba

### Nuevo
- **ISO universal** (`sudo iso/build.sh universal`, ~4,8 GB): sustituye a la
  "offline" a medias. Lleva dentro el sistema base, los diez escritorios, los
  tres kernels y las herramientas de privacidad (1.300 paquetes, 2,6 GB, en
  `/opt/staticlinux-offline`), así que **instala sin conexión**. Con red,
  pone el sistema al día (`pacman -Syu`) antes de añadir los sabores; sin
  ella, los sabores quedan pendientes para `sudo sl-ctl flavor add pending`.
  La ISO online (~2 GB) sigue existiendo.
- **Fondos nuevos para Aero y Nube**, a partir de fotos libres de Wikimedia
  Commons (laguna de Malapascua, CC BY 4.0, con burbujas de cristal encima;
  colinas de Palouse, CC BY 2.0), a 3840×2160
  (`branding/themes/photo_wallpaper.py`; autoría en cada `CREDITS`).
- **Repositorio propio firmado, `[staticlinux]`** ([wiki](docs/wiki/repositorio.md)):
  staticlinux-base, Brave Origin, paru, Astal y las fuentes llegan con un
  `pacman -Syu`, sin ISO nueva. Todo firmado con la **clave de Static
  Forge** (`3E61 7ED0 6C90 C757 35C9  C45E 51D5 8FA3 5045 B8D0`), que va en
  el nuevo paquete `staticlinux-keyring`; el instalador añade el repositorio
  con `SigLevel = Required`. `packages/publish-repo.sh` firma y lo sube.
- **Instantáneas antes de cada actualización** en BTRFS: el instalador
  configura Snapper para `/` (10 como máximo, sin las horarias), `snap-pac`
  hace una antes y otra después de cada operación de pacman y `grub-btrfsd`
  las pone en el menú de GRUB. `sl-ctl snapshot --rollback <n>` devuelve los
  archivos a esa instantánea (`snapper undochange`).
- **`sl-ctl flavor add/remove <sabor>`**: los sabores se añaden o quitan
  después de instalar, con las mismas listas y ajustes que el instalador;
  `remove` no toca lo que otro sabor, el escritorio o la base necesitan.
- **`sl-ctl audit`**: qué escucha fuera, qué conexiones hay abiertas y de
  qué proceso, si el DNS va cifrado, ufw y temporizadores.
- `sl-ctl privacy --profile` instala también las herramientas del perfil
  (firejail, usbguard, tor…), no solo su configuración.
- **Vistas previas reales en el instalador**: cada escritorio de la página
  de entornos enseña una captura de verdad (tema Ámbar, terminal y gestor de
  archivos) en lugar del dibujo genérico.
- **Sin entorno gráfico** y **Servidor / Homelab** en la página de
  escritorio: arrancan a la consola, sin servidor gráfico, navegador ni audio
  (tmux, btop, fuente Terminus a la medida de la pantalla). Servidor añade
  el sabor Servidor ([wiki](docs/wiki/servidor.md)).
- **`sl-ctl server`**: estado de los servicios del servidor y de lo que
  escucha en la red; `server on/off <servicio>` los activa o apaga y abre o
  cierra su puerto en ufw (ssh, cockpit, docker, nginx, mariadb, fail2ban,
  wireguard).
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

### Arreglos
- **DNS cifrado con una lista corta de servidores**: dnscrypt-proxy sondeaba
  unos 170 resolvers públicos en cada arranque (algunos, servidores caseros)
  y podía usar cualquiera. Ahora solo Quad9 (sin filtro), Mullvad y
  dnscry.pt (Madrid, París, Fráncfort, Ámsterdam). Visto en la auditoría de
  tráfico.
- **NetworkManager ya no pregunta a `ping.archlinux.org`** cada 5 minutos
  (HTTP en claro: tu IP y que usas Arch). Solo se pierde la página automática
  de los wifis de hotel.
- El perfil **Máximo** prometía `linux-hardened` y no lo instalaba, y
  ningún perfil instalaba sus herramientas (firejail, usbguard, tor…) desde
  el instalador: ahora sí. Y, una vez instalado, GRUB arrancaba igualmente
  `linux-lts` (va primero el de versión más alta): el instalador fija
  `GRUB_TOP_LEVEL` al kernel elegido.
- **AppArmor no se cargaba** en los perfiles Mejorado y Máximo: se
  activaba el servicio, pero nadie ponía AppArmor en la línea de arranque
  del kernel (los de Arch no lo cargan si no se pide). Ahora el perfil añade
  `lsm=…,apparmor,bpf` a GRUB, y Básico lo quita.
- XFCE arrancaba blueman-applet (~40 MB de RAM) también en equipos sin
  Bluetooth; ahora solo si hay un adaptador.
- El instalador decía "2026.10": ahora enseña la fecha de la ISO. Y el botón
  del diálogo de confirmación ya no sale como "%Regresar" (errata de la
  traducción de Calamares, corregida en nuestro paquete).
- La regla de diseño de RAM pasa de 500 a **650 MB en reposo**, para tener
  margen.
- La barra de Hyprland (Astal) no aparecía en equipos sin Wi-Fi: el icono
  de red anidaba dos `<With>` y gnim tumbaba la barra entera. Visto al
  sacar las vistas previas en la VM (solo cable).
- El aviso de cerrar sesión de i3, sway y bspwm (`Super+Mayús+E`) sale ya en
  el idioma del sistema: lo muestra el nuevo `sl-logout` (swaynag, i3-nagbar
  o rofi según la sesión).
- `sl-ctl server` decía "ufw desactivado" sin `sudo` aunque el cortafuegos
  estuviera activo (`ufw status` necesita root); ahora lee `ufw.conf` y el
  servicio. Visto al instalar Servidor / Homelab desde la ISO.
- `packages/local-repo.sh`: si un paquete AUR -git deja de compilar, conserva
  el último que funcionaba en vez de borrarlo antes de probar.

### Probado
- **Instalación sin conexión desde la ISO universal** (VM sin red,
  2026-11-14): KDE Plasma + tema Nube + privacidad Máxima + sabor Oficina en
  unos 7 minutos. Arranca `linux-hardened` con AppArmor en la línea del
  kernel, entra solo en KDE, y el sabor Oficina queda pendiente
  (`sl-ctl flavor list` lo marca) para cuando haya red. La caché de pacman
  del sistema instalado queda vacía (88 KB).
- **XFCE + btrfs + privacidad Mejorada** (VM, 2026-11-14): AppArmor con 80
  perfiles en enforce, Snapper con instantáneas antes y después de cada
  pacman, `grub-btrfsd` activo, `[staticlinux]` con su clave. Tráfico
  capturado en reposo: solo Quad9/dnscry.pt cifrado y NTP.
- **Servidor / Homelab instalado desde la ISO** (VM, 2026-11-14): arranca a
  consola (`multi-user.target`) con Terminus, sin Xorg, Brave ni GTK; nada
  escuchando salvo dnscrypt-proxy en localhost; **391 MB de RAM en reposo**,
  499 paquetes, 7,7 GB en disco. `sudo sl-ctl server on ssh` enciende sshd
  y abre el 22 en ufw, y responde desde fuera.
- **XFCE + sabor Gaming instalado desde la ISO** (VM, 2026-11-14): Steam,
  Lutris, GameMode, MangoHud, Prism, Heroic y Modrinth (flatpak); swapfile de
  2 GB (la VM tiene 3,9 GB) junto a zram; `scx_loader` arranca con lavd en
  modo Auto y `sl-game` lo pasa a Gaming y lo devuelve al salir el juego.
- `sl-game` pedía la contraseña (polkit) para cambiar el modo de lavd en
  mitad del arranque del juego. Nueva regla
  `50-static-linux-scx.rules`: sin contraseña para `wheel` con sesión local
  activa.

### Problemas conocidos
- El perfil `performance` de `sl-game` no se ha visto en acción: en una VM
  power-profiles-daemon solo ofrece `balanced` y `power-saver`. Falta
  probarlo en hardware real.
- XFCE con una terminal abierta usa ~750 MB de RAM en reposo (la regla es
  650 MB). Hay que recortar applets que arrancan aunque no hagan falta
  (blueman sin Bluetooth, por ejemplo). *Arreglado después: ~635 MB.*

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
