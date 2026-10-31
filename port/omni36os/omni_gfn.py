"""Omni36OS — GeForce NOW (OpenNOW-4Handhelds) em Aplicativos.

Instalado em /roms/apps (fora de Ports): OpenNOW.sh + opennow/. install() baixa a release mais
nova do GitHub e preserva opennow/stream.json (ajustes) e opennow/data (login). O .sh original
procura /roms/ports/opennow; a cópia daqui usa a própria pasta.

FN: "sistema" = atalhos FN do Omni valem; "gfn" = com o OpenNOW aberto, o FN vai só para ele
(abre o menu da sessão) e o serviço de atalhos ignora as combinações com FN.
"""
import json
import os
import re
import shutil
import tempfile
import urllib.request
import zipfile

DIR = "/roms/apps"
SH = os.path.join(DIR, "OpenNOW.sh")
GAME = os.path.join(DIR, "opennow")
REPO = "OpenCloudGaming/OpenNOW-4Handhelds"
VER = os.path.join(GAME, ".omni36os-versao")
FN_CONF = "/home/ark/.config/omni36os/gfn_fn"
PROC = "opennow-handhel"               # comm do opennow-handheld (15 letras)
KEEP = ("stream.json", "data")


def installed():
    return os.path.isfile(SH) and os.path.isdir(GAME)


def version():
    try:
        with open(VER) as f:
            return f.read().strip()
    except OSError:
        return ""


def fn_mode():
    try:
        with open(FN_CONF) as f:
            return "gfn" if f.read().strip() == "gfn" else "sistema"
    except OSError:
        return "sistema"


def set_fn_mode(mode):
    os.makedirs(os.path.dirname(FN_CONF), exist_ok=True)
    with open(FN_CONF, "w") as f:
        f.write(mode)
    os.chmod(FN_CONF, 0o666)


def running():
    for p in os.listdir("/proc"):
        if p.isdigit():
            try:
                with open(f"/proc/{p}/comm", "rb") as f:
                    if f.read().strip() == PROC.encode():
                        return True
            except OSError:
                pass
    return False


def latest():
    """(tag, url do zip) da release mais nova, beta incluída."""
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases?per_page=5",
                                 headers={"User-Agent": "Omni36OS"})
    with urllib.request.urlopen(req, timeout=30) as r:
        for rel in json.load(r):
            for a in rel.get("assets", []):
                if a["name"].endswith(".zip"):
                    return rel["tag_name"], a["browser_download_url"]
    raise RuntimeError("nenhuma release com zip")


def patch_sh(text):
    """GAMEDIR = pasta do próprio .sh (o original força /roms/ports/opennow)."""
    return re.sub(r'if \[ -n "\$\{directory:-\}" \]; then\n\s*GAMEDIR=.*\nelse\n\s*(GAMEDIR=.*)\nfi',
                  r"\1", text)


def install(log=lambda m: None, base=DIR):
    sh, game = os.path.join(base, "OpenNOW.sh"), os.path.join(base, "opennow")
    ver = os.path.join(game, ".omni36os-versao")
    tag, url = latest()
    if base == DIR and tag == version() and installed():
        return f"GeForce NOW já está na versão mais nova ({tag})."
    log(f"Baixando {tag}...")
    os.makedirs(base, exist_ok=True)
    tmp = tempfile.mkdtemp(dir=base, prefix=".gfn-")
    try:
        z = os.path.join(tmp, "a.zip")
        req = urllib.request.Request(url, headers={"User-Agent": "Omni36OS"})
        with urllib.request.urlopen(req, timeout=60) as r, open(z, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        x = os.path.join(tmp, "x")
        with zipfile.ZipFile(z) as zf:
            zf.extractall(x)
        if not os.path.isfile(os.path.join(x, "OpenNOW.sh")):
            raise RuntimeError("zip sem OpenNOW.sh")
        for k in KEEP:                 # ajustes e login continuam
            old = os.path.join(game, k)
            if os.path.exists(old):
                new = os.path.join(x, "opennow", k)
                shutil.rmtree(new, ignore_errors=True) if os.path.isdir(new) else (os.path.exists(new) and os.remove(new))
                shutil.move(old, new)
        shutil.rmtree(game, ignore_errors=True)
        shutil.move(os.path.join(x, "opennow"), game)
        with open(os.path.join(x, "OpenNOW.sh")) as f:
            txt = patch_sh(f.read())
        with open(sh, "w") as f:
            f.write(txt)
        os.chmod(sh, 0o755)
        for root, _, files in os.walk(game):
            for n in files:
                if n.startswith("opennow-"):
                    os.chmod(os.path.join(root, n), 0o755)
        with open(ver, "w") as f:
            f.write(tag)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return f"GeForce NOW {tag} instalado."


if __name__ == "__main__":              # imagem: omni_gfn.py --dest <pasta apps>
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--dest":
        print(install(print, sys.argv[2]))
