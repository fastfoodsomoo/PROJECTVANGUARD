// ═══════════════════════════════════════════════════════════════
// Vanguard — Unit Test: Rate Detection Algorithm
// ทดสอบ sliding window algorithm ที่ sentinel ใช้ตรวจจับ
// ═══════════════════════════════════════════════════════════════

#include <cassert>
#include <iostream>
#include <deque>
#include <map>
#include <string>
#include <ctime>

#define TEST(name) std::cout << "  testing: " << name << "... ";
#define PASS()     std::cout << "\033[1;32mPASS\033[0m" << std::endl;

// จำลอง rate detection algorithm เหมือนที่ใช้ใน sentinel.cpp
// คืน true ถ้าเกิน threshold (ต้อง ban)
bool check_rate(std::map<std::string, std::deque<time_t>>& history,
                const std::string& ip, time_t now,
                int threshold, int window) {
    auto& hist = history[ip];
    hist.push_back(now);

    // ลบ entry ที่เก่ากว่า window
    while (!hist.empty() && (now - hist.front()) > window)
        hist.pop_front();

    return (int)hist.size() >= threshold;
}

int main() {
    std::cout << "\n\033[1;36m=== Rate Detection Tests ===\033[0m\n" << std::endl;

    // ── Test 1: Below threshold — ไม่ควร ban ──────────────
    TEST("below threshold — not banned")
    {
        std::map<std::string, std::deque<time_t>> history;
        time_t now = 1000;
        // 4 hits กับ threshold=5 → ยังไม่ ban
        for (int i = 0; i < 4; i++) {
            assert(!check_rate(history, "1.1.1.1", now + i, 5, 60));
        }
    }
    PASS()

    // ── Test 2: At threshold — ควร ban ────────────────────
    TEST("at threshold — banned on 5th hit")
    {
        std::map<std::string, std::deque<time_t>> history;
        time_t now = 1000;
        // 4 hits ก่อน → ยังไม่ ban
        for (int i = 0; i < 4; i++) {
            assert(!check_rate(history, "2.2.2.2", now + i, 5, 60));
        }
        // hit ที่ 5 → ban!
        assert(check_rate(history, "2.2.2.2", now + 4, 5, 60) == true);
    }
    PASS()

    // ── Test 3: Sliding window expiry ─────────────────────
    TEST("sliding window — old entries expire")
    {
        std::map<std::string, std::deque<time_t>> history;
        time_t now = 1000;
        // 3 hits ที่เวลา 1000
        for (int i = 0; i < 3; i++) {
            check_rate(history, "3.3.3.3", now, 5, 10);
        }
        // 2 hits ที่เวลา 1015 (15 วินาทีต่อมา > window=10s)
        // entry เก่าต้องหมดอายุ → เหลือแค่ 2 hits → ยังไม่ ban
        assert(!check_rate(history, "3.3.3.3", now + 15, 5, 10));
        assert(!check_rate(history, "3.3.3.3", now + 16, 5, 10));
    }
    PASS()

    // ── Test 4: Different IPs — tracked independently ─────
    TEST("different IPs tracked independently")
    {
        std::map<std::string, std::deque<time_t>> history;
        time_t now = 1000;
        // IP A: 4 hits
        for (int i = 0; i < 4; i++) {
            check_rate(history, "4.4.4.4", now + i, 5, 60);
        }
        // IP B: 1 hit → ไม่ควร ban (independent)
        assert(!check_rate(history, "5.5.5.5", now, 5, 60));
        // IP A: hit ที่ 5 → ban!
        assert(check_rate(history, "4.4.4.4", now + 5, 5, 60) == true);
    }
    PASS()

    // ── Test 5: Burst attack ──────────────────────────────
    TEST("burst attack — rapid hits detected")
    {
        std::map<std::string, std::deque<time_t>> history;
        time_t now = 1000;
        bool banned = false;
        // 10 hits ในเวลาเดียวกัน → ต้อง ban
        for (int i = 0; i < 10; i++) {
            if (check_rate(history, "6.6.6.6", now, 5, 60)) {
                banned = true;
                assert(i >= 4);  // ban ครั้งแรกที่ hit #5 (index 4)
                break;
            }
        }
        assert(banned);
    }
    PASS()

    // ── Test 6: Spread over time — ไม่ ban ────────────────
    TEST("spread over time — not banned")
    {
        std::map<std::string, std::deque<time_t>> history;
        // 4 hits แต่ละครั้งห่างกัน 20 วินาที กับ window=15s
        // ทุกครั้งจะมีแค่ 1 hit ใน window
        for (int i = 0; i < 4; i++) {
            assert(!check_rate(history, "7.7.7.7", (time_t)(1000 + i * 20), 5, 15));
        }
    }
    PASS()

    // ── Test 7: Exact boundary — window ────────────────────
    TEST("exact boundary — entry at exactly window edge")
    {
        std::map<std::string, std::deque<time_t>> history;
        time_t now = 1000;
        // hit ที่เวลา 1000
        check_rate(history, "8.8.8.8", now, 5, 10);
        // hit ที่เวลา 1010 (ห่างพอดี 10 วินาที)
        // entry เก่าที่ now=1000 ยังอยู่ (> ไม่ใช่ >=)
        check_rate(history, "8.8.8.8", now + 10, 5, 10);
        // ควรเหลือ 2 entries
        assert(history["8.8.8.8"].size() == 2);
        // hit ที่เวลา 1011 (ห่าง 11 วินาที > window=10)
        // entry ที่ 1000 ต้องหมดอายุ
        check_rate(history, "8.8.8.8", now + 11, 5, 10);
        assert(history["8.8.8.8"].size() == 2);  // เหลือ 1010 กับ 1011
    }
    PASS()

    // ── Test 8: Threshold = 1 — ban ทันที ─────────────────
    TEST("threshold=1 — banned immediately")
    {
        std::map<std::string, std::deque<time_t>> history;
        assert(check_rate(history, "9.9.9.9", 1000, 1, 60) == true);
    }
    PASS()

    // ── Test 9: Large threshold ───────────────────────────
    TEST("large threshold — needs many hits")
    {
        std::map<std::string, std::deque<time_t>> history;
        time_t now = 1000;
        for (int i = 0; i < 99; i++) {
            assert(!check_rate(history, "10.10.10.10", now + i, 100, 300));
        }
        // hit ที่ 100 → ban!
        assert(check_rate(history, "10.10.10.10", now + 99, 100, 300) == true);
    }
    PASS()

    std::cout << "\n\033[1;32m✓ All rate detection tests passed!\033[0m\n" << std::endl;
    return 0;
}
