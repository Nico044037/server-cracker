import random
import threading
import time
from fastapi import FastAPI
from mcstatus import JavaServer

app = FastAPI(title="Minecraft Server Finder API")

# Expanded host list
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

found_servers = {}
lock = threading.Lock()
scanner_running = False
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


def check_server():
    global total_checked

    while scanner_running:
        name = generate_name()
        domain = random.choice(DOMAINS)
        address = f"{name}.{domain}"

        total_checked += 1

        try:
            server = JavaServer.lookup(address, timeout=TIMEOUT)
            status = server.status()

            online = status.players.online
            max_players = status.players.max

            # Ignore placeholder servers (0/0)
            if online == 0 and max_players == 0:
                return

            if max_players == 0:
                return

            with lock:
                if address not in found_servers:
                    found_servers[address] = {
                        "address": address,
                        "online_players": online,
                        "max_players": max_players,
                        "timestamp": int(time.time())
                    }
                    print(f"[FOUND] {address} {online}/{max_players}")

        except:
            pass


def scanner_loop():
    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)


def worker():
    while scanner_running:
        check_server()


@app.on_event("startup")
def auto_start():
    global scanner_running
    scanner_running = True
    threading.Thread(target=scanner_loop, daemon=True).start()
    print("Scanner started automatically")


@app.get("/")
def root():
    return {
        "status": "running",
        "servers_found": len(found_servers),
        "total_checked": total_checked,
        "threads": THREADS
    }


@app.get("/logs")
def get_logs():
    return {
        "count": len(found_servers),
        "servers": list(found_servers.values())
    }


@app.get("/stats")
def stats():
    return {
        "scanner_running": scanner_running,
        "servers_found": len(found_servers),
        "total_checked": total_checked,
        "domains": len(DOMAINS),
        "threads": THREADS
    }


@app.post("/start")
def start_scanner():
    global scanner_running
    if not scanner_running:
        scanner_running = True
        threading.Thread(target=scanner_loop, daemon=True).start()
        return {"message": "Scanner started"}
    return {"message": "Scanner already running"}


@app.post("/stop")
def stop_scanner():
    global scanner_running
    scanner_running = False
    return {"message": "Scanner stopped"}
