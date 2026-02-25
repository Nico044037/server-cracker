import asyncio
import random
import aiohttp
from mcstatus import JavaServer
import socket

API_URL = "https://web-production-79e19.up.railway.app/log"
API_KEY = "secret123"

# Minecraft scanners scale best with async concurrency
CONCURRENCY = 800
TIMEOUT = 1.5  # MC servers respond quickly if real

DOMAINS = [
    "minefort.com","aternos.me","server.pro","mc.gg",
    "aternos.org","falixsrv.me","exaroton.com",
    "pebble.host","sparked.host","revivenode.com",
    "apexmc.co","shockbyte.com","bisecthosting.com",
    "ggservers.com","mcprohosting.com",
    "noip.me","ddns.net","duckdns.org","hopto.org",
    "playit.gg","playit.cloud",
    "minecraft.host","minecraftserver.io",
    "playmc.net","playserver.net","multiplayer.gg"
]

COMMON_NAMES = [
    "mc","play","smp","pvp","survival","lifesteal",
    "skyblock","bedwars","network","hub","proxy",
    "factions","prison","anarchy","vanilla","modded",
    "earth","towny","pixelmon","forge","fabric",
    "nova","cosmic","vortex","zenith","apex",
    "test","dev","beta","alpha","gg","live","online"
]

def generate_name():
    return f"{random.choice(COMMON_NAMES)}{random.randint(1,999)}"

async def send_to_api(session, batch):
    if not batch:
        return

    headers = {"x-api-key": API_KEY}

    try:
        async with session.post(API_URL, json=batch, headers=headers) as r:
            print(f"[API BATCH {r.status}] Sent {len(batch)} servers")
    except:
        pass

async def scan_worker(session, semaphore, results_buffer):
    loop = asyncio.get_running_loop()

    while True:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"

        async with semaphore:
            try:
                # Async MC lookup (faster than blocking)
                server = await loop.run_in_executor(
                    None,
                    lambda: JavaServer.lookup(address)
                )

                status = await loop.run_in_executor(
                    None,
                    lambda: server.status(timeout=TIMEOUT)
                )

                if not status:
                    return

                if status.players.max <= 0:
                    return

                online = status.players.online
                max_players = status.players.max
                version = status.version.name if status.version else "unknown"

                print(f"[FOUND] {address} ({online}/{max_players})")

                results_buffer.append({
                    "ip": address,
                    "info": {
                        "players": online,
                        "max_players": max_players,
                        "version": version,
                        "source": "mc-fast-scanner"
                    }
                })

            except (TimeoutError, ConnectionError, OSError, socket.gaierror):
                pass
            except Exception:
                pass

async def batch_sender(session, results_buffer):
    while True:
        await asyncio.sleep(2)
        if results_buffer:
            batch = results_buffer[:]
            results_buffer.clear()
            await send_to_api(session, batch)

async def main():
    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)
    timeout = aiohttp.ClientTimeout(total=10)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    results_buffer = []

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        workers = [
            asyncio.create_task(scan_worker(session, semaphore, results_buffer))
            for _ in range(CONCURRENCY)
        ]

        sender = asyncio.create_task(batch_sender(session, results_buffer))

        await asyncio.gather(*workers, sender)

if __name__ == "__main__":
    asyncio.run(main())
