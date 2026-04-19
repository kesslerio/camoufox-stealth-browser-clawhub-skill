#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "list" ]]; then
  if [[ "${FAKE_DISTROBOX_NO_PYBOX:-0}" == "1" ]]; then
    echo "NAME | IMAGE"
    exit 0
  fi
  echo "NAME | IMAGE"
  echo "pybox | fedora:latest"
  exit 0
fi

if [[ "${1:-}" == "enter" ]]; then
  shift
  if [[ "${1:-}" == "pybox" ]]; then
    shift
  fi
  if [[ "${1:-}" == "--" ]]; then
    shift
  fi
  printf '%s\n' "FAKE DISTROBOX EXEC ${FAKE_DISTROBOX_EXEC_TEXT:-legacy fallback}"
  printf '%s\n' "$*" > "${FAKE_DISTROBOX_LOG:-/dev/null}"
  exit 0
fi

echo "unsupported fake distrobox invocation: $*" >&2
exit 1
