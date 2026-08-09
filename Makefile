CXX      = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O3 -pthread

# ═══════════════════════════════════════════════════════════
# Vanguard v2 — Build Targets
# Architecture: [Client] → proxy:8080 → backend:3000
# ═══════════════════════════════════════════════════════════

all: vanguard_proxy my_server
	@chmod +x test.sh simulate_attack.sh 2>/dev/null || true
	@echo "\033[1;32m[+]\033[0m Build complete!"
	@echo "\033[2m    ./my_server        → Backend on 127.0.0.1:3000\033[0m"
	@echo "\033[2m    ./vanguard_proxy   → WAF Proxy on 0.0.0.0:8080\033[0m"

vanguard_proxy: vanguard_proxy.cpp include/colors.h
	$(CXX) $(CXXFLAGS) -o vanguard_proxy vanguard_proxy.cpp

my_server: my_server.cpp include/colors.h
	$(CXX) $(CXXFLAGS) -o my_server my_server.cpp

# ═══════════════════════════════════════════════════════════
# Legacy v1 Targets (preserved for reference)
# ═══════════════════════════════════════════════════════════

legacy-server: server.cpp include/config.h include/colors.h include/logger.h
	$(CXX) $(CXXFLAGS) -o server server.cpp

legacy-sentinel: sentinel.cpp include/config.h include/colors.h include/ip_utils.h
	$(CXX) $(CXXFLAGS) -o sentinel sentinel.cpp

# ═══════════════════════════════════════════════════════════
# Unit Tests (preserved from v1)
# ═══════════════════════════════════════════════════════════

test-unit: test-ip test-config test-rate
	@echo ""
	@echo "\033[1;32m✓ All unit tests passed!\033[0m"

test-ip: tests/test_ip.cpp include/ip_utils.h
	@$(CXX) $(CXXFLAGS) -o tests/test_ip tests/test_ip.cpp
	@./tests/test_ip

test-config: tests/test_config.cpp include/config.h
	@$(CXX) $(CXXFLAGS) -o tests/test_config tests/test_config.cpp
	@./tests/test_config

test-rate: tests/test_rate.cpp
	@$(CXX) $(CXXFLAGS) -o tests/test_rate tests/test_rate.cpp
	@./tests/test_rate

# ═══════════════════════════════════════════════════════════
# Run / Utilities
# ═══════════════════════════════════════════════════════════

run-backend: my_server
	./my_server

run-proxy: vanguard_proxy
	./vanguard_proxy

test: vanguard_proxy my_server
	@chmod +x test.sh
	./test.sh

simulate: vanguard_proxy my_server
	@chmod +x simulate_attack.sh
	./simulate_attack.sh

# ═══════════════════════════════════════════════════════════
# Cleanup
# ═══════════════════════════════════════════════════════════

clean:
	rm -f vanguard_proxy my_server
	rm -f server sentinel
	rm -f tests/test_ip tests/test_config tests/test_rate

.PHONY: all clean run-backend run-proxy test test-unit test-ip test-config test-rate simulate legacy-server legacy-sentinel
