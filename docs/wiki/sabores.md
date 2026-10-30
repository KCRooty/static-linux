# Sabores (flavors)

Presets de instalación por encima del entorno base. Daily Driver no es un
sabor — es la base (siempre incluida). Los otros ocho son opcionales.

| Sabor | Incluye |
|---|---|
| 🖥️ Daily Driver | Siempre incluido — no es un sabor seleccionable |
| 🎮 Gaming | Steam + Proton-GE, Lutris, Heroic, MangoHud, GameMode |
| 🎨 Content Creation | Krita, GIMP, Blender, DaVinci, OBS, LMMS, Ardour |
| 💻 Development | VS Code, Git, Docker, Python, Rust, Node, Java |
| 🔒 Cybersecurity | Nmap, Wireshark, Metasploit, Hashcat, Ghidra, Tor |
| 📄 Office | LibreOffice, Obsidian, Joplin, Bitwarden |
| 🖥️ Server/Homelab | Docker, Nginx, MariaDB, WireGuard, Fail2ban, Cockpit |
| 🧪 Virtual Machines | QEMU+KVM, virt-manager, VirtualBox |
| 🎓 Education | GeoGebra, Stellarium, Anki, Jupyter, Thonny, FreeCAD |

## Cómo están construidos

Las listas canónicas viven en `packages/lists/sabor-<slug>.list` (mismo
formato que `base.list` — un paquete por línea, los del AUR comentados como
`# paquete (AUR)`). El job de Calamares `sabores` (`installer/calamares/modules/sabores/`)
las lee del sistema instalado, instala los paquetes de repos oficiales con
`pacman`, y **nunca** instala AUR durante el propio instalador (`pacman` no
puede compilar como root ahí) — los deja anotados en
`globalStorage["slSaboresAurPending"]` para avisar después.

!!! note "Falta la página de selección"
    El job ya funciona (`globalStorage["slSabores"]` → lista de slugs), pero
    todavía no existe la página del instalador donde elegirlos — ver
    [Instalación](instalacion.md). Después de instalar, `sl-ctl flavor --add
    <sabor>` es la otra vía (en desarrollo, marcada EXPERIMENTAL).

## Nombres de paquete

Verificados contra `archlinux.org/packages` y la API de AUR el 21/09/2026 —
cada archivo lo dice en su cabecera. Salió a relucir que varios paquetes que
solían ser solo-AUR ya están en `extra` (`metasploit`, `ghidra`, `obsidian`,
`geogebra`), que `visual-studio-code-bin` (AUR, telemetría de Microsoft) se
puede sustituir por `code` (oficial, el build Open Source de VS Code — mejor
encaje con la política de cero telemetría), que `virtualbox-host-modules-arch`
ya no existe (ahora es `virtualbox-host-dkms`) y que `bridge-utils` se cayó
de los repos oficiales (solo AUR). Como cualquier paquete de Arch, esto se
mueve con el tiempo — si construyes un ISO mucho después de esa fecha,
contrasta de nuevo contra `pacman -Ss`/AUR antes de dar por buena la lista.
