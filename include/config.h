#pragma once
// ═══════════════════════════════════════════════════════════════
// Vanguard — Shared Configuration Parser
// ใช้ร่วมกันระหว่าง server.cpp และ sentinel.cpp
// รวม config ทั้งหมดไว้ใน struct เดียว + มี error handling
// ═══════════════════════════════════════════════════════════════

#include <string>
#include <fstream>
#include <iostream>
#include <ctime>

// === Config Struct ===
// เก็บค่า config ทั้งหมดใน struct เดียว แทนที่จะเป็น global variables กระจาย
struct VanguardConfig {
    // Server settings
    int         port            = 8080;
    int         max_connections = 64;
    int         recv_timeout    = 5;
    std::string log_path        = "server_log.txt";

    // Sentinel settings
    int         ban_threshold   = 5;
    int         time_window     = 60;
    std::string whitelist_path  = "whitelist.conf";
};

// === Config Parser ===
// อ่าน config.conf แล้วคืน struct พร้อมใช้งาน
// ถ้าไฟล์ไม่มี หรือค่าไม่ถูกต้อง จะใช้ค่า default แทน (ไม่ crash)
inline VanguardConfig load_config(const std::string& path) {
    VanguardConfig cfg;
    std::ifstream f(path);
    if (!f.is_open()) return cfg;

    std::string line;
    while (std::getline(f, line)) {
        // ข้ามบรรทัดว่างและ comment
        if (line.empty() || line[0] == '#') continue;

        size_t eq = line.find('=');
        if (eq == std::string::npos) continue;

        // แยก key = value แล้ว trim whitespace
        std::string key = line.substr(0, eq);
        std::string val = line.substr(eq + 1);
        key.erase(key.find_last_not_of(" \t") + 1);
        key.erase(0, key.find_first_not_of(" \t"));
        val.erase(val.find_last_not_of(" \t") + 1);
        val.erase(0, val.find_first_not_of(" \t"));

        // ใช้ try-catch ป้องกัน crash จากค่าที่ไม่ใช่ตัวเลข
        try {
            if      (key == "port")            cfg.port            = std::stoi(val);
            else if (key == "max_connections") cfg.max_connections = std::stoi(val);
            else if (key == "recv_timeout")    cfg.recv_timeout    = std::stoi(val);
            else if (key == "log_path")        cfg.log_path        = val;
            else if (key == "ban_threshold")   cfg.ban_threshold   = std::stoi(val);
            else if (key == "time_window")     cfg.time_window     = std::stoi(val);
            else if (key == "whitelist")       cfg.whitelist_path  = val;
        } catch (const std::exception& e) {
            std::cerr << "[!] Invalid config value for '" << key
                      << "': " << val << " (" << e.what() << ")" << std::endl;
        }
    }
    return cfg;
}

// === Time Utility ===
// คืนเวลาปัจจุบันเป็น string "YYYY-MM-DD HH:MM:SS"
// ใช้ร่วมกันทั้ง server และ sentinel
inline std::string now_str() {
    auto t = std::time(nullptr);
    char buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&t));
    return buf;
}
