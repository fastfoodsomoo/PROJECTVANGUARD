#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
Vanguard v2 — TUI Observability Dashboard
Real-time terminal dashboard for monitoring the Vanguard backend.

Polls http://127.0.0.1:3000/stats every 1 second and renders:
  • Server status & uptime
  • Total requests & active connections
  • Calculated RPS (requests per second)

Requires: pip install rich requests
by Sattaya — Project Vanguard v2
═══════════════════════════════════════════════════════════════════════
"""

import time
import sys
import argparse
import requests
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.columns import Columns
from rich.rule import Rule

# ╔═══════════════════════════════════════╗
# ║         Configuration                 ║
# ╚═══════════════════════════════════════╝

DEFAULT_URL = "http://127.0.0.1:3000/stats"
POLL_INTERVAL = 1  # seconds

# ╔═══════════════════════════════════════╗
# ║        Time Formatting                ║
# ╚═══════════════════════════════════════╝

def format_uptime(seconds: int) -> str:
    """Convert seconds to human-readable uptime string."""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


# ╔═══════════════════════════════════════╗
# ║       Dashboard Renderer              ║
# ╚═══════════════════════════════════════╝

class VanguardDashboard:
    """Renders a TUI dashboard by polling the /stats endpoint."""

    def __init__(self, url: str = DEFAULT_URL):
        self.url = url
        self.console = Console()
        self.prev_requests = 0
        self.prev_time = time.monotonic()
        self.current_rps = 0.0
        self.rps_history: list[float] = []
        self.max_rps = 0.0
        self.poll_count = 0
        self.error_count = 0
        self.start_time = datetime.now()

    def fetch_stats(self) -> dict | None:
        """Poll the backend /stats endpoint. Returns None on failure."""
        try:
            resp = requests.get(self.url, timeout=2)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError):
            self.error_count += 1
            return None

    def calculate_rps(self, total_requests: int) -> float:
        """Calculate requests per second from delta between polls."""
        now = time.monotonic()
        elapsed = now - self.prev_time

        if elapsed > 0 and self.prev_requests > 0:
            rps = (total_requests - self.prev_requests) / elapsed
        else:
            rps = 0.0

        self.prev_requests = total_requests
        self.prev_time = now

        # Track history
        self.rps_history.append(rps)
        if len(self.rps_history) > 60:
            self.rps_history.pop(0)

        self.max_rps = max(self.max_rps, rps)
        return rps

    def make_header(self) -> Panel:
        """Top banner with system name."""
        header_text = Text()
        header_text.append("╔══════════════════════════════════════════════╗\n", style="bright_magenta")
        header_text.append("║   ", style="bright_magenta")
        header_text.append("VANGUARD v2", style="bold bright_white")
        header_text.append(" — Observability Dashboard   ", style="bright_magenta")
        header_text.append("║\n", style="bright_magenta")
        header_text.append("╚══════════════════════════════════════════════╝", style="bright_magenta")
        return Panel(
            Align.center(header_text),
            style="dim",
            border_style="bright_black",
        )

    def make_status_panel(self, data: dict | None) -> Panel:
        """Server status indicator panel."""
        if data is None:
            status_text = Text()
            status_text.append("● ", style="bold red")
            status_text.append("OFFLINE", style="bold red")
            status_text.append("\n\n  Connection to backend failed", style="dim red")
            status_text.append(f"\n  Endpoint: {self.url}", style="dim")
            status_text.append(f"\n  Errors: {self.error_count}", style="dim red")
            return Panel(
                status_text,
                title="[bold red]SERVER STATUS[/]",
                border_style="red",
                padding=(1, 2),
            )

        status = data.get("status", "unknown")
        server = data.get("server", "unknown")
        bind = data.get("bind", "unknown")
        uptime = data.get("uptime_seconds", 0)

        status_text = Text()
        status_text.append("● ", style="bold green")
        status_text.append("ONLINE", style="bold green")
        status_text.append(f"\n\n  Server   ", style="dim")
        status_text.append(f"{server}", style="bright_white")
        status_text.append(f"\n  Bind     ", style="dim")
        status_text.append(f"{bind}", style="bright_cyan")
        status_text.append(f"\n  Uptime   ", style="dim")
        status_text.append(f"{format_uptime(uptime)}", style="bright_yellow")
        status_text.append(f"\n  Status   ", style="dim")
        status_text.append(f"{status}", style="bright_green")

        return Panel(
            status_text,
            title="[bold green]SERVER STATUS[/]",
            border_style="green",
            padding=(1, 2),
        )

    def make_metrics_panel(self, data: dict | None) -> Panel:
        """Requests and connections metrics panel."""
        if data is None:
            metrics_text = Text("  No data available", style="dim red")
            return Panel(
                metrics_text,
                title="[bold red]METRICS[/]",
                border_style="red",
                padding=(1, 2),
            )

        total_reqs = data.get("total_requests", 0)
        active_conns = data.get("active_connections", 0)

        # Calculate RPS
        self.current_rps = self.calculate_rps(total_reqs)
        avg_rps = (sum(self.rps_history) / len(self.rps_history)) if self.rps_history else 0.0

        metrics_text = Text()
        metrics_text.append("  Total Requests     ", style="dim")
        metrics_text.append(f"{total_reqs:,}", style="bold bright_white")

        metrics_text.append("\n  Active Connections ", style="dim")
        conn_style = "bold bright_green" if active_conns < 10 else "bold bright_yellow" if active_conns < 50 else "bold bright_red"
        metrics_text.append(f"{active_conns}", style=conn_style)

        metrics_text.append("\n")
        metrics_text.append("\n  ── Throughput ─────────────────", style="bright_black")
        metrics_text.append("\n  Current RPS        ", style="dim")
        rps_style = "bold bright_cyan"
        metrics_text.append(f"{self.current_rps:.1f} req/s", style=rps_style)

        metrics_text.append("\n  Average RPS        ", style="dim")
        metrics_text.append(f"{avg_rps:.1f} req/s", style="bright_cyan")

        metrics_text.append("\n  Peak RPS           ", style="dim")
        metrics_text.append(f"{self.max_rps:.1f} req/s", style="bright_magenta")

        return Panel(
            metrics_text,
            title="[bold cyan]METRICS[/]",
            border_style="cyan",
            padding=(1, 2),
        )

    def make_rps_sparkline(self) -> Panel:
        """Visual RPS sparkline using Unicode block characters."""
        if not self.rps_history:
            return Panel(
                Text("  Collecting data...", style="dim"),
                title="[bold yellow]RPS HISTORY[/]",
                border_style="yellow",
                padding=(1, 2),
            )

        # Build a sparkline from the last 50 data points
        history = self.rps_history[-50:]
        max_val = max(history) if max(history) > 0 else 1
        blocks = " ▁▂▃▄▅▆▇█"

        sparkline = Text()
        sparkline.append("  ", style="dim")
        for val in history:
            idx = int((val / max_val) * (len(blocks) - 1))
            idx = min(idx, len(blocks) - 1)
            color = "bright_green" if val < max_val * 0.5 else "bright_yellow" if val < max_val * 0.8 else "bright_red"
            sparkline.append(blocks[idx], style=color)

        sparkline.append(f"\n  └{'─' * len(history)}┘", style="bright_black")
        sparkline.append(f"\n  Last {len(history)}s", style="dim")
        sparkline.append(f" │ Scale: 0 — {max_val:.0f} req/s", style="dim")

        return Panel(
            sparkline,
            title="[bold yellow]RPS HISTORY (sparkline)[/]",
            border_style="yellow",
            padding=(1, 2),
        )

    def make_footer(self) -> Panel:
        """Footer with dashboard meta info."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        running = datetime.now() - self.start_time
        running_str = format_uptime(int(running.total_seconds()))

        footer = Text()
        footer.append(f"  Polling: {self.url}", style="dim")
        footer.append(f"  │  Interval: {POLL_INTERVAL}s", style="dim")
        footer.append(f"  │  Dashboard uptime: {running_str}", style="dim")
        footer.append(f"  │  {now}", style="dim")
        footer.append(f"  │  Ctrl+C to exit", style="dim yellow")

        return Panel(footer, style="dim", border_style="bright_black")

    def build_layout(self, data: dict | None) -> Layout:
        """Compose the full dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
            Layout(name="sparkline", size=7),
            Layout(name="footer", size=3),
        )

        # Body: two columns
        layout["body"].split_row(
            Layout(name="status"),
            Layout(name="metrics"),
        )

        layout["header"].update(self.make_header())
        layout["status"].update(self.make_status_panel(data))
        layout["metrics"].update(self.make_metrics_panel(data))
        layout["sparkline"].update(self.make_rps_sparkline())
        layout["footer"].update(self.make_footer())

        return layout

    def run(self):
        """Main loop: poll and render."""
        self.console.clear()
        self.console.print(
            "\n  [bold magenta]VANGUARD[/] Dashboard starting...\n",
            style="dim",
        )

        try:
            with Live(
                self.build_layout(None),
                console=self.console,
                refresh_per_second=2,
                screen=True,
            ) as live:
                while True:
                    data = self.fetch_stats()
                    self.poll_count += 1
                    live.update(self.build_layout(data))
                    time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            self.console.clear()
            self.console.print(
                "\n  [bold yellow][*][/] Dashboard stopped. "
                f"({self.poll_count} polls, {self.error_count} errors)\n"
            )
            sys.exit(0)


# ╔═══════════════════════════════════════╗
# ║              Main                     ║
# ╚═══════════════════════════════════════╝

def main():
    parser = argparse.ArgumentParser(
        description="Vanguard v2 — TUI Observability Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python dashboard.py\n"
            "  python dashboard.py --url http://192.168.1.10:3000/stats\n"
        ),
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Backend /stats endpoint URL (default: {DEFAULT_URL})",
    )
    args = parser.parse_args()

    dashboard = VanguardDashboard(url=args.url)
    dashboard.run()


if __name__ == "__main__":
    main()
