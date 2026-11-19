# Mascota: Sae

Static Linux tiene mascota: **Sae**, una serpiente morada. Es la cara de
la distro.

`sae-boceto.png` es el boceto original de Core, dibujado con **Paint It!**
(`laboratorio/paint-it/` en la web) — morado sobre un poste marrón, lengua
roja bífida. `sae.png` es el mismo dibujo recortado y con el fondo blanco
hecho transparente (`convert -trim` + `-transparent white`), sin tocar el
trazo — es punto de partida, no arte final: el diseño de verdad (vector,
variantes de pose) lo hace Core cuando quiera.

### Dónde aparece ya
- **README.md** del repo, junto al logo.
- **sl-welcome** (`src/banner.py`): en la esquina de la cabecera, sobre las
  franjas del acento activo.
- **staticforge.me/linux** (hero, junto al `<h1>`) y copiada en
  `linux/img/sae.png` — ese repo tiene su propia copia, independiente de
  esta.
- Empaquetada por `staticlinux-base` en `/usr/share/static-linux/logo/sae.png`
  (`sl-welcome/src/paths.py:mascot_path()` la resuelve instalada o desde el
  checkout).

### Pendiente de decidir (de Core)
- Color: de momento es el morado que dibujó, sin tocar. Encaja con el morado
  de Shadow en DONNIES (`#7B61FF`) y con el tema **Violeta** de Static Linux
  — a decidir si se queda como un morado propio o se ata a uno de esos dos.
- Favicon de `/linux/`: se dejó la mónada SF (se lee mejor a 16 px; un
  dibujo con tanto detalle se emborrona de pequeño).
- GRUB / Plymouth: el boot splash actual usa la marca SF
  (`branding/logo/sf-static-forge.png`) por tema; meter a Sae ahí toca los
  9 temas, no se ha hecho.
- Variantes por tema/estilo, página de descarga, merch.
