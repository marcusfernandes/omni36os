"""Omni36OS — programas de terceiros em Aplicativos, instalados em /roms/apps (fora de Ports).

Cada um vem de um .zip no formato PortMaster (um .sh + uma pasta). install() baixa a versão
mais nova, preserva os arquivos de `keep` (login, pareamento, ajustes) e corrige o .sh para usar
a própria pasta (os originais apontam para /roms/ports/<pasta>).

  python3 omni_apps.py --dest <pasta> [id...]   (imagem: instala todos ou os escolhidos)
"""
import json
import os
import re
import shutil
import socket
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

DIR = "/roms/apps"
SELF_DIR = 'GAMEDIR="$(cd "$(dirname "$0")" && pwd)/{d}"'
PM_INDEX = "https://github.com/PortsMaster/PortMaster-New/releases/latest/download/ports.json"


def _gfn_patch(t):
    return re.sub(r'if \[ -n "\$\{directory:-\}" \]; then\n\s*GAMEDIR=.*\nelse\n\s*(GAMEDIR=.*)\nfi', r"\1", t)


def _moon_patch(t):
    t = re.sub(r"(?m)^GAMEDIR=.*$", lambda _: SELF_DIR.format(d="moonlightnew"), t)
    return re.sub(r"(?m)^MOONDIR=.*$", lambda _: 'MOONDIR="$GAMEDIR/moonlight"', t)


APPS = {
    "gfn": {"name": "GeForce NOW", "sh": "OpenNOW.sh", "dir": "opennow", "keep": ("stream.json", "data"),
            "github": "OpenCloudGaming/OpenNOW-4Handhelds", "patch": _gfn_patch, "size": "14 MB"},
    "moonlight": {"name": "Moonlight", "sh": "Moonlight.sh", "zip_sh": "Moonlight New.sh", "dir": "moonlightnew",
                  "keep": ("conf", "keys"), "portmaster": "moonlightnew.zip", "patch": _moon_patch, "size": "10 MB"},
}


def sh_path(app, base=DIR):
    return os.path.join(base, APPS[app]["sh"])


def installed(app):
    return os.path.isfile(sh_path(app)) and os.path.isdir(os.path.join(DIR, APPS[app]["dir"]))


def version(app):
    try:
        with open(os.path.join(DIR, APPS[app]["dir"], ".omni36os-versao")) as f:
            return f.read().strip()
    except OSError:
        return ""


def _open(url, timeout):
    """urlopen com 4 tentativas: o DNS do roteador às vezes falha uma consulta."""
    req = urllib.request.Request(url, headers={"User-Agent": "Omni36OS"})
    for n in range(4):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            if n == 3:
                if isinstance(getattr(e, "reason", None), socket.gaierror):
                    raise RuntimeError("Não foi possível achar o servidor (DNS). Confira o Wi-Fi e tente de novo.")
                raise
            time.sleep(3)


def latest(app):
    """(versão, url do zip)."""
    a = APPS[app]
    if "github" in a:
        with _open(f"https://api.github.com/repos/{a['github']}/releases?per_page=5", 30) as r:
            for rel in json.load(r):
                for z in rel.get("assets", []):
                    if z["name"].endswith(".zip"):
                        return rel["tag_name"], z["browser_download_url"]
        raise RuntimeError("nenhuma release com zip")
    with _open(PM_INDEX, 30) as r:
        p = json.load(r)["ports"][a["portmaster"]]
    return p["source"].get("date_updated") or p["source"]["url"].split("/")[-2], p["source"]["url"]


def _rm(path):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.exists(path):
        os.remove(path)


def install(app, log=lambda m: None, base=DIR):
    a = APPS[app]
    sh, game = sh_path(app, base), os.path.join(base, a["dir"])
    tag, url = latest(app)
    if base == DIR and tag == version(app) and installed(app):
        return f"{a['name']} já está na versão mais nova."
    log(f"Baixando {a['name']} {tag}...")
    os.makedirs(base, exist_ok=True)
    tmp = tempfile.mkdtemp(dir=base, prefix=".app-")
    try:
        z = os.path.join(tmp, "a.zip")
        with _open(url, 60) as r, open(z, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        x = os.path.join(tmp, "x")
        with zipfile.ZipFile(z) as zf:
            zf.extractall(x)
        src_sh = os.path.join(x, a.get("zip_sh", a["sh"]))
        if not os.path.isfile(src_sh) or not os.path.isdir(os.path.join(x, a["dir"])):
            raise RuntimeError("zip diferente do esperado")
        for k in a["keep"]:            # login, pareamento e ajustes continuam
            old = os.path.join(game, k)
            if os.path.exists(old):
                new = os.path.join(x, a["dir"], k)
                _rm(new)
                os.makedirs(os.path.dirname(new), exist_ok=True)
                shutil.move(old, new)
        _rm(game)
        shutil.move(os.path.join(x, a["dir"]), game)
        with open(src_sh) as f:
            txt = a["patch"](f.read())
        with open(sh, "w") as f:
            f.write(txt)
        os.chmod(sh, 0o755)
        with open(os.path.join(game, ".omni36os-versao"), "w") as f:
            f.write(tag)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return f"{a['name']} instalado."


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "--dest":
        bad = 0
        for app in sys.argv[3:] or list(APPS):
            try:
                print(install(app, print, sys.argv[2]))
            except Exception as e:
                print(f"{app}: {e}")
                bad = 1
        sys.exit(bad)
    print(__doc__)
