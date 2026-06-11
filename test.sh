#!/bin/bash
# test server + sentinel
# ต้องเปิด server ไว้ก่อน

URL="http://localhost:8080"
G="\033[1;32m"; R="\033[1;31m"; Y="\033[1;33m"; C="\033[1;36m"; X="\033[0m"

echo -e "\n${C}=== Vanguard Test Suite ===${X}\n"

# test 1
echo -ne "${Y}[Test 1]${X} GET / ... "
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/")
[ "$CODE" == "200" ] && echo -e "${G}PASS${X} ($CODE)" || echo -e "${R}FAIL${X} ($CODE)"
sleep 1

# test 2
echo -ne "${Y}[Test 2]${X} GET /VANGUARD ... "
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/VANGUARD")
[ "$CODE" == "200" ] && echo -e "${G}PASS${X} ($CODE)" || echo -e "${R}FAIL${X} ($CODE)"
sleep 1

# test 3
echo -ne "${Y}[Test 3]${X} Content-Length header ... "
HDR=$(curl -s -I "$URL/")
echo "$HDR" | grep -qi "Content-Length" && echo -e "${G}PASS${X}" || echo -e "${R}FAIL${X}"
sleep 1

# test 4
echo -ne "${Y}[Test 4]${X} Log file ... "
[ -f "server_log.txt" ] && echo -e "${G}PASS${X} ($(wc -l < server_log.txt) lines)" || echo -e "${R}FAIL${X}"
sleep 1

# test 5
echo -ne "${Y}[Test 5]${X} 5 concurrent requests ... "
for i in $(seq 1 5); do curl -s -o /dev/null "$URL/" & done
wait
echo -e "${G}PASS${X}"

# sentinel test
echo -e "\n${C}--- Sentinel Rate Detection ---${X}"
echo -e "${Y}[!]${X} จะส่ง 10 requests รวด (ถ้า ip ไม่อยู่ใน whitelist อาจโดน ban)"
read -p "กด Enter เพื่อเริ่ม... "

for i in $(seq 1 10); do
    resp=$(curl -s -o /dev/null -w "%{http_code}" "$URL/")
    echo -e "  ${C}#$i${X} -> HTTP $resp"
done

echo -e "\n${G}Done!${X} ดู terminal sentinel ว่ามี THREAT DETECTED มั้ย"
echo -e "ถ้าโดน ban: ${C}sudo ./unban.sh --all${X}\n"
