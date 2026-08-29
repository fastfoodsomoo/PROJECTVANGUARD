#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Vanguard v2 — Attack Simulator
# ส่ง HTTP requests จริงผ่าน curl ไปยัง proxy (port 8080)
# แทนการเขียน log ปลอมแบบเดิม
#
# ต้องเปิด vanguard_proxy + my_server ก่อนรัน!
# ═══════════════════════════════════════════════════════════════

URL="http://localhost:8080"
G="\033[1;32m"; R="\033[1;31m"; Y="\033[1;33m"; C="\033[1;36m"
M="\033[1;35m"; D="\033[2m"; X="\033[0m"

echo -e "\n${M}╔════════════════════════════════════════════════════╗${X}"
echo -e "${M}║     VANGUARD v2 — Attack Simulator                 ║${X}"
echo -e "${M}║     Target: ${URL}                   ║${X}"
echo -e "${M}╚════════════════════════════════════════════════════╝${X}\n"

echo -e "${Y}[!]${X} ต้องเปิด vanguard_proxy + my_server ก่อน!"
echo -e "${D}    Terminal 1: ./my_server${X}"
echo -e "${D}    Terminal 2: ./vanguard_proxy${X}\n"
sleep 1

PASS=0; FAIL=0

check() {
    local expected="$1" actual="$2" label="$3"
    if [ "$actual" == "$expected" ]; then
        echo -e "    ${G}✓${X} HTTP ${actual} ${D}(expected ${expected})${X}"
        ((PASS++))
    else
        echo -e "    ${R}✗${X} HTTP ${actual} ${D}(expected ${expected})${X}"
        ((FAIL++))
    fi
}

# ═══════════════════════════════════════════════════════════════
# Scenario 1: Normal User — 2 requests (expect 200)
# ═══════════════════════════════════════════════════════════════
echo -e "${C}[Scenario 1]${X} Normal User — 2 GET requests"
for i in 1 2; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/")
    echo -ne "  Request #$i: "
    check "200" "$CODE" "normal"
    sleep 0.5
done
echo ""
sleep 1

# ═══════════════════════════════════════════════════════════════
# Scenario 2: Brute Force / Rate Limit — 15 rapid requests
# Token Bucket: 10 burst, 10/s refill
# First ~10 should be 200, remaining should be 429
# ═══════════════════════════════════════════════════════════════
echo -e "${R}[Scenario 2]${X} Brute Force — 15 rapid requests (rate limit test)"
echo -e "  ${D}Token Bucket: burst=10, rate=10/s${X}"
GOT_429=false
for i in $(seq 1 15); do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/")
    if [ "$CODE" == "429" ]; then
        GOT_429=true
        echo -e "  Request #$(printf '%2d' $i): ${R}HTTP 429${X} — Rate Limited! 🛑"
    else
        echo -e "  Request #$(printf '%2d' $i): ${G}HTTP ${CODE}${X}"
    fi
done
if $GOT_429; then
    echo -e "  ${G}✓${X} Rate limiting triggered successfully"
    ((PASS++))
else
    echo -e "  ${R}✗${X} Expected some 429 responses but got none"
    echo -e "  ${Y}  Hint: Is 127.0.0.1 in whitelist.conf? It bypasses rate limiting.${X}"
    ((FAIL++))
fi
echo ""
sleep 2

# ═══════════════════════════════════════════════════════════════
# Scenario 3: WAF — SQL Injection (expect 403)
# ═══════════════════════════════════════════════════════════════
echo -e "${R}[Scenario 3]${X} WAF Test — SQL Injection"

echo -ne "  Payload: ' OR '1'='1 → "
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/?id=1'%20OR%20'1'='1")
check "403" "$CODE" "sqli1"

echo -ne "  Payload: UNION SELECT → "
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/?q=1%20UNION%20SELECT%20*%20FROM%20users")
check "403" "$CODE" "sqli2"

echo -ne "  Payload: DROP TABLE  → "
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/?x=;DROP%20TABLE%20users")
check "403" "$CODE" "sqli3"

echo ""
sleep 1

# ═══════════════════════════════════════════════════════════════
# Scenario 4: WAF — XSS (expect 403)
# ═══════════════════════════════════════════════════════════════
echo -e "${R}[Scenario 4]${X} WAF Test — Cross-Site Scripting (XSS)"

echo -ne "  Payload: <script>alert(1)</script> → "
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/?q=%3Cscript%3Ealert(1)%3C/script%3E")
check "403" "$CODE" "xss1"

echo -ne "  Payload: onerror=alert()          → "
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/?img=x%20onerror=alert(1)")
check "403" "$CODE" "xss2"

echo -ne "  Payload: javascript:void           → "
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/?url=javascript:void(0)")
check "403" "$CODE" "xss3"

echo ""

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
TOTAL=$((PASS + FAIL))
echo -e "${M}╔═══════════════════════════════════════╗${X}"
echo -e "${M}║           Simulation Summary          ║${X}"
echo -e "${M}╚═══════════════════════════════════════╝${X}"
echo -e "  ${G}Passed: ${PASS}${X} / ${TOTAL}"
echo -e "  ${R}Failed: ${FAIL}${X} / ${TOTAL}"
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo -e "  ${G}★ All scenarios passed! Vanguard WAF is working correctly.${X}"
else
    echo -e "  ${Y}⚠ Some scenarios failed. Check proxy logs for details.${X}"
fi
echo -e "\n${D}ไปดู terminal ของ vanguard_proxy เพื่อดู logs ย้อนกลับ${X}\n"
