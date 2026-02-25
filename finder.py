import threading
import random
import time
import requests
import os
from mcstatus import JavaServer

# ================== CONFIG ==================
API_URL = os.getenv("API_URL", "https://web-production-79e19.up.railway.app/log")
THREADS = int(os.getenv("THREADS", 25))
TIMEOUT = 2
DELAY = 0.05

DOMAINS = [
    "minefort.com","aternos.me","aternos.org","server.pro","zapto.org","mc.gg",
    "playit.gg","playit.cloud","play.hosting","apexmc.co","shockbyte.com",
    "bisecthosting.com","ggservers.com","scalacube.com","scalacube.pro",
    "nodecraft.com","nodecraft.games","cubedhost.com","hosthorde.com",
    "mcprohosting.com","meloncube.net","serverminer.com","sparked.host",
    "revivenode.com","bloom.host","titannodes.com","envyhost.net","winternode.com",
    "zaphosting.com","zap-hosting.com","g-portal.com","vivalacloud.net",
    "pebble.host","skynode.pro","falixsrv.me","freemc.host","ploudos.com",
    "minehut.gg","minehut.com","exaroton.com","omgserv.com","logicservers.com",
    "serverblend.com","mc-host24.de","host-unlimited.de","craftserve.pl",
    "nitrado.net","pingperfect.com","low.ms","dedimc.io","ultramc.com","foxomy.com",
    "no-ip.org","noip.me","ddns.net","duckdns.org","hopto.org","servegame.com",
    "serveftp.com","servehttp.com","myftp.biz","dynu.net","ddnsfree.com",
    "dyndns.org","dynv6.net","freedns.afraid.org","afraid.org","redirectme.net",
    "dnsalias.net","mooo.com","sytes.net","myqnapcloud.com","homeip.net",
    "ngrok.io","ngrok-free.app","trycloudflare.com","loca.lt","localto.net",
    "tunnelto.dev","pagekite.me","bore.pub","cloudflared.com","tailscale.net",
    "zerotier.com","herokuapp.com","onrender.com","railway.app","fly.dev",
    "vercel.app","replit.dev","glitch.me","firebaseapp.com","azurewebsites.net",
    "amazonaws.com","linode.com","vultr.com","contabo.com","hetzner.cloud",
    "ovh.net","ovhcloud.com","netcup.net","strato.de","ionos.com",
    "mcserv.me","mcserver.ws","minecraft.best","minecraft.host","joinmc.link",
    "joinserver.xyz","joinmc.net","playmc.at","playmc.me","playmc.net",
    "playmc.org","playmc.xyz","playminecraft.net","playserver.net",
    "playserver.xyz","mc.to","mc.lol","mc.host","mc.fun","mc.world",
    "mc.live","mc.one","mc.pro","mc.network"
]

COMMON_NAMES = [
    "mc","play","survival","pvp","smp","lobby","hub",
    "skyblock","bedwars","lifesteal","mine","craft",
    "vanilla","network","earth","fun","anarchy","pixel",
    "realm","world","hardcore","creative","minigames"
]

sent_cache = set()
lock = threading.Lock()

def generate_name():
    base = random.choice(COMMON_NAMES)
    return random.choice([
        base,
        f"{base}{random.randint(1,999)}",
        f"{base}{random.randint(1,99)}",
        f"play{base}",
        f"{base}mc",
        f"{random.choice(COMMON_NAMES)}{random.randint(1,999)}"
    ])

def send_to_api(address, online, max_players, version):
    if address in sent_cache:
        return

    payload = {
        "ip": address,
        "info": {
            "players": online,
            "max_players": max_players,
            "version": version,
            "timestamp": time.time(),
            "source": "railway-scanner"
        }
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=5)
        if r.status_code == 200:
            with lock:
                sent_cache.add(address)
            print(f"[API SENT] {address} ({online}/{max_players})")
        else:
            print(f"[API ERROR {r.status_code}] {address}")
    except Exception as e:
        print(f"[API FAILED] {address} -> {e}")

def check_server():
    while True:
        try:
            name = generate_name()
            domain = random.choice(DOMAINS)
            address = f"{name}.{domain}"

            server = JavaServer.lookup(address, timeout=TIMEOUT)
            status = server.status()

            online = status.players.online
            max_players = status.players.max

            # Ignore fake placeholder servers (0/0)
            if online == 0 and max_players == 0:
                continue

            if max_players == 0:
                continue

            version = status.version.name if status.version else "unknown"

            print(f"[FOUND] {address} | {online}/{max_players} | {version}")
            send_to_api(address, online, max_players, version)

            time.sleep(DELAY)

        except:
            pass

def main():
    print("=== Railway Minecraft Finder (API Mode) ===")
    print(f"API: {API_URL}")
    print(f"Threads: {THREADS}")
    print(f"Domains Loaded: {len(DOMAINS)}")
    print("Running 24/7...\n")

    for _ in range(THREADS):
        threading.Thread(target=check_server, daemon=True).start()

    while True:
        time.sleep(15)

if __name__ == "__main__":
    main()
