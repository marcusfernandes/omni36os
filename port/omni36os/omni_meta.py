"""Ficha dos ports em 2 camadas, guardada no cartão (busca uma vez por jogo, com Wi-Fi).

1. PortMaster: catálogo oficial dos ports (ports.json do PortMaster-New). Acha o port pelo
   .sh instalado e traz título, descrição, gêneros, quem portou, o que precisa e a imagem.
2. Steam: a loja (a mesma base que o SteamDB mostra), sem chave. Descrição em pt-BR quando há.
3. Wikipédia: busca na inglesa e só aceita a página com o nome do jogo; a descrição vem da versão
   em português da mesma página quando ela existe. Traz também o ano e uma imagem.
4. DuckDuckGo (último recurso): só quando as de cima não trouxeram capa ou descrição. A capa vem da
   busca de imagens; a descrição, da resposta instantânea (quando o DuckDuckGo tem uma).

Antes de tudo vale a pasta "infos" da pasta ports, uma para todos os jogos, com o nome do .sh:
para abismo.sh, infos/abismo.txt (descrição), infos/abismo.png, .jpg ou .webp (capa) e, se
quiser, infos/abismo.json (nome, descricao, estudio, lancamento, generos, porter, pronto).
Reserva antiga: a pasta "info" dentro da pasta do port. Lida do cartão, sem internet, e manda
sobre as outras camadas.

Cada camada completa o que as de cima não trouxeram. Erro de rede não grava nada (tenta de
novo na próxima vez que o launcher abrir); jogo sem ficha em nenhuma grava cache vazio.
"""
import html
import json
import os
import re
import socket
import threading
import time
import urllib.parse
import urllib.request

import omni_i18n

CACHE = os.environ.get("OMNI_META_DIR") or "/home/ark/.config/omni36os/steam"
STEAM = "https://store.steampowered.com/api"
PM_LIST = "https://github.com/PortsMaster/PortMaster-New/releases/latest/download/ports.json"
PM_RAW = "https://raw.githubusercontent.com/PortsMaster/PortMaster-New/main/ports"
PM_INDEX = os.path.join(CACHE, "_portmaster.json")   # versão enxuta do catálogo
UA = {"User-Agent": "Omni36OS"}

# Só IPv4 na resolução de nomes: o console não tem IPv6, e há roteadores que não respondem à pergunta
# de endereço IPv6 (AAAA) — cada nome levava ~6 s esperando essa resposta, e a busca inteira (Steam,
# PortMaster, Wikipédia, DuckDuckGo, capa) estourava o tempo. Se só houver IPv6, usa o normal.
_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_v4(host, port, family=0, *args, **kw):
    if family == 0:
        try:
            return _getaddrinfo(host, port, socket.AF_INET, *args, **kw)
        except socket.gaierror:
            pass
    return _getaddrinfo(host, port, family, *args, **kw)


socket.getaddrinfo = _getaddrinfo_v4
_busy = set()
_lock = threading.Lock()
_pm_lock = threading.Lock()
_pm = None


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "jogo"


def _norm(name):
    """Nome do port → termo de busca: tira extensão, parênteses e versões."""
    name = re.sub(r"\.(sh|zip|port)$", "", name, flags=re.I)
    name = re.sub(r"[\(\[].*?[\)\]]", " ", name)
    name = re.sub(r"\b(v?\d+(\.\d+)+|port|r36s)\b", " ", name, flags=re.I)
    return re.sub(r"[_\s]+", " ", name).strip()


