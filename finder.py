import threading
import random
import time
import requests
from mcstatus import JavaServer

API_URL = "https://web-production-79e19.up.railway.app/log"  # IMPORTANT: /log not /logs
API_KEY = "secret123"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY  # MUST match your FastAPI header
}

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

cache = set()
lock = threading.Lock()
sent = 0
checked = 0


def generate_name():
    base = random.choice(COMMON_NAMES)
    return random.choice([
        base,
        f"{base}{random.randint(1,999)}",
        f"{base}{random.randint(1,99)}",
        f"play{base}",
        f"{base}mc",
        f"{random.choice(COMMON_NAMES)}{random.randint(1,999)}",
    ])


def send_to_api(address, online, max_players, version):
    global sent
    try:
        payload = {
            "ip": address,  # your API expects "ip"
            "info": {
                "players": online,
                "max_players": max_players,
                "version": version,
                "source": "finder"
            }
        }

        r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)

        if r.status_code == 200:
            sent += 1
            print(f"[LOGGED] {address} ({online}/{max_players})")
        else:
            print(f"[API ERROR] {r.status_code} -> {r.text}")

    except Exception as e:
        print(f"[REQUEST FAILED] {e}")


def worker():
    global checked

    while True:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"
        checked += 1

        try:
            server = JavaServer.lookup(address, timeout=TIMEOUT)
            status = server.status()

            online = status.players.online
            max_players = status.players.max
            version = status.version.name if status.version else "unknown"

            # Ignore placeholder servers (0/0)
            if online == 0 and max_players == 0:
                continue
            if max_players == 0:
                continue

            with lock:
                if address not in cache:
                    cache.add(address)
                    send_to_api(address, online, max_players, version)

        except:
            pass


def main():
    print("=== Minecraft Finder (API MATCH MODE) ===")
    print(f"Endpoint: {API_URL}")
    print("Auth Header: x-api-key")
    print("JSON Format: MATCHED to your FastAPI")
    print(f"Threads: {THREADS}\n")

    for _ in range(THREADS):
        threading.Thread(target=worker, daemon=True).start()

    while True:
        print(f"[STATS] Checked: {checked} | Logged: {sent} | Unique: {len(cache)}")
        time.sleep(5)


if __name__ == "__main__":
    main()
