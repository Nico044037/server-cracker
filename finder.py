import asyncio
import random
import aiohttp
import socket
from mcstatus import JavaServer

API_URL = "https://web-production-79e19.up.railway.app/log"
API_KEY = "secret123"

# SAFE for Railway (600 is too high)
WORKERS = 120
MC_TIMEOUT = 1.5

DOMAINS = [
    "minefort.com","aternos.me","server.pro","mc.gg",
    "playit.gg","aternos.org","falixsrv.me","exaroton.com",
    "pebble.host","sparked.host","revivenode.com",
    "apexmc.co","shockbyte.com","bisecthosting.com",
    "ggservers.com","mcprohosting.com","meloncube.net",
    "noip.me","ddns.net","duckdns.org","hopto.org",
    "playit.cloud","minecraft.host","minecraftserver.io",
    "playmc.net","playserver.net","multiplayer.gg"
]

COMMON_NAMES = [
    "mc","play","smp","pvp","survival","lifesteal",
    "skyblock","bedwars","network","hub","proxy",
    "factions","prison","anarchy","vanilla","modded",
    "earth","towny","pixelmon","forge","fabric",
    "nova","cosmic","vortex","zenith","apex",
    "realm","world","kingdom","craft","cube","mine",
    "test","dev","beta","alpha","gg","live","online"
]

# Prevent duplicate spam to API
sent_cache = set()

def generate_name():
    return f"{random.choice(COMMON_NAMES)}{random.randint(1,999)}"

async def ping_minecraft(loop, address):
    try:
        server = await loop.run_in_executor(
            None,
            lambda: JavaServer.lookup(address)
        )
        status = await loop.run_in_executor(
            None,
            lambda: server.status(timeout=MC_TIMEOUT)
        )
        return status
    except (TimeoutError, ConnectionError, OSError, socket.gaierror):
        return None
    except Exception:
        return None

async def send_to_api(session, address, online, max_players, version):
    # Deduplicate
    if address in sent_cache:
        return

    payload = {
        "ip": address,
        "info": {
            "players": online,
            "max_players": max_players,
            "version": version,
            "source": "minecraft-scanner"
        }
    }

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        async with session.post(API_URL, json=payload, headers=headers) as resp:
            if resp.status == 200:
                sent_cache.add(address)
                print(f"[API SENT] {address} ({online}/{max_players})")
            else:
                text = await resp.text()
                print(f"[API ERROR {resp.status}] {address} -> {text}")
    except Exception as e:
        print(f"[API FAILED] {address} -> {e}")

async def worker(semaphore, session):
    loop = asyncio.get_running_loop()

    while True:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"

        async with semaphore:
            status = await ping_minecraft(loop, address)

        if not status:
            continue

        # Strong Minecraft validity filters
        if status.players is None:
            continue

        if status.players.max <= 0:
            continue

        online = status.players.online
        max_players = status.players.max

        # Ignore fake placeholder servers (VERY IMPORTANT)
        if online == 0 and max_players == 0:
            continue

        version = status.version.name if status.version else "unknown"

        print(f"[MC FOUND] {address} ({online}/{max_players}) {version}")

        await send_to_api(session, address, online, max_players, version)

async def main():
    semaphore = asyncio.Semaphore(WORKERS)

    connector = aiohttp.TCPConnector(
        limit=WORKERS,
        ttl_dns_cache=300,
        ssl=False
    )

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:

        tasks = [
            asyncio.create_task(worker(semaphore, session))
            for _ in range(WORKERS)
        ]

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
