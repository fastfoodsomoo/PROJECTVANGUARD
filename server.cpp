#include <sys/socket.h>
#include <netinet/in.h>
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <arpa/inet.h>
#include <fstream>
#include <string>
#include <sstream>
#include <ctime>
#include <csignal>
#include <thread>
#include <atomic>

// === Config (อ่านจาก config.conf ถ้ามี) ===
static int         PORT         = 8080;
static int         MAX_CONN     = 64;
static int         RECV_TIMEOUT = 5;
static std::string LOG_PATH     = "server_log.txt";

// ANSI colors
#define GREEN   "\033[1;32m"
#define CYAN    "\033[1;36m"
#define YELLOW  "\033[1;33m"
#define RED     "\033[1;31m"
#define MAGENTA "\033[1;35m"
#define RESET   "\033[0m"

int server_fd = -1;
std::atomic<int>  active_threads{0};
std::atomic<long> total_requests{0};

void load_config(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open()) {
        std::cout << YELLOW << "[*] " << RESET
                  << "config.conf not found, using defaults" << std::endl;
        return;
    }

    std::string line;
    while (std::getline(f, line)) {
        if (line.empty() || line[0] == '#') continue;
        size_t eq = line.find('=');
        if (eq == std::string::npos) continue;

        std::string key = line.substr(0, eq);
        std::string val = line.substr(eq + 1);

        // trim
        key.erase(key.find_last_not_of(" \t") + 1);
        key.erase(0, key.find_first_not_of(" \t"));
        val.erase(val.find_last_not_of(" \t") + 1);
        val.erase(0, val.find_first_not_of(" \t"));

        if      (key == "port")            PORT         = std::stoi(val);
        else if (key == "max_connections") MAX_CONN     = std::stoi(val);
        else if (key == "recv_timeout")    RECV_TIMEOUT = std::stoi(val);
        else if (key == "log_path")        LOG_PATH     = val;
    }
    std::cout << GREEN << "[+] " << RESET << "Loaded config from " << path << std::endl;
}

std::string get_time() {
    auto now = std::time(nullptr);
    char buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
    return std::string(buf);
}

// สร้าง HTTP response พร้อม html
std::string make_response(const std::string& title, const std::string& heading,
                          const std::string& subtitle, const std::string& status) {
    std::string body =
        "<!DOCTYPE html><html>"
        "<head><title>" + title + "</title></head>"
        "<body style='background-color: #0d1117; color: #00ff00;"
        " font-family: monospace; text-align: center; margin-top: 15%;'>"
        "<h1>" + heading + "</h1>"
        "<h2>" + subtitle + "</h2>"
        "<p>Status: " + status + "</p>"
        "<p>Developer: Sattaya</p>"
        "</body></html>";

    std::ostringstream resp;
    resp << "HTTP/1.1 200 OK\r\n"
         << "Content-Type: text/html; charset=utf-8\r\n"
         << "Content-Length: " << body.size() << "\r\n"
         << "Connection: close\r\n\r\n"
         << body;
    return resp.str();
}

// Ctrl+C handler
void signal_handler(int) {
    std::cout << "\n" << YELLOW << "[*] " << RESET
              << "Shutting down... (" << total_requests.load() << " requests served)" << std::endl;
    if (server_fd != -1) close(server_fd);
    exit(0);
}

// จัดการ client แต่ละคน (ทำงานใน thread แยก)
void handle_client(int sock, std::string ip) {
    active_threads++;
    long reqnum = ++total_requests;

    char buffer[4096] = {0};
    int n = recv(sock, buffer, sizeof(buffer) - 1, 0);
    if (n <= 0) {
        close(sock);
        active_threads--;
        return;
    }
    buffer[n] = '\0'; // null-terminate เอง เพราะ recv ไม่ทำให้

    std::string request(buffer);
    std::string ts = get_time();

    std::cout << CYAN << "[#" << reqnum << "] " << RESET
              << GREEN << ip << RESET << " connected at " << ts << std::endl;

    // เขียน log ทุก request
    std::ofstream logf(LOG_PATH, std::ios::app);
    if (logf.is_open()) {
        logf << "========== LOG ENTRY ==========\n"
             << "Time: " << ts << "\n"
             << "IP Address: " << ip << "\n"
             << "Request Data :\n" << request << "\n";
        logf.close();
    }

    std::string response;
    if (request.find("GET /VANGUARD") != std::string::npos) {
        response = make_response("Vanguard", "[ VANGUARD ]",
                                 "Welcome to Vanguard Page", "Active");
        std::cout << GREEN << "  -> " << RESET << "served /VANGUARD" << std::endl;
    } else {
        response = make_response("Forge Server", "[ SYSTEM ONLINE ]",
                                 "Welcome to C++ Core Server", "Fully Operational");
    }

    send(sock, response.c_str(), response.size(), 0);
    close(sock);
    active_threads--;
}

int main() {
    signal(SIGINT, signal_handler);
    load_config("config.conf");

    // banner
    std::cout << MAGENTA << "\n"
              << " ╔══════════════════════════════════════╗\n"
              << " ║     VANGUARD  —  C++ Core Server     ║\n"
              << " ╚══════════════════════════════════════╝\n"
              << RESET << std::endl;

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        std::cerr << RED << "[!] " << RESET << "socket() failed" << std::endl;
        return 1;
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        std::cerr << RED << "[!] " << RESET
                  << "bind() failed - port " << PORT << " in use?" << std::endl;
        return 1;
    }
    if (listen(server_fd, 10) < 0) {
        std::cerr << RED << "[!] " << RESET << "listen() failed" << std::endl;
        return 1;
    }

    std::cout << GREEN << "[+] " << RESET
              << "Listening on port " << PORT
              << " (max " << MAX_CONN << " connections)" << std::endl;
    std::cout << YELLOW << "[*] " << RESET << "Ctrl+C to shut down\n" << std::endl;

    while (true) {
        struct sockaddr_in cli_addr;
        socklen_t cli_len = sizeof(cli_addr);
        int clientsock = accept(server_fd, (struct sockaddr*)&cli_addr, &cli_len);
        if (clientsock < 0) continue;

        // timeout กัน client ค้าง
        struct timeval tv;
        tv.tv_sec = RECV_TIMEOUT;
        tv.tv_usec = 0;
        setsockopt(clientsock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof(tv));

        std::string client_ip = inet_ntoa(cli_addr.sin_addr);

        // ถ้า thread เต็มก็ reject ไปเลย (กัน DoS)
        if (active_threads.load() >= MAX_CONN) {
            std::cerr << RED << "[!] " << RESET
                      << "Connection limit reached, rejecting " << client_ip << std::endl;
            const char* busy = "HTTP/1.1 503 Service Unavailable\r\n"
                               "Content-Length: 16\r\nConnection: close\r\n\r\n"
                               "Server is busy.\n";
            send(clientsock, busy, strlen(busy), 0);
            close(clientsock);
            continue;
        }

        std::thread(handle_client, clientsock, client_ip).detach();
    }

    return 0;
}