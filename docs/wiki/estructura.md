# Estructura del repositorio

```
static-linux/
├── sl-detect/            Detección de hardware (Python, solo stdlib)
│   ├── detect.py         Lógica + CLI (--all/--json/--recommend-*/--gpu)
│   ├── rules/            Conocimiento de hardware como datos, no código
│   │   ├── gpu.rules         regex | familia | driver | wayland (GPUs PCI)
│   │   ├── gpu-soc.rules     lo mismo para GPUs de SoC ARM (device-tree)
│   │   ├── wayland.rules     familias vetadas (wayland = false forzado)
│   │   ├── entorno.rules     umbrales de RAM por tier
│   │   └── kernel.rules      LTS_CPU_YEAR + año aproximado por modelo de CPU
│   └── tests/            38 tests unittest (sin dependencias)
│
├── sl-ctl/               Gestión post-install (CLI). detect/info/privacy/tweaks
│   └── sl-ctl.py            operativos; update/snapshot/mirror/flavor experimentales
│
├── sl-welcome/           App GTK4/libadwaita de primer arranque
│   ├── src/                 main.py, window.py, pages/{overview,appearance,privacy,catalog}.py
│   ├── catalog/              8 categorías, ~56 apps extra
│   └── data/                 .desktop, política polkit, wrapper de pkexec
│
├── installer/calamares/
│   ├── modules/
│   │   ├── sl-detect/        job: publica el informe en globalStorage
│   │   ├── accent/           job: aplica el acento elegido en el target
│   │   ├── basepkgs/         job: instala packages/lists/base.list
│   │   ├── entorno/          packagechooser: elige el entorno (solo UI)
│   │   ├── entorno-pkgs/     job: instala el entorno elegido + su install.sh
│   │   ├── privacidad/       packagechooser: elige el perfil (solo UI)
│   │   ├── privacidad-apply/ job: corre el apply.sh del perfil elegido
│   │   ├── sabores/          job: instala los sabores elegidos
│   │   └── luks/             job: avisos de LUKS2 (hardware J1900, Secure Boot)
│   ├── branding/staticlinux/  branding.desc — sin logo real todavía
│   └── settings.conf          secuencia completa (live pacman, sin unpackfs)
│
├── entornos/             Configs y dotfiles, cada uno con su install.sh --home|--skel
│   ├── hyprland-astal-full/   ≥4 GB, Wayland, shell propio en Astal/AGS
│   ├── hyprland-astal-lite/   2-4 GB, Wayland, mismo shell sin blur/sombras
│   ├── xfce-themed/           ≥1 GB, Xorg — el único validado en hardware real
│   └── openbox-minimal/       512 MB, Xorg, sin compositor por defecto
│
├── privacidad/           3 perfiles + librería compartida
│   ├── scripts/lib.sh        helpers con backup automático
│   ├── perfil-basico/        baseline + UFW + MAC random · linux-zen
│   ├── perfil-mejorado/      + Firejail + AppArmor + USBGuard · linux-zen
│   └── perfil-maximo/        + Tor + kloak + swap cifrado · linux-hardened
│
├── packages/
│   ├── lists/            base + 4 entornos + 3 perfiles de privacidad + 8 sabores
│   │                     (sabor-*.list — no hay un directorio sabores/ aparte,
│   │                     el job de Calamares lee estas listas directamente)
│   └── staticlinux-base/ PKGBUILD real — lleva todo el repo a /usr/lib/static-linux/
│
├── branding/
│   ├── accents/           10 acentos, apply.sh (fastfetch/GTK/xfwm4/terminal/greeter/wallpaper)
│   ├── fastfetch/          logos ASCII + config.jsonc
│   └── wallpapers/         gen-wallpaper.py (stdlib puro) + un PNG por acento
│
├── iso/                  perfiles archiso — placeholders, sin airootfs todavía
│   ├── profiledir-online/    ISO online (~1 GB, mensual)
│   ├── profiledir-offline/   ISO offline (~4 GB, trimestral)
│   └── build.sh
│
├── docs/wiki/            fuentes MkDocs Material — sitio real, ver mkdocs.yml
├── .github/workflows/    deploy de la wiki a GitHub Pages
├── AGENTS.md             contexto del proyecto — leer primero
├── CONTRIBUTING.md
└── README.md
```

No existen (todavía) `entornos/shared/`, `sabores/` como directorio propio, ni
`scripts/{build,ci}/` — quedaron descartados o reemplazados por un diseño
distinto según se fue construyendo cada pieza; este documento refleja lo que
hay realmente en el repo, no el plan original.

## Reglas de oro

1. Todo tweak de `sl-ctl` y toda acción de privacidad → backup/restore automático.
2. El conocimiento de hardware va en `sl-detect/rules/*.rules`, no en `detect.py`.
3. `sl-detect` solo stdlib: tiene que correr en la ISO live mínima.
4. `[BUILD · bash]` para Linux · `[PROD · PowerShell]` para Windows. Nunca mezclar.
5. Techo de 4 GB RAM. >500 MB idle en Hyprland full = bug.
6. Bay Trail (Z36xxx) y Kepler → siempre XFCE, nunca Wayland. Confirmado.
