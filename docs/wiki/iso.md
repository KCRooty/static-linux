# Construir la ISO

```bash
sudo pacman -S archiso
cd iso
sudo ./build.sh online     # ~1 GB, necesita red al instalar
sudo ./build.sh offline    # ~4 GB, paquetes empaquetados
```

`iso/build.sh` monta el `airootfs/` de la sesión live desde tres sitios en
cada build (nada de esto se guarda en el repo, se genera siempre fresco):

1. `iso/airootfs-common/` — lo escrito a mano: autologin en tty1, `motd`,
   `hostname`, y el `.xinitrc` que arranca Openbox + Calamares directamente.
2. La función `package()` del propio `packages/staticlinux-base/PKGBUILD`,
   apuntando `pkgdir` al `airootfs/` en vez de a un paquete real — la sesión
   live acaba con el mismo árbol `/usr/lib/static-linux` que produciría
   `pacman -S staticlinux-base`, sin duplicar la lógica de empaquetado.
3. `installer/calamares/` copiado a `airootfs/etc/calamares/`.

La cadena de arranque (`efiboot/`, `syslinux/`, `grub/`, `pacman.conf`) se
copia tal cual del perfil `releng` del propio paquete `archiso` — no tiene
sentido mantener a mano una copia que se desincroniza de la versión de
archiso instalada en la máquina de build.

## `calamares` es solo-AUR

Comprobado contra la API real de Arch:
`archlinux.org/packages/search/json/?name=calamares` da cero resultados; sí
está en AUR. `mkarchiso` solo puede tirar de los repos pacman configurados
en la máquina de build (nunca del AUR directamente), así que hace falta un
repo local propio con `calamares` ya compilado antes de construir la ISO —
lo mismo que hacen EndeavourOS, Manjaro, etc., ya que Static Linux todavía
no tiene su propio repo (ver
[staticlinux-base](herramientas/staticlinux-base.md)). `build.sh` comprueba
esto al principio (`pacman -Si calamares`) y para con un mensaje claro en
vez de fallar a mitad de build.

## El ISO offline: empaquetado, no funcional todavía

`profiledir-offline/packages.x86_64` mete en la caché de pacman de la
imagen live todos los paquetes oficiales que aparecen en
`packages/lists/*.list` (base + los 4 entornos + los 8 sabores + los 3
perfiles de privacidad). Eso no es lo mismo que hacer que las llamadas
`pacman -S` en vivo de Calamares (`basepkgs`, `entorno-pkgs`, `sabores`,
`privacidad-apply`) lean de esa caché en vez de tirar de red durante la
instalación — falta esa parte (un `CacheDir` apuntado al punto de montaje
del ISO, o un repo local, antes de que corra `basepkgs`). Hasta que eso
exista, las dos ISOs necesitan red al instalar; la offline solo lleva ya
los paquetes descargados, lista para quien complete ese cableado.

Diez paquetes de `packages/lists/*.list` son solo-AUR (`paru`, `ttf-outfit`,
`otf-space-grotesk`, `nwg-dock-hyprland`, `davinci-resolve`, `thonny`,
`heroic-games-launcher-bin`, `proton-ge-custom-bin`, `joplin-desktop`,
`bridge-utils`) y tienen el mismo problema que `calamares` para el
empaquetado offline.

## Sin probar en hardware real

Nada de esto se ha construido de verdad esta sesión — sin máquina Arch
disponible (`archiso`/`mkarchiso` tampoco se pueden instalar en este
sandbox). Verificado con lo que sí había a mano: sintaxis de `build.sh`,
el ensamblado del `airootfs/` corrido de punta a punta contra un directorio
de prueba, y cada nombre de paquete de ambos `packages.x86_64` contrastado
contra `archlinux.org/packages/search/json`. Un `sudo ./build.sh online`
real, en Arch de verdad, es el siguiente paso.
