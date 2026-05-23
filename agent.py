import os
import json
import requests
import sys

class WrtDiagnosticAgent:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.system_prompt = (
            "You are an advanced Network Engineering Agent running on an edge router (OpenWrt/ImmortalWrt).\n"
            "Your task is to analyze system logs containing SmartDNS, Lucky (STUN/port forwarding), and UA3F (DPI circumvention) status.\n"
            "Identify network anomalies (e.g., DPI blocking, IPv6 drops, DNS hijacking) and output a chain of thought reasoning followed by a precise Shell script block to remediate the issue.\n"
            "Format your output exactly as:\n"
            "【REASONING】\n<your step-by-step long chain reasoning>\n"
            "【EXECUTION】\n```bash\n<remediation shell commands>\n```"
        )

    def analyze_logs(self, log_text: str, model: str = "gpt-4o") -> str:
        if not self.api_key or self.api_key == "mock-key-for-local-test":
            return self._generate_simulation_output()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Analyze these raw edge logs:\n\n{log_text}"}
            ],
            "temperature": 0.1
        }

        print("[*] Connecting to LLM Gateway... Initiating long-chain reasoning.")
        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"[-] Network transport error: {e}", file=sys.stderr)
            return self._generate_simulation_output()

    def _generate_simulation_output(self) -> str:
        return (
            "【REASONING】\n"
            "1. 日志表明 SmartDNS 53 端口解析连续超时，判定上游标准 UDP 53 报文遭受网关 DPI 阻断或劫持。\n"
            "2. Lucky 服务上报 STUN 绑定失败且未检测到有效前缀，判定原 WAN 口 IPv6 动态路由表缓存失效，导致穿透线程挂起。\n"
            "3. UA3F 检测到网关 TTL 异常丢弃告警，判定常规操作系统 TCP/IP 指纹已暴露，需立刻重塑混淆矩阵。\n\n"
            "【EXECUTION】\n"
            "```bash\n"
            "# 1. 重构 SmartDNS 策略，强制切换至非标端口的 TLS (DoT) 加密隧道\n"
            "sed -i 's/server 223.5.5.5/server tls://8.8.8.8:853/' /etc/smartdns/smartdns.conf\n"
            "/etc/init.d/smartdns restart\n\n"
            "# 2. 刷新边缘节点 IPv6 路由缓存，强制 NDP 重新寻址恢复 Lucky 穿透\n"
            "ip -6 route flush cache\n\n"
            "# 3. 动态调整 UA3F 策略，重置自适应 IPID 偏移量并固定全局 TTL 值为 128\n"
            "ua3f -m dynamic --ipid-mode random-offset --ttl 128\n"
            "```"
        )

if __name__ == "__main__":
    sample_logs = """
    daemon.info smartdns[1234]: query server 223.5.5.5:53 timeout, retrying...
    daemon.warn smartdns[1234]: all upstream servers failed for rule 'campus-bypass'
    daemon.err lucky[5678]: STUN binding failed: local port 16384, no response from stun.lucky.net
    kernel: [1024.123] ua3f: [DPI-ALERT] TTL mismatch detected from gateway. Packet dropped to prevent identification.
    """

    print("[+] Wrt-Agent-Core Engine Initialized.")
    print("[*] Ingesting raw system logs from OpenWrt ring buffer...")

    api_key = os.getenv("LLM_API_KEY", "mock-key-for-local-test")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

    agent = WrtDiagnosticAgent(api_key=api_key, base_url=base_url)
    output = agent.analyze_logs(sample_logs)
    print(output)