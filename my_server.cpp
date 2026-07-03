// ═══════════════════════════════════════════════════════════════════════
// Vanguard — Backend Web Server (Private)
// ฟังเฉพาะ 127.0.0.1:3000 — ไม่เปิดรับจากภายนอกโดยตรง
// ทุก request ต้องผ่าน vanguard_proxy (port 8080) ก่อน
//
// Features:
//   • Bind เฉพาะ loopback (127.0.0.1) เท่านั้น
//   • Log incoming headers เพื่อยืนยันว่า proxy inject headers สำเร็จ
//   • Dark theme HTML pages (เหมือน v1)
//   • Routes: / | /VANGUARD | /stats
//
// by Sattaya — Project Vanguard v2
// ═══════════════════════════════════════════════════════════════════════

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <sstream>
#include <csignal>
#include <thread>
#include <atomic>
#include <chrono>
#include <mutex>
#include <string>

#include "include/colors.h"

// ╔═══════════════════════════════════════╗
// ║         Configuration                 ║
// ╚═══════════════════════════════════════╝

static constexpr int         BACKEND_PORT = 3000;
static constexpr const char* BIND_ADDR    = "127.0.0.1";

// ╔═══════════════════════════════════════╗
// ║          Global State                 ║
// ╚═══════════════════════════════════════╝

static int                server_fd = -1;
static std::atomic<bool>  running{true};
static std::atomic<int>   active_threads{0};
static std::atomic<long>  total_requests{0};
static std::chrono::steady_clock::time_point start_time;
static std::mutex         cout_mtx;

// ╔═══════════════════════════════════════╗
// ║       Time Utility                    ║
// ╚═══════════════════════════════════════╝

static std::string now_str() {
    auto t = std::time(nullptr);
    char buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&t));
    return buf;
}

// ╔═══════════════════════════════════════╗
// ║       Header Extractor                ║
// ╚═══════════════════════════════════════╝

// ดึงค่า header จาก raw HTTP request
static std::string get_header(const std::string& request,
                               const std::string& name) {
    std::string search = name + ": ";
    auto pos = request.find(search);
    if (pos == std::string::npos) return "";
    pos += search.size();
    auto end = request.find("\r\n", pos);
    if (end == std::string::npos) return request.substr(pos);
    return request.substr(pos, end - pos);
}

// ╔═══════════════════════════════════════╗
// ║       HTML Page Generator             ║
// ╚═══════════════════════════════════════╝

// สร้างหน้า HTML แบบ modern dark UI พร้อม animation
static std::string make_page(const std::string& title,
                              const std::string& emoji,
                              const std::string& heading,
                              const std::string& subtitle,
                              const std::string& status_text,
                              bool is_ok) {
    std::string status_class = is_ok ? "online" : "error";
    std::string pulse_class  = is_ok ? "green"  : "red";

    return
        "<!DOCTYPE html><html lang=\"en\">"
        "<head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\">"
        "<title>" + title + "</title>"
        "<style>"
        "*{margin:0;padding:0;box-sizing:border-box}"
        "body{"
            "background:linear-gradient(135deg,#0d1117 0%,#161b22 50%,#0d1117 100%);"
            "color:#e6edf3;"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;"
            "min-height:100vh;display:flex;align-items:center;justify-content:center"
        "}"
        ".container{"
            "text-align:center;padding:3rem;"
            "background:rgba(22,27,34,0.8);"
            "border:1px solid #30363d;border-radius:12px;"
            "backdrop-filter:blur(10px);"
            "box-shadow:0 8px 32px rgba(0,0,0,0.3);"
            "max-width:500px;width:90%;"
            "animation:fadeIn .6s ease-out"
        "}"
        "@keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}"
        ".logo{font-size:3rem;margin-bottom:.5rem}"
        "h1{"
            "font-size:1.8rem;"
            "background:linear-gradient(135deg,#58a6ff,#3fb950);"
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
            "background-clip:text;margin-bottom:.5rem"
        "}"
        ".subtitle{color:#8b949e;font-size:1rem;margin-bottom:1.5rem}"
        ".status{"
            "display:inline-block;padding:.35rem 1rem;"
            "border-radius:2rem;font-size:.85rem;font-weight:600"
        "}"
        ".status.online{background:rgba(63,185,80,.15);color:#3fb950;border:1px solid rgba(63,185,80,.4)}"
        ".status.error{background:rgba(248,81,73,.15);color:#f85149;border:1px solid rgba(248,81,73,.4)}"
        ".pulse{"
            "display:inline-block;width:8px;height:8px;"
            "border-radius:50%;margin-right:6px;"
            "animation:pulse 2s infinite"
        "}"
        ".pulse.green{background:#3fb950}"
        ".pulse.red{background:#f85149}"
        "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}"
        ".footer{"
            "color:#484f58;margin-top:2rem;font-size:.75rem;"
            "border-top:1px solid #21262d;padding-top:1rem"
        "}"
        "</style></head>"
        "<body><div class=\"container\">"
        "<div class=\"logo\">" + emoji + "</div>"
        "<h1>" + heading + "</h1>"
        "<p class=\"subtitle\">" + subtitle + "</p>"
        "<span class=\"status " + status_class + "\">"
        "<span class=\"pulse " + pulse_class + "\"></span>"
        + status_text + "</span>"
        "<p class=\"footer\">Vanguard Backend v2.0 &middot; Built with C++ &middot; by Sattaya</p>"
        "</div></body></html>";
}

