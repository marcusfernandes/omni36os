#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/../.." && pwd)"
SOURCE="$ROOT/cartao/EASYROMS/ports/Daytona USA.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

make_case() {
    local name="$1"
    local dir="$TMP/$name"
    mkdir -p "$dir/daytona" "$dir/bin"
    cp "$SOURCE" "$dir/Daytona USA.sh"
    touch "$dir/daytona/daytona93.zip"
    cat > "$dir/daytona/daytona_r36s.geo" <<'GAME'
#!/bin/sh
printf 'game\n' >> "$TEST_EVENTS"
GAME
    chmod +x "$dir/daytona/daytona_r36s.geo"
    cat > "$dir/bin/systemctl" <<'SYSTEMCTL'
#!/bin/sh
printf 'systemctl %s\n' "$*" >> "$TEST_EVENTS"
if [ "$1" = is-active ]; then exit 0; fi
exit 0
SYSTEMCTL
    cat > "$dir/bin/sudo" <<'SUDO'
#!/bin/sh
printf 'sudo %s\n' "$*" >> "$TEST_EVENTS"
if [ "$1" = systemctl ]; then shift; exec systemctl "$@"; fi
if [ "$1" = env ]; then shift; exec env "$@"; fi
exec "$@"
SUDO
    cat > "$dir/bin/pactl" <<'PACTL'
#!/bin/sh
exit 0
PACTL
    chmod +x "$dir/bin/systemctl" "$dir/bin/sudo" "$dir/bin/pactl"
}

run_case() {
    local name="$1" handoff="$2" expected="$3"
    local dir="$TMP/$name"
    : > "$TMP/$name.events"
    if ! (cd "$dir" && env PATH="$dir/bin:$PATH" TEST_EVENTS="$TMP/$name.events" \
        DAYTONA_NO_MENU=1 OMNI_PORT_HANDOFF="$handoff" \
        bash "./Daytona USA.sh" >/dev/null 2>&1); then
        echo "FAIL: launcher scenario $name exited unsuccessfully" >&2
        return 1
    fi
    if ! grep -qxF "$expected" "$TMP/$name.events"; then
        echo "FAIL: expected '$expected' in $name events" >&2
        cat "$TMP/$name.events" >&2
        return 1
    fi
    if [ "$handoff" = 1 ] && grep -q 'systemctl stop omni36os-launcher.service' "$TMP/$name.events"; then
        echo "FAIL: normal launcher handoff stopped its owning service" >&2
        cat "$TMP/$name.events" >&2
        return 1
    fi
}

make_case direct
run_case direct 0 'sudo systemctl start omni36os-launcher.service'
grep -qxF 'sudo systemctl stop omni36os-launcher.service' "$TMP/direct.events"
make_case handoff
run_case handoff 1 game
! grep -q 'systemctl start omni36os-launcher.service' "$TMP/handoff.events"
echo 'Daytona launcher handoff tests: OK'
