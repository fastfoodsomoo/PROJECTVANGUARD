#!/bin/bash
# unban tool - ปลด ip ที่โดน sentinel ban
# sudo ./unban.sh              -> เมนู
# sudo ./unban.sh 10.0.0.66    -> ปลด ip นี้
# sudo ./unban.sh --all        -> ปลดหมด

G="\033[1;32m"; R="\033[1;31m"; Y="\033[1;33m"; C="\033[1;36m"; X="\033[0m"

if [ "$EUID" -ne 0 ]; then
    echo -e "${R}[!]${X} ต้องรันด้วย sudo!"
    exit 1
fi

unban_one() {
    while iptables -D INPUT -s "$1" -j DROP 2>/dev/null; do true; done
    echo -e "${G}[+]${X} unbanned: $1"
}

unban_all() {
    while iptables -D INPUT -j DROP 2>/dev/null; do true; done
    echo -e "${G}[+]${X} all IPs unbanned"
}

echo -e "\n${C}=== Vanguard Unban Tool ===${X}\n"

if [ -n "$1" ] && [ "$1" != "--all" ]; then
    unban_one "$1"
    echo -e "${Y}[tip]${X} เพิ่มใน whitelist ด้วย: echo \"$1\" >> whitelist.conf"
    exit 0
fi

if [ "$1" == "--all" ]; then
    unban_all
    exit 0
fi

# interactive mode
echo -e "${Y}[*]${X} Banned IPs (DROP rules):"
iptables -L INPUT -n --line-numbers | grep "DROP"
[ $? -ne 0 ] && echo "  (none)" && exit 0

echo ""
echo "1) ปลด ip ที่ระบุ"
echo "2) ปลดทั้งหมด"
echo "3) ออก"
read -p "เลือก: " c

case $c in
    1) read -p "IP: " ip; unban_one "$ip";;
    2) unban_all;;
    *) echo "bye";;
esac
echo ""
