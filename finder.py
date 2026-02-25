import asyncio
import random
import aiohttp
import socket
from mcstatus import JavaServer

# ===== CONFIG =====
API_URL = "https://web-production-79e19.up.railway.app/log"
API_KEY = "secret123"

WORKERS = 1000        # Increase for more speed (300–800 recommended)
MC_TIMEOUT = 1.5     # Minecraft servers respond fast if real
BATCH_INTERVAL = 2   # Seconds between API batch sends

# Minecraft hosting + common ecosystems
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

# Realistic Minecraft server name patterns
COMMON_NAMES = [
    "mc","play","smp","pvp","survival","lifesteal",
    "skyblock","bedwars","network","hub","proxy",
    "factions","prison","anarchy","vanilla","modded",
    "earth","towny","pixelmon","forge","fabric",
    "nova","cosmic","vortex","zenith","apex",
    "realm","world","kingdom","craft","cube","mine",
    "test","dev","beta","alpha","gg","live","online"
]

def generate_name():
    return f"{random.choice(COMMON_NAMES)}{random.randint(1, 999)}"

async def ping_minecraft(loop, address):
    """Fast Minecraft Java status ping"""
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

async def send_batch(session, batch):
    """Send multiple found MC servers in one request (much faster)"""
    if not batch:
        return

    headers = {"x-api-key": API_KEY}

    try:
        async with session.post(API_URL, json=batch, headers=headers) as resp:
            print(f"[API {resp.status}] Sent {len(batch)} servers")
    except Exception as e:
        print(f"[API ERROR] {e}")

async def worker(semaphore, session, results):
    loop = asyncio.get_running_loop()

    while True:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"

        # DEBUG: shows active scanning (important)
        print(f"[SCAN] {address}")

        async with semaphore:
            status = await ping_minecraft(loop, address)

        # CRITICAL: must be continue, NOT return (prevents dead workers)
        if not status:
            continue

        if status.players is None:
            continue

        if status.players.max <= 0:
            continue

        online = status.players.online
        max_players = status.players.max
        version = status.version.name if status.version else "unknown"

        print(f"[MC FOUND] {address} ({online}/{max_players}) {version}")

        results.append({
            "ip": address,
            "info": {
                "players": online,
                "max_players": max_players,
                "version": version,
                "source": "minecraft-scanner"
            }
        })

async def batch_sender(session, results):
    """Continuously sends results to your API"""
    while True:
        await asyncio.sleep(BATCH_INTERVAL)

        if results:
            batch = results[:]
            results.clear()
            await send_batch(session, batch)

async def main():
    print("=== MINECRAFT SCANNER STARTED ===")

    semaphore = asyncio.Semaphore(WORKERS)
    results = []

    # ssl=False helps on Windows + Railway environments
    connector = aiohttp.TCPConnector(
        limit=WORKERS,
        ssl=False,
        ttl_dns_cache=300
    )

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:

        # Start MC scanning workers
        tasks = [
            asyncio.create_task(worker(semaphore, session, results))
            for _ in range(WORKERS)
        ]

        # Start API batch sender
        tasks.append(asyncio.create_task(batch_sender(session, results)))

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
