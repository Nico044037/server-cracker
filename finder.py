import threading
import random
import time
import requests
from mcstatus import JavaServer

API_URL = "https://web-production-79e19.up.railway.app/log"
API_KEY = "secret123"

THREADS = 25
TIMEOUT = 2

# Toggle whitelist system
WHITELIST_ENABLED = True

# Full server whitelist (exact match)
WHITELIST_SERVERS = {
    # Example:
    # "play.minefort.com",
    # "mc.aternos.me",
}

# Domain whitelist (only log servers from these domains)
WHITELIST_DOMAINS = {
    "minefort.com",
    "aternos.me",
    "server.pro"
}

DOMAINS = [
    "minefort.com","aternos.me","server.pro","mc.gg",
    "playit.gg","duckdns.org","aternos.org","ploudos.com","falixsrv.me",
    "freemc.host","exaroton.com","omgserv.com","scalacube.pro",
    "skynode.pro","pebble.host","sparked.host","revivenode.com",
    "bloom.host","titannodes.com","envyhost.net","winternode.com",
    "apexmc.co","shockbyte.com","bisecthosting.com","ggservers.com",
    "mcprohosting.com","meloncube.net","nodecraft.games",
    "cubedhost.com","hosthorde.com","logicservers.com",
    "serverminer.com","zap-hosting.com","zaphosting.com",
    "g-portal.com","nitrado.net","pingperfect.com",
    "my.pebble.host","panel.ggservers.com","panel.bisecthosting.com",
    "panel.apexmc.co","panel.falixsrv.me",
    "no-ip.org","noip.me","ddns.net","duckdns.org","hopto.org",
    "servegame.com","serveftp.com","servehttp.com","myftp.biz",
    "dynu.net","dyndns.org","dynv6.net","afraid.org",
    "freedns.afraid.org","redirectme.net","dnsalias.net",
    "mooo.com","sytes.net","homeip.net",
    "playit.cloud","ngrok.io","ngrok-free.app","trycloudflare.com",
    "loca.lt","localto.net","tunnelto.dev","pagekite.me","bore.pub",
    "minecraft.host","minecraft.best","minecraftserver.io",
    "joinmc.link","joinserver.xyz","playmc.net","playmc.org",
    "playmc.xyz","playserver.net","playserver.org","mcnode.net","multiplayer.gg"
]

COMMON_NAMES = [
    "mc","play","survival","pvp","smp","lobby",
    "skyblock","bedwars","lifesteal","network",
    "factions","prison","creative","hardcore","anarchy",
    "kitpvp","uhc","duels","minigames","arcade",
    "practice","events","vanilla","modded","economy",
    "oneblock","earth","towny","gens","gen","opprison",
    "opskyblock","boxpvp","crystalpvp","roleplay",
    "rpg","pixelmon","cobblemon","forge","fabric",
    "hub","main","proxy","bungee","velocity","core",
    "global","central","official","public","premium",
    "craft","block","cube","mine","realm","world",
    "arena","combat","clan","wars","battle",
    "nova","zenith","cosmic","lunar","nebula",
    "test","dev","beta","alpha","season","classic",
    "reborn","plus","gg","live","online","host","server"
]

seen_servers = set()
lock = threading.Lock()

def generate_name():
    base = random.choice(COMMON_NAMES)
    return f"{base}{random.randint(1,999)}"

def is_whitelisted(address, domain):
    if not WHITELIST_ENABLED:
        return True

    address = address.lower()
    domain = domain.lower()

    # Exact server whitelist
    if address in WHITELIST_SERVERS:
        return True

    # Domain-based whitelist
    if domain in WHITELIST_DOMAINS:
        return True

    return False

def send_to_api(address, online, max_players, version):
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
        r = requests.post(API_URL, json=payload, headers=headers, timeout=5)
        print(f"[API {r.status_code}] {address}")
    except Exception as e:
        print(f"[API FAILED] {address} -> {e}")

def scan():
    while True:
        try:
            name = generate_name()
            domain = random.choice(DOMAINS)
            address = f"{name}.{domain}".lower()

            # Whitelist gate (MAIN FIX)
            if not is_whitelisted(address, domain):
                continue

            # Pre duplicate check (fast)
            with lock:
                if address in seen_servers:
                    continue

            server = JavaServer.lookup(address, timeout=TIMEOUT)
            status = server.status()

            if not status:
                continue

            if status.players.max == 0:
                continue

            version = status.version.name if status.version else "unknown"

            # Final duplicate protection (thread-safe)
            with lock:
                if address in seen_servers:
                    continue
                seen_servers.add(address)

            print(f"[LOGGED] {address} | {status.players.online}/{status.players.max} | {version}")

            send_to_api(address, status.players.online, status.players.max, version)

        except Exception:
            continue  # never kill thread

def main():
    for _ in range(THREADS):
        threading.Thread(target=scan, daemon=True).start()

    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()
