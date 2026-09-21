# Branding y sistema de acentos

## Identidad

```
Void:         #0B0C10  (fondo principal)
Signal Green: #00C8A0  (acento primario de marca)
Amber:        #F5A623  (ISO offline, avisos)
Blanco:       #FFFFFF  (texto sobre fondo oscuro)
```

Tipografías (todas SIL OFL): **Outfit 700** para titulares/GRUB/SDDM,
**Space Grotesk 400** para UI y cuerpo de texto, **JetBrains Mono** para
terminal, código y `sl-ctl`.

## Los 10 acentos

`branding/accents/palette.conf` — morado es el acento por defecto de marca,
pero el usuario puede elegir cualquiera de los diez (incluye dos modos de
alto contraste):

morado · amarillo · rojo · verde · azul · rosa · gris · monocromo ·
alto contraste oscuro · alto contraste claro

## Un solo sistema, todo lo toca

`branding/accents/apply.sh <acento>` es el único camino de theming del
sistema. Renderiza plantillas (`templates/*.in`) con los valores de
`palette.conf` y toca:

- fastfetch (`/etc/fastfetch/config.jsonc`, requiere root)
- GTK 3/4 (`~/.config/gtk-*/gtk.css`) — define los colores con nombre de
  libadwaita (`accent_color`, `theme_selected_bg_color`...), por eso
  cualquier app GTK4/libadwaita (incluido [`sl-welcome`](herramientas/sl-welcome.md)
  y la barra de Astal en Hyprland) hereda el acento gratis
- Borde de ventana xfwm4 (tema `Static-Void`)
- Colores de `xfce4-terminal`
- Greeter de LightDM (requiere root)
- Fondo de pantalla (genera uno por acento si no existe, con
  `branding/wallpapers/gen-wallpaper.py`)

Todo con backup automático en `/var/backups/static-linux/accent/` antes de
tocar nada.

```bash
branding/accents/apply.sh --list              # ver los acentos disponibles
branding/accents/apply.sh purple               # aplicar al usuario actual
sudo branding/accents/apply.sh green --skel    # aplicar a /etc/skel (build de ISO)
```

## Huecos conocidos

Ni Openbox (borde de `rc.xml`) ni Hyprland (`col.active_border` en
`hyprland.conf`) siguen el acento todavía — ver
[Entornos § theming compartido](entornos.md#theming-compartido-con-huecos-conocidos).
