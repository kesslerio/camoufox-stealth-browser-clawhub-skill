#!/usr/bin/env bash
set -euo pipefail

echo "🥷 Checking stealth browser runtimes..."
echo ""

have_host_native=0
have_distrobox=0

if command -v camoufox-nixos >/dev/null 2>&1; then
  have_host_native=1
  echo "✅ Browser lane ready: camoufox-nixos detected"
else
  echo "ℹ️  camoufox-nixos not found"
fi

if command -v distrobox >/dev/null 2>&1; then
  if distrobox list | grep -q "pybox"; then
    have_distrobox=1
    echo "✅ Legacy fallback available: distrobox + pybox detected"
    echo "📦 Installing fallback/API packages in pybox..."
    distrobox enter pybox -- python3.14 -m pip install --upgrade pip
    distrobox enter pybox -- python3.14 -m pip install camoufox curl_cffi
    echo "🦊 Installing Camoufox browser in pybox..."
    distrobox enter pybox -- python3.14 -c "import camoufox; camoufox.install()"
    echo "🔧 Installing optional headed-browser deps in pybox..."
    distrobox enter pybox -- sudo dnf install -y gtk3 libXt nss at-spi2-atk cups-libs libdrm mesa-libgbm 2>/dev/null || true
  else
    echo "ℹ️  distrobox is installed but pybox is missing"
    echo "   Create it with: distrobox create --name pybox --image fedora:latest"
  fi
else
  echo "ℹ️  distrobox not found"
fi

echo ""

if [[ "$have_host_native" -eq 0 && "$have_distrobox" -eq 0 ]]; then
  echo "❌ No supported runtime is ready."
  echo "   Browser default: install camoufox-nixos"
  echo "   Fallback/API lane: install distrobox and create pybox, then rerun this script"
  exit 1
fi

echo "Runtime summary:"
if [[ "$have_host_native" -eq 1 ]]; then
  echo "  - Browser default: camoufox-nixos"
fi
if [[ "$have_distrobox" -eq 1 ]]; then
  echo "  - Browser fallback: distrobox + pybox"
  echo "  - API lane: curl_cffi in distrobox + pybox"
fi

echo ""
echo "Try browser fetch with:"
echo "  python scripts/camoufox-fetch.py https://example.com --headless"
echo ""
echo "Try session status with:"
echo "  python scripts/camoufox-session.py --profile demo --status https://example.com"
echo ""
if [[ "$have_distrobox" -eq 1 ]]; then
  echo "Try the API lane with:"
  echo "  distrobox enter pybox -- python3.14 scripts/curl-api.py https://api.example.com"
  echo ""
fi
echo "✅ Setup guidance complete"
