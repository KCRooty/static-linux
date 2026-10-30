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

## `sl-ctl info`

Lee el JSON de `sl-detect` y el perfil de privacidad activo, y muestra un
resumen con marca — CPU, RAM, GPU, entorno/FS/kernel recomendados.

## `sl-ctl welcome`

Busca `sl-welcome` en el `PATH` (`shutil.which`) y lo relanza. Si no está
instalado, lo dice y no falla.
