# ═══════════════════════════════════════════════════════════════════════
# Vanguard v2 — Multi-Stage Docker Build
# Architecture: [Client] → vanguard_proxy:8080 → my_server:3000
#
# Stage 1 (builder): Compile both C++ binaries on Alpine with g++
# Stage 2 (runtime): Minimal Alpine image with only the binaries
# ═══════════════════════════════════════════════════════════════════════

# ── Stage 1: Builder ─────────────────────────────────────────────────
FROM alpine:3.20 AS builder

RUN apk add --no-cache \
    g++ \
    make \
    musl-dev \
    linux-headers

WORKDIR /build

# Copy source code
COPY Makefile          .
COPY vanguard_proxy.cpp .
COPY my_server.cpp     .
COPY include/          include/

# Compile both binaries with static linking for portability
RUN make all CXXFLAGS="-std=c++17 -Wall -Wextra -O3 -pthread -static"

# Verify binaries exist
RUN test -f vanguard_proxy && test -f my_server \
    && echo "[+] Build successful" \
    || (echo "[!] Build failed" && exit 1)

# ── Stage 2: Runtime ─────────────────────────────────────────────────
FROM alpine:3.20 AS runtime

LABEL maintainer="Sattaya — Project Vanguard v2"
LABEL description="Vanguard Edge Proxy + Backend Server"
LABEL version="2.0"

# Install:
#   curl    — healthcheck
#   tini    — proper PID 1 signal forwarding
#   bash    — entrypoint uses bash features (wait -n)
RUN apk add --no-cache curl tini bash

WORKDIR /app

# Copy compiled binaries from builder stage
COPY --from=builder /build/vanguard_proxy .
COPY --from=builder /build/my_server      .

# Copy configuration files
COPY whitelist.conf .

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh vanguard_proxy my_server

# Expose proxy port (backend is loopback-only, not exposed)
EXPOSE 8080

# Use tini as PID 1 for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/app/entrypoint.sh"]
