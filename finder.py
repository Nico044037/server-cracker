import threading
import random
import time
import requests
from mcstatus import JavaServer

API_URL = "https://web-production-79e19.up.railway.app/logs"
API_KEY = "secret123"  # your key

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"  # Most common format
    # If your API uses x-api-key instead, tell me and I'll switch it
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


def send_to_api(address, online, max_players):
    global sent
    try:
        payload = {
            "address": address,
            "online_players": online,
            "max_players": max_players,
            "timestamp": int(time.time())
        }

        r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)

        if r.status_code in (200, 201):
            sent += 1
            print(f"[SENT] {address} ({online}/{max_players})")
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

            # Skip fake placeholder hosts
            if online == 0 and max_players == 0:
                continue
            if max_players == 0:
                continue

            with lock:
                if address not in cache:
                    cache.add(address)
                    send_to_api(address, online, max_players)

        except:
            pass


def main():
    print("=== API-ONLY Minecraft Scanner (AUTH MODE) ===")
    print(f"API: {API_URL}")
    print("Auth: Bearer API Key enabled")
    print(f"Threads: {THREADS}")
    print("Local saving: DISABLED\n")

    for _ in range(THREADS):
        threading.Thread(target=worker, daemon=True).start()

    while True:
        print(f"[STATS] Checked: {checked} | Sent: {sent} | Unique: {len(cache)}")
        time.sleep(5)


if __name__ == "__main__":
    main()
