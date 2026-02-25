import threading
import random
import time
import requests
from mcstatus import JavaServer

API_URL = "https://web-production-79e19.up.railway.app/log"
API_KEY = "secret123"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

# Focused + realistic hosting domains (including Aternos priority)
DOMAINS = [
    "aternos.me",
    "aternos.org",
    "minefort.com",
    "server.pro",
    "mc.gg",
    "playit.gg",
    "minehut.gg",
    "ploudos.com",
    "falixsrv.net",
    "skynode.pro",
    "serverminer.com",
    "ggservers.com"
]

# Base seed names (used by AI generator)
COMMON_NAMES = [
    "mc", "play", "survival", "pvp", "smp", "lobby", "hub",
    "skyblock", "bedwars", "lifesteal", "craft", "mine",
    "vanilla", "network", "earth", "fun", "official",
    "anarchy", "minigames", "pixel", "realm", "world",
    "hardcore", "creative", "gens", "practice"
]

# AI-style word components (dynamic expansion)
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
    "core", "online", "plus", "live"
]

THREADS = 40
TIMEOUT = 2

cache = set()
lock = threading.Lock()
sent = 0
checked = 0


def ai_generate_name():
    """
    AI-style smart name generator (much better than static lists)
    """
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


def generate_domain():
    """
    Smart domain selection (bias toward Aternos for better hits)
    """
    if random.random() < 0.6:
        return random.choice(["aternos.me", "aternos.org"])
    return random.choice(DOMAINS)


def send_to_api(address, online, max_players, version):
    global sent
    try:
        payload = {
            "ip": address,
            "info": {
                "players": online,
                "max_players": max_players,
                "version": version,
                "source": "ai-finder"
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
        try:
            name = ai_generate_name()
            domain = generate_domain()
            address = f"{name}.{domain}".lower()

            checked += 1

            # Prevent duplicate checks (reduces API spam & log filling)
            with lock:
                if address in cache:
                    continue
                cache.add(address)

            server = JavaServer.lookup(address, timeout=TIMEOUT)
            status = server.status()

            online = status.players.online if status.players else 0
            max_players = status.players.max if status.players else 0
            version = status.version.name if status.version else "unknown"

            # Skip empty/placeholder servers
            if online == 0 and max_players == 0:
                continue
            if max_players == 0:
                continue

            send_to_api(address, online, max_players, version)

        except:
            pass


def main():
    print("=== AI Minecraft Finder (Railway API Mode) ===")
    print(f"Endpoint: {API_URL}")
    print("Auth Header: x-api-key")
    print("AI Name Generation: ENABLED")
    print("Aternos Priority: ENABLED")
    print(f"Threads: {THREADS}\n")

    for _ in range(THREADS):
        threading.Thread(target=worker, daemon=True).start()

    while True:
        print(f"[STATS] Checked: {checked} | Logged: {sent} | Unique Generated: {len(cache)}")
        time.sleep(5)


if __name__ == "__main__":
    main()
