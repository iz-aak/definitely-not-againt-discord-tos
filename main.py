import os
import sys
import json
import asyncio
import platform
import requests
import websockets
from colorama import init, Fore
from keep_alive import keep_alive

init(autoreset=True)

status = "idle"  # online/dnd/idle
custom_status = "https://izaa.k.vu"  # Custom Status

usertoken = os.getenv("TOKEN")
if not usertoken:
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Please add a token inside Secrets.")
    sys.exit()

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

# Using standard API endpoint for better stability
validate = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
if validate.status_code != 200:
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Your token might be invalid. Please check it again.")
    sys.exit()

userinfo = validate.json()
username = userinfo["username"]
# Discriminator is deprecated in 2026, but kept for script compatibility
discriminator = userinfo.get("discriminator", "0000")
userid = userinfo["id"]

async def onliner(token, status):
    # Added max_size to handle large initial payloads from Discord
    async with websockets.connect(
        "wss://gateway.discord.gg/?v=9&encoding=json", 
        max_size=10_000_000
    ) as ws:
        start = json.loads(await ws.recv())
        heartbeat = start["d"]["heartbeat_interval"]

        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "Windows 10",
                    "$browser": "Google Chrome",
                    "$device": "Windows",
                },
                "presence": {"status": status, "afk": False},
            },
        }
        await ws.send(json.dumps(auth))

        cstatus = {
            "op": 3,
            "d": {
                "since": 0,
                "activities": [
                    {
                        "type": 4,
                        "state": custom_status,
                        "name": "Custom Status",
                        "id": "custom",
                    }
                ],
                "status": status,
                "afk": False,
            },
        }
        await ws.send(json.dumps(cstatus))

        # Fixed heartbeat payload: Must be None (null), not "None" (string)
        online = {"op": 1, "d": None}
        
        # Keep the connection alive for one heartbeat cycle
        await asyncio.sleep(heartbeat / 1000)
        await ws.send(json.dumps(online))

async def run_onliner():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
    
    print(f"{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] Logged in as {Fore.LIGHTBLUE_EX}{username}#{discriminator} {Fore.WHITE}({userid})!")
    
    while True:
        try:
            await onliner(usertoken, status)
        except Exception as e:
            print(f"{Fore.RED}[-]{Fore.WHITE} Connection error: {e}. Reconnecting...")
        
        # Sleep before restarting the connection cycle
        await asyncio.sleep(30)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(run_onliner())
