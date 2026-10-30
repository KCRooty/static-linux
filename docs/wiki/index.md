# Static Linux

**by Static Forge — fast. private. yours.**

Distribución basada en Arch Linux con detección automática de hardware
(`sl-detect`), entornos de escritorio adaptativos según el equipo detectado,
y privacidad por defecto (cero telemetría, siempre).

No es un remix con un wallpaper distinto encima de Arch. La idea central es
que el propio instalador decida qué entorno, sistema de archivos y kernel le
convienen a *tu* máquina — desde un Celeron J1900 de 2013 con HDD hasta un
equipo moderno con GPU dedicada — en vez de que lo decidas tú a ciegas o te
lo impongan.

## Por qué existe

Revivir hardware viejo (el primer equipo de pruebas real es un
[Packard Bell iMedia S2883](hardware/imedia-s2883.md) de 2013 rescatado de la
basura) sin que el sistema operativo sea el cuello de botella. Arch por la
base rodante y AUR, `sl-detect` para que la instalación se ajuste al equipo
en vez de forzar un único perfil "recomendado" para todo el mundo.

## Piezas

| Pieza | Qué hace |
|---|---|
| [`sl-detect`](herramientas/sl-detect.md) | Detecta hardware, recomienda entorno/FS/kernel |
| [`sl-ctl`](herramientas/sl-ctl.md) | Gestión post-instalación (tweaks, snapshots, sabores, privacidad) |
| [`sl-welcome`](herramientas/sl-welcome.md) | App de primer arranque: apariencia, privacidad, catálogo de apps |
| [`staticlinux-base`](herramientas/staticlinux-base.md) | El paquete que lleva todo lo anterior a `/usr/lib/static-linux/` |
| [Entornos](entornos.md) | Hyprland+Astal (full/lite) · XFCE temático · Openbox minimal |
| [Privacidad](privacidad.md) | 3 perfiles reversibles: Básico, Mejorado, Máximo |
| [Sabores](sabores.md) | 9 presets de instalación (Gaming, Dev, Cybersecurity...) |
| [Branding y acentos](branding-accents.md) | 10 acentos de color, un solo sistema de theming |

## Reglas que no van a cambiar

Estas decisiones ya están tomadas — ver [FAQ](faq.md) para el porqué de
cada una:

- Base: **Arch**, no Artix/Debian/Ubuntu.
- Init: **systemd**.
- Navegador por defecto: **Brave Origin** (canal Release).
- AUR helper: **paru**, únicamente CLI.
- **Secure Boot: no soportado.**
- Telemetría: **cero, absoluto**.
- Techo recomendado: **4 GB de RAM**.

## Estado del proyecto

Fase 1 (base mínima arrancable) completa, validada en el iMedia S2883. Fase 2
(XFCE + `sl-detect`) en curso. Ver `AGENTS.md` en la raíz del repositorio
para el estado detallado, y
[la estructura del repositorio](https://github.com/KCRooty/static-linux/blob/main/docs/wiki/estructura.md)
para cómo está organizado todo.

## Enlaces

- [Repositorio en GitHub](https://github.com/KCRooty/static-linux)
- [Reportar un problema](https://github.com/KCRooty/static-linux/issues/new)
- [Cómo contribuir](contribuir.md)
