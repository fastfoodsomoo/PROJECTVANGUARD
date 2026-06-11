#!/bin/bash
# จำลองการโจมตีจาก ip ปลอมหลายตัว
# เขียน log ลง server_log.txt ให้ sentinel ตรวจจับ
# * ต้องเปิด sentinel ใน terminal อื่นก่อน! *

LOG="server_log.txt"
G="\033[1;32m"; R="\033[1;31m"; Y="\033[1;33m"; C="\033[1;36m"; X="\033[0m"
[ ! -f "$LOG" ] && touch "$LOG"

echo -e "\n${C}=== Attack Simulator ===${X}"
echo -e "${Y}[!]${X} เปิด sentinel ใน terminal อื่นก่อนนะ!\n"

inject() {
    local ip="$1" ua="$2" path="$3"
    local ts=$(date "+%Y-%m-%d %H:%M:%S")
    echo "========== LOG ENTRY ==========
Time: $ts
IP Address: $ip
Request Data :
GET $path HTTP/1.1
Host: target:8080
User-Agent: $ua
" >> "$LOG"
}

# --- 1: user ปกติ 2 ครั้ง (ไม่ควรโดน ban) ---
echo -e "${C}[Scenario 1]${X} Normal user — 192.168.1.50 (2 requests)"
for i in 1 2; do
    inject "192.168.1.50" "Chrome (visit #$i)" "/"
    echo -e "  injected ${G}#$i${X}"
    sleep 1
done
echo -e "  Expected: ${G}Not banned${X} (below threshold)\n"
sleep 2

# --- 2: brute force 8 ครั้งจาก ip เดียว (ควรโดน ban!) ---
echo -e "${R}[Scenario 2]${X} Brute force — 10.0.0.66 (8 requests)"
for i in $(seq 1 8); do
    inject "10.0.0.66" "BruteBot (attempt #$i)" "/admin"
    echo -e "  injected ${R}#$i${X}"
    sleep 0.5
done
echo -e "  Expected: ${R}BANNED!${X} (exceeds threshold)\n"
sleep 2

# --- 3: หลาย ip คนละครั้ง (ไม่ควร ban) ---
echo -e "${Y}[Scenario 3]${X} Distributed scan — 172.16.0.10~14 (1 each)"
for i in $(seq 10 14); do
    inject "172.16.0.$i" "Scanner" "/scan"
    echo -e "  injected ${Y}172.16.0.$i${X}"
    sleep 0.8
done
echo -e "  Expected: ${G}Not banned${X} (distributed)\n"
sleep 2

# --- 4: ddos อีก ip ---
echo -e "${R}[Scenario 4]${X} DDoS flood — 203.0.113.99 (7 requests)"
for i in $(seq 1 7); do
    inject "203.0.113.99" "FloodTool (req #$i)" "/login"
    echo -e "  injected ${R}#$i${X}"
    sleep 0.3
done
echo -e "  Expected: ${R}BANNED!${X}\n"
sleep 1

# สรุป
echo -e "${C}=== Summary ===${X}"
echo -e "  192.168.1.50    (2x)  -> ${G}safe${X}"
echo -e "  10.0.0.66       (8x)  -> ${R}BANNED${X}"
echo -e "  172.16.0.10-14  (1x)  -> ${G}safe${X}"
echo -e "  203.0.113.99    (7x)  -> ${R}BANNED${X}"
echo ""
echo -e "ไปดู terminal sentinel เพื่อยืนยันผล"
echo -e "ปลด ban: ${C}sudo ./unban.sh --all${X}\n"