// ╔═══════════════════════════════════════╗
// ║       HTTP Response Builder           ║
// ╚═══════════════════════════════════════╝

static std::string http_response(int code, const std::string& status,
                                  const std::string& content_type,
                                  const std::string& body) {
    std::ostringstream resp;
    resp << "HTTP/1.1 " << code << " " << status << "\r\n"
         << "Content-Type: " << content_type << "\r\n"
         << "Content-Length: " << body.size() << "\r\n"
         << "Server: Vanguard-Backend/2.0\r\n"
         << "Connection: close\r\n\r\n"
         << body;
    return resp.str();
}

// ╔═══════════════════════════════════════╗
// ║       Signal Handler (Ctrl+C)         ║
// ╚═══════════════════════════════════════╝

void signal_handler(int) {
    std::cout << "\n" << YELLOW << "[*] " << RESET
              << "Shutting down backend... ("
              << total_requests.load() << " requests served)"
              << std::endl;
    running.store(false);
    if (server_fd != -1) {
        shutdown(server_fd, SHUT_RDWR);
        close(server_fd);
        server_fd = -1;
    }
}

// ╔═══════════════════════════════════════╗
// ║       Client Handler (per thread)     ║
// ╚═══════════════════════════════════════╝

void handle_client(int sock) {
    active_threads++;
    long reqnum = ++total_requests;

    // รับ request
    char buffer[4096] = {0};
    int n = recv(sock, buffer, sizeof(buffer) - 1, 0);
    if (n <= 0) {
        close(sock);
        active_threads--;
        return;
    }
    buffer[n] = '\0';

    std::string request(buffer);
    std::string ts = now_str();

    // ดึง injected headers จาก proxy
    std::string vanguard_ip = get_header(request, "X-Vanguard-Connecting-IP");
    std::string ray_id      = get_header(request, "X-Vanguard-Ray-ID");

    // Log incoming request พร้อม injected headers
    {
        std::lock_guard<std::mutex> lock(cout_mtx);
        std::cout << CYAN << "[#" << reqnum << "] " << RESET
                  << ts;
        if (!vanguard_ip.empty()) {
            std::cout << " | client=" << GREEN << vanguard_ip << RESET;
        }
        if (!ray_id.empty()) {
            std::cout << " | ray=" << DIM << ray_id << RESET;
        }
        std::cout << std::endl;
    }

    // แยก HTTP method
    std::string method = request.substr(0, request.find(' '));
    std::string response;

    // ── Routing ──

    if (method != "GET" && method != "HEAD") {
        // 405 Method Not Allowed
        std::string body = make_page("405 Method Not Allowed", "🚫",
            "METHOD NOT ALLOWED",
            "Only GET and HEAD methods are supported",
            "Error 405", false);
        response = http_response(405, "Method Not Allowed",
                                 "text/html; charset=utf-8", body);

    } else if (request.find("GET /VANGUARD") != std::string::npos ||
               request.find("HEAD /VANGUARD") != std::string::npos) {
        // /VANGUARD
        std::string body = make_page("Vanguard", "🛡️",
            "VANGUARD",
            "Network Security Suite — Active Defense System",
            "Active", true);
        response = http_response(200, "OK",
                                 "text/html; charset=utf-8", body);

    } else if (request.find("GET /stats") != std::string::npos ||
               request.find("HEAD /stats") != std::string::npos) {
        // /stats — JSON endpoint
        auto elapsed = std::chrono::steady_clock::now() - start_time;
        long uptime  = std::chrono::duration_cast<std::chrono::seconds>(elapsed).count();

        std::ostringstream json;
        json << "{\n"
             << "  \"server\": \"Vanguard-Backend/2.0\",\n"
             << "  \"status\": \"online\",\n"
             << "  \"bind\": \"" << BIND_ADDR << ":" << BACKEND_PORT << "\",\n"
             << "  \"total_requests\": " << total_requests.load() << ",\n"
             << "  \"active_connections\": " << active_threads.load() << ",\n"
             << "  \"uptime_seconds\": " << uptime << "\n"
             << "}";
        response = http_response(200, "OK",
                                 "application/json; charset=utf-8", json.str());

    } else if (request.find("GET /") != std::string::npos ||
               request.find("HEAD /") != std::string::npos) {
        // / — Home page
        std::string body = make_page("Vanguard Server", "⚡",
            "SYSTEM ONLINE",
            "C++ Backend Server — Protected by Vanguard Edge Proxy",
            "Fully Operational", true);
        response = http_response(200, "OK",
                                 "text/html; charset=utf-8", body);

    } else {
        // 404
        std::string body = make_page("404 Not Found", "🔍",
            "NOT FOUND",
            "The requested page could not be found on this server",
            "Error 404", false);
        response = http_response(404, "Not Found",
                                 "text/html; charset=utf-8", body);
    }

    send(sock, response.c_str(), response.size(), 0);
    close(sock);
    active_threads--;
}

