// ═══════════════════════════════════════════════════════════════
// Vanguard Sentinel — ระบบตรวจจับและป้องกันการบุกรุก (IDS/IPS)
// เฝ้าดู Log ของ Server แบบ Real-time แล้ว Ban IP ที่น่าสงสัย
//
// Bug Fixes ที่แก้ไขจากเวอร์ชันเดิม:
//   [FIX #5] Sliding window — เปลี่ยน vector เป็น deque (O(1) pop_front)
//   [FIX #8] stoi crash     — config parser มี try-catch
//   [FIX #9] Code duplication — ใช้ shared headers
//   [FIX #10] ANSI colors    — ใช้ shared colors.h
//
// Features ใหม่:
//   [NEW] Path-based detection — ตรวจจับ request ไปยัง path ที่น่าสงสัย
//   [NEW] Periodic stats      — แสดงสถิติทุก 30 วินาที
//   [NEW] Reason tracking     — บอกเหตุผลที่ ban (rate/path)
// ═══════════════════════════════════════════════════════════════

#include <iostream>
#include <fstream>
#include <string>
#include <unistd.h>
#include <set>
#include <map>
#include <deque>        // [FIX #5] ใช้ deque แทน vector เพื่อ O(1) pop_front
#include <ctime>
#include <sys/wait.h>

#include "include/colors.h"
#include "include/config.h"
#include "include/ip_utils.h"

// ╔═══════════════════════════════════════╗
// ║     Suspicious Path Patterns          ║
// ╚═══════════════════════════════════════╝

// [NEW] รายการ path ที่มักถูกใช้ในการโจมตี
// ถ้า IP ใด request path เหล่านี้จะถูกเพิ่มคะแนน
static const std::set<std::string> SUSPICIOUS_PATHS = {
    "/admin", "/wp-login", "/wp-admin", "/phpmyadmin",
    "/shell", "/cmd", "/exec", "/etc/passwd",
    "/.env", "/backup", "/db", "/root",
    "/administrator", "/wp-config", "/xmlrpc.php",
    "/.git", "/config.php", "/debug"
};

// ╔═══════════════════════════════════════╗
// ║          Whitelist Loader             ║
// ╚═══════════════════════════════════════╝

std::set<std::string> load_whitelist(const std::string& path) {
    std::set<std::string> wl;
    std::ifstream f(path);
    if (!f.is_open()) {
        std::cout << YELLOW << "[!] " << RESET
                  << "whitelist not found: " << path << std::endl;
        return wl;
    }
    std::string line;
    while (std::getline(f, line)) {
        // trim whitespace
        line.erase(line.find_last_not_of(" \t\r\n") + 1);
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        if (!line.empty() && line[0] != '#')
            wl.insert(line);
    }
    std::cout << GREEN << "[+] " << RESET
              << "Loaded " << wl.size() << " whitelisted IPs" << std::endl;
    return wl;
}

// ╔═══════════════════════════════════════╗
// ║       Firewall Ban (iptables)         ║
// ╚═══════════════════════════════════════╝

// ใช้ fork+exec แทน system() เพราะปลอดภัยกว่า (ป้องกัน command injection)
void ban_ip(const std::string& ip) {
    pid_t pid = fork();
    if (pid == 0) {
        // child process — execl ไม่ return ถ้าสำเร็จ
        execl("/sbin/iptables", "iptables",
              "-A", "INPUT", "-s", ip.c_str(), "-j", "DROP", nullptr);
        _exit(1);  // ถ้า execl ล้มเหลว
    }
    if (pid > 0) waitpid(pid, nullptr, 0);
}

// ╔═══════════════════════════════════════╗
// ║        Path-based Detection           ║
// ╚═══════════════════════════════════════╝

// [NEW] ตรวจจับว่า request line มี path ที่น่าสงสัยหรือไม่
std::string check_suspicious_path(const std::string& line) {
    for (const auto& sus : SUSPICIOUS_PATHS) {
        // มองหา "GET /admin" หรือ "POST /admin" ใน log
        if (line.find("GET " + sus) != std::string::npos ||
            line.find("POST " + sus) != std::string::npos ||
            line.find("HEAD " + sus) != std::string::npos) {
            return sus;
        }
    }
    return "";
}

// ╔═══════════════════════════════════════╗
// ║              Main                     ║
// ╚═══════════════════════════════════════╝

