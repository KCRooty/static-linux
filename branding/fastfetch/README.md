# fastfetch branding

Static Linux ships a branded `fastfetch` as the system default.

## Files

| File | Installs to | What |
|---|---|---|
| `config.jsonc` | `/etc/fastfetch/config.jsonc` | system default config (Signal Green keys + title, tagline line, grouped modules) |
| `logo-static-linux.fastfetch` | `/usr/share/static-linux/fastfetch/` | **default logo** — `figlet -f slant "static linux"`, one colour (`$1` = Signal Green) |
| `logo-static.fastfetch` | idem | `figlet -f slant "Static"` — narrower |
| `logo-sf.fastfetch` | idem | `figlet -f slant "SF"` — compact, one colour |
| `logo-sf-bicolor.fastfetch` | idem | `SF` with `$1` green (S) / `$2` white (F) — the diagonal-split monogram nod |
| `logo-*.txt` | — | raw figlet output, no colour markup (source of truth) |

The `.fastfetch` files use fastfetch colour placeholders: every line is
prefixed with `$1` (and `$2` for the bicolor one). Colours are set in
`config.jsonc` under `logo.color`, or on the CLI with `--logo-color-1`.

## Switch the logo

Edit `logo.source` in `config.jsonc`, or per-user:

```bash
mkdir -p ~/.config/fastfetch
cp /etc/fastfetch/config.jsonc ~/.config/fastfetch/
# then change "source" to logo-sf-bicolor.fastfetch, etc.
```

## Regenerate the art

```bash
figlet -f slant "static linux" > logo-static-linux.txt
sed 's/^/$1/' logo-static-linux.txt > logo-static-linux.fastfetch
```

`slant` is a core figlet font (package `figlet`). Other candidates tried:
`standard` (the "ST" block), `small`, `smslant`.

## TODO (branding pass)

- Hand-drawn SF monogram in half-block characters (▀▄█) with a true diagonal
  bicolour split — the real brand mark, replacing the figlet nod.
