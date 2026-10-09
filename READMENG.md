╔═══════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                           ║
║        ██╗   ██╗ ██████╗  ███╗   ██╗  ██████╗   ██╗   ██╗ ██████╗  ██████╗  ██████╗       ║
║        ██║   ██║ ██╔══██╗ ████╗  ██║  ██╔════╝  ██║   ██║ ██╔══██╗ ██╔══██╗ ██╔══██╗      ║
║        ██║   ██║ ███████║ ██╔██╗ ██║  ██║  ███╗ ██║   ██║ ███████║ ██████╔╝ ██║  ██║      ║
║        ╚██╗ ██╔╝ ██╔══██║ ██║╚██╗██║  ██║   ██║ ██║   ██║ ██╔══██║ ██╔══██╗ ██╔══██║      ║
║         ╚████╔╝  ██║  ██║ ██║ ╚████║  ╚██████╔╝  ╚██████╔╝██║  ██║ ██║  ██║ ██████╔╝      ║
║          ╚═══╝   ╚═╝  ╚═╝ ╚═╝  ╚═══╝   ╚═════╝    ╚═════╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═════╝       ║
║                                                                                           ║
║                         VANGUARD v2 : AUTONOMOUS AI SOC AGENT & WAF ENGINE                ║
║                           Cloudflare-like Reverse Proxy in C++17                          ║
║                                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════════════════════╝

**Vanguard v2 is a high-performance Web Application Firewall (WAF) and Reverse Proxy written completely from scratch in C++17 without using any external frameworks. It runs directly on Linux `epoll(7)` for maximum efficiency and security.** It elevates the architecture to a full-fledged **Autonomous AI SOC Agent**, powered by **Google Gemini 3.5 Flash**, capable of analyzing, making decisions, and automatically blocking cyber threats in real-time with zero human intervention.

<p align="center">
  <img src="https://img.shields.io/badge/HACKATHON-All%20Things%20Agentic-blueviolet?style=flat-square" alt="Hackathon Badge"/>
  <img src="https://img.shields.io/badge/TRACK-Taskmaster-critical?style=flat-square" alt="Track Badge"/>
  <img src="https://img.shields.io/badge/AI-Gemini%203.5%20Flash-blue?style=flat-square&logo=google" alt="Gemini Badge"/>
  <img src="https://img.shields.io/badge/Cloud-Google%20Firestore-orange?style=flat-square&logo=firebase" alt="Firestore Badge"/>
</p>

