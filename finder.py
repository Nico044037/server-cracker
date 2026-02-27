import threading
import random
import time
import requests
from mcstatus import JavaServer

API_URL = "http://127.0.0.1:8000/log"
API_KEY = "secret123"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

# ONLY Minehut
DOMAIN = "aternos.me"

COMMON_NAMES = [
    "mc", "play", "survival", "pvp", "smp", "lobby", "hub",
    "skyblock", "bedwars", "lifesteal", "craft", "mine",
    "vanilla", "network", "earth", "fun", "official",
    "anarchy", "minigames", "pixel", "realm", "world",
    "hardcore", "creative", "gens", "practice"
]

PREFIXES = [
    "nova", "zen", "astro", "pixel", "void", "lunar",
    "apex", "fusion", "quantum", "echo", "vortex",
    "stellar", "nebula", "orbit", "vertex", "cosmic",
    "alpha", "omega", "prime", "ultra", "hyper"
]

SUFFIXES = [
    "mc", "smp", "pvp", "network", "craft", "realm",
    "block", "world", "server", "hub", "lifesteal",
    "skyblock", "survival", "gens", "practice",
    "core", "online", "live"
]

THREADS = 200  # 800 is overkill and may get you rate-limited
TIMEOUT = 3    # 0 can hang forever

cache = set()
lock = threading.Lock()
sent = 0
checked = 0


def ai_generate_name():
    style = random.randint(0, 6)

    if style == 0:
        return random.choice(COMMON_NAMES)
    elif style == 1:
        return f"{random.choice(COMMON_NAMES)}{random.randint(1, 999)}"
    elif style == 2:
        return f"{random.choice(PREFIXES)}{random.choice(SUFFIXES)}"
    elif style == 3:
        return f"play{random.choice(COMMON_NAMES)}"
    elif style == 4:
        return f"{random.choice(PREFIXES)}{random.choice(COMMON_NAMES)}"
    elif style == 5:
        return f"{random.choice(COMMON_NAMES)}{random.choice(SUFFIXES)}"
    else:
        return f"{random.choice(PREFIXES)}{random.choice(SUFFIXES)}{random.randint(1,99)}"


def generate_minehut_address():
    return f"{ai_generate_name()}.{DOMAIN}".lower()


def send_to_api(address, online, max_players, version):
    global sent
    try:
        payload = {
            "ip": address,
            "info": {
                "players": online,
                "max_players": max_players,
                "version": version,
                "source": "minehut-finder"
            }
        }

        r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)

        if r.status_code == 200:
            sent += 1
            print(f"[LOGGED ONLINE] {address} ({online}/{max_players})")
        else:
            print(f"[API ERROR] {r.status_code} -> {r.text}")

    except Exception as e:
        print(f"[REQUEST FAILED] {e}")


def worker():
    global checked

    while True:
        try:
            address = generate_minehut_address()
            checked += 1

            # Prevent duplicate checks
            with lock:
                if address in cache:
                    continue
                cache.add(address)

            server = JavaServer.lookup(address, timeout=TIMEOUT)
            status = server.status()

            # Extract player info safely
            online = status.players.online if status.players else 0
            max_players = status.players.max if status.players else 0
            version = status.version.name if status.version else "unknown"

            # ONLY log real online servers (at least 1 player)
            if online <= 0:
                return

            # Extra safeguard against placeholder/ghost servers
            if max_players <= 0:
                return

            send_to_api(address, online, max_players, version)

        except:
            pass


def main():
    print("=== Minehut Online Server Finder ===")
    print(f"Endpoint: {API_URL}")
    print("Domain Filter: minehut.gg ONLY")
    print("Logging: ONLINE servers only (players > 0)")
    print(f"Threads: {THREADS}\n")

    for _ in range(THREADS):
        threading.Thread(target=worker, daemon=True).start()

    while True:
        print(f"[STATS] Checked: {checked} | Logged Online: {sent} | Unique: {len(cache)}")
        time.sleep(5)


if __name__ == "__main__":
    main()
