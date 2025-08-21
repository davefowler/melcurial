#!/usr/bin/env bash
set -euo pipefail

# mel installer
# - Installs the single-file CLI to a writable bin directory
# - Works on macOS and Linux
# - Defaults to /usr/local/bin if writable; otherwise falls back to ~/.local/bin
# - Does NOT modify your PATH by default. To opt-in, set MEL_ADD_TO_PATH=1
# - You can pass a custom install dir as the first argument

REPO_RAW_BASE="https://raw.githubusercontent.com/davefowler/melcurial/main"
CLI_NAME="mel"
CLI_URL="$REPO_RAW_BASE/$CLI_NAME"

info() { printf "[mel] %s\n" "$*"; }
warn() { printf "[mel] WARNING: %s\n" "$*" 1>&2; }
fail() { printf "[mel] ERROR: %s\n" "$*" 1>&2; exit 1; }

command -v curl >/dev/null 2>&1 || fail "curl is required"

choose_target_dir() {
  local arg_dir="${1:-}"
  if [[ -n "$arg_dir" ]]; then
    echo "$arg_dir"
    return 0
  fi

  # Prefer /usr/local/bin if writable
  if [[ -d "/usr/local/bin" && -w "/usr/local/bin" ]]; then
    echo "/usr/local/bin"
    return 0
  fi

  # Fallback to ~/.local/bin
  echo "$HOME/.local/bin"
}

TARGET_DIR="$(choose_target_dir "${1:-}")"
TARGET_PATH="$TARGET_DIR/$CLI_NAME"

mkdir -p "$TARGET_DIR"

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

info "Downloading $CLI_NAME → $TARGET_PATH"
curl -fsSL "$CLI_URL" -o "$TMP_FILE"
chmod +x "$TMP_FILE"

if mv "$TMP_FILE" "$TARGET_PATH" 2>/dev/null; then
  :
else
  # If mv fails due to permissions, fall back to user bin
  DEFAULT_FALLBACK="$HOME/.local/bin/$CLI_NAME"
  warn "Cannot write to $TARGET_DIR. Installing to $HOME/.local/bin instead."
  mkdir -p "$HOME/.local/bin"
  mv "$TMP_FILE" "$DEFAULT_FALLBACK"
  TARGET_DIR="$HOME/.local/bin"
  TARGET_PATH="$DEFAULT_FALLBACK"
fi

if ! command -v python3 >/dev/null 2>&1; then
  warn "python3 not found in PATH. $CLI_NAME uses '#!/usr/bin/env python3'."
fi

# PATH hint
case ":$PATH:" in
  *":$TARGET_DIR:"*) ;;
  *)
    if [[ "${MEL_ADD_TO_PATH:-}" == "1" ]]; then
      # Opt-in PATH modification
      PREFERRED_PROFILE=""
      case "${SHELL:-}" in
        *zsh*) PREFERRED_PROFILE="$HOME/.zshrc" ;;
        *bash*) PREFERRED_PROFILE="$HOME/.bashrc" ;;
        *) PREFERRED_PROFILE="$HOME/.profile" ;;
      esac
      if [[ ! -f "$PREFERRED_PROFILE" ]]; then
        : > "$PREFERRED_PROFILE"
      fi
      if ! grep -qsF "$TARGET_DIR" "$PREFERRED_PROFILE"; then
        info "Adding $TARGET_DIR to PATH in $(basename "$PREFERRED_PROFILE")"
        {
          printf '\n# Added by mel installer on %s\n' "$(date)"
          printf 'export PATH="%s:$PATH"\n' "$TARGET_DIR"
        } >> "$PREFERRED_PROFILE"
        info "Reload your shell or run: source \"$PREFERRED_PROFILE\""
      fi
    else
      warn "$TARGET_DIR is not in your PATH. Either run it via: $TARGET_PATH"
      warn "Or add it to PATH by appending this to your shell profile:"
      printf '\n    export PATH="%s:$PATH"\n\n' "$TARGET_DIR"
    fi
    ;;
esac

info "Installed: $TARGET_PATH"
info "Run: 'mel help'"


