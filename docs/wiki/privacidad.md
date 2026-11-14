# Privacidad

Tres perfiles, todos reversibles, todos con backup automático antes de tocar
nada (`/var/backups/static-linux/privacy/`). Cero telemetría en los tres —
eso no es un perfil, es la línea base de Static Linux.

| Perfil | Qué añade | Kernel |
|---|---|---|
| **Básico** | Ajustes seguros desde el primer día + UFW + MAC aleatoria | `linux-zen` |
| **Mejorado** | + Firejail + AppArmor + USBGuard | `linux-zen` |
| **Máximo** | + Tor + kloak + swap cifrado | `linux-hardened` |

## Cambiar de perfil

```bash
sudo sl-ctl privacy --profile basico    # o mejorado / maximo
```

O desde [`sl-welcome`](herramientas/sl-welcome.md), página Privacidad (pide
contraseña de administrador vía `pkexec`).

## AppArmor

En Mejorado y Máximo, el perfil añade
`lsm=landlock,lockdown,yama,integrity,apparmor,bpf` a
`GRUB_CMDLINE_LINUX_DEFAULT` (con copia en `/var/backups/static-linux/privacy/`)
y activa `apparmor.service`. Los kernels de Arch no cargan AppArmor si no se
pide así, y sin eso el servicio no hace nada. Volver a Básico lo quita de la
línea de arranque. Hace falta reiniciar; `aa-status` dice cuántos perfiles
hay cargados.

## Cómo están construidos

`privacidad/<perfil>/apply.sh` — todos comparten `privacidad/scripts/lib.sh`
para las funciones de backup (`sl_require_root`, `sl_apply_baseline`,
`sl_record_profile`, ...), así que el mecanismo de reversión es idéntico en
los tres. Reaplicar cualquier perfil (incluido el mismo) vuelve a copiar
los originales antes de escribir nada nuevo.

Las listas de paquetes canónicas viven en
`packages/lists/privacy-{basic,enhanced,max}.list` — los `packages.list`
dentro de cada `privacidad/<perfil>/` son solo un puntero a ellas, para que
el builder del ISO y `apply.sh` nunca diverjan.
