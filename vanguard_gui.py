#!/usr/bin/env python3
"""
VANGUARD Control Center v2 — Ultra Hacker Purple Cyberpunk Edition
PyQt6 + pyqtgraph Desktop GUI for the VANGUARD C++ HTTP Proxy/WAF project.

Features:
  - Deep Black & Neon Purple Hacker Cyberpunk Aesthetics (ธีมม่วงดำ)
  - Full ANSI Escape Sequence Parser (strips text background boxes & color code artifacts)
  - Top Tactical Warning Header with Real-time Clock
  - 3-Column Tactical HUD Layout (Intrusion Log Stream, RPS Traffic Monitor, Core Metrics & Controls)
  - Monospace Typography ('Consolas', 'Courier New', 'Monospace')
  - Start/Stop toggle buttons with OS-level external process discovery & termination (psutil)
  - Stress Test Preset Modal Menu
  - Non-blocking async design (QThread, QProcess, QTimer)
"""

import sys
import os
import json
import time
import signal
import re
import urllib.request
import urllib.error
from collections import deque
from datetime import datetime
from vanguard_agent import VanguardAIAgent

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
    QSizePolicy, QGraphicsDropShadowEffect, QDialog,
)

import pyqtgraph as pg

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ── Tactical Cyberpunk Theme Palette (Purple & Void Black) ───────────────────

BG_VOID           = "#020204"     # Ultra deep void black
BG_PANEL          = "#06060c"     # Dark panel background
BG_CARD           = "#0a0814"     # HUD module background
BG_CARD_HOVER     = "#120e24"     # Hover state for cards

BORDER_PURPLE     = "#a855f7"     # Bright neon purple border
BORDER_PURPLE_DIM = "#4c1d95"     # Deep muted purple border
BORDER_PURPLE_GLOW= "#c084fc"     # Glowing neon purple

ACCENT_PURPLE     = "#a855f7"     # Primary purple accent
ACCENT_PURPLE_LIGHT = "#e9d5ff"   # Light purple highlight
ACCENT_CYAN       = "#06b6d4"     # Tactical cyan accent
COLOR_SUCCESS     = "#22c55e"     # Green status
COLOR_WARN        = "#f59e0b"     # Amber warning
COLOR_DANGER      = "#ef4444"     # Red alarm/stop

TEXT_PRIMARY      = "#f8fafc"     # Crisp text primary
TEXT_DIM          = "#94a3b8"     # Subdued text
TEXT_MUTED        = "#64748b"     # Muted text

MONO_FONT         = "Consolas, 'Courier New', Monospace"


# ── ANSI Escape Code to HTML Converter ───────────────────────────────────────

def ansi_to_html(text: str) -> str:
    """Parses ANSI color escape sequences into clean HTML without text background boxes."""
    if not text:
        return ""
    
    # HTML escape special characters
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Strip any ANSI background color codes (40-47, 100-107, 48;...) to eliminate background color boxes
    text = re.sub(r'\x1b\[(?:4[0-7]|10[0-7]|48;[0-9;]+)m', '', text)
    
    fg_map = {
        '0': '</span>',
        '1': '<span style="font-weight:bold;">',
        '2': '<span style="opacity:0.75;">',
        '30': '<span style="color:#64748b;">',
        '31': '<span style="color:#ef4444;">',
        '32': '<span style="color:#22c55e;">',
        '33': '<span style="color:#fbbf24;">',
        '34': '<span style="color:#3b82f6;">',
        '35': '<span style="color:#c084fc;">',
        '36': '<span style="color:#06b6d4;">',
        '37': '<span style="color:#f8fafc;">',
        '90': '<span style="color:#64748b;">',
        '91': '<span style="color:#f87171;">',
        '92': '<span style="color:#4ade80;">',
        '93': '<span style="color:#fde047;">',
        '94': '<span style="color:#60a5fa;">',
        '95': '<span style="color:#e879f9;">',
        '96': '<span style="color:#22d3ee;">',
        '97': '<span style="color:#ffffff;">',
        '1;31': '<span style="color:#ef4444;font-weight:bold;">',
        '1;32': '<span style="color:#22c55e;font-weight:bold;">',
        '1;33': '<span style="color:#fbbf24;font-weight:bold;">',
        '1;34': '<span style="color:#3b82f6;font-weight:bold;">',
        '1;35': '<span style="color:#c084fc;font-weight:bold;">',
        '1;36': '<span style="color:#06b6d4;font-weight:bold;">',
    }

    def replace_ansi(match):
        code = match.group(1)
        if code in fg_map:
            return fg_map[code]
        elif code == '0' or code == '':
            return '</span>'
        else:
            return ''

    # Replace escape codes \x1b[...]m
    text = re.sub(r'\x1b\[([0-9;]*)m', replace_ansi, text)
    # Strip any remaining control codes \x1b[...]
    text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    return text


# ── Stress Test Presets ──────────────────────────────────────────────────────

STRESS_PRESETS = [
    {
        "name": "🟢 LIGHT LOAD",
        "mode": "normal",
        "concurrency": 10,
        "requests": 200,
        "description": "Steady traffic load with 10ms delays",
        "expected": "HTTP 200 (All Pass)",
        "accent": COLOR_SUCCESS,
    },
    {
        "name": "🟡 NORMAL LOAD",
        "mode": "normal",
        "concurrency": 50,
        "requests": 1000,
        "description": "Standard load test with moderate concurrency",
        "expected": "HTTP 200 (All Pass)",
        "accent": COLOR_WARN,
    },
    {
        "name": "🔴 HEAVY LOAD",
        "mode": "bruteforce",
        "concurrency": 100,
        "requests": 5000,
        "description": "Flood requests to trigger Token Bucket rate limiter",
        "expected": "HTTP 200 + 429 (Rate Limited)",
        "accent": COLOR_DANGER,
    },
    {
        "name": "🛡️ WAF TEST (SQLI)",
        "mode": "sqli",
        "concurrency": 20,
        "requests": 200,
        "description": "SQL Injection payloads to verify WAF protection",
        "expected": "HTTP 403 (Blocked by WAF)",
        "accent": ACCENT_CYAN,
    },
    {
        "name": "⚡ MAX STRESS",
        "mode": "bruteforce",
        "concurrency": 200,
        "requests": 10000,
        "description": "Extreme throughput and concurrency stress test",
        "expected": "HTTP 200 + 429 (Heavy Rate Limiting)",
        "accent": ACCENT_PURPLE,
    },
]


