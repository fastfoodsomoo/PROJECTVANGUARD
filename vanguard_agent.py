import os
import json
import logging
from typing import Dict, Any, Optional

# Google GenAI SDK & Cloud Firestore
from google import genai
from google.genai import types
from google.cloud import firestore

# Retry logic for transient API failures
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Setup Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VanguardAIAgent")

# ─── Constants ────────────────────────────────────────────────────────────────
REQUIRED_RESPONSE_KEYS = {"action", "ip", "reason"}


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

    # ─── Gemini Analysis with Retry & Validation ──────────────────────────
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, json.JSONDecodeError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Gemini API call failed (attempt {retry_state.attempt_number}/3), retrying…"
        ),
        reraise=True,
    )
    def analyze_threat(self, log_entry: str) -> Dict[str, Any]:
        """
        ส่ง Log ไปให้ Gemini 3.5 Flash วิเคราะห์และคืนค่า JSON
        Retries up to 3 times on transient failures.
        Validates that the response contains all required keys.
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

            # ── Input Validation ──────────────────────────────────────
            missing_keys = REQUIRED_RESPONSE_KEYS - result.keys()
            if missing_keys:
                raise ValueError(
                    f"Gemini response missing required keys: {missing_keys}. "
                    f"Got: {result}"
                )

            if not result["ip"] or result["ip"].lower() == "unknown":
                logger.warning(f"Gemini returned non-actionable IP: '{result['ip']}'")

            logger.info(f"Threat Analyzed - IP: {result.get('ip')}, Action: {result.get('action')}")
            return result

        except (json.JSONDecodeError, ValueError):
            # Let tenacity retry on these
            raise
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


# ═══════════════════════════════════════════════════════════════════════════════
# Enhanced Demo — Multiple Attack Scenarios
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    SAMPLE_LOGS = [
        {
            "label": "SQL Injection (sqlmap)",
            "log": (
                '203.0.113.195 - - [29/Aug/2026:22:15:30 +0700] '
                '"GET /api/v1/users?id=1%27%20UNION%20SELECT%20null,username,password%20FROM%20users-- HTTP/1.1" '
                '403 512 "-" "sqlmap/1.7.2#stable (https://sqlmap.org)"'
            ),
        },
        {
            "label": "Reflected XSS Probe",
            "log": (
                '198.51.100.42 - - [29/Aug/2026:22:18:05 +0700] '
                '"GET /search?q=%3Cscript%3Ealert(document.cookie)%3C%2Fscript%3E HTTP/1.1" '
                '403 256 "https://evil.example.com/" "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"'
            ),
        },
        {
            "label": "Path Traversal / LFI",
            "log": (
                '192.0.2.77 - - [29/Aug/2026:22:20:44 +0700] '
                '"GET /static/../../../etc/passwd HTTP/1.1" '
                '403 0 "-" "Nikto/2.5.0"'
            ),
        },
    ]

    print("=" * 72)
    print("  Vanguard Autonomous SOC Agent — Multi-Scenario Demo")
    print("=" * 72)

    try:
        agent = VanguardAIAgent()

        for idx, scenario in enumerate(SAMPLE_LOGS, start=1):
            print(f"\n{'─' * 72}")
            print(f"  Scenario {idx}/{len(SAMPLE_LOGS)}: {scenario['label']}")
            print(f"{'─' * 72}")
            print(f"  Log:\n  {scenario['log']}\n")

            result = agent.process_and_mitigate(scenario["log"])
            print(f"  Agent Decision:\n{json.dumps(result, indent=4)}")

        print(f"\n{'=' * 72}")
        print("  All scenarios processed successfully.")
        print(f"{'=' * 72}")

    except Exception as err:
        print(f"\nExecution Error: {err}")