# Vanguard — In-line Reverse Proxy & WAF Engine

![C++17](https://img.shields.io/badge/C%2B%2B-17-blue?style=flat-square&logo=cplusplus)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-orange?style=flat-square&logo=linux)
![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)

Reverse Proxy พร้อม Web Application Firewall (WAF) เขียนด้วย **C++17** ตั้งแต่ต้น ทำงานแบบ In-line คล้าย Cloudflare Edge Proxy — ตรวจจับ SQL Injection, XSS, จำกัด Rate ต่อ IP แล้ว forward request ที่ปลอดภัยไปยัง backend

```
 ╔════════════════════════════════════════════════════════╗
 ║   VANGUARD EDGE PROXY — Cloudflare-like WAF Engine    ║
 ║   C++17 • epoll • Zero-Copy • In-line Filtering       ║
 ╚════════════════════════════════════════════════════════╝
```

## สารบัญ

- [สถาปัตยกรรม](#สถาปัตยกรรม)
- [ฟีเจอร์](#ฟีเจอร์)
- [วิธีใช้งาน](#วิธีใช้งาน)
- [การตั้งค่า](#การตั้งค่า)
- [หลักการทำงาน](#หลักการทำงาน)
- [Docker](#docker)
- [Dashboard (Observability)](#dashboard-observability)
- [Stress Tester (Performance)](#stress-tester-performance)
- [การทดสอบ](#การทดสอบ)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [สิ่งที่ได้เรียนรู้](#สิ่งที่ได้เรียนรู้)
- [ผู้พัฒนา](#ผู้พัฒนา)

---

## สถาปัตยกรรม

```
                       ┌──────────────────┐
                       │  Client/Attacker │
                       └────────┬─────────┘
                                │ HTTP Request
                                ▼
              ┌──────────────────────────────────────┐
              │        vanguard_proxy (Port 8080)     │
              │        ── Edge Proxy & WAF ──         │
              │                                      │
              │  1. Parse HTTP (string_view)          │
              │  2. WAF: ตรวจ SQLi / XSS patterns    │
              │     ├─ ตรงกัน → 403 Forbidden        │
              │     └─ ปลอดภัย → ไปต่อ               │
              │  3. Rate Limit: Token Bucket per-IP   │
              │     ├─ เกิน → 429 Too Many Requests  │
              │     └─ ผ่าน → forward                │
              │  4. Inject headers:                   │
              │     X-Vanguard-Connecting-IP           │
              │     X-Vanguard-Ray-ID                  │
              │  5. Forward ไป backend                │
              │  6. รับ response กลับมา               │
              │  7. Override: Server header            │
              └───────────────┬──────────────────────┘
                              │ (ถ้าปลอดภัย)
                              ▼
              ┌──────────────────────────────────────┐
              │        my_server (Port 3000)          │
              │     ── Backend Web Server ──          │
              │     Bind: 127.0.0.1 เท่านั้น          │
              │     ไม่เปิดรับจากภายนอกโดยตรง          │
              │                                      │
              │  Routes: / | /VANGUARD | /stats       │
              │  Log: แสดง injected headers จาก proxy │
              └──────────────────────────────────────┘
```

**ก่อนหน้า (v1):** Client → server:8080 → เขียน log ลงดิสก์ → sentinel อ่าน log → iptables ban

**ตอนนี้ (v2):** Client → vanguard_proxy:8080 → ตรวจสอบ in-line ทันที → forward หรือ block

---

## ฟีเจอร์

### Edge Proxy / WAF (`vanguard_proxy.cpp`)

| ฟีเจอร์ | รายละเอียด |
|---------|-----------|
| **epoll Event Loop** | ใช้ `epoll(7)` กับ non-blocking socket (`O_NONBLOCK`) สำหรับ accept loop ที่รองรับ connection จำนวนมาก |
| **Zero-Copy HTTP Parsing** | Parse request ด้วย `std::string_view` — ไม่ copy string ระหว่างตรวจสอบ |
| **Token Bucket Rate Limiter** | จำกัด rate ต่อ IP แบบ in-memory (10 req/s, burst 10) ด้วย `std::unordered_map` + `std::mutex` |
| **WAF: SQL Injection** | ตรวจจับ 22 patterns เช่น `UNION SELECT`, `' OR '1'='1`, `DROP TABLE` (รวม URL-encoded) |
| **WAF: XSS** | ตรวจจับ 18 patterns เช่น `<script>`, `javascript:`, `onerror=`, `eval()` |
| **Reverse Proxy** | Forward request ไป `127.0.0.1:3000` พร้อม inject `X-Vanguard-Connecting-IP` และ `X-Vanguard-Ray-ID` |
| **Header Override** | แทนที่ `Server:` header ใน response เป็น `Vanguard-Edge-Engine/1.0` |
| **Whitelist** | IP ใน `whitelist.conf` ข้ามการเช็ค rate limit (แต่ยังผ่าน WAF) |
| **Custom Block Pages** | หน้า HTML สำหรับ 429, 403, 502 แบบ terminal panel พร้อม Ray ID |

### Backend Server (`my_server.cpp`)

| ฟีเจอร์ | รายละเอียด |
|---------|-----------|
| **Private Binding** | Bind เฉพาะ `127.0.0.1:3000` — ไม่เปิดรับ connection จากภายนอก |
| **Header Logging** | แสดง `X-Vanguard-Connecting-IP` และ `X-Vanguard-Ray-ID` ที่ proxy inject มา |
| **Multi-threaded** | สร้าง thread ใหม่สำหรับแต่ละ request |
| **HTTP Routing** | รองรับ `/` (หน้าหลัก), `/VANGUARD` (status), `/stats` (JSON), 404, 405 |
| **Graceful Shutdown** | `Ctrl+C` → รอ thread ที่ทำงานอยู่จบก่อนปิด |

---

## วิธีใช้งาน

### สิ่งที่ต้องมี

- Linux (หรือ WSL บน Windows)
- `g++` ที่รองรับ C++17
- `make`
- `curl` (สำหรับ test)

### Build

```bash
git clone https://github.com/fastfoodsomoo/PROJECTVANGUARD.git
cd PROJECTVANGUARD

make clean && make
```

### รัน

ต้องเปิด 2 terminal:

```bash
# Terminal 1 — Backend (ต้องเปิดก่อน)
./my_server

# Terminal 2 — Edge Proxy / WAF
./vanguard_proxy
```

### ทดสอบ

```bash
# Terminal 3
curl http://localhost:8080/                          # หน้าหลัก (ผ่าน proxy)
curl -I http://localhost:8080/                       # ดู Server header
curl "http://localhost:8080/?id=1' OR '1'='1"        # ทดสอบ SQLi → 403
curl "http://localhost:8080/?q=<script>alert(1)</script>"  # ทดสอบ XSS → 403
```

---

## การตั้งค่า

### `whitelist.conf`

IP ที่อยู่ในไฟล์นี้จะ**ข้ามการเช็ค rate limit** (แต่ยังต้องผ่าน WAF):

```conf
# Vanguard Edge Proxy — Whitelisted IPs
# 127.0.0.1 ถูก comment ไว้เพื่อให้ test rate limit จาก localhost ได้
# Uncomment ในเครื่อง production ถ้าต้องการ

# 127.0.0.1
192.168.1.50
10.0.0.1
```

### Rate Limit (ตั้งค่าใน source code)

ค่า default ตั้งไว้ใน `vanguard_proxy.cpp`:

| ค่า | Default | หมายความ |
|-----|---------|---------|
| `RATE_TOKENS_S` | 10.0 | เติม 10 tokens ต่อวินาที |
| `RATE_BURST` | 10.0 | ถังจุได้สูงสุด 10 tokens |
| `PROXY_PORT` | 8080 | port ที่ proxy ฟัง |
| `BACKEND_PORT` | 3000 | port ของ backend |

---

## หลักการทำงาน

### Pipeline ทีละขั้น

```
Request เข้ามา
    │
    ▼
[1] Parse HTTP Request ─── string_view (zero-copy)
    │                      แยก method, URI, headers, body
    ▼
[2] WAF Inspection ─────── ตรวจ URI + body
    │                      SQLi patterns (22 ตัว)
    │                      XSS patterns (18 ตัว)
    │                      case-insensitive + URL-decoded
    ├─ ตรงกัน → 403 Forbidden (ทันที, ไม่ forward)
    │
    ▼
[3] Rate Limit ─────────── Token Bucket per-IP
    │                      เช็คว่า IP อยู่ใน whitelist ไหม
    │                      ถ้าไม่ → ตรวจ token ในถัง
    ├─ หมด → 429 Too Many Requests
    │
    ▼
[4] Forward to Backend ─── connect() ไป 127.0.0.1:3000
    │                      inject X-Vanguard-Connecting-IP
    │                      inject X-Vanguard-Ray-ID
    │
    ▼
[5] รับ Response ───────── อ่าน response จาก backend
    │                      override Server header
    │                      ส่งกลับให้ client
    ▼
Done
```

### Token Bucket Rate Limiter

แต่ละ IP มี "ถังเหรียญ" ของตัวเอง:

- ถังเริ่มต้นมี `RATE_BURST` (10) เหรียญ
- ทุก request ใช้ 1 เหรียญ
- ถังเติมเหรียญ `RATE_TOKENS_S` (10) เหรียญต่อวินาที
- ถ้าเหรียญหมด → ตอบ 429 ทันที
- IP ใน whitelist ข้ามขั้นตอนนี้

### WAF Patterns

**SQLi** — ตรวจจับ patterns เหล่านี้ (case-insensitive):
```
union select    ' or '1'='1    drop table    ; select
'; drop         1=1--          select * from  insert into
delete from     exec(          sleep(         benchmark(
```

**XSS** — ตรวจจับ patterns เหล่านี้:
```
<script         javascript:    onerror=       onload=
onclick=        alert(         eval(          <iframe
document.cookie prompt(        confirm(       expression(
```

ทุก pattern ตรวจทั้งแบบปกติและ URL-encoded (เช่น `%3Cscript`, `%20OR%20`)

---

## Docker

รัน Vanguard ทั้ง proxy + backend ใน container เดียวด้วย multi-stage build

### สถาปัตยกรรม Container

```
┌─────────────────────────────────────────────┐
│  Alpine 3.20 Container                      │
│                                             │
│  entrypoint.sh (PID 1 via tini)             │
│  ├── my_server       → 127.0.0.1:3000      │
│  └── vanguard_proxy  → 0.0.0.0:8080  ←─────┼── exposed
│                                             │
│  whitelist.conf                             │
└─────────────────────────────────────────────┘
```

### Multi-Stage Build

| Stage | Base Image | หน้าที่ |
|-------|-----------|--------|
| **builder** | `alpine:3.20` + g++ | คอมไพล์ทั้ง 2 binaries ด้วย `-static` |
| **runtime** | `alpine:3.20` (clean) | รันเฉพาะ binaries + curl (healthcheck) + tini (PID 1) |

### รันด้วย Docker Compose

```bash
# Build และรัน
docker compose up --build -d

# เช็ค health status
docker compose ps
docker inspect --format='{{.State.Health.Status}}' vanguard-v2

# ดู logs
docker compose logs -f

# หยุด
docker compose down
```

### ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | หน้าที่ |
|------|--------|
| `Dockerfile` | Multi-stage build (builder → runtime), non-root user, tini PID 1 |
| `docker-compose.yml` | Expose port 8080, healthcheck `/VANGUARD`, resource limits, log rotation |
| `entrypoint.sh` | เปิด my_server (background) → รอ port 3000 ready → เปิด vanguard_proxy (foreground) |
| `.dockerignore` | ตัดไฟล์ที่ไม่จำเป็นออกจาก build context |

### Design Decisions

- **Static linking** (`-static`) — binary รันได้บน minimal Alpine โดยไม่ต้องพึ่ง glibc
- **tini** เป็น PID 1 — forward signal (SIGTERM) ไปยัง child processes ได้ถูกต้อง
- **Non-root user** (`vanguard`) — ลด attack surface ใน container
- **Healthcheck** — Docker ตรวจ `/VANGUARD` ผ่าน proxy ทุก 15 วินาที เพื่อยืนยันว่าทั้ง proxy และ backend ทำงานอยู่

---

## Dashboard (Observability)

TUI Dashboard แบบ real-time สำหรับ monitor Vanguard backend เขียนด้วย Python + Rich

### หน้าจอ

```
╔══════════════════════════════════════════════╗
║   VANGUARD v2 — Observability Dashboard     ║
╚══════════════════════════════════════════════╝
┌─ SERVER STATUS ──────┐┌─ METRICS ───────────┐
│ ● ONLINE             ││ Total Requests 1,500│
│ Server Vanguard-2.0  ││ Active Conns       2│
│ Uptime  6m 0s        ││ Current RPS    45.2 │
│ Bind  127.0.0.1:3000 ││ Average RPS    38.7 │
│                      ││ Peak RPS       52.1 │
└──────────────────────┘└─────────────────────┘
┌─ RPS HISTORY (sparkline) ───────────────────┐
│ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▁▂▃▄▅▆▇█▇▆▅▄▃▂▁            │
└─────────────────────────────────────────────┘
```

### ฟีเจอร์

| ฟีเจอร์ | รายละเอียด |
|---------|------------|
| **Server Status** | แสดง Online/Offline พร้อมสี (เขียว/แดง) |
| **Metrics** | Total requests, active connections, current/average/peak RPS |
| **RPS Sparkline** | กราฟ Unicode block ย้อนหลัง 50 วินาที เปลี่ยนสีตามความเข้ม |
| **Error Handling** | แสดง `● OFFLINE` สีแดงเมื่อ backend ไม่ตอบ โดยไม่ crash |
| **Auto-refresh** | Poll `/stats` ทุก 1 วินาที |

### วิธีใช้

```bash
pip install -r requirements.txt

# รัน dashboard (ต้องเปิด my_server ก่อน)
python dashboard.py

# ใช้กับ host อื่น
python dashboard.py --url http://192.168.1.10:3000/stats
```

### RPS Calculation

RPS คำนวณแบบ **dynamic** จากผลต่างของ `total_requests` ระหว่าง 2 รอบ poll:

```
RPS = (total_requests[t] - total_requests[t-1]) / interval
```

---

## Stress Tester (Performance)

Asynchronous stress tester สำหรับทดสอบ performance และ security ของ Vanguard proxy เขียนด้วย Python + asyncio + aiohttp

### 3 โหมดการทดสอบ

| โหมด | URL | Delay | ผลที่คาดหวัง |
|------|-----|-------|--------------|
| `normal` | `http://127.0.0.1:8080/` | 10ms | HTTP 200 ทั้งหมด |
| `bruteforce` | `http://127.0.0.1:8080/` | 0ms (flood) | ผสม HTTP 200 + 429 |
| `sqli` | `http://127.0.0.1:8080/?id=1'%20OR%20'1'%3D'1` | 5ms | HTTP 403 |

### รายงานผลลัพธ์

Script จะแสดงรายงานแบบ formatted ประกอบด้วย:

| ส่วน | รายละเอียด |
|------|------------|
| **Performance Summary** | Total time, throughput (RPS), completed/failed |
| **Latency Distribution** | Average, Min, Max, P50, P95, P99 (มิลลิวินาที) |
| **Status Code Breakdown** | กราฟแท่ง Unicode พร้อมจำนวนและเปอร์เซ็นต์ |
| **Verdict** | Pass/Fail อัตโนมัติตามผลที่คาดหวังของแต่ละโหมด |

### วิธีใช้

```bash
pip install -r requirements.txt

# Normal load test (50 concurrent, 1000 requests)
python vanguard_stress.py -m normal

# Bruteforce — ทดสอบ rate limiter
python vanguard_stress.py -m bruteforce -c 100 -n 5000

# SQLi — ทดสอบ WAF
python vanguard_stress.py -m sqli -c 20 -n 200

# กำหนด target เอง
python vanguard_stress.py -m normal -t http://192.168.1.10:8080
```

### Arguments

| Flag | Default | คำอธิบาย |
|------|---------|----------|
| `-m`, `--mode` | `normal` | โหมด: `normal`, `bruteforce`, `sqli` |
| `-c`, `--concurrency` | `50` | จำนวน concurrent connections |
| `-n`, `--num-requests` | `1000` | จำนวน requests ทั้งหมด |
| `-t`, `--target` | `http://127.0.0.1:8080` | Base URL ของ target |

---

## การทดสอบ

### Test Suite อัตโนมัติ

```bash
# เปิด my_server + vanguard_proxy ก่อน แล้วรัน:
./test.sh
```

สิ่งที่ test:

| # | การทดสอบ | คาดหวัง |
|---|---------|---------|
| 1 | `GET /` ผ่าน proxy → backend | HTTP 200 |
| 2 | Response header `Server:` | `Vanguard-Edge-Engine/1.0` |
| 3 | `Content-Length` header | มี |
| 4 | `GET /VANGUARD` | HTTP 200 |
| 5 | `GET /stats` | JSON ที่มี `"status"` |
| 6 | SQLi payload `' OR '1'='1` | HTTP 403 |
| 7 | XSS payload `<script>` | HTTP 403 |
| 8 | 20 requests รวด | HTTP 429 (หลัง burst หมด) |
| 9 | 5 concurrent requests | ไม่ crash |

### จำลองการโจมตี

```bash
./simulate_attack.sh
```

4 สถานการณ์:

| สถานการณ์ | รายละเอียด | ผลลัพธ์ |
|-----------|-----------|---------|
| Normal User | 2 GET requests ปกติ | HTTP 200 |
| Brute Force | 15 requests รวด | บาง request ได้ 429 |
| SQLi | `?id=1' OR '1'='1` | HTTP 403 |
| XSS | `?q=<script>alert(1)</script>` | HTTP 403 |

### ทดสอบด้วยมือ

```bash
# Request ปกติ
curl http://localhost:8080/

# ดู headers
curl -I http://localhost:8080/

# SQLi
curl "http://localhost:8080/?id=1'%20OR%20'1'='1"

# XSS
curl "http://localhost:8080/?q=%3Cscript%3Ealert(1)%3C/script%3E"

# Rate limit (ส่งรัว ๆ)
for i in $(seq 1 15); do
    echo "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)"
done
```

### Unit Tests (จาก v1)

```bash
make test-unit
```

| ไฟล์ | ทดสอบ |
|------|------|
| `tests/test_ip.cpp` | IP validation + parsing (20 cases) |
| `tests/test_config.cpp` | Config parser (7 cases) |
| `tests/test_rate.cpp` | Rate detection algorithm (9 cases) |

---

## โครงสร้างโปรเจกต์

```
vanguard/
├── vanguard_proxy.cpp      # Edge Proxy + WAF Engine (epoll, rate limit, WAF)
├── my_server.cpp           # Backend Web Server (127.0.0.1:3000)
├── whitelist.conf          # IP ที่ bypass rate limit
├── Makefile                # Build system (g++ -std=c++17 -O3)
│
├── Dockerfile              # Multi-stage build (Alpine builder → runtime)
├── docker-compose.yml      # Orchestration + healthcheck + resource limits
├── entrypoint.sh           # Container entrypoint (backend + proxy)
├── .dockerignore           # Exclude files จาก build context
│
├── dashboard.py            # TUI Dashboard (Rich) — monitor /stats
├── vanguard_stress.py      # Async Stress Tester (asyncio + aiohttp)
├── requirements.txt        # Python dependencies
│
├── simulate_attack.sh      # จำลองการโจมตีผ่าน curl
├── test.sh                 # Test suite อัตโนมัติ
│
├── include/                # Shared headers
│   ├── colors.h            #   ANSI color constants
│   ├── config.h            #   Config parser (ใช้กับ legacy v1)
│   ├── ip_utils.h          #   IP validation & parsing
│   └── logger.h            #   Thread-safe Logger (ใช้กับ legacy v1)
│
├── tests/                  # Unit tests
│   ├── test_ip.cpp         #   IP validation (20 cases)
│   ├── test_config.cpp     #   Config parser (7 cases)
│   └── test_rate.cpp       #   Rate detection (9 cases)
│
├── server.cpp              # [Legacy v1] HTTP Server (port 8080)
├── sentinel.cpp            # [Legacy v1] Log-based IDS/IPS
├── config.conf             # [Legacy v1] Shared config file
├── unban.sh                # [Legacy v1] iptables unban script
│
├── .github/workflows/      # CI/CD
├── .gitignore
├── LICENSE                 # MIT
└── README.md               # ไฟล์นี้
```

---

## เทคโนโลยีที่ใช้

| เทคโนโลยี | การใช้งาน |
|-----------|---------|
| **C++17** | ภาษาหลัก — `std::string_view`, structured bindings, `constexpr` |
| **Linux epoll** | Event loop สำหรับ non-blocking accept (proxy) |
| **POSIX Sockets** | TCP socket programming ตั้งแต่ต้น |
| **std::thread** | Thread-per-connection สำหรับ proxy handler |
| **std::mutex** | Thread-safe rate limiter + console output |
| **std::atomic** | Lock-free counters (requests, blocked, forwarded) |
| **std::unordered_map** | Token bucket storage per-IP |
| **std::unordered_set** | Whitelist lookup O(1) |
| **std::mt19937_64** | Ray ID generation (thread-local RNG) |
| **Docker** | Multi-stage build, Alpine runtime, tini PID 1, healthcheck |
| **Python (Rich)** | TUI observability dashboard พร้อม sparkline |
| **Python (asyncio + aiohttp)** | Async stress tester รองรับ 3 โหมด |

---

## สิ่งที่ได้เรียนรู้

### Network & Systems Programming
- สร้าง HTTP Server + Reverse Proxy ตั้งแต่ต้นด้วย POSIX `socket()`, `bind()`, `listen()`, `accept()`, `connect()`
- ใช้ `epoll(7)` สำหรับ non-blocking I/O ที่รองรับ connection จำนวนมาก
- ใช้ `string_view` สำหรับ zero-copy parsing — ลด memory allocation ระหว่าง request inspection

### Concurrency
- ออกแบบ thread-safe rate limiter ด้วย `std::mutex` + `std::lock_guard`
- ใช้ `inet_ntop()` แทน `inet_ntoa()` เพราะ thread-safe
- ใช้ `std::atomic` สำหรับ counters ที่หลาย thread เข้าถึงพร้อมกัน
- `SIGPIPE` ignored เพื่อไม่ให้ crash เมื่อ client ปิด connection กลางทาง

### Security
- ออกแบบ WAF engine ที่ตรวจจับ SQLi + XSS patterns ทั้ง raw และ URL-encoded
- ใช้ Token Bucket algorithm สำหรับ rate limiting ที่ยืดหยุ่นกว่า sliding window
- แยก proxy (public) กับ backend (private/loopback) เพื่อลด attack surface
- Inject headers (`X-Vanguard-Connecting-IP`) เพื่อให้ backend รู้ IP จริงของ client

### Software Design
- เปลี่ยนจาก out-of-band (อ่าน log file) เป็น in-line (ตรวจสอบทันทีก่อน forward)
- แยก concerns: proxy ทำ security, backend ทำ business logic
- ใช้ Ray ID สำหรับ request tracing ข้าม proxy และ backend

### DevOps & Tooling
- ออกแบบ multi-stage Docker build ที่ static-link binaries สำหรับ minimal Alpine runtime
- ใช้ `tini` เป็น PID 1 เพื่อ forward signals อย่างถูกต้องใน container
- สร้าง TUI dashboard ด้วย Rich library พร้อม sparkline visualization
- สร้าง async stress tester ด้วย `asyncio` + `aiohttp` พร้อม latency percentiles (P50/P95/P99)

---

## ผู้พัฒนา

**สัตยา ทองแดง (Sattaya Thongdaeng)**

---

## สัญญาอนุญาต

โปรเจกต์นี้ใช้สัญญาอนุญาต MIT — ดูรายละเอียดที่ไฟล์ [LICENSE](LICENSE)
