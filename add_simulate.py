import re

def update():
    with open('README.md', 'r', encoding='utf-8') as f:
        text = f.read()

    addition = """## การใช้งานสคริปต์จำลองการโจมตีและการทดสอบระบบ (Simulate & Test)

นอกจากเครื่องมือ Stress Testing แล้ว ระบบยังมีสคริปต์สำหรับการจำลองการโจมตี (Attack Simulation) และการรัน Automated Tests เพื่อตรวจสอบการทำงานของ WAF และ Proxy:

### 1. การจำลองการโจมตี (`simulate_attack.sh`)
สคริปต์นี้ใช้สำหรับจำลองพฤติกรรมของแฮกเกอร์และผู้ใช้ทั่วไป เพื่อทดสอบว่า WAF และ Rate Limiter ทำงานบล็อกการโจมตีได้ถูกต้องหรือไม่:
```bash
# ⚠️ ข้อควรระวัง: ต้องเปิด vanguard_proxy และ my_server ให้ทำงานอยู่ก่อนรัน
bash simulate_attack.sh
```
สคริปต์จะทำการทดสอบ 4 สถานการณ์:
- **Scenario 1:** Normal User (Traffic ปกติ, ควรได้ HTTP 200)
- **Scenario 2:** Brute Force / Rate Limit (ยิงรัว 15 requests, ควรได้ HTTP 429)
- **Scenario 3:** WAF Test - SQL Injection (ยิง Payload SQLi, ควรได้ HTTP 403)
- **Scenario 4:** WAF Test - XSS (ยิง Payload XSS, ควรได้ HTTP 403)

### 2. ชุดทดสอบระบบอัตโนมัติ (`test.sh`)
สคริปต์สำหรับตรวจสอบ Integration Test ระหว่าง Proxy และ Backend:
```bash
bash test.sh
```
จะทำการทดสอบระบบตั้งแต่ การส่งต่อข้อมูล (Forwarding), การแก้ไข Header (Server, Content-Length), การดึงข้อมูล JSON จาก `/stats`, ไปจนถึงประสิทธิภาพการป้องกัน WAF และ Rate Limit รวม 9 การทดสอบ

### 3. การตั้งค่า Whitelist / Blacklist
ระบบรองรับการตั้งค่าผ่านไฟล์ Configuration:
- `whitelist.conf`: กำหนด IP ที่จะไม่ถูกจำกัดความเร็ว (Bypass Rate Limiting) เช่น IP ของผู้ดูแลระบบ (แต่ยังคงถูกตรวจสอบ WAF อยู่)
- `blacklist.conf`: ไฟล์ที่ Autonomous AI Agent จะใช้ในการเขียน IP ของผู้โจมตีลงไปเพื่อบล็อกการเชื่อมต่อโดยอัตโนมัติ (Auto-Ban)

"""

    # Add to TOC
    toc_old = "- [เครื่องมือ CLI และ Stress Testing](#เครื่องมือ-cli-และ-stress-testing)"
    toc_new = "- [การใช้งานสคริปต์จำลองการโจมตีและการทดสอบระบบ (Simulate & Test)](#การใช้งานสคริปต์จำลองการโจมตีและการทดสอบระบบ-simulate--test)\n- [เครื่องมือ CLI และ Stress Testing](#เครื่องมือ-cli-และ-stress-testing)"
    text = text.replace(toc_old, toc_new)

    # Add content
    header_old = "เครื่องมือ CLI และ Stress Testing\n```bash"
    header_new = addition + "## เครื่องมือ CLI และ Stress Testing\n```bash"
    text = text.replace(header_old, header_new)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(text)

if __name__ == "__main__":
    update()
