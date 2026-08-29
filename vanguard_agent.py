import os
import json
import logging
from typing import Dict, Any, Optional

# Google GenAI SDK & Cloud Firestore
from google import genai
from google.genai import types
from google.cloud import firestore

# Setup Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VanguardAIAgent")


class VanguardAIAgent:
    """
    Autonomous SOC Agent that analyzes incoming proxy/WAF logs using Gemini 3.5 Flash
    and logs threat mitigations directly to Google Cloud Firestore.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        database_id: str = "vanguardagent",
        model_name: str = "gemini-3.5-flash"
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Error: ไม่พบ GEMINI_API_KEY ใน Environment Variables กรุณาตั้งค่าก่อนเริ่มใช้งาน")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "vanguard-agent-507021")
        self.database_id = database_id

        # ระบุ database_id="vanguardagent" ให้ตรงกับที่สร้างไว้ใน Google Cloud
        try:
            self.db = firestore.Client(project=self.project_id, database=self.database_id)
            logger.info(f"Firestore Client initialized successfully (Database: {self.database_id}).")
        except Exception as e:
            logger.warning(f"Firestore Client warning: {e}. (Set GOOGLE_APPLICATION_CREDENTIALS if needed)")
            self.db = None

    def analyze_threat(self, log_entry: str) -> Dict[str, Any]:
        """
        ส่ง Log ไปให้ Gemini 3.5 Flash วิเคราะห์และคืนค่า JSON
        """
        system_instruction = (
            "You are an expert Autonomous SOC / Cybersecurity AI Agent embedded in a high-performance WAF & Edge Proxy. "
            "Your task is to analyze the provided raw web server / proxy log line for security threats "
            "(e.g., SQL Injection, XSS, Path Traversal, Directory Bruteforce, RCE, Scanning tools, Malicious User-Agents). "
            "Determine the attacker's IP and decide the mitigation action. "
            "You MUST respond ONLY with a valid JSON object matching this exact format:\n"
            "{\n"
            '  "action": "ban",\n'
            '  "ip": "<attacker_ip>",\n'
            '  "reason": "<short_reason>"\n'
            "}"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"Analyze this suspicious log entry:\n{log_entry}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            raw_text = response.text.strip()
            result: Dict[str, Any] = json.loads(raw_text)
            logger.info(f"Threat Analyzed - IP: {result.get('ip')}, Action: {result.get('action')}")
            return result

        except Exception as e:
            logger.error(f"Error during Gemini threat analysis: {e}")
            raise

    def log_to_firestore(self, ip: str, reason: str) -> str:
        """
        บันทึกข้อมูล IP ที่ถูกแบนลง Firestore Collection 'blocked_threats'
        """
        if not self.db:
            raise RuntimeError("Firestore Client is not initialized.")

        collection_name = "blocked_threats"
        doc_data = {
            "ip": ip,
            "reason": reason,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "model": self.model_name,
            "status": "active_ban"
        }

        collection_ref = self.db.collection(collection_name)
        _, doc_ref = collection_ref.add(doc_data)
        logger.info(f"Threat logged to Firestore ID: [{doc_ref.id}]")
        return doc_ref.id

    def process_and_mitigate(self, log_entry: str) -> Optional[Dict[str, Any]]:
        """
        Pipeline Action: วิเคราะห์ Log -> สั่งแบนและบันทึกขึ้น Firestore
        """
        analysis = self.analyze_threat(log_entry)
        action = analysis.get("action", "").lower()
        ip = analysis.get("ip")
        reason = analysis.get("reason", "Malicious activity detected")

        if action == "ban" and ip and ip != "unknown":
            if self.db:
                doc_id = self.log_to_firestore(ip=ip, reason=reason)
                analysis["firestore_doc_id"] = doc_id
            return analysis

        return analysis


if __name__ == "__main__":
    sample_malicious_log = (
        '203.0.113.195 - - [29/Aug/2026:22:15:30 +0700] "GET /api/v1/users?id=1%27%20UNION%20SELECT%20null,username,password%20FROM%20users-- HTTP/1.1" '
        '403 512 "-" "sqlmap/1.7.2#stable (https://sqlmap.org)"'
    )

    print("=== Testing Vanguard Autonomous SOC Agent ===")
    try:
        agent = VanguardAIAgent()
        print(f"\n Input Log:\n{sample_malicious_log}")
        
        result = agent.process_and_mitigate(sample_malicious_log)
        print(f"\n Agent Decision Output:\n{json.dumps(result, indent=2)}")
        
    except Exception as err:
        print(f"\nExecution Error: {err}")