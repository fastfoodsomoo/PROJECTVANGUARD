import re

def update_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        text = f.read()

    # Update title in banner
    text = text.replace('AUTONOMOUS AI SOC AGENT & WAF ENGINE', 'VANGUARD v2 : AUTONOMOUS AI SOC AGENT & WAF ENGINE')
    text = text.replace('**Vanguard คือ', '**Vanguard v2 คือ')
    text = text.replace('**Vanguard** แก้ปัญหานี้', '**Vanguard v2** แก้ปัญหานี้')
    text = text.replace('Vanguard Control Center (GUI', 'Vanguard Control Center v2 (GUI')
    text = text.replace('Vanguard Edge Proxy', 'Vanguard v2 Edge Proxy')

    # Fix formatting issues
    text = text.replace('ทันที:Bash#', 'ทันที:\n```bash\n#')
    text = text.replace('python3 vanguard_gui.py\nสถาปัตยกรรมระบบ (Architecture)Plaintext', 'python3 vanguard_gui.py\n```\n\n## สถาปัตยกรรมระบบ (Architecture)\n```plaintext')
    text = text.replace('GUI:Bashpython3 dashboard.py', 'GUI:\n```bash\npython3 dashboard.py\n```')
    text = text.replace('TestingBash# ทดสอบ Normal Traffic', 'Testing\n```bash\n# ทดสอบ Normal Traffic')
    text = text.replace('DockerBash# Build', 'Docker\n```bash\n# Build')
    text = text.replace('โครงสร้างโปรเจกต์PlaintextPROJECTVANGUARD', 'โครงสร้างโปรเจกต์\n```plaintext\nPROJECTVANGUARD')
    text = text.replace('LICENSE                 # สัญญาอนุญาต MIT\n  Made by Sattaya Thongdaeng', 'LICENSE                 # สัญญาอนุญาต MIT\n```\n\n## สัญญาอนุญาต\nMade by Sattaya Thongdaeng')
    text = text.replace('Cloudเพื่อให้ระบบ Autonomous SOC ทำงานได้สมบูรณ์ จำเป็นต้องตั้งค่า API: \n\nexport GEMINI_API_KEY', 'Cloud\nเพื่อให้ระบบ Autonomous SOC ทำงานได้สมบูรณ์ จำเป็นต้องตั้งค่า API: \n```bash\nexport GEMINI_API_KEY')
    text = text.replace('export GOOGLE_APPLICATION_CREDENTIALS="gcp-key.json"\n\nเมื่อ setup', 'export GOOGLE_APPLICATION_CREDENTIALS="gcp-key.json"\n```\n\nเมื่อ setup')
    text = text.replace('Terminalสำหรับสภาพแวดล้อม', '## TUI Dashboard สำหรับ Terminal\nสำหรับสภาพแวดล้อม')
    
    # Check if headers are missing '## ' and fix them if so
    if 'จุดเด่นทางวิศวกรรม & AI Features\n🔧' in text:
        text = text.replace('จุดเด่นทางวิศวกรรม & AI Features\n🔧', '## จุดเด่นทางวิศวกรรม & AI Features\n### 🔧')
    if '🧠 ระบบ Autonomous AI SOC Agent\nContext-Aware' in text:
        text = text.replace('🧠 ระบบ Autonomous AI SOC Agent\nContext-Aware', '### 🧠 ระบบ Autonomous AI SOC Agent\nContext-Aware')
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(text)
    print('README.md updated successfully.')

if __name__ == "__main__":
    update_readme()
