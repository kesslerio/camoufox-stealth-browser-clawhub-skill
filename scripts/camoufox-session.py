#!/usr/bin/env python3
"""
Camoufox with persistent sessions (cookies + localStorage).
Login once, stay logged in across runs.

Usage:
    # First run: login manually (headed mode)
    python camoufox-session.py "https://airbnb.com" --profile airbnb --login
    
    # Subsequent runs: use saved session (headless)
    python camoufox-session.py "https://airbnb.com/trips" --profile airbnb --headless
    
    # Export cookies to JSON
    python camoufox-session.py --profile airbnb --export-cookies cookies.json
    
    # Import cookies from JSON
    python camoufox-session.py "https://airbnb.com" --profile airbnb --import-cookies cookies.json

Options:
    --profile NAME    Profile name (stored in ~/.stealth-browser/profiles/NAME/)
    --login           Interactive login mode (headed, waits for you to login)
    --headless        Run headless (use after login)
    --export-cookies  Export session cookies to JSON file
    --import-cookies  Import cookies from JSON file
    --wait N          Wait N seconds after page load (default: 5)
    --screenshot FILE Save screenshot
    --output FILE     Save HTML to file
    --proxy URL       Use proxy
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

try:
    from camoufox.async_api import AsyncCamoufox
except ImportError:
    print("Error: camoufox not installed. Run:")
    print("  pip install camoufox")
    print("  camoufox fetch")
    sys.exit(1)

# Default profiles directory
PROFILES_DIR = Path.home() / ".stealth-browser" / "profiles"


def get_profile_path(name: str) -> Path:
    """Get path to profile directory."""
    path = PROFILES_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cookies_path(profile_name: str) -> Path:
    """Get path to cookies JSON file for a profile."""
    return get_profile_path(profile_name) / "cookies.json"


async def export_cookies(profile_name: str, output_file: str):
    """Export cookies from a profile to JSON file."""
    cookies_path = get_cookies_path(profile_name)
    
    if not cookies_path.exists():
        print(f"❌ No cookies found for profile '{profile_name}'")
        print(f"   Run with --login first to create a session")
        sys.exit(1)
    
    with open(cookies_path, 'r') as f:
        cookies = json.load(f)
    
    with open(output_file, 'w') as f:
        json.dump(cookies, f, indent=2)
    
    print(f"✅ Exported {len(cookies)} cookies to {output_file}")


async def interactive_login(url: str, profile_name: str, proxy: str = None):
    """Open browser for manual login, save session when done."""
    profile_path = get_profile_path(profile_name)
    cookies_path = get_cookies_path(profile_name)
    
    print(f"🔐 Opening browser for login...")
    print(f"   Profile: {profile_name}")
    print(f"   URL: {url}")
    print()
    print("   👉 Login manually in the browser window")
    print("   👉 Press Enter here when done to save session")
    print()
    
    config = {"headless": False}
    if proxy:
        if "@" in proxy:
            auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
            host_part = proxy.split("@")[1]
            user, password = auth_part.split(":")
            host, port = host_part.split(":")
            config["proxy"] = {
                "server": f"http://{host}:{port}",
                "username": user,
                "password": password,
            }
        else:
            config["proxy"] = {"server": proxy}
    
    async with AsyncCamoufox(**config) as browser:
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        
        # Wait for user to login
        input("\n⏳ Press Enter after you've logged in...")
        
        # Get cookies
        cookies = await page.context.cookies()
        
        # Save cookies
        with open(cookies_path, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        # Also save localStorage if possible
        try:
            local_storage = await page.evaluate("() => JSON.stringify(localStorage)")
            ls_path = profile_path / "localStorage.json"
            with open(ls_path, 'w') as f:
                f.write(local_storage)
            print(f"💾 Saved localStorage to {ls_path}")
        except Exception as e:
            print(f"⚠️  Could not save localStorage: {e}")
        
        print(f"✅ Saved {len(cookies)} cookies to {cookies_path}")
        print(f"   Profile '{profile_name}' is ready for headless use")


async def fetch_with_session(url: str, profile_name: str, headless: bool = True,
                             wait: int = 5, screenshot: str = None, 
                             output: str = None, proxy: str = None,
                             import_cookies: str = None):
    """Fetch a page using saved session."""
    cookies_path = get_cookies_path(profile_name)
    profile_path = get_profile_path(profile_name)
    
    # Load cookies
    cookies = []
    if import_cookies:
        with open(import_cookies, 'r') as f:
            cookies = json.load(f)
        print(f"📥 Imported {len(cookies)} cookies from {import_cookies}")
    elif cookies_path.exists():
        with open(cookies_path, 'r') as f:
            cookies = json.load(f)
        print(f"🍪 Loaded {len(cookies)} cookies from profile '{profile_name}'")
    else:
        print(f"⚠️  No saved session for profile '{profile_name}'")
        print(f"   Run with --login first, or use --import-cookies")
    
    config = {"headless": headless}
    if proxy:
        if "@" in proxy:
            auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
            host_part = proxy.split("@")[1]
            user, password = auth_part.split(":")
            host, port = host_part.split(":")
            config["proxy"] = {
                "server": f"http://{host}:{port}",
                "username": user,
                "password": password,
            }
        else:
            config["proxy"] = {"server": proxy}
    
    print(f"🥷 Starting Camoufox ({'headless' if headless else 'headed'})...")
    
    async with AsyncCamoufox(**config) as browser:
        page = await browser.new_page()
        
        # Add cookies before navigation
        if cookies:
            await page.context.add_cookies(cookies)
        
        # Restore localStorage if available
        ls_path = profile_path / "localStorage.json"
        if ls_path.exists():
            try:
                with open(ls_path, 'r') as f:
                    local_storage = json.load(f)
                # Navigate to domain first (required for localStorage)
                await page.goto(url, wait_until="domcontentloaded")
                for key, value in local_storage.items():
                    await page.evaluate(f"localStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                # Reload to apply localStorage
                await page.reload(wait_until="domcontentloaded")
                print(f"💾 Restored localStorage ({len(local_storage)} items)")
            except Exception as e:
                print(f"⚠️  Could not restore localStorage: {e}")
                await page.goto(url, wait_until="domcontentloaded")
        else:
            await page.goto(url, wait_until="domcontentloaded")
        
        print(f"📡 Navigating to: {url}")
        print(f"⏳ Waiting {wait}s...")
        await asyncio.sleep(wait)
        
        title = await page.title()
        print(f"📄 Page title: {title}")
        
        content = await page.content()
        
        # Update saved cookies (session may have been refreshed)
        new_cookies = await page.context.cookies()
        with open(cookies_path, 'w') as f:
            json.dump(new_cookies, f, indent=2)
        
        # Check for login indicators
        if "login" in title.lower() or "sign in" in title.lower():
            print("⚠️  Warning: Page title suggests you may not be logged in")
        
        if screenshot:
            await page.screenshot(path=screenshot, full_page=True)
            print(f"📸 Screenshot saved: {screenshot}")
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"💾 HTML saved: {output}")
        
        print(f"\n✅ Success! Page loaded ({len(content)} bytes)")
        return content


def main():
    parser = argparse.ArgumentParser(description="Camoufox with persistent sessions")
    parser.add_argument("url", nargs="?", help="URL to fetch")
    parser.add_argument("--profile", required=True, help="Profile name for session storage")
    parser.add_argument("--login", action="store_true", help="Interactive login mode (headed)")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--export-cookies", metavar="FILE", help="Export cookies to JSON file")
    parser.add_argument("--import-cookies", metavar="FILE", help="Import cookies from JSON file")
    parser.add_argument("--wait", type=int, default=5, help="Wait time in seconds (default: 5)")
    parser.add_argument("--screenshot", help="Save screenshot to file")
    parser.add_argument("--output", help="Save HTML to file")
    parser.add_argument("--proxy", help="Proxy URL (http://user:pass@host:port)")
    
    args = parser.parse_args()
    
    # Export cookies mode
    if args.export_cookies:
        asyncio.run(export_cookies(args.profile, args.export_cookies))
        return
    
    # Require URL for other modes
    if not args.url:
        parser.error("URL is required (unless using --export-cookies)")
    
    # Login mode
    if args.login:
        asyncio.run(interactive_login(args.url, args.profile, args.proxy))
        return
    
    # Fetch mode
    asyncio.run(fetch_with_session(
        url=args.url,
        profile_name=args.profile,
        headless=args.headless,
        wait=args.wait,
        screenshot=args.screenshot,
        output=args.output,
        proxy=args.proxy,
        import_cookies=args.import_cookies
    ))


if __name__ == "__main__":
    main()
