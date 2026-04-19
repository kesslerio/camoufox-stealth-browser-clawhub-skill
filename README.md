# Camoufox Stealth Browser 🦊

Camoufox is the stealth-browser skill for sites that block standard automation.

## What Changed

Browser workflows are now:

1. `camoufox-nixos` first on NixOS hosts that have it
2. `distrobox` + `pybox` fallback on compatible Linux setups

`curl_cffi` remains the separate API-only lane and still uses the legacy distrobox setup in this repo.

## Browser Quick Start

```bash
python scripts/camoufox-fetch.py "https://example.com" --headless

python scripts/camoufox-session.py \
  --profile example \
  --status "https://example.com"
```

The browser scripts self-detect runtime. You do not need to decide between host-native and fallback manually.

## Setup

If `camoufox-nixos` is already installed, the browser lane is ready.

If it is missing, or if you also want the `curl_cffi` lane, run:

```bash
bash scripts/setup.sh
```

That script configures the distrobox fallback when possible and tells you what is missing when it cannot.

## Runtime Matrix

| Use case | Preferred lane | Fallback |
|----------|----------------|----------|
| Browser automation on NixOS host | `camoufox-nixos` | `distrobox` + `pybox` |
| Browser automation on other compatible Linux hosts | `distrobox` + `pybox` | none in this repo |
| API-only scraping | `curl_cffi` in distrobox | none in this repo |

## State

Browser state depends on runtime:

- `camoufox-nixos`: `~/.cache/camoufox-nixos`
- legacy distrobox lane: `~/.stealth-browser/profiles/<name>/`

## Notes

- `--export-cookies` still works.
- `--import-cookies` is a legacy fallback feature.
- This repo does not try to make `camoufox-nixos` a generic cross-platform install target.

## Docs

- [SKILL.md](SKILL.md) — full usage guide
- [references/proxy-setup.md](references/proxy-setup.md) — proxy guidance
- [references/fingerprint-checks.md](references/fingerprint-checks.md) — anti-bot fingerprint categories