# ── Background Stats Poller Thread ───────────────────────────────────────────

class StatsPoller(QThread):
    """Background thread polling /stats every second without blocking UI."""

    stats_received = pyqtSignal(dict)
    stats_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

    def run(self):
        while self._running:
            try:
                req = urllib.request.Request("http://127.0.0.1:3000/stats")
                with urllib.request.urlopen(req, timeout=1.0) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    self.stats_received.emit(data)
            except Exception as e:
                self.stats_error.emit(str(e))
            
            for _ in range(10):
                if not self._running:
                    break
                time.sleep(0.1)

    def stop(self):
        self._running = False
        self.wait(2000)


# ── AI Agent Background Worker Thread ────────────────────────────────────────

class AgentWorkerThread(QThread):
    """Background thread running VanguardAIAgent analysis without blocking the UI."""

    thought = pyqtSignal(str, str)         # (tag, message)
    ban_ready = pyqtSignal(str, str, str)  # (ip, reason, firestore_doc_id)
    error = pyqtSignal(str)

    def __init__(self, agent, log_entry: str, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.log_entry = log_entry

    def run(self):
        try:
            self.thought.emit("SYSTEM", "Anomaly detected — processing suspicious log…")
            time.sleep(0.3)

            self.thought.emit("AI", "Calling Gemini 3.5 Flash for threat analysis…")
            result = self.agent.analyze_threat(self.log_entry)

            action = result.get("action", "").lower()
            ip = result.get("ip", "unknown")
            reason = result.get("reason", "Malicious activity detected")

            self.thought.emit("AI", f"Threat: {reason}. Action: {action.upper()}. Target IP: {ip}")

            if action == "ban" and ip and ip.lower() != "unknown":
                self.thought.emit("AI", "Executing Auto-Ban pipeline…")

                doc_id = ""
                if self.agent.db:
                    try:
                        doc_id = self.agent.log_to_firestore(ip=ip, reason=reason)
                        self.thought.emit("FIRESTORE", f"Threat logged to Firestore — Doc ID: {doc_id}")
                    except Exception as e:
                        self.thought.emit("ERROR", f"Firestore logging failed: {e}")
                else:
                    self.thought.emit("SYSTEM", "Firestore not configured — skipping cloud log.")

                self.ban_ready.emit(ip, reason, doc_id)
            else:
                self.thought.emit("SYSTEM", f"Analysis complete — no ban action required (action={action})")

        except Exception as e:
            self.thought.emit("ERROR", f"Agent pipeline failed: {e}")
            self.error.emit(str(e))


# ── Pulsing Status Indicator Dot ─────────────────────────────────────────────

class PulsingDot(QWidget):
    """Animated pulsing indicator dot for server status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._color = QColor(COLOR_DANGER)
        self._opacity = 1.0

        self.anim = QPropertyAnimation(self, b"opacity")
        self.anim.setDuration(900)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.25)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.anim.setLoopCount(-1)
        self.anim.start()

    def set_color(self, color_str):
        self._color = QColor(color_str)
        self.update()

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, val):
        self._opacity = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        painter.setBrush(QBrush(c))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())


# ── Status Metric Card ───────────────────────────────────────────────────────

class StatusCard(QFrame):
    """Metric display card enclosed in a purple HUD border frame with transparent text backgrounds."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setStyleSheet(f"""
            QFrame#statusCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_PURPLE_DIM};
                border-radius: 4px;
            }}
            QFrame#statusCard:hover {{
                background-color: {BG_CARD_HOVER};
                border: 1px solid {BORDER_PURPLE};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-weight: bold;
            font-size: 9px;
            font-family: {MONO_FONT};
            letter-spacing: 1px;
            border: none;
            background: transparent;
        """)
        
        self.val_layout = QHBoxLayout()
        self.val_layout.setContentsMargins(0, 0, 0, 0)
        self.val_layout.setSpacing(6)

        self.val_label = QLabel("--")
        self.val_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-weight: bold;
            font-size: 16px;
            font-family: {MONO_FONT};
            border: none;
            background: transparent;
        """)
        
        self.val_layout.addWidget(self.val_label)
        self.val_layout.addStretch()
        
        layout.addWidget(self.title_label)
        layout.addLayout(self.val_layout)
        
    def set_value(self, text, color=None):
        self.val_label.setText(text)
        c = color or TEXT_PRIMARY
        self.val_label.setStyleSheet(f"""
            color: {c};
            font-weight: bold;
            font-size: 16px;
            font-family: {MONO_FONT};
            border: none;
            background: transparent;
        """)

    def add_widget(self, widget):
        self.val_layout.insertWidget(0, widget)


# ── Monospace Command Input ──────────────────────────────────────────────────

