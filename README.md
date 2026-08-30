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

**Vanguard v2 คือ Web Application Firewall (WAF) และ Reverse Proxy ประสิทธิภาพสูง ที่ถูกพัฒนาขึ้นด้วยภาษา C++17 ด้วยมือทั้งหมดโดยไม่ใช้เฟรมเวิร์กใด ๆ ทำงานอยู่บน Linux `epoll(7)` โดยตรงเพื่อประสิทธิภาพและความปลอดภัยสูงสุด** พร้อมยกระดับสถาปัตยกรรมสู่การเป็น **Autonomous AI SOC Agent** เต็มรูปแบบ ขับเคลื่อนด้วยขุมพลัง **Google Gemini 3.5 Flash** ที่สามารถวิเคราะห์ ตัดสินใจ และบล็อกภัยคุกคามทางไซเบอร์ได้อัตโนมัติแบบเรียลไทม์โดยไม่ต้องใช้มนุษย์ควบคุม (Zero Human Intervention)

<p align="center">
  <img src="https://img.shields.io/badge/HACKATHON-All%20Things%20Agentic-blueviolet?style=flat-square" alt="Hackathon Badge"/>
  <img src="https://img.shields.io/badge/TRACK-Taskmaster-critical?style=flat-square" alt="Track Badge"/>
  <img src="https://img.shields.io/badge/AI-Gemini%203.5%20Flash-blue?style=flat-square&logo=google" alt="Gemini Badge"/>
  <img src="https://img.shields.io/badge/Cloud-Google%20Firestore-orange?style=flat-square&logo=firebase" alt="Firestore Badge"/>
</p>

