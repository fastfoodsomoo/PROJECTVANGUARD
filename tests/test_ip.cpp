// ═══════════════════════════════════════════════════════════════
// Vanguard — Unit Test: IP Validation
// ทดสอบฟังก์ชัน valid_ip() และ parse_ip() จาก ip_utils.h
// ═══════════════════════════════════════════════════════════════

#include "../include/ip_utils.h"
#include <cassert>
#include <iostream>
#include <string>

#define TEST(name) std::cout << "  testing: " << name << "... ";
#define PASS()     std::cout << "\033[1;32mPASS\033[0m" << std::endl;

int main() {
    std::cout << "\n\033[1;36m=== IP Validation Tests ===\033[0m\n" << std::endl;

    // ── valid_ip(): Valid addresses ──────────────────────────
    TEST("valid — 192.168.1.1")
    assert(valid_ip("192.168.1.1") == true);
    PASS()

    TEST("valid — 0.0.0.0")
    assert(valid_ip("0.0.0.0") == true);
    PASS()

    TEST("valid — 255.255.255.255")
    assert(valid_ip("255.255.255.255") == true);
    PASS()

    TEST("valid — 10.0.0.1")
    assert(valid_ip("10.0.0.1") == true);
    PASS()

    TEST("valid — 127.0.0.1 (loopback)")
    assert(valid_ip("127.0.0.1") == true);
    PASS()

    TEST("valid — 1.1.1.1")
    assert(valid_ip("1.1.1.1") == true);
    PASS()

    // ── valid_ip(): Invalid addresses ───────────────────────
    TEST("invalid — 256.1.1.1 (octet > 255)")
    assert(valid_ip("256.1.1.1") == false);
    PASS()

    TEST("invalid — 1.2.3 (only 3 octets)")
    assert(valid_ip("1.2.3") == false);
    PASS()

    TEST("invalid — empty string")
    assert(valid_ip("") == false);
    PASS()

    TEST("invalid — abc.def.ghi.jkl (letters)")
    assert(valid_ip("abc.def.ghi.jkl") == false);
    PASS()

    TEST("invalid — 1.2.3.4.5 (5 octets)")
    assert(valid_ip("1.2.3.4.5") == false);
    PASS()

    TEST("invalid — 192.168.1.999 (octet > 255)")
    assert(valid_ip("192.168.1.999") == false);
    PASS()

    TEST("invalid — single number")
    assert(valid_ip("12345") == false);
    PASS()

    TEST("invalid — with spaces")
    assert(valid_ip("192.168.1. 1") == false);
    PASS()

    // ── parse_ip(): Extract IP from log line ────────────────
    TEST("parse — 'IP Address: 192.168.1.1'")
    assert(parse_ip("IP Address: 192.168.1.1") == "192.168.1.1");
    PASS()

    TEST("parse — 'IP Address:10.0.0.1' (no space)")
    assert(parse_ip("IP Address:10.0.0.1") == "10.0.0.1");
    PASS()

    TEST("parse — 'IP Address:  127.0.0.1  ' (extra spaces)")
    assert(parse_ip("IP Address:  127.0.0.1  ") == "127.0.0.1");
    PASS()

    TEST("parse — 'Some other line' (no tag)")
    assert(parse_ip("Some other line") == "");
    PASS()

    TEST("parse — empty string")
    assert(parse_ip("") == "");
    PASS()

    TEST("parse — 'Time: 2026-01-01' (wrong tag)")
    assert(parse_ip("Time: 2026-01-01") == "");
    PASS()

    std::cout << "\n\033[1;32m✓ All IP validation tests passed!\033[0m\n" << std::endl;
    return 0;
}
