# Referencia: Packard Bell iMedia S2883

El primer equipo real de Static Linux — rescatado, no comprado para probar.
Toda la lógica de `sl-detect` se valida contra este hardware antes que
contra nada más.

```
Modelo:   Packard Bell iMedia S2883
CPU:      Intel Celeron J1900 (Bay Trail, 2013, 4 núcleos)
GPU:      Intel Atom Processor Z36xxx/Z37xxx (driver i915)
RAM:      8 GB DDR3 instalados / 3.64 GB usables (VRAM compartida)
Disco:    250 GB HDD (sda1=512 MB EFI, sda2=232 GB EXT4)
Red:      LAN integrada enp3s0 (ethernet)
Pantalla: MAG 272F 1920x1080
Kernel:   linux-lts 6.18.50-2-lts
```

## Salida de referencia (fastfetch)

```
OS:      Arch Linux x86_64
Host:    iMedia S2883
Kernel:  Linux 6.18.50-2-lts
CPU:     Intel(R) Celeron(R) J1900 (4)
GPU:     Intel Atom Processor Z36xxx/Z37xxx
Memory:  769.16 MiB / 3.64 GiB
Swap:    599.11 MiB / 2.00 GiB
Shell:   bash 5.3.15
```

## Salida esperada de `sl-detect --all`

```
gpu:        intel_bay_trail
driver:     i915
wayland:    False   ← Bay Trail tiene mal soporte de Wayland
ram_mb:     3727
arch:       x86_64
firmware:   uefi
storage:    hdd
recommend:  xfce-themed
fs:         ext4
kernel:     linux-lts
```

## Lecciones de la instalación (Fase 1)

Ya forman parte del diseño del instalador — no son notas sueltas:

| Problema | Qué pasó | Solución en Static Linux |
|---|---|---|
| Firmware UEFI limitado | `efibootmgr` daba I/O error en el UEFI del J1900 | Siempre se copia `grubx64.efi` a `/EFI/BOOT/BOOTX64.EFI` |
| OOM compilando Rust | `paru` moría (SIGKILL) compilando | Swapfile de 2 GB automático si RAM < 4 GB |
| EXT4 sobre BTRFS | J1900 + HDD → overhead de BTRFS notable | `sl-detect`: HDD → EXT4, SSD+4GB → BTRFS |
| Bay Trail sin Wayland | GPU Z36xxx = sin Wayland viable | `sl-detect`: Z36xxx → fuerza fallback a XFCE |
| Swapfile no persistente | El swap desaparecía al reiniciar | El instalador añade `/swapfile` a `/etc/fstab` |

## Validado en vivo

Este equipo llegó a arrancar Static Linux completo con XFCE temático,
fastfetch de marca (logo Static Forge, tema `Static-Void`) y el acento
morado por defecto funcionando en vivo. El equipo ya no está disponible para
seguir probando — las pruebas reales continúan en el
[PC Principal](pc-principal.md), que lo sustituye como máquina de referencia.
Los valores de esta página siguen fijados como tests de regresión de
`sl-detect`.
