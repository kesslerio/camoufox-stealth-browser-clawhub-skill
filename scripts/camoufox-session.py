#!/usr/bin/env python3
"""
Camoufox persistent session manager.

Usage:
    python camoufox-session.py --profile NAME [--login|--headless] [--status]
      [--import-cookies FILE] [--export-cookies FILE] URL
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from runtime_support import (
    BrowserRuntime,
    BrowserRuntimeError,
    detect_browser_runtime,
    find_distrobox_runtime,
    payload_error_message,
    require_ok,
    run_camoufox_nixos,
    run_distrobox_fallback,
)


PROFILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,62}$")
LOGIN_PATH_MARKERS = ("/login", "/signin", "/auth")
TITLE_MARKERS = ("login", "sign in", "sign-in", "authenticate", "sign on")
CONTENT_MARKERS = (
    "login",
    "sign in",
    "sign-in",
    "sign on",
    "authenticate",
    "authentication",
    "access denied",
    "unauthorized",
    "forbidden",
    "verify your identity",
)


def validate_profile_name(name: str) -> str:
    if not name or not PROFILE_RE.match(name):
        raise argparse.ArgumentTypeError(
            "Invalid profile name. Use 1-63 chars: letters, numbers, _ or -."
        )
    return name


def ensure_profile_dir(profile_name: str) -> Path:
    base_dir = Path.home() / ".stealth-browser" / "profiles"
    profile_dir = base_dir / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(profile_dir, 0o700)
    return profile_dir


def chmod_file(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except FileNotFoundError:
        return


def domain_matches(cookie_domain: str, host: str) -> bool:
    if not cookie_domain or not host:
        return False

    cookie_domain = cookie_domain.lower().lstrip(".")
    host = host.lower()
    if host == cookie_domain:
        return True
    return host.endswith("." + cookie_domain)


def filter_cookies_for_host(cookies: Iterable[dict], host: str) -> List[dict]:
    matched = []
    for cookie in cookies:
        domain = cookie.get("domain", "")
        if domain_matches(domain, host):
            matched.append(cookie)
    return matched


def load_cookies(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Cookie file must be a JSON list")
    return data


def save_cookies(path: Path, cookies: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(cookies, handle, indent=2, sort_keys=True)
    chmod_file(path)


def extract_host(url: str) -> str:
    parsed = urlparse(url)
    return parsed.hostname or ""


def login_wall_signals(url: str, title: str, content: str) -> List[str]:
    signals = []
    lower_url = url.lower()
    if any(marker in lower_url for marker in LOGIN_PATH_MARKERS):
        signals.append("url-path")
    lower_title = title.lower()
    if any(marker in lower_title for marker in TITLE_MARKERS):
        signals.append("title")
    lower_content = content.lower()
    if any(marker in lower_content for marker in CONTENT_MARKERS):
        signals.append("content")
    return signals


async def detect_login_wall(page, response) -> Tuple[bool, List[str]]:
    signals = []
    if response is not None:
        status = response.status
        if status in (401, 403):
            signals.append(f"http-{status}")
    try:
        title = await page.title()
    except Exception:
        title = ""
    try:
        content = await page.content()
    except Exception:
        content = ""
    try:
        password_field = await page.query_selector(
            "input[type='password'], input[name='password'], "
            "input[autocomplete='current-password']"
        )
    except Exception:
        password_field = None
    if password_field is not None:
        signals.append("password-form")

    signals.extend(login_wall_signals(page.url, title, content))
    return bool(signals), signals


async def wait_for_enter(prompt: str) -> None:
    await asyncio.get_running_loop().run_in_executor(None, lambda: input(prompt))


def print_runtime_error(message: str) -> int:
    print(f"Error: {message}", file=sys.stderr)
    return 1


def filter_storage_state_for_host(path: Path, host: str) -> List[dict]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    cookies = payload.get("cookies", [])
    if not isinstance(cookies, list):
        return []
    return filter_cookies_for_host(cookies, host)


def detect_login_wall_host_native(page: dict, content: str, has_password_field: bool) -> Tuple[bool, List[str]]:
    signals = login_wall_signals(page.get("url", ""), page.get("title", ""), content)
    if has_password_field:
        signals.append("password-form")
    return bool(signals), signals


def load_page_state_host_native(
    runtime: BrowserRuntime,
    session_id: str,
) -> Tuple[dict, str, bool]:
    html_payload = run_camoufox_nixos(
        runtime,
        ["eval", "--session", session_id, "document.documentElement.outerHTML"],
    )
    require_ok(html_payload, "Failed to read page HTML.")
    content = html_payload.get("data", {}).get("result", "")
    if not isinstance(content, str):
        content = json.dumps(content)

    password_payload = run_camoufox_nixos(
        runtime,
        [
            "eval",
            "--session",
            session_id,
            "Boolean(document.querySelector(\"input[type='password'], input[name='password'], input[autocomplete='current-password']\"))",
        ],
    )
    require_ok(password_payload, "Failed to inspect page login state.")
    has_password_field = bool(password_payload.get("data", {}).get("result"))
    return html_payload.get("page") or {}, content, has_password_field


def export_cookies_host_native(
    runtime: BrowserRuntime,
    session_id: str,
    host: str,
    export_path: Path,
) -> None:
    with tempfile.NamedTemporaryFile(prefix="camoufox-storage-", suffix=".json", delete=False) as handle:
        storage_path = Path(handle.name)
    try:
        storage_payload = run_camoufox_nixos(
            runtime,
            ["storage-state", "--session", session_id, str(storage_path)],
        )
        require_ok(storage_payload, "Failed to export storage state.")
        matched = filter_storage_state_for_host(storage_path, host)
        save_cookies(export_path, matched)
        print(f"🍪 Exported {len(matched)} cookies to: {export_path}")
    finally:
        storage_path.unlink(missing_ok=True)


def run_session_host_native(
    runtime: BrowserRuntime,
    url: str,
    profile_name: str,
    login_mode: bool,
    headless: bool,
    export_cookies: Optional[Path],
    import_cookies: Optional[Path],
    status_only: bool,
) -> int:
    if import_cookies:
        fallback = find_distrobox_runtime()
        if fallback is not None:
            return run_distrobox_fallback(Path(__file__).resolve(), sys.argv[1:], fallback)
        print("Error: --import-cookies requires the legacy distrobox fallback.", file=sys.stderr)
        return 2

    host = extract_host(url)
    if not host:
        print("Error: Invalid URL (missing host)")
        return 2

    print("🥷 Starting Camoufox persistent session (NixOS-native runtime)...")

    open_args = ["open", "--profile", profile_name]
    if headless or status_only or not login_mode:
        open_args.append("--headless")
    open_args.append(url)

    open_payload = run_camoufox_nixos(runtime, open_args)
    require_ok(open_payload, "Failed to open session.")
    session_id = open_payload.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        raise BrowserRuntimeError("camoufox-nixos did not return a session id.")

    try:
        print(f"📡 Navigating to: {url}")
        time.sleep(2)

        page, content, has_password_field = load_page_state_host_native(runtime, session_id)
        login_wall, signals = detect_login_wall_host_native(page, content, has_password_field)
        if login_wall:
            print(f"🔒 Login wall signals: {', '.join(signals)}")
        else:
            print("✅ No obvious login wall detected")

        if status_only:
            with tempfile.NamedTemporaryFile(prefix="camoufox-status-", suffix=".json", delete=False) as handle:
                storage_path = Path(handle.name)
            try:
                storage_payload = run_camoufox_nixos(
                    runtime,
                    ["storage-state", "--session", session_id, str(storage_path)],
                )
                require_ok(storage_payload, "Failed to inspect stored cookies.")
                matched = filter_storage_state_for_host(storage_path, host)
            finally:
                storage_path.unlink(missing_ok=True)
            print(f"📦 Profile: {profile_name}")
            print(f"   Stored cookies for {host}: {len(matched)}")
            return 0

        if login_mode:
            print("🧭 Login mode enabled (headed).")
            if login_wall:
                print("   Complete login in the open browser window.")
            asyncio.run(wait_for_enter("Press Enter to save session and exit... "))

        if export_cookies:
            export_cookies_host_native(runtime, session_id, host, export_cookies)

        return 0
    finally:
        close_payload = run_camoufox_nixos(runtime, ["close", "--session", session_id])
        if close_payload.get("ok") is not True:
            message = payload_error_message(close_payload, "Failed to close session.")
            print(f"Warning: {message}", file=sys.stderr)


async def run_session(
    url: str,
    profile_name: str,
    login_mode: bool,
    headless: bool,
    export_cookies: Optional[Path],
    import_cookies: Optional[Path],
    status_only: bool,
) -> int:
    from camoufox.async_api import AsyncCamoufox

    profile_dir = ensure_profile_dir(profile_name)
    host = extract_host(url)
    if not host:
        print("Error: Invalid URL (missing host)")
        return 2

    print("🥷 Starting Camoufox persistent session...")
    config = {
        "headless": headless,
        "persistent_context": True,
        "user_data_dir": str(profile_dir),
    }

    async with AsyncCamoufox(**config) as context:
        if import_cookies:
            try:
                all_cookies = load_cookies(import_cookies)
            except Exception as exc:
                print(f"Error: Failed to load cookies: {exc}")
                return 2
            matched = filter_cookies_for_host(all_cookies, host)
            if matched:
                try:
                    await context.add_cookies(matched)
                    print(f"🍪 Imported {len(matched)} cookies for {host}")
                except Exception as exc:
                    print(f"Error: Failed to import cookies (invalid format?): {exc}")
                    return 2
            else:
                print(f"🍪 No cookies matched {host}")

        page = await context.new_page()
        print(f"📡 Navigating to: {url}")
        response = await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        login_wall, signals = await detect_login_wall(page, response)
        if login_wall:
            print(f"🔒 Login wall signals: {', '.join(signals)}")
        else:
            print("✅ No obvious login wall detected")

        if status_only:
            cookies = await context.cookies()
            matched = filter_cookies_for_host(cookies, host)
            print(f"📦 Profile: {profile_name}")
            print(f"   Stored cookies for {host}: {len(matched)}")
            return 0

        if login_mode:
            print("🧭 Login mode enabled (headed).")
            if login_wall:
                print("   Complete login in the open browser window.")
            await wait_for_enter("Press Enter to save session and exit... ")

        if export_cookies:
            cookies = await context.cookies()
            matched = filter_cookies_for_host(cookies, host)
            save_cookies(export_cookies, matched)
            print(f"🍪 Exported {len(matched)} cookies to: {export_cookies}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Camoufox persistent session manager (profile-based)"
    )
    parser.add_argument("url", help="Target URL")
    parser.add_argument(
        "--profile",
        required=True,
        type=validate_profile_name,
        help="Profile name (letters, numbers, _ or -)",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Headed mode for manual login",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run headless using saved session",
    )
    parser.add_argument(
        "--export-cookies",
        help="Export cookies to file",
    )
    parser.add_argument(
        "--import-cookies",
        help="Import cookies from file",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show session status for URL",
    )
    parser.add_argument(
        "--runtime",
        choices=("auto", "legacy"),
        default="auto",
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    if args.login and args.headless:
        print("Error: --login and --headless are mutually exclusive")
        return 2

    export_path = Path(args.export_cookies).expanduser() if args.export_cookies else None
    import_path = Path(args.import_cookies).expanduser() if args.import_cookies else None

    headless = args.headless
    if args.login:
        headless = False

    try:
        if args.runtime == "legacy":
            return asyncio.run(
                run_session(
                    url=args.url,
                    profile_name=args.profile,
                    login_mode=args.login,
                    headless=headless,
                    export_cookies=export_path,
                    import_cookies=import_path,
                    status_only=args.status,
                )
            )

        selection = detect_browser_runtime()
        runtime = selection.runtime
        if runtime is None:
            return print_runtime_error(selection.error_message or "No supported browser runtime found.")

        if runtime.kind == "distrobox":
            return run_distrobox_fallback(Path(__file__).resolve(), sys.argv[1:], runtime)

        return run_session_host_native(
            runtime=runtime,
            url=args.url,
            profile_name=args.profile,
            login_mode=args.login,
            headless=headless,
            export_cookies=export_path,
            import_cookies=import_path,
            status_only=args.status,
        )
    except ImportError:
        return print_runtime_error("camoufox not installed in the selected legacy runtime.")
    except BrowserRuntimeError as exc:
        return print_runtime_error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
