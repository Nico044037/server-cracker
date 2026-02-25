import asyncio
import random
import aiohttp
import socket
from mcstatus import JavaServer

API_URL = "https://web-production-79e19.up.railway.app/log"
API_KEY = "secret123"

# Minecraft-specific tuning
WORKERS = 600
MC_TIMEOUT = 1.2  # MC servers respond fast if real

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

# Names actually common in Minecraft server naming
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
    return f"{random.choice(COMMON_NAMES)}{random.randint(1,999)}"

async def ping_minecraft(loop, address):
    """Fast Minecraft Java ping using mcstatus in executor."""
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
    if not batch:
        return
    try:
        headers = {"x-api-key": API_KEY}
        async with session.post(API_URL, json=batch, headers=headers) as resp:
            print(f"[API {resp.status}] Sent {len(batch)} servers")
    except:
        pass

async def worker(semaphore, session, results):
    loop = asyncio.get_running_loop()

    while True:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"

        async with semaphore:
            status = await ping_minecraft(loop, address)

        if not status:
            continue

        # Minecraft-specific validity checks
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
    """Batch API sender to reduce HTTP overhead (important for MC scans)"""
    while True:
        await asyncio.sleep(2)
        if results:
            batch = results[:]
            results.clear()
            await send_batch(session, batch)

async def main():
    semaphore = asyncio.Semaphore(WORKERS)
    results = []

    connector = aiohttp.TCPConnector(
        limit=WORKERS,
        ttl_dns_cache=300,  # Huge speed boost for repeated domains
        ssl=False
    )

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:

        tasks = [
            asyncio.create_task(worker(semaphore, session, results))
            for _ in range(WORKERS)
        ]

        tasks.append(asyncio.create_task(batch_sender(session, results)))

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