class CommandInput(QLineEdit):
    """Terminal input field with command history navigation and transparent background."""

    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.history_idx = -1
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_VOID};
                color: {ACCENT_PURPLE_LIGHT};
                border: 1px solid {BORDER_PURPLE_DIM};
                border-radius: 4px;
                padding: 6px 10px;
                font-family: {MONO_FONT};
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border: 1px solid {BORDER_PURPLE};
                background-color: #05040a;
            }}
        """)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            cmd = self.text().strip()
            if cmd:
                self.history.append(cmd)
                self.history_idx = len(self.history)
                self.command_submitted.emit(cmd)
                self.clear()
        elif event.key() == Qt.Key.Key_Up:
            if self.history and self.history_idx > 0:
                self.history_idx -= 1
                self.setText(self.history[self.history_idx])
        elif event.key() == Qt.Key.Key_Down:
            if self.history and self.history_idx < len(self.history) - 1:
                self.history_idx += 1
                self.setText(self.history[self.history_idx])
            else:
                self.history_idx = len(self.history)
                self.clear()
        else:
            super().keyPressEvent(event)


# ── Stress Test Modal Dialog ─────────────────────────────────────────────────

class StressTestDialog(QDialog):
    """Modal dialog for selecting a stress test profile."""

    preset_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("[ VANGUARD V2 // STRESS TEST CONFIG ]")
        self.setFixedSize(580, 640)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_PURPLE};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header Frame
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            background-color: {BG_CARD};
            border: 1px solid {BORDER_PURPLE_DIM};
            border-radius: 4px;
            padding: 8px;
        """)
        tf_layout = QVBoxLayout(title_frame)
        tf_layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("⚡ [ SELECT STRESS TEST PROFILE ]")
        title.setStyleSheet(f"color: {COLOR_WARN}; font-size: 15px; font-weight: bold; font-family: {MONO_FONT}; letter-spacing: 2px; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tf_layout.addWidget(title)

        desc = QLabel("SELECT PRESET PAYLOAD PROFILE TO STRESS TEST EDGE PROXY & WAF RULES")
        desc.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-family: {MONO_FONT}; background: transparent;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tf_layout.addWidget(desc)

        layout.addWidget(title_frame)

        # Preset Buttons
        for preset in STRESS_PRESETS:
            btn = QPushButton()
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BG_CARD};
                    color: {TEXT_PRIMARY};
                    border: 1px solid {BORDER_PURPLE_DIM};
                    border-left: 4px solid {preset['accent']};
                    border-radius: 4px;
                    text-align: left;
                    padding: 10px;
                    font-family: {MONO_FONT};
                }}
                QPushButton:hover {{
                    background-color: {BG_CARD_HOVER};
                    border: 1px solid {BORDER_PURPLE};
                    border-left: 4px solid {preset['accent']};
                }}
            """)
            
            btn_layout = QVBoxLayout(btn)
            btn_layout.setContentsMargins(8, 4, 8, 4)
            btn_layout.setSpacing(3)
            
            h_layout = QHBoxLayout()
            name_lbl = QLabel(preset["name"].upper())
            name_lbl.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {preset['accent']}; font-family: {MONO_FONT}; background: transparent;")
            stats_lbl = QLabel(f"CONC:{preset['concurrency']} | REQS:{preset['requests']} | MODE:{preset['mode'].upper()}")
            stats_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-family: {MONO_FONT}; background: transparent;")
            
            h_layout.addWidget(name_lbl)
            h_layout.addStretch()
            h_layout.addWidget(stats_lbl)
            
            desc_lbl = QLabel(f"{preset['description']}  → EXPECT: {preset['expected']}")
            desc_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-family: {MONO_FONT}; background: transparent;")
            
            btn_layout.addLayout(h_layout)
            btn_layout.addWidget(desc_lbl)
            
            btn.clicked.connect(lambda checked, p=preset: self._on_preset_click(p))
            layout.addWidget(btn)
            
        layout.addStretch()
        
        cancel_btn = QPushButton("✕ CANCEL")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_CARD};
                color: {TEXT_DIM};
                border: 1px solid {BORDER_PURPLE_DIM};
                border-radius: 4px;
                padding: 10px;
                font-family: {MONO_FONT};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1a0b29;
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_PURPLE};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def _on_preset_click(self, preset):
        self.preset_selected.emit(preset)
        self.accept()


# ── Tactical Command Center Main Window ──────────────────────────────────────

class VanguardControlCenter(QMainWindow):
    """Main Window implementing the Tactical Cyberpunk Breach HUD Layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VANGUARD V2 // CONTROL CENTER")
        self.setMinimumSize(1150, 780)
        self.resize(1280, 840)
        self.setStyleSheet(f"background-color: {BG_VOID};")

        self._processes = {}
        self._external_pids = {}
        self._stats_history = deque([0]*60, maxlen=60)
        self._prev_total = None
        self._prev_time = None

        # AI SOC Agent (lazy-initialized on first use)
        self._ai_agent = None
        self._agent_thread = None
        
        self._init_ui()
        
        # Background Stats Poller Thread
        self.poller = StatsPoller()
        self.poller.stats_received.connect(self._on_stats)
        self.poller.stats_error.connect(self._on_stats_error)
        self.poller.start()
        
        # Process Discovery Timer (Sync external process state every 2s)
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self._sync_external_processes)
        self.sync_timer.start(2000)
        
        # Live Chart Refresh Timer (1s)
        self.chart_timer = QTimer(self)
        self.chart_timer.timeout.connect(self._update_chart)
        self.chart_timer.start(1000)

        # Header Live Clock Timer (1s)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_header_clock)
        self.clock_timer.start(1000)

        self._term_write_system("VANGUARD CONTROL CENTER V2 INITIALIZED // PURPLE HACKER DASHBOARD ACTIVE.")

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ── 1. TOP WARNING HEADER BAR ────────────────────────────────────────
        header_panel = QFrame()
        header_panel.setObjectName("headerPanel")
        header_panel.setStyleSheet(f"""
            QFrame#headerPanel {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_PURPLE};
                border-radius: 4px;
            }}
        """)
        hp_layout = QHBoxLayout(header_panel)
        hp_layout.setContentsMargins(14, 8, 14, 8)

        warn_icon = QLabel("⚠️ ::")
        warn_icon.setStyleSheet(f"color: {COLOR_WARN}; font-size: 14px; font-weight: bold; font-family: {MONO_FONT}; border: none; background: transparent;")
        
        header_title = QLabel("[ VANGUARD V2 // SECURITY CONTROL CENTER ]")
        header_title.setStyleSheet(f"""
            color: {ACCENT_PURPLE_LIGHT};
            font-size: 15px;
            font-weight: bold;
            font-family: {MONO_FONT};
            letter-spacing: 3px;
            background: transparent;
            border: none;
        """)

        warn_icon2 = QLabel(":: ⚠️")
        warn_icon2.setStyleSheet(f"color: {COLOR_WARN}; font-size: 14px; font-weight: bold; font-family: {MONO_FONT}; border: none; background: transparent;")

        self.timestamp_label = QLabel(f"TIMESTAMP: {datetime.now().strftime('%H:%M:%S')}")
        self.timestamp_label.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 12px; font-weight: bold; font-family: {MONO_FONT}; letter-spacing: 1px; border: none; background: transparent;")

        hp_layout.addWidget(warn_icon)
        hp_layout.addWidget(header_title)
        hp_layout.addWidget(warn_icon2)
        hp_layout.addStretch()
        hp_layout.addWidget(self.timestamp_label)

        main_layout.addWidget(header_panel)

        # ── 2. MAIN 3-COLUMN TACTICAL HUD SPLITTER ───────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {BORDER_PURPLE_DIM};
                width: 2px;
            }}
        """)

        # ── LEFT COLUMN: LIVE INTRUSION LOGS & TERMINAL ──
        logs_panel = QFrame()
        logs_panel.setObjectName("logsPanel")
        logs_panel.setStyleSheet(f"""
            QFrame#logsPanel {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_PURPLE};
                border-radius: 4px;
            }}
        """)
        lp_layout = QVBoxLayout(logs_panel)
        lp_layout.setContentsMargins(10, 10, 10, 10)
        lp_layout.setSpacing(6)

        logs_hdr = QLabel("[ LIVE INTRUSION EVENTS // LOG STREAM ]")
        logs_hdr.setStyleSheet(f"color: {ACCENT_PURPLE}; font-size: 11px; font-weight: bold; font-family: {MONO_FONT}; letter-spacing: 1px; border: none; background: transparent;")
        lp_layout.addWidget(logs_hdr)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_VOID};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_PURPLE_DIM};
                border-radius: 4px;
                font-family: {MONO_FONT};
                font-size: 11px;
                padding: 6px;
            }}
            QScrollBar:vertical {{
                background: {BG_VOID};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER_PURPLE_DIM};
                min-height: 16px;
                border-radius: 3px;
            }}
        """)
        lp_layout.addWidget(self.terminal)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(4)
        prompt = QLabel("$")
        prompt.setStyleSheet(f"color: {ACCENT_PURPLE_LIGHT}; font-weight: bold; font-family: {MONO_FONT}; font-size: 12px; border: none; background: transparent;")
        self.cmd_input = CommandInput()
        self.cmd_input.command_submitted.connect(self._on_manual_command)
        input_layout.addWidget(prompt)
        input_layout.addWidget(self.cmd_input)
        lp_layout.addLayout(input_layout)

        splitter.addWidget(logs_panel)

        # ── CENTER COLUMN: REALTIME RPS TRAFFIC MONITOR ──
        center_panel = QFrame()
        center_panel.setObjectName("centerPanel")
        center_panel.setStyleSheet(f"""
            QFrame#centerPanel {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_PURPLE};
                border-radius: 4px;
            }}
        """)
        cp_layout = QVBoxLayout(center_panel)
        cp_layout.setContentsMargins(10, 10, 10, 10)
        cp_layout.setSpacing(8)

        chart_hdr = QLabel("[ REALTIME RPS TRAFFIC MONITOR ]")
        chart_hdr.setStyleSheet(f"color: {ACCENT_PURPLE}; font-size: 11px; font-weight: bold; font-family: {MONO_FONT}; letter-spacing: 1px; border: none; background: transparent;")
        cp_layout.addWidget(chart_hdr)

        # Status Banner Box
        banner_box = QFrame()
        banner_box.setStyleSheet(f"""
            background-color: {BG_CARD};
            border: 1px solid {BORDER_PURPLE_DIM};
            border-radius: 4px;
            padding: 6px;
        """)
        bb_layout = QHBoxLayout(banner_box)
        bb_layout.setContentsMargins(10, 4, 10, 4)

        self.banner_status_lbl = QLabel("[ SYSTEM STATUS: ONLINE ]")
        self.banner_status_lbl.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold; font-size: 12px; font-family: {MONO_FONT}; border: none; background: transparent;")
        self.banner_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bb_layout.addWidget(self.banner_status_lbl)
        cp_layout.addWidget(banner_box)

        # pyqtgraph RPS chart
        pg.setConfigOption('background', BG_VOID)
        pg.setConfigOption('foreground', TEXT_DIM)
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setStyleSheet(f"border: 1px solid {BORDER_PURPLE_DIM}; border-radius: 4px;")
        self.chart_widget.showGrid(x=False, y=True, alpha=0.15)
        self.chart_widget.setLabel('left', 'RPS', **{'font-family': 'Consolas', 'font-size': '8pt', 'color': TEXT_DIM})
        self.chart_widget.setLabel('bottom', 'Seconds Ago', **{'font-family': 'Consolas', 'font-size': '8pt', 'color': TEXT_DIM})
        self.chart_widget.setYRange(0, 10)
        self.chart_widget.getAxis('left').setStyle(tickFont=QFont("Consolas", 8))
        self.chart_widget.getAxis('bottom').setStyle(tickFont=QFont("Consolas", 8))
        
        pen = pg.mkPen(color=ACCENT_PURPLE, width=2)
        brush = pg.mkBrush(color=QColor(168, 85, 247, 35))
        self.curve = self.chart_widget.plot([], [], pen=pen, fillLevel=0, brush=brush)
        
        cp_layout.addWidget(self.chart_widget)
        splitter.addWidget(center_panel)

        # ── RIGHT COLUMN: CORE METRICS & PROCESS CONTROLS ──
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_panel.setStyleSheet(f"""
            QFrame#rightPanel {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_PURPLE};
                border-radius: 4px;
            }}
        """)
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(10, 10, 10, 10)
        rp_layout.setSpacing(10)

        right_hdr = QLabel("[ CORE METRICS & CONTROLS ]")
        right_hdr.setStyleSheet(f"color: {ACCENT_PURPLE}; font-size: 11px; font-weight: bold; font-family: {MONO_FONT}; letter-spacing: 1px; border: none; background: transparent;")
        rp_layout.addWidget(right_hdr)

        # Status Cards Layout
        cards_vlayout = QVBoxLayout()
        cards_vlayout.setSpacing(6)

        self.card_status = StatusCard("SERVER STATUS")
        self.dot = PulsingDot()
        self.card_status.add_widget(self.dot)
        self.card_status.set_value("OFFLINE", COLOR_DANGER)
        
        self.card_uptime = StatusCard("UPTIME")
        self.card_uptime.set_value("0s")
        
        self.card_requests = StatusCard("TOTAL REQUESTS")
        self.card_requests.set_value("0")
        
        self.card_conns = StatusCard("ACTIVE CONNS")
        self.card_conns.set_value("0")
        
        self.card_rps = StatusCard("CURRENT RPS")
        self.card_rps.set_value("0.0")

        cards_vlayout.addWidget(self.card_status)
        cards_vlayout.addWidget(self.card_uptime)
        cards_vlayout.addWidget(self.card_requests)
        cards_vlayout.addWidget(self.card_conns)
        cards_vlayout.addWidget(self.card_rps)

        rp_layout.addLayout(cards_vlayout)
        rp_layout.addSpacing(6)

        # Controls Section
        ctrl_title = QLabel("[ ACTION CONTROLS ]")
        ctrl_title.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-weight: bold; font-family: {MONO_FONT}; letter-spacing: 1px; border: none; background: transparent;")
        rp_layout.addWidget(ctrl_title)

        self.btn_backend = QPushButton("▶ START BACKEND")
        self.btn_backend.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_backend.clicked.connect(lambda: self._toggle_process("Backend", "./my_server", []))
        
        self.btn_proxy = QPushButton("▶ START PROXY")
        self.btn_proxy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_proxy.clicked.connect(lambda: self._toggle_process("Proxy", "./vanguard_proxy", []))
        
        self.btn_stress = QPushButton("⚡ LAUNCH STRESS TEST")
        self.btn_stress.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stress.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1204;
                color: {COLOR_WARN};
                border: 1px solid #d97706;
                border-radius: 4px;
                padding: 8px;
                font-family: {MONO_FONT};
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: #2b1c06;
                border: 1px solid {COLOR_WARN};
            }}
        """)
        self.btn_stress.clicked.connect(self._open_stress_dialog)

        # AI Analyze Button
        self.btn_ai_analyze = QPushButton("🧠 AI ANALYZE LOG")
        self.btn_ai_analyze.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ai_analyze.setStyleSheet(f"""
            QPushButton {{
                background-color: #0a1a24;
                color: {ACCENT_CYAN};
                border: 1px solid {ACCENT_CYAN};
                border-radius: 4px;
                padding: 8px;
                font-family: {MONO_FONT};
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: #0d2836;
                color: #ffffff;
                border: 1px solid {BORDER_PURPLE_GLOW};
            }}
        """)
        self.btn_ai_analyze.clicked.connect(lambda: self._launch_ai_analysis())
        
        self._update_button_state("Backend", False)
        self._update_button_state("Proxy", False)
        
        rp_layout.addWidget(self.btn_backend)
        rp_layout.addWidget(self.btn_proxy)
        rp_layout.addWidget(self.btn_stress)
        rp_layout.addWidget(self.btn_ai_analyze)

        splitter.addWidget(logs_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)

        splitter.setSizes([340, 520, 320])
        main_layout.addWidget(splitter)

        # ── 3. AI AGENT THOUGHT PROCESS PANEL ────────────────────────────────
        ai_panel = QFrame()
        ai_panel.setObjectName("aiPanel")
        ai_panel.setStyleSheet(f"""
            QFrame#aiPanel {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_PURPLE};
                border-radius: 4px;
            }}
        """)
        ai_layout = QVBoxLayout(ai_panel)
        ai_layout.setContentsMargins(10, 8, 10, 8)
        ai_layout.setSpacing(4)

        ai_hdr = QLabel("[ AI AGENT THOUGHT PROCESS ]")
        ai_hdr.setStyleSheet(f"""
            color: {ACCENT_PURPLE};
            font-size: 11px;
            font-weight: bold;
            font-family: {MONO_FONT};
            letter-spacing: 1px;
            border: none;
            background: transparent;
        """)
        ai_layout.addWidget(ai_hdr)

        self.ai_thought_box = QTextEdit()
        self.ai_thought_box.setReadOnly(True)
        self.ai_thought_box.setFixedHeight(130)
        self.ai_thought_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_VOID};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_PURPLE_DIM};
                border-radius: 4px;
                font-family: {MONO_FONT};
                font-size: 11px;
                padding: 6px;
            }}
            QScrollBar:vertical {{
                background: {BG_VOID};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER_PURPLE_DIM};
                min-height: 16px;
                border-radius: 3px;
            }}
        """)
        ai_layout.addWidget(self.ai_thought_box)

        main_layout.addWidget(ai_panel)

        # ── 4. BOTTOM FOOTER BAR ─────────────────────────────────────────────
        footer_panel = QFrame()
        footer_panel.setStyleSheet(f"""
            background-color: {BG_PANEL};
            border: 1px solid {BORDER_PURPLE_DIM};
            border-radius: 4px;
            padding: 4px;
        """)
        fp_layout = QHBoxLayout(footer_panel)
        fp_layout.setContentsMargins(10, 4, 10, 4)

        footer_text = QLabel("VANGUARD-V2 :: EDGE PROXY & WAF ENGINE :: SYSTEM OPERATIONAL [0.0.0.0:8080 -> 127.0.0.1:3000]")
        footer_text.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-family: {MONO_FONT}; border: none; background: transparent;")
        fp_layout.addWidget(footer_text)
        fp_layout.addStretch()

        footer_right = QLabel("ALL SYSTEMS MONITORED")
        footer_right.setStyleSheet(f"color: {ACCENT_PURPLE_LIGHT}; font-size: 10px; font-family: {MONO_FONT}; border: none; background: transparent;")
        fp_layout.addWidget(footer_right)

        main_layout.addWidget(footer_panel)

    def _update_header_clock(self):
        self.timestamp_label.setText(f"TIMESTAMP: {datetime.now().strftime('%H:%M:%S')}")

    # ── Toggle Button Styling ────────────────────────────────────────────────

    def _update_button_state(self, label: str, is_running: bool):
        if label == "Backend":
            if is_running:
                self.btn_backend.setText("■ STOP BACKEND")
                self.btn_backend.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #280909;
                        color: {COLOR_DANGER};
                        border: 1px solid {COLOR_DANGER};
                        border-radius: 4px;
                        padding: 8px;
                        font-family: {MONO_FONT};
                        font-weight: bold;
                        font-size: 10px;
                        letter-spacing: 1px;
                    }}
                    QPushButton:hover {{ background-color: #3a0f0f; }}
                """)
            else:
                self.btn_backend.setText("▶ START BACKEND")
                self.btn_backend.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #130924;
                        color: {ACCENT_PURPLE_LIGHT};
                        border: 1px solid {BORDER_PURPLE};
                        border-radius: 4px;
                        padding: 8px;
                        font-family: {MONO_FONT};
                        font-weight: bold;
                        font-size: 10px;
                        letter-spacing: 1px;
                    }}
                    QPushButton:hover {{ background-color: #1e0d36; color: #ffffff; }}
                """)
        elif label == "Proxy":
            if is_running:
                self.btn_proxy.setText("■ STOP PROXY")
                self.btn_proxy.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #280909;
                        color: {COLOR_DANGER};
                        border: 1px solid {COLOR_DANGER};
                        border-radius: 4px;
                        padding: 8px;
                        font-family: {MONO_FONT};
                        font-weight: bold;
                        font-size: 10px;
                        letter-spacing: 1px;
                    }}
                    QPushButton:hover {{ background-color: #3a0f0f; }}
                """)
            else:
                self.btn_proxy.setText("▶ START PROXY")
                self.btn_proxy.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #130924;
                        color: {ACCENT_CYAN};
                        border: 1px solid {ACCENT_CYAN};
                        border-radius: 4px;
                        padding: 8px;
                        font-family: {MONO_FONT};
                        font-weight: bold;
                        font-size: 10px;
                        letter-spacing: 1px;
                    }}
                    QPushButton:hover {{ background-color: #1e0d36; color: #ffffff; }}
                """)

    # ── Terminal Logging Helpers (with ANSI-to-HTML Parser) ──────────────────

    def _term_write(self, html):
        self.terminal.append(html)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

    def _term_write_system(self, msg):
        time_str = datetime.now().strftime("%H:%M:%S")
        parsed_msg = ansi_to_html(msg)
        self._term_write(f"<span style='color:{TEXT_MUTED}'>[{time_str}]</span> <span style='color:{ACCENT_PURPLE_LIGHT}'>[SYS]</span> {parsed_msg}")

    def _term_write_stdout(self, label, msg):
        time_str = datetime.now().strftime("%H:%M:%S")
        color = COLOR_SUCCESS if label == "Backend" else ACCENT_CYAN
        parsed_msg = ansi_to_html(msg)
        self._term_write(f"<span style='color:{TEXT_MUTED}'>[{time_str}]</span> <span style='color:{color}'>[{label.upper()}]</span> {parsed_msg}")

    def _term_write_stderr(self, label, msg):
        time_str = datetime.now().strftime("%H:%M:%S")
        parsed_msg = ansi_to_html(msg)
        self._term_write(f"<span style='color:{TEXT_MUTED}'>[{time_str}]</span> <span style='color:{COLOR_WARN}'>[{label.upper()} ERR]</span> {parsed_msg}")

    # ── Service State & Process Management ──────────────────────────────────

    def _is_service_running(self, label: str) -> bool:
        if label in self._external_pids:
            return True
        if label in self._processes:
            return self._processes[label].state() != QProcess.ProcessState.NotRunning
        return False

    def _toggle_process(self, label, program, args):
        if self._is_service_running(label):
            self._stop_process(label)
        else:
            self._start_process(label, program, args)

    def _start_process(self, label, program, args):
        if label in self._processes and self._processes[label].state() != QProcess.ProcessState.NotRunning:
            return
            
        proc = QProcess(self)
        self._processes[label] = proc
        
        proc.readyReadStandardOutput.connect(lambda: self._on_proc_stdout(label))
        proc.readyReadStandardError.connect(lambda: self._on_proc_stderr(label))
        proc.finished.connect(lambda exitCode, exitStatus: self._on_proc_finished(label, exitCode, exitStatus))
        
        self._term_write_system(f"Launching {label}: {program} {' '.join(args)}")
        proc.start(program, args)
        self._update_button_state(label, True)

    def _stop_process(self, label: str):
        """Terminate managed or externally detected service gracefully with OS fallback."""
        if label in self._external_pids:
            pid = self._external_pids[label]
            self._term_write_system(f"[{label.upper()}] Terminating external process (PID {pid})...")
            killed = False
            
            if HAS_PSUTIL:
                service_names = {"Backend": "my_server", "Proxy": "vanguard_proxy"}
                target_name = service_names.get(label, "")
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        pname = proc.info['name'] or ''
                        if pname == target_name or pname == f"{target_name}.exe" or pname.startswith(target_name):
                            self._term_write_system(f"[{label.upper()}] Terminating {pname} (PID {proc.info['pid']})...")
                            p = psutil.Process(proc.info['pid'])
                            p.terminate()
                            try:
                                p.wait(timeout=3)
                                killed = True
                            except psutil.TimeoutExpired:
                                p.kill()
                                p.wait(timeout=2)
                                killed = True
                                self._term_write_system(f"[{label.upper()}] Force-killed PID {proc.info['pid']}.")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError) as e:
                        self._term_write_stderr(label, f"Error stopping PID: {e}")
                        continue
            
            if not killed:
                try:
                    os.kill(pid, signal.SIGTERM)
                    killed = True
                    self._term_write_system(f"[{label.upper()}] Sent SIGTERM to PID {pid}.")
                except (ProcessLookupError, PermissionError, OSError) as e:
                    self._term_write_stderr(label, f"OS kill fallback failed: {e}")
            
            if label in self._external_pids:
                del self._external_pids[label]
            self._update_button_state(label, False)
            
            if killed:
                self._term_write_system(f"[{label.upper()}] External process terminated.")
            else:
                self._term_write_stderr(label, "Could not terminate external process.")
            return

        if label in self._processes:
            proc = self._processes[label]
            if proc.state() != QProcess.ProcessState.NotRunning:
                pid = proc.processId()
                self._term_write_system(f"[{label.upper()}] Stopping managed process (PID {pid})...")
                proc.terminate()
                if not proc.waitForFinished(3000):
                    proc.kill()
                    proc.waitForFinished(2000)
                    self._term_write_system(f"[{label.upper()}] Force-killed PID {pid}.")
                return

        self._term_write_system(f"[{label.upper()}] No running process found.")

    def _on_proc_stdout(self, label):
        proc = self._processes.get(label)
        if proc:
            data = proc.readAllStandardOutput().data().decode('utf-8', errors='replace').strip()
            if data:
                for line in data.split('\n'):
                    self._term_write_stdout(label, line)

    def _on_proc_stderr(self, label):
        proc = self._processes.get(label)
        if proc:
            data = proc.readAllStandardError().data().decode('utf-8', errors='replace').strip()
            if data:
                for line in data.split('\n'):
                    self._term_write_stderr(label, line)

    def _on_proc_finished(self, label, exitCode, exitStatus):
        self._term_write_system(f"[{label.upper()}] Process exited (Code: {exitCode})")
        self._update_button_state(label, False)

    # ── Process Discovery Sync (Terminal Sync) ───────────────────────────────

    def _sync_external_processes(self):
        """Scans system processes to sync external terminal executions with GUI buttons."""
        services = {"Backend": "my_server", "Proxy": "vanguard_proxy"}
        
        for label, name in services.items():
            if label in self._processes and self._processes[label].state() != QProcess.ProcessState.NotRunning:
                continue
                
            pid = self._find_external_process(name)
            if pid:
                if label not in self._external_pids:
                    self._external_pids[label] = pid
                    self._update_button_state(label, True)
                    self._term_write_system(f"[{label.upper()}] External process detected via Terminal Sync (PID {pid})")
            else:
                if label in self._external_pids:
                    del self._external_pids[label]
                    self._update_button_state(label, False)
                    self._term_write_system(f"[{label.upper()}] External process terminated externally.")

    def _find_external_process(self, name: str) -> int | None:
        if not HAS_PSUTIL:
            return None
        try:
            my_pid = os.getpid()
            managed_pids = set()
            for proc in self._processes.values():
                if proc.state() != QProcess.ProcessState.NotRunning:
                    managed_pids.add(proc.processId())
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pinfo = proc.info
                    pid = pinfo['pid']
                    pname = pinfo['name'] or ''
                    if pid == my_pid or pid in managed_pids:
                        continue
                    if pname == name or pname == f"{name}.exe" or pname.startswith(name):
                        return pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return None

    # ── Manual Console Command Handler ───────────────────────────────────────

    def _on_manual_command(self, cmd):
        # AI agent analyze shortcut
        if cmd.lower().startswith("analyze "):
            log_entry = cmd[8:].strip()
            if log_entry:
                self._term_write_system(f"AI Analyze: {log_entry[:80]}")
                self._launch_ai_analysis(log_entry)
            else:
                self._ai_thought_write("ERROR", "Usage: analyze <log_entry>")
            return

        self._term_write_system(f"Executing: {cmd}")
        parts = cmd.split()
        if not parts:
            return
        
        proc = QProcess(self)
        proc.readyReadStandardOutput.connect(lambda: self._term_write_stdout("CMD", proc.readAllStandardOutput().data().decode('utf-8', errors='replace')))
        proc.readyReadStandardError.connect(lambda: self._term_write_stderr("CMD", proc.readAllStandardError().data().decode('utf-8', errors='replace')))
        
        proc.start(parts[0], parts[1:])
        
        if not hasattr(self, '_manual_procs'):
            self._manual_procs = []
        self._manual_procs.append(proc)
        proc.finished.connect(lambda: self._manual_procs.remove(proc) if proc in self._manual_procs else None)

    # ── Stress Test Modal Launch ─────────────────────────────────────────────

    def _open_stress_dialog(self):
        dlg = StressTestDialog(self)
        dlg.preset_selected.connect(self._run_stress_preset)
        dlg.exec()

    def _run_stress_preset(self, preset):
        self._term_write_system(f"Launching Stress Test Preset: {preset['name']}")
        args = ["vanguard_stress.py", "-m", preset["mode"], "-c", str(preset["concurrency"]), "-n", str(preset["requests"])]
        self._start_process("StressTest", sys.executable, args)

    # ── AI SOC Agent — Thought Process & Auto-Ban Pipeline ───────────────────

    def _ai_thought_write(self, tag: str, message: str):
        """Write a tagged message to the AI Thought Process box."""
        time_str = datetime.now().strftime("%H:%M:%S")
        tag_colors = {
            "SYSTEM": ACCENT_PURPLE_LIGHT,
            "AI":     ACCENT_CYAN,
            "FIRESTORE": COLOR_SUCCESS,
            "BAN":    COLOR_DANGER,
            "ERROR":  COLOR_DANGER,
        }
        color = tag_colors.get(tag, TEXT_DIM)
        self.ai_thought_box.append(
            f"<span style='color:{TEXT_MUTED}'>[{time_str}]</span> "
            f"<span style='color:{color}'>[{tag}]</span> "
            f"<span style='color:{TEXT_PRIMARY}'>{message}</span>"
        )
        self.ai_thought_box.moveCursor(QTextCursor.MoveOperation.End)

    def _append_to_blacklist(self, ip: str, reason: str):
        """Append banned IP to blacklist.conf, avoiding duplicates."""
        blacklist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blacklist.conf")

        # Check for duplicate
        existing_ips = set()
        if os.path.exists(blacklist_path):
            with open(blacklist_path, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        existing_ips.add(stripped.split("#")[0].strip())

        if ip in existing_ips:
            self._ai_thought_write("BAN", f"IP {ip} already in blacklist.conf — skipping duplicate.")
            return

        with open(blacklist_path, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ip}    # {reason} — banned {timestamp}\n")

        self._ai_thought_write("BAN", f"IP {ip} appended to blacklist.conf")
        self._term_write_system(f"[AI AUTO-BAN] IP {ip} added to blacklist.conf — Reason: {reason}")

    def _restart_proxy(self):
        """Terminate and restart vanguard_proxy to reload blacklist."""
        self._ai_thought_write("SYSTEM", "Terminating vanguard_proxy to reload blacklist…")

        if self._is_service_running("Proxy"):
            self._stop_process("Proxy")
            # Brief delay to allow clean shutdown before restart
            QTimer.singleShot(1500, self._do_restart_proxy)
        else:
            self._ai_thought_write("SYSTEM", "Proxy was not running — starting fresh.")
            self._do_restart_proxy()

    def _do_restart_proxy(self):
        """Delayed restart callback after proxy termination."""
        self._start_process("Proxy", "./vanguard_proxy", [])
        self._ai_thought_write("SYSTEM", "vanguard_proxy restarted with updated blacklist.")

    def _on_ban_ready(self, ip: str, reason: str, doc_id: str):
        """Auto-ban pipeline: append to blacklist → restart proxy."""
        self._append_to_blacklist(ip, reason)
        self._restart_proxy()
        self._ai_thought_write("SYSTEM", "═══ Auto-Ban pipeline complete. Proxy reloaded. ═══")

    def _launch_ai_analysis(self, log_entry: str = None):
        """Launch AI analysis on a given log line, or the last terminal line."""
        # Lazy-initialize agent
        if self._ai_agent is None:
            try:
                self._ai_agent = VanguardAIAgent()
                self._ai_thought_write("SYSTEM", "VanguardAIAgent initialized successfully.")
            except ValueError as e:
                self._ai_thought_write("ERROR", str(e))
                return

        if log_entry is None:
            # Extract the last 15 lines as a context block for Gemini
            text = self.terminal.toPlainText()
            lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

            if not lines:
                self._ai_thought_write("SYSTEM", "No log entries in terminal to analyze.")
                return

            context_lines = lines[-15:]
            log_entry = "\n".join(context_lines)
            self._ai_thought_write("SYSTEM", f"Extracted {len(context_lines)} log lines for contextual analysis.")

        display = (log_entry[:120] + "…") if len(log_entry) > 120 else log_entry
        self._ai_thought_write("SYSTEM", f"Selected log: {display}")

        self._agent_thread = AgentWorkerThread(self._ai_agent, log_entry, parent=self)
        self._agent_thread.thought.connect(self._ai_thought_write)
        self._agent_thread.ban_ready.connect(self._on_ban_ready)
        self._agent_thread.error.connect(lambda e: self._term_write_stderr("AI", e))
        self._agent_thread.start()

    # ── Metrics Polling & Chart Update ───────────────────────────────────────

    def _on_stats(self, data):
        now = time.monotonic()
        self.dot.set_color(COLOR_SUCCESS)

        # Status
        status = data.get("status", "unknown")
        if status == "online":
            self.card_status.set_value("ONLINE", COLOR_SUCCESS)
            self.banner_status_lbl.setText("[ SYSTEM STATUS: ONLINE // PROXY ACTIVE ]")
            self.banner_status_lbl.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold; font-size: 12px; font-family: {MONO_FONT}; border: none; background: transparent;")
        else:
            self.card_status.set_value(status.upper(), COLOR_WARN)
            self.banner_status_lbl.setText(f"[ SYSTEM STATUS: {status.upper()} ]")
            self.banner_status_lbl.setStyleSheet(f"color: {COLOR_WARN}; font-weight: bold; font-size: 12px; font-family: {MONO_FONT}; border: none; background: transparent;")

        # Uptime
        secs = int(data.get("uptime_seconds", 0))
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        parts = []
        if d: parts.append(f"{d}d")
        if h or d: parts.append(f"{h}h")
        parts.append(f"{m}m {s}s")
        self.card_uptime.set_value(" ".join(parts), ACCENT_CYAN)

        # Total requests
        total = int(data.get("total_requests", 0))
        self.card_requests.set_value(f"{total:,}", TEXT_PRIMARY)

        # Active connections
        conns = int(data.get("active_connections", 0))
        if conns < 10:
            conn_color = COLOR_SUCCESS
        elif conns < 50:
            conn_color = COLOR_WARN
        else:
            conn_color = COLOR_DANGER
        self.card_conns.set_value(str(conns), conn_color)

        # RPS calculation
        rps = 0.0
        if self._prev_total is not None and self._prev_time is not None:
            dt = now - self._prev_time
            if dt > 0:
                rps = max(0.0, (total - self._prev_total) / dt)
        self._prev_total = total
        self._prev_time = now
        self._stats_history.append(rps)

        self.card_rps.set_value(f"{rps:.1f}", ACCENT_PURPLE_LIGHT if rps < 100 else COLOR_WARN)

    def _on_stats_error(self, msg):
        self.dot.set_color(COLOR_DANGER)
        self.card_status.set_value("OFFLINE", COLOR_DANGER)
        self.banner_status_lbl.setText("[ SYSTEM STATUS: OFFLINE // NO BACKEND DETECTED ]")
        self.banner_status_lbl.setStyleSheet(f"color: {COLOR_DANGER}; font-weight: bold; font-size: 12px; font-family: {MONO_FONT}; border: none; background: transparent;")
        self.card_uptime.set_value("—", TEXT_DIM)
        self.card_requests.set_value("—", TEXT_DIM)
        self.card_conns.set_value("—", TEXT_DIM)
        self.card_rps.set_value("—", TEXT_DIM)
        self._stats_history.append(0)

    def _update_chart(self):
        n = len(self._stats_history)
        x = list(range(-n + 1, 1))
        y = list(self._stats_history)
        self.curve.setData(x, y)
        if y:
            max_y = max(max(y) * 1.2, 5)
            self.chart_widget.setYRange(0, max_y)

    def closeEvent(self, event):
        self.sync_timer.stop()
        self.chart_timer.stop()
        self.clock_timer.stop()
        self.poller.stop()

        # Stop AI agent thread if running
        if self._agent_thread and self._agent_thread.isRunning():
            self._agent_thread.quit()
            self._agent_thread.wait(2000)
        
        for label, proc in self._processes.items():
            if proc.state() != QProcess.ProcessState.NotRunning:
                proc.kill()
                proc.waitForFinished(1000)
                
        if hasattr(self, '_manual_procs'):
            for proc in self._manual_procs:
                if proc.state() != QProcess.ProcessState.NotRunning:
                    proc.kill()
                    
        event.accept()


# ── Application Main Entry Point ─────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_VOID))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(BG_PANEL))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_PURPLE))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BG_VOID))
    app.setPalette(palette)
    
    app.setFont(QFont("Consolas", 10))
    
    window = VanguardControlCenter()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
