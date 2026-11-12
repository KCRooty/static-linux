# Temas y estilos

Un **tema** es un fondo de pantalla y la paleta que sale de él. Un **estilo**
es la forma del escritorio: ventanas, barra y controles. Cada tema trae su
estilo; `sl-theme` lo pinta todo a la vez. La dirección visual completa está
en [`DESIGN.md`](https://github.com/KCRooty/static-linux/blob/main/DESIGN.md).

!!! note "Estado (2026-11-12)"
    Los temas funcionan en **XFCE** de punta a punta: instalador, sistema
    instalado, sl-welcome y `sl-ctl theme`. KDE, Hyprland y Openbox, la
    pantalla de inicio de sesión, Plymouth y GRUB todavía no siguen el tema.

## Los ocho temas

| | Tema | Modo | Estilo | Acento | Fondo |
|---|---|---|---|---|---|
| ![Ámbar](img/temas/ambar.webp){ width=160 } | **Ámbar** (por defecto) | oscuro | minimal | `#E0A84F` | Hokusai, «Tormenta bajo el Fuji» (CC0) |
| ![Papel](img/temas/papel.webp){ width=160 } | **Papel** | claro | minimal | `#666211` | Hokusai, «Fujimigahara en Owari» (CC0) |
| ![Nórdico](img/temas/nordico.webp){ width=160 } | **Nórdico** | oscuro | minimal | `#88C0D0` | Hiroshige, «Nieve al anochecer en Kanbara» (dominio público) |
| ![Bosque](img/temas/bosque.webp){ width=160 } | **Bosque** | oscuro | minimal | `#9BC4A0` | Hiroshige, «Lluvia de primavera en Tsuchiyama» (CC0) |
| ![Sakura](img/temas/sakura.webp){ width=160 } | **Sakura** | oscuro | minimal | `#F2A7BC` | Hokusai, «El Fuji desde Gotenyama» (CC0) |
| ![Violeta](img/temas/violeta.webp){ width=160 } | **Violeta** | oscuro | minimal | `#8F86F2` | provisional, dibujado por código (GPL-3.0) |
| ![Aero](img/temas/aero.webp){ width=160 } | **Aero** | claro | aero | `#1667A8` | original, dibujado por código (GPL-3.0) |
| ![Ventanas](img/temas/ventanas.webp){ width=160 } | **Ventanas** | oscuro | ventanas | `#4CC2FF` | original, dibujado por código (GPL-3.0) |

Cada fondo lleva autor, licencia y cambios en `branding/themes/<id>/CREDITS`.
Los escaneos son de The Metropolitan Museum of Art (Open Access).

## Los tres estilos

| Estilo | Ventanas | Barra | Fuente |
|---|---|---|---|
| **minimal** | borde de 2 px, botones como tres puntos | arriba, 30 px, escritorios como puntos y reloj al centro | Space Grotesk |
| **aero** | barra de título con brillo, botones cápsula, cerrar en rojo | abajo, 40 px con brillo; reloj con fecha y "mostrar escritorio" | Noto Sans |
| **ventanas** | plana, botones de 46 px ─ □ ✕ | abajo, 48 px, apps al centro, la activa subrayada | Inter |

<div class="grid" markdown>
![Aero](img/temas/aero.webp)
![Ventanas](img/temas/ventanas.webp)
</div>

El brillo de aero son degradados sobre color sólido: ningún estilo usa
transparencia. La barra solo se reescribe cuando **cambia el estilo**; un
cambio de paleta dentro del mismo estilo respeta los retoques que hayas hecho
en tu panel.

## Dónde se elige

- **Instalador:** página **Tema**, con capturas reales de los ocho.
- **sl-welcome:** pestaña **Apariencia**.
- **Terminal:**

```bash
sl-ctl theme --list        # temas y cuál está activo
sl-ctl theme aero          # aplicar al usuario actual
sl-theme --current         # id del tema activo
sudo sl-theme ambar --skel # pintar /etc/skel (build de la ISO)
```

## Qué toca `sl-theme`

Todo sale de `branding/themes/<id>/theme.conf` y de las plantillas de
`branding/themes/templates/` (la lista exacta está en `templates/MANIFEST`):

- GTK 3 y 4 (`~/.config/gtk-{3,4}.0/gtk.css`) sobre adw-gtk3: las apps
  libadwaita, sl-welcome incluida, heredan la paleta.
- Tema de ventanas xfwm4 `StaticLinux`, dibujado píxel a píxel con antialias
  por `xfwm4.py` según el estilo.
- Iconos Papirus con carpetas del color del tema (`icons.py`).
- xsettings (tema, fuente, iconos, botones de ventana) y el panel de XFCE.
- Terminal (xfce4-terminal y kitty), fastfetch y cava.
- El fondo de pantalla.

Tus reglas propias van en `~/.config/gtk-{3,4}.0/gtk-custom.css`, que
`sl-theme` crea vacío y nunca sobrescribe. Todo lo que sobrescribe se copia
antes a `~/.local/state/static-linux/theme-backup/<fecha>/`.

Al cambiar de estilo con la sesión abierta, el panel se reconstruye en
caliente. Las apps que ya estaban abiertas cambian al reabrirlas.

## Hacer un tema

```ini
# branding/themes/<id>/theme.conf
name=Mi tema
mode=dark            # dark | light
style=minimal        # minimal | aero | ventanas (opcional, minimal si falta)
font_ui=Inter        # opcional, Space Grotesk si falta
folders=yellow       # opcional, color de carpetas de Papirus
bg=262321            # fondo de ventana
surface=302C29       # campos, terminal, filas
line=4A443F          # bordes
text=EBDDBF
text_dim=BFB29A
accent=E0A84F
accent_fg=262321     # texto sobre el acento
danger=EB6F68
warning=D8A657
term=...             # 8 colores de terminal
term_bright=...      # 8 colores brillantes
```

Al lado, `wallpaper.jpg` (3840×2160), `preview.jpg` (320×180) y `CREDITS`.
`branding/themes/check.py` comprueba el contraste AA de texto y terminal: un
tema que falla no entra en la ISO. Los fondos originales se generan con
`branding/themes/gen_wallpaper.py`.

## Identidad de marca

```
Void:         #0B0C10  (fondo principal)
Signal Green: #00C8A0  (acento de marca)
Amber:        #F5A623  (ISO offline, avisos)
```

Tipografías (SIL OFL): **Outfit 700** para titulares, GRUB y logotipo;
**Space Grotesk** para interfaz; **JetBrains Mono** para terminal y código.

## Los acentos de antes

`branding/accents/apply.sh` y sus diez acentos siguen en el repo: el
instalador los usa como capa base para fastfetch y el greeter de LightDM
antes de aplicar el tema, y Openbox e Hyprland todavía dependen de ellos.
Se retirarán cuando los temas lleguen a esos entornos.
