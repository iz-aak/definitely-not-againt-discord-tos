import os
import sys
import json
import asyncio
import platform
import requests
import websockets
import time
from datetime import datetime
from colorama import init, Fore
from keep_alive import keep_alive
from webhook import log_startup, log_heartbeat, send_health

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

state = {
    "start_time": time.time(),
    "reconnects": 0,
    "last_heartbeat": None,
    "connected": False,
    "status": status,
    "custom_status": custom_status,
    "secs_to_next_pulse": 0,
}

async def health_loop():
    while True:
        try:
            send_health(state)
        except Exception as e:
            print(f"{Fore.RED}[{get_time()}] [HEALTH] Embed update failed: {e}")
        await asyncio.sleep(30)

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

        state["connected"] = True
        try:
            log_startup(username, userid, heartbeat_interval, status, custom_status)
        except Exception as e:
            print(f"{Fore.RED}[{get_time()}] [LOG] Startup log failed: {e}")

        while True:
            sleep_secs = heartbeat_interval / 1000
            for i in range(int(sleep_secs), 0, -1):
                state["secs_to_next_pulse"] = i
                await asyncio.sleep(1)

            print(f"{Fore.WHITE}[{get_time()}] {Fore.MAGENTA}[HEARTBEAT] {Fore.WHITE}Sending keep-alive pulse...")
            try:
                await ws.send(json.dumps({"op": 1, "d": None}))
                state["last_heartbeat"] = time.time()
                state["secs_to_next_pulse"] = int(sleep_secs)
                print(f"{Fore.WHITE}[{get_time()}] {Fore.GREEN}[SUCCESS] {Fore.WHITE}Pulse sent.")
                try:
                    log_heartbeat(True)
                except Exception as e:
                    print(f"{Fore.RED}[{get_time()}] [LOG] Heartbeat log failed: {e}")
            except Exception as e:
                state["connected"] = False
                print(f"{Fore.RED}[FAILURE] Pulse failed: {e}")
                try:
                    log_heartbeat(False, str(e))
                except Exception as le:
                    print(f"{Fore.RED}[{get_time()}] [LOG] Failure log failed: {le}")
                break

async def run_onliner():
    if platform.system() != "Windows":
        os.system("clear")
    print(f"{Fore.CYAN}[SCRIPT STARTED] copyright 2026 @uh.izaak")
    print(f"{Fore.GREEN}[INFO] Authenticated as: {username} ({userid})")

    asyncio.ensure_future(health_loop())

    while True:
        try:
            await onliner(usertoken, status)
        except Exception as e:
            state["connected"] = False
            state["reconnects"] += 1
            print(f"{Fore.WHITE}[{get_time()}] {Fore.RED}[RETRYING] {Fore.WHITE}Connection dropped ({e}). Reconnecting in 5s...")
            try:
                log_heartbeat(False, str(e))
            except Exception:
                pass
            await asyncio.sleep(5)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(run_onliner())
