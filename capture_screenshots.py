"""
VARLYTIX — Automated 15-Feature Visual Workstation Capture Script
Captures exactly 15 high-fidelity screenshots showcasing core features and distinct workflows:
1.  01_overview_workstation.png
2.  02_portfolio_active_holdings.png
3.  03_portfolio_log_transaction.png
4.  04_portfolio_broker_import.png
5.  05_portfolio_configuration.png
6.  06_risk_lab_core_metrics.png
7.  07_correlation_matrix_heatmap.png
8.  08_simulation_fan_chart.png
9.  09_stress_test_standard_shocks.png
10. 10_stress_test_custom_builder.png
11. 11_stress_test_historical_replay.png
12. 12_optimizer_efficient_frontier.png
13. 13_optimizer_what_if_rebalancer.png
14. 14_reports_and_dossier_export.png
15. 15_data_centre_quality_audit.png
"""

import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
import websockets

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "project screenshots")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PYTHON_PATH = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
STREAMLIT_PORT = 8512
CHROME_DEBUG_PORT = 9231

os.makedirs(OUTPUT_DIR, exist_ok=True)


class CDPClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=50 * 1024 * 1024)

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def send_cmd(self, method, params=None):
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method}
        if params:
            payload["params"] = params
        await self.ws.send(json.dumps(payload))
        while True:
            raw = await self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == self.msg_id:
                return data.get("result", {})

    async def eval_js(self, expression):
        res = await self.send_cmd("Runtime.evaluate", {
            "expression": expression,
            "awaitPromise": True,
            "returnByValue": True
        })
        val = res.get("result", {}).get("value")
        return val

    async def capture_screenshot(self, filepath):
        res = await self.send_cmd("Page.captureScreenshot", {
            "format": "png",
            "quality": 100,
            "fromSurface": True,
            "captureBeyondViewport": False
        })
        data = res.get("data", "")
        img_bytes = base64.b64decode(data)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        size_kb = len(img_bytes) // 1024
        print(f"  [SAVED] {os.path.basename(filepath)} ({size_kb} KB)", flush=True)
        return filepath


