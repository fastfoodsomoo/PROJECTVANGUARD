#include <iostream>
#include <fstream>
#include <string>
#include <unistd.h>
#include <set>
#include <map>
#include <vector>
#include <regex>
#include <ctime>
#include <sys/wait.h>

// === Config ===
static int         BAN_THRESHOLD = 5;
static int         TIME_WINDOW   = 60;
static std::string LOG_PATH      = "server_log.txt";
static std::string WL_PATH       = "whitelist.conf";

#define GREEN   "\033[1;32m"
#define CYAN    "\033[1;36m"
#define YELLOW  "\033[1;33m"
#define RED     "\033[1;31m"
#define MAGENTA "\033[1;35m"
#define RESET   "\033[0m"

static long total_scanned = 0;
static long total_blocked = 0;

// --- Whitelist ---
std::set<std::string> load_whitelist(const std::string& path) {
    std::set<std::string> wl;
    std::ifstream f(path);
    if (!f.is_open()) {
        std::cout << YELLOW << "[!] " << RESET << "whitelist not found: " << path << std::endl;
        return wl;
    }
    std::string line;
    while (std::getline(f, line)) {
        line.erase(line.find_last_not_of(" \t\r\n") + 1);
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        if (!line.empty() && line[0] != '#')
            wl.insert(line);
    }
    std::cout << GREEN << "[+] " << RESET
              << "Loaded " << wl.size() << " whitelisted IPs" << std::endl;
    return wl;
}

void load_config(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open()) return;

    std::string line;
    while (std::getline(f, line)) {
        if (line.empty() || line[0] == '#') continue;
        size_t eq = line.find('=');
        if (eq == std::string::npos) continue;

        std::string key = line.substr(0, eq);
        std::string val = line.substr(eq + 1);
        key.erase(key.find_last_not_of(" \t") + 1);
        key.erase(0, key.find_first_not_of(" \t"));
        val.erase(val.find_last_not_of(" \t") + 1);
        val.erase(0, val.find_first_not_of(" \t"));

        if      (key == "ban_threshold") BAN_THRESHOLD = std::stoi(val);
        else if (key == "time_window")   TIME_WINDOW   = std::stoi(val);
        else if (key == "log_path")      LOG_PATH      = val;
        else if (key == "whitelist")     WL_PATH       = val;
    }
}

// validate ip address (เช็คทั้ง format และ range 0-255)
bool valid_ip(const std::string& ip) {
    std::regex pat(R"(^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$)");
    std::smatch m;
    if (!std::regex_match(ip, m, pat)) return false;

    for (int i = 1; i <= 4; i++) {
        int octet = std::stoi(m[i].str());
        if (octet < 0 || octet > 255) return false;
    }
    return true;
}

// ดึง ip จากบรรทัด log (ใช้ find แทน hardcode offset เผื่อ format เปลี่ยน)
std::string parse_ip(const std::string& line) {
    std::string tag = "IP Address:";
    size_t pos = line.find(tag);
    if (pos == std::string::npos) return "";

    std::string ip = line.substr(pos + tag.length());
    ip.erase(ip.find_last_not_of(" \t\r\n") + 1);
    ip.erase(0, ip.find_first_not_of(" \t\r\n"));
    return ip;
}

// ban ip ผ่าน iptables
// ใช้ fork+exec แทน system() เพราะปลอดภัยกว่า (ป้องกัน command injection)
void ban_ip(const std::string& ip) {
    pid_t pid = fork();
    if (pid == 0) {
        execl("/sbin/iptables", "iptables",
              "-A", "INPUT", "-s", ip.c_str(), "-j", "DROP", nullptr);
        _exit(1);
    }
    if (pid > 0) waitpid(pid, nullptr, 0);
}

std::string now_str() {
    auto t = std::time(nullptr);
    char buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&t));
    return buf;
}

int main() {
    load_config("config.conf");

    std::cout << MAGENTA << "\n"
              << " ╔══════════════════════════════════════╗\n"
              << " ║   VANGUARD SENTINEL  —  IDS / IPS    ║\n"
              << " ╚══════════════════════════════════════╝\n"
              << RESET << std::endl;

    std::ifstream logfile(LOG_PATH);
    if (!logfile.is_open()) {
        std::cerr << RED << "[!] " << RESET << "Cannot open " << LOG_PATH << std::endl;
        return 1;
    }

    std::set<std::string> blacklist;
    std::set<std::string> whitelist = load_whitelist(WL_PATH);

    // เก็บ timestamp ของแต่ละ ip สำหรับทำ rate-based detection
    std::map<std::string, std::vector<time_t>> ip_history;

    std::cout << YELLOW << "[*] " << RESET << "Monitoring: " << LOG_PATH << std::endl;
    std::cout << YELLOW << "[*] " << RESET
              << "Ban threshold: " << BAN_THRESHOLD
              << " hits in " << TIME_WINDOW << "s" << std::endl;
    std::cout << YELLOW << "[*] " << RESET << "Waiting for new entries...\n" << std::endl;

    while (true) {
        std::string line;

        while (std::getline(logfile, line)) {
            if (line.find("IP Address:") == std::string::npos) continue;
            total_scanned++;

            std::string ip = parse_ip(line);

            if (!valid_ip(ip)) {
                std::cout << YELLOW << "[?] " << RESET
                          << "invalid ip skipped: " << ip << std::endl;
                continue;
            }

            if (whitelist.count(ip)) {
                std::cout << GREEN << "[ok] " << RESET
                          << ip << " is whitelisted, skipping" << std::endl;
                continue;
            }

            if (blacklist.count(ip)) continue; // เคย ban แล้ว

            /*
             * Rate-based detection
             * แนวคิด: เก็บเวลาที่ ip เข้ามาใน sliding window
             * ถ้าจำนวนครั้งเกิน threshold ภายใน time_window -> ban
             * วิธีนี้ user ปกติไม่โดน ban เพราะไม่ได้เข้าถี่ขนาดนั้น
             */
            time_t now = std::time(nullptr);
            auto& hist = ip_history[ip];
            hist.push_back(now);

            // ลบ entry ที่เก่ากว่า time_window ออก
            while (!hist.empty() && (now - hist.front()) > TIME_WINDOW)
                hist.erase(hist.begin());

            int hits = (int)hist.size();

            if (hits >= BAN_THRESHOLD) {
                blacklist.insert(ip);
                total_blocked++;

                std::cout << "\n" << RED
                          << "  ╔═══════════════════════════════════╗\n"
                          << "  ║        ⚠ THREAT DETECTED          ║\n"
                          << "  ╚═══════════════════════════════════╝" << RESET << std::endl;
                std::cout << "  IP:      " << ip << std::endl;
                std::cout << "  Time:    " << now_str() << std::endl;
                std::cout << "  Hits:    " << hits << " in " << TIME_WINDOW << "s" << std::endl;
                std::cout << "  Action:  " << RED << "BANNED" << RESET
                          << " (iptables DROP)" << std::endl;
                std::cout << "  Blocked: " << blacklist.size() << " total\n" << std::endl;

                ban_ip(ip);
            } else {
                std::cout << CYAN << "[watch] " << RESET
                          << ip << " — " << hits << "/" << BAN_THRESHOLD << std::endl;
            }
        }

        logfile.clear();
        sleep(1);
    }

    return 0;
}