# Contribuir

La guía completa vive en
[`CONTRIBUTING.md`](https://github.com/KCRooty/static-linux/blob/main/CONTRIBUTING.md)
en la raíz del repositorio — esta página es solo el resumen rápido.

## Reglas de oro

- Toda contribución compatible con **GPL-3.0**.
- Abre un issue **antes** de empezar un cambio grande — discutir el enfoque
  primero.
- Todo tweak de `sl-ctl` y toda acción de privacidad necesita
  backup/restore automático. Ningún cambio irreversible.
- Prueba en hardware real o una VM antes de abrir el PR.

## Dónde ayuda más hace falta ahora mismo

- **`sl-detect`**: reglas de GPU para hardware raro y placas ARM.
- **Entornos**: `hyprland-astal-full`/`lite` y `openbox-minimal` están
  escritos pero sin probar en hardware real todavía — cualquier prueba en
  vivo (o corrección de lo que falle) es oro.
- **Calamares**: página de selección de sabores/privacidad, y completar los
  módulos `entorno`/`privacidad` (hoy son stubs vacíos).
- **Branding**: el acento no llega todavía al borde de ventana en Openbox ni
  en Hyprland (ver [Branding y acentos § huecos conocidos](branding-accents.md#huecos-conocidos)).
- **Documentación**: páginas de esta wiki en otros idiomas.
- **ARM64**: RPi 4/5, Pinebook Pro, RK3588 — `sl-detect` ya sabe detectar
  estas GPUs por device-tree, falta probarlo en las placas reales.

## Reportar un bug

Usa las [plantillas de GitHub Issues](https://github.com/KCRooty/static-linux/issues/new/choose).
Incluye siempre:

- Salida de `sl-detect --all`
- Logs relevantes de `journalctl`
- Modelo de hardware
- Qué ISO (online/offline) y su fecha de build
