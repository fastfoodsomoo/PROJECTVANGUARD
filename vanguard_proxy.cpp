// ═══════════════════════════════════════════════════════════════════════
// Vanguard Edge Proxy — Cloudflare-like In-line WAF Engine
// เขียนด้วย C++17 บน Linux epoll ตั้งแต่ต้น
//
// Architecture:
//   [Client] → (Port 8080) → [vanguard_proxy] → (Port 3000) → [my_server]
//
// Features:
//   • epoll(7) non-blocking accept loop (O_NONBLOCK + EPOLLIN)
//   • Zero-copy HTTP parsing ด้วย std::string_view
//   • Token Bucket rate limiter (per-IP, in-memory)
//   • WAF inspection: SQLi + XSS pattern detection
//   • Reverse proxy forwarding พร้อม header injection
//   • Custom block pages (429 / 403) แบบ dark theme
//   • Server header override: Vanguard-Edge-Engine/1.0
//
// by Sattaya — Project Vanguard v2
// ═══════════════════════════════════════════════════════════════════════

#include <sys/socket.h>
#include <sys/epoll.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>
#include <chrono>
#include <fstream>
#include <sstream>
#include <random>
#include <csignal>
#include <cstring>
#include <algorithm>
#include <functional>

#include "include/colors.h"

// ╔═══════════════════════════════════════════════════════════╗
// ║              Configuration Constants                      ║
// ╚═══════════════════════════════════════════════════════════╝

static constexpr int         PROXY_PORT     = 8080;
static constexpr const char* BACKEND_HOST   = "127.0.0.1";
static constexpr int         BACKEND_PORT   = 3000;
static constexpr int         MAX_EVENTS     = 256;
static constexpr int         BUFFER_SIZE    = 16384;
static constexpr double      RATE_TOKENS_S  = 10.0;    // refill rate (tokens/sec)
static constexpr double      RATE_BURST     = 10.0;    // max bucket capacity
static constexpr const char* WHITELIST_FILE = "whitelist.conf";

// ╔═══════════════════════════════════════════════════════════╗
// ║              Global State                                 ║
// ╚═══════════════════════════════════════════════════════════╝

static std::unordered_set<std::string> g_whitelist;
static std::atomic<bool>  g_running{true};
static std::atomic<long>  g_total_requests{0};
static std::atomic<long>  g_blocked_rate{0};
static std::atomic<long>  g_blocked_waf{0};
static std::atomic<long>  g_forwarded{0};
static int                g_listen_fd = -1;
static std::chrono::steady_clock::time_point g_start_time;

// ╔═══════════════════════════════════════════════════════════╗
// ║       Token Bucket Rate Limiter (per-IP, in-memory)       ║
// ╚═══════════════════════════════════════════════════════════╝
//
// แนวคิด: แต่ละ IP มี "ถังเหรียญ" (Token Bucket)
//   - ถังเติมเหรียญ RATE_TOKENS_S เหรียญต่อวินาที
//   - ถังจุได้สูงสุด RATE_BURST เหรียญ
//   - ทุก request ใช้ 1 เหรียญ, ถ้าหมด → 429
//   - Whitelisted IP ข้ามการเช็ค rate limit

struct TokenBucket {
    double tokens;
    std::chrono::steady_clock::time_point last_refill;

    TokenBucket()
        : tokens(RATE_BURST)
        , last_refill(std::chrono::steady_clock::now()) {}
};

static std::unordered_map<std::string, TokenBucket> g_buckets;
static std::mutex g_bucket_mutex;

