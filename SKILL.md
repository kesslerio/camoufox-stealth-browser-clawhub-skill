---
name: camoufox-stealth-browser
homepage: https://github.com/kesslerio/camoufox-stealth-browser-clawhub-skill
description: C++ level anti-bot browser automation using Camoufox (patched Firefox). Browser workflows prefer camoufox-nixos on NixOS hosts and fall back to distrobox plus pybox on compatible Linux setups. Use when standard Playwright or Selenium gets blocked by Cloudflare, Datadome, Airbnb, Yelp, or similar anti-bot systems. NOT for normal browser automation.
metadata:
  openclaw:
    emoji: "🦊"
    requires:
      bins: []
      env: []
---

# Camoufox Stealth Browser 🦊

Camoufox is the stealth lane for hostile sites. It patches Firefox at the browser level instead of bolting JavaScript tricks on top after launch.

## Why Camoufox

| Approach | Patch level | Typical weakness |
|----------|-------------|------------------|
| **Camoufox** | Browser/runtime | Harder to fingerprint with timing and JS consistency checks |
| undetected-chromedriver | JS/runtime glue | Timing and environment mismatches |
| puppeteer-stealth | JS injection | Patches land after page startup |
| playwright-stealth | JS injection | Same class of weakness |

## Runtime Selection

The skill now uses this order for **browser** workflows:

1. `camoufox-nixos`
2. `distrobox` with `pybox`
3. clear setup failure if neither exists

`curl_cffi` is unchanged. It remains the API-only lane and still relies on the legacy distrobox setup in this repo.

## Quick Start

### Browser workflows

The browser scripts self-detect runtime. Use them directly:

```bash
python scripts/camoufox-fetch.py "https://example.com" --headless

python scripts/camoufox-session.py \
  --profile economist \
  --status "https://www.economist.com"
```

### Legacy/API setup

If `camoufox-nixos` is missing, or if you need the `curl_cffi` lane, run:

```bash
bash scripts/setup.sh
```

That script configures the distrobox fallback when `pybox` is available and tells you what is missing when it is not.

## When To Use

- Standard Playwright or Selenium gets blocked
- The site shows Cloudflare challenge loops
- You need persistent authenticated browsing for hostile or paywalled sites
- You need actual stealth rather than generic browser automation

Do **not** use this skill for ordinary browsing or generic site testing. Use your normal browser automation tool for that.

## Workflow Summary

### Protected-page fetch

```bash
python scripts/camoufox-fetch.py \
  "https://www.yelp.com/biz/example" \
  --headless \
  --wait 8 \
  --screenshot yelp.png \
  --output yelp.html
```

### Persistent session

```bash
# Interactive login
python scripts/camoufox-session.py \
  --profile airbnb \
  --login "https://www.airbnb.com/account-settings"

# Reuse saved session
python scripts/camoufox-session.py \
  --profile airbnb \
  --headless "https://www.airbnb.com/trips"

# Check session status
python scripts/camoufox-session.py \
  --profile airbnb \
  --status "https://www.airbnb.com"
```

## State Model

Browser profile state now depends on the selected runtime:

- **Host-native (`camoufox-nixos`)**: `~/.cache/camoufox-nixos`
- **Legacy distrobox fallback**: `~/.stealth-browser/profiles/<name>/`

Implications:

- Persistent session reuse still works in both lanes.
- `--import-cookies` is a legacy fallback feature. If you ask for it without the distrobox lane, the script fails clearly instead of pretending parity.
- `--export-cookies` continues to work.

## `curl_cffi` Lane

`curl_cffi` remains the API-only path. It is useful when:

- there is no browser interaction requirement
- you already know the API endpoint
- browser overhead would be wasted

Current repo guidance for it is still the legacy distrobox path:

```bash
distrobox enter pybox -- python3.14 scripts/curl-api.py "https://api.example.com"
```

## Non-NixOS And Missing Runtime

- **NixOS hosts with `camoufox-nixos`**: browser lane is host-native by default
- **Other Linux hosts**: use the distrobox fallback
- **macOS / Windows**: `camoufox-nixos` is not the portability story; the repo’s portable browser guidance is still the distrobox fallback where available

This skill does **not** try to teach every machine how to recreate `camoufox-nixos`. That wrapper is host-specific.

## Proxy Reminder

For Airbnb, Yelp, Datadome, and similar targets:

- datacenter IPs often get blocked immediately
- residential or mobile proxies are usually required
- sticky sessions matter more than rotating every request

See [references/proxy-setup.md](references/proxy-setup.md).

## Remote / Headed Login Notes

Interactive login still needs a visible browser window regardless of runtime. If you are remote, use a display-capable setup such as:

- local desktop session
- SSH with display forwarding where supported
- VNC or similar remote desktop

## Troubleshooting

| Problem | Meaning | What to do |
|---------|---------|------------|
| `No supported browser runtime found` | Neither `camoufox-nixos` nor valid distrobox fallback was detected | Install the host wrapper or configure distrobox plus pybox |
| `--import-cookies requires the legacy distrobox fallback` | Host-native lane cannot honestly reproduce that legacy import flow | Use the fallback lane for that operation |
| Browser lane works but `curl-api.py` does not | `curl_cffi` lane is still legacy-path setup in this repo | Run `bash scripts/setup.sh` |
| Immediate block or challenge loop | Proxy quality or behavior issue | Use residential/mobile proxy and increase wait time |

## References

- [README.md](README.md) — repo overview
- [references/proxy-setup.md](references/proxy-setup.md) — proxy guidance
- [references/fingerprint-checks.md](references/fingerprint-checks.md) — anti-bot fingerprint categories
