cat > main.py << 'EOF'
import os
import sys
import json
import asyncio
import platform
import requests
import websockets
from datetime import datetime
from colorama import init, Fore
from keep_alive import keep_alive

init(autoreset=True)

status = "idle"
custom_status = ""

usertoken = os.getenv("TOKEN")
if not usertoken:
    print(f"{Fore.RED}[ERROR] No TOKEN found in environment variables.")
    sys.exit()

def get_time():
    return datetime.now().strftime("%H:%M:%S")

headers = {"Authorization": usertoken, "Content-Type": "application/json"}
validate = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers)
if validate.status_code != 200:
    print(f"{Fore.RED}[ERROR] Token Invalid (HTTP {validate.status_code})")
    sys.exit()

userinfo = validate.json()
username = userinfo["username"]
userid = userinfo["id"]

async def onliner(token, status):
    async with websockets.connect(
        "wss://gateway.discord.gg/?v=9&encoding=json",
        max_size=10_000_000,
        ping_interval=None,
        ping_timeout=None
    ) as ws:
        print(f"{Fore.WHITE}[{get_time()}] {Fore.YELLOW}[CONNECTING] {Fore.WHITE}Establishing Gateway connection...")
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]
        print(f"{Fore.WHITE}[{get_time()}] {Fore.GREEN}[SUCCESS] {Fore.WHITE}Handshake complete. Interval: {heartbeat_interval}ms")

        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {"$os": "Linux", "$browser": "Chrome", "$device": "Desktop"},
                "presence": {"status": status, "afk": False},
            },
        }
        await ws.send(json.dumps(auth))

        cstatus = {
            "op": 3,
            "d": {
                "since": 0,
                "activities": [{"type": 4, "state": custom_status, "name": "Custom Status", "id": "custom"}],
                "status": status,
                "afk": False,
            },
        }
        await ws.send(json.dumps(cstatus))
        print(f"{Fore.WHITE}[{get_time()}] {Fore.CYAN}[SUCCESS] {Fore.WHITE}Presence set to: {custom_status}")

        while True:
            await asyncio.sleep(heartbeat_interval / 1000)
            print(f"{Fore.WHITE}[{get_time()}] {Fore.MAGENTA}[HEARTBEAT] {Fore.WHITE}Sending keep-alive pulse...")
            try:
                await ws.send(json.dumps({"op": 1, "d": None}))
                print(f"{Fore.WHITE}[{get_time()}] {Fore.GREEN}[SUCCESS] {Fore.WHITE}Pulse sent.")
            except Exception as e:
                print(f"{Fore.RED}[FAILURE] Pulse failed: {e}")
                break

async def run_onliner():
    if platform.system() != "Windows":
        os.system("clear")
    print(f"{Fore.CYAN}[SCRIPT STARTED] copyright 2026 @uh.izaak")
    print(f"{Fore.GREEN}[INFO] Authenticated as: {username} ({userid})")

    while True:
        try:
            await onliner(usertoken, status)
        except Exception as e:
            print(f"{Fore.WHITE}[{get_time()}] {Fore.RED}[RETRYING] {Fore.WHITE}Connection dropped. Reconnecting in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(run_onliner())
EOF
