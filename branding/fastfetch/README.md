# fastfetch branding

Static Linux ships a minimal branded `fastfetch` as the system default.
Look reference: Archcraft — small logo, few fields, dim keys, breathing room.

```
                   Static Linux   fast. private. yours.
   █████  █████    core@staticlinux
   █      █        ──────────────────────────────
   █████  █████      distro  Static Linux x86_64
       █  █          kernel  6.18.50-2-lts
   █████  █          uptime  1h 53m
                     pkgs    577
                     wm      xfwm4
                     shell   bash 5.3.15
                     memory  1.2 GiB / 3.6 GiB (34%)

                   ● ● ● ● ● ● ● ●
```

`distro` says **Static Linux** because `/etc/os-release` is replaced —
see [`packages/staticlinux-base/os-release`](../../packages/staticlinux-base/os-release).

## Files

| File | Installs to | What |
|---|---|---|
| `config.jsonc` | `/etc/fastfetch/config.jsonc` | the minimal config above |
| `logo-sf-block.fastfetch` | `/usr/share/static-linux/fastfetch/` | **default** — SF monogram, `$1` green (S) / `$2` white (F) |
| `logo-sf-mono.fastfetch` | idem | 3-row SF monogram, more compact |
| `logo-sf-round.fastfetch` | idem | 3-row SF with rounded strokes |
| `logo-static-linux.fastfetch` | idem | `figlet -f slant "static linux"`, one colour |
| `logo-static.fastfetch` / `logo-sf.fastfetch` | idem | slant "Static" / "SF" |
| `logo-*.txt` | — | raw source (figlet output / plain monogram) |

`$1` / `$2` are fastfetch colour placeholders; colours are set in
`config.jsonc` under `logo.color`.

## Switch logo / tweak

Edit `logo.source` in `config.jsonc` (system) or copy it per-user:

```bash
mkdir -p ~/.config/fastfetch && cp /etc/fastfetch/config.jsonc ~/.config/fastfetch/
```

## Regenerate art

```bash
# figlet variants
figlet -f slant "static linux" > logo-static-linux.txt
sed 's/^/$1/' logo-static-linux.txt > logo-static-linux.fastfetch

# the SF block monogram is hand-drawn with U+2588 / U+2580 / U+2584
```

## TODO

- Nerd-font icon variant of the config, once a nerd font is packaged.
- Half-block SF with a true diagonal bicolour split (current split is vertical).
