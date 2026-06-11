CXX      = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -pthread

all: my_server sentinel
	@chmod +x test.sh unban.sh simulate_attack.sh 2>/dev/null || true

my_server: server.cpp
	$(CXX) $(CXXFLAGS) -o my_server server.cpp

sentinel: sentinel.cpp
	$(CXX) $(CXXFLAGS) -o sentinel sentinel.cpp

clean:
	rm -f my_server sentinel

run-server: my_server
	./my_server

run-sentinel: sentinel
	sudo ./sentinel

test: my_server
	@chmod +x test.sh
	./test.sh

simulate: all
	@chmod +x simulate_attack.sh
	./simulate_attack.sh

unban:
	@chmod +x unban.sh
	sudo ./unban.sh

.PHONY: all clean run-server run-sentinel test simulate unban
