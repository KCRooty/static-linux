# Sabores y catálogo

## Sabores

Paquetes de apps que se eligen en el instalador (página **Sabores**, se pueden
marcar varios o ninguno). Daily Driver no es un sabor: es la base, siempre
incluida — y trae **7-Zip, FFmpeg, yt-dlp, OpenSSH, Git, Flatpak y paru** de
serie.

| Sabor | Incluye | Ajustes de rendimiento |
|---|---|---|
| 🎮 Gaming | Steam + Proton, Lutris, Heroic (Epic/GOG/Amazon), Prism Launcher, Modrinth, MangoHud, GameMode, Gamescope, Wine | `[multilib]`, driver Vulkan de 32 bits de tu GPU, grupo `gamemode`, módulo `ntsync` |
| 🎨 Creación | Krita, GIMP, Inkscape, Blender, Kdenlive, Shotcut, OBS, Audacity, Ardour, LMMS, Hydrogen | audio en tiempo real (`realtime-privileges`) |
| 💻 Desarrollo | Git, GitHub CLI, Docker (+Compose, Buildx), Code - OSS, Python, Rust, Node, Java | Docker por *socket*: no gasta RAM hasta que lo usas |
| 📄 Oficina | LibreOffice en español con corrector, Obsidian, KeePassXC, Xournal++, PDF Arranger | — |
| 🧪 Máquinas virtuales | QEMU/KVM, virt-manager, GNOME Boxes, UEFI y TPM para invitados | libvirt por *socket*, grupo `libvirt` |
| 🎓 Educación | GeoGebra, Stellarium, Anki, Jupyter, FreeCAD | — |
| 🔒 Ciberseguridad | Nmap, Wireshark, Hashcat, John, Metasploit, Ghidra, Tor | — |
| 🖥️ Servidor | Docker, Nginx, MariaDB, WireGuard, Fail2ban, Cockpit | nada escuchando hasta que lo actives con [`sl-ctl server`](servidor.md) |

Las listas viven en `packages/lists/sabor-<slug>.list`: una línea por paquete
oficial, `# flatpak: <id>` para apps de Flathub (se instalan durante la
instalación) y `# paquete (AUR)` para lo del AUR, que no se puede compilar como
root durante la instalación: queda en `/etc/static-linux/pending-aur` y la
bienvenida lo ofrece ya marcado.

## Catálogo (bienvenida → Catálogo)

Más de 80 apps en 10 categorías — navegadores (Firefox, Zen, Chromium),
Vesktop (Discord + Vencord), Spotify + Spicetify, spotDL, DAWs (Ardour, LMMS,
Bitwig, REAPER), DaVinci Resolve, Kdenlive, Shotcut, Steam, Heroic, Minecraft
Java (Prism, Modrinth, launcher oficial) y Bedrock, VS Code / VSCodium,
LibreOffice, Obsidian, KeePassXC, qBittorrent, máquinas virtuales…

Cada app sale de la mejor fuente disponible, en este orden:

1. **Repos oficiales** — se instalan con un clic (pide la contraseña una vez).
2. **Flathub** — sin contraseña, para tu usuario.
3. **AUR** — se abre una terminal con `paru`.

Lo que ya tienes instalado aparece como tal.