[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg?style=flat-square&logo=cplusplus)](https://isocpp.org/)
[![License: Proprietary](https://img.shields.io/badge/License-All%20Rights%20Reserved-red.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg?style=flat-square&logo=linux)](https://kernel.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker)](docker-compose.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-yellow.svg?style=flat-square&logo=python)](https://python.org/)

---

## สารบัญ

- [ภาพรวมโปรเจกต์ (Overview & Value Proposition)](#ภาพรวมโปรเจกต์-overview--value-proposition)
- [เริ่มต้นใช้งานอย่างเร็ว (Quick Start)](#เริ่มต้นใช้งานอย่างเร็ว-quick-start)
- [สถาปัตยกรรมระบบ (Architecture)](#สถาปัตยกรรมระบบ-architecture)
- [จุดเด่นทางวิศวกรรม & AI Features](#จุดเด่นทางวิศวกรรม--ai-features)
- [Vanguard Control Center v2 (GUI - Muted Purple Theme)](#vanguard-control-center-gui---muted-purple-theme)
- [TUI Dashboard สำหรับ Terminal](#tui-dashboard-สำหรับ-terminal)
- [การใช้งานสคริปต์จำลองการโจมตีและการทดสอบระบบ (Simulate & Test)](#การใช้งานสคริปต์จำลองการโจมตีและการทดสอบระบบ-simulate--test)
- [เครื่องมือ CLI และ Stress Testing](#เครื่องมือ-cli-และ-stress-testing)
- [การ Deploy ด้วย Docker](#การ-deploy-ด้วย-docker)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [สัญญาอนุญาต](#สัญญาอนุญาต)

---

## ภาพรวมโปรเจกต์ (Overview & Value Proposition)

ปัญหาของศูนย์ปฏิบัติการรักษาความปลอดภัย (SOC) แบบดั้งเดิมคือ ผู้ดูแลระบบต้องใช้เวลาอ่าน Log นับพันบรรทัดเพื่อค้นหาผู้โจมตี ทำให้การตอบสนองต่อภัยคุกคามล่าช้าและเกิดความเสียหาย

**Vanguard v2** แก้ปัญหานี้ด้วยการเป็นชุดเครื่องมือรักษาความปลอดภัยเครือข่ายแบบ Full-Stack ประกอบด้วย Edge Proxy ภาษา C++ ที่มี WAF Engine ในตัว ทำงานร่วมกับเว็บเซิร์ฟเวอร์ Backend และเครื่องมือ Python โดยเพิ่มระบบ **Autonomous AI SOC Agent** เข้าไป ทุก HTTP Request จะผ่าน Vanguard v2 Edge Proxy ซึ่งจะตรวจสอบการโจมตี SQL Injection และ Cross-Site Scripting, บังคับใช้ Rate Limiting แบบ Per-IP ด้วยอัลกอริทึม Token Bucket หากพบความผิดปกติ AI จะดึงบริบทของเหตุการณ์ (Context) ส่งให้ Gemini วิเคราะห์ และทำการเขียนไฟล์กฎไฟร์วอลล์ สั่งรีสตาร์ท Proxy และบันทึกประวัติขึ้น Google Cloud Firestore ให้ทันทีโดยอัตโนมัติ

| คอมโพเนนต์ | ภาษา | คำอธิบาย |
|---|---|---|
| `vanguard_proxy` | C++17 | Edge Proxy พร้อม WAF, Rate Limiter และ Reverse Proxy (epoll) |
| `my_server` | C++17 | Backend Server แบบ Private พร้อม JSON `/stats` API |
| `vanguard_gui.py` | Python/PyQt6 | Desktop Control Center (Muted Purple Hacker Dashboard, Process Discovery & Termination) |
| `vanguard_agent.py`| Python/GenAI | Autonomous AI Agent ประมวลผลด้วย Gemini 3.5 Flash และบันทึก Log ลง Firestore |
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

🔑 ตั้งค่า API Keys สำหรับ AI & Cloud
เพื่อให้ระบบ Autonomous SOC ทำงานได้สมบูรณ์ จำเป็นต้องตั้งค่า API: 
```bash
export GEMINI_API_KEY="ใส่_GEMINI_API_KEY_ของคุณที่นี่"
# (ตัวเลือกเสริม) สำหรับบันทึกข้อมูล Threat Intelligence ขึ้น Cloud
export GOOGLE_APPLICATION_CREDENTIALS="gcp-key.json"
```

เมื่อ setup เสร็จแล้ว สามารถเปิด GUI ได้ทันที:
```bash
# เปิด GUI Control Center (Muted Purple Cyberpunk Theme)
python3 vanguard_gui.py
```

## สถาปัตยกรรมระบบ (Architecture)
```plaintext  
══════════════════════════════════════════════════════════════
                    ┌──────────────────────────────────────┐
                    │        INTERNET / ไคลเอนต์            │
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
                              │                │ (Traffic ปลอดภัย)
                   (Log ถูกดึง) │                ▼
┌──────────────────────┐      │        ┌───────────────────┐
│ PyQt6 Control Center │◄─────┘        │  Backend Server   │
│ ┌──────────────────┐ │               │  127.0.0.1:3000   │
│ │ VanguardAIAgent  │ │               └───────────────────┘
│ │ (Gemini 3.5)     │ │───┐
│ └──────────────────┘ │   │ (Auto-Ban)
└──────────┬───────────┘   ▼
           │           blacklist.conf / whitelist.conf
           │           (AI สั่งรีสตาร์ท Proxy อัตโนมัติ)
           ▼
┌──────────────────────┐
│ Google Firestore     │ (บันทึกประวัติภัยคุกคาม)
└──────────────────────┘
## จุดเด่นทางวิศวกรรม & AI Features
### 🔧 ขุมพลัง C++17 Edge Proxy
epoll(7) Non-Blocking I/O: Proxy ใช้ epoll ของ Linux Kernel สำหรับ Event Notification แบบ O(1) บน Listening Socket โดยรับ Connection ใหม่ในลูปแบบ Non-blocking (O_NONBLOCK + EPOLLIN) แล้วส่งต่อไปยัง Handler Thread

Zero-Copy HTTP Parsing ด้วย std::string_view: HTTP Parser ที่เขียนขึ้นเองทำงานบน std::string_view ที่อ้างอิงกลับไปยัง Receive Buffer เดิม — แยก Method, URI, Headers และ Body โดยไม่มีการ Allocate หน่วยความจำหรือ Copy String

Token Bucket Rate Limiter แบบ Thread-Safe: ทุก Client IP จะได้รับ Token Bucket อิสระ (ค่าเริ่มต้น: 10 tokens/วินาที, ความจุ burst: 10) ป้องกันด้วย std::mutex เพื่อความปลอดภัยระหว่าง Thread

WAF Inspection Engine: ตรวจจับ SQL Injection 22 pattern (UNION SELECT, OR 1=1, DROP TABLE, SLEEP(), BENCHMARK()) และ Cross-Site Scripting 18 pattern (<script>, javascript:, onerror=, eval(), document.cookie)

### 🧠 ระบบ Autonomous AI SOC Agent
Context-Aware Analysis: AI ไม่ได้อ่าน Log แค่บรรทัดเดียว แต่จะดึง Log 15 บรรทัดล่าสุด ส่งให้ Gemini 3.5 Flash เพื่อวิเคราะห์บริบท (Context) ช่วยแยกแยะระหว่างทราฟฟิกปกติกับการโจมตีจริง ลดอัตรา False Positives ได้อย่างแม่นยำ

Autonomous Auto-Ban Pipeline (Take Action): เมื่อพบภัยคุกคาม ระบบจะตอบกลับเป็น JSON และใช้ psutil ทำการเพิ่ม IP ลงใน Blacklist พร้อมสั่ง Hot-reload รีสตาร์ท C++ Proxy ทันทีเพื่อบล็อกแฮกเกอร์แบบอัตโนมัติ โดยไม่ทำให้ GUI ค้าง (รันบน QThread)

Google Cloud Telemetry: ข้อมูลภัยคุกคามทั้งหมด (Threat Intelligence) รวมถึงเหตุผลที่ AI ตัดสินใจบล็อก จะถูกบันทึกขึ้น blocked_threats collection บน Google Cloud Firestore เพื่อใช้ในการตรวจสอบ (Audit Trail)

## Vanguard Control Center v2 (GUI - Muted Purple Theme)
### 🎨 สไตล์ UI/UX: Muted Purple Hacker Dashboard
Muted Dark Purple Palette: สีหลักเน้นม่วงเข้มโทนสุขุม (#6a0dad, #5e35b1, #7b1fa2, #a855f7) ผสานพื้นหลังสีดำสนิท (#050508 / #0a0a0f)

Monospace Typography: ใช้ฟอนต์ Monospace (Consolas, 'Courier New', Monospace) ทั้งแอปพลิเคชัน พร้อม Header ตัวพิมพ์ใหญ่ (UPPERCASE)

Panel Enclosures: แยกแต่ละส่วน (Stats, Chart, Controls, Terminal) ด้วยกรอบ QFrame เส้นขอบม่วงบาง (1px solid #6a0dad) และ padding พอเหมาะ

⚡ ฟีเจอร์เด่นใน GUI
1. 🔥 AI Agent Thought Process Terminal (New)
กล่องข้อความจำลอง Terminal แบบเรียลไทม์ที่ด้านล่างของหน้าจอ ให้ผู้ดูแลระบบสามารถสังเกตกระบวนการคิด การดึงข้อมูล และการลงมือปฏิบัติ (Take Action) ของ AI Agent ได้อย่างโปร่งใส

2. 🔄 Start/Stop Toggle & OS-Level Process Termination
ปุ่มควบคุม Backend และ Proxy สลับสถานะได้แบบ Dynamic (เขียว/ฟ้าสำหรับ Start, แดงสำหรับ Stop) ระบบสามารถตรวจจับ Process ภายนอกและสั่งยุติการทำงานที่ระดับ OS ด้วย psutil.Process(pid).terminate() และ fallback os.kill(pid, signal.SIGTERM) อย่างปลอดภัย

3. 🔗 Terminal Sync (Process Discovery)
สแกนหา Process my_server และ vanguard_proxy ทุก 2 วินาทีผ่าน psutil.process_iter() ปรับสถานะปุ่มใน GUI ให้ตรงกับสภาวะจริงในระบบปฏิบัติการอัตโนมัติ

4. ⚡ Stress Test Modal Dialog
ปุ่ม ⚡ LAUNCH STRESS TEST เปิด Dialog ป๊อปอัปเลือก Preset การโจมตีเพื่อทดสอบความแม่นยำของ WAF และ AI:
| โปรไฟล์                | โหมด  | Concurrency | Requests | คำอธิบาย |
|---|---|---|---|---|
| 🟢 LIGHT LOAD        | normal     | 10 |      200     | Traffic ปกติพร้อม delay 10ms |
| 🟡 NORMAL LOAD       | normal     | 50 |      1,000   | ทดสอบ Load ระดับมาตรฐาน |
| 🔴 HEAVY LOAD        | bruteforce | 100|      5,000   | ยิงถล่มเพื่อทดสอบ Token Bucket Rate Limiter |
| 🛡️ WAF TEST (SQLI)   | sqli       | 20 |      200     | ส่ง SQL Injection payloads ทดสอบ WAF Block (HTTP 403) |
| ⚡ MAX STRESS        | bruteforce | 200|      10,000  | ทดสอบ Load ความรุนแรงสูงสุด |
## TUI Dashboard สำหรับ Terminal
สำหรับสภาพแวดล้อม Terminal ไร้ GUI:
```bash
python3 dashboard.py
```
## การใช้งานสคริปต์จำลองการโจมตีและการทดสอบระบบ (Simulate & Test)

นอกจากเครื่องมือ Stress Testing แล้ว ระบบยังมีสคริปต์สำหรับการจำลองการโจมตี (Attack Simulation) และการรัน Automated Tests เพื่อตรวจสอบการทำงานของ WAF และ Proxy:

### 1. การจำลองการโจมตี (`simulate_attack.sh`)
สคริปต์นี้ใช้สำหรับจำลองพฤติกรรมของแฮกเกอร์และผู้ใช้ทั่วไป เพื่อทดสอบว่า WAF และ Rate Limiter ทำงานบล็อกการโจมตีได้ถูกต้องหรือไม่:
```bash
# ⚠️ ข้อควรระวัง: ต้องเปิด vanguard_proxy และ my_server ให้ทำงานอยู่ก่อนรัน
bash simulate_attack.sh
```
สคริปต์จะทำการทดสอบ 4 สถานการณ์:
- **Scenario 1:** Normal User (Traffic ปกติ, ควรได้ HTTP 200)
- **Scenario 2:** Brute Force / Rate Limit (ยิงรัว 15 requests, ควรได้ HTTP 429)
- **Scenario 3:** WAF Test - SQL Injection (ยิง Payload SQLi, ควรได้ HTTP 403)
- **Scenario 4:** WAF Test - XSS (ยิง Payload XSS, ควรได้ HTTP 403)

### 2. ชุดทดสอบระบบอัตโนมัติ (`test.sh`)
สคริปต์สำหรับตรวจสอบ Integration Test ระหว่าง Proxy และ Backend:
```bash
bash test.sh
```
จะทำการทดสอบระบบตั้งแต่ การส่งต่อข้อมูล (Forwarding), การแก้ไข Header (Server, Content-Length), การดึงข้อมูล JSON จาก `/stats`, ไปจนถึงประสิทธิภาพการป้องกัน WAF และ Rate Limit รวม 9 การทดสอบ

### 3. การตั้งค่า Whitelist / Blacklist
ระบบรองรับการตั้งค่าผ่านไฟล์ Configuration:
- `whitelist.conf`: กำหนด IP ที่จะไม่ถูกจำกัดความเร็ว (Bypass Rate Limiting) เช่น IP ของผู้ดูแลระบบ (แต่ยังคงถูกตรวจสอบ WAF อยู่)
- `blacklist.conf`: ไฟล์ที่ Autonomous AI Agent จะใช้ในการเขียน IP ของผู้โจมตีลงไปเพื่อบล็อกการเชื่อมต่อโดยอัตโนมัติ (Auto-Ban)

## เครื่องมือ CLI และ Stress Testing
```bash
# ทดสอบ Normal Traffic
python3 vanguard_stress.py -m normal

# ทดสอบ Bruteforce (Rate Limiter)
python3 vanguard_stress.py -m bruteforce -c 100 -n 5000

# ทดสอบ WAF Rules
python3 vanguard_stress.py -m sqli -c 20 -n 200
การ Deploy ด้วย Docker
```bash
# Build และรันผ่าน Docker Compose
sudo docker compose up -d

# ดู Log
sudo docker compose logs -f

# หยุดทำงาน
sudo docker compose down
โครงสร้างโปรเจกต์
```plaintext
PROJECTVANGUARD/
├── setup.sh                # ⚡ สคริปต์ One-Click Setup (APT + Build + PyDeps + Cleanup)
├── vanguard_proxy.cpp      # Edge Proxy + WAF Engine (C++17, epoll)
├── my_server.cpp           # Backend Server แบบ Private (C++17)
├── vanguard_gui.py         # Desktop Control Center (Muted Purple Cyberpunk Theme, PyQt6)
├── vanguard_agent.py       # Autonomous AI Agent ขับเคลื่อนด้วย Gemini 3.5 Flash
├── dashboard.py            # TUI Dashboard (Rich)
├── vanguard_stress.py      # เครื่องมือทดสอบ Stress (aiohttp)
├── Makefile                # ระบบ Build (make / make clean)
├── include/                # Header files สำหรับ C++
├── whitelist.conf          # Whitelist IP สำหรับ Rate Limiter
├── test.sh                 # ชุดทดสอบ Integration
├── simulate_attack.sh      # สคริปต์จำลองการโจมตี
├── Dockerfile              # Build Container แบบ Multi-stage
├── docker-compose.yml      # จัดการ Container
├── entrypoint.sh           # สคริปต์ Entrypoint ของ Docker
├── requirements.txt        # Python Dependencies
├── tests/                  # C++ Unit Tests
└── LICENSE                 # สัญญาอนุญาต MIT
```
Made by Sattaya Thongdaeng 

## สัญญาอนุญาต

  สัญญาอนุญาตโปรเจกต์นี้เป็นลิขสิทธิ์เฉพาะของ นายสัตยา ทองแดง (All Rights Reserved) 
  ไม่อนุญาตให้นำไปใช้งานหรือเผยแพร่ทุกกรณี จัดทำขึ้นเพื่อใช้เป็นผลงานสำหรับศึกษาต่อ ณ 
  มหาวิทยาลัยเกษตรศาสตร์ คณะวิทยาศาสตร์ สาขาวิทยาการคอมพิวเตอร์ 
  ดูรายละเอียดที่ LICENSE