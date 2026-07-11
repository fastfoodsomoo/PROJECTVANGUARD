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

**Vanguard คือ Web Application Firewall (WAF) และ Reverse Proxy ประсิทธิภาพสูง ที่ถูกพัฒนาขึ้นด้วยภาษา C++17 ด้วยมือทั้งหมดโดยไม่ใช้เฟรมเวิร์กใด ๆ ทำงานอยู่บน Linux `epoll(7)` โดยตรงเพื่อประสิทธิภาพและความปลอดภัยสูงสุด**

[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg?style=flat-square&logo=cplusplus)](https://isocpp.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg?style=flat-square&logo=linux)](https://kernel.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker)](docker-compose.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-yellow.svg?style=flat-square&logo=python)](https://python.org/)

---

## สารบัญ

- [ภาพรวมโปรเจกต์](#ภาพรวมโปรเจกต์)
- [สถาปัตยกรรมระบบ](#สถาปัตยกรรมระบบ)
- [จุดเด่นทางวิศวกรรม](#จุดเด่นทางวิศวกรรม)
- [ความต้องการระบบและการติดตั้ง](#ความต้องการระบบและการติดตั้ง)
- [เริ่มต้นใช้งานอย่างเร็ว](#เริ่มต้นใช้งานอย่างเร็ว)
- [Vanguard Control Center (GUI)](#vanguard-control-center-gui)
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

ระบบนิเวศประกอบด้วย:

| คอมโพเนนต์ | ภาษา | คำอธิบาย |
|---|---|---|
| `vanguard_proxy` | C++17 | Edge Proxy พร้อม WAF, Rate Limiter และ Reverse Proxy |
| `my_server` | C++17 | Backend Server แบบ Private พร้อม JSON `/stats` API |
| `vanguard_gui.py` | Python/PyQt6 | Desktop Control Center พร้อม Dashboard แบบ Real-time และ Terminal |
| `dashboard.py` | Python/Rich | TUI Dashboard สำหรับสภาพแวดล้อมแบบ Terminal |
| `vanguard_stress.py` | Python/aiohttp | เครื่องมือทดสอบ Load แบบ Asynchronous |
| `docker-compose.yml` | YAML | Deploy ด้วยคำสั่งเดียวผ่าน Container |

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

  ════════════════════════════════════════════════════════════
                    ┌──────────────────────────────────────┐
                    │       ชั้น OBSERVABILITY               │
                    │                                      │
                    │  ┌──────────┐ ┌──────────┐ ┌──────┐  │
                    │  │ GUI App  │ │ TUI Dash │ │ Load │  │
                    │  │ (PyQt6)  │ │ (Rich)   │ │ Test │  │
                    │  └──────────┘ └──────────┘ └──────┘  │
                    │     ดึงข้อมูล /stats ทุก 1 วินาที          │
                    └──────────────────────────────────────┘
```

---

## จุดเด่นทางวิศวกรรม

### ⚡ epoll(7) Non-Blocking I/O

Proxy ใช้ `epoll` ของ Linux Kernel สำหรับ Event Notification แบบ O(1) บน Listening Socket โดยรับ Connection ใหม่ในลูปแบบ Non-blocking (`O_NONBLOCK` + `EPOLLIN`) แล้วส่งต่อไปยัง Handler Thread ทำให้สามารถรองรับ Connection พร้อมกันหลายพันตัวได้อย่างมีประสิทธิภาพ โดยไม่เกิดปัญหา Thundering Herd

### 🔍 Zero-Copy HTTP Parsing ด้วย `std::string_view`

HTTP Parser ที่เขียนขึ้นเองทำงานบน `std::string_view` ที่อ้างอิงกลับไปยัง Receive Buffer เดิม — แยก Method, URI, Headers และ Body โดยไม่มีการ Allocate หน่วยความจำหรือ Copy String เลย ทำให้ได้ Throughput ในการ Parse สูงสุดด้วย Memory Pressure ที่ต่ำที่สุด

### 🪣 Token Bucket Rate Limiter แบบ Thread-Safe

ทุก Client IP จะได้รับ Token Bucket อิสระที่เติมเหรียญในอัตราที่กำหนดได้ (ค่าเริ่มต้น: 10 tokens/วินาที, ความจุ burst: 10) สถานะของ Bucket ถูกป้องกันด้วย `std::mutex` เพื่อความปลอดภัยระหว่าง Thread โดย IP ที่อยู่ใน Whitelist จะข้ามการ Rate Limiting ทั้งหมด

```
อัลกอริทึม Token Bucket:
  tokens = min(BURST, tokens + เวลาที่ผ่านไป × RATE)
  ถ้า tokens >= 1.0 → อนุญาต (ใช้ 1 token)
  มิฉะนั้น           → บล็อก (HTTP 429)
```

### 🛡️ WAF Inspection Engine แบบ O(N)

Web Application Firewall ทำการตรวจสอบ Inline ทั้ง URI และ Request Body เทียบกับฐานข้อมูล Signature สองชุด:

- **SQL Injection**: 22 pattern รวมถึง `UNION SELECT`, `OR 1=1`, `DROP TABLE`, `SLEEP()`, `BENCHMARK()`
- **Cross-Site Scripting**: 18 pattern รวมถึง `<script>`, `javascript:`, `onerror=`, `eval()`, `document.cookie`

การจับคู่ทั้งหมดเป็นแบบ Case-insensitive ผ่าน `std::transform` และ `std::tolower` การสแกน Pattern มีความซับซ้อน O(N × P) โดย N คือความยาวของ Input และ P คือจำนวน Pattern

### 🆔 Ray ID แบบ Cloudflare

ทุก Request จะถูกติดแท็กด้วย Ray ID แบบ Hex 16 ตัวอักษรที่ไม่ซ้ำกัน (สร้างด้วย `std::mt19937_64`) เพื่อให้สามารถติดตาม Request แบบ End-to-End ตั้งแต่ Log ของ Proxy ไปจนถึง Log ของ Backend

### 🔒 Header Injection และ Server Masking

Proxy จะฉีด Header `X-Vanguard-Connecting-IP` และ `X-Vanguard-Ray-ID` เข้าไปใน Request ที่ส่งต่อ และเขียนทับ Header `Server` ของ Backend ด้วย `Vanguard-Edge-Engine/1.0` ใน Response ทั้งหมด

---

## ความต้องการระบบและการติดตั้ง

### ความต้องการระบบ

| ความต้องการ | เวอร์ชัน |
|---|---|
| ระบบปฏิบัติการ | Linux (Ubuntu 20.04+ / Debian 11+) |
| คอมไพเลอร์ C++ | g++ ที่รองรับ C++17 |
| Make | GNU Make |
| Python | 3.10 ขึ้นไป |
| Docker *(ไม่บังคับ)* | 20.10+ พร้อม Compose V2 |

### ขั้นตอนที่ 1 — ติดตั้งแพ็กเกจระบบ

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y build-essential g++ make curl python3 python3-pip

# macOS (Homebrew)
brew install gcc make python3 curl
```

### ขั้นตอนที่ 2 — ติดตั้ง Python Dependencies

```bash
pip install PyQt6 pyqtgraph aiohttp requests rich
```

หรือใช้ไฟล์ requirements ที่เตรียมไว้:

```bash
pip install -r requirements.txt
```

*หมายเหตุ: สำหรับระบบปฏิบัติการ Linux รุ่นใหม่ ๆ (เช่น Ubuntu 23.04+ หรือ Debian 12+) ที่เปิดใช้งานการปกป้องสภาพแวดล้อมระบบภายนอก (PEP 668) คุณอาจต้องติดตั้งผ่านแฟล็ก `--break-system-packages` ดังนี้:*
```bash
pip install --break-system-packages PyQt6 pyqtgraph aiohttp requests rich
```
*หรือแนะนำให้สร้างและใช้งานผ่าน Virtual Environment (`python3 -m venv venv && source venv/bin/activate`)*

### ขั้นตอนที่ 3 — Build ไบนารี C++

```bash
make
```

คำสั่งนี้จะ Compile ทั้ง `vanguard_proxy` และ `my_server` ด้วย:
- `-std=c++17` — มาตรฐาน C++17
- `-O3` — การ Optimize ระดับสูงสุด
- `-pthread` — POSIX threads
- `-Wall -Wextra` — เปิด Warning ทั้งหมด

ผลลัพธ์ที่คาดหวัง:
```
[+] Build complete!
    ./my_server        → Backend on 127.0.0.1:3000
    ./vanguard_proxy   → WAF Proxy on 0.0.0.0:8080
```

---

## เริ่มต้นใช้งานอย่างเร็ว

### ตัวเลือก A — แบบ Manual (สอง Terminal)

```bash
# Terminal 1: เริ่ม Backend Server
./my_server

# Terminal 2: เริ่ม Edge Proxy (อาจต้องใช้ sudo ในบางระบบปฏิบัติการหากต้องการสิทธิ์เข้าถึงเน็ตเวิร์ก)
./vanguard_proxy
```

จากนั้นเปิดเบราว์เซอร์ไปที่ `http://localhost:8080`

### ตัวเลือก B — GUI Control Center

```bash
python3 vanguard_gui.py
```

*หมายเหตุ: บนระบบ Linux บางรุ่นที่ติดตั้ง PyQt6 เป็นครั้งแรก อาจต้องใช้สิทธิ์ผู้ดูแลระบบหรือรันผ่าน Virtual Environment ที่ตั้งค่ากราฟิกให้ถูกต้อง*

### ตัวเลือก C — Docker

การรัน Docker และ Docker Compose บนระบบ Linux ส่วนใหญ่จำเป็นต้องมีสิทธิ์รูท (root) หรือใช้สิทธิ์ `sudo` นำหน้าคำสั่งเสมอดังนี้:

```bash
sudo docker compose up -d
```

Service ทั้งสองจะเริ่มทำงานโดยอัตโนมัติภายใน Container เดียว

---

## Vanguard Control Center (GUI)

```
╔═══════════════════════════════════════════════════════════════════╗
║                  VANGUARD CONTROL CENTER                          ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  ┌─ STATUS ──┐  ┌─ UPTIME ──┐  ┌─ REQUESTS ─┐  ┌─ RPS ────────┐   ║
║  │ ● ONLINE  │  │  2h 14m   │  │   12,847   │  │   142.3/s    │   ║
║  └───────────┘  └───────────┘  └────────────┘  └──────────────┘   ║
║                                                                   ║
║  ┌─ RPS CHART (60 วินาทีล่าสุด) ─────────────────────────────────┐    ║
║  │  150 ┤                     ╭──╮                           │    ║
║  │  100 ┤              ╭─────╯  ╰──╮      ╭──╮               │    ║
║  │   50 ┤  ╭──────────╯            ╰──────╯  ╰───            │    ║
║  │    0 ┤──╯                                                 │    ║
║  │      └────────────────────────────────────────────        │    ║
║  └───────────────────────────────────────────────────────────────┘║
║                                                                   ║
║  [ ▶ Start Backend ]  [ ▶ Start Proxy ]  [ ⚡ Stress Test ]       ║
║                                                                   ║
║  ┌─ TERMINAL ────────────────────────────────────────────────────┐║
║  │ $ ./my_server                                                 │║
║  │ [+] Listening on 127.0.0.1:3000 (private)                    │║
║  │ [+] Routes: / | /VANGUARD | /stats                           │║
║  │ $ ./vanguard_proxy                                            │║
║  │ [+] Listening on 0.0.0.0:8080 (epoll)                        │║
║  │ [+] WAF: SQLi + XSS detection enabled                        │║
║  └───────────────────────────────────────────────────────────────┘║
║  $ █                                                              ║
╚═══════════════════════════════════════════════════════════════════╝
```

### คุณสมบัติ

- **Dashboard แบบ Real-time** — ดึงข้อมูลจาก `http://127.0.0.1:3000/stats` ทุกวินาที แสดงสถานะเซิร์ฟเวอร์, Uptime, จำนวน Request ทั้งหมด, Connection ที่ Active และ RPS ที่คำนวณได้
- **กราฟเส้น RPS** — พล็อตแบบ Real-time ด้วย `pyqtgraph` แสดง Requests Per Second ย้อนหลัง 60 วินาที
- **Terminal ในตัว** — รันคำสั่ง Shell ได้โดยตรงจาก GUI พร้อมสตรีม stdout/stderr แบบ Real-time
- **ปุ่มลัด** — กดปุ่มเดียวเพื่อเริ่ม Backend, Proxy หรือรัน Stress Test
- **ไม่บล็อก UI** — Thread ดึงข้อมูลทำงานอยู่เบื้องหลัง ทำให้ UI ไม่ค้าง
- **ธีมมืด** — อินเทอร์เฟซธีมมืดสไตล์ Hacker พร้อมสีเขียว Matrix

### วิธีเปิดใช้งาน

```bash
python3 vanguard_gui.py
```

### Dependencies ที่จำเป็น

```
PyQt6 >= 6.4
pyqtgraph >= 0.13
```

---

## TUI Dashboard สำหรับ Terminal

สำหรับสภาพแวดล้อมที่ใช้ Terminal เท่านั้น สามารถใช้ TUI Dashboard ที่สร้างด้วย Rich สำหรับ Monitoring แบบ Real-time:

```bash
python3 dashboard.py
```

```bash
# เชื่อมต่อไปยัง Backend ระยะไกล
python3 dashboard.py --url http://192.168.1.10:3000/stats
```

คุณสมบัติ:
- แผงแสดงสถานะเซิร์ฟเวอร์ (Online/Offline)
- แผง Metrics (Total Requests, Active Connections, RPS)
- กราฟ Sparkline แบบ Unicode แสดงประวัติ RPS
- รีเฟรชอัตโนมัติทุก 1 วินาที
- UI แบบเต็มหน้าจอ Terminal

---

## เครื่องมือ CLI และ Stress Testing

### `vanguard_stress.py` — เครื่องมือทดสอบ Load แบบ Asynchronous

เครื่องมือทดสอบ Stress ประสิทธิภาพสูงที่สร้างบน `asyncio` และ `aiohttp` ของ Python ออกแบบมาเพื่อทดสอบกฎ WAF และ Rate Limiter ของ Proxy ภายใต้ Load

### โหมดการทดสอบ

| โหมด | แฟล็ก | คำอธิบาย | Response ที่คาดหวัง |
|---|---|---|---|
| **Normal** | `-m normal` | Traffic ปกติพร้อมหน่วงเวลา 10ms | HTTP 200 (ผ่านทั้งหมด) |
| **Bruteforce** | `-m bruteforce` | ยิงถล่มไม่หน่วงเวลาเพื่อกระตุ้น Rate Limiter | HTTP 200 + 429 (ถูกจำกัดอัตรา) |
| **SQL Injection** | `-m sqli` | ส่ง Payload SQLi เพื่อทดสอบการบล็อกของ WAF | HTTP 403 (ถูกบล็อกโดย WAF) |

### วิธีใช้งาน

```bash
# ทดสอบ Load ปกติ (1000 requests, 50 concurrent)
python3 vanguard_stress.py -m normal

# ยิงถล่มแบบ Bruteforce (5000 requests, 100 concurrent)
python3 vanguard_stress.py -m bruteforce -c 100 -n 5000

# ทดสอบ SQL Injection (200 requests, 20 concurrent)
python3 vanguard_stress.py -m sqli -c 20 -n 200

# กำหนด URL เป้าหมายเอง
python3 vanguard_stress.py -m normal -t http://192.168.1.10:8080
```

### ตัวเลือกคำสั่ง

| แฟล็ก | ค่าเริ่มต้น | คำอธิบาย |
|---|---|---|
| `-m, --mode` | `normal` | โหมดทดสอบ: `normal`, `bruteforce`, `sqli` |
| `-c, --concurrency` | `50` | จำนวน Connection พร้อมกัน |
| `-n, --num-requests` | `1000` | จำนวน Request ทั้งหมดที่จะส่ง |
| `-t, --target` | `http://127.0.0.1:8080` | URL ฐานของเป้าหมาย |

### ตัวอย่างผลลัพธ์

```
  ╔══════════════════════════════════════════════════════════╗
  ║         VANGUARD STRESS TEST — RESULTS REPORT            ║
  ╚══════════════════════════════════════════════════════════╝

  สรุปประสิทธิภาพ
  ──────────────────────────────────────────────────────────
  เวลาทั้งหมด       2.347s
  Throughput (RPS)  426.1 req/s
  สำเร็จ             1,000
  ล้มเหลว            0

  การกระจายตัวของ LATENCY
  ──────────────────────────────────────────────────────────
  ค่าเฉลี่ย          4.23 ms
  P50 (Median)      3.81 ms
  P95               8.14 ms
  P99               12.67 ms

  HTTP STATUS CODES
  ──────────────────────────────────────────────────────────
  200 OK              ████████████████████████████  712 (71.2%)
  429 RATE LIMITED    ████████████                  288 (28.8%)

  ✓ ผ่าน — Rate Limiter ทำงานสำเร็จ
```

---

## การ Deploy ด้วย Docker

### Build และ Run

การเรียกใช้งานคำสั่ง Docker บนระบบปฏิบัติการส่วนใหญ่จำเป็นต้องมีสิทธิ์ผู้ดูแลระบบ โดยใช้ `sudo` นำหน้าคำสั่ง:

```bash
# Build และเริ่มในโหมด Detached
sudo docker compose up -d

# ดู Log ของคอนเทนเนอร์
sudo docker compose logs -f vanguard

# ตรวจสอบสถานะและ Health ของเซอร์วิส
sudo docker compose ps

# หยุดการทำงานและลบคอนเทนเนอร์
sudo docker compose down
```

### รายละเอียด Container

| คุณสมบัติ | ค่า |
|---|---|
| ชื่อ Container | `vanguard-v2` |
| Port ที่เปิด | `8080` → Proxy |
| Health Check | `curl http://localhost:8080/VANGUARD` ทุก 15 วินาที |
| จำกัด CPU | 2.0 cores |
| จำกัดหน่วยความจำ | 256 MB |
| นโยบาย Restart | `unless-stopped` |
| Timezone | `Asia/Bangkok` |

Docker Image จะ Build ไบนารี C++ ทั้งสองจาก Source Code, เริ่ม Backend Server ก่อน จากนั้นจึงเปิด Proxy — ทั้งหมดจัดการโดยสคริปต์ `entrypoint.sh`

---

## การตั้งค่า

### `config.conf`

ไฟล์ตั้งค่าหลักของ Proxy (โหลดเมื่อเริ่มทำงานถ้ามีไฟล์อยู่)

### `whitelist.conf`

IP ที่ระบุในไฟล์นี้จะข้ามการ Rate Limiting (IP ละบรรทัด) อย่างไรก็ตาม การตรวจสอบ WAF ยังคงใช้กับทุก IP โดยไม่คำนึงถึงสถานะ Whitelist

```conf
# IP ที่อยู่ใน Whitelist — ข้ามการ Rate Limit
127.0.0.1
10.0.0.1
192.168.1.100
```

### การปรับแต่ง Rate Limiter

พารามิเตอร์ของ Rate Limiter ถูกกำหนดเป็นค่าคงที่ตอน Compile ใน `vanguard_proxy.cpp`:

```cpp
static constexpr double RATE_TOKENS_S = 10.0;  // จำนวน token ที่เติมต่อวินาที
static constexpr double RATE_BURST    = 10.0;  // ความจุสูงสุดของ bucket
```

---

## โครงสร้างโปรเจกต์

```
PROJECTVANGUARD/
├── vanguard_proxy.cpp      # Edge Proxy + WAF Engine (C++17, epoll)
├── my_server.cpp           # Backend Server แบบ Private (C++17)
├── vanguard_gui.py         # Desktop Control Center (PyQt6 + pyqtgraph)
├── dashboard.py            # TUI Dashboard (Rich)
├── vanguard_stress.py      # เครื่องมือทดสอบ Stress แบบ Async (aiohttp)
├── Makefile                # ระบบ Build (make / make clean)
├── include/
│   └── colors.h            # ค่าคงที่สี ANSI
├── config.conf             # ไฟล์ตั้งค่า Proxy
├── whitelist.conf          # Whitelist IP สำหรับ Rate Limiter
├── test.sh                 # ชุดทดสอบ Integration
├── simulate_attack.sh      # สคริปต์จำลองการโจมตี
├── unban.sh                # เครื่องมือปลด Ban IP
├── Dockerfile              # Build Container แบบ Multi-stage
├── docker-compose.yml      # จัดการ Container
├── entrypoint.sh           # สคริปต์ Entrypoint ของ Docker
├── requirements.txt        # Python Dependencies
├── tests/
│   ├── test_ip.cpp         # Unit Test สำหรับ IP utilities
│   ├── test_config.cpp     # Unit Test สำหรับ Config parser
│   └── test_rate.cpp       # Unit Test สำหรับ Rate Limiter
└── LICENSE                 # สัญญาอนุญาต MIT
```

---

## Makefile Targets

| Target | คำอธิบาย |
|---|---|
| `make` | Build `vanguard_proxy` และ `my_server` |
| `make run-proxy` | Build และรัน Proxy |
| `make run-backend` | Build และรัน Backend Server |
| `make test` | รันชุดทดสอบ Integration (`test.sh`) |
| `make test-unit` | รัน C++ Unit Tests |
| `make simulate` | รันการจำลองการโจมตี |
| `make clean` | ลบไบนารีที่ Compile แล้วทั้งหมด |

---

  ╔══════════════════════════════════════════════╗
  ║  Make by Sattaya Thongdaeng                  ║
  ╚══════════════════════════════════════════════╝

---
## สัญญาอนุญาต

โปรเจกต์นี้อยู่ภายใต้สัญญาอนุญาต MIT ดูรายละเอียดที่ [LICENSE](LICENSE)