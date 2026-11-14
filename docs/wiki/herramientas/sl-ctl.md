# sl-ctl

Gestión post-instalación. CLI en `sl-ctl/sl-ctl.py`, en el idioma del
sistema. Todos los comandos de abajo funcionan; los que cambian algo piden
`sudo`.

```bash
sl-ctl update                    # pacman + AUR + Flatpak
sl-ctl tweaks --list             # todos los tweaks y su estado
sl-ctl tweaks --apply <nombre>   # aplicar con backup automático
sl-ctl tweaks --revert <nombre>  # volver al original
sl-ctl snapshot                  # instantáneas (BTRFS + Snapper)
sudo sl-ctl snapshot --create    # instantánea manual
sudo sl-ctl snapshot --rollback <n>  # devolver los archivos a la instantánea n
sl-ctl flavor                    # sabores y cuáles están instalados
sudo sl-ctl flavor add gaming    # añadir un sabor tras la instalación
sudo sl-ctl flavor remove gaming # quitarlo
sudo sl-ctl privacy --profile <perfil>  # cambiar de perfil de privacidad
sl-ctl audit                     # qué se conecta a la red ahora mismo
sl-ctl theme --list              # temas disponibles y el activo
sl-ctl theme <tema>              # aplicar un tema (fondo + paleta + estilo)
sl-ctl perf                      # rendimiento: planificador, energía, swap, discos
sl-ctl perf profile performance  # perfil de energía
sudo sl-ctl perf scheduler lavd  # planificador de CPU (sched_ext) u off
sl-ctl server                    # servicios del servidor y qué escucha en la red
sudo sl-ctl server on cockpit    # activar un servicio (y abrir su puerto en ufw)
sudo sl-ctl server off cockpit   # pararlo y cerrar su puerto
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

## `sl-ctl update` y `sl-ctl snapshot`

`update` = `pacman -Syu` + AUR (`paru`, con tu usuario) + Flatpak. Con el
repositorio [`[staticlinux]`](../repositorio.md) también llegan así las
versiones nuevas de `staticlinux-base`, Brave Origin y el resto de paquetes
propios, sin reinstalar desde una ISO.

En una instalación con **BTRFS**, el instalador deja Snapper configurado
para `/` (máximo 10 instantáneas, sin las horarias) y `snap-pac` hace una
**antes y otra después de cada operación de pacman**, `sl-ctl update`
incluido. `grub-btrfsd` las añade al menú de GRUB, así que si una
actualización deja el sistema sin arrancar se puede entrar en la anterior.

`sl-ctl snapshot --rollback <n>` devuelve los archivos del sistema al estado
de la instantánea `n` con `snapper undochange` (antes crea otra, por si
quieres volver). No usa `snapper rollback`: el instalador monta `subvol=@`
explícitamente y cambiar el subvolumen por defecto no tendría efecto.
En EXT4 no hay instantáneas.

## `sl-ctl flavor`

Instala o quita un [sabor](../sabores.md) después de instalar, con las mismas
listas que usa el instalador (`packages/lists/sabor-*.list`) y los mismos
ajustes: grupos del usuario (gamemode, docker, libvirt, realtime), sockets
(docker, libvirtd), y en Gaming el driver Vulkan de 32 bits de tu GPU, el
módulo `ntsync` y el planificador `scx_lavd`. Las apps de Flathub se instalan
para todo el sistema; las del AUR, con `paru` y tu usuario.

`remove` solo quita lo que ningún otro sabor instalado, ni el sistema base,
ni el escritorio necesitan (`pacman -Rsu`, la configuración se queda como
`.pacsave`). Los sabores instalados se guardan en `/etc/static-linux/flavors`.

## `sl-ctl audit`

Lo que sale a la red en este momento: puertos escuchando fuera de
localhost, conexiones abiertas y de qué proceso son, si el DNS va cifrado
por dnscrypt-proxy, el estado de ufw y los temporizadores de systemd. Con
`sudo` ve también los procesos de root y de otros usuarios. Ver
[Privacidad → Auditoría](../privacidad.md#auditoria-de-conexiones).

## `sl-ctl privacy`

Instala las herramientas del perfil (firejail, usbguard, tor… según el
caso; el kernel no se cambia) y ejecuta `privacidad/<perfil>/apply.sh` (ver
[Privacidad](../privacidad.md)). Sin argumento, muestra el perfil activo
(`/var/lib/static-linux/privacy-profile`).

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

## `sl-ctl server`

Para el sabor Servidor / Homelab, que se instala con todo apagado. Sin
argumentos enseña cada servicio (instalado, activo o parado, y sus puertos),
lo que escucha en la red fuera de `localhost` y si ufw está activo.
`server on <servicio>` lo activa y arranca, y si ufw está activo abre sus
puertos con el comentario `sl-ctl server <servicio>`; `server off` lo para,
lo desactiva y borra esas reglas. Servicios: `ssh` (22), `cockpit` (9090),
`docker` (añade tu usuario al grupo), `nginx` (80, 443), `mariadb`
(inicializa la base de datos la primera vez; el 3306 no se abre),
`fail2ban` y `wireguard` (51820/udp, necesita `/etc/wireguard/wg0.conf`).
Ver [Servidor](../servidor.md).

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
