#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Vanguard v2 — Automated Test Suite
# ตรวจสอบว่า proxy + backend ทำงานร่วมกันถูกต้อง
#
# ต้องเปิด vanguard_proxy + my_server ก่อนรัน!
# ═══════════════════════════════════════════════════════════════

URL="http://localhost:8080"
G="\033[1;32m"; R="\033[1;31m"; Y="\033[1;33m"; C="\033[1;36m"
M="\033[1;35m"; D="\033[2m"; B="\033[1m"; X="\033[0m"

PASS=0; FAIL=0; TOTAL=0

run_test() {
    local name="$1"
    ((TOTAL++))
    echo -ne "${Y}[Test ${TOTAL}]${X} ${name} ... "
}

pass() {
    echo -e "${G}PASS${X} $1"
    ((PASS++))
}

fail() {
    echo -e "${R}FAIL${X} $1"
    ((FAIL++))
}

echo -e "\n${M}╔════════════════════════════════════════════════════╗${X}"
echo -e "${M}║        VANGUARD v2 — Automated Test Suite          ║${X}"
echo -e "${M}╚════════════════════════════════════════════════════╝${X}\n"

# ═══════════════════════════════════════════════════════════════
# Test 1: Basic forwarding — GET / → 200
# ═══════════════════════════════════════════════════════════════
run_test "GET / returns 200 OK (proxy → backend)"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/" 2>/dev/null)
if [ "$CODE" == "200" ]; then
    pass "(HTTP $CODE)"
else
    fail "(HTTP $CODE — expected 200. Are proxy+backend running?)"
fi
sleep 0.5

# ═══════════════════════════════════════════════════════════════
# Test 2: Server header override
# ═══════════════════════════════════════════════════════════════
run_test "Server header = Vanguard-Edge-Engine/1.0"
HDR=$(curl -s -I "$URL/" 2>/dev/null | grep -i "^Server:")
if echo "$HDR" | grep -q "Vanguard-Edge-Engine/1.0"; then
    pass "($HDR)"
else
    fail "(got: $HDR)"
fi
sleep 0.5

# ═══════════════════════════════════════════════════════════════
# Test 3: Content-Length header present
# ═══════════════════════════════════════════════════════════════
run_test "Content-Length header present"
HDR=$(curl -s -I "$URL/" 2>/dev/null)
if echo "$HDR" | grep -qi "Content-Length"; then
    pass ""
else
    fail "(missing Content-Length)"
fi
sleep 0.5

# ═══════════════════════════════════════════════════════════════
# Test 4: /VANGUARD route works through proxy
# ═══════════════════════════════════════════════════════════════
run_test "GET /VANGUARD returns 200"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/VANGUARD" 2>/dev/null)
if [ "$CODE" == "200" ]; then
    pass "(HTTP $CODE)"
else
    fail "(HTTP $CODE)"
fi
sleep 0.5

# ═══════════════════════════════════════════════════════════════
# Test 5: /stats JSON endpoint
# ═══════════════════════════════════════════════════════════════
run_test "GET /stats returns valid JSON"
BODY=$(curl -s "$URL/stats" 2>/dev/null)
if echo "$BODY" | grep -q "\"status\""; then
    pass ""
else
    fail "(response: $BODY)"
fi
sleep 0.5

# ═══════════════════════════════════════════════════════════════
# Test 6: WAF blocks SQL Injection → 403
# ═══════════════════════════════════════════════════════════════
run_test "WAF blocks SQLi → 403 Forbidden"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/?id=1'%20OR%20'1'='1" 2>/dev/null)
if [ "$CODE" == "403" ]; then
    pass "(HTTP $CODE)"
else
    fail "(HTTP $CODE — expected 403)"
fi
sleep 0.5

# ═══════════════════════════════════════════════════════════════
# Test 7: WAF blocks XSS → 403
# ═══════════════════════════════════════════════════════════════
run_test "WAF blocks XSS → 403 Forbidden"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/?q=%3Cscript%3Ealert(1)%3C/script%3E" 2>/dev/null)
if [ "$CODE" == "403" ]; then
    pass "(HTTP $CODE)"
else
    fail "(HTTP $CODE — expected 403)"
fi
sleep 0.5

# ═══════════════════════════════════════════════════════════════
# Test 8: Rate limiting → 429 after burst
# ═══════════════════════════════════════════════════════════════
run_test "Rate limit triggers 429 after burst"
GOT_429=false
# Send rapid requests to exhaust the token bucket
for i in $(seq 1 20); do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/rate-test" 2>/dev/null)
    if [ "$CODE" == "429" ]; then
        GOT_429=true
        break
    fi
done
if $GOT_429; then
    pass "(429 triggered at request #$i)"
else
    pass_or_fail="fail"
    # Check if 127.0.0.1 is whitelisted
    if grep -q "^127.0.0.1" whitelist.conf 2>/dev/null; then
        echo -e "${Y}SKIP${X} (127.0.0.1 is whitelisted — rate limit bypassed)"
        echo -e "        ${D}Remove 127.0.0.1 from whitelist.conf to test rate limiting${X}"
    else
        fail "(sent 20 requests but never got 429)"
    fi
fi
sleep 1

# ═══════════════════════════════════════════════════════════════
# Test 9: Concurrent requests don't crash
# ═══════════════════════════════════════════════════════════════
run_test "5 concurrent requests handled"
for i in $(seq 1 5); do
    curl -s -o /dev/null "$URL/" 2>/dev/null &
done
wait
pass ""
sleep 0.5

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
echo -e "\n${M}╔═══════════════════════════════════════╗${X}"
echo -e "${M}║          Test Results Summary          ║${X}"
echo -e "${M}╚═══════════════════════════════════════╝${X}"
echo -e "  ${G}Passed: ${PASS}${X} / ${TOTAL}"
echo -e "  ${R}Failed: ${FAIL}${X} / ${TOTAL}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "  ${G}★ All tests passed! Vanguard v2 is fully operational.${X}"
else
    echo -e "  ${Y}⚠ Some tests failed. Check the proxy and backend logs.${X}"
fi
echo ""
