#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
Vanguard v2 — Asynchronous Stress Tester
Performance and security testing tool for the Vanguard proxy.

Modes:
  normal     — Standard load test with slight delays (expect 200)
  bruteforce — Flood to trigger rate limiter (expect 200 + 429)
  sqli       — SQL injection payloads to test WAF (expect 403)

Requires: pip install aiohttp
by Sattaya — Project Vanguard v2
═══════════════════════════════════════════════════════════════════════
"""

import asyncio
import argparse
import time
import sys
from collections import Counter
from dataclasses import dataclass, field

import aiohttp

# ╔═══════════════════════════════════════╗
# ║         Configuration                 ║
# ╚═══════════════════════════════════════╝

DEFAULT_TARGET = "http://127.0.0.1:8080"


# ╔═══════════════════════════════════════╗
# ║        Result Tracking                ║
# ╚═══════════════════════════════════════╝

@dataclass
class StressResult:
    """Aggregated results from a stress test run."""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    status_codes: Counter = field(default_factory=Counter)
    latencies: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def elapsed(self) -> float:
        return self.end_time - self.start_time

    @property
    def rps(self) -> float:
        return self.total_requests / self.elapsed if self.elapsed > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        return (sum(self.latencies) / len(self.latencies)) if self.latencies else 0.0

    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0.0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0.0

    @property
    def p50_latency(self) -> float:
        return self._percentile(50)

    @property
    def p95_latency(self) -> float:
        return self._percentile(95)

    @property
    def p99_latency(self) -> float:
        return self._percentile(99)

    def _percentile(self, p: int) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * p / 100)
        idx = min(idx, len(sorted_lat) - 1)
        return sorted_lat[idx]


# ╔═══════════════════════════════════════╗
# ║         ANSI Color Helpers            ║
# ╚═══════════════════════════════════════╝

class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[97m"
    BG_BLACK = "\033[40m"

C = Colors


# ╔═══════════════════════════════════════╗
# ║        Request Workers                ║
# ╚═══════════════════════════════════════╝

async def send_request(
    session: aiohttp.ClientSession,
    url: str,
    result: StressResult,
    semaphore: asyncio.Semaphore,
    delay: float = 0.0,
):
    """Send a single HTTP request and record metrics."""
    async with semaphore:
        if delay > 0:
            await asyncio.sleep(delay)

        start = time.monotonic()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                await resp.read()
                elapsed = time.monotonic() - start
                result.latencies.append(elapsed)
                result.status_codes[resp.status] += 1
                result.successful += 1
        except asyncio.TimeoutError:
            result.errors.append("timeout")
            result.failed += 1
        except aiohttp.ClientError as e:
            result.errors.append(str(e)[:80])
            result.failed += 1
        except Exception as e:
            result.errors.append(f"unexpected: {str(e)[:60]}")
            result.failed += 1
        finally:
            result.total_requests += 1


# ╔═══════════════════════════════════════╗
# ║        Mode Definitions               ║
# ╚═══════════════════════════════════════╝

def get_mode_config(mode: str, target: str) -> dict:
    """Return URL and delay config based on test mode."""
    modes = {
        "normal": {
            "url": f"{target}/",
            "delay": 0.01,  # 10ms between requests (realistic load)
            "description": "Normal load — steady traffic with slight delays",
            "expected": "HTTP 200 (all pass)",
        },
        "bruteforce": {
            "url": f"{target}/",
            "delay": 0.0,   # No delay — blast as fast as possible
            "description": "Bruteforce flood — trigger token bucket rate limiter",
            "expected": "Mix of HTTP 200 + 429 (rate limited)",
        },
        "sqli": {
            "url": f"{target}/?id=1'%20OR%20'1'%3D'1",
            "delay": 0.005,
            "description": "SQL Injection — WAF bypass attempt",
            "expected": "HTTP 403 (blocked by WAF)",
        },
    }
    return modes[mode]


# ╔═══════════════════════════════════════╗
# ║        Progress Reporter              ║
# ╚═══════════════════════════════════════╝

async def progress_reporter(result: StressResult, total: int):
    """Live progress updates during the test."""
    bar_width = 40
    while result.total_requests < total:
        done = result.total_requests
        pct = (done / total) * 100 if total > 0 else 0
        filled = int(bar_width * done / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        elapsed = time.monotonic() - result.start_time
        rps = done / elapsed if elapsed > 0 else 0

        sys.stdout.write(
            f"\r  {C.CYAN}[{bar}]{C.RESET} "
            f"{C.BOLD}{pct:5.1f}%{C.RESET} "
            f"({done:,}/{total:,}) "
            f"{C.DIM}│{C.RESET} "
            f"{C.GREEN}{rps:,.0f} req/s{C.RESET} "
            f"{C.DIM}│{C.RESET} "
            f"{C.YELLOW}{result.failed} err{C.RESET}"
        )
        sys.stdout.flush()
        await asyncio.sleep(0.25)

    # Final state
    sys.stdout.write(
        f"\r  {C.CYAN}[{'█' * bar_width}]{C.RESET} "
        f"{C.BOLD}100.0%{C.RESET} "
        f"({total:,}/{total:,}) "
        f"{C.DIM}│{C.RESET} "
        f"{C.GREEN}Done!{C.RESET}          \n"
    )
    sys.stdout.flush()


# ╔═══════════════════════════════════════╗
# ║          Report Renderer              ║
# ╚═══════════════════════════════════════╝

def print_report(result: StressResult, mode_cfg: dict, args):
    """Print a formatted terminal report of the test results."""
    sep = f"{C.DIM}{'─' * 60}{C.RESET}"

    print(f"\n{C.MAGENTA}{C.BOLD}")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║         VANGUARD STRESS TEST — RESULTS REPORT          ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(C.RESET)

    # ── Test Configuration ──
    print(f"  {C.BOLD}{C.WHITE}TEST CONFIGURATION{C.RESET}")
    print(f"  {sep}")
    print(f"  Mode             {C.CYAN}{args.mode}{C.RESET}")
    print(f"  Description      {C.DIM}{mode_cfg['description']}{C.RESET}")
    print(f"  Target URL       {C.DIM}{mode_cfg['url']}{C.RESET}")
    print(f"  Concurrency      {C.YELLOW}{args.concurrency}{C.RESET}")
    print(f"  Total Requests   {C.YELLOW}{args.num_requests:,}{C.RESET}")
    print(f"  Expected         {C.DIM}{mode_cfg['expected']}{C.RESET}")
    print()

    # ── Performance Summary ──
    print(f"  {C.BOLD}{C.WHITE}PERFORMANCE SUMMARY{C.RESET}")
    print(f"  {sep}")
    print(f"  Total Time       {C.BOLD}{C.WHITE}{result.elapsed:.3f}s{C.RESET}")
    print(f"  Throughput (RPS) {C.BOLD}{C.GREEN}{result.rps:,.1f} req/s{C.RESET}")
    print(f"  Completed        {C.GREEN}{result.successful:,}{C.RESET}")
    print(f"  Failed           ", end="")
    if result.failed > 0:
        print(f"{C.RED}{result.failed:,}{C.RESET}")
    else:
        print(f"{C.GREEN}0{C.RESET}")
    print()

    # ── Latency Distribution ──
    print(f"  {C.BOLD}{C.WHITE}LATENCY DISTRIBUTION{C.RESET}")
    print(f"  {sep}")
    if result.latencies:
        print(f"  Average          {C.CYAN}{result.avg_latency * 1000:.2f} ms{C.RESET}")
        print(f"  Min              {C.GREEN}{result.min_latency * 1000:.2f} ms{C.RESET}")
        print(f"  Max              {C.YELLOW}{result.max_latency * 1000:.2f} ms{C.RESET}")
        print(f"  P50 (Median)     {C.CYAN}{result.p50_latency * 1000:.2f} ms{C.RESET}")
        print(f"  P95              {C.YELLOW}{result.p95_latency * 1000:.2f} ms{C.RESET}")
        print(f"  P99              {C.RED}{result.p99_latency * 1000:.2f} ms{C.RESET}")
    else:
        print(f"  {C.DIM}No latency data (all requests failed){C.RESET}")
    print()

    # ── HTTP Status Code Breakdown ──
    print(f"  {C.BOLD}{C.WHITE}HTTP STATUS CODES{C.RESET}")
    print(f"  {sep}")

    total = sum(result.status_codes.values()) or 1
    for code, count in sorted(result.status_codes.items()):
        pct = (count / total) * 100
        bar_len = int(pct / 2.5)  # scale to ~40 chars max
        bar = "█" * bar_len

        # Color code by status category
        if 200 <= code < 300:
            color = C.GREEN
            label = "OK"
        elif code == 403:
            color = C.RED
            label = "BLOCKED (WAF)"
        elif code == 429:
            color = C.YELLOW
            label = "RATE LIMITED"
        elif 400 <= code < 500:
            color = C.YELLOW
            label = "CLIENT ERROR"
        elif 500 <= code < 600:
            color = C.RED
            label = "SERVER ERROR"
        else:
            color = C.DIM
            label = ""

        print(
            f"  {color}{code}{C.RESET} "
            f"{C.DIM}{label:<15}{C.RESET} "
            f"{color}{bar}{C.RESET} "
            f"{C.BOLD}{count:>6,}{C.RESET} "
            f"{C.DIM}({pct:.1f}%){C.RESET}"
        )
    print()

    # ── Errors ──
    if result.errors:
        unique_errors = Counter(result.errors)
        print(f"  {C.BOLD}{C.RED}ERRORS{C.RESET}")
        print(f"  {sep}")
        for err, cnt in unique_errors.most_common(5):
            print(f"  {C.RED}×{C.RESET} {err} {C.DIM}(×{cnt}){C.RESET}")
        if len(unique_errors) > 5:
            remaining = len(unique_errors) - 5
            print(f"  {C.DIM}... and {remaining} more unique errors{C.RESET}")
        print()

    # ── Verdict ──
    print(f"  {sep}")
    if args.mode == "normal" and result.status_codes.get(200, 0) == result.successful:
        print(f"  {C.GREEN}{C.BOLD}✓ PASS{C.RESET} — All requests returned HTTP 200")
    elif args.mode == "bruteforce" and result.status_codes.get(429, 0) > 0:
        rate_limited = result.status_codes.get(429, 0)
        passed = result.status_codes.get(200, 0)
        print(f"  {C.GREEN}{C.BOLD}✓ PASS{C.RESET} — Rate limiter triggered successfully")
        print(f"          {C.GREEN}{passed:,} allowed{C.RESET} / {C.YELLOW}{rate_limited:,} rate-limited{C.RESET}")
    elif args.mode == "sqli" and result.status_codes.get(403, 0) > 0:
        blocked = result.status_codes.get(403, 0)
        print(f"  {C.GREEN}{C.BOLD}✓ PASS{C.RESET} — WAF blocked {blocked:,}/{result.successful:,} SQLi attempts")
    else:
        print(f"  {C.YELLOW}{C.BOLD}⚠ REVIEW{C.RESET} — Unexpected status code distribution")
    print()


# ╔═══════════════════════════════════════╗
# ║          Main Runner                  ║
# ╚═══════════════════════════════════════╝

async def run_stress_test(args):
    """Execute the stress test with the given arguments."""
    mode_cfg = get_mode_config(args.mode, args.target)
    result = StressResult()

    # ── Banner ──
    print(f"\n{C.MAGENTA}{C.BOLD}")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║         VANGUARD v2 — STRESS TESTER                    ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(C.RESET)
    print(f"  {C.BOLD}Mode:{C.RESET}        {C.CYAN}{args.mode}{C.RESET}")
    print(f"  {C.BOLD}Target:{C.RESET}      {C.DIM}{mode_cfg['url']}{C.RESET}")
    print(f"  {C.BOLD}Requests:{C.RESET}    {C.YELLOW}{args.num_requests:,}{C.RESET}")
    print(f"  {C.BOLD}Concurrency:{C.RESET} {C.YELLOW}{args.concurrency}{C.RESET}")
    print(f"  {C.BOLD}Expected:{C.RESET}    {C.DIM}{mode_cfg['expected']}{C.RESET}")
    print()
    print(f"  {C.DIM}Starting in 2 seconds...{C.RESET}")
    await asyncio.sleep(2)

    # ── Create semaphore for concurrency limiting ──
    semaphore = asyncio.Semaphore(args.concurrency)

    # ── Configure connection pool ──
    connector = aiohttp.TCPConnector(
        limit=args.concurrency,
        limit_per_host=args.concurrency,
        enable_cleanup_closed=True,
    )

    async with aiohttp.ClientSession(connector=connector) as session:
        result.start_time = time.monotonic()

        # Launch progress reporter
        progress_task = asyncio.create_task(
            progress_reporter(result, args.num_requests)
        )

        # Fire all requests
        tasks = [
            send_request(
                session,
                mode_cfg["url"],
                result,
                semaphore,
                delay=mode_cfg["delay"],
            )
            for _ in range(args.num_requests)
        ]

        await asyncio.gather(*tasks)
        result.end_time = time.monotonic()

        # Wait for progress bar to finish
        await progress_task

    # ── Print Report ──
    print_report(result, mode_cfg, args)


def main():
    parser = argparse.ArgumentParser(
        description="Vanguard v2 — Asynchronous Stress Tester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python vanguard_stress.py -m normal\n"
            "  python vanguard_stress.py -m bruteforce -c 100 -n 5000\n"
            "  python vanguard_stress.py -m sqli -c 20 -n 200\n"
        ),
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=50,
        help="Number of concurrent connections (default: 50)",
    )
    parser.add_argument(
        "-n", "--num-requests",
        type=int,
        default=1000,
        help="Total number of requests to send (default: 1000)",
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["normal", "bruteforce", "sqli"],
        default="normal",
        help="Test mode: normal, bruteforce, or sqli (default: normal)",
    )
    parser.add_argument(
        "-t", "--target",
        default=DEFAULT_TARGET,
        help=f"Target base URL (default: {DEFAULT_TARGET})",
    )
    args = parser.parse_args()

    # Validate
    if args.concurrency < 1:
        parser.error("Concurrency must be at least 1")
    if args.num_requests < 1:
        parser.error("Number of requests must be at least 1")

    try:
        asyncio.run(run_stress_test(args))
    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}[*]{C.RESET} Test interrupted by user.\n")
        sys.exit(130)


if __name__ == "__main__":
    main()
