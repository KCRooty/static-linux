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

## Nombres de paquete: verificar antes de construir la ISO

Las listas se escribieron con los nombres de paquete habituales de Arch/AUR,
pero sin verificarlas contra los repositorios en el momento de construir el
ISO — cada archivo lo dice en su cabecera. Si vas a construir un ISO con un
sabor nuevo, contrasta la lista contra `pacman -Ss`/AUR primero.
