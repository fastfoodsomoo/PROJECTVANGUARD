#pragma once
// ═══════════════════════════════════════════════════════════════
// Vanguard — Thread-Safe Logger
// ใช้ std::mutex ป้องกัน Race Condition เมื่อ Thread หลายตัว
// เขียน Log พร้อมกัน (แก้ปัญหาที่พบในเวอร์ชันเดิม)
// ═══════════════════════════════════════════════════════════════

#include <string>
#include <fstream>
#include <mutex>

class Logger {
    std::mutex  mtx_;       // ล็อกเพื่อป้องกัน concurrent writes
    std::string filepath_;  // path ไปยังไฟล์ log

public:
    explicit Logger(const std::string& path) : filepath_(path) {}

    // === Thread-Safe Log Entry ===
    // ใช้ lock_guard เพื่อให้แน่ใจว่ามีแค่ thread เดียวที่เขียน log ในเวลาเดียวกัน
    // ป้องกัน log entries สลับกัน (interleave) เมื่อมี request พร้อมกัน
    void log(const std::string& timestamp, const std::string& ip,
             const std::string& request_data) {
        std::lock_guard<std::mutex> lock(mtx_);
        std::ofstream f(filepath_, std::ios::app);
        if (f.is_open()) {
            f << "========== LOG ENTRY ==========\n"
              << "Time: " << timestamp << "\n"
              << "IP Address: " << ip << "\n"
              << "Request Data :\n" << request_data << "\n";
        }
    }
};
