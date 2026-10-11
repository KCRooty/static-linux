# Referencia: PC Principal (Ryzen 5 5600 + RTX 3070 Ti)

El equipo de desarrollo y pruebas actual. Sustituye al
[iMedia S2883](imedia-s2883.md), que ya no está disponible: aquel validó el
extremo bajo de `sl-detect` (Bay Trail, HDD, XFCE forzado); este valida el
extremo alto (Wayland, SSD, NVIDIA propietario).

```
CPU:      AMD Ryzen 5 5600 (Zen 3, 2022, 6 núcleos)
GPU:      NVIDIA GeForce RTX 3070 Ti (GA104, driver propietario nvidia-dkms)
RAM:      32 GB DDR4 (31.3 GB usables)
Disco:    SSD SATA 128 GB (sdb1=EFI, sdb2=BTRFS con subvolumen @)
Firmware: UEFI
Kernel:   linux-zen 7.2.9-zen1-1-zen
Entorno:  XFCE + LightDM (instalación Arch manual, octubre 2026)
```

## Salida real de `sl-detect --all`

```
CPU        : AMD Ryzen 5 5600 6-Core Processor  (~2022)
Arch       : x86_64
Firmware   : uefi
RAM        : 32006 MB
GPU        : NVIDIA Corporation GA104 [GeForce RTX 3070 Ti]
  family   : nvidia_turing_plus
  driver   : nvidia
Wayland    : True
Storage    : ssd
→ environment : hyprland-astal-full
→ filesystem  : btrfs
→ kernel      : linux-zen
→ I/O sched   : none
swapfile 2G  : False
EFI fallback : True
force XFCE   : False
```

Es el resultado esperado: GPU Turing+ con Wayland viable y RAM de sobra →
`hyprland-astal-full`; SSD con ≥ 4 GB → BTRFS; CPU de 2022 sobre SSD →
`linux-zen`. Fijado como test de regresión en
`sl-detect/tests/test_detect.py` (`PcPrincipalReference`).

## Qué queda por validar aquí

`sl-detect` *recomienda* Hyprland, pero el equipo corre XFCE: los entornos
`hyprland-astal-full` / `hyprland-astal-lite` siguen sin probarse en hardware
real, y NVIDIA propietario es justo el caso delicado en Wayland.

| Pendiente | Por qué importa en este equipo |
|---|---|
| `entornos/hyprland-astal-full/install.sh --home` | Primer arranque real de Hyprland + Astal, y con NVIDIA |
| `entornos/xfce-themed/install.sh --home` | Revalidar el tema XFCE en doble monitor |
| `iso/build.sh` (online) + arranque en QEMU/KVM | Con 32 GB ya no hace falta otro equipo para construir y probar la ISO |
| `sl-welcome` | Nunca se ha ejecutado completo fuera del iMedia |

## Discos: solo uno es de trabajo

Este equipo tiene más discos conectados que el de Arch, y contienen datos que
no son del proyecto. Para cualquier prueba del instalador, de la ISO o de
particionado:

- El único disco de trabajo es el SSD de 128 GB donde vive Arch.
- Las pruebas del instalador se hacen **en una VM con disco virtual**, nunca
  contra un disco físico de este equipo.
- Antes de cualquier operación de discos se comprueba el destino con
  `lsblk -o NAME,MODEL,SIZE` — por modelo, no por letra: `sdX` puede cambiar
  entre arranques.
