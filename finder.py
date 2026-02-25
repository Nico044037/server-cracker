import asyncio
import random
import aiohttp
from mcstatus import JavaServer
import socket

API_URL = "https://web-production-79e19.up.railway.app/log"
API_KEY = "secret123"

# Higher = faster (be careful with your network limits)
CONCURRENCY = 500
TIMEOUT = 2

DOMAINS = [
    "minefort.com","aternos.me","server.pro","mc.gg",
    "playit.gg","duckdns.org","aternos.org","ploudos.com",
    "falixsrv.me","freemc.host","exaroton.com","omgserv.com",
    "scalacube.pro","skynode.pro","pebble.host","sparked.host",
    "revivenode.com","bloom.host","titannodes.com","envyhost.net",
    "winternode.com","apexmc.co","shockbyte.com","bisecthosting.com",
    "ggservers.com","mcprohosting.com","meloncube.net","nodecraft.games",
    "cubedhost.com","hosthorde.com","logicservers.com","serverminer.com",
    "zap-hosting.com","g-portal.com","nitrado.net","pingperfect.com",
    "noip.me","ddns.net","hopto.org","servegame.com","dynu.net",
    "ngrok.io","trycloudflare.com","loca.lt","pagekite.me",
    "minecraft.host","minecraft.best","minecraftserver.io",
    "joinmc.link","playmc.net","playserver.net","multiplayer.gg"
]

COMMON_NAMES = [
    "mc","play","survival","pvp","smp","lobby","skyblock",
    "bedwars","lifesteal","network","factions","prison",
    "creative","anarchy","kitpvp","duels","minigames",
    "practice","vanilla","modded","economy","oneblock",
    "towny","pixelmon","forge","fabric","hub","main",
    "proxy","core","global","official","public","premium",
    "craft","cube","mine","realm","world","kingdom",
    "empire","nova","zenith","cosmic","nebula","vortex",
    "test","dev","beta","alpha","classic","reborn","gg","live"
]

def generate_name():
    return f"{random.choice(COMMON_NAMES)}{random.randint(1,999)}"

async def send_to_api(session, address, online, max_players, version):
    payload = {
        "ip": address,
        "info": {
            "players": online,
            "max_players": max_players,
            "version": version,
            "source": "railway-finder"
        }
    }
    headers = {"x-api-key": API_KEY}

    try:
        async with session.post(API_URL, json=payload, headers=headers, timeout=5) as r:
            print(f"[API {r.status}] {address}")
    except:
        pass

async def scan_worker(session, semaphore):
    loop = asyncio.get_event_loop()

    while True:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"

        async with semaphore:
            try:
                # Run blocking mcstatus in thread pool (VERY important for speed)
                server = await loop.run_in_executor(
                    None,
                    lambda: JavaServer.lookup(address)
                )

                status = await loop.run_in_executor(
                    None,
                    lambda: server.status(timeout=TIMEOUT)
                )

                if not status or status.players.max <= 0:
                    continue

                version = status.version.name if status.version else "unknown"
                online = status.players.online
                max_players = status.players.max

                print(f"[FOUND] {address} ({online}/{max_players})")

                await send_to_api(session, address, online, max_players, version)

            except (TimeoutError, ConnectionError, OSError, socket.gaierror):
                pass
            except Exception:
                pass

async def main():
    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        semaphore = asyncio.Semaphore(CONCURRENCY)

        tasks = [
            asyncio.create_task(scan_worker(session, semaphore))
            for _ in range(CONCURRENCY)
        ]

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
