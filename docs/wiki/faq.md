# FAQ

## ¿Por qué Arch y no Artix/Debian/Ubuntu?

Decisión ya tomada, no se reabre (ver `AGENTS.md § DO NOT RE-SUGGEST`). Base
rodante, AUR para todo lo que no está en repos oficiales, y es la base sobre
la que ya está construido `sl-detect`.

## ¿Por qué no hay Secure Boot?

No está soportado, por decisión de diseño. Firmar cada release para Secure
Boot (MOK, shim, llaves propias) es mantenimiento continuo que este proyecto
no está asumiendo todavía. El job de Calamares `luks` incluso avisa si
detecta Secure Boot activado en el firmware live, porque GRUB sin firmar +
Secure Boot puede dejar el sistema instalado sin arrancar.

## ¿Por qué el techo de RAM es 4 GB?

Porque el hardware que Static Linux quiere revivir vive ahí o por debajo —
el propio [iMedia S2883](hardware/imedia-s2883.md) tiene 3.64 GB usables. Si
tu equipo tiene más RAM, sigue funcionando perfectamente; el "techo" es
sobre qué hardware se diseña y se prueba primero, no un límite duro.

## ¿Por qué LUKS2 no se recomienda en hardware tipo J1900?

Cifrado + HDD es un golpe de rendimiento serio, y ese es exactamente el
hardware que este proyecto prioriza. Sigue siendo una opción — el
instalador no la bloquea — pero `sl-detect` no la recomienda por defecto en
hardware de esa clase, y el job `luks` avisa (no bloquea) si detectas
cifrado en un equipo así.

## ¿Por qué Brave y no Firefox?

Decisión de marca ya tomada — en concreto **Brave Origin** (canal Release):
la variante recortada de Brave, solo con lo esencial de privacidad, sin
wallet, rewards ni VPN. Firefox está disponible en el
[catálogo de `sl-welcome`](herramientas/sl-welcome.md) si lo prefieres.

## ¿Cero telemetría de verdad, o "cero telemetría, con opción de activarla"?

Cero, absoluto, en los tres perfiles de privacidad. No es un perfil — es la
línea base.

## ¿Cómo pruebo en mi propia máquina si no tengo el hardware de referencia?

Cualquier hardware sirve — de hecho es lo que más falta (ver
[Contribuir](contribuir.md)). Corre `sl-detect --all` y compáralo con lo que
esperarías; si algo no cuadra, es un issue con la salida completa adjunta,
tal como pide `CONTRIBUTING.md`.
