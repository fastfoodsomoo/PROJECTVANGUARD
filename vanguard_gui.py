#!/usr/bin/env python3
"""
VANGUARD Control Center v2
PyQt6 + pyqtgraph Desktop GUI for the VANGUARD C++ HTTP Proxy/WAF project.
"""

import sys
import json
import time
import urllib.request
import urllib.error
from collections import deque
from datetime import datetime

from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QProcess, QTimer, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QSize,
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QTextCursor, QKeyEvent, QPainter,
    QLinearGradient, QBrush, QPen, QIcon, QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QLineEdit, QPushButton, QFrame, QSplitter,
    QSizePolicy, QGraphicsDropShadowEffect,
)

import pyqtgraph as pg


# ── Theme constants ──────────────────────────────────────────────────────────

BG_DARKEST   = "#0a0a0a"
BG_DARK      = "#111111"
BG_CARD      = "#1a1a1a"
BORDER_CARD  = "#2a2a2a"
ACCENT_GREEN = "#00ff88"
ACCENT_CYAN  = "#00ccff"
COLOR_WARN   = "#ffaa00"
COLOR_DANGER = "#ff4444"
TEXT_PRIMARY  = "#cccccc"
TEXT_DIM      = "#666666"
MONO_FONT    = "Consolas"


# ── Stats poller (QThread worker) ────────────────────────────────────────────

class StatsPoller(QThread):
    """Background thread that polls /stats every second and emits results."""

    stats_received = pyqtSignal(dict)
    stats_error    = pyqtSignal(str)

    def __init__(self, url: str = "http://127.0.0.1:3000/stats", parent=None):
        super().__init__(parent)
        self._url = url
        self._running = True

    def run(self):
        while self._running:
            try:
                req = urllib.request.Request(self._url, method="GET")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode())
                self.stats_received.emit(data)
            except Exception as exc:
                self.stats_error.emit(str(exc))
            self.msleep(1000)

    def stop(self):
        self._running = False
        self.wait(3000)


# ── Pulsing dot widget ───────────────────────────────────────────────────────

class PulsingDot(QWidget):
    """Small circle that pulses between bright and dim to indicate liveness."""

    def __init__(self, color: str = ACCENT_GREEN, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._color = QColor(color)
        self._opacity = 1.0

        self._anim = QPropertyAnimation(self, b"opacity")
        self._anim.setDuration(900)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.25)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)
        self._anim.start()

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, v):
        self._opacity = v
        self.update()

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 2, 10, 10)
        p.end()


# ── Status card ──────────────────────────────────────────────────────────────

