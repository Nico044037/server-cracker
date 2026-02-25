import threading
import random
import time
import requests
from mcstatus import JavaServer
from socket import gaierror

API_URL = "https://web-production-79e19.up.railway.app/log"
API_KEY = "secret123"

THREADS = 25
TIMEOUT = 2
DELAY = 0.2  # Prevents CPU/DNS hammering

DOMAINS = list(set([
    "minefort.com","aternos.me","server.pro","mc.gg",
    "playit.gg","duckdns.org","aternos.org","ploudos.com",
    "falixsrv.me","freemc.host","exaroton.com","omgserv.com",
    "scalacube.pro","skynode.pro","pebble.host","sparked.host",
    "revivenode.com","bloom.host","titannodes.com","envyhost.net",
    "winternode.com","apexmc.co","shockbyte.com","bisecthosting.com",
    "ggservers.com","mcprohosting.com","meloncube.net","nodecraft.games",
    "cubedhost.com","hosthorde.com","logicservers.com","serverminer.com",
    "zap-hosting.com","zaphosting.com","g-portal.com","nitrado.net",
    "pingperfect.com","my.pebble.host","panel.ggservers.com",
    "panel.bisecthosting.com","panel.apexmc.co","panel.falixsrv.me",
    "no-ip.org","noip.me","ddns.net","hopto.org","servegame.com",
    "serveftp.com","servehttp.com","myftp.biz","dynu.net","dyndns.org",
    "dynv6.net","afraid.org","freedns.afraid.org","redirectme.net",
    "dnsalias.net","mooo.com","sytes.net","homeip.net","playit.cloud",
    "ngrok.io","ngrok-free.app","trycloudflare.com","loca.lt",
    "localto.net","tunnelto.dev","pagekite.me","bore.pub",
    "minecraft.host","minecraft.best","minecraftserver.io","joinmc.link",
    "joinserver.xyz","playmc.net","playmc.org","playmc.xyz",
    "playserver.net","playserver.org","mcnode.net","multiplayer.gg"
]))

COMMON_NAMES = [
    "mc","play","survival","pvp","smp","lobby","skyblock","bedwars",
    "lifesteal","network","factions","prison","creative","hardcore",
    "anarchy","kitpvp","uhc","duels","minigames","arcade","practice",
    "events","vanilla","modded","economy","oneblock","earth","towny",
    "gens","gen","opprison","opskyblock","boxpvp","crystalpvp",
    "roleplay","rpg","pixelmon","cobblemon","forge","fabric",
    "hub","main","proxy","bungee","velocity","core","global",
    "central","official","public","premium","craft","cube","mine",
    "realm","world","kingdom","empire","legacy","origins","arena",
    "clan","wars","battle","ranked","nova","zenith","cosmic",
    "nebula","eclipse","orbit","quantum","vertex","apex","pulse",
    "fusion","echo","vortex","test","dev","beta","alpha","new",
    "classic","reborn","plus","gg","live","online","server"
]

def generate_name():
    return f"{random.choice(COMMON_NAMES)}{random.randint(1, 999)}"

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
    except requests.RequestException as e:
        print(f"[API ERROR] {address} -> {e}")

def scan(thread_id):
    while True:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"

        try:
            server = JavaServer.lookup(address)
            status = server.status(timeout=TIMEOUT)

            # Skip invalid/empty servers
            if not status or status.players.max <= 0:
                time.sleep(DELAY)
                continue

            version = status.version.name if status.version else "unknown"
            online = status.players.online
            max_players = status.players.max

            print(f"[T{thread_id}] FOUND: {address} ({online}/{max_players})")
            send_to_api(address, online, max_players, version)

        except (TimeoutError, ConnectionError, OSError, gaierror):
            pass  # Normal for random DNS scanning
        except Exception as e:
            print(f"[ERROR] {address} -> {e}")

        time.sleep(DELAY)

def main():
    for i in range(THREADS):
        t = threading.Thread(target=scan, args=(i,), daemon=True)
        t.start()

    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()
