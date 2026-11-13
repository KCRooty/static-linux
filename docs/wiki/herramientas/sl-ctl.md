# sl-ctl

Gestión post-instalación. CLI en `sl-ctl/sl-ctl.py`. `detect`, `info`,
`privacy` y las herramientas de backup/restore de `tweaks` funcionan hoy;
`update`, `snapshot`, `flavor` y `mirror` están en desarrollo (EXPERIMENTAL
en el propio `--help`).

```bash
sl-ctl update                    # pacman + AUR + Flatpak
sl-ctl tweaks --list             # todos los tweaks y su estado
sl-ctl tweaks --apply <nombre>   # aplicar con backup automático
sl-ctl tweaks --revert <nombre>  # volver al original
sl-ctl snapshot --create         # snapshot manual (Snapper)
sl-ctl snapshot --list
sl-ctl snapshot --rollback <id>
sl-ctl flavor --add <sabor>      # añadir un sabor tras la instalación
sl-ctl flavor --remove <sabor>
sl-ctl privacy --profile <perfil>  # cambiar de perfil de privacidad
sl-ctl theme --list              # temas disponibles y el activo
sl-ctl theme <tema>              # aplicar un tema (fondo + paleta + estilo)
sl-ctl perf                      # rendimiento: planificador, energía, swap, discos
sl-ctl perf profile performance  # perfil de energía
sudo sl-ctl perf scheduler lavd  # planificador de CPU (sched_ext) u off
sl-ctl info                      # info del sistema, con marca
sl-ctl detect                    # ejecuta sl-detect
sl-ctl welcome                   # relanza sl-welcome
sl-ctl mirror                    # actualiza mirrors
```

!!! danger "Regla que no se negocia"
    **Todo tweak de `sl-ctl` tiene que tener backup/restore automático.
    Ningún cambio irreversible. Nunca.** Cada `tweaks --apply` copia el
    archivo original (o marca que no existía) a
    `/var/backups/static-linux/tweaks/<nombre>/` antes de tocar nada.

## `sl-ctl privacy`

Delega en `privacidad/<perfil>/apply.sh` (ver [Privacidad](../privacidad.md)).
Sin argumento, muestra el perfil activo (`/var/lib/static-linux/privacy-profile`).

## `sl-ctl theme`

Delega en `sl-theme` (ver [Temas y estilos](../temas.md)). Sin argumento,
muestra el tema activo. Aplica al usuario que lo ejecuta, sin `sudo`.

## `sl-ctl perf`

Muestra el kernel, el planificador de CPU (el del kernel o uno de sched_ext),
el perfil de energía, la swap, el `swappiness`, el planificador de cada disco
y si earlyoom está activo. `perf profile` cambia el perfil de
power-profiles-daemon; `perf scheduler <lavd|bpfland|cosmos|flash|rusty|off>`
instala scx si falta, guarda la configuración anterior y deja el cambio
también para el próximo arranque. Ver [Rendimiento](../rendimiento.md).

## `sl-ctl tweaks`

| Tweak | Qué hace |
|---|---|
| `trim-timer` | Activa `fstrim.timer` (ya viene activado de serie) |
| `split-lock` | Vuelve a frenar los split locks (de serie no se frenan) |
| `watchdog` | Vuelve a cargar los watchdogs de hardware (de serie no se cargan) |

`swappiness-10` y `hdd-bfq` desaparecieron: con zram, un swappiness alto es
lo correcto, y cada tipo de disco ya recibe su planificador.

## `sl-ctl info`

Lee el JSON de `sl-detect` y el perfil de privacidad activo, y muestra un
resumen con marca — CPU, RAM, GPU, entorno/FS/kernel recomendados.

## `sl-ctl welcome`

Busca `sl-welcome` en el `PATH` (`shutil.which`) y lo relanza. Si no está
instalado, lo dice y no falla.
