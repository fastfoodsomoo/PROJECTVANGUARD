```
 ╔═══════════════════════════════════════════════════════════════════════════════════════════╗
 ║                                                                                           ║
 ║        ██╗   ██╗ ██████╗  ███╗   ██╗  ██████╗   ██╗   ██╗ ██████╗  ██████╗  ██████╗       ║
 ║        ██║   ██║ ██╔══██╗ ████╗  ██║  ██╔════╝  ██║   ██║ ██╔══██╗ ██╔══██╗ ██╔══██╗      ║
 ║        ██║   ██║ ███████║ ██╔██╗ ██║  ██║  ███╗ ██║   ██║ ███████║ ██████╔╝ ██║  ██║      ║
 ║        ╚██╗ ██╔╝ ██╔══██║ ██║╚██╗██║  ██║   ██║ ██║   ██║ ██╔══██║ ██╔══██╗ ██╔══██║      ║
 ║         ╚████╔╝  ██║  ██║ ██║ ╚████║  ╚██████╔╝  ╚██████╔╝██║  ██║ ██║  ██║ ██████╔╝      ║
 ║          ╚═══╝   ╚═╝  ╚═╝ ╚═╝  ╚═══╝   ╚═════╝    ╚═════╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═════╝       ║
 ║                                                                                           ║
 ║                                  EDGE PROXY & WAF ENGINE                                  ║
 ║                           Cloudflare-like Reverse Proxy in C++17                          ║
 ║                                                                                           ║
 ╚═══════════════════════════════════════════════════════════════════════════════════════════╝
```

**Vanguard คือ Web Application Firewall (WAF) และ Reverse Proxy ประสิทธิภาพสูง ที่ถูกพัฒนาขึ้นด้วยภาษา C++17 ด้วยมือทั้งหมดโดยไม่ใช้เฟรมเวิร์กใด ๆ ทำงานอยู่บน Linux `epoll(7)` โดยตรงเพื่อประสิทธิภาพและความปลอดภัยสูงสุด**

