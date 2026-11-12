# DESIGN.md · Static Linux

Dirección visual de Static Linux. Todo lo que dibuja el sistema (instalador, arranque, login,
escritorio, apps, sl-welcome, sl-ctl, wiki) sale de aquí. Si una decisión no está escrita en este
archivo, no está decidida.

Decidido por Core el 2026-11-12.

## 1. Idea

**El fondo manda.** Cada tema es una ilustración y una paleta sacada de ella; ventanas, barra,
terminal, apps, login y arranque se pintan con esa paleta. El sistema resulta llamativo por el
color y el dibujo, no por efectos: nada de cristal, brillos ni degradados de relleno.

Encima del fondo, todo es plano y sólido: ventanas con borde fino, una barra superior estrecha y
widgets de terminal (fastfetch, visualizador de audio, reloj) que decoran y además informan.

Lema de marca, se mantiene tal cual: **fast. private. yours.**

## 2. Diales (antislop)

Lectura: escritorio de sistema operativo para gente que instala su propia distro y quiere que se
vea suyo; lenguaje plano y gráfico sobre ilustración; dial **ENERGY 2 / RHYTHM 2 / MOTION 1**.

- **ENERGY 2:** la ilustración pone la energía; la interfaz se queda quieta y legible encima.
- **RHYTHM 2:** estructura constante (barra arriba, ventanas flotando con aire entre ellas), con el
  fondo y los widgets como única variación.
- **MOTION 1:** solo movimiento que informa (abrir y cerrar ventanas, progreso, visualizador de audio
  cuando suena algo). Todo se para con "reducir animaciones".

## 3. Temas

Un tema es una carpeta `branding/themes/<id>/` con `theme.conf` (paleta) y su fondo.
`branding/themes/check.py` valida el contraste de cada tema; un tema que falla no entra en la ISO.

| Tema | Modo | Carácter | Acento |
|---|---|---|---|
| **Ámbar** (por defecto) | oscuro | madera, mostaza y verde azulado de los 70 | `#E0A84F` |
| **Papel** | claro | papel envejecido, tinta, oliva | `#666211` |
| **Nórdico** | oscuro | pizarra azulada, hielo | `#88C0D0` |
| **Bosque** | oscuro | niebla sobre pinos | `#9BC4A0` |
| **Sakura** | oscuro | ventanas de tinta sobre rosa cerezo | `#F2A7BC` |
| **Violeta** | oscuro | monocromo violeta | `#8F86F2` |
| **Tu fondo** | según la imagen | paleta calculada con matugen de cualquier imagen | el que salga |

Por qué Ámbar por defecto: es el heredero del estilo Retro 70s que Core eligió en octubre (cálido,
reconocible) y funciona bien en pantallas baratas.

**Claves de `theme.conf`:** `bg` (fondo de ventana), `surface` (campos, terminal, filas), `line`
(bordes), `text`, `text_dim`, `accent`, `accent_fg` (texto sobre el acento), `danger`, `warning`,
`term` y `term_bright` (los 16 colores de terminal).

**Reglas de color:**
- El acento marca **una cosa por pantalla**: lo seleccionado, el foco y la acción principal.
- Peligro y aviso nunca se comunican solo con color: siempre con icono o texto.
- "Tu fondo" pasa por el mismo `check.py`; si la imagen da una paleta sin contraste, se corrige
  aclarando u oscureciendo el color que falla, sin cambiar su tono.

## 4. Fondos

Mezcla: ilustraciones de Core como fondos insignia y arte con licencia libre (CC0 o CC-BY) para el
resto. Cada fondo lleva autor y licencia en `branding/themes/<id>/CREDITS` y en la wiki.
Ningún arte de Core se publica sin su visto bueno expreso, pieza por pieza. Mientras falte un fondo
definitivo, el tema usa uno provisional y su `CREDITS` lo dice.

## 5. Forma (igual en todos los temas)

| Pieza | Decisión | Por qué |
|---|---|---|
| Ventanas | sólidas, borde de 2 px (`line`; `accent` en la ventana activa), radio 8 px | El borde activo dice dónde escribes sin brillos. |
| Separación | 12 px entre ventanas y con los bordes de pantalla en Hyprland; en XFCE, Openbox y KDE las ventanas flotan | Deja ver el fondo, que es la identidad. |
| Barra superior | 30 px, `bg` sólido; izquierda: escritorios como puntos; centro: reloj; derecha: estado en texto + icono | Lo esencial a la vista, nada de iconos de adorno. |
| Barra de título | sin texto de adorno; botones como tres puntos de 10 px en `text_dim`, el de cerrar en `danger` al pasar el ratón | Mínima, y se sabe qué hace cada punto. |
| Controles | radio 6 px; contenedores (menús, tarjetas) 8 px | El radio separa control de contenedor. |
| Sombras | solo en menús y ventanas flotantes, una sombra corta | Marca lo que está por encima. |
| Transparencia | ninguna | Decisión de Core: "menos glass". |

## 6. Tipografía

| Uso | Fuente | Por qué |
|---|---|---|
| Titulares, logotipo, GRUB, arranque, reloj grande | **Outfit 700** | Geométrica y redonda, se lee de lejos. |
| Interfaz y barra | **Space Grotesk 400/500** | Legible en pequeño y con carácter en los números. |
| Terminal, widgets, código | **JetBrains Mono** | Los widgets son salida de terminal: monoespaciada es su contenido, no un adorno. |

## 7. Superficies, una a una

- **GRUB:** fondo del tema oscurecido, logotipo en Outfit, lista centrada, selección en el acento.
- **Arranque (Plymouth):** fondo del tema, logotipo y una barra fina de progreso en el acento.
- **Login (LightDM):** el fondo del tema; tarjeta `bg` con el nombre del usuario y su inicial en un
  círculo del acento (sin avatar inventado); reloj grande en Outfit.
- **Live:** escritorio Ámbar con el instalador abierto y un icono para volver a él.
- **Instalador:** barra lateral y páginas en la paleta del tema por defecto; una página **Tema** con
  vistas reales de cada tema (capturas del escritorio, no esqueletos), la descripción junto a la imagen.
- **Escritorio:** la forma del punto 5 en los cuatro entornos; GTK (adw-gtk3 + libadwaita), Qt
  (esquema de color de KDE y Kvantum), terminal, fastfetch, cava y btop toman la paleta.
- **sl-welcome y sl-ctl:** misma paleta; la cabecera de sl-welcome muestra el fondo del tema.

## 8. Texto

- Español, tuteo, frases cortas. Sin rayas largas (—): coma, punto, dos puntos o paréntesis.
- Nada de cifras o promesas que el sistema no cumpla: cada afirmación tiene que poder comprobarse en el código.
- Botones con el verbo de lo que hacen ("Instalar", "Aplicar perfil"), no "Empezar" ni "Descubrir".

## 9. Accesibilidad

- Contraste AA en todo el texto y en los 16 colores de terminal, comprobado por `check.py`.
- Foco de teclado visible en todos los controles (borde del acento).
- Todo se puede usar con teclado, instalador incluido.
- Hay un tema de alto contraste oscuro y otro claro, completos (pendientes de definir).
