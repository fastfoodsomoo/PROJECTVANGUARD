#pragma once
// ═══════════════════════════════════════════════════════════════
// Vanguard — IP Address Utilities
// ฟังก์ชันสำหรับตรวจสอบและดึง IP จาก log
// แยกออกมาเพื่อใช้ร่วมกันและทดสอบด้วย unit test ได้
// ═══════════════════════════════════════════════════════════════

#include <string>
#include <regex>

// === IP Validation ===
// ตรวจสอบว่า string เป็น IPv4 address ที่ถูกต้องหรือไม่
// เช็คทั้ง format (x.x.x.x) และ range (0-255) ทุก octet
inline bool valid_ip(const std::string& ip) {
    static const std::regex pat(R"(^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$)");
    std::smatch m;
    if (!std::regex_match(ip, m, pat)) return false;

    for (int i = 1; i <= 4; i++) {
        int octet = std::stoi(m[i].str());
        if (octet < 0 || octet > 255) return false;
    }
    return true;
}

// === IP Parser ===
// ดึง IP address จากบรรทัด log ที่มี "IP Address: x.x.x.x"
// ใช้ find แทน hardcode offset เผื่อ format เปลี่ยน
inline std::string parse_ip(const std::string& line) {
    const std::string tag = "IP Address:";
    size_t pos = line.find(tag);
    if (pos == std::string::npos) return "";

    std::string ip = line.substr(pos + tag.length());
    // trim whitespace รอบ IP
    ip.erase(ip.find_last_not_of(" \t\r\n") + 1);
    ip.erase(0, ip.find_first_not_of(" \t\r\n"));
    return ip;
}