[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg?style=flat-square&logo=cplusplus)](https://isocpp.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg?style=flat-square&logo=linux)](https://kernel.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker)](docker-compose.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-yellow.svg?style=flat-square&logo=python)](https://python.org/)

---

## สารบัญ

- [ภาพรวมโปรเจกต์](#ภาพรวมโปรเจกต์)
- [เริ่มต้นใช้งานอย่างเร็ว (Quick Start)](#เริ่มต้นใช้งานอย่างเร็ว-quick-start)
- [สถาปัตยกรรมระบบ](#สถาปัตยกรรมระบบ)
- [จุดเด่นทางวิศวกรรม](#จุดเด่นทางวิศวกรรม)
- [Vanguard Control Center (GUI - Muted Purple Theme)](#vanguard-control-center-gui---muted-purple-theme)
- [TUI Dashboard สำหรับ Terminal](#tui-dashboard-สำหรับ-terminal)
- [เครื่องมือ CLI และ Stress Testing](#เครื่องมือ-cli-และ-stress-testing)
- [การ Deploy ด้วย Docker](#การ-deploy-ด้วย-docker)
- [การตั้งค่า](#การตั้งค่า)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [สัญญาอนุญาต](#สัญญาอนุญาต)

---

## ภาพรวมโปรเจกต์

**Vanguard** เป็นชุดเครื่องมือรักษาความปลอดภัยเครือข่ายแบบ Full-Stack ประกอบด้วย Edge Proxy ภาษา C++ ที่มี WAF Engine ในตัว ทำงานร่วมกับเว็บเซิร์ฟเวอร์ Backend และเครื่องมือ Python สำหรับทดสอบและตรวจสอบสถานะของระบบ

ทุก HTTP Request จะผ่าน Vanguard Edge Proxy ซึ่งจะตรวจสอบการโจมตี SQL Injection และ Cross-Site Scripting, บังคับใช้ Rate Limiting แบบ Per-IP ด้วยอัลกอริทึม Token Bucket จากนั้นจึงส่งต่อ Traffic ที่ปลอดภัยไปยัง Backend Server — ทั้งหมดนี้ทำงานที่ความเร็วระดับ Wire Speed โดยใช้ `epoll(7)` I/O Multiplexing ของ Linux

| คอมโพเนนต์ | ภาษา | คำอธิบาย |
|---|---|---|
| `vanguard_proxy` | C++17 | Edge Proxy พร้อม WAF, Rate Limiter และ Reverse Proxy (epoll) |
| `my_server` | C++17 | Backend Server แบบ Private พร้อม JSON `/stats` API |
| `vanguard_gui.py` | Python/PyQt6 | Desktop Control Center (Muted Purple Hacker Dashboard, Process Discovery & Termination) |
| `dashboard.py` | Python/Rich | TUI Dashboard สำหรับสภาพแวดล้อมแบบ Terminal |
| `vanguard_stress.py` | Python/aiohttp | เครื่องมือทดสอบ Load แบบ Asynchronous |
| `setup.sh` | Bash | สคริปต์ตั้งค่าแบบ One-Click (ติดตั้ง APT dependencies, compile `make`, `chmod`, `pip install`) |

---

## เริ่มต้นใช้งานอย่างเร็ว (Quick Start)

### ⚡ One-Click Setup (`setup.sh`)

คำสั่งเดียวสำหรับตั้งค่าระบบทั้งหมด:

```bash
bash setup.sh
```

สคริปต์ `setup.sh` ทำงาน 6 ขั้นตอนโดยอัตโนมัติ:
1. 📦 **APT Package Installation**: รัน `sudo apt update && sudo apt install -y build-essential python3-pip python3-venv python3-dev` เพื่อติดตั้งระบบและคอมไพเลอร์ที่จำเป็น
2. 🔍 **System Dependency Verification**: ตรวจสอบการมีอยู่ของ `g++`, `make`, `python3`, `pip`
3. ⚙️ **C++ Binary Compilation**: คอมไพล์ `vanguard_proxy` และ `my_server` ด้วย `make` (`-O3 -std=c++17`)
4. 🔑 **Permissions Configuration**: กำหนดสิทธิ์ให้รันได้ด้วย `chmod +x` บน binaries และ scripts ทั้งหมด
5. 🐍 **Python Environment & Dependencies**: สร้าง Python Virtual Environment (`./venv`) หรือใช้ `--break-system-packages` เพื่อติดตั้ง `PyQt6`, `pyqtgraph`, `psutil`, `rich`, `aiohttp`, `requests`
6. 🧹 **Workspace Artifact Cleanup**: กำจัดไฟล์ขยะ `Zone.Identifier` และไฟล์ legacy v1

เมื่อ setup เสร็จแล้ว สามารถเปิด GUI ได้ทันที:

```bash
# เปิด GUI Control Center (Muted Purple Cyberpunk Theme)
python3 vanguard_gui.py

# หรือเริ่ม Manual (แยก Terminal)
./my_server          # Terminal 1 (Backend Server)
./vanguard_proxy     # Terminal 2 (Edge WAF Proxy)
```

---

## สถาปัตยกรรมระบบ

```
                        Vanguard — Request Flow
  ══════════════════════════════════════════════════════════════

                    ┌──────────────────────────────────────┐
                    │        INTERNET / ไคลเอนต์            │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │       VANGUARD EDGE PROXY            │
                    │       0.0.0.0:8080                   │
                    │                                      │
                    │  ┌────────────┐  ┌────────────────┐  │
                    │  │  WAF Engine│  │  Rate Limiter  │  │
                    │  │  SQLi + XSS│  │  Token Bucket  │  │
                    │  └──────┬─────┘  └───────┬────────┘  │
                    │         │                │           │
                    │         ▼                ▼           │
                    │  ┌─────────────────────────────────┐ │
                    │  │  403 บล็อก   │  429 จำกัดอัตรา      │ │
                    │  └─────────────────────────────────┘ │
                    │         │ (Traffic ที่ปลอดภัย)          │
                    │         ▼                            │
                    │  ┌─────────────────────────────────┐ │
                    │  │  Reverse Proxy + Header Inject  │ │
                    │  │  X-Vanguard-Connecting-IP       │ │
                    │  │  X-Vanguard-Ray-ID              │ │
                    │  └──────────────┬──────────────────┘ │
                    └─────────────────┼────────────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────────┐
                    │       BACKEND WEB SERVER             │
                    │       127.0.0.1:3000 (loopback)      │
                    │                                      │
                    │  เส้นทาง: / | /VANGUARD | /stats       │
                    │  Engine: C++17 / POSIX sockets       │
                    └──────────────────────────────────────┘
```

---

## จุดเด่นทางวิศวกรรม

### ⚡ epoll(7) Non-Blocking I/O

Proxy ใช้ `epoll` ของ Linux Kernel สำหรับ Event Notification แบบ O(1) บน Listening Socket โดยรับ Connection ใหม่ในลูปแบบ Non-blocking (`O_NONBLOCK` + `EPOLLIN`) แล้วส่งต่อไปยัง Handler Thread

### 🔍 Zero-Copy HTTP Parsing ด้วย `std::string_view`

HTTP Parser ที่เขียนขึ้นเองทำงานบน `std::string_view` ที่อ้างอิงกลับไปยัง Receive Buffer เดิม — แยก Method, URI, Headers และ Body โดยไม่มีการ Allocate หน่วยความจำหรือ Copy String

### 🪣 Token Bucket Rate Limiter แบบ Thread-Safe

ทุก Client IP จะได้รับ Token Bucket อิสระ (ค่าเริ่มต้น: 10 tokens/วินาที, ความจุ burst: 10) ป้องกันด้วย `std::mutex` เพื่อความปลอดภัยระหว่าง Thread

### 🛡️ WAF Inspection Engine

- **SQL Injection**: 22 pattern (`UNION SELECT`, `OR 1=1`, `DROP TABLE`, `SLEEP()`, `BENCHMARK()`)
- **Cross-Site Scripting**: 18 pattern (`<script>`, `javascript:`, `onerror=`, `eval()`, `document.cookie`)

---

## Vanguard Control Center (GUI - Muted Purple Theme)

```
╔═══════════════════════════════════════════════════════════════════╗
║     ⟨ VANGUARD V2 // EDGE PROXY & WAF DASHBOARD ⟩                 ║
╠═══════════════════════════════════════════════════════════════════╣
║ ┌─ [ SYSTEM METRICS ] ──────────────────────────────────────────┐ ║
║ │ STATUS: ONLINE │ UPTIME: 1h 24m │ REQS: 42,910 │ RPS: 154.2   │ ║
║ └───────────────────────────────────────────────────────────────┘ ║
║                                                                   ║
║ ┌─ [ LIVE RPS MONITOR // 60S HISTORY ] ─────────────────────────┐ ║
║ │ 200 ┤                     ╭──╮                                │ ║
║ │ 100 ┤              ╭─────╯  ╰──╮      ╭──╮                    │ ║
║ │   0 ┤──╯                                                      │ ║
║ └───────────────────────────────────────────────────────────────┘ ║
║                                                                   ║
║ ┌─ [ PROCESS CONTROLS & LOG STREAM ] ───────────────────────────┐ ║
║ │ [ ■ STOP BACKEND ]   [ ▶ START PROXY ]   [ ⚡ LAUNCH STRESS ] │ ║
║ │                                                               │ ║
║ │ [SYS] VANGUARD CONTROL CENTER V2 INITIALIZED.                 │ ║
║ │ [SYS] External process detected via Terminal Sync (PID 14201) │ ║
║ └───────────────────────────────────────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════════╝
```

### 🎨 สไตล์ UI/UX: Muted Purple Hacker Dashboard

- **Muted Dark Purple Palette**: สีหลักเน้นม่วงเข้มโทนสุขุม (`#6a0dad`, `#5e35b1`, `#7b1fa2`, `#a855f7`) ผสานพื้นหลังสีดำสนิท (`#050508` / `#0a0a0f`)
- **Monospace Typography**: ใช้ฟอนต์ Monospace (`Consolas`, `'Courier New'`, `Monospace`) ทั้งแอปพลิเคชัน พร้อม Header ตัวพิมพ์ใหญ่ (`UPPERCASE`)
- **Panel Enclosures**: แยกแต่ละส่วน (Stats, Chart, Controls, Terminal) ด้วยกรอบ `QFrame` เส้นขอบม่วงบาง (`1px solid #6a0dad`) และ padding พอเหมาะ
- **Non-blocking Architecture**: ใช้ `QThread` ดึงสถิติ, `QProcess` รันและควบคุม Process, และ `QTimer` สแกน Process อัตโนมัติ

### ⚡ ฟีเจอร์เด่นใน GUI

#### 1. 🔄 Start/Stop Toggle & OS-Level Process Termination
- ปุ่มควบคุม Backend และ Proxy สลับสถานะได้แบบ Dynamic (เขียว/ฟ้าสำหรับ Start, แดงสำหรับ Stop)
- **External Process Killing (`psutil`)**: เมื่อคลิก "Stop" GUI จะตรวจสอบว่า Process ทำงานอยู่ภายนอกหรือไม่ (เช่น เริ่มจาก VS Code Terminal) และสั่งยุติการทำงานที่ระดับ OS ด้วย `psutil.Process(pid).terminate()` และ fallback `os.kill(pid, signal.SIGTERM)` อย่างปลอดภัย

#### 2. 🔗 Terminal Sync (Process Discovery)
- สแกนหา Process `my_server` และ `vanguard_proxy` ทุก 2 วินาทีผ่าน `psutil.process_iter()`
- ปรับสถานะปุ่มใน GUI ให้ตรงกับสภาวะจริงในระบบปฏิบัติการอัตโนมัติ

#### 3. ⚡ Stress Test Modal Dialog
- ปุ่ม `⚡ LAUNCH STRESS TEST` เปิด Dialog ป๊อปอัปเลือก Preset 5 รูปแบบ:

| โปรไฟล์ | โหมด | Concurrency | Requests | คำอธิบาย |
|---|---|---|---|---|
| 🟢 LIGHT LOAD | `normal` | 10 | 200 | Traffic ปกติพร้อม delay 10ms |
| 🟡 NORMAL LOAD | `normal` | 50 | 1,000 | ทดสอบ Load ระดับมาตรฐาน |
| 🔴 HEAVY LOAD | `bruteforce` | 100 | 5,000 | ยิงถล่มเพื่อทดสอบ Token Bucket Rate Limiter |
| 🛡️ WAF TEST (SQLI) | `sqli` | 20 | 200 | ส่ง SQL Injection payloads ทดสอบ WAF Block (HTTP 403) |
| ⚡ MAX STRESS | `bruteforce` | 200 | 10,000 | ทดสอบ Load ความรุนแรงสูงสุด |

---

## TUI Dashboard สำหรับ Terminal

สำหรับสภาพแวดล้อม Terminal ไร้ GUI:

```bash
python3 dashboard.py
```

---

## เครื่องมือ CLI และ Stress Testing

```bash
# ทดสอบ Normal Traffic
python3 vanguard_stress.py -m normal

# ทดสอบ Bruteforce (Rate Limiter)
python3 vanguard_stress.py -m bruteforce -c 100 -n 5000

# ทดสอบ WAF Rules
python3 vanguard_stress.py -m sqli -c 20 -n 200
```

---

## การ Deploy ด้วย Docker

```bash
# Build และรันผ่าน Docker Compose
sudo docker compose up -d

# ดู Log
sudo docker compose logs -f

# หยุดทำงาน
sudo docker compose down
```

---

## โครงสร้างโปรเจกต์

```
PROJECTVANGUARD/
├── setup.sh                # ⚡ สคริปต์ One-Click Setup (APT + Build + PyDeps + Cleanup)
├── vanguard_proxy.cpp      # Edge Proxy + WAF Engine (C++17, epoll)
├── my_server.cpp           # Backend Server แบบ Private (C++17)
├── vanguard_gui.py         # Desktop Control Center (Muted Purple Cyberpunk Theme, PyQt6)
├── dashboard.py            # TUI Dashboard (Rich)
├── vanguard_stress.py      # เครื่องมือทดสอบ Stress (aiohttp)
├── Makefile                # ระบบ Build (make / make clean)
├── include/
│   ├── colors.h            # ค่าคงที่สี ANSI
│   ├── config.h            # Config parser (สำหรับ Unit Tests)
│   ├── ip_utils.h          # IP utility functions
│   └── logger.h            # Thread-safe logger
├── whitelist.conf          # Whitelist IP สำหรับ Rate Limiter
├── test.sh                 # ชุดทดสอบ Integration
├── simulate_attack.sh      # สคริปต์จำลองการโจมตี
├── Dockerfile              # Build Container แบบ Multi-stage
├── docker-compose.yml      # จัดการ Container
├── entrypoint.sh           # สคริปต์ Entrypoint ของ Docker
├── requirements.txt        # Python Dependencies (PyQt6, pyqtgraph, psutil, rich, aiohttp)
├── tests/
│   ├── test_ip.cpp         # Unit Test สำหรับ IP utilities
│   ├── test_config.cpp     # Unit Test สำหรับ Config parser
│   └── test_rate.cpp       # Unit Test สำหรับ Rate Limiter
└── LICENSE                 # สัญญาอนุญาต MIT
```

---

  ╔══════════════════════════════════════════════╗
  ║  Made by Sattaya Thongdaeng                  ║
  ╚══════════════════════════════════════════════╝

---
## สัญญาอนุญาต

โปรเจกต์นี้อยู่ภายใต้สัญญาอนุญาต MIT ดูรายละเอียดที่ [LICENSE](LICENSE)