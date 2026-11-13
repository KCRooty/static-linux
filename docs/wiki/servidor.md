# Servidor / Homelab

Static Linux también sirve para una máquina sin pantalla: un servidor en casa,
un NAS, un mini PC con Docker. En el instalador, en la página de escritorio:

- **Sin entorno gráfico**: solo la consola. Ver
  [Entornos](entornos.md#sin-entorno-grafico-y-servidor-homelab).
- **Servidor / Homelab**: la consola más el sabor Servidor: Docker y
  docker-compose, Nginx, MariaDB, WireGuard, Fail2ban y Cockpit (un panel web
  para administrar la máquina desde el navegador de otro ordenador).

El sabor Servidor también se puede marcar con cualquier escritorio, en la
página de sabores.

## Nada escucha hasta que tú lo digas

Todo se instala apagado: el sistema recién instalado no abre ningún puerto.
Se activa servicio a servicio con `sl-ctl server`:

```bash
sl-ctl server                    # qué hay, qué está activo, qué escucha
sudo sl-ctl server on ssh        # entrar por SSH desde otra máquina
sudo sl-ctl server on cockpit    # panel web en https://<ip>:9090
sudo sl-ctl server on docker     # Docker (socket) y tu usuario en el grupo docker
sudo sl-ctl server off nginx     # parar y cerrar el puerto
```

Si el cortafuegos (ufw, perfiles de privacidad *mejorada* y *máxima*) está
activo, `on` abre el puerto del servicio y `off` lo vuelve a cerrar. MariaDB
se queda sin puerto abierto: para conectarte desde fuera, ábrelo tú
(`sudo ufw allow 3306/tcp`) sabiendo lo que haces.

## WireGuard

`sl-ctl server on wireguard` levanta `wg-quick@wg0`, así que antes hace
falta la configuración:

```bash
sudo -i
cd /etc/wireguard
umask 077
wg genkey | tee privada | wg pubkey > publica
cat > wg0.conf <<CONF
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = $(cat privada)

# [Peer]
# PublicKey = <clave pública del otro equipo>
# AllowedIPs = 10.8.0.2/32
CONF
sl-ctl server on wireguard
```

## Consejos

- Usa `tmux` para que lo que lances por SSH siga vivo al desconectarte, y
  `btop` para ver la máquina.
- `sl-ctl update` actualiza todo; en un servidor, mejor a mano y con
  instantánea antes (`sl-ctl snapshot --create`, si instalaste en btrfs).