// คืน true = อนุญาต, false = rate limited
bool rate_limit_allow(const std::string& ip) {
    std::lock_guard<std::mutex> lock(g_bucket_mutex);
    auto now = std::chrono::steady_clock::now();
    auto& bucket = g_buckets[ip];

    // เติมเหรียญตามเวลาที่ผ่านไป
    double elapsed = std::chrono::duration<double>(now - bucket.last_refill).count();
    bucket.tokens = std::min(RATE_BURST, bucket.tokens + elapsed * RATE_TOKENS_S);
    bucket.last_refill = now;

    if (bucket.tokens >= 1.0) {
        bucket.tokens -= 1.0;
        return true;   // ยังมีเหรียญ → อนุญาต
    }
    return false;      // หมดเหรียญ → บล็อก
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       Ray ID Generator (Cloudflare-style)                 ║
// ╚═══════════════════════════════════════════════════════════╝

std::string generate_ray_id() {
    static thread_local std::mt19937_64 rng(
        std::chrono::steady_clock::now().time_since_epoch().count() ^
        std::hash<std::thread::id>{}(std::this_thread::get_id()));

    uint64_t val = rng();
    char buf[17];
    snprintf(buf, sizeof(buf), "%016lx", val);
    return std::string(buf);
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       WAF Inspection Engine (SQLi + XSS)                  ║
// ╚═══════════════════════════════════════════════════════════╝
//
// ตรวจสอบ URI และ body ด้วย pattern matching แบบ case-insensitive
// ใช้ std::string_view เป็น input เพื่อ zero-copy

enum class WafVerdict { SAFE, SQLI_DETECTED, XSS_DETECTED };

WafVerdict inspect_waf(std::string_view uri, std::string_view body) {
    // สร้าง lowercase copy สำหรับ case-insensitive matching
    auto to_lower = [](std::string_view sv) {
        std::string s(sv);
        std::transform(s.begin(), s.end(), s.begin(),
                       [](unsigned char c) { return std::tolower(c); });
        return s;
    };

    std::string l_uri  = to_lower(uri);
    std::string l_body = to_lower(body);

    // --- SQLi Signatures ---
    static const char* sqli_patterns[] = {
        "union select",     "union%20select",
        "' or '1'='1",      "'%20or%20'1'%3d'1",
        "or 1=1",           "or%201%3d1",
        "drop table",       "drop%20table",
        "; select",         ";%20select",
        "'; drop",          "1=1--",
        "' or ''='",        "select * from",
        "insert into",      "delete from",
        "exec(",            "execute(",
        "' or 'x'='x",     "benchmark(",
        "sleep(",           "waitfor delay",
    };

    // --- XSS Signatures ---
    static const char* xss_patterns[] = {
        "<script",          "%3cscript",
        "javascript:",      "javascript%3a",
        "onerror=",         "onload=",
        "onclick=",         "onmouseover=",
        "onfocus=",         "onblur=",
        "alert(",           "document.cookie",
        "eval(",            "<iframe",
        "%3ciframe",        "expression(",
        "prompt(",          "confirm(",
    };

    auto contains = [](const std::string& haystack, const char* needle) {
        return haystack.find(needle) != std::string::npos;
    };

    for (const auto& pat : sqli_patterns) {
        if (contains(l_uri, pat) || contains(l_body, pat))
            return WafVerdict::SQLI_DETECTED;
    }

    for (const auto& pat : xss_patterns) {
        if (contains(l_uri, pat) || contains(l_body, pat))
            return WafVerdict::XSS_DETECTED;
    }

    return WafVerdict::SAFE;
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       Whitelist Loader                                    ║
// ╚═══════════════════════════════════════════════════════════╝

std::unordered_set<std::string> load_whitelist(const char* path) {
    std::unordered_set<std::string> wl;
    std::ifstream f(path);
    if (!f.is_open()) {
        std::cout << YELLOW << "[!] " << RESET
                  << "Whitelist file not found: " << path << std::endl;
        return wl;
    }
    std::string line;
    while (std::getline(f, line)) {
        line.erase(line.find_last_not_of(" \t\r\n") + 1);
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        if (!line.empty() && line[0] != '#')
            wl.insert(line);
    }
    return wl;
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       Custom Block Pages (dark theme HTML)                ║
// ╚═══════════════════════════════════════════════════════════╝

// สร้างหน้า block page พร้อม CSS animation แบบ Cloudflare
std::string make_block_page(int code, const std::string& title,
                             const std::string& emoji,
                             const std::string& heading,
                             const std::string& message,
                             const std::string& detail,
                             const std::string& ray_id) {
    std::ostringstream html;
    html << "<!DOCTYPE html><html lang=\"en\">"
         << "<head><meta charset=\"UTF-8\">"
         << "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\">"
         << "<title>" << title << "</title>"
         << "<style>"
         << "*{margin:0;padding:0;box-sizing:border-box}"
         << "body{"
         <<   "background:linear-gradient(135deg,#0d1117 0%,#161b22 50%,#0d1117 100%);"
         <<   "color:#e6edf3;"
         <<   "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;"
         <<   "min-height:100vh;display:flex;align-items:center;justify-content:center"
         << "}"
         << ".container{"
         <<   "text-align:center;padding:3rem;"
         <<   "background:rgba(22,27,34,0.8);"
         <<   "border:1px solid #30363d;border-radius:12px;"
         <<   "backdrop-filter:blur(10px);"
         <<   "box-shadow:0 8px 32px rgba(0,0,0,0.3);"
         <<   "max-width:560px;width:90%;"
         <<   "animation:fadeIn .6s ease-out"
         << "}"
         << "@keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}"
         << ".logo{font-size:3.5rem;margin-bottom:.5rem}"
         << "h1{"
         <<   "font-size:1.8rem;"
         <<   "background:linear-gradient(135deg,#f85149,#da3633);"
         <<   "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
         <<   "background-clip:text;margin-bottom:.5rem"
         << "}"
         << ".message{color:#8b949e;font-size:1rem;margin-bottom:1.5rem;line-height:1.6}"
         << ".status{"
         <<   "display:inline-block;padding:.35rem 1rem;"
         <<   "border-radius:2rem;font-size:.85rem;font-weight:600;"
         <<   "background:rgba(248,81,73,.15);color:#f85149;border:1px solid rgba(248,81,73,.4)"
         << "}"
         << ".pulse{"
         <<   "display:inline-block;width:8px;height:8px;"
         <<   "border-radius:50%;margin-right:6px;"
         <<   "background:#f85149;animation:pulse 2s infinite"
         << "}"
         << "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}"
         << ".detail{color:#484f58;font-size:.8rem;margin-top:1rem;font-family:'SF Mono',Consolas,monospace}"
         << ".footer{"
         <<   "color:#484f58;margin-top:1.5rem;font-size:.75rem;"
         <<   "border-top:1px solid #21262d;padding-top:1rem"
         << "}"
         << "</style></head>"
         << "<body><div class=\"container\">"
         << "<div class=\"logo\">" << emoji << "</div>"
         << "<h1>" << heading << "</h1>"
         << "<p class=\"message\">" << message << "</p>"
         << "<span class=\"status\">"
         << "<span class=\"pulse\"></span>"
         << "Error " << code
         << "</span>"
         << "<p class=\"detail\">" << detail << "</p>"
         << "<p class=\"detail\">Ray ID: " << ray_id << "</p>"
         << "<p class=\"footer\">Vanguard Edge Engine v1.0 &middot; Protection by Vanguard WAF &middot; by Sattaya</p>"
         << "</div></body></html>";
    return html.str();
}

static std::string make_429_page(const std::string& ray_id) {
    return make_block_page(429, "429 Too Many Requests", "🛑",
        "RATE LIMIT EXCEEDED",
        "You are sending requests too quickly.<br>"
        "Please slow down and try again in a few seconds.",
        "Your IP has been temporarily rate-limited by Vanguard Edge Engine.",
        ray_id);
}

static std::string make_403_sqli_page(const std::string& ray_id) {
    return make_block_page(403, "403 Forbidden &mdash; WAF Block", "🛡️",
        "REQUEST BLOCKED &mdash; SQL INJECTION",
        "Your request was blocked because it contained a pattern<br>"
        "matching a known SQL Injection attack signature.",
        "Incident logged. Repeated violations may result in a permanent ban.",
        ray_id);
}

static std::string make_403_xss_page(const std::string& ray_id) {
    return make_block_page(403, "403 Forbidden &mdash; WAF Block", "⚠️",
        "REQUEST BLOCKED &mdash; XSS DETECTED",
        "Your request was blocked because it contained a pattern<br>"
        "matching a known Cross-Site Scripting (XSS) attack signature.",
        "Incident logged. Repeated violations may result in a permanent ban.",
        ray_id);
}

static std::string make_502_page(const std::string& ray_id,
                                  const std::string& detail) {
    return make_block_page(502, "502 Bad Gateway", "💥",
        "BACKEND UNREACHABLE",
        "The upstream server is not responding.<br>"
        "Please ensure the backend service is running.",
        detail, ray_id);
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       HTTP Response Builder                               ║
// ╚═══════════════════════════════════════════════════════════╝

std::string build_block_response(int code, const std::string& status,
                                  const std::string& body) {
    std::ostringstream resp;
    resp << "HTTP/1.1 " << code << " " << status << "\r\n"
         << "Content-Type: text/html; charset=utf-8\r\n"
         << "Content-Length: " << body.size() << "\r\n"
         << "Server: Vanguard-Edge-Engine/1.0\r\n"
         << "X-Vanguard-WAF: active\r\n"
         << "Connection: close\r\n\r\n"
         << body;
    return resp.str();
}

// ╔═══════════════════════════════════════════════════════════╗
// ║   Zero-Copy HTTP Request Parser (std::string_view)        ║
// ╚═══════════════════════════════════════════════════════════╝
//
// แยก request ออกเป็น method / uri / headers / body
// โดยไม่ copy ข้อมูล — ใช้ string_view ชี้กลับไปที่ buffer เดิม

struct ParsedRequest {
    std::string_view method;
    std::string_view uri;
    std::string_view version;
    std::string_view headers_block;
    std::string_view body;
    bool valid = false;
};

ParsedRequest parse_request(std::string_view raw) {
    ParsedRequest req;

    // หา end of request line (\r\n)
    auto line_end = raw.find("\r\n");
    if (line_end == std::string_view::npos) return req;

    std::string_view request_line = raw.substr(0, line_end);

    // แยก "METHOD URI VERSION"
    auto sp1 = request_line.find(' ');
    if (sp1 == std::string_view::npos) return req;
    req.method = request_line.substr(0, sp1);

    auto sp2 = request_line.find(' ', sp1 + 1);
    if (sp2 == std::string_view::npos) return req;
    req.uri     = request_line.substr(sp1 + 1, sp2 - sp1 - 1);
    req.version = request_line.substr(sp2 + 1);

    // แยก headers กับ body (คั่นด้วย \r\n\r\n)
    auto header_end = raw.find("\r\n\r\n");
    if (header_end != std::string_view::npos) {
        req.headers_block = raw.substr(line_end + 2, header_end - line_end - 2);
        if (header_end + 4 < raw.size())
            req.body = raw.substr(header_end + 4);
    } else {
        req.headers_block = raw.substr(line_end + 2);
    }

    req.valid = true;
    return req;
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       Backend Connection & Reverse Proxy                  ║
// ╚═══════════════════════════════════════════════════════════╝

// เชื่อมต่อไปยัง backend server (blocking connect — local เร็วมาก)
int connect_backend() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(BACKEND_PORT);
    inet_pton(AF_INET, BACKEND_HOST, &addr.sin_addr);

    // timeout กัน backend ค้าง
    struct timeval tv{3, 0};
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    if (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(fd);
        return -1;
    }
    return fd;
}

// Forward request ไปยัง backend พร้อม inject headers
// คืน raw HTTP response กลับมา (พร้อม Server header ที่ถูก override)
std::string forward_to_backend(const std::string& raw_request,
                                const std::string& client_ip,
                                const std::string& ray_id) {
    int backend_fd = connect_backend();
    if (backend_fd < 0) {
        return build_block_response(502, "Bad Gateway",
            make_502_page(ray_id, "Cannot connect to backend at "
                          + std::string(BACKEND_HOST) + ":"
                          + std::to_string(BACKEND_PORT)));
    }

    // Inject custom headers หลัง request line
    // เดิม: "GET / HTTP/1.1\r\nHost: ...\r\n..."
    // ใหม่: "GET / HTTP/1.1\r\nX-Vanguard-Connecting-IP: x\r\nX-Vanguard-Ray-ID: y\r\nHost: ...\r\n..."
    std::string modified;
    size_t first_crlf = raw_request.find("\r\n");
    if (first_crlf != std::string::npos) {
        modified  = raw_request.substr(0, first_crlf + 2);
        modified += "X-Vanguard-Connecting-IP: " + client_ip + "\r\n";
        modified += "X-Vanguard-Ray-ID: " + ray_id + "\r\n";
        modified += raw_request.substr(first_crlf + 2);
    } else {
        modified = raw_request;
    }

    // ส่ง request ไป backend
    ssize_t sent = send(backend_fd, modified.c_str(), modified.size(), 0);
    if (sent < 0) {
        close(backend_fd);
        return build_block_response(502, "Bad Gateway",
            make_502_page(ray_id, "Failed to send request to backend."));
    }

    // อ่าน response จาก backend (loop จนกว่า connection จะปิด)
    std::string response;
    char buf[BUFFER_SIZE];
    ssize_t n;
    while ((n = recv(backend_fd, buf, sizeof(buf), 0)) > 0) {
        response.append(buf, static_cast<size_t>(n));
    }
    close(backend_fd);

    if (response.empty()) {
        return build_block_response(502, "Bad Gateway",
            make_502_page(ray_id, "Backend returned an empty response."));
    }

    // Override Server header ใน response
    // หา "Server: xxx" แล้วแทนที่ด้วย "Server: Vanguard-Edge-Engine/1.0"
    std::string target_header = "Server:";
    auto pos = response.find(target_header);
    if (pos != std::string::npos) {
        auto end = response.find("\r\n", pos);
        if (end != std::string::npos) {
            response.replace(pos, end - pos,
                             "Server: Vanguard-Edge-Engine/1.0");
        }
    } else {
        // ถ้าไม่มี Server header เลย → แทรกเข้าไป
        auto first = response.find("\r\n");
        if (first != std::string::npos) {
            response.insert(first + 2,
                            "Server: Vanguard-Edge-Engine/1.0\r\n");
        }
    }

    return response;
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       Connection Handler (1 thread ต่อ 1 connection)      ║
// ╚═══════════════════════════════════════════════════════════╝

void handle_connection(int client_fd, std::string client_ip) {
    long reqnum = ++g_total_requests;
    std::string ray_id = generate_ray_id();

    // ตั้ง recv timeout
    struct timeval tv{5, 0};
    setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    // รับ request จาก client
    char buffer[BUFFER_SIZE];
    ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
    if (n <= 0) {
        close(client_fd);
        return;
    }
    buffer[n] = '\0';

    std::string raw_request(buffer, static_cast<size_t>(n));
    std::string_view raw_view(raw_request);

    // Zero-copy parse
    auto req = parse_request(raw_view);
    if (!req.valid) {
        close(client_fd);
        return;
    }

    std::cout << CYAN << "[#" << reqnum << "] " << RESET
              << GREEN << client_ip << RESET
              << " " << req.method << " " << req.uri
              << " " << DIM << "[ray:" << ray_id << "]" << RESET
              << std::endl;

    std::string response;

    // ━━━ Step 1: WAF Inspection (ทุก IP ต้องผ่าน รวม whitelist) ━━━
    WafVerdict waf = inspect_waf(req.uri, req.body);

    if (waf == WafVerdict::SQLI_DETECTED) {
        g_blocked_waf++;
        std::cout << RED << "  ✗ " << RESET
                  << "WAF BLOCK — SQL Injection detected" << std::endl;
        response = build_block_response(403, "Forbidden",
                                         make_403_sqli_page(ray_id));
        send(client_fd, response.c_str(), response.size(), 0);
        close(client_fd);
        return;
    }

    if (waf == WafVerdict::XSS_DETECTED) {
        g_blocked_waf++;
        std::cout << RED << "  ✗ " << RESET
                  << "WAF BLOCK — XSS detected" << std::endl;
        response = build_block_response(403, "Forbidden",
                                         make_403_xss_page(ray_id));
        send(client_fd, response.c_str(), response.size(), 0);
        close(client_fd);
        return;
    }

    // ━━━ Step 2: Rate Limiting (skip สำหรับ whitelisted IPs) ━━━
    if (g_whitelist.find(client_ip) == g_whitelist.end()) {
        if (!rate_limit_allow(client_ip)) {
            g_blocked_rate++;
            std::cout << YELLOW << "  ✗ " << RESET
                      << "RATE LIMITED — 429 Too Many Requests" << std::endl;
            response = build_block_response(429, "Too Many Requests",
                                             make_429_page(ray_id));
            send(client_fd, response.c_str(), response.size(), 0);
            close(client_fd);
            return;
        }
    } else {
        std::cout << DIM << "  ↳ whitelisted — bypass rate limit"
                  << RESET << std::endl;
    }

    // ━━━ Step 3: Forward to Backend ━━━
    g_forwarded++;
    std::cout << GREEN << "  ✓ " << RESET
              << "Forwarding → " << BACKEND_HOST << ":" << BACKEND_PORT
              << std::endl;

    response = forward_to_backend(raw_request, client_ip, ray_id);
    send(client_fd, response.c_str(), response.size(), 0);
    close(client_fd);
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       Signal Handler (Ctrl+C)                             ║
// ╚═══════════════════════════════════════════════════════════╝

void signal_handler(int) {
    std::cout << "\n" << YELLOW << "[*] " << RESET
              << "Shutting down Vanguard Edge Proxy... ("
              << g_total_requests.load() << " requests processed)"
              << std::endl;
    g_running.store(false);
    if (g_listen_fd != -1) {
        shutdown(g_listen_fd, SHUT_RDWR);
        close(g_listen_fd);
        g_listen_fd = -1;
    }
}

// ╔═══════════════════════════════════════════════════════════╗
// ║       Utility: Set Non-blocking Socket                    ║
// ╚═══════════════════════════════════════════════════════════╝

int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

// ╔═══════════════════════════════════════════════════════════╗
// ║              Main — epoll Event Loop                      ║
// ╚═══════════════════════════════════════════════════════════╝

int main() {
    signal(SIGINT,  signal_handler);
    signal(SIGPIPE, SIG_IGN);      // ไม่ให้ crash เมื่อ client ปิด connection กลางทาง
    g_start_time = std::chrono::steady_clock::now();

    // ── Banner ──
    std::cout << MAGENTA << "\n"
        << " ╔════════════════════════════════════════════════════════╗\n"
        << " ║   VANGUARD EDGE PROXY — Cloudflare-like WAF Engine    ║\n"
        << " ║   C++17 • epoll • Zero-Copy • In-line Filtering       ║\n"
        << " ╚════════════════════════════════════════════════════════╝\n"
        << RESET << std::endl;

    // ── Load Whitelist ──
    g_whitelist = load_whitelist(WHITELIST_FILE);
    std::cout << GREEN << "[+] " << RESET
              << "Loaded " << g_whitelist.size() << " whitelisted IPs"
              << std::endl;
    for (const auto& ip : g_whitelist) {
        std::cout << DIM << "    • " << ip << RESET << std::endl;
    }

    // ── Create Listen Socket ──
    g_listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (g_listen_fd < 0) {
        std::cerr << RED << "[!] " << RESET << "socket() failed" << std::endl;
        return 1;
    }

    int opt = 1;
    setsockopt(g_listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    if (set_nonblocking(g_listen_fd) < 0) {
        std::cerr << RED << "[!] " << RESET
                  << "fcntl(O_NONBLOCK) failed" << std::endl;
        close(g_listen_fd);
        return 1;
    }

    struct sockaddr_in addr{};
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;   // 0.0.0.0
    addr.sin_port        = htons(PROXY_PORT);

    if (bind(g_listen_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        std::cerr << RED << "[!] " << RESET
                  << "bind() failed — port " << PROXY_PORT << " in use?"
                  << std::endl;
        close(g_listen_fd);
        return 1;
    }

    if (listen(g_listen_fd, SOMAXCONN) < 0) {
        std::cerr << RED << "[!] " << RESET << "listen() failed" << std::endl;
        close(g_listen_fd);
        return 1;
    }

    // ── Create epoll Instance ──
    int epoll_fd = epoll_create1(0);
    if (epoll_fd < 0) {
        std::cerr << RED << "[!] " << RESET
                  << "epoll_create1() failed" << std::endl;
        close(g_listen_fd);
        return 1;
    }

    struct epoll_event ev{};
    ev.events  = EPOLLIN;
    ev.data.fd = g_listen_fd;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, g_listen_fd, &ev) < 0) {
        std::cerr << RED << "[!] " << RESET
                  << "epoll_ctl() failed" << std::endl;
        close(g_listen_fd);
        close(epoll_fd);
        return 1;
    }

    // ── Startup Info ──
    std::cout << GREEN << "[+] " << RESET
              << "Listening on " << BOLD << "0.0.0.0:" << PROXY_PORT
              << RESET << " (epoll)" << std::endl;
    std::cout << GREEN << "[+] " << RESET
              << "Backend: " << BACKEND_HOST << ":" << BACKEND_PORT
              << std::endl;
    std::cout << GREEN << "[+] " << RESET
              << "WAF: SQLi + XSS detection " << GREEN << "enabled"
              << RESET << std::endl;
    std::cout << GREEN << "[+] " << RESET
              << "Rate Limit: " << static_cast<int>(RATE_TOKENS_S)
              << " req/s, burst " << static_cast<int>(RATE_BURST)
              << std::endl;
    std::cout << YELLOW << "[*] " << RESET
              << "Ctrl+C to shut down\n" << std::endl;

    // ══════════════════════════════════════
    //       epoll Main Event Loop
    // ══════════════════════════════════════
    struct epoll_event events[MAX_EVENTS];

    while (g_running.load()) {
        int nfds = epoll_wait(epoll_fd, events, MAX_EVENTS, 1000);

        if (nfds < 0) {
            if (errno == EINTR) continue;  // signal ขัดจังหวะ
            break;
        }

        for (int i = 0; i < nfds; i++) {
            if (events[i].data.fd == g_listen_fd) {
                // Accept ทุก pending connection (non-blocking)
                while (true) {
                    struct sockaddr_in cli_addr{};
                    socklen_t cli_len = sizeof(cli_addr);
                    int client_fd = accept(g_listen_fd,
                                           (struct sockaddr*)&cli_addr,
                                           &cli_len);

                    if (client_fd < 0) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK)
                            break;   // หมด pending connections
                        continue;
                    }

                    // ดึง IP (thread-safe ด้วย inet_ntop)
                    char ip_buf[INET_ADDRSTRLEN];
                    inet_ntop(AF_INET, &cli_addr.sin_addr,
                              ip_buf, sizeof(ip_buf));
                    std::string client_ip(ip_buf);

                    // Spawn handler thread
                    std::thread(handle_connection, client_fd,
                                std::move(client_ip)).detach();
                }
            }
        }
    }

    close(epoll_fd);

    // ── Final Stats ──
    auto elapsed = std::chrono::steady_clock::now() - g_start_time;
    long uptime = std::chrono::duration_cast<std::chrono::seconds>(elapsed).count();

    std::cout << "\n" << CYAN
              << "  ╔═══════════════════════════════════╗\n"
              << "  ║         Final Statistics          ║\n"
              << "  ╚═══════════════════════════════════╝"
              << RESET << std::endl;
    std::cout << "  Uptime:            " << uptime << "s" << std::endl;
    std::cout << "  Total requests:    " << g_total_requests.load() << std::endl;
    std::cout << "  Forwarded:         " << GREEN << g_forwarded.load()
              << RESET << std::endl;
    std::cout << "  Blocked (rate):    " << YELLOW << g_blocked_rate.load()
              << RESET << std::endl;
    std::cout << "  Blocked (WAF):     " << RED << g_blocked_waf.load()
              << RESET << std::endl;
    std::cout << GREEN << "\n[+] " << RESET
              << "Vanguard Edge Proxy stopped cleanly." << std::endl;

    return 0;
}
