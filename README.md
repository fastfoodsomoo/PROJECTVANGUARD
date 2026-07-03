# 🛡️ Vanguard — ระบบรักษาความปลอดภัยเครือข่ายด้วย C++

![C++17](https://img.shields.io/badge/C%2B%2B-17-blue?style=flat-square&logo=cplusplus)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-orange?style=flat-square&logo=linux)
![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square)

HTTP Server แบบ Multi-threaded พร้อมระบบตรวจจับและป้องกันการบุกรุก (IDS/IPS) แบบ Real-time เขียนด้วย **C++17** บน POSIX Sockets ทั้งหมดตั้งแต่ต้น ไม่ใช้ framework ใดๆ

```
 ╔══════════════════════════════════════╗
 ║     VANGUARD  —  C++ Core Server     ║
 ║         Network Security Suite       ║
 ╚══════════════════════════════════════╝
```

## 📋 สารบัญ

- [ภาพรวมโปรเจกต์](#ภาพรวมโปรเจกต์)
- [สถาปัตยกรรมระบบ](#สถาปัตยกรรมระบบ)
- [ฟีเจอร์](#ฟีเจอร์)
- [เทคโนโลยีที่ใช้](#เทคโนโลยีที่ใช้)
- [วิธีเริ่มต้นใช้งาน](#วิธีเริ่มต้นใช้งาน)
- [การตั้งค่า](#การตั้งค่า)
- [หลักการทำงาน](#หลักการทำงาน)
- [การทดสอบ](#การทดสอบ)
- [วิธี Bypass / Unban ตัวเอง](#วิธี-bypass--unban-ตัวเอง)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [สิ่งที่ได้เรียนรู้](#สิ่งที่ได้เรียนรู้)
- [แผนพัฒนาในอนาคต](#แผนพัฒนาในอนาคต)
- [ผู้พัฒนา](#ผู้พัฒนา)

---

## ภาพรวมโปรเจกต์

**Vanguard** คือโปรเจกต์ด้านความปลอดภัยเครือข่าย ที่แสดงให้เห็นถึงความเข้าใจในการเขียนโปรแกรมระดับ System Programming:

- **Socket Programming** — สร้าง HTTP Server ตั้งแต่ต้นโดยไม่ใช้ library ภายนอก
- **Multi-threading** — รองรับ Client หลายคนพร้อมกันอย่างปลอดภัย (Thread-safe logging)
- **Process Management** — ใช้ `fork()` และ `exec()` ในการสั่งงาน Firewall
- **Real-time Log Monitoring** — ตรวจสอบ Log ของ Server อย่างต่อเนื่อง
- **Rate-based Intrusion Detection** — ตรวจจับและบล็อกรูปแบบทราฟฟิกที่น่าสงสัย
- **Path-based Detection** — ตรวจจับ Request ไปยัง Path ที่อันตราย (เช่น `/admin`, `/wp-login`)

โปรเจกต์นี้ออกแบบมาเพื่อแสดงความเข้าใจด้าน Computer Networking, Operating Systems และ Security Fundamentals

---

## สถาปัตยกรรมระบบ

```
                        ┌─────────────────────┐
                        │   Client (Browser)  │
                        └─────────┬───────────┘
                                  │ HTTP Request
                                  ▼
                  ┌───────────────────────────────┐
                  │        Vanguard Server        │
                  │         (server.cpp)          │
                  │                               │
                  │  ┌──────────┐  ┌────────────┐ │
                  │  │  Socket  │  │  จัดการ     │ │
                  │  │  Listener│──│  Thread    │ │
                  │  └──────────┘  └────────────┘ │
                  │        │               │      │
                  │        ▼               ▼      │
                  │  ┌──────────┐  ┌────────────┐ │  
                  │  │  แยกวิเค- │  │    สร้าง    │ │
                  │  │   ราะห์   │  │    HTTP    │ │
                  │  │  Request │  │  Response  │ │
                  │  └──────────┘  └────────────┘ │
                  └───────────┬───────────────────┘
                              │ บันทึก Log (Thread-safe)
                              ▼
                    ┌───────────────────┐
                    │  server_log.txt   │ ◄── ไฟล์ Log ที่ใช้ร่วมกัน
                    └─────────┬─────────┘
                              │ อ่านแบบ Real-time
                              ▼
                  ┌────────────────────────────────┐
                  │      Vanguard Sentinel         │
                  │       (sentinel.cpp)           │
                  │                                │
                  │  ┌──────────┐  ┌────────────┐  │
<<<<<<< HEAD
                  │  │  แยกวิเค- │  │  ตรวจจับ    │  │
                  │  │  ราะห์    │──│  ตาม Rate  │  │
                  │  │  Log     │  └────────────┘  │
=======
                  │  │  แยกวิเค-│  │  ตรวจจับ   │  │
                  │  │  ราะห์   │──│  ตาม Rate   │  │
                  │  │  Log     │  │  + Path     │  │
                  │  │          │  └────────────┘  │
>>>>>>> ec22e6c (Feat: Add Vanguard Proxy engine and clean workspace)
                  │  └──────────┘         │        │
                  │        │              ▼        │
                  │  ┌──────────┐  ┌────────────┐  │
                  │  │  ตรวจสอบ │  │  สั่ง Ban    │  │
                  │  │  IP      │  │  (iptables)│  │
                  │  └──────────┘  └────────────┘  │
                  └────────────────────────────────┘
```

**ลำดับการทำงาน:**
1. Client ส่ง HTTP Request มาที่ **Server**
2. Server บันทึก Request (IP, เวลา, Headers) ลงใน `server_log.txt` ผ่าน **Thread-safe Logger**
3. **Sentinel** เฝ้าดูไฟล์ Log แบบ Real-time
4. หาก IP ใดเชื่อมต่อเกินจำนวนที่กำหนด หรือเข้าถึง Path ที่น่าสงสัย จะถูก **Ban ผ่าน iptables** ทันที

---

## ฟีเจอร์

### 🖥️ Server (`server.cpp`)
| ฟีเจอร์ | รายละเอียด |
|---------|------------|
| **Raw Socket HTTP** | สร้าง HTTP Server จากศูนย์ด้วย POSIX `socket()`, `bind()`, `listen()`, `accept()` |
| **Multi-threaded** | สร้าง Thread ใหม่สำหรับแต่ละ Client เพื่อรองรับการเชื่อมต่อพร้อมกัน |
| **Thread-safe Logging** | ใช้ `std::mutex` ป้องกัน Race Condition เมื่อ Thread หลายตัวเขียน Log |
| **จำกัดจำนวน Connection** | ใช้ Atomic Counter จำกัดจำนวน Thread สูงสุดเพื่อป้องกัน DoS |
| **HTTP Routing** | รองรับ `/`, `/VANGUARD`, `/stats` พร้อม 404 และ 405 |
| **Stats Endpoint** | `/stats` คืน JSON แสดงสถานะ: requests, connections, uptime |
| **ตั้งค่าได้** | Port, Timeout, จำนวน Connection สูงสุด อ่านจาก `config.conf` |
| **ปิดอย่างปลอดภัย** | Graceful Shutdown ด้วย `atomic<bool>` — รอ Thread จบก่อนปิด |
| **ป้องกัน Buffer Overflow** | จำกัดขนาด Buffer และทำ Null-termination อย่างถูกต้อง |
| **Modern UI** | หน้า HTML แบบ Dark Theme พร้อม CSS Animation |

### 🔍 Sentinel (`sentinel.cpp`)
| ฟีเจอร์ | รายละเอียด |
|---------|------------|
| **เฝ้าระวังแบบ Real-Time** | ตรวจสอบไฟล์ Log อย่างต่อเนื่องเพื่อหา Entry ใหม่ |
| **ตรวจจับตาม Rate** | Ban เฉพาะ IP ที่เชื่อมต่อเกิน N ครั้งภายในกรอบเวลาที่กำหนด |
| **Path-based Detection** | ตรวจจับ Request ไปยัง Path อันตราย (เช่น `/admin`, `/wp-login`) |
| **ตรวจสอบ IP** | ใช้ Regex ตรวจสอบรูปแบบ IP พร้อมเช็คช่วง 0-255 ทุก Octet |
| **รองรับ Whitelist** | IP ที่เชื่อถือได้จาก `whitelist.conf` จะไม่ถูก Ban |
| **สั่ง Firewall อย่างปลอดภัย** | ใช้ `fork()` + `execl()` แทน `system()` ในการสั่ง iptables |
| **แสดงสถิติ** | แสดง Scan Count, Blocked IPs, Suspicious Paths ทุก 30 วินาที |
| **Sliding Window ที่มีประสิทธิภาพ** | ใช้ `std::deque` แทน `vector` สำหรับ O(1) pop_front |

### 🧩 Modular Architecture
| ส่วนประกอบ | รายละเอียด |
|-----------|------------|
| `include/config.h` | Shared config parser — ใช้ร่วมกันทั้ง server และ sentinel |
| `include/colors.h` | ANSI color constants — ลด code duplication |
| `include/ip_utils.h` | IP validation & parsing — แยกออกมาเพื่อ unit test |
| `include/logger.h` | Thread-safe Logger class — ป้องกัน Race Condition |

---

## เทคโนโลยีที่ใช้

| เทคโนโลยี | การใช้งาน |
|-----------|----------|
| **C++17** | ภาษาหลัก |
| **POSIX Sockets** | จัดการ Network I/O (`sys/socket.h`, `netinet/in.h`) |
| **std::thread** | Multi-threading สำหรับรองรับ Client พร้อมกัน |
| **std::mutex** | Thread-safe Logging ป้องกัน Race Condition |
| **std::atomic** | Lock-free counters สำหรับ request count, thread count |
| **iptables** | Firewall ระดับ Linux Kernel |
| **fork/exec** | สร้าง Process ลูกอย่างปลอดภัยสำหรับคำสั่งระบบ |
| **std::regex** | ตรวจสอบรูปแบบ IP Address |
| **std::deque** | Sliding window algorithm ที่มีประสิทธิภาพ |
| **GitHub Actions** | CI/CD สำหรับ Build & Test อัตโนมัติ |

---

## วิธีเริ่มต้นใช้งาน

### สิ่งที่ต้องมี
- ระบบปฏิบัติการ Linux (หรือ WSL บน Windows)
- `g++` ที่รองรับ C++17
- `make`
- `iptables` (สำหรับ Sentinel ต้องใช้สิทธิ์ root)

### การ Build

```bash
# Clone repository
git clone https://github.com/your-username/vanguard.git
cd vanguard

# Build ทั้ง Server และ Sentinel
make all

# รัน Unit Tests
make test-unit
```

### การรัน

```bash
# Terminal 1: เริ่มต้น Server
make run-server
# หรือ: ./my_server

# Terminal 2: เริ่มต้น Sentinel (ต้องใช้สิทธิ์ root สำหรับ iptables)
make run-sentinel
# หรือ: sudo ./sentinel

# Terminal 3: ทดสอบด้วย Browser หรือ curl
curl http://localhost:8080/          # หน้า Default
curl http://localhost:8080/VANGUARD  # หน้า Vanguard
curl http://localhost:8080/stats     # JSON Stats
```

---

## การตั้งค่า

ตั้งค่าทั้งหมดอยู่ใน [`config.conf`](config.conf):

```conf
# ตั้งค่า Server
port            = 8080       # Port ที่ Server จะรับฟัง
max_connections = 64         # จำนวน Client Thread สูงสุด
recv_timeout    = 5          # Timeout ในการรับข้อมูล (วินาที)
log_path        = server_log.txt

# ตั้งค่า Sentinel
ban_threshold   = 5          # Ban หลังเชื่อมต่อ N ครั้ง...
time_window     = 60         # ...ภายในเวลากี่วินาที
whitelist       = whitelist.conf
```

IP ที่เชื่อถือได้ใส่ใน [`whitelist.conf`](whitelist.conf):
```
127.0.0.1
192.168.1.100
```

> **หมายเหตุ:** Config parser มี error handling — ถ้าค่าไม่ถูกต้อง (เช่น `port = abc`) จะใช้ค่า default แทน โดยไม่ crash

---

## หลักการทำงาน

### ลำดับการเชื่อมต่อ
```
Client เชื่อมต่อ  ──►  Server รับ (สร้าง Thread ใหม่)
                           │
                           ├── บันทึก: IP + เวลา + Headers (Thread-safe)
                           ├── Route: / | /VANGUARD | /stats | 404 | 405
                           └── ส่ง HTTP Response แล้วปิด Socket

ในขณะเดียวกัน...

Sentinel อ่าน Log  ──►  ดึง IP จาก "IP Address:"
                              │
                              ├── IP ไม่ถูกต้อง?   → ข้าม
                              ├── อยู่ใน Whitelist? → ปล่อยผ่าน
                              ├── Request Path น่าสงสัย? → แจ้งเตือน ⚠
                              ├── ต่ำกว่า Threshold? → เฝ้าระวัง
                              └── เกิน Threshold?   → BAN (iptables DROP)
```

### อัลกอริทึมตรวจจับตาม Rate (Rate-Based Detection)
แทนที่จะ Ban ทุก IP ที่ไม่รู้จักทันที Sentinel จะติดตามความถี่ของการเชื่อมต่อ:

1. เก็บ Timestamp ของการเชื่อมต่อแต่ละ IP ไว้ใน **Sliding Window** (ใช้ `std::deque` สำหรับ O(1) pop_front)
2. ลบ Entry เก่าที่อยู่นอกกรอบเวลา (`time_window` วินาที) ออก
3. หากจำนวนภายใน Window เกิน `ban_threshold` → Ban IP นั้น
4. วิธีนี้ป้องกันการ Ban ผู้ใช้ปกติ ขณะที่ยังจับรูปแบบที่น่าสงสัยได้

### Path-based Detection (ใหม่)
นอกจากการตรวจจับตาม Rate แล้ว Sentinel ยังตรวจจับ Request ที่เข้าถึง Path อันตราย เช่น:
- `/admin`, `/wp-login`, `/wp-admin` — ช่องทางเข้าผู้ดูแล
- `/phpmyadmin`, `/.env`, `/config.php` — ไฟล์ configuration
- `/shell`, `/cmd`, `/exec` — คำสั่งระบบ

---

## การทดสอบ

### Unit Tests (C++)

โปรเจกต์มี Unit Test ที่เขียนด้วย C++ สำหรับทดสอบ core logic:

```bash
# รัน Unit Tests ทั้งหมด
make test-unit
```

| Test File | ทดสอบ | จำนวน Test Cases |
|-----------|--------|-----------------|
| `tests/test_ip.cpp` | IP Validation (`valid_ip`, `parse_ip`) | 20 cases |
| `tests/test_config.cpp` | Config Parser (defaults, custom, errors) | 7 cases |
| `tests/test_rate.cpp` | Rate Detection Algorithm (sliding window) | 9 cases |

### Integration Tests (Shell)

```bash
# Build แล้วรัน Test Suite
make test

# หรือรันตรง
chmod +x test.sh
./test.sh
```

สิ่งที่ Test Suite ทดสอบ:

| ลำดับ | การทดสอบ | รายละเอียด |
|-------|----------|------------|
| 1 | หน้า Default | ส่ง GET `/` แล้วเช็คว่าได้ HTTP 200 |
| 2 | หน้า VANGUARD | ส่ง GET `/VANGUARD` แล้วเช็คว่าได้ HTTP 200 |
| 3 | Content-Length | ตรวจสอบว่า Response มี Header ที่ถูกต้อง |
| 4 | Log File | ตรวจสอบว่า `server_log.txt` ถูกเขียน |
| 5 | Concurrent | ส่ง 5 Request พร้อมกันเพื่อทดสอบ Multi-threading |
| 6 | Rate Detection | ส่ง 10 Request ติดกันเพื่อ trigger Sentinel |

### 🔥 จำลองการโจมตีจาก IP ปลอม (แนะนำ!)

วิธีนี้เห็นผลชัดที่สุด — จำลอง IP ต่างประเทศโจมตีเข้ามาโดยเขียน log entries ปลอมลง `server_log.txt`:

```bash
# Terminal 1 — เปิด Sentinel ไว้ดูผล
sudo ./sentinel

# Terminal 2 — รันตัวจำลองการโจมตี
chmod +x simulate_attack.sh
./simulate_attack.sh

# หรือผ่าน Makefile
make simulate
```

สคริปต์จำลอง 4 สถานการณ์:

| สถานการณ์ | IP ปลอม | จำนวน Request | ผลลัพธ์ที่คาดหวัง |
|-----------|---------|---------------|-------------------|
| 1. ผู้ใช้ปกติ | `192.168.1.50` | 2 ครั้ง | ✅ ไม่ถูก Ban (ต่ำกว่า threshold) |
| 2. Brute Force | `10.0.0.66` | 8 ครั้ง | 🔴 ถูก Ban! (เกิน threshold) |
| 3. Distributed Scan | `172.16.0.10-14` | คนละ 1 ครั้ง | ✅ ไม่ถูก Ban (กระจายตัว) |
| 4. DDoS | `203.0.113.99` | 7 ครั้ง | 🔴 ถูก Ban! (เกิน threshold) |

### ทดสอบด้วยมือ (Manual Test)

```bash
# Terminal 1 — เปิด Server
./my_server

# Terminal 2 — เปิด Sentinel
sudo ./sentinel

# Terminal 3 — ทดสอบ
curl http://localhost:8080/              # หน้า Default
curl http://localhost:8080/VANGUARD      # หน้า Vanguard
curl http://localhost:8080/stats         # JSON Stats
curl -I http://localhost:8080/           # ดูเฉพาะ Headers

# ทดสอบ Rate Detection (ส่ง Request รัว ๆ)
for i in $(seq 1 10); do curl -s http://localhost:8080/ > /dev/null; done
# แล้วดู Terminal ของ Sentinel ว่ามี THREAT DETECTED หรือไม่
```

---

## วิธี Bypass / Unban ตัวเอง

> ⚠️ **ถ้าคุณทดสอบแล้วโดน Sentinel Ban ตัวเอง** — ไม่ต้องตกใจ! ทำตามนี้:

### วิธีที่ 1: ใช้สคริปต์ `unban.sh` (แนะนำ)

```bash
# ปลด Ban ทุก IP ที่ถูกบล็อก
sudo ./unban.sh --all

# หรือปลดเฉพาะ IP ของตัวเอง
sudo ./unban.sh 127.0.0.1

# หรือเปิดเมนูโต้ตอบ
sudo ./unban.sh

# หรือผ่าน Makefile
make unban
```

### วิธีที่ 2: ใช้คำสั่ง iptables ตรง ๆ

```bash
# ดู IP ที่ถูก Ban ทั้งหมด
sudo iptables -L INPUT -n --line-numbers

# ปลด Ban IP ที่ระบุ
sudo iptables -D INPUT -s 127.0.0.1 -j DROP

# ลบ Rule ทุกอันใน INPUT chain (ระวัง! ลบหมดเลย)
sudo iptables -F INPUT
```

### วิธีที่ 3: ป้องกันไม่ให้โดน Ban ตั้งแต่แรก

```bash
# เพิ่ม IP ของตัวเองลงใน whitelist.conf
echo "127.0.0.1" >> whitelist.conf      # สำหรับ localhost
echo "192.168.1.100" >> whitelist.conf   # สำหรับ IP จริง (เปลี่ยนตามเครื่อง)
```

### วิธีที่ 4: เพิ่ม Threshold ชั่วคราว (สำหรับทดสอบ)

แก้ [`config.conf`](config.conf) ให้ threshold สูงขึ้น:
```conf
ban_threshold = 100    # จาก 5 เป็น 100 เพื่อทดสอบ
time_window   = 10     # จาก 60 เป็น 10 วินาที
```
แล้ว restart Sentinel ใหม่

---

## โครงสร้างโปรเจกต์

```
vanguard/
├── include/                # Shared header files
│   ├── colors.h            #   ├── ANSI color constants
│   ├── config.h            #   ├── Config parser + VanguardConfig struct
│   ├── ip_utils.h          #   ├── IP validation & parsing
│   └── logger.h            #   └── Thread-safe Logger class
├── tests/                  # Unit tests (C++)
│   ├── test_ip.cpp         #   ├── IP validation tests (20 cases)
│   ├── test_config.cpp     #   ├── Config parser tests (7 cases)
│   └── test_rate.cpp       #   └── Rate detection tests (9 cases)
├── .github/workflows/      # CI/CD
│   └── build.yml           #   └── GitHub Actions: Build & Test
├── server.cpp              # HTTP Server แบบ Multi-threaded
├── sentinel.cpp            # ระบบตรวจจับภัยคุกคามแบบ Real-time (IDS/IPS)
├── config.conf             # ไฟล์ตั้งค่าที่ใช้ร่วมกัน
├── whitelist.conf          # รายการ IP ที่เชื่อถือได้
├── test.sh                 # สคริปต์ทดสอบ Integration (Shell)
├── simulate_attack.sh      # จำลองการโจมตีจาก IP ปลอม
├── unban.sh                # เครื่องมือปลด Ban IP
├── Makefile                # สคริปต์สำหรับ Build / Test / Run
├── .gitignore              # กฎสำหรับ Git ไม่ Track ไฟล์บางประเภท
├── LICENSE                 # สัญญาอนุญาต MIT
└── README.md               # ไฟล์นี้
```

---

## สิ่งที่ได้เรียนรู้

โปรเจกต์นี้ทำให้ได้เรียนรู้แนวคิดหลายอย่างในเชิงลึก:

### 🔌 Network Programming
- เข้าใจลำดับการทำงานของ Socket: `socket()` → `bind()` → `listen()` → `accept()` → `recv()`/`send()`
- เข้าใจโครงสร้าง HTTP Request/Response ในระดับ byte
- ได้ลองสร้าง HTTP Server ที่ทำงานได้จริงโดยไม่พึ่ง library ภายนอก

### 🧵 Concurrency & Thread Safety
- เข้าใจว่าทำไม Multi-threaded program ต้องมี `mutex` — เจอ Race Condition ในการเขียน Log และแก้ไขด้วย `std::lock_guard`
- เรียนรู้ความแตกต่างระหว่าง `inet_ntoa()` (thread-unsafe) กับ `inet_ntop()` (thread-safe)
- ใช้ `std::atomic` สำหรับ counters ที่หลาย thread เข้าถึง
- ออกแบบ Graceful Shutdown ที่รอ threads จบก่อนปิดโปรแกรม

### 🛡️ Security Concepts
- เข้าใจหลักการของ IDS/IPS (Intrusion Detection/Prevention System)
- ใช้ `fork()` + `execl()` แทน `system()` เพื่อป้องกัน Command Injection
- ออกแบบ Rate Limiting Algorithm ด้วย Sliding Window
- เรียนรู้การใช้ iptables สำหรับ Firewall ระดับ Linux Kernel

### 📐 Software Engineering
- แยก code เป็น Header files เพื่อลด duplication และเพิ่ม reusability
- เขียน Unit Tests ที่ครอบคลุม edge cases
- ใช้ `try-catch` สำหรับ error handling ที่ robust
- เลือกโครงสร้างข้อมูลที่เหมาะสม (`std::deque` แทน `vector` สำหรับ O(1) front removal)

---

## แผนพัฒนาในอนาคต

- [ ] **IPv6 Support** — รองรับ IPv6 Address ใน validation และ firewall
- [ ] **Web Dashboard** — สร้างหน้า Dashboard แสดง Real-time stats, กราฟ traffic, รายการ Banned IPs
- [ ] **HTTP 429 Response** — ส่ง "Too Many Requests" ก่อนที่จะ ban จริง ๆ
- [ ] **User-Agent Detection** — ตรวจจับ bot/scanner จาก User-Agent header
- [ ] **Log Rotation** — หมุนไฟล์ Log อัตโนมัติเมื่อมีขนาดใหญ่
- [ ] **Config Hot-reload** — อ่าน config ใหม่โดยไม่ต้อง restart
- [ ] **Payload Inspection** — ตรวจจับ SQL Injection patterns ใน request body

---

## ผู้พัฒนา

**สัตยา ทองแดง (Sattaya Thongdaeng)**

สร้างด้วย 💚 จาก C++ และ POSIX Systems Programming

---

## สัญญาอนุญาต

โปรเจกต์นี้ใช้สัญญาอนุญาต MIT — ดูรายละเอียดที่ไฟล์ [LICENSE](LICENSE)
