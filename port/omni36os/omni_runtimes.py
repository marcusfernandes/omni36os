#!/usr/bin/env python3
"""Omni36OS — runtimes do PortMaster entregues pelo Omni36OS.

A lista fica em runtimes.txt (vem com cada atualização do Omni). sync() compara cada um com o
índice do PortMaster (ports.json da release mais nova: URL, md5 e tamanho) e baixa só o que
falta ou mudou, conferindo o md5. O md5 local fica guardado (tamanho + data) para não reler
arquivos grandes a cada vez.

No console roda em segundo plano pelo omni_atalho.py (Runner), presa ao Wi-Fi: confere ao
conectar (também depois de uma atualização, que reinicia o serviço) e a cada 6 h com rede;
para no meio se um jogo abrir.
Na imagem: omni_runtimes.py --dest <pasta> deixa a pasta igual à lista (apaga o que saiu).
"""
import hashlib
import json
import os
import shutil
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LIST = os.path.join(HERE, "runtimes.txt")
LIBS = "/roms/tools/PortMaster/libs"
INDEX = "https://github.com/PortsMaster/PortMaster-New/releases/latest/download/ports.json"
CACHE = ".omni36os-md5.json"
ARCH = "aarch64"
CHUNK = 1 << 20
SPARE = 64 << 20                       # folga no cartão além do arquivo


class Stopped(Exception):
    pass


def wanted():
    try:
        with open(LIST) as f:
            return [n.strip() for n in f if n.strip() and not n.startswith("#")]
    except OSError:
        return []


def index():
    """nome -> {url, md5, size} para aarch64."""
    req = urllib.request.Request(INDEX, headers={"User-Agent": "Omni36OS"})
    with urllib.request.urlopen(req, timeout=30) as r:
        utils = json.load(r).get("utils", {})
    return {u["runtime_name"]: u for u in utils.values() if u.get("runtime_arch") == ARCH and u.get("url")}


def _md5(path, cache):
    st = os.stat(path)
    key = [st.st_size, int(st.st_mtime)]
    hit = cache.get(os.path.basename(path))
    if hit and hit[:2] == key:
        return hit[2]
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(CHUNK), b""):
            h.update(b)
    cache[os.path.basename(path)] = key + [h.hexdigest()]
    return h.hexdigest()


def _download(info, dest, stop):
    tmp = dest + ".part"
    h = hashlib.md5()
    req = urllib.request.Request(info["url"], headers={"User-Agent": "Omni36OS"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as fo:
            for b in iter(lambda: r.read(CHUNK), b""):
                if stop():
                    raise Stopped()
                fo.write(b)
                h.update(b)
        if h.hexdigest() != info["md5"]:
            raise ValueError("md5 não confere")
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def sync(libs=LIBS, stop=lambda: False, prune=False, log=print):
    """Deixa os runtimes da lista em dia em `libs`. Devolve (baixados, falhas)."""
    os.makedirs(libs, exist_ok=True)
    idx = index()
    cpath = os.path.join(libs, CACHE)
    try:
        with open(cpath) as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = {}
    got, bad = [], []
    names = wanted()
    try:
        for n in names:
            info = idx.get(n)
            if not info:
                bad.append(f"{n}: fora do índice do PortMaster")
                continue
            dest = os.path.join(libs, n)
            if os.path.isfile(dest) and _md5(dest, cache) == info["md5"]:
                continue
            free = shutil.disk_usage(libs).free + (os.path.getsize(dest) if os.path.isfile(dest) else 0)
            if free < info["size"] + SPARE:
                bad.append(f"{n}: sem espaço")
                continue
            log(f"baixando {n} ({info['size'] >> 20} MB)")
            try:
                _download(info, dest, stop)
                _md5(dest, cache)
                got.append(n)
            except Stopped:
                raise
            except Exception as e:
                bad.append(f"{n}: {e}")
    except Stopped:
        log("parado: um jogo abriu")
    finally:
        with open(cpath, "w") as f:
            json.dump(cache, f)
    if prune:                          # só na pasta da imagem: o console guarda o que o usuário pôs
        for f in os.listdir(libs):
            if f.endswith(".squashfs") and f not in names:
                os.remove(os.path.join(libs, f))
                log(f"removido {f}")
    return got, bad


def online():
    """Há rota padrão (Wi-Fi ou rede USB conectados)? Leitura direta, sem chamar programas."""
    try:
        with open("/proc/net/route") as f:
            return any(line.split()[1] == "00000000" for line in f.readlines()[1:] if line.split())
    except OSError:
        return False


class Runner:
    """Sincronização em segundo plano no serviço de atalhos, presa ao Wi-Fi: confere ao conectar,
    depois a cada 6 h enquanto houver rede. Falhou com rede: tenta de novo em 10 min. Jogo aberto:
    espera ele fechar."""
    CHECK, EVERY, RETRY = 30, 6 * 3600, 600

    def __init__(self, busy):
        self.busy = busy               # função: há jogo aberto?
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        was, due = False, 0.0
        while True:
            time.sleep(self.CHECK)
            now = time.monotonic()
            if not online():
                was = False
                continue
            if not was:                # acabou de conectar
                was, due = True, now
            if now < due or self.busy():
                continue
            try:
                got, bad = sync(stop=self.busy, log=lambda m: print(f"runtimes: {m}", file=sys.stderr, flush=True))
                print(f"runtimes: conferidos, {len(got)} baixado(s); {'; '.join(bad) or 'sem falhas'}",
                      file=sys.stderr, flush=True)
                due = now if self.busy() else now + self.EVERY   # parou por um jogo: segue quando ele fechar
            except Exception as e:     # rede sem internet, GitHub fora: tenta logo
                print(f"runtimes: {e}", file=sys.stderr, flush=True)
                due = now + self.RETRY


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--dest":
        got, bad = sync(sys.argv[2], prune=True)
        print(f"{len(got)} baixado(s)" + (f"; falhas: {'; '.join(bad)}" if bad else ""))
        sys.exit(1 if bad else 0)
    print(__doc__)
