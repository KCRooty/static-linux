# Rendimiento y estabilidad

!!! info "La parte de *fast*"
    Todo esto viene de serie y se puede deshacer: cada ajuste está en una ruta
    de proveedor y un fichero con el mismo nombre en `/etc` gana.

Ajustes de sistema que instala `staticlinux-base`. Siguen la guía de gaming de
CachyOS, adaptada a una distro que también tiene que ir bien en un Celeron con
disco duro. Todo va en rutas de proveedor (`/usr/lib/...`): un fichero con el
mismo nombre en `/etc` gana, así que cualquier ajuste se puede deshacer sin
tocar el paquete. No se toca la línea de arranque del kernel.

| Fichero | Instalado en | Qué hace |
|---|---|---|
| `sysctl.d/70-static-linux.conf` | `/usr/lib/sysctl.d/` | Memoria pensada para zram (swappiness 100, page-cluster 0), escritura a disco en bloques pequeños para que una copia grande no congele el escritorio, sin watchdog NMI, sin frenar los split locks, red con BBR + fq |
| `zram-generator.conf` | `/usr/lib/systemd/` | swap comprimida en RAM: la mitad de la RAM, 8 GB como mucho, zstd, prioridad 100 |
| `udev/60-static-linux-ioschedulers.rules` | `/usr/lib/udev/rules.d/` | Planificador de disco por tipo: NVMe `none`, SSD/eMMC `mq-deadline`, disco duro `bfq` |
| `modprobe.d/static-linux.conf` | `/usr/lib/modprobe.d/` | Sin los watchdogs de hardware `iTCO_wdt` y `sp5100_tco` (despiertan la CPU y pueden colgar el apagado) |
| `systemd/journald.conf` | `/usr/lib/systemd/journald.conf.d/` | El journal no pasa de 256 MB en disco ni de 64 MB en RAM |
| `systemd/earlyoom.conf` | `earlyoom.service.d/` | Con RAM y swap casi llenas, cierra el proceso más grande antes de que el escritorio se congele; nunca la sesión, el compositor ni el audio; primero pestañas y apps Electron |
| `environment.d/60-static-linux.conf`, `profile.d/static-linux-gpu.sh` | `/usr/lib/environment.d/`, `/etc/profile.d/` | Caché de shaders de 12 GB para Mesa y NVIDIA: menos tirones la segunda vez que juegas |
| `makepkg.conf.d/static-linux.conf` | `/etc/makepkg.conf.d/` | paru/makepkg compilan con todos los núcleos y comprimen en paralelo |
| `scx/config.toml` | `/usr/share/static-linux/rendimiento/` | Plantilla de `/etc/scx_loader/config.toml`: planificador de CPU `scx_lavd` |

## Servicios

El instalador activa `earlyoom`, `power-profiles-daemon` y `paccache.timer`
(limpia la caché de paquetes cada semana y deja las 3 últimas versiones).
`fstrim.timer` ya venía activado.

## Lo que depende de la máquina

El job `rendimiento` del instalador hace dos cosas:

- **Menos de 4 GB de RAM:** un `/swapfile` de 2 GB con prioridad 10 (zram
  sigue primero) y su línea en `fstab`. En btrfs no se crea, porque rompería
  las instantáneas, y btrfs solo se elige con 4 GB o más.
- **Sabor Gaming:** instala `scx-scheds` y `scx-tools`, escribe
  `/etc/scx_loader/config.toml` y activa `scx_loader`. `scx_lavd` sigue la
  carga por su cuenta (ahorra en reposo y rinde bajo carga) y prioriza lo
  interactivo. Si falla, el kernel vuelve solo a su planificador.

## Juegos: `sl-game`

En las opciones de lanzamiento de Steam:

    sl-game %command%
    sl-game gamemoderun mangohud %command%

Mientras el juego está abierto, power-profiles-daemon mantiene el perfil
`performance` y, si hay un planificador sched_ext, lo pasa a su modo Gaming.
Al salir, aunque el juego se cuelgue, vuelve todo a como estaba.

## `sl-ctl perf`

    sl-ctl perf                        # estado: kernel, planificador, energía, swap, discos
    sl-ctl perf profile performance    # power-saver | balanced | performance
    sudo sl-ctl perf scheduler lavd    # lavd | bpfland | cosmos | flash | rusty | off

`scheduler` instala scx si falta, guarda una copia de la configuración
anterior y deja el cambio también para el siguiente arranque.

## Lo que no se hace, y por qué

- **ananicy-cpp:** choca con gamemode y con sched_ext, como avisa CachyOS.
- **Parámetros del kernel** (`mitigations=off`, `nowatchdog`…): cambiarían
  GRUB y la seguridad. Lo equivalente que se puede hacer sin tocar el
  arranque ya va en sysctl y modprobe.
- **Kernel propio:** Static Linux usa `linux-zen` (o `linux-lts` en máquinas
  viejas), que ya trae sched_ext.

Ajustes reversibles con `sl-ctl tweaks`: `split-lock` (vuelve a frenar los
split locks) y `watchdog` (vuelve a cargar los watchdogs).
