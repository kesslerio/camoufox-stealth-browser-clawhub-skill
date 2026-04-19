# Gotchas

These are the recurring footguns for this repo. They matter more than generic advice.

## Runtime Framing

- Do not say the browser lane failed because system Python cannot import the `camoufox` module.
- Do not narrate browser execution as "switching to the proper runtime."
- Run `./scripts/camoufox-fetch.py` or `./scripts/camoufox-session.py` directly.
- Those wrapper scripts detect `camoufox-nixos` first and fall back automatically when the legacy distrobox lane is valid.

## Browser Lane Vs API Helper

- The primary skill contract is hostile-site browser automation.
- `curl_cffi` is still present, but it is a secondary API-only helper.
- If the task needs login, session reuse, page interaction, or anti-bot browser behavior, use the browser lane, not `curl-api.py`.

## State Ownership

- This skill owns no durable state.
- `camoufox-nixos` owns host-native browser state under `~/.cache/camoufox-nixos`.
- The legacy distrobox browser lane owns its own profile state under `~/.stealth-browser/profiles/<name>/`.
- Do not treat those runtime-owned directories as skill-managed state.

## Headed Login Expectations

- Interactive login still needs a visible browser window.
- `--login` is for headed manual session establishment, not headless auth magic.
- If you are remote, you still need a display-capable setup such as a local desktop session, forwarding that actually works, or VNC.

## Fallback Assumptions

- The distrobox lane is a Linux compatibility path, not a universal cross-platform story.
- `camoufox-nixos` is host-specific. This repo does not explain how to recreate it on macOS or Windows.
- If neither `camoufox-nixos` nor distrobox + `pybox` exists, browser workflows should fail clearly instead of guessing.

## Legacy-Only Features

- `--import-cookies` is a legacy fallback feature.
- Do not assume the host-native browser lane can honestly reproduce every old distrobox-era storage trick.
- `--export-cookies` still works, but the storage model is different between runtimes.
