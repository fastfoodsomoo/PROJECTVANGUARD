#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
# Vanguard v2 — One-Click Setup Script
# Installs system-level APT dependencies, compiles C++ binaries,
# sets permissions, installs Python packages, and cleans up artifacts.
# Usage:  bash setup.sh
# ═══════════════════════════════════════════════════════════════════════

set -e  # Exit on first error

# ── ANSI Color Tokens ────────────────────────────────────────────────
R="\033[0m"
B="\033[1m"
DIM="\033[2m"
PURPLE="\033[35m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"

banner() {
    echo ""
    echo -e "${PURPLE}${B}"
    echo "  ╔══════════════════════════════════════════════════════════╗"
    echo "  ║         VANGUARD v2 — AUTOMATED SETUP SCRIPT           ║"
    echo "  ╚══════════════════════════════════════════════════════════╝"
    echo -e "${R}"
}

step() {
    echo -e "  ${PURPLE}${B}[$1/${TOTAL_STEPS}]${R} ${B}$2${R}"
}

ok() {
    echo -e "      ${GREEN}✓${R} $1"
}

warn() {
    echo -e "      ${YELLOW}⚠${R} $1"
}

fail() {
    echo -e "      ${RED}✗${R} $1"
}

TOTAL_STEPS=6

banner

# ═══════════════════════════════════════════════════════════════════════
# Step 1: Install System APT Dependencies
# ═══════════════════════════════════════════════════════════════════════

step 1 "Installing system-level dependencies via APT..."

if command -v apt-get &>/dev/null || command -v apt &>/dev/null; then
    echo -e "      ${DIM}Running: sudo apt update && sudo apt install -y build-essential python3-pip python3-venv python3-dev${R}"
    if sudo apt update && sudo apt install -y build-essential python3-pip python3-venv python3-dev; then
        ok "System APT packages installed successfully."
    else
        warn "APT package installation encountered warnings. Proceeding with dependency check..."
    fi
else
    warn "APT package manager not detected (non-Debian/Ubuntu system). Skipping APT step."
fi

# ═══════════════════════════════════════════════════════════════════════
# Step 2: Check System Build & Runtime Tooling
# ═══════════════════════════════════════════════════════════════════════

step 2 "Verifying core development tools..."

MISSING=""

if ! command -v g++ &>/dev/null; then MISSING="$MISSING g++"; fi
if ! command -v make &>/dev/null; then MISSING="$MISSING make"; fi
if ! command -v python3 &>/dev/null; then MISSING="$MISSING python3"; fi
if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null 2>&1; then MISSING="$MISSING pip3"; fi

if [ -n "$MISSING" ]; then
    fail "Missing required tools:${MISSING}"
    echo -e "  ${YELLOW}Please install missing tools using your system package manager.${R}"
    exit 1
fi

ok "g++, make, python3, pip — verified."

# ═══════════════════════════════════════════════════════════════════════
# Step 3: Compile C++ Source Code
# ═══════════════════════════════════════════════════════════════════════

step 3 "Compiling C++ binaries (vanguard_proxy & my_server)..."

if make; then
    ok "vanguard_proxy compiled successfully."
    ok "my_server compiled successfully."
else
    fail "Compilation failed. Check C++ error output above."
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════
# Step 4: Grant Executable Permissions
# ═══════════════════════════════════════════════════════════════════════

step 4 "Configuring executable permissions..."

chmod +x my_server vanguard_proxy 2>/dev/null && ok "chmod +x my_server vanguard_proxy" || warn "Could not set permissions on binaries."
chmod +x test.sh simulate_attack.sh entrypoint.sh setup.sh 2>/dev/null && ok "chmod +x shell scripts" || warn "Could not set permissions on scripts."

# ═══════════════════════════════════════════════════════════════════════
# Step 5: Install Python Dependencies
# ═══════════════════════════════════════════════════════════════════════

step 5 "Installing Python packages (PyQt6, pyqtgraph, psutil, rich, aiohttp)..."

PIP_CMD=""

if [ -n "$VIRTUAL_ENV" ]; then
    PIP_CMD="pip install"
    ok "Using active virtual environment: $VIRTUAL_ENV"
elif [ -d "venv" ] && [ -f "venv/bin/pip" ]; then
    PIP_CMD="./venv/bin/pip install"
    ok "Using existing local environment at ./venv"
elif python3 -m venv --help &>/dev/null 2>&1; then
    echo -e "      ${DIM}Creating Python virtual environment (./venv)...${R}"
    python3 -m venv venv
    PIP_CMD="./venv/bin/pip install"
    ok "Created virtual environment at ./venv"
    echo -e "      ${DIM}Activate anytime using: source venv/bin/activate${R}"
else
    PIP_CMD="pip3 install --break-system-packages"
    warn "No virtualenv tool found. Using --break-system-packages flag."
fi

if $PIP_CMD -r requirements.txt; then
    ok "All Python requirements installed successfully."
else
    warn "Standard pip install failed. Retrying with --break-system-packages..."
    pip3 install --break-system-packages -r requirements.txt && \
        ok "Installed Python requirements with --break-system-packages." || \
        fail "Could not install Python requirements."
fi

# ═══════════════════════════════════════════════════════════════════════
# Step 6: Clean Up Legacy Artifacts
# ═══════════════════════════════════════════════════════════════════════

step 6 "Cleaning obsolete artifacts & Windows Zone.Identifier files..."

# Remove Zone.Identifier files
ZONE_COUNT=$(find . -name "*Zone.Identifier*" -type f 2>/dev/null | wc -l)
if [ "$ZONE_COUNT" -gt 0 ]; then
    find . -name "*Zone.Identifier*" -type f -delete 2>/dev/null
    ok "Purged $ZONE_COUNT Zone.Identifier artifact files."
else
    ok "No Zone.Identifier artifacts found."
fi

# Remove legacy files
LEGACY_FILES=("server.cpp" "sentinel.cpp" "server_log.txt" "unban.sh")
REMOVED=0
for f in "${LEGACY_FILES[@]}"; do
    if [ -f "$f" ]; then
        rm -f "$f"
        ok "Removed legacy file: $f"
        REMOVED=$((REMOVED + 1))
    fi
done
if [ "$REMOVED" -eq 0 ]; then
    ok "Clean workspace — no legacy v1 files found."
fi

# ═══════════════════════════════════════════════════════════════════════
# Completion Summary
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo -e "  ${PURPLE}${B}═══════════════════════════════════════════════════════════${R}"
echo -e "  ${PURPLE}${B}  ✓ VANGUARD V2 SETUP COMPLETE!${R}"
echo -e "  ${PURPLE}${B}═══════════════════════════════════════════════════════════${R}"
echo ""
echo -e "  ${B}Quick Start Commands:${R}"
echo -e "    ${CYAN}1.${R} Launch Control Center GUI:  ${YELLOW}python3 vanguard_gui.py${R}"
echo -e "    ${CYAN}2.${R} Or Start Backend Server:    ${YELLOW}./my_server${R}"
echo -e "    ${CYAN}3.${R} Or Start Edge WAF Proxy:    ${YELLOW}./vanguard_proxy${R}"
echo ""