def _key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _save(path, text):
    """Grava sem deixar arquivo pela metade (bateria acabando no meio): escreve ao lado e troca."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read()


def _clean(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def paths(name):
    base = os.path.join(CACHE, _slug(name))
    return base + ".json", base + ".jpg"


def cached(name):
    """Ficha guardada (dict), {} se já se sabe que não há, ou None se ainda não buscou."""
    js, _ = paths(name)
    try:
        with open(js) as f:
            info = json.load(f)
    except (OSError, ValueError):
        return None
    # ficha incompleta de antes do DuckDuckGo: busca de novo uma vez para ele completar
    if not ("capa" in info and info.get("descricao")) and "wiki" not in info:
        return None
    return info


# --- 0. pasta "info" do port ---

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")


SKIP_DIRS = {"images", "videos", "manuals", "portmaster", "autoinstall", "info", "infos"}


def port_dir(path):
    """Pasta do port, ao lado do .sh: a de mesmo nome (sem maiúsculas, espaços ou _); senão a
    que o .sh cita ("/halo"); senão a que começa igual ("daytona" para "Daytona USA.sh")."""
    base, sh = os.path.split(path or "")
    want = _key(os.path.splitext(sh)[0])
    if not want:
        return None
    try:
        dirs = [d for d in os.listdir(base) if d.lower() not in SKIP_DIRS and os.path.isdir(os.path.join(base, d))]
    except OSError:
        return None
    hit = next((d for d in dirs if _key(d) == want), None)
    if not hit:
        try:
            with open(path, errors="replace") as f:
                text = f.read(20000)
            hit = next((d for d in dirs if re.search(r"/" + re.escape(d) + r"(?=[\"'/\s]|$)", text, re.M)), None)
        except OSError:
            pass
    if not hit:
        hit = next((d for d in sorted(dirs, key=len, reverse=True)
                    if len(_key(d)) >= 4 and want.startswith(_key(d))), None)
    return os.path.join(base, hit) if hit else None


def es_image(path):
    """Imagem do gamelist do ES (ports/images/<nome>-image.png), se houver."""
    base, sh = os.path.split(path or "")
    stem = os.path.splitext(sh)[0]
    for suf in ("-image", "-thumb"):
        for ext in IMG_EXT:
            f = os.path.join(base, "images", stem + suf + ext)
            if os.path.isfile(f):
                return f
    return None


FIELDS = ("nome", "descricao", "estudio", "lancamento", "generos", "porter", "pronto")


def infos(path):
    """Ficha de ports/infos/<nome do .sh>.{txt,png,jpg,jpeg,webp,json} (sem diferença de maiúsculas)."""
    base, sh = os.path.split(path or "")
    stem = os.path.splitext(sh)[0].lower()
    try:
        d = next((os.path.join(base, x) for x in os.listdir(base) if x.lower() == "infos"), None)
        files = {f.lower(): f for f in os.listdir(d)} if d and os.path.isdir(d) else {}
    except OSError:
        files = {}
    out = {}
    js = files.get(stem + ".json")
    if js:
        try:
            with open(os.path.join(d, js), encoding="utf-8") as fh:
                data = json.load(fh)
            out = {k: data[k] for k in FIELDS if data.get(k) not in (None, "")}
            if isinstance(out.get("generos"), list):
                out["generos"] = ", ".join(out["generos"])
        except (OSError, ValueError, AttributeError):
            out = {}
    txt = files.get(stem + ".txt")
    if txt and "descricao" not in out:
        try:
            with open(os.path.join(d, txt), encoding="utf-8", errors="replace") as fh:
                out["descricao"] = re.sub(r"\s+", " ", fh.read(4000)).strip()
        except OSError:
            pass
    img = next((files[stem + e] for e in IMG_EXT if stem + e in files), None)
    if img:
        out["capa"] = os.path.join(d, img)
    return out


def local(path):
    """ports/infos primeiro; o que faltar vem da reserva antiga, a pasta info do port."""
    out = infos(path)
    for k, v in _local_old(path).items():
        out.setdefault(k, v)
    return out


def _local_old(path):
    """Ficha da pasta info do port: info.json (campos de FIELDS + "capa"), o .txt como reserva
    da descrição e a primeira imagem como reserva da capa. JSON com erro é ignorado."""
    d = port_dir(path)
    info_dir = d and next((os.path.join(d, x) for x in sorted(os.listdir(d)) if x.lower() == "info"), None)
    if not info_dir or not os.path.isdir(info_dir):
        img = es_image(path)
        return {"capa": img} if img else {}
    files = sorted(os.listdir(info_dir))
    out = {}
    js = next((f for f in files if f.lower() == "info.json"), None) or \
        next((f for f in files if f.lower().endswith(".json")), None)
    if js:
        try:
            with open(os.path.join(info_dir, js), encoding="utf-8") as fh:
                data = json.load(fh)
            out = {k: data[k] for k in FIELDS if data.get(k) not in (None, "")}
            if isinstance(out.get("generos"), list):
                out["generos"] = ", ".join(out["generos"])
            cap = data.get("capa")
            if cap and os.path.isfile(os.path.join(info_dir, cap)):
                out["capa"] = os.path.join(info_dir, cap)
        except (OSError, ValueError, AttributeError):
            out = {}
    for f in files:
        full, low = os.path.join(info_dir, f), f.lower()
        if low.endswith(IMG_EXT) and "capa" not in out:
            out["capa"] = full
        elif low.endswith(".txt") and "descricao" not in out:
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    out["descricao"] = re.sub(r"\s+", " ", fh.read(4000)).strip()
            except OSError:
                pass
    if "capa" not in out and es_image(path):
        out["capa"] = es_image(path)
    return out


# --- 1. PortMaster ---

def _pm_index():
    """{chave do .sh ou do título: ficha}; o catálogo é baixado de novo a cada 7 dias."""
    global _pm
    with _pm_lock:
        if _pm is not None:
            return _pm
        try:
            fresh = time.time() - os.path.getmtime(PM_INDEX) < 7 * 86400
        except OSError:
            fresh = False
        if not fresh:
            ports = json.loads(_get(PM_LIST)).get("ports", {})
            idx = {}
            for zipname, p in ports.items():
                a, folder = p.get("attr", {}), zipname[:-4]
                shot = (a.get("image") or {}).get("screenshot")
                e = {"titulo": a.get("title", ""), "descricao": a.get("desc", ""),
                     "porter": ", ".join(a.get("porter") or []),
                     "generos": ", ".join(g.title() for g in a.get("genres") or []),
                     "pronto": bool(a.get("rtr")),
                     "img": f"{PM_RAW}/{folder}/{shot}" if shot else ""}
                for it in p.get("items") or []:
                    if it.lower().endswith(".sh"):
                        idx.setdefault(_key(it[:-3]), e)
                idx.setdefault(_key(e["titulo"]), e)
            _save(PM_INDEX, json.dumps(idx, ensure_ascii=False))
        try:
            with open(PM_INDEX) as f:
                _pm = json.load(f)
        except (OSError, ValueError):     # catálogo estragado: baixa de novo na próxima vez
            _pm = {}
        return _pm


def portmaster(name, path):
    idx = _pm_index()
    sh = os.path.splitext(os.path.basename(path or ""))[0]
    return idx.get(_key(sh)) or idx.get(_key(name)) or idx.get(_key(_norm(name)))


# --- 2. Steam ---

def steam(term):
    lang = "english" if omni_i18n.get_lang() == "en" else "brazilian"
    country = "US" if lang == "english" else "BR"
    q = urllib.parse.urlencode({"term": term, "l": lang, "cc": country})
    found = json.loads(_get(f"{STEAM}/storesearch/?{q}")).get("items") or []
    app = next((i for i in found if _key(i.get("name", "")) == _key(term)), None)
    if not app:
        return None                   # só aceita nome igual: a busca da Steam devolve parecidos
    aid = app["id"]
    d = json.loads(_get(f"{STEAM}/appdetails?appids={aid}&l={lang}&cc={country}"))[str(aid)]
    d = d.get("data", {}) if d.get("success") else {}
    return {"nome": d.get("name") or app.get("name"), "descricao": _clean(d.get("short_description")),
            "estudio": ", ".join(d.get("developers") or []),
            "generos": ", ".join(g["description"] for g in d.get("genres") or [])[:60],
            "lancamento": (d.get("release_date") or {}).get("date", ""),
            "img": d.get("header_image") or "", "steamdb": f"https://steamdb.info/app/{aid}/"}


# --- 3. Wikipédia ---

WIKI_UA = {"User-Agent": "Omni36OS/1.11 (https://github.com/mpjsilva/omni36os)"}   # a Wikimedia pede contato


def _wiki_ok(title, term):
    """A página é deste jogo? "Claw (video game)" serve para Claw; "Blobby Volley" para Blobby
    Volley 2 (a série); listas e outros jogos parecidos não."""
    t, k = _key(re.sub(r"\s*\((?:[^)]*\b)?(?:video )?game\)$", "", title, flags=re.I)), _key(term)
    return t == k or (k.startswith(t) and k[len(t):].isdigit())


def _wiki_get(lang, query):
    return json.loads(_get(f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {**query, "format": "json"}), headers=WIKI_UA))


def _wiki_summary(lang, title):
    return json.loads(_get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
                           + urllib.parse.quote(title.replace(" ", "_")), headers=WIKI_UA))


def wikipedia(term):
    lang = "en" if omni_i18n.get_lang() == "en" else "pt"
    hits = _wiki_get(lang, {"action": "query", "list": "search", "srsearch": f"{term} video game",
                            "srlimit": 5})["query"]["search"]
    title = next((h["title"] for h in hits if _wiki_ok(h["title"], term)), None)
    if not title:
        return None
    summary = _wiki_summary(lang, title)
    if lang == "en" and not summary.get("extract"):
        lang = "pt"
        hits = _wiki_get(lang, {"action": "query", "list": "search", "srsearch": f"{term} jogo",
                                "srlimit": 5})["query"]["search"]
        title = next((h["title"] for h in hits if _wiki_ok(h["title"], term)), None)
        if title:
            summary = _wiki_summary(lang, title)
    out = {"nome": term, "descricao": summary.get("extract", "")}
    year = re.search(r"\b(19[7-9]\d|20[0-4]\d)\b", summary.get("description", "") + " " + out["descricao"][:120])
    if year:
        out["lancamento"] = year.group(1)
    img = (summary.get("originalimage") or summary.get("thumbnail") or {}).get("source", "")
    if re.search(r"\.(jpe?g|png)$", img, re.I):
        out["img"] = img
    return out


# --- 4. DuckDuckGo (último recurso) ---

DDG = "https://duckduckgo.com"
DDG_UA = {"User-Agent": "Mozilla/5.0 (X11; Linux aarch64) Omni36OS"}   # sem cara de navegador ele recusa


def ddg(term, need_img=True, need_desc=True):
    out = {}
    if need_desc:
        region = "us-en" if omni_i18n.get_lang() == "en" else "br-pt"
        q = urllib.parse.urlencode({"q": f"{term} video game", "format": "json", "no_html": 1, "kl": region})
        a = json.loads(_get(f"https://api.duckduckgo.com/?{q}", headers=DDG_UA))
        if a.get("AbstractText"):
            out["descricao"] = _clean(a["AbstractText"])
        if a.get("Image"):
            out["img"] = urllib.parse.urljoin(DDG, a["Image"])
    if need_img and not out.get("img"):
        q = f"{term} game cover"
        page = _get(f"{DDG}/?" + urllib.parse.urlencode({"q": q, "iax": "images", "ia": "images"}),
                    headers=DDG_UA).decode(errors="ignore")
        m = re.search(r"vqd=[\"']?([\d-]+)", page)          # o token que a busca de imagens exige
        if m:
            r = json.loads(_get(f"{DDG}/i.js?" + urllib.parse.urlencode(
                {"l": "br-pt", "o": "json", "q": q, "vqd": m.group(1), "f": ",,,,,", "p": "1"}),
                headers={**DDG_UA, "Referer": f"{DDG}/"}))
            ok = [i for i in r.get("results", [])[:10]
                  if re.search(r"\.(jpe?g|png)(\?|$)", i.get("image", ""), re.I)]   # o SDL não abre webp/svg
            wide = [i for i in ok if i.get("width", 0) >= i.get("height", 1) * 1.2]   # a capa da ficha é larga
            pick = (wide or ok or [None])[0]
            if pick:
                out["img"] = pick["image"]
    return out or None


def _pt(text):
    """Descrição parece português? (a Steam devolve inglês quando não há tradução)"""
    words = set(re.findall(r"[a-zà-ú]+", (text or "").lower()))
    return len(words & {"o", "a", "de", "que", "um", "uma", "do", "da", "em", "para", "com", "você"}) >= 3


def fetch(name, path=""):
    english = omni_i18n.get_lang() == "en"
    pm = portmaster(name, path)
    term = (pm or {}).get("titulo") or _norm(name)
    info, descs, imgs = {}, [], []
    layers = [("PortMaster", pm), ("Steam", steam(term))]
    active_descs = lambda: any((d or {}).get("descricao") and (not english or not _pt((d or {}).get("descricao")))
                               for _, d in layers)
    if not any((d or {}).get("img") for _, d in layers) or not active_descs():
        try:                          # sem capa ou descrição no idioma atual: a Wikipédia completa
            layers.append(("Wikipédia", wikipedia(term)))
            info["wiki"] = True
        except (OSError, ValueError, KeyError):
            pass
    if not any((d or {}).get("img") for _, d in layers) or not active_descs():
        try:                          # faltou capa ou descrição no idioma atual: DuckDuckGo completa
            layers.append(("DuckDuckGo", ddg(term, not any((d or {}).get("img") for _, d in layers),
                                             not active_descs())))
            info["ddg"] = True        # já tentou: não busca de novo a cada abertura
        except (OSError, ValueError, KeyError):
            pass
    for src, d in layers:
        if not d:
            continue
        info.setdefault("fontes", []).append(src)
        d = dict(d, nome=d.get("nome") or d.get("titulo"))
        for k in ("nome", "estudio", "lancamento", "generos", "porter", "steamdb"):
            if d.get(k) and not info.get(k):
                info[k] = d[k]
        if "pronto" in d:
            info["pronto"] = d["pronto"]
        if d.get("descricao"):
            descs.append(d["descricao"])
        if d.get("img"):
            imgs.append((src, d["img"]))
    if descs:
        # Prefer the active language; for user-supplied/PortMaster text, retain the best available description.
        if english:
            info["descricao"] = next((t for t in descs if not _pt(t)), descs[0])
        else:
            info["descricao"] = next((t for t in descs if _pt(t)), descs[0])
    os.makedirs(CACHE, exist_ok=True)
    js, jpg = paths(name)
    prio = {"Steam": 0, "PortMaster": 1, "Wikipédia": 2, "DuckDuckGo": 3}
    for _, url in sorted(imgs, key=lambda i: prio[i[0]]):   # capa: Steam (larga), PortMaster, DuckDuckGo
        try:
            data = _get(url, headers=DDG_UA)   # sites de imagem recusam quem não parece navegador
            with open(jpg + ".tmp", "wb") as f:  # inteira ou nada: o launcher fecha ao abrir um jogo
                f.write(data)
            os.replace(jpg + ".tmp", jpg)
            info["capa"] = jpg
            break
        except OSError:
            continue
    _save(js, json.dumps(info, ensure_ascii=False))
    return info


def want(name, path="", done=None):
    """Pede a ficha em segundo plano (uma busca por jogo de cada vez)."""
    with _lock:
        if name in _busy:
            return
        _busy.add(name)

    def run():
        try:
            fetch(name, path)
        except Exception:
            pass                      # sem internet ou serviço fora: fica para a próxima
        finally:
            with _lock:
                _busy.discard(name)
            if done:
                done(name)
    threading.Thread(target=run, daemon=True).start()