// ╔═══════════════════════════════════════╗
// ║              Main                     ║
// ╚═══════════════════════════════════════╝

int main() {
    signal(SIGINT, signal_handler);
    start_time = std::chrono::steady_clock::now();

    // Banner
    std::cout << MAGENTA << "\n"
              << " ╔══════════════════════════════════════════════╗\n"
              << " ║   VANGUARD BACKEND — Private Web Server      ║\n"
              << " ║   Listening on " << BIND_ADDR << ":" << BACKEND_PORT
              << " (loopback only)   ║\n"
              << " ╚══════════════════════════════════════════════╝\n"
              << RESET << std::endl;

    // สร้าง socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        std::cerr << RED << "[!] " << RESET
                  << "socket() failed" << std::endl;
        return 1;
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    // ── Bind เฉพาะ 127.0.0.1 (ไม่ใช่ INADDR_ANY) ──
    inet_pton(AF_INET, BIND_ADDR, &addr.sin_addr);
    addr.sin_port = htons(BACKEND_PORT);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        std::cerr << RED << "[!] " << RESET
                  << "bind() failed — port " << BACKEND_PORT << " in use?"
                  << std::endl;
        close(server_fd);
        return 1;
    }

    if (listen(server_fd, 64) < 0) {
        std::cerr << RED << "[!] " << RESET
                  << "listen() failed" << std::endl;
        close(server_fd);
        return 1;
    }

    std::cout << GREEN << "[+] " << RESET
              << "Listening on " << BOLD << BIND_ADDR << ":"
              << BACKEND_PORT << RESET << " (private)" << std::endl;
    std::cout << GREEN << "[+] " << RESET
              << "Routes: / | /VANGUARD | /stats" << std::endl;
    std::cout << GREEN << "[+] " << RESET
              << "Proxy headers: X-Vanguard-Connecting-IP, X-Vanguard-Ray-ID"
              << std::endl;
    std::cout << YELLOW << "[*] " << RESET
              << "Ctrl+C to shut down\n" << std::endl;

    // === Main Accept Loop ===
    while (running.load()) {
        struct sockaddr_in cli_addr{};
        socklen_t cli_len = sizeof(cli_addr);
        int clientsock = accept(server_fd, (struct sockaddr*)&cli_addr,
                                &cli_len);

        if (clientsock < 0) {
            if (!running.load()) break;
            continue;
        }

        // ตั้ง recv timeout
        struct timeval tv;
        tv.tv_sec  = 5;
        tv.tv_usec = 0;
        setsockopt(clientsock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

        std::thread(handle_client, clientsock).detach();
    }

    // Graceful shutdown
    if (active_threads.load() > 0) {
        std::cout << YELLOW << "[*] " << RESET
                  << "Waiting for " << active_threads.load()
                  << " active connections..." << std::endl;
        int wait_count = 0;
        while (active_threads.load() > 0 && wait_count < 50) {
            usleep(100000);
            wait_count++;
        }
    }

    std::cout << GREEN << "[+] " << RESET
              << "Backend stopped cleanly." << std::endl;
    return 0;
}
