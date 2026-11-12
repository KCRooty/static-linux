# Cambios

Notas de desarrollo de Static Linux. Las versiones largas, con capturas, están
en el blog: [staticforge.me/linux/blog](https://staticforge.me/linux/blog/).
Aún no hay ISO pública: todo se construye desde este repositorio.

## Sin publicar · Los temas, en todos los escritorios y en el arranque

### Nuevo
- **KDE Plasma, Hyprland y Openbox siguen el tema.** `sl-theme` escribe cada
  pieza solo si su programa está instalado (columna nueva en
  `templates/MANIFEST`): esquema de color y Konsole en Plasma; bordes,
  hyprpaper, hyprlock y barra en Hyprland; tema de ventanas, tint2, jgmenu,
  dunst, LXTerminal y fondo en Openbox. Los `install.sh` de esos entornos ya
  no usan los acentos viejos.
- **Arranque e inicio de sesión con el tema:** `sl-theme <id> --system` pinta
  LightDM (o el fondo de SDDM), el menú de GRUB y una pantalla de Plymouth
  propia con la petición de contraseña de LUKS. El instalador lo ejecuta
  antes de generar el initramfs, y `sudo sl-ctl theme` lo repite al cambiar
  de tema. `base.list` suma `plymouth`.
- Con la sesión abierta, Openbox, tint2, dunst, Hyprland y Plasma recargan
  el tema sin cerrar sesión.

### Arreglos
- kitty no cargaba los colores del tema: faltaba el `include` en
  `kitty.conf`.
- LXTerminal ignoraba su paleta (faltaba `color_preset=Custom`).
- El menú de GRUB decía "Static Linux Linux".
- La barra de Hyprland usaba colores (`@sl_bg`, `@sl_text`) que el tema no
  definía.

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
