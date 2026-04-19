# Camoufox Stealth Browser 🦊

Camoufox is the browser-stealth skill for hostile sites that block standard automation.

## Primary Use

Browser workflows are now:

1. `camoufox-nixos` first on NixOS hosts that have it
2. `distrobox` + `pybox` fallback on compatible Linux setups

This is the repo's primary promise. The `curl_cffi` helper still exists, but it is a secondary API-only lane rather than the main routing target.

## Browser Quick Start

```bash
./scripts/camoufox-fetch.py "https://example.com" --headless

./scripts/camoufox-session.py \
  --profile example \
  --status "https://example.com"
```

The browser scripts self-detect runtime. You do not need to decide between host-native and fallback manually, and you should not describe this as importing `camoufox` into system Python.

## Setup

If `camoufox-nixos` is already installed, the browser lane is ready.

If it is missing, or if you also want the optional API helper lane, run:

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

## State Ownership

This skill owns no durable state. Browser state depends on the selected runtime:

- `camoufox-nixos`: `~/.cache/camoufox-nixos`
- legacy distrobox lane: `~/.stealth-browser/profiles/<name>/`

## Gotchas

Read [references/gotchas.md](references/gotchas.md) before assuming parity between the host-native browser lane and the legacy distrobox lane.

## Secondary API Helper

- `--export-cookies` still works.
- `--import-cookies` is a legacy fallback feature.
- `curl_cffi` stays available for API-only scraping, but it is not the main reason this skill exists.
- This repo does not try to make `camoufox-nixos` a generic cross-platform install target.

## Verification

Skill/package checks:

```bash
bash scripts/lint-skill.sh
bash scripts/test-discovery.sh
```

Browser adapter checks:

```bash
bash tests/runtime-selection.sh
bash tests/camoufox-fetch-adapter.sh
bash tests/camoufox-session-adapter.sh
```

## Docs

- [SKILL.md](SKILL.md) — full usage guide
- [references/gotchas.md](references/gotchas.md) — recurring footguns and local assumptions
- [references/proxy-setup.md](references/proxy-setup.md) — proxy guidance
- [references/fingerprint-checks.md](references/fingerprint-checks.md) — anti-bot fingerprint categories