def wait_for_http(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "VARLYTIX-Capture"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


async def main():
    print("=" * 65, flush=True)
    print("   VARLYTIX — 15 Distinct Features Visual Workstation Capture     ", flush=True)
    print("=" * 65, flush=True)

    # 1. Start Streamlit on custom port
    print(f"[*] Launching Streamlit on port {STREAMLIT_PORT}...", flush=True)
    streamlit_log = open(os.path.join(PROJECT_ROOT, "streamlit_capture.log"), "w", encoding="utf-8")
    cmd = [
        PYTHON_PATH, "-m", "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    st_proc = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=streamlit_log,
        stderr=streamlit_log
    )

    chrome_proc = None
    cdp = None

    try:
        # Wait for Streamlit HTTP
        print(f"[*] Waiting for Streamlit server at http://127.0.0.1:{STREAMLIT_PORT}...", flush=True)
        st_ready = wait_for_http(f"http://127.0.0.1:{STREAMLIT_PORT}", timeout=35)
        if not st_ready:
            raise RuntimeError("Streamlit failed to initialize within timeout. Check streamlit_capture.log")
        print("[✓] Streamlit server is active!", flush=True)

        # 2. Launch Headless Chrome
        print("[*] Launching Headless Chrome with Remote Debugging...", flush=True)
        chrome_proc = subprocess.Popen([
            CHROME_PATH,
            f"--remote-debugging-port={CHROME_DEBUG_PORT}",
            "--headless=new",
            "--window-size=1600,1050",
            "--hide-scrollbars",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank"
        ])
        await asyncio.sleep(2.0)

        # Get WebSocket URL
        req = urllib.request.Request(f"http://127.0.0.1:{CHROME_DEBUG_PORT}/json")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            tabs = json.loads(resp.read().decode())
            ws_url = tabs[0]["webSocketDebuggerUrl"]

        cdp = CDPClient(ws_url)
        await cdp.connect()
        await cdp.send_cmd("Page.enable")
        await cdp.send_cmd("DOM.enable")

        target_url = f"http://127.0.0.1:{STREAMLIT_PORT}"
        print(f"[*] Navigating to {target_url}...", flush=True)
        await cdp.send_cmd("Page.navigate", {"url": target_url})

        # Wait for Streamlit app to fully hydrate
        print("[*] Waiting for Streamlit application to render...", flush=True)
        for _ in range(40):
            has_nav = await cdp.eval_js("""
                Boolean(Array.from(document.querySelectorAll('*')).find(el => el.children.length === 0 && (el.textContent || '').trim() === 'Overview'))
            """)
            if has_nav:
                break
            await asyncio.sleep(0.5)
        await asyncio.sleep(3.5)
        print("[✓] Streamlit application rendered successfully!", flush=True)

        async def switch_workspace(workspace_name):
            print(f"[*] Switching workspace to: {workspace_name}...", flush=True)
            js = f"""
            (() => {{
                const leaves = Array.from(document.querySelectorAll('*')).filter(el => el.children.length === 0 && (el.textContent || '').trim() === '{workspace_name}');
                const targetLeaf = leaves.find(l => l.closest('button[role="radio"], button'));
                if (targetLeaf) {{
                    const btn = targetLeaf.closest('button');
                    btn.click();
                    return true;
                }}
                return false;
            }})()
            """
            ok = await cdp.eval_js(js)
            if not ok:
                print(f"[!] Warning: Could not find button for '{workspace_name}'", flush=True)
            await asyncio.sleep(3.5)

        async def switch_tab(tab_name):
            print(f"[*] Switching tab to: {tab_name}...", flush=True)
            js = f"""
            (() => {{
                const tabs = Array.from(document.querySelectorAll('[role="tab"], [data-baseweb="tab"]'));
                const target = tabs.find(t => (t.textContent || '').includes('{tab_name}'));
                if (target) {{
                    target.click();
                    return true;
                }}
                return false;
            }})()
            """
            ok = await cdp.eval_js(js)
            if not ok:
                print(f"[!] Warning: Could not find tab '{tab_name}'", flush=True)
            await asyncio.sleep(2.5)

        # -----------------------------------------------------------------
        # 1. Overview Dashboard Workstation
        # -----------------------------------------------------------------
        print("\n[1/15] Capturing 01_overview_workstation.png...", flush=True)
        await asyncio.sleep(1.5)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "01_overview_workstation.png"))

        # -----------------------------------------------------------------
        # 2. Portfolio Active Holdings
        # -----------------------------------------------------------------
        print("\n[2/15] Capturing 02_portfolio_active_holdings.png...", flush=True)
        await switch_workspace("Portfolio")
        await switch_tab("Active Holdings")
        await asyncio.sleep(1.5)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "02_portfolio_active_holdings.png"))

        # -----------------------------------------------------------------
        # 3. Portfolio Log Transaction
        # -----------------------------------------------------------------
        print("\n[3/15] Capturing 03_portfolio_log_transaction.png...", flush=True)
        await switch_tab("Log Transaction")
        await asyncio.sleep(1.5)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "03_portfolio_log_transaction.png"))

        # -----------------------------------------------------------------
        # 4. Portfolio One-Click Broker Import
        # -----------------------------------------------------------------
        print("\n[4/15] Capturing 04_portfolio_broker_import.png...", flush=True)
        await switch_tab("Broker Import")
        await asyncio.sleep(1.5)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "04_portfolio_broker_import.png"))

        # -----------------------------------------------------------------
        # 5. Portfolio Configuration
        # -----------------------------------------------------------------
        print("\n[5/15] Capturing 05_portfolio_configuration.png...", flush=True)
        await switch_tab("Portfolio Configuration")
        await asyncio.sleep(1.5)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "05_portfolio_configuration.png"))

        # -----------------------------------------------------------------
        # 6. Risk Lab Core Quantitative Metrics
        # -----------------------------------------------------------------
        print("\n[6/15] Capturing 06_risk_lab_core_metrics.png...", flush=True)
        await switch_workspace("Risk Lab")
        await asyncio.sleep(2.0)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "06_risk_lab_core_metrics.png"))

        # -----------------------------------------------------------------
        # 7. Correlation Intelligence Matrix Heatmap
        # -----------------------------------------------------------------
        print("\n[7/15] Capturing 07_correlation_matrix_heatmap.png...", flush=True)
        await switch_workspace("Correlation")
        await asyncio.sleep(2.0)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "07_correlation_matrix_heatmap.png"))

        # -----------------------------------------------------------------
        # 8. Monte Carlo Simulation Fan Chart
        # -----------------------------------------------------------------
        print("\n[8/15] Capturing 08_simulation_fan_chart.png...", flush=True)
        await switch_workspace("Simulation")
        await asyncio.sleep(2.5)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "08_simulation_fan_chart.png"))

        # -----------------------------------------------------------------
        # 9. Stress Testing Standard Macro Shocks
        # -----------------------------------------------------------------
        print("\n[9/15] Capturing 09_stress_test_standard_shocks.png...", flush=True)
        await switch_workspace("Stress Test")
        await switch_tab("Standard Macro Shocks")
        await asyncio.sleep(2.0)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "09_stress_test_standard_shocks.png"))

        # -----------------------------------------------------------------
        # 10. Stress Testing Custom Asset Shock Builder
        # -----------------------------------------------------------------
        print("\n[10/15] Capturing 10_stress_test_custom_builder.png...", flush=True)
        await switch_tab("Custom Asset Shock")
        await asyncio.sleep(2.0)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "10_stress_test_custom_builder.png"))

        # -----------------------------------------------------------------
        # 11. Stress Testing Historical Event Replay
        # -----------------------------------------------------------------
        print("\n[11/15] Capturing 11_stress_test_historical_replay.png...", flush=True)
        await switch_tab("Historical Event Replay")
        await asyncio.sleep(2.0)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "11_stress_test_historical_replay.png"))

        # -----------------------------------------------------------------
        # 12. Optimizer Efficient Frontier
        # -----------------------------------------------------------------
        print("\n[12/15] Capturing 12_optimizer_efficient_frontier.png...", flush=True)
        await switch_workspace("Optimizer")
        await switch_tab("Efficient Frontier")
        await asyncio.sleep(2.5)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "12_optimizer_efficient_frontier.png"))

        # -----------------------------------------------------------------
        # 13. Optimizer 'What If?' Rebalancing Sandbox
        # -----------------------------------------------------------------
        print("\n[13/15] Capturing 13_optimizer_what_if_rebalancer.png...", flush=True)
        await switch_tab("Rebalancing Sandbox")
        await asyncio.sleep(2.0)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "13_optimizer_what_if_rebalancer.png"))

        # -----------------------------------------------------------------
        # 14. Institutional Reports & Export Dossier
        # -----------------------------------------------------------------
        print("\n[14/15] Capturing 14_reports_and_dossier_export.png...", flush=True)
        await switch_workspace("Reports")
        await asyncio.sleep(2.0)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "14_reports_and_dossier_export.png"))

        # -----------------------------------------------------------------
        # 15. Market Data Centre & Quality Audit
        # -----------------------------------------------------------------
        print("\n[15/15] Capturing 15_data_centre_quality_audit.png...", flush=True)
        await switch_workspace("Data Centre")
        await switch_tab("Observation Audit")
        await asyncio.sleep(2.0)
        await cdp.capture_screenshot(os.path.join(OUTPUT_DIR, "15_data_centre_quality_audit.png"))

        print("\n" + "=" * 65, flush=True)
        print("   [SUCCESS] All 15 distinct visual workstation screenshots captured! ", flush=True)
        print("=" * 65, flush=True)

    finally:
        # Clean shutdown
        if cdp:
            try:
                await cdp.close()
            except Exception:
                pass
        if chrome_proc:
            print("[*] Terminating Chrome...", flush=True)
            chrome_proc.terminate()
            try:
                chrome_proc.wait(timeout=5)
            except Exception:
                chrome_proc.kill()
        if st_proc:
            print("[*] Terminating Streamlit server...", flush=True)
            st_proc.terminate()
            try:
                st_proc.wait(timeout=5)
            except Exception:
                st_proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
