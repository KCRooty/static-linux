# sl-detect

Detección de hardware. Python 3, **solo librería estándar** — tiene que
poder correr en el ISO live mínimo, antes de que exista nada más. Vive en
`sl-detect/detect.py`, nunca falla de forma ruidosa: cada sonda degrada a un
valor seguro (XFCE / EXT4 / linux-lts) si algo no se puede detectar.

## CLI

```bash
sl-detect --all               # informe completo, legible
sl-detect --json              # para el módulo de Calamares
sl-detect --recommend-env     # solo el entorno recomendado
sl-detect --recommend-fs      # solo el sistema de archivos
sl-detect --recommend-kernel  # solo el kernel
sl-detect --gpu               # modelo de GPU, driver, soporte Wayland
```

## El conocimiento de hardware vive en datos, no en código

`sl-detect/rules/*.rules` — añadir una GPU o afinar un umbral de RAM es
editar un archivo de texto, no tocar `detect.py`:

| Archivo | Qué define |
|---|---|
| `gpu.rules` | `regex \| familia \| driver \| wayland` — GPUs PCI (`lspci`) |
| `gpu-soc.rules` | Lo mismo pero para GPUs de SoC ARM (device-tree, no PCI) |
| `wayland.rules` | Veto duro: familias forzadas a `wayland=false` pase lo que pase |
| `entorno.rules` | Umbrales de RAM por nivel (`FULL_RAM_MB`, `LITE_RAM_MB`, ...) |
| `kernel.rules` | Año aproximado de la CPU por substring, umbral LTS |

Archivo ausente o sin match → tabla mínima integrada en `detect.py` (mismo
resultado seguro: sin Wayland).

## GPUs ARM: por device-tree, no PCI

`lspci` no ve nada en una Raspberry Pi, un RK3588 o un Pinebook Pro — esas
GPUs son dispositivos de plataforma descritos en el device-tree, no tarjetas
PCI. `sl-detect` prueba primero `lspci`/`/sys/bus/pci`, y si no encuentra
nada, cae a leer `/proc/device-tree/compatible` y lo compara contra
`gpu-soc.rules`. Cubre por ahora Raspberry Pi 3/4/5, RK3399 (Pinebook Pro),
RK3588, y Allwinner/Amlogic — las placas que pide `CONTRIBUTING.md` en su
lista de "ayuda necesaria" para ARM64.

## Lógica de recomendación

```python
# Entorno
if wayland_support and ram_mb >= 4096:  → hyprland-astal-full
if wayland_support and ram_mb >= 2048:  → hyprland-astal-lite
if wayland_support and ram_mb >= 1024:  → xfce-themed
if not wayland_support:                 → xfce-themed (FORZADO)
if ram_mb < 1024:                       → openbox-minimal
if arch == 'arm32':                     → openbox-minimal

# Sistema de archivos
if storage == 'ssd' and ram_mb >= 4096: → btrfs
if storage == 'hdd' or ram_mb < 2048:   → ext4
if storage == 'emmc':                   → f2fs

# Kernel
if year_cpu < 2015 or storage == 'hdd': → linux-lts
else:                                   → linux-zen
```

(`linux-hardened` lo elige el perfil de privacidad Máximo, no `sl-detect`.)

## Tests

```bash
python3 -m unittest discover -s sl-detect/tests -v
```

38 tests, stdlib `unittest` — nada de `pytest` para no meter una dependencia
que el ISO live no tiene. Si pruebas en una máquina nueva, añade la salida
de `sl-detect --all` a tu PR (lo pide `CONTRIBUTING.md`).
