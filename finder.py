import threading
import random
import time
import requests
from mcstatus import JavaServer

# Your existing API endpoint
API_URL = "https://web-production-79e19.up.railway.app/logs"

DOMAINS = [
    "minefort.com", "aternos.me", "server.pro", "zapto.org",
    "mc.gg", "playit.gg", "play.hosting", "minehut.gg",
    "aternos.org", "freemcserver.net", "falixsrv.net",
    "ploudos.com", "skynode.pro", "serverminer.com",
    "mcserver.ws", "mcserver.us", "mcserver.io",
    "ggservers.com", "scalacube.com", "holy.gg",
    "hosthorde.net", "cubedhost.com"
]

COMMON_NAMES = [
    "mc", "play", "survival", "pvp", "smp", "lobby", "hub",
    "skyblock", "bedwars", "lifesteal", "craft", "mine",
    "vanilla", "network", "earth", "fun", "pro", "official",
    "test", "server", "minecraft", "anarchy", "minigames",
    "pixel", "realm", "world", "hardcore", "creative"
]

THREADS = 40
TIMEOUT = 2

found_cache = set()
lock = threading.Lock()
total_sent = 0
total_checked = 0


def generate_name():
    base = random.choice(COMMON_NAMES)
    patterns = [
        base,
        f"{base}{random.randint(1, 999)}",
        f"{base}{random.randint(1, 99)}",
        f"play{base}",
        f"{base}mc",
        f"{random.choice(COMMON_NAMES)}{random.randint(1, 999)}",
    ]
    return random.choice(patterns)


def send_to_api(address, online, max_players):
    global total_sent
    try:
        payload = {
            "address": address,
            "online_players": online,
            "max_players": max_players,
            "timestamp": int(time.time())
        }
        requests.post(API_URL, json=payload, timeout=3)
        total_sent += 1
        print(f"[SENT] {address} ({online}/{max_players})")
    except Exception as e:
        print(f"[API ERROR] {e}")


def worker():
    global total_checked

    while True:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"
        total_checked += 1

        try:
            server = JavaServer.lookup(address, timeout=TIMEOUT)
            status = server.status()

            online = status.players.online
            max_players = status.players.max

            # Ignore fake placeholder servers (0/0)
            if online == 0 and max_players == 0:
                return

            if max_players == 0:
                return

            with lock:
                if address not in found_cache:
                    found_cache.add(address)
                    send_to_api(address, online, max_players)

        except:
            # Offline / invalid server
            pass


def main():
    print("=== Minecraft Server Finder (API ONLY MODE) ===")
    print(f"Sending results ONLY to: {API_URL}")
    print(f"Threads: {THREADS}")
    print("Local file saving: DISABLED")
    print("Press CTRL+C to stop.\n")

    for _ in range(THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    while True:
        print(f"[STATS] Checked: {total_checked} | Sent: {total_sent} | Cached: {len(found_cache)}")
        time.sleep(5)


if __name__ == "__main__":
    main()
