import threading
import random
import time
import requests
from mcstatus import JavaServer

# ===== CONFIG =====
API_URL = "https://web-production-d205.up.railway.app/log"
API_KEY = "secret123"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

# Domains (NO Minehut)
DOMAINS = [
    "aternos.me",
    "aternos.org",
    "minefort.com",
    "server.pro",
    "ploudos.com",
    "falixsrv.net",
    "skynode.pro",
    "playit.gg",
    "mc.gg"
]

COMMON_NAMES = [
    "mc", "play", "survival", "pvp", "smp", "lobby", "hub",
    "skyblock", "bedwars", "lifesteal", "craft", "mine",
    "vanilla", "network", "earth", "fun", "official",
    "anarchy", "minigames", "pixel", "realm", "world"
]

PREFIXES = [
    "nova", "zen", "astro", "pixel", "void", "lunar",
    "apex", "fusion", "quantum", "echo", "vortex",
    "stellar", "nebula", "orbit", "vertex", "cosmic"
]

SUFFIXES = [
    "mc", "smp", "pvp", "network", "craft", "realm",
    "block", "world", "server", "hub", "survival", "online"
]

THREADS = 400   # safer for IP scanning
TIMEOUT = 2

cache = set()
lock = threading.Lock()
sent = 0
checked = 0


def random_ipv4():
    """Generate random public IPv4 (avoid obvious private ranges)"""
    while True:
        ip = ".".join(str(random.randint(1, 254)) for _ in range(4))

        # Skip private/reserved ranges (reduces useless scans)
        if ip.startswith(("10.", "127.", "192.168.", "172.16.")):
            continue
        return f"{ip}:25565"


def ai_generate_name():
    style = random.randint(0, 5)

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
    else:
        return f"{random.choice(COMMON_NAMES)}{random.choice(SUFFIXES)}"


def generate_domain_address():
    """Generate hosted server addresses (no minehut)"""
    if random.random() < 0.6:
        domain = random.choice(["aternos.me", "aternos.org"])
    else:
        domain = random.choice(DOMAINS)

    return f"{ai_generate_name()}.{domain}".lower()


def generate_target():
    """
    50% real IP servers
    50% hosted domain servers
    """
    if random.random() < 0.5:
        return random_ipv4()
    return generate_domain_address()


def send_to_api(address, online, max_players, version):
    global sent
    try:
        payload = {
            "ip": address,
            "info": {
                "players": online,
                "max_players": max_players,
                "version": version,
                "source": "hybrid-ip-domain-finder"
            }
        }

        r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            sent += 1
            print(f"[ONLINE] {address} ({online}/{max_players})")
    except:
        pass


def worker():
    global checked

    while True:
        try:
            address = generate_target()
            checked += 1

            with lock:
                if address in cache:
                    continue
                cache.add(address)

            try:
                server = JavaServer.lookup(address, timeout=TIMEOUT)
                status = server.status()
            except:
                continue  # unreachable / closed port

            if not status or not status.players:
                continue

            online = status.players.online or 0
            max_players = status.players.max or 0
            version = status.version.name if status.version else "unknown"

            # Only log real active servers
            if online > 0 and max_players > 0:
                send_to_api(address, online, max_players, version)

        except:
            continue


def main():
    print("=== Hybrid Minecraft Finder (Domains + Real IPs) ===")
    print("Scanning:")
    print("- Hosted servers (Aternos, Falix, etc.)")
    print("- Real IP servers (IPv4:25565)")
    print("Minehut: EXCLUDED")
    print(f"Threads: {THREADS}\n")

    for _ in range(THREADS):
        threading.Thread(target=worker, daemon=True).start()

    while True:
        print(
            f"[STATS] Checked: {checked} | "
            f"Online Found: {sent} | "
            f"Unique Targets: {len(cache)}"
        )
        time.sleep(5)


if __name__ == "__main__":
    main()
