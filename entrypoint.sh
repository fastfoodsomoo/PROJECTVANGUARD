#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Vanguard v2 — Container Entrypoint
# Runs BOTH binaries in a single container:
#   1. my_server       (background)  → 127.0.0.1:3000
#   2. vanguard_proxy  (foreground)  → 0.0.0.0:8080
#
# Signal handling: SIGTERM/SIGINT gracefully stops both processes.
# ═══════════════════════════════════════════════════════════════════════

set -e

BACKEND_PID=""
PROXY_PID=""

# ── Graceful Shutdown ────────────────────────────────────────────────
cleanup() {
    echo ""
    echo "[*] Shutting down Vanguard..."

    # Stop proxy
    if [ -n "$PROXY_PID" ] && kill -0 "$PROXY_PID" 2>/dev/null; then
        kill -TERM "$PROXY_PID" 2>/dev/null
        wait "$PROXY_PID" 2>/dev/null || true
    fi

    # Stop backend
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill -TERM "$BACKEND_PID" 2>/dev/null
        wait "$BACKEND_PID" 2>/dev/null || true
    fi

    echo "[+] All processes stopped."
    exit 0
}

trap cleanup SIGTERM SIGINT

# ── Start Backend Server (background) ───────────────────────────────
echo "[*] Starting backend server (127.0.0.1:3000)..."
/app/my_server &
BACKEND_PID=$!

# Wait for backend to be ready (up to 10 seconds)
# Use curl instead of nc — curl is already installed for healthcheck
echo "[*] Waiting for backend to bind..."
RETRIES=0
while ! curl -sf http://127.0.0.1:3000/stats > /dev/null 2>&1; do
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -ge 20 ]; then
        echo "[!] Backend failed to start after 10s — aborting."
        kill "$BACKEND_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 0.5
done
echo "[+] Backend is ready."

# ── Start Proxy (foreground) ─────────────────────────────────────────
echo "[*] Starting vanguard proxy (0.0.0.0:8080)..."
/app/vanguard_proxy &
PROXY_PID=$!

# Wait for either process to exit
# bash supports `wait -n` (wait for any child to exit)
wait -n "$BACKEND_PID" "$PROXY_PID" 2>/dev/null || true

echo "[!] A process exited unexpectedly — shutting down."
cleanup