class StatusCard(QFrame):
    """A single metric card with a label and value."""

    def __init__(self, title: str, initial_value: str = "—", parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setStyleSheet(f"""
            #statusCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_CARD};
                border-radius: 8px;
                padding: 10px 16px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self._title_label = QLabel(title)
        self._title_label.setFont(QFont(MONO_FONT, 9))
        self._title_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
        layout.addWidget(self._title_label)

        self._value_label = QLabel(initial_value)
        self._value_label.setFont(QFont(MONO_FONT, 18, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(self._value_label)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, text: str, color: str | None = None):
        self._value_label.setText(text)
        c = color or TEXT_PRIMARY
        self._value_label.setStyleSheet(f"color: {c}; background: transparent; border: none;")


# ── Command input with history ───────────────────────────────────────────────

class CommandInput(QLineEdit):
    """QLineEdit that supports command history via up/down arrows."""

    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: list[str] = []
        self._hist_idx = -1

        self.setFont(QFont(MONO_FONT, 11))
        self.setPlaceholderText("Enter command…")
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_DARKEST};
                color: {ACCENT_GREEN};
                border: 1px solid {BORDER_CARD};
                border-radius: 4px;
                padding: 6px 10px;
                selection-background-color: {ACCENT_CYAN};
            }}
        """)
        self.returnPressed.connect(self._on_submit)

    def _on_submit(self):
        cmd = self.text().strip()
        if cmd:
            self._history.append(cmd)
            self._hist_idx = len(self._history)
            self.command_submitted.emit(cmd)
        self.clear()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            if self._history and self._hist_idx > 0:
                self._hist_idx -= 1
                self.setText(self._history[self._hist_idx])
            return
        if event.key() == Qt.Key.Key_Down:
            if self._hist_idx < len(self._history) - 1:
                self._hist_idx += 1
                self.setText(self._history[self._hist_idx])
            else:
                self._hist_idx = len(self._history)
                self.clear()
            return
        super().keyPressEvent(event)


# ── Main window ──────────────────────────────────────────────────────────────

class VanguardControlCenter(QMainWindow):
    """Top-level window for the VANGUARD Control Center."""

    def __init__(self):
        super().__init__()

        # ── Window chrome ────────────────────────────────────────────────
        self.setWindowTitle("VANGUARD Control Center")
        self.setMinimumSize(1000, 750)
        self.resize(1200, 850)
        self._set_icon()

        # ── State ────────────────────────────────────────────────────────
        self._prev_total: int | None = None
        self._prev_time: float | None = None
        self._rps_history: deque[float] = deque(maxlen=60)
        self._processes: dict[str, QProcess] = {}   # label -> QProcess

        # ── Central widget ───────────────────────────────────────────────
        central = QWidget()
        central.setStyleSheet(f"background-color: {BG_DARKEST};")
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {BORDER_CARD};
                height: 3px;
            }}
        """)
        root_layout.addWidget(splitter)

        # ── Top panel (dashboard) ────────────────────────────────────────
        top_panel = QWidget()
        top_panel.setStyleSheet(f"background-color: {BG_DARK};")
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(18, 14, 18, 10)
        top_layout.setSpacing(12)

        # Header
        header = QLabel("⟨ VANGUARD  CONTROL  CENTER  v2 ⟩")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont(MONO_FONT, 22, QFont.Weight.Bold))
        header.setStyleSheet(f"""
            color: {ACCENT_GREEN};
            padding: 10px;
            letter-spacing: 4px;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {BG_DARKEST}, stop:0.5 #0d1f15, stop:1 {BG_DARKEST}
            );
            border: 1px solid #1a3a28;
            border-radius: 6px;
        """)
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setColor(QColor(ACCENT_GREEN))
        glow.setOffset(0, 0)
        header.setGraphicsEffect(glow)
        top_layout.addWidget(header)

        # Status cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self._card_status = StatusCard("SERVER STATUS", "OFFLINE")
        self._dot = PulsingDot(COLOR_DANGER)
        status_inner = QHBoxLayout()
        status_inner.addWidget(self._dot)
        status_inner.addWidget(self._card_status)
        status_inner.setSpacing(6)
        cards_row.addLayout(status_inner, 1)

        self._card_uptime  = StatusCard("UPTIME", "—")
        self._card_reqs    = StatusCard("TOTAL REQUESTS", "—")
        self._card_conns   = StatusCard("ACTIVE CONNS", "—")
        self._card_rps     = StatusCard("CURRENT RPS", "—")

        for card in (self._card_uptime, self._card_reqs, self._card_conns, self._card_rps):
            cards_row.addWidget(card, 1)

        top_layout.addLayout(cards_row)

        # Live chart
        pg.setConfigOptions(antialias=True)
        self._chart = pg.PlotWidget()
        self._chart.setBackground(BG_DARKEST)
        self._chart.setTitle("Requests Per Second (last 60 s)", color=TEXT_DIM, size="10pt")
        self._chart.setLabel("left", "RPS", color=TEXT_DIM)
        self._chart.setLabel("bottom", "Seconds Ago", color=TEXT_DIM)
        self._chart.showGrid(x=True, y=True, alpha=0.15)
        self._chart.setYRange(0, 10)
        self._chart.setXRange(-60, 0)
        self._chart.getAxis("bottom").setStyle(tickFont=QFont(MONO_FONT, 8))
        self._chart.getAxis("left").setStyle(tickFont=QFont(MONO_FONT, 8))
        self._chart.getAxis("bottom").setTextPen(pg.mkPen(TEXT_DIM))
        self._chart.getAxis("left").setTextPen(pg.mkPen(TEXT_DIM))

        grad = QLinearGradient(0, 0, 1, 0)
        grad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectMode)
        grad.setColorAt(0, QColor(ACCENT_GREEN))
        grad.setColorAt(1, QColor(ACCENT_CYAN))

        pen = pg.mkPen(color=QColor(ACCENT_CYAN), width=2)
        self._curve = self._chart.plot([], [], pen=pen, fillLevel=0,
                                        brush=pg.mkBrush(0, 204, 255, 30))

        self._chart.setMinimumHeight(160)
        self._chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        top_layout.addWidget(self._chart)

        splitter.addWidget(top_panel)

        # ── Bottom panel (controls + terminal) ───────────────────────────
        bottom_panel = QWidget()
        bottom_panel.setStyleSheet(f"background-color: {BG_DARKEST};")
        bot_layout = QVBoxLayout(bottom_panel)
        bot_layout.setContentsMargins(18, 8, 18, 12)
        bot_layout.setSpacing(8)

        # Control buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_style_template = """
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 10px 20px;
                font-family: {font};
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {hover_border};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
            }}
        """

        self._btn_backend = QPushButton("▶  Start Backend")
        self._btn_backend.setStyleSheet(btn_style_template.format(
            bg="#0d2818", fg=ACCENT_GREEN, border="#1a4a2e", font=MONO_FONT,
            hover_bg="#154030", hover_border=ACCENT_GREEN, pressed_bg="#0a1e12"))
        self._btn_backend.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_backend.clicked.connect(lambda: self._run_process("Backend", "./my_server"))

        self._btn_proxy = QPushButton("▶  Start Proxy")
        self._btn_proxy.setStyleSheet(btn_style_template.format(
            bg="#0d1e30", fg=ACCENT_CYAN, border="#1a3a5a", font=MONO_FONT,
            hover_bg="#153050", hover_border=ACCENT_CYAN, pressed_bg="#0a1520"))
        self._btn_proxy.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_proxy.clicked.connect(lambda: self._run_process("Proxy", "./vanguard_proxy"))

        self._btn_stress = QPushButton("⚡  Stress Test")
        self._btn_stress.setStyleSheet(btn_style_template.format(
            bg="#2a1a00", fg=COLOR_WARN, border="#4a3000", font=MONO_FONT,
            hover_bg="#3a2800", hover_border=COLOR_WARN, pressed_bg="#1a1000"))
        self._btn_stress.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_stress.clicked.connect(
            lambda: self._run_process("StressTest", "python3",
                                      ["vanguard_stress.py", "-m", "bruteforce", "-c", "50", "-n", "1000"]))

        btn_row.addWidget(self._btn_backend)
        btn_row.addWidget(self._btn_proxy)
        btn_row.addWidget(self._btn_stress)
        bot_layout.addLayout(btn_row)

        # Terminal output
        self._terminal = QTextEdit()
        self._terminal.setReadOnly(True)
        self._terminal.setFont(QFont(MONO_FONT, 10))
        self._terminal.setStyleSheet(f"""
            QTextEdit {{
                background-color: #050505;
                color: {ACCENT_GREEN};
                border: 1px solid {BORDER_CARD};
                border-radius: 4px;
                padding: 8px;
                selection-background-color: #224433;
            }}
            QScrollBar:vertical {{
                background: {BG_DARKEST};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER_CARD};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        self._terminal.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bot_layout.addWidget(self._terminal)

        # Command input row
        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(6)
        prompt_label = QLabel("$")
        prompt_label.setFont(QFont(MONO_FONT, 13, QFont.Weight.Bold))
        prompt_label.setStyleSheet(f"color: {ACCENT_GREEN}; background: transparent;")
        prompt_label.setFixedWidth(18)
        cmd_row.addWidget(prompt_label)

        self._cmd_input = CommandInput()
        self._cmd_input.command_submitted.connect(self._on_manual_command)
        cmd_row.addWidget(self._cmd_input)
        bot_layout.addLayout(cmd_row)

        splitter.addWidget(bottom_panel)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 4)

        # ── Stats poller ─────────────────────────────────────────────────
        self._poller = StatsPoller()
        self._poller.stats_received.connect(self._on_stats)
        self._poller.stats_error.connect(self._on_stats_error)
        self._poller.start()

        # Boot message
        self._term_write_system("VANGUARD Control Center v2 initialized.")
        self._term_write_system("Type commands below or use the control buttons.")

    # ── Icon helper ──────────────────────────────────────────────────────

    def _set_icon(self):
        """Generate a simple green-V pixmap icon for the window."""
        px = QPixmap(64, 64)
        px.fill(QColor(BG_DARKEST))
        painter = QPainter(px)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(ACCENT_GREEN), 5)
        painter.setPen(pen)
        painter.drawLine(10, 12, 32, 52)
        painter.drawLine(32, 52, 54, 12)
        painter.end()
        self.setWindowIcon(QIcon(px))

    # ── Terminal helpers ─────────────────────────────────────────────────

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _term_write_system(self, text: str):
        self._terminal.append(
            f'<span style="color:{TEXT_DIM}">[{self._timestamp()}]</span> '
            f'<span style="color:{ACCENT_CYAN}">{text}</span>'
        )
        self._scroll_terminal()

    def _term_write_cmd(self, cmd: str):
        self._terminal.append(
            f'<span style="color:{TEXT_DIM}">[{self._timestamp()}]</span> '
            f'<span style="color:{COLOR_WARN}">$</span> '
            f'<span style="color:{TEXT_PRIMARY}">{cmd}</span>'
        )
        self._scroll_terminal()

    def _term_write_stdout(self, text: str):
        # Escape HTML entities for safe display
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for line in safe.splitlines():
            self._terminal.append(
                f'<span style="color:{ACCENT_GREEN}">{line}</span>'
            )
        self._scroll_terminal()

    def _term_write_stderr(self, text: str):
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for line in safe.splitlines():
            self._terminal.append(
                f'<span style="color:{COLOR_DANGER}">{line}</span>'
            )
        self._scroll_terminal()

    def _scroll_terminal(self):
        cursor = self._terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._terminal.setTextCursor(cursor)
        self._terminal.ensureCursorVisible()

    # ── Process management ───────────────────────────────────────────────

    def _run_process(self, label: str, program: str, args: list[str] | None = None):
        """Start a QProcess and pipe its output into the terminal."""
        if args is None:
            args = []

        # If a process with this label already exists and is running, notify
        if label in self._processes:
            proc = self._processes[label]
            if proc.state() != QProcess.ProcessState.NotRunning:
                self._term_write_system(f"[{label}] process is already running (PID {proc.processId()}).")
                return

        full_cmd = program + (" " + " ".join(args) if args else "")
        self._term_write_cmd(full_cmd)
        self._term_write_system(f"[{label}] Starting…")

        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)

        # Capture label in closures
        proc.readyReadStandardOutput.connect(lambda p=proc: self._on_proc_stdout(p))
        proc.readyReadStandardError.connect(lambda p=proc: self._on_proc_stderr(p))
        proc.finished.connect(lambda code, status, lb=label: self._on_proc_finished(lb, code, status))

        self._processes[label] = proc
        proc.start(program, args)

    def _on_proc_stdout(self, proc: QProcess):
        data = proc.readAllStandardOutput()
        if data:
            text = bytes(data).decode("utf-8", errors="replace")
            self._term_write_stdout(text)

    def _on_proc_stderr(self, proc: QProcess):
        data = proc.readAllStandardError()
        if data:
            text = bytes(data).decode("utf-8", errors="replace")
            self._term_write_stderr(text)

    def _on_proc_finished(self, label: str, exit_code: int, _status):
        color = ACCENT_GREEN if exit_code == 0 else COLOR_DANGER
        self._terminal.append(
            f'<span style="color:{TEXT_DIM}">[{self._timestamp()}]</span> '
            f'<span style="color:{color}">[{label}] Process exited with code {exit_code}</span>'
        )
        self._scroll_terminal()

    def _on_manual_command(self, cmd: str):
        """Execute an arbitrary shell command typed by the user."""
        self._term_write_cmd(cmd)

        parts = cmd.split()
        if not parts:
            return

        program = parts[0]
        args = parts[1:]

        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        proc.readyReadStandardOutput.connect(lambda p=proc: self._on_proc_stdout(p))
        proc.readyReadStandardError.connect(lambda p=proc: self._on_proc_stderr(p))
        proc.finished.connect(lambda code, status: self._on_proc_finished("cmd", code, status))

        # Store under a unique key so it doesn't collide
        key = f"manual_{id(proc)}"
        self._processes[key] = proc
        proc.start(program, args)

    # ── Stats handling ───────────────────────────────────────────────────

    def _on_stats(self, data: dict):
        now = time.monotonic()

        # Status
        status = data.get("status", "unknown")
        if status == "online":
            self._card_status.set_value("ONLINE", ACCENT_GREEN)
            self._dot.set_color(ACCENT_GREEN)
        else:
            self._card_status.set_value(status.upper(), COLOR_WARN)
            self._dot.set_color(COLOR_WARN)

        # Uptime
        secs = int(data.get("uptime_seconds", 0))
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m, s   = divmod(rem, 60)
        parts = []
        if d: parts.append(f"{d}d")
        if h or d: parts.append(f"{h}h")
        parts.append(f"{m}m")
        parts.append(f"{s}s")
        self._card_uptime.set_value(" ".join(parts), ACCENT_CYAN)

        # Total requests
        total = int(data.get("total_requests", 0))
        self._card_reqs.set_value(f"{total:,}", TEXT_PRIMARY)

        # Active connections
        conns = int(data.get("active_connections", 0))
        if conns < 10:
            conn_color = ACCENT_GREEN
        elif conns < 50:
            conn_color = COLOR_WARN
        else:
            conn_color = COLOR_DANGER
        self._card_conns.set_value(str(conns), conn_color)

        # RPS calculation
        rps = 0.0
        if self._prev_total is not None and self._prev_time is not None:
            dt = now - self._prev_time
            if dt > 0:
                rps = max(0.0, (total - self._prev_total) / dt)
        self._prev_total = total
        self._prev_time = now
        self._rps_history.append(rps)

        self._card_rps.set_value(f"{rps:.1f}", ACCENT_GREEN if rps < 100 else COLOR_WARN)

        # Update chart
        self._update_chart()

    def _on_stats_error(self, _msg: str):
        self._card_status.set_value("OFFLINE", COLOR_DANGER)
        self._dot.set_color(COLOR_DANGER)
        self._card_uptime.set_value("—", TEXT_DIM)
        self._card_reqs.set_value("—", TEXT_DIM)
        self._card_conns.set_value("—", TEXT_DIM)
        self._card_rps.set_value("—", TEXT_DIM)
        self._rps_history.append(0.0)
        self._update_chart()

    def _update_chart(self):
        n = len(self._rps_history)
        x = list(range(-n + 1, 1))  # e.g. [-59, -58, …, 0]
        y = list(self._rps_history)
        self._curve.setData(x, y)

        if y:
            max_y = max(max(y) * 1.2, 5)
            self._chart.setYRange(0, max_y)

    # ── Cleanup ──────────────────────────────────────────────────────────

    def closeEvent(self, event):
        # Stop the poller thread
        self._poller.stop()

        # Kill all child processes
        for label, proc in self._processes.items():
            if proc.state() != QProcess.ProcessState.NotRunning:
                proc.kill()
                proc.waitForFinished(2000)

        event.accept()


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)

    # Global dark palette as fallback
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG_DARKEST))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base,            QColor(BG_DARK))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.Text,            QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button,          QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT_CYAN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BG_DARKEST))
    app.setPalette(palette)
    app.setFont(QFont(MONO_FONT, 10))

    window = VanguardControlCenter()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