[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg?style=flat-square&logo=cplusplus)](https://isocpp.org/)
[![License: Proprietary](https://img.shields.io/badge/License-All%20Rights%20Reserved-red.svg?style=flat-square)](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg?style=flat-square&logo=linux)](https://kernel.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker)](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/docker-compose.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-yellow.svg?style=flat-square&logo=python)](https://python.org/)

---

## Table of Contents

- [Project Overview & Value Proposition](#project-overview--value-proposition)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Engineering & AI Features](#engineering--ai-features)
- [Vanguard Control Center v2 (GUI - Muted Purple Theme)](#vanguard-control-center-v2-gui---muted-purple-theme)
- [TUI Dashboard for Terminal](#tui-dashboard-for-terminal)
- [Attack Simulation and System Testing (Simulate & Test)](#attack-simulation-and-system-testing-simulate--test)
- [CLI and Stress Testing Tools](#cli-and-stress-testing-tools)
- [Deployment with Docker](#deployment-with-docker)
- [Project Structure](#project-structure)
- [License](#license)

---

## Project Overview & Value Proposition

Traditional Security Operations Center (SOC) workflows suffer from delays as administrators must manually sift through thousands of lines of logs to identify attackers, leading to slow response times and potential damage.

**Vanguard v2** solves this problem by offering a full-stack network security suite. It consists of a C++ Edge Proxy with a built-in WAF Engine, a backend web server, and Python tools—all integrated with an **Autonomous AI SOC Agent**. Every HTTP request passes through the Vanguard v2 Edge Proxy, which inspects it for SQL Injection and Cross-Site Scripting (XSS) attacks, and enforces per-IP Rate Limiting using a Token Bucket algorithm. When an anomaly is detected, the AI extracts the event context, sends it to Gemini for analysis, dynamically writes firewall rules, restarts the proxy, and logs the incident to Google Cloud Firestore automatically.

| Component | Language | Description |
|---|---|---|
| [`vanguard_proxy.cpp`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/vanguard_proxy.cpp) | C++17 | Edge Proxy with built-in WAF, Rate Limiter, and Reverse Proxy (epoll) |
| [`my_server.cpp`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/my_server.cpp) | C++17 | Private Backend Server with a JSON `/stats` API |
| [`vanguard_gui.py`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/vanguard_gui.py) | Python/PyQt6 | Desktop Control Center (Muted Purple Hacker Dashboard with process discovery & termination) |
| [`vanguard_agent.py`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/vanguard_agent.py) | Python/GenAI | Autonomous AI Agent powered by Gemini 3.5 Flash and logs data to Firestore |
| [`dashboard.py`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/dashboard.py) | Python/Rich | TUI Dashboard for terminal environments |
| [`vanguard_stress.py`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/vanguard_stress.py) | Python/aiohttp | Asynchronous load/stress testing tool |
| [`setup.sh`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/setup.sh) | Bash | One-click setup script (installs APT dependencies, compiles binaries via `make`, configures permissions with `chmod`, and runs `pip install`) |

---

## Quick Start

### ⚡ One-Click Setup ([`setup.sh`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/setup.sh))

A single command to set up the entire system:

```bash
bash setup.sh
```

The [`setup.sh`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/setup.sh) script automatically performs the following 6 steps:
1. 📦 **APT Package Installation**: Runs `sudo apt update && sudo apt install -y build-essential python3-pip python3-venv python3-dev` to install the required system tools and compilers.
2. 🔍 **System Dependency Verification**: Verifies the presence of `g++`, `make`, `python3`, and `pip`.
3. ⚙️ **C++ Binary Compilation**: Compiles `vanguard_proxy` and `my_server` using `make` with optimized flags (`-O3 -std=c++17`).
4. 🔑 **Permissions Configuration**: Grants execution permissions to all compiled binaries and scripts using `chmod +x`.
5. 🐍 **Python Environment & Dependencies**: Sets up a Python Virtual Environment (`./venv`) or falls back to using `--break-system-packages` to install dependencies: `PyQt6`, `pyqtgraph`, `psutil`, `rich`, `aiohttp`, and `requests`.
6. 🧹 **Workspace Artifact Cleanup**: Cleans up leftover Windows Zone Identifier metadata (`Zone.Identifier` files) and legacy v1 artifacts.

🔑 Configure API Keys for AI & Cloud
To enable the Autonomous SOC Agent's features, you need to configure the following environment variables:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
# (Optional) For logging threat intelligence data to Google Cloud Firestore
export GOOGLE_APPLICATION_CREDENTIALS="gcp-key.json"
```

Once the setup is complete, you can launch the GUI immediately:
```bash
# Launch the GUI Control Center (Muted Purple Cyberpunk Theme)
python3 vanguard_gui.py
```

---

## System Architecture

```plaintext  
══════════════════════════════════════════════════════════════
                    ┌──────────────────────────────────────┐
                    │          INTERNET / CLIENTS          │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │       VANGUARD EDGE PROXY            │
                    │       0.0.0.0:8080                   │
                    │  ┌────────────┐  ┌────────────────┐  │
                    │  │  WAF Engine│  │  Rate Limiter  │  │
                    │  │  SQLi + XSS│  │  Token Bucket  │  │
                    │  └──────┬─────┘  └───────┬────────┘  │
                    └─────────┼────────────────┼───────────┘
                               │                │ (Safe Traffic)
                    (Pull Logs)│                ▼
┌──────────────────────┐      │        ┌───────────────────┐
│ PyQt6 Control Center │◄─────┘        │  Backend Server   │
│ ┌──────────────────┐ │               │  127.0.0.1:3000   │
│ │ VanguardAIAgent  │ │               └───────────────────┘
│ │ (Gemini 3.5)     │ │───┐
│ └──────────────────┘ │   │ (Auto-Ban)
└──────────┬───────────┘   ▼
           │           blacklist.conf / whitelist.conf
           │           (AI auto-restarts the Proxy)
           ▼
┌──────────────────────┐
│ Google Firestore     │ (Threat Intelligence Logs)
└──────────────────────┘
```

---

## Engineering & AI Features

### 🔧 C++17 Edge Proxy Powerhouse

- **epoll(7) Non-Blocking I/O**: The proxy utilizes Linux Kernel epoll for `O(1)` event notifications on the listening socket. It accepts incoming connections in a non-blocking loop (`O_NONBLOCK` + `EPOLLIN`) and delegates them to worker handler threads.
- **Zero-Copy HTTP Parsing with std::string_view**: A custom HTTP parser written from scratch operates directly on `std::string_view` pointing to the original receive buffer. It extracts the HTTP Method, URI, Headers, and Body without any dynamic memory allocations or string copying.
- **Thread-Safe Token Bucket Rate Limiter**: Each client IP receives an independent token bucket (default: 10 tokens/second, burst capacity: 10). It is protected by `std::mutex` for thread safety under concurrency.
- **WAF Inspection Engine**: Detects SQL Injection (22 patterns, including `UNION SELECT`, `OR 1=1`, `DROP TABLE`, `SLEEP()`, `BENCHMARK()`) and Cross-Site Scripting (18 patterns, including `<script>`, `javascript:`, `onerror=`, `eval()`, `document.cookie`).

### 🧠 Autonomous AI SOC Agent System

- **Context-Aware Analysis**: The AI goes beyond reading single log lines. It retrieves the last 15 log lines and submits them to Gemini 3.5 Flash to analyze the overall context. This enables accurate distinction between legitimate traffic and actual attacks, significantly reducing false positives.
- **Autonomous Auto-Ban Pipeline (Take Action)**: Upon detecting a threat, the agent parses the structured JSON response, adds the attacker's IP to the blacklist using `psutil`, and triggers a hot-reload of the C++ Proxy. This blocks the hacker automatically, running in a separate `QThread` to prevent the GUI from freezing.
- **Google Cloud Telemetry**: All threat intelligence data, including the AI's reasoning for blocking, is logged to the `blocked_threats` collection in Google Cloud Firestore to maintain a clear audit trail.

---

## Vanguard Control Center v2 (GUI - Muted Purple Theme)

### 🎨 UI/UX Style: Muted Purple Hacker Dashboard

- **Muted Dark Purple Palette**: The primary colors feature clean, dark purple tones (`#6a0dad`, `#5e35b1`, `#7b1fa2`, `#a855f7`) blended with deep black backgrounds (`#050508` / `#0a0a0f`).
- **Monospace Typography**: Styled with monospace fonts (`Consolas`, `'Courier New'`, `Monospace`) across the entire application, utilizing uppercase headers for a terminal-like appearance.
- **Panel Enclosures**: Each section (Stats, Chart, Controls, Terminal) is separated by `QFrame` borders (1px solid `#6a0dad`) with appropriate padding.

### ⚡ Key GUI Features

1. 🔥 **AI Agent Thought Process Terminal (New)**: A real-time simulated Terminal box at the bottom of the window allows administrators to transparently monitor the AI Agent's thought processes, data collection, and actions taken (Take Action).
2. 🔄 **Start/Stop Toggle & OS-Level Process Termination**: Dynamic toggle buttons for Backend and Proxy (Green/Cyan for Start, Red for Stop). The system discovers external processes and terminates them safely at the OS level using `psutil.Process(pid).terminate()` with a fallback to `os.kill(pid, signal.SIGTERM)`.
3. 🔗 **Terminal Sync (Process Discovery)**: Scans for `my_server` and `vanguard_proxy` processes every 2 seconds via `psutil.process_iter()`, automatically syncing the GUI button states with the actual operating system process states.
4. ⚡ **Stress Test Modal Dialog**: Clicking `⚡ LAUNCH STRESS TEST` opens a popup dialog to choose from predefined attack presets to evaluate WAF and AI accuracy:

| Profile | Mode | Concurrency | Requests | Description |
|---|---|---|---|---|
| 🟢 LIGHT LOAD | normal | 10 | 200 | Normal traffic with a 10ms delay |
| 🟡 NORMAL LOAD | normal | 50 | 1,000 | Standard load testing |
| 🔴 HEAVY LOAD | bruteforce | 100 | 5,000 | High request volume to test the Token Bucket rate limiter |
| 🛡️ WAF TEST (SQLI) | sqli | 20 | 200 | Sends SQL Injection payloads to test WAF blocking (HTTP 403) |
| ⚡ MAX STRESS | bruteforce | 200 | 10,000 | Maximum capacity stress test |

---

## TUI Dashboard for Terminal

For headless or terminal-only environments:

```bash
python3 dashboard.py
```

---

## Attack Simulation and System Testing (Simulate & Test)

In addition to the Stress Testing tool, the system includes scripts for simulating attacks and running automated integration tests to verify WAF and Proxy operations:

### 1. Attack Simulation ([`simulate_attack.sh`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/simulate_attack.sh))

This script simulates traffic from both regular users and attackers to verify if the WAF and Rate Limiter block malicious behaviors correctly:

```bash
# ⚠️ Warning: Ensure both vanguard_proxy and my_server are running before executing this script.!
bash simulate_attack.sh
```

The script runs tests across 4 scenarios:
- **Scenario 1:** Normal User (Regular traffic, expects HTTP 200)
- **Scenario 2:** Brute Force / Rate Limit (15 rapid requests, expects HTTP 429)
- **Scenario 3:** WAF Test - SQL Injection (Sends SQLi payload, expects HTTP 403)
- **Scenario 4:** WAF Test - Cross-Site Scripting (Sends XSS payload, expects HTTP 403)

### 2. Automated Integration Testing ([`test.sh`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/test.sh))

Script for end-to-end integration tests between the Proxy and Backend:

```bash
bash test.sh
```

Runs a total of 9 integration test cases covering request forwarding, header modification (Server, Content-Length), JSON stats retrieval via `/stats`, WAF protection, and rate limiting.

### 3. Whitelist / Blacklist Configuration

The system supports custom configuration files:
- [`whitelist.conf`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/whitelist.conf): Restricts rate limiting for specific IPs (e.g., administrator IPs) while keeping WAF inspection active.
- [`blacklist.conf`](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/blacklist.conf): The file where the Autonomous AI Agent writes detected attacker IPs to automatically block connections (Auto-Ban).

---

## CLI and Stress Testing Tools

```bash
# Test Normal Traffic
python3 vanguard_stress.py -m normal

# Test Bruteforce (Rate Limiter)
python3 vanguard_stress.py -m bruteforce -c 100 -n 5000

# Test WAF Rules
python3 vanguard_stress.py -m sqli -c 20 -n 200
```

---

## Deployment with Docker

```bash
# Build and run via Docker Compose
sudo docker compose up -d

# View Logs
sudo docker compose logs -f

# Stop services
sudo docker compose down
```

---

## Project Structure

```plaintext
PROJECTVANGUARD/
├── setup.sh                # ⚡ One-Click Setup script (APT + Build + PyDeps + Cleanup)
├── vanguard_proxy.cpp      # Edge Proxy + WAF Engine (C++17, epoll)
├── my_server.cpp           # Private Backend Server (C++17)
├── vanguard_gui.py         # Desktop Control Center (Muted Purple Cyberpunk Theme, PyQt6)
├── vanguard_agent.py       # Autonomous AI Agent powered by Gemini 3.5 Flash
├── dashboard.py            # TUI Dashboard (Rich)
├── vanguard_stress.py      # Stress testing tool (aiohttp)
├── Makefile                # Build system configuration (make / make clean)
├── include/                # C++ Header files
├── whitelist.conf          # IP Whitelist configuration for Rate Limiter
├── test.sh                 # Integration test suite
├── simulate_attack.sh      # Attack simulation script
├── Dockerfile              # Multi-stage Dockerfile
├── docker-compose.yml      # Docker Compose configuration
├── entrypoint.sh           # Docker Entrypoint script
├── requirements.txt        # Python Dependencies
├── tests/                  # C++ Unit Tests
└── LICENSE                 # Project License (Proprietary / All Rights Reserved)
```

Made by Sattaya Thongdaeng 

---

## License

This project is proprietary and copyrighted by Mr. Sattaya Thongdaeng (All Rights Reserved). Use, distribution, or reproduction is strictly prohibited. It was developed as a portfolio project for further studies at Kasetsart University, Faculty of Science, Department of Computer Science. See [LICENSE](file:///c:/Users/Sattaya%20Thongdaeng/Documents/comsciku/LICENSE) for more details.