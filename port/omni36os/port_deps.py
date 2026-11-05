#!/usr/bin/env python3
"""Omni36OS — runtimes do PortMaster que um port pede, antes de ele abrir.

Lê o script do port e acha os runtimes (squashfs) que ele cita: o nome direto
("mono-6.12.0.122-aarch64.squashfs") ou a variável runtime="frt_3.5.2". Os que
não estão em /roms/tools/PortMaster/libs são baixados do PortMaster (URL e md5
do config/runtimes.json), com a barra de progresso do omni_dialog na tela. Sem
internet, o usuário copia o arquivo para essa pasta pelo PC.

Ports antigos (TMNT, jogos em Mono/FNA) só montam o arquivo e não chamam o
runtime_check do PortMaster; ports de fora do PortMaster fazem o mesmo.

Uso: port_deps.py "/roms2/ports/Jogo.sh"   (código 0: tudo no lugar)
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import omni_i18n
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LIBS = "/roms/tools/PortMaster/libs"
RUNTIMES_JSON = "/roms/tools/PortMaster/config/runtimes.json"
ARCH = "aarch64"
CHUNK = 1 << 20

NAME_RE = re.compile(r"([A-Za-z0-9_.+-]+\.squashfs)")
VAR_RE = re.compile(r"""\bruntime=["']?([A-Za-z0-9_.+-]+)["']?""")


def load_known():
    try:
        with open(RUNTIMES_JSON) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def wanted(script, known):
    """Runtimes citados no script que o PortMaster conhece."""
    try:
        text = open(script, errors="ignore").read()
    except OSError:
        return []
    names = set(NAME_RE.findall(text))
    names |= {n if n.endswith(".squashfs") else n + ".squashfs" for n in VAR_RE.findall(text)}
    return [n for n in sorted(names) if n in known]


class Gauge:
    """Barra do omni_dialog (--gauge); sem tela, segue em silêncio."""

    def __init__(self, title):
        try:
            self.p = subprocess.Popen(
                [sys.executable, "-B", os.path.join(HERE, "omni_dialog.py"), "--title", title,
                 "--gauge", "", "0", "0", "0"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            self.p = None
        self.last = None

    def set(self, pct, msg):
        if not self.p or (pct, msg) == self.last:
            return
        self.last = (pct, msg)
        try:
            self.p.stdin.write(f"XXX\n{int(pct)}\n{msg}\nXXX\n".encode())
            self.p.stdin.flush()
        except OSError:
            self.p = None

    def close(self):
        if self.p:
            try:
                self.p.stdin.close()
                self.p.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                self.p.kill()


def message(text):
    subprocess.run([sys.executable, "-B", os.path.join(HERE, "omni_dialog.py"), "--title", omni_i18n._("deps_title"),
                    "--msgbox", text, "0", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def download(info, dest, label, gauge):
    tmp = dest + ".part"
    md5 = hashlib.md5()
    req = urllib.request.Request(info["url"], headers={"User-Agent": "Omni36OS"})
    with urllib.request.urlopen(req, timeout=30) as r, open(tmp, "wb") as fo:
        total = int(r.headers.get("Content-Length") or info.get("size") or 1)
        done = 0
        for data in iter(lambda: r.read(CHUNK), b""):
            fo.write(data)
            md5.update(data)
            done += len(data)
            gauge.set(done * 100 // total, omni_i18n._("deps_downloading").format(label=label, done=done >> 20, total=total >> 20))
    if info.get("md5") and md5.hexdigest() != info["md5"]:
        os.remove(tmp)
        raise ValueError(omni_i18n._("deps_corrupt_download"))
    os.replace(tmp, dest)


def main(script):
    known = load_known()
    missing = [n for n in wanted(script, known) if not os.path.isfile(os.path.join(LIBS, n))]
    if not missing:
        return 0
    os.makedirs(LIBS, exist_ok=True)
    gauge = Gauge(omni_i18n._("deps_port_title"))
    falhas = []
    for n in missing:
        dest = os.path.join(LIBS, n)
        label = known.get(n, {}).get("name") or n[:-len(".squashfs")]
        try:
            info = known.get(n, {}).get("remote", {}).get(ARCH)
            if info:
                download(info, dest, label, gauge)
            else:
                raise LookupError(omni_i18n._("deps_missing_device_runtime"))
        except Exception as e:                       # o port abre mesmo assim; o aviso diz o que faltou
            try:
                os.remove(dest + ".part")
            except OSError:
                pass
            falhas.append(f"{label}: {e}")
    gauge.close()
    if falhas:
        message(omni_i18n._("deps_download_failed").format(failures="\n".join(falhas)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) > 1 else 2)
