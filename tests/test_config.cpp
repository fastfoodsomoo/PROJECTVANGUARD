// ═══════════════════════════════════════════════════════════════
// Vanguard — Unit Test: Config Parser
// ทดสอบ load_config() จาก config.h
// สร้างไฟล์ config ชั่วคราวแล้วทดสอบว่า parse ถูกต้อง
// ═══════════════════════════════════════════════════════════════

#include "../include/config.h"
#include <cassert>
#include <iostream>
#include <fstream>
#include <cstdio>

#define TEST(name) std::cout << "  testing: " << name << "... ";
#define PASS()     std::cout << "\033[1;32mPASS\033[0m" << std::endl;

// สร้างไฟล์ config ชั่วคราวสำหรับทดสอบ
void write_temp(const std::string& path, const std::string& content) {
    std::ofstream f(path);
    f << content;
    f.close();
}

int main() {
    std::cout << "\n\033[1;36m=== Config Parser Tests ===\033[0m\n" << std::endl;

    // ── Test 1: Default values (file not found) ─────────────
    TEST("defaults when file not found")
    {
        VanguardConfig cfg = load_config("/tmp/_vanguard_nonexistent_.conf");
        assert(cfg.port == 8080);
        assert(cfg.max_connections == 64);
        assert(cfg.recv_timeout == 5);
        assert(cfg.log_path == "server_log.txt");
        assert(cfg.ban_threshold == 5);
        assert(cfg.time_window == 60);
        assert(cfg.whitelist_path == "whitelist.conf");
    }
    PASS()

    // ── Test 2: Parse custom values ─────────────────────────
    TEST("custom values")
    {
        write_temp("/tmp/_vanguard_test2_.conf",
            "port = 9090\n"
            "max_connections = 128\n"
            "recv_timeout = 10\n"
            "log_path = /var/log/vanguard.txt\n"
            "ban_threshold = 10\n"
            "time_window = 30\n"
            "whitelist = /etc/whitelist.conf\n"
        );
        VanguardConfig cfg = load_config("/tmp/_vanguard_test2_.conf");
        assert(cfg.port == 9090);
        assert(cfg.max_connections == 128);
        assert(cfg.recv_timeout == 10);
        assert(cfg.log_path == "/var/log/vanguard.txt");
        assert(cfg.ban_threshold == 10);
        assert(cfg.time_window == 30);
        assert(cfg.whitelist_path == "/etc/whitelist.conf");
        std::remove("/tmp/_vanguard_test2_.conf");
    }
    PASS()

    // ── Test 3: Comments and empty lines are skipped ────────
    TEST("comments and empty lines")
    {
        write_temp("/tmp/_vanguard_test3_.conf",
            "# This is a comment\n"
            "\n"
            "port = 3000\n"
            "# another comment\n"
            "\n"
            "max_connections = 32\n"
        );
        VanguardConfig cfg = load_config("/tmp/_vanguard_test3_.conf");
        assert(cfg.port == 3000);
        assert(cfg.max_connections == 32);
        assert(cfg.ban_threshold == 5);  // ไม่ได้ตั้ง ต้องเป็น default
        std::remove("/tmp/_vanguard_test3_.conf");
    }
    PASS()

    // ── Test 4: Invalid values don't crash ──────────────────
    TEST("invalid values handled gracefully")
    {
        write_temp("/tmp/_vanguard_test4_.conf",
            "port = not_a_number\n"
            "max_connections = 64\n"
            "ban_threshold = abc\n"
        );
        // ต้องไม่ crash — ค่าที่ผิดจะถูกข้าม ใช้ default แทน
        VanguardConfig cfg = load_config("/tmp/_vanguard_test4_.conf");
        assert(cfg.port == 8080);            // default (parse failed)
        assert(cfg.max_connections == 64);    // parsed OK
        assert(cfg.ban_threshold == 5);       // default (parse failed)
        std::remove("/tmp/_vanguard_test4_.conf");
    }
    PASS()

    // ── Test 5: Whitespace handling ─────────────────────────
    TEST("whitespace around key/value")
    {
        write_temp("/tmp/_vanguard_test5_.conf",
            "  port   =   4000  \n"
            "  max_connections=16\n"
        );
        VanguardConfig cfg = load_config("/tmp/_vanguard_test5_.conf");
        assert(cfg.port == 4000);
        assert(cfg.max_connections == 16);
        std::remove("/tmp/_vanguard_test5_.conf");
    }
    PASS()

    // ── Test 6: Partial config (only some keys) ─────────────
    TEST("partial config uses defaults for missing keys")
    {
        write_temp("/tmp/_vanguard_test6_.conf",
            "port = 5000\n"
        );
        VanguardConfig cfg = load_config("/tmp/_vanguard_test6_.conf");
        assert(cfg.port == 5000);
        assert(cfg.max_connections == 64);  // default
        assert(cfg.recv_timeout == 5);      // default
        assert(cfg.ban_threshold == 5);     // default
        std::remove("/tmp/_vanguard_test6_.conf");
    }
    PASS()

    // ── Test 7: Empty file ──────────────────────────────────
    TEST("empty file returns all defaults")
    {
        write_temp("/tmp/_vanguard_test7_.conf", "");
        VanguardConfig cfg = load_config("/tmp/_vanguard_test7_.conf");
        assert(cfg.port == 8080);
        assert(cfg.ban_threshold == 5);
        std::remove("/tmp/_vanguard_test7_.conf");
    }
    PASS()

    std::cout << "\n\033[1;32m✓ All config parser tests passed!\033[0m\n" << std::endl;
    return 0;
}
