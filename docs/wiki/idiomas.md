# Idiomas

Static Linux habla **18 idiomas**: español (el original), inglés, catalán,
euskera, gallego, francés, alemán, italiano, portugués, portugués de Brasil,
neerlandés, polaco, ruso, ucraniano, turco, japonés, coreano y chino
simplificado. Si tu idioma no está, todo sale en inglés.

Se traduce todo lo que es de Static Linux:

- el instalador: páginas de escritorio, tema, sabores y privacidad, la
  presentación mientras instala y los pasos que va mostrando;
- sl-welcome, los ajustes rápidos (sl-quick), la guía de atajos de Hyprland,
  las capturas y la barra de Hyprland;
- `sl-ctl` y `sl-game`;
- los nombres y descripciones de temas, catálogo y lanzadores;
- la pantalla de bloqueo de Hyprland y la petición de contraseña del disco al
  arrancar.

El idioma es el del sistema (`LANG`, el que eliges en el instalador). Para
probar otro en una sola orden: `LANGUAGE=fr sl-ctl perf`.

## Cómo se traduce

Los textos originales están en español dentro del código y se extraen con
gettext (dominio `static-linux`):

```bash
python3 i18n/extract.py     # actualiza i18n/static-linux.pot y los i18n/po/*.po
bash i18n/build.sh          # compila los .mo y escribe las traducciones del instalador
```

Para añadir un idioma, copia `i18n/static-linux.pot` a `i18n/po/<código>.po`,
traduce los `msgstr` y abre un PR. `build.sh` lo incluye solo. Ver
[Contribuir](contribuir.md).
