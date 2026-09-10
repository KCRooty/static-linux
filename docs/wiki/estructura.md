# Estructura del repositorio

```
static-linux/
├── sl-detect/            Detección de hardware (Python, solo stdlib) — PRIORIDAD
│   ├── detect.py         Lógica + CLI (--all/--json/--recommend-*/--gpu)
│   ├── rules/            Conocimiento de hardware como datos, no código
│   │   ├── gpu.rules         regex | familia | driver | wayland
│   │   ├── wayland.rules     familias vetadas (wayland = false forzado)
│   │   ├── entorno.rules     umbrales de RAM por tier
│   │   └── kernel.rules      LTS_CPU_YEAR + año aproximado por modelo de CPU
│   └── tests/            28 tests unittest (sin dependencias)
│
├── sl-ctl/               Gestión post-install (CLI). detect/info/privacy/tweaks
│   └── sl-ctl.py            operativos; update/snapshot/mirror experimentales
│
├── sl-welcome/           App GTK4 de primer arranque (Fase 7)
│
├── installer/calamares/
│   ├── modules/
│   │   ├── sl-detect/    Job Python: publica el informe en globalStorage
│   │   ├── entorno/      Selector de escritorio
│   │   ├── privacidad/   Selector de perfil de privacidad
│   │   └── recomendador/ Lógica de recomendación en la UI
│   ├── branding/staticlinux/
│   └── settings.conf
│
├── entornos/             Configs y dotfiles por entorno
│   ├── hyprland-astal-full/   4 GB, Wayland
│   ├── hyprland-astal-lite/   2 GB, Wayland
│   ├── xfce-themed/           1 GB, Xorg — FOCO ACTUAL
│   ├── openbox-minimal/       512 MB, Xorg
│   └── shared/                temas, iconos, fuentes, wallpapers, cursores
│
├── sabores/              Presets de instalación (Fase 6)
│   gaming · development · cybersecurity · content-creation ·
│   office · server · vm · education
│
├── privacidad/           3 perfiles + librería compartida
│   ├── scripts/lib.sh        helpers con backup automático
│   ├── perfil-basico/        baseline + UFW + MAC random · linux-zen
│   ├── perfil-mejorado/      + Firejail + AppArmor + USBGuard · linux-zen
│   └── perfil-maximo/        + Tor + kloak + swap cifrado · linux-hardened
│
├── packages/
│   ├── lists/            base + 4 entornos + 3 perfiles de privacidad
│   └── staticlinux-base/ meta-paquete (PKGBUILD, Fase 2+)
│
├── branding/             GRUB · SDDM · Plymouth · wallpapers · logos SF
│
├── iso/
│   ├── profiledir-online/    perfil archiso ISO online (~1 GB, mensual)
│   ├── profiledir-offline/   perfil archiso ISO offline (~4 GB, trimestral)
│   └── build.sh             script de build unificado
│
├── scripts/{build,ci}/   automatización de build y CI
├── docs/wiki/            fuentes MkDocs Material
├── docs/PROYECTO.md             especificación y decisiones de diseño
├── CONTRIBUTING.md
└── README.md
```

## Reglas de oro

1. Todo tweak de `sl-ctl` y toda acción de privacidad → backup/restore automático.
2. El conocimiento de hardware va en `sl-detect/rules/*.rules`, no en `detect.py`.
3. `sl-detect` solo stdlib: tiene que correr en la ISO live mínima.
4. `[BUILD · bash]` para Linux · `[PROD · PowerShell]` para Windows. Nunca mezclar.
5. Techo de 4 GB RAM. >500 MB idle en Hyprland full = bug.
6. Bay Trail (Z36xxx) y Kepler → siempre XFCE, nunca Wayland. Confirmado.