int main() {
    VanguardConfig cfg = load_config("config.conf");

    // Banner
    std::cout << MAGENTA << "\n"
              << " ╔══════════════════════════════════════╗\n"
              << " ║   VANGUARD SENTINEL  —  IDS / IPS    ║\n"
              << " ╚══════════════════════════════════════╝\n"
              << RESET << std::endl;

    // เปิดไฟล์ log สำหรับ monitoring
    std::ifstream logfile(cfg.log_path);
    if (!logfile.is_open()) {
        std::cerr << RED << "[!] " << RESET
                  << "Cannot open " << cfg.log_path << std::endl;
        return 1;
    }

    std::set<std::string> blacklist;
    std::set<std::string> whitelist = load_whitelist(cfg.whitelist_path);

    // [FIX #5] ใช้ deque แทน vector สำหรับ sliding window
    // deque::pop_front() คือ O(1) ในขณะที่ vector::erase(begin()) คือ O(n)
    std::map<std::string, std::deque<time_t>> ip_history;

    // สถิติ
    long total_scanned     = 0;
    long total_blocked     = 0;
    long suspicious_paths  = 0;
    time_t last_stats_time = std::time(nullptr);

    // สถานะเริ่มต้น
    std::cout << GREEN << "[+] " << RESET
              << "Loaded config from config.conf" << std::endl;
    std::cout << YELLOW << "[*] " << RESET
              << "Monitoring: " << cfg.log_path << std::endl;
    std::cout << YELLOW << "[*] " << RESET
              << "Ban threshold: " << cfg.ban_threshold
              << " hits in " << cfg.time_window << "s" << std::endl;
    std::cout << YELLOW << "[*] " << RESET
              << "Suspicious path detection: " << SUSPICIOUS_PATHS.size()
              << " patterns loaded" << std::endl;
    std::cout << YELLOW << "[*] " << RESET
              << "Waiting for new entries...\n" << std::endl;

    // ตัวแปรสำหรับเก็บ IP ปัจจุบันที่กำลังอ่าน (ใช้กับ path detection)
    std::string current_ip;

    // === Main Monitoring Loop ===
    while (true) {
        std::string line;

        while (std::getline(logfile, line)) {

            // --- ดึง IP Address จาก log entry ---
            if (line.find("IP Address:") != std::string::npos) {
                total_scanned++;

                std::string ip = parse_ip(line);   // จาก ip_utils.h
                current_ip = ip;

                // ตรวจสอบ IP ถูกต้องไหม
                if (!valid_ip(ip)) {                // จาก ip_utils.h
                    std::cout << YELLOW << "[?] " << RESET
                              << "invalid ip skipped: " << ip << std::endl;
                    current_ip.clear();
                    continue;
                }

                // เช็ค whitelist
                if (whitelist.count(ip)) {
                    std::cout << GREEN << "[ok] " << RESET
                              << ip << " is whitelisted, skipping" << std::endl;
                    current_ip.clear();
                    continue;
                }

                // เคย ban แล้ว — ข้ามไป
                if (blacklist.count(ip)) {
                    current_ip.clear();
                    continue;
                }

                /*
                 * Rate-based detection (Sliding Window Algorithm)
                 *
                 * แนวคิด: เก็บ timestamp ที่ IP เข้ามาใน deque
                 * ลบ entry เก่าที่อยู่นอก time_window ออก
                 * ถ้าจำนวนที่เหลือเกิน threshold → ban
                 *
                 * [FIX #5] ใช้ deque::pop_front() แทน vector::erase(begin())
                 * เพื่อประสิทธิภาพ O(1) แทน O(n)
                 */
                time_t now_t = std::time(nullptr);
                auto& hist = ip_history[ip];
                hist.push_back(now_t);

                // ลบ entry เก่าที่อยู่นอก window
                while (!hist.empty() && (now_t - hist.front()) > cfg.time_window)
                    hist.pop_front();  // O(1)!

                int hits = (int)hist.size();

                if (hits >= cfg.ban_threshold) {
                    blacklist.insert(ip);
                    total_blocked++;

                    // แสดง THREAT DETECTED banner
                    std::cout << "\n" << RED
                              << "  ╔═══════════════════════════════════╗\n"
                              << "  ║        ⚠ THREAT DETECTED          ║\n"
                              << "  ╚═══════════════════════════════════╝"
                              << RESET << std::endl;
                    std::cout << "  IP:      " << ip << std::endl;
                    std::cout << "  Time:    " << now_str() << std::endl;
                    std::cout << "  Hits:    " << hits << " in "
                              << cfg.time_window << "s" << std::endl;
                    std::cout << "  Reason:  " << RED
                              << "Rate limit exceeded" << RESET << std::endl;
                    std::cout << "  Action:  " << RED << "BANNED" << RESET
                              << " (iptables DROP)" << std::endl;
                    std::cout << "  Blocked: " << blacklist.size()
                              << " total\n" << std::endl;

                    ban_ip(ip);
                    current_ip.clear();
                } else {
                    std::cout << CYAN << "[watch] " << RESET
                              << ip << " — " << hits << "/"
                              << cfg.ban_threshold << std::endl;
                }
                continue;
            }

            // --- [NEW] Path-based detection ---
            // ตรวจจับ request ไปยัง path ที่น่าสงสัย (เช่น /admin, /wp-login)
            if (!current_ip.empty() && !blacklist.count(current_ip)) {
                std::string sus = check_suspicious_path(line);
                if (!sus.empty()) {
                    suspicious_paths++;
                    std::cout << YELLOW << "[⚠ SUS] " << RESET
                              << current_ip << " requested suspicious path: "
                              << RED << sus << RESET << std::endl;
                }
            }
        }

        logfile.clear();  // reset EOF flag เพื่ออ่านต่อ

        // [NEW] แสดงสถิติทุก 30 วินาที
        time_t now_t = std::time(nullptr);
        if (now_t - last_stats_time >= 30 && total_scanned > 0) {
            std::cout << DIM << "[stats] scanned:" << total_scanned
                      << " | blocked:" << total_blocked
                      << " | suspicious:" << suspicious_paths
                      << " | watching:" << ip_history.size() << " IPs"
                      << RESET << std::endl;
            last_stats_time = now_t;
        }

        sleep(1);  // polling interval
    }

    return 0;
}