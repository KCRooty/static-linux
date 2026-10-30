# Requisitos de hardware

`sl-detect` recomienda un entorno, sistema de archivos y kernel distintos
según en qué fila caes. No hay una única "instalación recomendada" — hay
cuatro, y el instalador elige por ti (siempre puedes anular la
recomendación).

| Nivel | RAM | Almacenamiento | Entorno |
|---|---|---|---|
| Mínimo absoluto | 512 MB | 10 GB | Openbox minimal |
| Mínimo funcional | 1 GB | 15 GB | XFCE temático |
| Estándar | 2 GB | 20 GB | XFCE o Hyprland lite |
| Recomendado (techo) | 4 GB | 30 GB | Hyprland + Astal full |

**Techo de RAM recomendado: 4 GB.** Static Linux no persigue ser el sistema
más ligero del mercado (ese nicho ya está cubierto) — persigue ser usable en
hardware que Windows 11 o una distro "moderna" por defecto ya descartaron,
sin sacrificar tener un entorno gráfico agradable.

## Arquitecturas

- `x86_64` — objetivo principal, el más probado.
- `arm64` — soporte activo en desarrollo (Raspberry Pi 4/5, RK3399/Pinebook
  Pro, RK3588). Ver [sl-detect](../herramientas/sl-detect.md#gpus-arm-por-device-tree-no-pci)
  para cómo se detecta la GPU en estas placas (no son dispositivos PCI).
- `arm32` — soportado con el perfil Openbox minimal forzado.

## GPU → soporte de Wayland

La tabla completa vive como datos en
[`sl-detect/rules/gpu.rules`](https://github.com/KCRooty/static-linux/blob/main/sl-detect/rules/gpu.rules)
y `gpu-soc.rules` (ARM), no en código — para añadir una familia de GPU no
hace falta tocar Python. Resumen:

| Familia | Wayland |
|---|---|
| Intel Bay Trail (Z36xxx/Z37xxx) | ❌ — confirmado en el iMedia S2883 |
| Intel GMA (pre-2010, 945/950/X3xxx) | ❌ |
| Intel Gen9+ / Xe / Arc | ✅ |
| AMD GCN+ (HD 7000+, Polaris, Vega, RDNA) | ✅ |
| AMD pre-GCN (HD 2000-6000) | ❌ |
| Nvidia Kepler/Fermi (nouveau) | ❌ |
| Nvidia Maxwell+ (GTX 900+) | ✅ |
| Broadcom VideoCore VI/VII (RPi 4/5) | ✅ |
| Broadcom VideoCore IV (RPi 3) | ❌ — demasiado débil para un compositor |
| Mali Valhall/Midgard (RK3588/RK3399) | ✅ |

Sin GPU reconocida → `wayland_ok = false` por defecto (nunca al revés).
