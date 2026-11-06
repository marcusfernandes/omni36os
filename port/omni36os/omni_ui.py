#!/usr/bin/env python3
"""Omni36OS — interface gráfica (SDL2) do assistente do R36S.

Tela inicial com 9 cartões; cada cartão abre uma página com o diagnóstico
(regras fixas de omni_checks.py) à esquerda e os controles à direita.
Controle: direcional/analógico navega, A confirma, B volta; o power abre Energia.
Os botões A/B seguem a inversão do sistema ou do Omni36OS.

Variáveis: OMNI_FAKE=1 (dados de mentira, para desenhar no PC),
OMNI_WINDOWED=1, OMNI_DEMO="right,ok,wait800,shot,..." + OMNI_SHOT_DIR (roteiro
com screenshots PPM, para testar sem mãos).
"""
import ctypes as C
import glob
import json
import math
import os
import re
import signal
import struct
import sys
import threading
import time

import omni_i18n
import gfx
from gfx import W, H, hexc, alpha

FAKE = os.environ.get("OMNI_FAKE") == "1"
DEMO_STEP = float(os.environ.get("OMNI_DEMO_STEP", "0.45"))   # segundos entre passos do OMNI_DEMO (testes: menos)
if not FAKE:
    import omni
    import omni_backup
    import omni_checks
    import omni_games
    import omni_ports_fix
    import omni_sistema
    import omni_tools
    import omni_update
else:   # simulador: a ficha da Steam vem de verdade, mas o cache fica no PC
    os.environ.setdefault("OMNI_META_DIR", os.path.expanduser("~/.cache/omni36os-steam"))
import omni_meta  # noqa: E402
import omni_combos  # noqa: E402
import omni_gfn  # noqa: E402
import omni_apps  # noqa: E402
import omni_mouse  # noqa: E402

if os.environ.get("OMNI_PREVIEW_LANG") in ("pt-BR", "en"):
    omni_i18n.set_lang = lambda _lang: None

# --- paleta ---

# Tema escuro e claro (Tela e som > Tema). INK é a cor dos véus e contornos: branco
# sobre o fundo escuro, azul-marinho sobre o claro. ON_TEXT é o texto em cima da
# cor de destaque (item escolhido), branco nos dois temas.
from omni_theme import THEMES  # noqa: E402
ON_TEXT = (255, 255, 255, 255)
THEME = "escuro"


def apply_theme(name):
    global THEME, BG_TOP, BG_BOT, TEXT, MUTED, FAINT, INK, GLASS, GLASS_HI, MODAL_A, MODAL_B, TOAST, BLOB_A
    THEME = name if name in THEMES else "escuro"
    t = THEMES[THEME]
    BG_TOP, BG_BOT, TEXT, MUTED, FAINT = (hexc(t[k]) for k in ("BG_TOP", "BG_BOT", "TEXT", "MUTED", "FAINT"))
    MODAL_A, MODAL_B, TOAST = hexc(t["MODAL_A"]), hexc(t["MODAL_B"]), hexc(t["TOAST"])
    INK = hexc(t["INK"])[:3]
    GLASS, GLASS_HI = (*INK, 14), (*INK, 26)
    BLOB_A = t["BLOB"]


def ink(a):
    return (*INK, a)


THEME_FILE = os.path.expanduser("~ark/.config/omni36os/tema")


def saved_theme():
    if FAKE:
        return os.environ.get("OMNI_TEMA", "escuro")
    try:
        with open(THEME_FILE) as f:
            return f.read().strip()
    except OSError:
        return "escuro"


apply_theme(saved_theme())
LEVEL = {"ok": hexc("34d399"), "aviso": hexc("fbbf24"), "problema": hexc("f87171"), "info": hexc("60a5fa"),
         "dica": hexc("c084fc")}   # dica: mini explicação do item escolhido
LEVEL_ICON = {"ok": "check", "aviso": "alert-triangle", "problema": "x", "info": "info-circle", "dica": "bulb"}

CARDS = [
    # id, título, ícone, cor 1, cor 2 (3 x 3: Ports no centro, a abertura entrega o destaque nele)
    ("tela", omni_i18n._("card_tela"), "device-tv", "fbbf24", "f97316"),
    ("rede", omni_i18n._("card_rede"), "wifi", "38bdf8", "0ea5e9"),
    ("controles", omni_i18n._("card_controles"), "keyboard", "818cf8", "4f46e5"),
    ("desempenho", omni_i18n._("card_desempenho"), "gauge", "fb7185", "e11d48"),
    ("ports", omni_i18n._("card_ports"), "device-gamepad-2", "c084fc", "7c3aed"),     # abre a biblioteca
    ("apps", omni_i18n._("card_apps"), "apps", "f472b6", "db2777"),
    ("cartoes", omni_i18n._("card_cartoes"), "device-sd-card", "2dd4bf", "0284c7"),
    ("ferramentas", omni_i18n._("card_ferramentas"), "adjustments", "94a3b8", "475569"),
    ("geral", omni_i18n._("card_geral"), "settings", "60a5fa", "a78bfa"),
]
PORTS_AT = next(i for i, c in enumerate(CARDS) if c[0] == "ports")
COLS = 3
# Páginas abertas de dentro de outro card: B volta para o card de origem e os
# alertas delas aparecem no ponto do card de origem.
TWO_COLS = set()      # cartões sem painel de diagnóstico: as ações vêm em duas colunas (hoje nenhum)
SUBPAGES = {            "calibracao": (omni_i18n._("sub_calibracao"), "battery-2", "a3e635", "16a34a", "tela"),
            "usbrede": (omni_i18n._("sub_usbrede"), "network", "38bdf8", "4f46e5", "rede"),
            "seguranca": (omni_i18n._("sub_seguranca"), "lock", "60a5fa", "a78bfa", "geral"),
            "backup": (omni_i18n._("sub_backup"), "device-floppy", "60a5fa", "a78bfa", "geral"),
            "checkup": (omni_i18n._("sub_checkup"), "stethoscope", "22d3ee", "3b82f6", "geral"),
            "sobre": (omni_i18n._("sub_sobre"), "help-circle", "60a5fa", "a78bfa", "geral"),
            "atalhos": (omni_i18n._("sub_atalhos"), "keyboard", "818cf8", "4f46e5", "controles"),
            "gfn": (omni_i18n._("sub_gfn"), "device-tv", "84cc16", "15803d", "apps"),
            "moonlight": (omni_i18n._("sub_moonlight"), "device-tv", "818cf8", "4338ca", "apps"),
            "testar": (omni_i18n._("sub_testar"), "player-play", "34d399", "059669", "ferramentas")}
PARENT = {cid: v[4] for cid, v in SUBPAGES.items()}
SOURCE_NAMES = {"roms": "ROMS", "roms2": "ROMS2", "ambos": omni_i18n._("source_both_cards")}
ZRAM_SIZES = [0, 256, 512, 768]   # MB do zram (Desempenho); 0 = desligado, o padrão
LIVE = {"usbrede": 3.0, "calibracao": 10.0, "rede": 5.0}   # subpáginas com estado que muda sozinho: relê a cada N s


LIB_CARD = ("jogos", omni_i18n._("ui_games"), "device-gamepad-2", "c084fc", "7c3aed")   # cor da biblioteca (tela inicial)


def card_info(cid):
    """(id, título, ícone, cor 1, cor 2) de um card ou subpágina."""
    if cid == "jogos":
        return LIB_CARD
    if cid in SUBPAGES:
        return (cid, *SUBPAGES[cid][:4])
    return next(c for c in CARDS if c[0] == cid)
FPS_ACTIVE, FPS_IDLE, IDLE_AFTER = 30, 10, 4.0   # quadros/s; segundos sem botão até ficar parado
LIB_POS = "/tmp/omni36os-biblioteca.json"
HUB = os.environ.get("OMNI_HUB", "")         # boot: shell do sistema; jogo: por cima de um jogo (botão de power)
POWER_SHM = "/dev/shm/omni36os-power"          # mesma pasta do power_button.py (lá está o porquê)
POWER_PRESS = f"{POWER_SHM}/press"               # menu na tela: o pid deste Omni36OS
POWER_PENDING = f"{POWER_SHM}/pending"
POWER_FLAG = f"{POWER_SHM}/menu"                 # abrir já no menu de energia
PANIC_MSG = f"{POWER_SHM}/panic-msg"
BAT_MSG = f"{POWER_SHM}/bat-msg"                 # omni_atalho.py: título na 1ª linha, texto depois
BAT_FLAG = f"{POWER_SHM}/bateria"                # aberto por cima de uma ferramenta só para o aviso de bateria
RESUME = os.environ.get("OMNI_RESUME", "")   # "testar": o Omni36OS voltou de um teste de port
# Estado guardado na RAM ao sair para um jogo ou ferramenta: na volta o menu abre na hora com as
# verificações de antes (que levavam ~10 s no console) e elas se refazem em segundo plano.
STATE_CACHE = "/dev/shm/omni36os-estado.json"
STATE_MAX_AGE = 30 * 60

import omni_help
import omni_musica  # noqa: E402
import omni_video  # noqa: E402
import omni_logs  # noqa: E402
import omni_teclado  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def omni_version():
    try:
        with open(os.path.join(HERE, "VERSION")) as f:
            return f.read().strip() or "?"
    except OSError:
        return "?"


SEEN_FILE = "/home/ark/.config/omni36os/versao-vista"   # versão cujas novidades já apareceram


def card_of(game):
    """Em qual cartão o port está: "2" para /roms2, "1" para o resto (/roms)."""
    return "2" if game.get("path", "").startswith("/roms2/") else "1"


def vtuple(v):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", (v or "").strip())
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def news_text(news):
    """[(versão, data, [itens])] no formato do leitor, respeitando o idioma ativo."""
    english = omni_i18n.get_lang() == "en"
    out = []
    for version, date, items in news:
        out.append(f"# {'Version' if english else 'Versão'} {version} ({date})")
        translated = omni_help.NOVIDADES_EN.get(version, []) if english else []
        for i, item in enumerate(items):
            text = translated[i] if i < len(translated) else item
            out.append(f"• {text}")
        out.append("")
    return "\n".join(out).strip()


def about_findings():
    """Painel de Geral e Sobre: qual Omni36OS e qual Omni36OS estão rodando."""
    ver = omni_version()
    inst = time.strftime("%d/%m/%Y %H:%M", time.localtime(os.path.getmtime(os.path.join(HERE, "omni_ui.py"))))
    out = [("info", omni_i18n._("ui_about_version_installed").format(version=ver, date=inst))]
    news = next((n for n in omni_help.NOVIDADES if n[0] == ver), None)
    if news:
        translated_news = omni_help.NOVIDADES_EN.get(ver, []) if omni_i18n.get_lang() == "en" else []
        item = translated_news[0] if translated_news else news[2][0]
        out.append(("info", omni_i18n._("ui_about_news").format(news=item)))
    try:
        with open("/home/ark/.config/.VERSION") as f:
            d = f.read().strip()
        out.append(("info", omni_i18n._("ui_about_base_version").format(date=f"{d[2:4]}/{d[:2]}/{d[4:]}") if len(d) == 8 else omni_i18n._("ui_about_base_build").format(version=d)))
    except OSError:
        pass
    return out

FAKE_CARD = os.path.expanduser("~/Apps/Omni36OS/cartao/EASYROMS/ports")   # cópia do cartão no PC
FAKE_GAMES = [
    {"name": "ports", "full": "Ports", "path": "/roms2/ports", "n_unknown": 0, "unknown": [], "games": [
        {"path": "/roms2/ports/Stardew Valley.sh", "name": "Stardew Valley", "size": 524288000, "fav": 1,
         "plays": 12, "time": 18400, "last": "20261024T201000"},
        {"path": "/roms/ports/Celeste.sh", "name": "Celeste", "size": 1200000000, "plays": 3,
         "time": 3600, "last": "20261020T101000"},
        {"path": "/roms2/ports/Undertale.sh", "name": "Undertale", "size": 180000000, "fav": 1},
        {"path": FAKE_CARD + "/Daytona USA.sh", "name": "Daytona USA", "size": 90000000},   # pasta info
        {"path": FAKE_CARD + "/Halo - Combat Evolved.sh", "name": "Halo - Combat Evolved", "size": 50000000},
        {"path": FAKE_CARD + "/McpeLauncher.sh", "name": "Minecraft", "size": 300000000},
        {"path": "/roms2/ports/Half-Life.sh", "name": "Half-Life", "size": 400000000},
        {"path": "/roms2/ports/Hollow Knight.sh", "name": "Hollow Knight", "size": 900000000}]},
]

FAKE_PORTS = [{"dir": "/roms2/ports", "label": "/roms2/ports (cartão de jogos)", "es": True,
               "ports": ["/roms2/ports/Daytona USA.sh", "/roms2/ports/NFSU1.sh", "/roms2/ports/Undertale.sh"]}]
GAMMAS = [0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4, 1.6]
GOV_NAMES = {"powersave": "Economia", "ondemand": "Equilibrado", "schedutil": "Equilibrado (kernel)",
             "performance": "Máximo"}


def swapped_ab():
    if os.path.exists("/var/cache/Switch_AB"):
        return True
    try:
        with open("/home/ark/.emulationstation/es_settings.cfg") as f:
            return 'name="InvertButtons" value="true"' in f.read()
    except OSError:
        return False


# --- dados (reais ou de mentira) ---

def charging_now():
    if FAKE:
        return os.path.exists("/tmp/omni36os-carregando")    # simulador: crie o arquivo para "ligar" o carregador
    return omni.read_text("/sys/class/power_supply/battery/status", "") in ("Charging", "Full")


def ipv4(iface):
    """IPv4 da interface (ou "") sem chamar programa: um ioctl SIOCGIFADDR."""
    import fcntl
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sk:
            raw = fcntl.ioctl(sk.fileno(), 0x8915, struct.pack("256s", iface[:15].encode()))
        return socket.inet_ntoa(raw[20:24])
    except OSError:
        return ""


def wifi_state():
    """Wi-Fi da pílula, só com leituras do /sys e do /proc (rápidas, a cada 5 s): o adaptador (qualquer
    interface sem fio, não só wlan0), se está conectado e a força do sinal (0 a 100)."""
    iface = next((n for n in sorted(os.listdir("/sys/class/net"))
                  if os.path.isdir(f"/sys/class/net/{n}/wireless") or n.startswith("wlan")), None)
    if not iface:
        return {"wifi": False, "conectado": False, "sinal": 0}
    for rf in glob.glob(f"/sys/class/net/{iface}/phy80211/rfkill*"):   # rádio desligado (Ligar o Wi-Fi)
        if "1" in (omni.read_text(f"{rf}/soft", "0"), omni.read_text(f"{rf}/hard", "0")):
            return {"wifi": False, "conectado": False, "sinal": 0}
    # conectado = associado a uma rede E com IPv4: o driver da Realtek (rtl8821cu) deixa a interface
    # "up" mesmo sem rede, e o operstate sozinho fazia a pílula mostrar conexão que não existe
    up = omni.read_text(f"/sys/class/net/{iface}/operstate") == "up" and \
        omni.read_text(f"/sys/class/net/{iface}/carrier", "0") == "1" and bool(ipv4(iface))
    sinal = 0
    for ln in omni.read_text("/proc/net/wireless", "").splitlines():
        if ln.strip().startswith(iface + ":"):
            try:
                sinal = min(100, int(float(ln.split()[2].rstrip(".")) * 100 / 70))   # qualidade do link, de 0 a 70
            except (IndexError, ValueError):
                pass
    return {"wifi": True, "conectado": up, "sinal": sinal if up else 0}


def ancoragem_ativa():
    """Internet pela ancoragem USB do celular: interface de um destes drivers, com link e IPv4.
    O modo Rede pelo celular (g_ether) não entra: ali o console é o aparelho USB."""
    for n in os.listdir("/sys/class/net"):
        drv = os.path.basename(os.path.realpath(f"/sys/class/net/{n}/device/driver"))
        if drv in ("rndis_host", "cdc_ether", "cdc_ncm") and \
                omni.read_text(f"/sys/class/net/{n}/carrier", "0") == "1" and ipv4(n):
            return True
    return False


class Data:
    def status(self):
        if FAKE:
            return {"bat": 87, "carregando": False, "temp": 52, "wifi": True, "conectado": True, "sinal": 72,
                    "gov": "ondemand", "cpu_max": 1296}
        t = omni.read_text("/sys/class/thermal/thermal_zone0/temp", "0")
        return {
            "bat": int(omni.read_text("/sys/class/power_supply/battery/capacity", "0")),
            "carregando": omni.read_text("/sys/class/power_supply/battery/status") in ("Charging", "Full"),
            "temp": int(t) // 1000 if t.isdigit() else 0,
            **wifi_state(),
            "ancoragem": ancoragem_ativa(),
            "gov": omni.get_preferred_governor(),
            "cpu_max": omni.get_cpu_max(),
        }

    def check(self, name):
        if FAKE:
            time.sleep(0.4)
            som = ("ok", omni_i18n._("ui_sim_speaker"))
            fake = {
                "checkup": ([], [("ok", omni_i18n._("ui_sim_all_ok")),
                                 ("info", omni_i18n._("ui_sim_card_detail"))]),
                "bateria": ([], [("ok", omni_i18n._("ui_sim_battery")), ("ok", omni_i18n._("ui_sim_brightness")),
                                 ("ok", omni_i18n._("ui_sim_cpu_min"))]),
                "atualizar": ([], [("ok", omni_i18n._("ui_sim_volume")), som]),
                "desempenho": ([], [("ok", omni_i18n._("ui_sim_temp")),
                                    ("ok", omni_i18n._("ui_sim_cpu_balanced")),
                                    ("info", omni_i18n._("ui_sim_limits"))]),
                "cartoes": ([], [("ok", omni_i18n._("ui_sim_card1")), ("ok", omni_i18n._("ui_sim_card2")),
                                 ("ok", omni_i18n._("ui_sim_system_space")),
                                 ("ok", omni_i18n._("ui_sim_card2_space"))]),
                "pc": (["ligar_pendrive"], [("ok", omni_i18n._("ui_sim_usb_pc")),
                                            ("info", omni_i18n._("ui_sim_usb_restart"))]),
            }
            acts, found = fake.get(name, ([], [("ok", omni_i18n._("ui_sim_ok_test_data"))]))
            nivel = "problema" if any(l == "problema" for l, _ in found) else \
                "aviso" if any(l == "aviso" for l, _ in found) else "ok"
            return {"nivel": nivel, "acoes": acts, "achados": found}
        return omni_checks.CHECKS[name]()

    def action(self, name):
        if FAKE:
            time.sleep(1)
            return "Feito!"
        return omni_checks.run_action(name)

    def label(self, name):
        if FAKE:
            return omni_i18n._(omni_checks.ACTION_KEYS[name][0])
        return omni_checks.ACTIONS[name][0]

    def get(self, what):
        if what == "idioma":
            return omni_i18n.get_lang()
        if what == "gfn_fn":
            return omni_gfn.fn_mode() if not FAKE else self.__dict__.get("fake_gfn", "sistema")
        if what.startswith("m_"):         # Aplicativos > Músicas (o mesmo arquivo no simulador e no console)
            return music_cfg()[what[2:]]
        if FAKE:
            if what in self.__dict__.get("fake_vals", {}):   # simulador: guarda o que foi mudado
                return self.fake_vals[what]
            if what.startswith("at_"):
                return omni_combos.defaults()[what[3:]]
            return {"brilho": 40, "volume": 60, "gov": "ondemand", "govs": ["powersave", "ondemand", "performance"],
                    "part": "roms2", "pendrive": False, "cpu_max": 1296, "cpu_freqs": [0, 1296, 1416, 1512],
                    "gpu_max": 520, "gpu_freqs": [0, 400, 480, 520, 600], "oc": False, "zram": 0, "fonte": "roms", "gamma": 1.0, "contraste": 50, "led": "verde", "remoto": "desligados", "busca": "ligada" if busca_on() else "desligada",
                    "inverter": "ligado" if swapped_ab() else "desligado",
                    "power": "desligar", "tema": THEME}[what]
        if what == "brilho":
            return omni.get_brightness()
        if what == "volume":
            return omni.get_volume()
        if what == "gov":
            return omni.get_preferred_governor()
        if what == "govs":
            return [g for g in ("powersave", "ondemand", "schedutil", "performance") if g in omni.get_cpu_governors()]
        if what == "part":
            return omni.usb_run("part") or ("roms2" if os.path.ismount("/roms2") else "roms")
        if what == "pendrive":
            return omni.usb_facts()["modo_pendrive_ligado"]
        if what == "oc":
            return omni.oc_unlocked()
        if what == "cpu_max":
            return omni.get_cpu_max()
        if what == "cpu_freqs":
            return omni.cpu_freqs()
        if what == "gpu_max":
            return omni.get_gpu_max()
        if what == "gpu_freqs":
            return omni.gpu_freqs()
        if what == "zram":
            return omni_sistema.zram_get()
        if what == "fonte":
            return omni.get_game_source()
        if what == "gamma":
            return omni.get_gamma()
        if what == "contraste":
            return int(round((self.get("gamma") - 0.5) * 100))
        if what == "led":
            return omni.get_led()
        if what == "remoto":
            return "ligados" if omni_sistema.remote_on() else "desligados"
        if what == "busca":
            return "ligada" if busca_on() else "desligada"
        if what == "inverter":
            return "ligado" if omni.get_swap_ab() or omni.get_swap_xy() else "desligado"
        if what == "tema":
            return THEME
        if what.startswith("at_"):          # Controles > Atalhos
            return omni.get_atalhos()[what[3:]]

    def set(self, what, value):
        if what == "gfn_fn":
            if FAKE:
                self.fake_gfn = value
            else:
                omni_gfn.set_fn_mode(value)
            return "ok"
        if what.startswith("m_"):
            music_save(**{what[2:]: value})
            return "ok"
        if what == "idioma":
            omni_i18n.set_lang(value)
            refresh_i18n_labels()
            if getattr(self, "page", None) is not None:
                self.items = self.build_items(self.page)
            if getattr(self, "music", None) is not None:
                self.MUSIC_OPTIONS = self.music_options()
            global LIB_CARD
            LIB_CARD = ("jogos", omni_i18n._("ui_games"), "device-gamepad-2", "c084fc", "7c3aed")
            omni_logs.NAMES.update({func: omni_i18n._(key) for func, key in omni_logs.NAME_KEYS.items()})
            omni_checks.ACTIONS.update({name: (omni_i18n._(key), fn)
                                        for name, (key, fn) in omni_checks.ACTION_KEYS.items()})
            # Recarrega os cartões e subpáginas com o novo idioma
            global CARDS, SUBPAGES
            CARDS = [
                ("tela", omni_i18n._("card_tela"), "device-tv", "fbbf24", "f97316"),
                ("rede", omni_i18n._("card_rede"), "wifi", "38bdf8", "0ea5e9"),
                ("controles", omni_i18n._("card_controles"), "keyboard", "818cf8", "4f46e5"),
                ("desempenho", omni_i18n._("card_desempenho"), "gauge", "fb7185", "e11d48"),
                ("ports", omni_i18n._("card_ports"), "device-gamepad-2", "c084fc", "7c3aed"),
                ("apps", omni_i18n._("card_apps"), "apps", "f472b6", "db2777"),
                ("cartoes", omni_i18n._("card_cartoes"), "device-sd-card", "2dd4bf", "0284c7"),
                ("ferramentas", omni_i18n._("card_ferramentas"), "adjustments", "94a3b8", "475569"),
                ("geral", omni_i18n._("card_geral"), "settings", "60a5fa", "a78bfa"),
            ]
            SUBPAGES = {
                "calibracao": (omni_i18n._("sub_calibracao"), "battery-2", "a3e635", "16a34a", "tela"),
                "usbrede": (omni_i18n._("sub_usbrede"), "network", "38bdf8", "4f46e5", "rede"),
                "seguranca": (omni_i18n._("sub_seguranca"), "lock", "60a5fa", "a78bfa", "geral"),
                "backup": (omni_i18n._("sub_backup"), "device-floppy", "60a5fa", "a78bfa", "geral"),
                "checkup": (omni_i18n._("sub_checkup"), "stethoscope", "22d3ee", "3b82f6", "geral"),
                "sobre": (omni_i18n._("sub_sobre"), "help-circle", "60a5fa", "a78bfa", "geral"),
                "atalhos": (omni_i18n._("sub_atalhos"), "keyboard", "818cf8", "4f46e5", "controles"),
                "gfn": (omni_i18n._("sub_gfn"), "device-tv", "84cc16", "15803d", "apps"),
                "moonlight": (omni_i18n._("sub_moonlight"), "device-tv", "818cf8", "4338ca", "apps"),
                "testar": (omni_i18n._("sub_testar"), "player-play", "34d399", "059669", "ferramentas")
            }
            return "ok"
        if what == "tema":
            apply_theme(value)
            if not FAKE:
                omni.save_file(THEME_FILE, value)
            return "tema"
        if FAKE:
            self.__dict__.setdefault("fake_vals", {})[what] = value
            return "ok"
        if what == "brilho":
            return omni.set_screen_brightness({"value": max(10, value)})
        if what == "volume":
            return omni.set_system_volume({"value": value})
        if what == "gov":
            return omni.set_preferred_governor({"governor": value})
        if what == "part":
            return omni.usb_set_partition({"part": value})
        if what == "cpu_max":
            return omni.set_cpu_max({"mhz": value})
        if what == "gpu_max":
            return omni.set_gpu_max({"mhz": value})
        if what == "zram":
            return omni_sistema.zram_set(value)
        if what == "fonte":
            return omni.set_game_source({"source": value})
        if what == "gamma":
            return omni.set_gamma({"value": value})
        if what == "contraste":
            return self.set("gamma", 0.5 + value / 100)
        if what == "led":
            return omni.set_led({"color": value})
        if what == "busca":
            put_flag(BUSCA, value)
            return "ok"
        if what == "remoto":
            return "ok" if FAKE else omni_sistema.usbnet_services(value == "ligados")
        if what == "inverter":            # A com B e X com Y, sempre juntos
            if FAKE:
                return "ok"
            on = {"on": value == "ligado"}
            omni.set_swap_ab(on)
            omni.set_swap_xy(on)
            return "ok"
        if what.startswith("at_"):
            return omni.set_atalho({"key": what[3:], "value": value})

    def run(self, tool, args=None):
        if FAKE:
            time.sleep(1.2)
            return "Escrita: 18.2 MB/s\nLeitura: 41.0 MB/s"
        return omni.run_tool({"tool": tool, "args": args or {}})


TURBO = "/run/omni36os-turbo"           # boot em andamento com tudo no máximo (omni36os-turbo)
D = Data()
if not FAKE:
    try:
        omni.migrate_cpu_settings()   # modo do processador de versões antigas
        # no boot o omni36os-turbo deixou tudo no máximo: o mínimo só vem com o menu pronto (App.turbo_off)
        if os.environ.get("OMNI_HUB") != "jogo" and not os.path.exists(TURBO):   # jogo pausado: voltaria lento
            omni.relax_clocks()       # menu = mínimo (o port deixou tudo no máximo)
    except OSError:
        pass


# --- controles de uma página ---

class Action:
    def __init__(self, label, icon, fn, confirm=None, danger=False, cancel=False):
        self.label, self.icon, self.fn, self.confirm, self.danger = label, icon, fn, confirm, danger
        self.cancel = cancel          # a confirmação abre com "Cancelar" escolhido (evita um toque a mais)


class Slider:
    def __init__(self, label, icon, key, step=10, lo=0):
        self.label, self.icon, self.key, self.step, self.lo = label, icon, key, step, lo
        self.value = D.get(key)
        self.shown = float(self.value)


# ferramentas perigosas: (segundos de espera, segurar A, o que pode dar errado, como desfazer)
BOOT_UNDO = omni_i18n._("ui_danger_boot_undo")
DANGER = {
    "dArkOSen_dtb_patcher_v1.2.sh": (10, True, omni_i18n._("ui_danger_wrong_dtb"), BOOT_UNDO),
    "60hz_display_timing_patcher.sh": (10, True, omni_i18n._("ui_danger_bad_timing"), BOOT_UNDO),
    "Restore dArkOSen.sh": (10, True, omni_i18n._("ui_danger_restore_darken"), BOOT_UNDO),
    "fix-sd2-mount.sh": (10, False, omni_i18n._("ui_danger_rebuild_dtb"), BOOT_UNDO),
    "Enable Quick Mode.sh": (5, False, omni_i18n._("ui_danger_boot_mode"), omni_i18n._("ui_danger_run_again")),
    "Remove Kodi.sh": (5, False, omni_i18n._("ui_danger_remove_kodi"), omni_i18n._("ui_danger_reinstall_kodi")),
}
ONOFF = {True: omni_i18n._("ui_settings_on"), False: omni_i18n._("ui_settings_off")}
SWAP_NAMES = {"desligado": omni_i18n._("ui_settings_off"), "ligado": omni_i18n._("ui_settings_on")}


def refresh_i18n_labels():
    """Refresh module-level labels after changing the selected language."""
    global ONOFF, SWAP_NAMES, VIS_NAMES, BLANK_NAMES
    ONOFF = {True: omni_i18n._("ui_settings_on"), False: omni_i18n._("ui_settings_off")}
    VIS_NAMES = {"capa": omni_i18n._("ui_music_cover"), "barras": omni_i18n._("ui_music_bars"), "ondas": omni_i18n._("ui_music_waves"), "anel": omni_i18n._("ui_music_ring"), "aurora": omni_i18n._("ui_music_aurora")}
    BLANK_NAMES = {30: omni_i18n._("ui_music_timeout_30"), 60: omni_i18n._("ui_music_timeout_60"), 120: omni_i18n._("ui_music_timeout_120"), 300: omni_i18n._("ui_music_timeout_300"), 0: omni_i18n._("ui_music_timeout_never")}
    SWAP_NAMES = {"desligado": omni_i18n._("ui_settings_off"), "ligado": omni_i18n._("ui_settings_on")}
HUD_FLAG, CAP_FLAG, SHOT_FLAG = "/dev/shm/omni36os-hud", "/dev/shm/omni36os-fpscap", "/dev/shm/omni36os-shot"
HUD_NAMES = {"1": "FPS", "2": omni_i18n._("ui_hud_fps_cpu"), "3": omni_i18n._("ui_hud_fps_cpu_gpu"), "4": omni_i18n._("ui_hud_fps_cpu_gpu_ram")}   # 0: escondido


def hud_step(cur, d):
    """Carrossel do contador (o mesmo do FN + X): 0 escondido, 1 a 4 mostram mais a cada passo."""
    cur = int(cur) if cur in ("0", "1", "2", "3", "4") else 0
    return str((cur + (1 if d > 0 else -1)) % 5)


def flag(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def put_flag(path, value):
    with open(path, "w") as f:
        f.write(str(value))
    try:
        os.chmod(path, 0o666)
    except OSError:
        pass
BUSCA = "/tmp/omni36os-busca" if FAKE else "/home/ark/.config/omni36os/busca"   # "desligada": sem busca automática


def busca_on():
    return flag(BUSCA) != "desligada"


PAD_DEV = "/dev/input/by-path/platform-odroidgo3-joypad-event-joystick"   # a gravação de atalho lê direto daqui
# simulador: comandos do teclado -> botões do controle (KP8 = FN), só na gravação de atalho
SIM_BUTTONS = {"ok": 305, "back": 304, "x": 307, "y": 308, "l1": 310, "r1": 311, "start": 705, "select": 704,
               "up": 544, "down": 545, "left": 546, "right": 547, "fn": 708}
# o que o ogage (serviço do dArkOSen) já faz com o FN: nenhum atalho do Omni36OS usa essas combinações
FN_SYSTEM = [("info", "tx_fn1"), ("info", "tx_fn2"), ("info", "tx_fn3")]


class Choice:
    def __init__(self, label, icon, key, options, names=None):
        self.label, self.icon, self.key, self.options = label, icon, key, options
        self.names = names or {}
        cur = D.get(key)
        self.index = options.index(cur) if cur in options else 0


IMAGE_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
# FN + Y fora de um jogo: o serviço de atalhos cria este arquivo e o Omni36OS grava a própria tela
BOOT_CIANO, BOOT_ROXO = (0x2D, 0xE2, 0xE6, 255), (0xA8, 0x55, 0xF7, 255)   # cores das telas do boot
UI_SHOT = "/dev/shm/omni36os-power/shot"
SHOT_DIR = "/roms/imagens"


VIS_NAMES = {"capa": omni_i18n._("ui_music_cover"), "barras": omni_i18n._("ui_music_bars"), "ondas": omni_i18n._("ui_music_waves"), "anel": omni_i18n._("ui_music_ring"), "aurora": omni_i18n._("ui_music_aurora")}
BLANK_NAMES = {30: omni_i18n._("ui_music_timeout_30"), 60: omni_i18n._("ui_music_timeout_60"), 120: omni_i18n._("ui_music_timeout_120"), 300: omni_i18n._("ui_music_timeout_300"), 0: omni_i18n._("ui_music_timeout_never")}
MUSIC_CFG = "/tmp/omni36os-musica.json" if FAKE else "/home/ark/.config/omni36os/musica.json"
MUSIC_DEF = {"vis": "capa", "tela": 60, "sub": False}


def music_cfg():
    try:
        with open(MUSIC_CFG) as f:
            cfg = {**MUSIC_DEF, **json.load(f)}
    except (OSError, ValueError):
        cfg = dict(MUSIC_DEF)
    if cfg["vis"] not in VIS_NAMES:   # "nenhuma" (1.12.0) virou a capa do álbum
        cfg["vis"] = "capa"
    return cfg


def music_save(**kw):
    cfg = {**music_cfg(), **kw}
    try:
        with open(MUSIC_CFG + ".tmp", "w") as f:
            json.dump(cfg, f)
        os.replace(MUSIC_CFG + ".tmp", MUSIC_CFG)
        os.chmod(MUSIC_CFG, 0o666)
    except OSError:
        pass
    return cfg


NOTE_COLORS = (hexc("fbbf24"), hexc("f97316"))
VIDEO_COLORS = (hexc("38bdf8"), hexc("8b5cf6"))
IMAGE_COLORS = (hexc("34d399"), hexc("0ea5e9"))
TEXT_EXT = (".txt", ".md", ".log", ".ini", ".cfg", ".conf")
NOTES_DIR = "/roms/notas"


def is_text(name):
    return name.lower().endswith(TEXT_EXT)


def is_image(name):
    return name.lower().endswith(IMAGE_EXT)


def subpage(action, cid):
    """Marca o botão que abre uma subpágina (o B dela volta com ele selecionado)."""
    action.sub = cid
    return action


def tip(item, text):
    """Mini explicação do controle: aparece no topo do painel da esquerda quando ele está escolhido."""
    item.tip = text
    return item


# Mini explicações por rótulo (o começo basta); Cartões põe as dele direto nos itens.
TIPS = {
    omni_i18n._("ui_wifi_action_on"): omni_i18n._("ui_tip_wifi"),
    omni_i18n._("ui_card_option_wifi_status"): omni_i18n._("ui_tip_recheck"),
    omni_i18n._("ui_card_button_test"): omni_i18n._("ui_tip_test_controller"),
    omni_i18n._("ui_card_option_fix_shortcuts"): omni_i18n._("ui_tip_hotkey_service"),
    omni_i18n._("ui_card_option_calibrate_battery"): omni_i18n._("ui_tip_battery_calibration"),
    omni_i18n._("ui_calibration_start"): omni_i18n._("ui_tip_calibration_start"),
    omni_i18n._("ui_calibration_stop"): omni_i18n._("ui_tip_calibration_stop"),
    omni_i18n._("ui_calibration_apply"): omni_i18n._("ui_tip_calibration_apply"),
    omni_i18n._("ui_calibration_restore"): omni_i18n._("ui_tip_calibration_restore"),
    omni_i18n._("ui_card_option_password"): omni_i18n._("ui_tip_password_ssh"),
    omni_i18n._("ui_card_option_samba_password"): omni_i18n._("ui_tip_password_samba"),
    omni_i18n._("ui_card_option_password_lock"): omni_i18n._("ui_tip_password_lock"),
    omni_i18n._("ui_card_option_cpu_limit"): omni_i18n._("ui_tip_cpu"),
    omni_i18n._("ui_card_option_gpu_limit"): omni_i18n._("ui_tip_gpu"),
    omni_i18n._("ui_card_option_zram"): omni_i18n._("ui_tip_zram"),
    omni_i18n._("ui_card_option_unlock_oc"): omni_i18n._("ui_tip_oc_unlock"),
    omni_i18n._("ui_card_option_lock_oc"): omni_i18n._("ui_card_lock_oc_tip"),
    omni_i18n._("ui_usb_action_universal"): omni_i18n._("ui_tip_usb_universal"),
    omni_i18n._("ui_usb_action_internet"): omni_i18n._("ui_tip_usb_internet"),
    omni_i18n._("ui_card_option_remote_services"): omni_i18n._("ui_tip_remote_services"),
    omni_i18n._("ui_usb_action_off"): omni_i18n._("ui_tip_usb_off"),
    omni_i18n._("ui_usbnet_compat_title"): omni_i18n._("ui_tip_usb_compat"),
    omni_i18n._("ui_card_option_game_source"): omni_i18n._("ui_tip_game_source"),
    omni_i18n._("ui_card_option_screen_details"): omni_i18n._("ui_tip_screen_details"),
    omni_i18n._("sub_checkup"): omni_i18n._("ui_tip_check_all"),
    omni_i18n._("sub_sobre"): omni_i18n._("ui_tip_about"),
    omni_i18n._("ui_card_option_check_repair"): omni_i18n._("ui_tip_check_repair"),
    omni_i18n._("ui_card_option_files"): omni_i18n._("ui_tip_files"),
    omni_i18n._("ui_card_option_test_ports"): omni_i18n._("ui_tip_test_ports"),
    omni_i18n._("ui_card_choose_port"): omni_i18n._("ui_tip_pick_port"),
    omni_i18n._("ui_card_option_clear_failures"): omni_i18n._("ui_tip_clear_failures"),
    omni_i18n._("ui_card_option_manual"): omni_i18n._("ui_tip_manual"),
    omni_i18n._("ui_card_option_cautions"): omni_i18n._("ui_tip_cautions"),
    omni_i18n._("ui_card_option_news"): omni_i18n._("ui_tip_news"),
    omni_i18n._("ui_card_option_credits"): omni_i18n._("ui_tip_credits"),
}


def add_tips(items):
    for it in items:
        if not getattr(it, "tip", None):
            it.tip = next((t for k, t in TIPS.items() if it.label.startswith(k)), None)
    return items


def joined(*rs):
    """Junta verificações num painel só (cards que reúnem assuntos: Cartões, Controles)."""
    found = [f for r in rs for f in r["achados"]]
    acts = [a for r in rs for a in r.get("acoes", [])]
    lv = [lvl for lvl, _ in found]
    return {"nivel": "problema" if "problema" in lv else "aviso" if "aviso" in lv else "ok",
            "achados": sorted(found, key=lambda f: {"problema": 0, "aviso": 1}.get(f[0], 2)), "acoes": acts}


def tagged(action, name):
    """Marca o controle com a ação de omni_checks que ele faz (evita repetir a sugestão)."""
    action.act = name
    return action


# --- animação ---

def approach(cur, target, dt, speed=14.0):
    return target + (cur - target) * math.exp(-speed * dt)


def quad(x0, y0, x1, y1, c_top, c_bot):
    """Retângulo em 2 triângulos com degradê vertical (para juntar vários num só desenho)."""
    return [(x0, y0, c_top), (x1, y0, c_top), (x0, y1, c_bot), (x0, y1, c_bot), (x1, y0, c_top), (x1, y1, c_bot)]


def polyline(pts, width, c):
    """Linha grossa ligando os pontos, em triângulos."""
    v, h = [], width / 2
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        dx, dy = xb - xa, yb - ya
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n * h, dx / n * h
        v += [(xa + nx, ya + ny, c), (xb + nx, yb + ny, c), (xa - nx, ya - ny, c),
              (xa - nx, ya - ny, c), (xb + nx, yb + ny, c), (xb - nx, yb - ny, c)]
    return v


class App:
    def __init__(self):
        if not FAKE:
            os.environ.setdefault("SDL_GAMECONTROLLERCONFIG_FILE", "/opt/inttools/gamecontrollerdb.txt")
            # se o launcher caiu ou reiniciou com a tela apagada pelo player, a luz volta aqui
            for p in glob.glob("/sys/class/backlight/*/bl_power"):
                try:
                    with open(p, "w") as f:
                        f.write("0")
                except OSError:
                    pass
        self.g = gfx.Gfx()
        # o SDL apaga a tela ao assumir o vídeo: redesenha a boas-vindas do boot já no primeiro
        # quadro, antes de montar o resto, para a passagem do boot ao launcher não piscar preto
        self.player = os.environ.get("OMNI_JOGADOR", "") if FAKE else omni_sistema.player_name()
        self.t = 0.0
        self.draw_welcome()
        self.g.present()
        print(f"abertura na tela {time.clock_gettime(time.CLOCK_BOOTTIME):.1f} s após ligar", file=sys.stderr, flush=True)
        self.swap = swapped_ab()
        self.swap_xy = os.path.exists("/var/cache/Switch_XY") and not FAKE
        self.running = True
        self.last_input = time.monotonic()
        self.t = 0.0
        self.sel = PORTS_AT           # a abertura entrega o destaque no Ports (centro)
        self.sel_x, self.sel_y = 0.0, 0.0
        self.deliver = None           # instante em que o menu apareceu (animação de entrega)
        self.accent = [hexc(CARDS[PORTS_AT][3]), hexc(CARDS[PORTS_AT][4])]
        self.page = None              # id do cartão aberto
        self.vol, self.vol_at = None, 0.0   # volume da pílula: lido no início e após os botões de volume
        self.last_page = None         # a página que está saindo (na transição)
        self.snap = None              # (página, última) já desenhadas nas camadas
        self.warm = [c[0] for c in CARDS] + list(SUBPAGES)  # páginas a pré-montar
        self.page_anim = 0.0          # 0 = início, 1 = página
        self.status = D.status()
        self.status_at = 0.0
        self.home_check = None
        self.modal = None             # {"title","text","icon","buttons":[...], "sel"}
        self.levels = None            # painel de brilho, contraste e volume (Tela e som)
        self.viewer = None            # imagem em tela cheia (Arquivos)
        self.music = None             # Aplicativos > Músicas (tela cheia)
        self.MUSIC_OPTIONS = self.music_options()
        self.want_shot = False        # FN + Y no menu: grava a tela no próximo quadro
        self.reader = None            # texto longo com rolagem (Ajuda)
        self.find_top = self.find_max = 0   # rolagem do diagnóstico (L1/R1)
        self.find_scroll = 0.0
        self.picker = None            # lista de ports para testar
        self.view = "menu"            # menu: os cards (tela inicial); lib: a biblioteca (card Ports)
        self.lib = {"sys": 0, "game": 0, "top": 0.0, "stop": 0.0}
        try:                          # volta para o mesmo jogo depois de jogar
            with open(LIB_POS) as f:
                self.lib.update(json.load(f))
        except (OSError, ValueError):
            pass
        self.toast = None             # (texto, nível, até)
        if not FAKE and self.player and not os.path.exists(omni_sistema.TELA):   # nome de antes da tela com nome
            threading.Thread(target=omni_sistema.set_player_name, args=(self.player,), daemon=True).start()
        self.want_power = self.want_msg = False
        self.bat_return = False
        if HUB == "jogo" and not FAKE:
            try:
                self.bat_return = time.time() - os.path.getmtime(BAT_FLAG) < 60
                os.remove(BAT_FLAG)
            except OSError:
                pass
        self.msg_t = -9.0
        signal.signal(signal.SIGUSR1, lambda *_: setattr(self, "want_power", True))
        try:
            if os.environ.get("SDL_VIDEODRIVER") == "offscreen":
                raise OSError("teste fora da tela")
            os.makedirs(POWER_SHM, exist_ok=True)
            try:
                os.chmod(POWER_SHM, 0o777)
            except OSError:
                pass
            with open(f"{POWER_SHM}/ui-pid", "w") as f:   # o power_button.py só sinaliza este
                f.write(str(os.getpid()))
            os.chmod(f"{POWER_SHM}/ui-pid", 0o666)
        except OSError:
            pass
        signal.signal(signal.SIGUSR2, lambda *_: setattr(self, "want_msg", True))
        self.busy = None              # texto enquanto uma tarefa roda
        self.held = {}                # direção -> próximo repeat
        self.combo = set()
        self.pending = []
        self.alerts = {}              # cartão -> (pior nível, quantos alertas)
        self.results = {}             # cartão -> última verificação
        # Tela de carregamento: as verificações rodam antes do menu aparecer,
        # para não disputar o processador com a animação depois.
        self.loading = True
        self.load_done, self.load_total, self.load_label = 0, 1, omni_i18n._("ui_preparing")
        self.load_shown = 0.0
        self.t_start = time.monotonic()
        self.refresh_at = None
        cached = self.load_state()
        self.fast = HUB == "jogo" and not FAKE   # power num jogo: menu na hora, verificações depois
        if self.fast:
            self.refresh_at = time.monotonic() + 4
            self.warm_later, self.warm = self.warm, []
        elif cached:
            self._all_checked(cached)
            self.refresh_at = time.monotonic() + 4      # refaz as verificações depois que o menu abrir
            self.warm_later, self.warm = self.warm, []   # as páginas se montam com o menu parado
        else:
            self.worker(self.check_all, self._all_checked, quiet=True)

    # --- tarefas em segundo plano ---

    def worker(self, fn, done, busy=None, quiet=False):
        if busy:
            self.busy = busy

        def run():
            try:
                res = fn()
            except Exception as e:  # mostra o erro em vez de travar a tela
                res = e
            self.pending.append((done, res, bool(busy)))
        threading.Thread(target=run, daemon=True).start()

    def _home_checked(self, res):
        if not isinstance(res, Exception):
            self.home_check = res

    # Verificação de cada cartão (sem o teste de velocidade, que é demorado):
    # dá os pontos de notificação da tela inicial.
    def card_check(self, cid):
        if cid == "desempenho" and not FAKE:
            return self._lento_rapido()
        if cid == "cartoes" and not FAKE:   # Cartões = cartões + porta USB
            return joined(self._cartoes(), D.check("pc"))
        if cid == "controles":
            out, acts = [], []
            if not FAKE:
                omni_checks.check_services(out, acts)
            return joined({"achados": out or [("ok", omni_i18n._("ui_controls_ok"))], "acoes": acts})
        if cid == "testar":
            return self._testar()
        if cid == "ports":
            idx = self.games()
            n = sum(len(s["games"]) for s in idx)
            return {"nivel": "ok", "acoes": [], "achados": [("ok", omni_i18n._("ui_library_count").format(count=n))]}
        if cid == "backup":
            return self._backup()
        if cid == "ferramentas":
            return self._ferramentas()
        if cid == "rede" and FAKE:
            on = getattr(self, "fake_wifi", True)
            return {"nivel": "ok", "acoes": [], "achados": [("ok", omni_i18n._("ui_fake_wifi_connected")),
                                                            ("ok", omni_i18n._("ui_fake_console_ip"))] if on else
                    [("info", omni_i18n._("ui_fake_wifi_off"))]}
        if cid == "rede":
            return omni_checks.finish(omni_sistema.wifi_status(), [], {})
        if cid == "moonlight":
            if not FAKE and not omni_apps.installed("moonlight"):
                return {"nivel": "info", "acoes": [], "achados": [("info", omni_i18n._("ui_app_not_installed"))]}
            return {"nivel": "ok", "acoes": [], "achados": [
                ("ok", omni_i18n._("ui_moonlight_path")),
                ("info", omni_i18n._("ui_moonlight_network"))]}
        if cid == "gfn":
            if not FAKE and not omni_gfn.installed():
                return {"nivel": "info", "acoes": [], "achados": [("info", omni_i18n._("ui_app_not_installed"))]}
            v = "beta" if FAKE else (omni_gfn.version() or "instalado")
            return {"nivel": "ok", "acoes": [], "achados": [
                ("ok", omni_i18n._("ui_gfn_version_path").format(version=v)),
                ("info", omni_i18n._("ui_gfn_cloud_info"))]}
        if cid in ("usbrede", "calibracao"):
            if FAKE:
                return {"nivel": "ok", "acoes": [], "achados": [("ok", omni_i18n._("ui_fake_check_ok").format(page=cid))]}
            fn = {"usbrede": omni_sistema.usbnet_status, "calibracao": omni_sistema.cal_status}[cid]
            return omni_checks.finish(fn(), [], {})
        if cid == "atalhos":
            hud = FAKE or os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hud", "omni_hud.so"))
            return {"nivel": "ok" if hud else "aviso", "acoes": [], "achados": [
                ("ok" if hud else "aviso", omni_i18n._("ui_hotkeys_working" if hud else "ui_hotkeys_missing")),
                *[(lvl, omni_i18n._(key)) for lvl, key in FN_SYSTEM]]}
        if cid == "seguranca":
            locked = (os.environ.get("OMNI_TRAVA") == "1") if FAKE else omni_sistema.lock_on()
            return {"nivel": "ok", "acoes": [], "achados": [
                ("ok", omni_i18n._("ui_password_locked_info") if locked else omni_i18n._("ui_password_unlocked_info")),
                ("ok", omni_i18n._("ui_system_user_password_info"))]}
        if cid == "tela":                 # Tela e som: brilho e contraste + as duas verificações (o som já diz volume e saída)
            now = [("info", omni_i18n._("ui_brightness_contrast").format(brightness=D.get('brilho'), contrast=D.get('contraste')))]
            if FAKE:
                return joined({"achados": now, "acoes": []}, D.check("atualizar"), D.check("bateria"))
            a, b, c = D.check("atualizar"), D.check("sem_som"), D.check("bateria")
            return omni_checks.finish(now + a["achados"] + b["achados"] + c["achados"],
                                      a["acoes"] + b["acoes"] + c["acoes"],
                                      {**a.get("fatos", {}), **b.get("fatos", {}), **c.get("fatos", {})})
        if cid == "apps":
            here = omni_musica.roots() if not FAKE else [("/roms/musicas", "Cartão 1")]
            return {"nivel": "ok", "acoes": [], "achados": [
                ("ok", omni_i18n._("ui_music_folders").format(folders=", ".join(f"{n} ({p})" for p, n in here))) if here else
                ("info", omni_i18n._("ui_music_folder_create")),
                ("info", omni_i18n._("ui_music_subfolders")),
                ("info", omni_i18n._("ui_media_folders")),
                ("info", omni_i18n._("ui_files_open_app"))]}
        if FAKE and cid == "cartoes":
            return joined(D.check("cartoes"), D.check("pc"))
        name = {"tela": "atualizar"}.get(cid, cid)
        return D.check(name)

    def check_all(self):
        out = {}
        todo = [c for c in CARDS + [card_info(c) for c in SUBPAGES]
                if c[0] not in ("geral", "sobre") and (RESUME != "testar" or c[0] == "testar")]
        if self.loading:              # na atualização em segundo plano não há tela de carregamento
            self.warm.insert(0, "home")
            self.load_total = len(todo) + len(self.warm)
        for k, (cid, title, *_) in enumerate(todo):
            self.load_label = omni_i18n._("ui_checking_item").format(item=title.lower())
            self.load_done = k
            try:
                out[cid] = self.card_check(cid)
            except Exception as e:
                out[cid] = {"nivel": "problema", "achados": [("problema", omni_i18n._("ui_error_prefix").format(error=e))], "acoes": []}
        return out

    def save_shot(self):
        """Grava a tela de agora em <cartão 1>/imagens (PNG, com data e hora no nome)."""
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagens", "capturas") if FAKE else SHOT_DIR
        name = time.strftime("Omni36OS %Y-%m-%d %H-%M-%S.png")
        try:
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, name)
            if not self.g.screenshot_png(path):
                raise OSError("falhou ao gravar")
            if not FAKE:
                os.chown(folder, 1000, 1000)
                os.chown(path, 1000, 1000)
            self.toast = (omni_i18n._("ui_screenshot_saved"), "ok", self.t + 2.5)
        except OSError as e:
            self.toast = (omni_i18n._("ui_screenshot_failed").format(error=e), "aviso", self.t + 3)

    def load_state(self):
        if not RESUME or RESUME == "testar" or FAKE:
            return None
        try:
            with open(STATE_CACHE) as f:
                st = json.load(f)
            os.remove(STATE_CACHE)
        except (OSError, ValueError):
            return None
        if st.get("versao") != omni_version() or not 0 <= time.time() - st.get("t", 0) < STATE_MAX_AGE:
            return None
        return st.get("resultados") or None

    def save_state(self):
        """Só ao sair para um jogo ou ferramenta (o launch-direct.sh reabre o Omni36OS na volta)."""
        if FAKE or not self.results or not os.path.exists(omni.HANDOFF):
            return
        try:
            res = dict(self.results)
            if self.home_check:
                res["checkup"] = self.home_check
            with open(STATE_CACHE + ".tmp", "w") as f:
                json.dump({"versao": omni_version(), "t": time.time(), "resultados": res}, f, default=str)
            os.replace(STATE_CACHE + ".tmp", STATE_CACHE)
        except (OSError, TypeError, ValueError):
            pass

    def _all_checked(self, res):
        print(f"verificações prontas em {time.monotonic() - self.t_start:.1f} s", file=sys.stderr, flush=True)
        if isinstance(res, Exception):
            return
        self.home_check = res.get("checkup")
        for cid, r in res.items():
            self.set_result(cid, r)

    def set_result(self, cid, r):
        self.results[cid] = r
        home = PARENT.get(cid, cid)
        worst, n = "ok", 0
        for c in [home] + [k for k, p in PARENT.items() if p == home and k != "checkup"]:
            rc = self.results.get(c)
            if not rc:
                continue
            k = sum(1 for lvl, _ in rc["achados"] if lvl in ("aviso", "problema"))
            if k:
                n += k
                worst = "problema" if "problema" in (worst, rc["nivel"]) else "aviso"
        if n:
            self.alerts[home] = (worst, n)
        else:
            self.alerts.pop(home, None)

    # --- páginas ---

    def open_page(self, cid):
        self.page = self.last_page = cid
        self.items, self.item_sel, self.item_y, self.item_h = self.build_items(cid), 0, 0.0, 0.0
        self.act_off = 0.0
        self.findings, self.info = None, []
        self.find_top, self.find_max, self.find_scroll = 0, 0, 0.0
        if cid in self.results:       # já verificado no carregamento
            self._got_findings(self.results[cid])
        else:
            self.reload_findings()

    def recheck(self, cid):
        """Refaz a verificação de um cartão em segundo plano (a página, se aberta, é atualizada)."""
        def done(res):
            if not isinstance(res, Exception):
                self.set_result(cid, res)
                if self.page == cid:
                    self._got_findings(res)
        self.worker(lambda: self.card_check(cid), done)

    def reload_findings(self, quiet=False):
        cid = self.page
        if cid in ("geral", "sobre"):
            self.findings = {"nivel": "ok", "achados": about_findings(), "acoes": []}
            return
        if not quiet:                 # quiet: mantém o diagnóstico na tela até o novo chegar
            self.findings = None

        def done(res):
            if not isinstance(res, Exception):
                self.set_result(cid, res)
            if self.page == cid:
                self._got_findings(res)
        self.worker(lambda: self.card_check(cid), done)

    def _lento_rapido(self):
        f = omni_checks.cpu_facts()
        out = []
        omni_checks.check_temp(f, out)
        out.append(("ok", omni_i18n._("ui_performance_menu_info").format(freq=f['freq_mhz'])) )
        omni_checks.check_overclock(f, out, [])   # tirar o OC é o seletor omni_i18n._("ui_card_option_cpu_limit") daqui
        acts = []
        z = omni.zram_facts()
        cpu = omni_i18n._("ui_frequency_auto").format(freq=omni.auto_ceiling()) if not f["cpu_max_mhz"] else f"{f['cpu_max_mhz']} MHz"
        gpu = omni_i18n._("ui_frequency_auto_f").format(freq=omni.gpu_auto_ceiling()) if not f["gpu_max_mhz"] else f"{f['gpu_max_mhz']} MHz"
        out.append(("info", omni_i18n._("ui_performance_limits").format(cpu=cpu, gpu=gpu, zram=z['zram_mb'], used=z['zram_usado_mb'])))
        return omni_checks.finish(out, acts, f)

    def _testar(self):
        groups = FAKE_PORTS if FAKE else omni.port_groups()
        res = {} if FAKE else omni.port_results()
        out = []
        self.port_count = sum(len(g["ports"]) for g in groups)
        acks = set() if FAKE else omni.port_acks()
        for g in groups:
            out.append(("ok", omni_i18n._("ui_ports_group_count").format(count=len(g['ports']), label=g['label'])) )
        names = {os.path.basename(p)[:-3] for g in groups for p in g["ports"]}
        fails = sorted(n for n, r in res.items() if r[0] == "falhou" and n in names
                       and f"{n}|{r[1]}" not in acks)
        seen = sum(1 for n, r in res.items() if r[0] == "falhou" and n in names and f"{n}|{r[1]}" in acks)
        if seen:
            out.append(("info", omni_i18n._("ui_port_test_seen_failures").format(count=seen)))
        oks = sum(1 for n, r in res.items() if r[0] == "ok" and n in names)
        for n in fails:
            out.append(("aviso", omni_i18n._("ui_port_test_failed").format(name=n, test=res[n][1], report=f"logs/teste de ports/teste_{n}.txt")))
        if oks:
            out.append(("ok", omni_i18n._("ui_port_test_passed").format(count=oks)))
        out.append(("info", omni_i18n._("ui_port_test_duration")) )
        return omni_checks.finish(out, [], {}) if not FAKE else {
            "nivel": "aviso" if fails else "ok", "achados": out, "acoes": []}

    def ask_dtb(self):
        """Ferramentas > Trocar DTB: alerta com trava de 10 s antes de liberar o Trocar."""
        if self.busy_game():
            return
        lock = 10

        def go():
            if FAKE:
                self.toast = (omni_i18n._("ui_dtb_fake_restarting"), "ok", self.t + 3)
                return
            self.worker(omni.dtb_retest, lambda r: self.__setattr__(
                "toast", (str(r), "problema" if str(r).startswith("Erro") else "ok", self.t + 5)),
                busy=omni_i18n._("ui_dtb_retest_busy"))
        self.modal = {"title": omni_i18n._("ui_dtb_retest_title"), "icon": "alert-triangle", "sel": 1,
                      "buttons": [omni_i18n._("ui_dtb_retest_button"), omni_i18n._("ui_cancel")], "fns": [go, lambda: None],
                      "lock": (0, self.t + lock), "danger": True,
                      "text": omni_i18n._("ui_dtb_retest_text")}

    def refresh_ports(self):
        """Ferramentas > Atualizar ports: relê tudo do zero (lista, capas e descrições locais)."""
        def run():
            if FAKE:
                return sum(len(sy["games"]) for sy in FAKE_GAMES)
            idx = omni_games.index(force=True)
            return sum(len(sy["games"]) for sy in idx)

        def done(res):
            if isinstance(res, Exception):
                self.toast = (omni_i18n._("ui_refresh_ports_error").format(error=res), "problema", self.t + 4)
                return
            if not FAKE:
                self.games_idx = None
                self.games(force=False)
            self.__dict__.pop("meta_cache", None)      # capas e descrições lidas de novo
            self.toast = (omni_i18n._("ui_refresh_ports_done").format(count=res), "ok", self.t + 3)
        self.worker(run, done, busy=omni_i18n._("ui_refresh_ports_busy"))

    def check_runtimes(self):
        """Ferramentas > Runtimes faltando: varre os ports e, com internet, oferece baixar o que falta."""
        import omni_runtimes as R

        def run():
            if FAKE:
                return {"mono-6.12.0.122-aarch64.squashfs": ["TMNT"]}
            return R.scan()

        def done(res):
            if isinstance(res, Exception):
                self.toast = (omni_i18n._("ui_runtime_search_error").format(error=res), "problema", self.t + 4)
                return
            if not res:
                self.toast = (omni_i18n._("ui_runtime_none"), "ok", self.t + 3)
                return
            names = sorted(res)
            lines = "\n".join(f"{n[:-9]}: {', '.join(res[n][:3])}" + ("..." if len(res[n]) > 3 else "")
                              for n in names[:6])
            more = f"\n+{len(names) - 6} outros" if len(names) > 6 else ""
            head = omni_i18n._("ui_runtime_missing_title").format(count=len(names))
            if not (FAKE or R.online()):
                self.modal = {"title": head, "icon": "database", "sel": 0, "buttons": [omni_i18n._("btn_ok")],
                              "text": f"{lines}{more}\n{omni_i18n._('ui_runtime_wifi_hint')}"}
                return
            self.modal = {"title": head, "icon": "database", "sel": 0, "buttons": [omni_i18n._("ui_download"), omni_i18n._("ui_not_now")],
                          "fns": [lambda: download(names), lambda: None],
                          "text": f"{lines}{more}\n{omni_i18n._('ui_runtime_download_prompt')}"}

        def download(names):
            def get():
                if FAKE:
                    return names, []
                return R.sync(names=names, log=lambda *_: None)

            def fin(res):
                if isinstance(res, Exception):
                    self.toast = (omni_i18n._("ui_runtime_download_error").format(error=res), "problema", self.t + 4)
                    return
                got, bad = res
                if bad:
                    self.modal = {"title": omni_i18n._("ui_runtime_download_result").format(got=len(got), failed=len(bad)), "icon": "database",
                                  "sel": 0, "buttons": [omni_i18n._("btn_ok")], "text": "\n".join(bad[:6])}
                else:
                    self.toast = (omni_i18n._("ui_runtime_downloaded").format(count=len(got)),
                                  "ok", self.t + 3)
            self.worker(get, fin, busy=omni_i18n._("ui_runtime_downloading"))
        self.worker(run, done, busy=omni_i18n._("ui_runtime_searching"))

    def games(self, force=False):
        if FAKE:
            self.games_idx = FAKE_GAMES
        elif force or not getattr(self, "games_idx", None):
            self.games_idx = omni_games.index(force)
        return self.games_idx

    def _backup(self):
        if FAKE:
            return {"nivel": "ok", "acoes": [], "achados": [("info", omni_i18n._("ui_backup_none"))]}
        out = [("info", omni_i18n._("ui_backup_location").format(path=omni_backup.backup_dir()))]
        last = omni_backup.last_backups()
        for mod, (name, *_x) in omni_backup.MODULES.items():
            if mod in last:
                out.append(("ok", omni_i18n._("ui_backup_last").format(name=name, date=last[mod][1])))
            else:
                out.append(("info", omni_i18n._("ui_backup_module_none").format(name=name)))
        out.append(("info", omni_i18n._("ui_backup_scope")))
        return omni_checks.finish(out, [], {})

    def _cartoes(self):
        out = []
        for c in omni_checks.sd_facts()["cartoes"]:
            fab = f", {c['fabricante']}" if c["fabricante"] != "desconhecido" else ""   # sem marca: só no teste
            out.append(("ok", omni_i18n._("ui_sd_card_summary").format(card=1 if c['cartao'] == 'sistema' else 2, size=c['tamanho_gb'], manufacturer=fab)))
        omni_checks.check_disk(out)
        for part, r in omni.last_scan().items():
            ok = r["resultado"] == "clean"
            status = r["resultado"]
            key = {"clean": "ui_scan_clean", "repaired": "ui_scan_repaired", "failed": "ui_scan_failed"}.get(status)
            txt = omni_i18n._(key) if key else omni_i18n._("ui_scan_unknown").format(result=status)
            out.append(("ok" if ok else "aviso", omni_i18n._("ui_scan_last_result").format(part=part, date=r['quando'], result=txt)))
        return omni_checks.finish(out, [], {})

    def _got_findings(self, res):
        if isinstance(res, Exception):
            self.findings = {"nivel": "problema", "achados": [("problema", omni_i18n._("ui_error_prefix").format(error=res))], "acoes": []}
            return
        # alertas das subpáginas (ex.: Cartões SD em Desempenho) aparecem aqui também
        extra_alerts = []
        for sub, parent in PARENT.items():
            r = self.results.get(sub)
            if parent == self.page and r:
                n = sum(1 for lvl, _ in r["achados"] if lvl in ("aviso", "problema"))
                if n:
                    extra_alerts.append((r["nivel"], omni_i18n._("tx_alerts").format(page=SUBPAGES[sub][0], count=n)))
        if extra_alerts:
            order = {"problema": 0, "aviso": 1, "ok": 2, "info": 3}
            res = dict(res, achados=sorted(extra_alerts + list(res["achados"]), key=lambda x: order.get(x[0], 9)))
            if res["nivel"] == "ok" or "problema" in (lvl for lvl, _ in extra_alerts):
                res["nivel"] = "problema" if any(l == "problema" for l, _ in extra_alerts) else "aviso"
        self.findings = res
        # ações sugeridas pela verificação entram no topo da lista
        base = [i for i in self.items if not getattr(i, "suggested", False)]
        extra = []
        for a in res.get("acoes", []):
            if any(isinstance(i, Action) and getattr(i, "act", None) == a for i in base):
                continue
            act = Action(D.label(a), "bolt", lambda a=a: self.do_action(a),
                         confirm=f"{D.label(a)}?")
            act.suggested, act.act = True, a
            act.tip = omni_i18n._("ui_suggested_action_tip")
            extra.append(act)
        self.items = extra + base
        self.item_sel = min(self.item_sel, len(self.items) - 1)

    def build_items(self, cid):
        return add_tips(self._build_items(cid))

    def _build_items(self, cid):
        A = Action
        recheck = A(omni_i18n._("ui_recheck"), "refresh", self.reload_findings)
        if cid == "checkup":
            return [recheck]
        if cid == "controles":
            return [A(omni_i18n._("ui_card_button_test"), "device-gamepad-2", self.open_pad),
                    tip(Choice(omni_i18n._("ui_card_option_switch_buttons"), "arrows-exchange", "inverter", ["desligado", "ligado"], SWAP_NAMES),
                        omni_i18n._("ui_card_toggle_buttons_tip")),
                    subpage(A(omni_i18n._("ui_card_option_shortcuts"), "keyboard", lambda: self.open_page("atalhos")), "atalhos"),
                    A(omni_i18n._("ui_card_option_fix_shortcuts"), "tool", lambda: self.native("fix_hotkeys", omni_i18n._("ui_card_restart_hotkeys")),
                      confirm=omni_i18n._("ui_card_fix_hotkeys_confirm")),
                    recheck]
        if cid == "apps":
            return [tip(A(omni_i18n._("ui_card_music_subtitle"), "music", self.open_music),
                        omni_i18n._("ui_build_apps_music_tip")),
                    tip(A(omni_i18n._("ui_card_videos"), "movie", lambda: self.open_videos()),
                        omni_i18n._("ui_build_apps_videos_tip")),
                    tip(A(omni_i18n._("ui_card_images"), "photo-search", lambda: self.open_images()),
                        omni_i18n._("ui_build_apps_images_tip")),
                    tip(A(omni_i18n._("ui_card_notes"), "notes", lambda: self.open_notes()),
                        omni_i18n._("ui_build_apps_notes_tip")),
                    tip(subpage(A("GeForce NOW", "device-tv", lambda: self.open_page("gfn")), "gfn"),
                        omni_i18n._("ui_build_apps_gfn_tip")),
                    tip(subpage(A("Moonlight", "device-tv", lambda: self.open_page("moonlight")), "moonlight"),
                        omni_i18n._("ui_build_apps_moonlight_tip"))]
        if cid == "tela":
            return [tip(A(omni_i18n._("ui_build_display_levels"), "adjustments", self.open_levels),
                        omni_i18n._("ui_card_levels_tip")),
                    Choice(omni_i18n._("ui_card_option_theme"), "palette", "tema", list(THEMES), {"escuro": omni_i18n._("ui_settings_theme_dark"), "claro": omni_i18n._("ui_settings_theme_light")}),
                    Choice(omni_i18n._("ui_card_option_led"), "bulb", "led", ["verde", "vermelho"], {"verde": omni_i18n._("ui_settings_green"), "vermelho": omni_i18n._("ui_settings_red")}),
                    A(omni_i18n._("ui_card_option_screen_details"), "info-circle", lambda: self.run_info(omni_i18n._("ui_card_screen_and_model"), "detect_hardware_and_screen")),
                    subpage(A(omni_i18n._("ui_card_option_calibrate_battery"), "battery-2", lambda: self.open_page("calibracao")), "calibracao"),
                    tagged(A(omni_i18n._("ui_card_option_restore_audio"), "rotate", lambda: self.do_action("restaurar_audio"),
                             confirm=omni_i18n._("ui_card_audio_restore_prompt")),
                           "restaurar_audio")]
        if cid == "geral":
            lang_names = {lang: name for lang, name in omni_i18n.available_languages()}
            current_lang = omni_i18n.get_lang()
            return [Choice(omni_i18n._("label_language"), "language", "idioma",
                          [l for l, _ in omni_i18n.available_languages()], lang_names),
                    A(f"{omni_i18n._('menu_player_name')}: {self.player or omni_i18n._('ui_player_name_empty')}", "users", lambda: self.ask_name(first=False)),
                    subpage(A(omni_i18n._("sub_seguranca"), "lock", lambda: self.open_page("seguranca")), "seguranca"),
                    subpage(A(omni_i18n._("sub_backup"), "device-floppy", lambda: self.open_page("backup")), "backup"),
                    tip(A(omni_i18n._("menu_update_check"), "refresh", self.update_check),
                        omni_i18n._("ui_build_general_update_tip")),
                    *([tip(A(omni_i18n._("menu_update_back"), "rotate", self.update_back,
                             confirm=omni_i18n._("ui_update_back_confirm"), cancel=True),
                           omni_i18n._("ui_build_general_update_back_tip"))]
                      if not FAKE and omni_update.can_go_back() else []),
                    subpage(A(omni_i18n._("sub_checkup"), "stethoscope", lambda: self.open_page("checkup")), "checkup"),
                    subpage(A(omni_i18n._("sub_sobre"), "help-circle", lambda: self.open_page("sobre")), "sobre"),
                    tip(A(omni_i18n._("ui_card_ssh_mode"), "plug", self.ssh_mode_on), omni_i18n._("ui_build_ssh_mode_tip")),
                    A(omni_i18n._("menu_reset"), "rotate", self.ask_reset)]
        if cid == "atalhos":
            combos = D.get("at_combos")
            out = [tip(Choice(f"{name} · {omni_combos.text(combos[k])}", icon, "at_" + k, [True, False], ONOFF),
                       omni_combos.tip(k, combos))
                   for k, (name, icon, *_x) in omni_combos.ACTIONS.items()]
            return out + [tip(A(omni_i18n._("ui_card_custom_shortcut"), "pencil", self.pick_atalho),
                              omni_i18n._("ui_build_shortcuts_custom_tip")),
                          tip(A(omni_i18n._("ui_card_restore_default_buttons"), "rotate", self.reset_combos,
                                confirm=omni_i18n._("ui_shortcuts_restore_confirm")),
                              omni_i18n._("ui_build_shortcuts_restore_tip"))]
        if cid == "seguranca":
            locked = (os.environ.get("OMNI_TRAVA") == "1") if FAKE else omni_sistema.lock_on()
            return [A(omni_i18n._("ui_card_option_password"), "lock", self.ask_password),
                    A(omni_i18n._("ui_card_option_samba_password"), "device-floppy", self.ask_samba),
                    A(omni_i18n._("ui_build_security_lock").format(state=omni_i18n._("ui_build_on") if locked else omni_i18n._("ui_build_off")), "lock", self.ask_lock)]
        if cid == "desempenho":
            return [tip(Choice(omni_i18n._("ui_card_option_cpu_limit"), "gauge", "cpu_max", D.get("cpu_freqs"),
                               {f: omni_i18n._("ui_choice_automatic") if not f else f"{f} MHz" + (" (OC)" if f > 1296 else "")
                                for f in D.get("cpu_freqs")}),
                        omni_i18n._("ui_build_cpu_tip")),
                    tip(Choice(omni_i18n._("ui_card_option_gpu_limit"), "device-gamepad-2", "gpu_max", D.get("gpu_freqs"),
                               {f: omni_i18n._("ui_choice_automatic") if not f else f"{f} MHz" + (" (OC)" if f > 520 else "")
                                for f in D.get("gpu_freqs")}),
                        omni_i18n._("ui_build_gpu_tip")),
                    tip(Choice(omni_i18n._("ui_card_option_zram"), "database", "zram", ZRAM_SIZES,
                               {m: f"{m} MB" if m else omni_i18n._("ui_choice_zram_off") for m in ZRAM_SIZES}),
                        omni_i18n._("ui_build_zram_tip")),
                    A(omni_i18n._("ui_card_option_lock_oc"), "lock", self.lock_oc,
                      confirm=omni_i18n._("ui_build_lock_oc_confirm")) if D.get("oc") else
                    A(omni_i18n._("ui_card_option_unlock_oc"), "gauge", self.ask_overclock)]
        if cid == "cartoes":
            on = D.get("pendrive")
            tog = A(omni_i18n._("ui_usb_mode_off" if on else "ui_usb_mode_on"), "power",
                    lambda: self.do_action("desligar_pendrive" if on else "ligar_pendrive"),
                    confirm=omni_i18n._("ui_usb_mode_off_confirm" if on else "ui_usb_mode_on_confirm"))
            tog.act = "desligar_pendrive" if on else "ligar_pendrive"
            mounted = getattr(self, "fake_usb", False) if FAKE else os.path.ismount("/mnt/usbdrive")
            return [*([Choice(omni_i18n._("ui_card_option_game_source"), "folder", "fonte", list(SOURCE_NAMES), SOURCE_NAMES)]
                      if FAKE or os.path.ismount("/roms2") else []),   # sem ROMS2: só ROMS, sem escolha
                    *self.card2_items(),
                    tip(A(omni_i18n._("ui_card_option_cards_detail") if self.sd_count() > 1 else omni_i18n._("ui_card_option_card_detail"), "info-circle",
                          self.speed_test),
                        omni_i18n._("ui_build_cards_detail_tip")),
                    tip(tog, omni_i18n._("ui_tip_usb_mode")),
                    *([tip(Choice(omni_i18n._("ui_card_option_partition_pc"), "device-floppy", "part", ["roms2", "roms"],
                                  {"roms2": "ROMS2", "roms": "ROMS"}),
                           omni_i18n._("ui_tip_partition"))]
                      if FAKE or os.path.ismount("/roms2") else []),   # sem cartão 2: sempre ROMS, sem escolha
                    tip(A(omni_i18n._("ui_card_option_unmount_usb"), "player-eject", lambda: self.native("usb_umount", omni_i18n._("ui_usb_drive_connecting")))
                        if mounted else
                        A(omni_i18n._("ui_card_option_mount_usb"), "plug", lambda: self.native("usb_mount", omni_i18n._("ui_usb_drive_mounting"))),
                        self.pendrive_tip(mounted)),
                    tip(tagged(A(omni_i18n._("ui_card_option_clean_mac"), "x", lambda: self.do_action("limpar_mac", omni_i18n._("ui_clean_mac_busy")),
                                 confirm=omni_i18n._("ui_clean_mac_confirm")),
                               "limpar_mac"),
                        omni_i18n._("ui_tip_clean_mac")),
                    A(omni_i18n._("ui_card_option_check_repair"), "device-sd-card", lambda: self.run_tool_toast("schedule_scan"),
                      confirm=omni_i18n._("ui_repair_confirm"), danger=True),
                    tip(A(omni_i18n._("ui_card_option_restore_boot"), "arrow-back-up", lambda: self.run_tool_toast("usb_restore"),
                          confirm=omni_i18n._("ui_restore_boot_confirm"), danger=True),
                        omni_i18n._("ui_tip_restore_boot"))]
        if cid == "ferramentas":
            out = [A(omni_i18n._("ui_card_option_files"), "folder", self.open_files),
                   subpage(A(omni_i18n._("ui_ports_test"), "player-play", lambda: self.open_page("testar")), "testar"),
                   tip(A(omni_i18n._("ui_card_update_ports"), "refresh", self.refresh_ports),
                       omni_i18n._("ui_build_refresh_ports_tip")),
                   tip(Choice(omni_i18n._("ui_card_option_search_auto"), "photo-search", "busca", ["ligada", "desligada"],
                              {"ligada": omni_i18n._("ui_settings_on"), "desligada": omni_i18n._("ui_settings_off")}),
                       omni_i18n._("ui_search_auto_tip"))]
            out += [tip(A(t["name"], "device-gamepad-2" if "PortMaster" in t["name"] else "folder",
                          lambda t=t: self.ask_tool(t)),
                        f"{t.get('desc', '')} {omni_i18n._('ui_tip_tool_suffix')}".strip())
                    for t in self.tool_list()]
            out.append(tip(A(omni_i18n._("ui_card_change_dtb"), "device-tv", self.ask_dtb),
                           omni_i18n._("ui_tip_change_dtb")))
            return out
        if cid == "rede":
            on = getattr(self, "fake_wifi", True) if FAKE else omni_sistema.wifi_on()
            tether = getattr(self, "fake_tether", True) if FAKE else omni_sistema.ancoragem_on()
            return [tip(A(omni_i18n._("ui_build_wifi_off" if on else "ui_build_wifi_on"), "wifi-off" if on else "wifi",
                          lambda: self.wifi_toggle(not on)),
                        omni_i18n._("ui_tip_wifi_off" if on else "ui_tip_wifi_on")),
                    tip(A(omni_i18n._("ui_build_network_search"), "refresh", self.wifi_scan),
                        omni_i18n._("ui_build_network_scan_tip")),
                    tip(A(omni_i18n._("ui_build_network_saved"), "device-floppy", self.wifi_saved),
                        omni_i18n._("ui_build_network_saved_tip")),
                    tip(A(omni_i18n._("ui_build_network_disconnect"), "plug-connected-x", lambda: self.wifi_run(omni_sistema.wifi_disconnect if not FAKE else
                                                                    (lambda: omni_i18n._("ui_usb_net_disconnected")), omni_i18n._("ui_usb_net_disconnect_busy"))),
                        omni_i18n._("ui_tip_disconnect")),
                    tip(A(omni_i18n._("ui_tether_on" if tether else "ui_tether_off"), "usb",
                          lambda: self.tether_toggle(not tether)),
                        omni_i18n._("ui_tether_tip")),
                    tip(subpage(A(omni_i18n._("ui_usb_network"), "network", lambda: self.open_page("usbrede")), "usbrede"),
                        omni_i18n._("ui_usb_net_intro_tip")),
                    recheck]
        if cid == "usbrede":
            S = omni_sistema if not FAKE else None
            run = lambda fn, busy: (lambda: self.worker(fn if S else (lambda: "teste"), self._sys_done, busy=busy))
            mode = S.usbnet_mode() if S else self.__dict__.get("fake_vals", {}).get("usbnet", "desligada")
            if not S:
                def fake(m, txt):
                    return lambda: self.__dict__.setdefault("fake_vals", {}).update(usbnet=m) or txt
                run_u = lambda f: (lambda: self.worker(f, self._sys_done, busy=omni_i18n._("ui_usbnet_mode_busy")))
                uni = run_u(fake("universal", omni_i18n._("ui_usbnet_fake_universal")))
                net = run_u(fake("internet", omni_i18n._("ui_usbnet_fake_internet")))
                off = run_u(fake("desligada", omni_i18n._("ui_usbnet_fake_off")))
            else:
                uni = run(S.usbnet_universal, omni_i18n._("ui_usbnet_universal_busy"))
                net = run(S.usbnet_internet, omni_i18n._("ui_usbnet_ip_busy"))
                off = run(S.usbnet_stop, omni_i18n._("ui_usbnet_off_busy"))
            on = lambda m, txt: omni_i18n._("ui_usbnet_mode_active").format(label=txt) if mode == m else omni_i18n._("ui_usbnet_mode_enable").format(label=txt)
            return [A(on("universal", omni_i18n._("ui_usbnet_mode_universal")), "check" if mode == "universal" else "usb", uni,
                      confirm=omni_i18n._("ui_usbnet_enable_universal_confirm")),
                    A(on("internet", omni_i18n._("ui_usbnet_mode_internet")), "check" if mode == "internet" else "wifi", net,
                      confirm=omni_i18n._("ui_usbnet_enable_internet_confirm")),
                    Choice(omni_i18n._("ui_remote_services_label"), "device-floppy", "remoto", ["desligados", "ligados"],
                           {"desligados": omni_i18n._("ui_remote_off"), "ligados": omni_i18n._("ui_remote_on")}),
                    A(omni_i18n._("ui_usb_action_off") if mode != "desligada" else omni_i18n._("ui_usb_network_off"), "power", off),
                    A(omni_i18n._("ui_usbnet_compat_title"), "info-circle", lambda: self.worker(
                        (S and S.usbnet_compat) or (lambda: "teste"),
                        lambda r: self.read(omni_i18n._("ui_usbnet_compat_title"), "network", str(r)), busy=omni_i18n._("ui_usbnet_compat_busy")))]
        if cid == "calibracao":
            S = omni_sistema if not FAKE else None
            run = lambda fn, busy: (lambda: self.worker(fn if S else (lambda: "teste"), self._sys_done, busy=busy))
            running = S.cal_running() if S else os.environ.get("OMNI_CALIBRANDO") == "1"
            toggle = A(omni_i18n._("ui_calibration_stop"), "x", run(S and S.cal_stop, omni_i18n._("ui_calibration_stop_busy"))) if running else \
                A(omni_i18n._("ui_calibration_start"), "player-play", run(S and S.cal_start, omni_i18n._("ui_calibration_start_busy")),
                  confirm=omni_i18n._("ui_calibration_start_confirm"))
            return [toggle,
                    A(omni_i18n._("ui_calibration_apply"), "check", run(S and S.cal_apply, omni_i18n._("ui_calibration_apply_busy")),
                      confirm=omni_i18n._("ui_calibration_apply_confirm")),
                    A(omni_i18n._("ui_calibration_restore"), "rotate", run(S and S.cal_restore, omni_i18n._("ui_calibration_restore_busy")),
                      confirm=omni_i18n._("ui_calibration_restore_confirm"), danger=True)]
        if cid == "gfn":
            ok = FAKE or omni_gfn.installed()
            get = A(omni_i18n._("ui_gfn_update" if ok else "ui_install"), "refresh", lambda: self.worker(
                (lambda: "teste") if FAKE else omni_gfn.install, self._sys_done, busy=omni_i18n._("ui_gfn_update_busy")),
                confirm=None if ok else omni_i18n._("ui_gfn_download_confirm"))
            items = [tip(Choice(omni_i18n._("ui_gfn_fn"), "keyboard", "gfn_fn", ["sistema", "gfn"],
                                {"sistema": omni_i18n._("ui_system"), "gfn": "GeForce NOW"}),
                         omni_i18n._("ui_gfn_fn_tip"))]
            return ([tip(A(omni_i18n._("ui_gfn_open"), "player-play", self.open_gfn),
                         omni_i18n._("ui_gfn_login_tip"))] + items + [get]) if ok else [get] + items
        if cid == "moonlight":
            ok = FAKE or omni_apps.installed("moonlight")
            get = A(omni_i18n._("ui_gfn_update" if ok else "ui_install"), "refresh", lambda: self.worker(
                (lambda: "teste") if FAKE else (lambda: omni_apps.install("moonlight")), self._sys_done,
                busy=omni_i18n._("ui_moonlight_update_busy")),
                confirm=None if ok else omni_i18n._("ui_moonlight_download_confirm"))
            return [tip(A(omni_i18n._("ui_moonlight_open"), "player-play", lambda: self.open_app("moonlight")),
                        omni_i18n._("ui_moonlight_pair_tip")), get] \
                if ok else [get]
        if cid == "testar":
            return [A(omni_i18n._("ui_card_choose_port"), "player-play", self.open_picker),
                    tip(A(omni_i18n._("ui_test_reports"), "notes", lambda: self.open_logs(omni_logs.TESTS, from_page=True)),
                        omni_i18n._("ui_test_reports_tip")),
                    tip(A(omni_i18n._("ui_missing_runtimes"), "database", self.check_runtimes),
                       omni_i18n._("ui_missing_runtimes_tip")),
                    A(omni_i18n._("ui_port_alerts_clear"), "check", lambda: self.run_tool_toast("clear_port_alerts")), recheck]
        if cid == "backup":
            where = "/roms/backup/omni36os" if FAKE else omni_backup.backup_dir()
            return [tip(A(omni_i18n._("ui_backup_export"), "device-floppy", lambda: self.backup_where("omni36os")),
                        omni_i18n._("ui_backup_export_tip")),
                    tip(A(omni_i18n._("ui_backup_import"), "arrow-back-up", lambda: self.backup_browse("omni36os", where)),
                        omni_i18n._("ui_backup_import_tip"))]
        if cid == "sobre":
            return [A(omni_i18n._("ui_manual_title"), "book", lambda: self.read(omni_i18n._("ui_manual_title"), "book", omni_help.manual(D.get("at_combos")))),
                    A(omni_i18n._("ui_cautions_title"), "alert-triangle", lambda: self.read(omni_i18n._("ui_cautions_title"), "alert-triangle", omni_help.cuidados_text())),
                    A(omni_i18n._("ui_news_title"), "tag", lambda: self.read(f"{omni_i18n._('ui_news_title')} · Omni36OS {omni_version()}", "tag",
                                                          omni_help.novidades_text())),
                    A(omni_i18n._("ui_credits_title"), "users", self.open_credits)]
        return [recheck]

    # --- atualização ---

    def update_check(self):
        def done(r):
            if isinstance(r, Exception):
                self.toast = (omni_i18n._("ui_update_no_response"), "aviso", self.t + 4)
            elif not r["nova"]:
                self.toast = (omni_i18n._("ui_update_current").format(version=r['atual']), "ok", self.t + 3.5)
            else:
                self.update_offer(r)
        fake = {"atual": omni_version(), "nova": "9.9.9", "tag": "omni-v9.9.9", "novidades": omni_help.NOVIDADES[:2]}
        self.worker((lambda: fake) if FAKE else omni_update.check, done, busy=omni_i18n._("ui_update_searching"))

    def update_offer(self, r):
        """Janela da versão nova: omni_i18n._("ui_not_now") vem escolhido; omni_i18n._("ui_news_button") mostra o que muda e volta aqui."""
        install = lambda: self.worker((lambda: "Teste: instalaria") if FAKE else
                                      (lambda: omni_update.install(r["tag"], r["nova"])),
                                      self._sys_done, busy=omni_i18n._("ui_update_downloading"))
        news = r.get("novidades") or []
        first = news[0][2][0] if news and news[0][2] else ""
        self.modal = {"title": f"Omni36OS {r['nova']}", "icon": "refresh", "sel": 2,
                      "buttons": [omni_i18n._("ui_update_button"), omni_i18n._("ui_news_button"), omni_i18n._("ui_not_now")],
                      "text": omni_i18n._("ui_update_offer_text").format(current=r['atual'], first=(f"{first}\n" if first else "")),
                      "fns": [install,
                              lambda: self.read(omni_i18n._("ui_update_news_until").format(version=r['nova']), "refresh",
                                                news_text(news) or omni_i18n._("ui_update_news_unavailable"),
                                                on_close=lambda: self.update_offer(r)),
                              lambda: None]}

    def update_back(self):
        self.worker(omni_update.go_back, self._sys_done, busy=omni_i18n._("ui_update_reverting"))

    # --- ações ---

    def do_action(self, name, busy=omni_i18n._("ui_working")):
        self.worker(lambda: D.action(name), self._action_done, busy=busy)

    def _action_done(self, res):
        txt = omni_i18n._("ui_error_prefix").format(error=res) if isinstance(res, Exception) else (str(res).splitlines() or [omni_i18n._("ui_done")])[0]
        self.toast = (txt, "problema" if isinstance(res, Exception) else "ok", self.t + 3.5)
        if self.page:
            keep = self.item_sel
            self.items = self.build_items(self.page)
            self.item_sel = min(keep, len(self.items) - 1)
            self.reload_findings()

    def run_info(self, title, tool):
        def done(res):
            self.modal = {"title": title, "text": str(res), "icon": "info-circle", "buttons": ["OK"], "sel": 0}
        self.worker(lambda: D.run(tool), done, busy=omni_i18n._("ui_reading"))

    def busy_game(self):
        if HUB == "jogo":
            self.toast = (omni_i18n._("ui_close_game_first"), "aviso", self.t + 3.5)
            return True
        return False

    def run_tool_toast(self, tool):
        self.worker(lambda: D.run(tool), self._action_done, busy=omni_i18n._("ui_working"))

    def card2_alert(self):
        """Alerta vermelho: o cartão 2 saiu sem Ejetar. O OK só libera depois de 5 s."""
        self.sheet = self.danger = None
        self.modal = {"title": omni_i18n._("ui_card2_removed_title"), "icon": "alert-triangle", "sel": 0,
                      "buttons": ["OK"], "fns": [lambda: None], "lock": (0, self.t + 5), "danger": True,
                      "text": omni_i18n._("ui_card2_removed_text")}

    def card2_items(self):
        """Ejetar (montado) ou Montar (no slot, desmontado) o cartão 2. Manual: nada fica vigiando o slot."""
        st = ("montado" if getattr(self, "fake_card2", True) else "fora") if FAKE else omni.card2_state()

        def go(fn, busy):
            def run():
                if FAKE:
                    self.fake_card2 = fn == "mount"
                    return omni_i18n._("ui_card2_mounted") if fn == "mount" else omni_i18n._("ui_card2_ejected")
                return omni.card2_mount() if fn == "mount" else omni.card2_eject()

            def done(res):
                if not FAKE:
                    self.games_idx = None          # a biblioteca relê os ports sem (ou com) o cartão 2
                    self.results.pop("ports", None)
                self._sys_done(res)
                if self.page == "cartoes":
                    self.items = self.build_items("cartoes")
                    self.item_sel = min(self.item_sel, len(self.items) - 1)
            self.worker(run, done, busy=busy)
        if st == "montado":
            return [tip(Action(omni_i18n._("ui_eject_card2"), "player-eject", lambda: go("eject", omni_i18n._("ui_ejecting_card2")),
                          confirm=omni_i18n._("ui_eject_card2_confirm")),
                        omni_i18n._("ui_card2_eject_tip"))]
        if st == "fora":
            return [tip(Action(omni_i18n._("ui_mount_card2"), "device-sd-card", lambda: go("mount", omni_i18n._("ui_mounting_card2"))),
                        omni_i18n._("ui_card2_mount_tip"))]
        return []

    def sd_count(self):
        return 2 if FAKE else max(1, len(omni_checks.sd_facts()["cartoes"]))

    def speed_test(self):
        def fn():
            if FAKE:
                time.sleep(1)
                return {"nivel": "ok", "acoes": [], "achados": [
                    ("ok", "Cartão 1: 16 GB, SanDisk (SL16G). 18.2 MB/s escrita, 41.0 MB/s leitura."),
                    ("ok", "Espaço do cartão 1: 6.8 GB livres, 9.2 GB ocupados."),
                    ("ok", "Cartão 2: 64 GB, sem marca (SD64G). 12.5 MB/s escrita, 38.7 MB/s leitura."),
                    ("ok", "Espaço do cartão 2: 31.2 GB livres, 32.8 GB ocupados."),
                    ("info", "Cartão 2 sem marca identificada (código 0xfe), comum em cartões genéricos. "
                             "Se ele travar ou perder arquivos, vale trocar.")]}
            return omni_checks.detalhes()

        def done(res):
            if isinstance(res, dict):
                self.findings = res
                self.toast = (omni_i18n._("ui_sd_test_done"), "ok", self.t + 3)
            else:
                self.modal = {"title": omni_i18n._("tx_cards"), "text": str(res), "icon": "brand-speedtest",
                              "buttons": ["OK"], "sel": 0}
        self.worker(fn, done, busy=omni_i18n._("ui_sd_testing"))

    def show_list(self, title, icon, rows, on_ok, ok_label, start=None):
        """rows: {"head", "tag", "tagc"} (título de grupo) ou {"name", "right", "icon", ...}.
        on_ok(row) roda no A; start é a linha escolhida ao abrir (padrão: a primeira)."""
        items = [i for i, r in enumerate(rows) if "name" in r]
        if not items:
            return False
        self.picker = {"title": title, "icon": icon, "rows": rows,
                       "sel": start if start in items else items[0], "top": 0,
                       "scroll": 0.0, "on_ok": on_ok, "ok_label": ok_label}
        return True

    def picker_input(self, cmd):
        pk = self.picker
        items = [i for i, r in enumerate(pk["rows"]) if "name" in r]
        k = items.index(pk["sel"])
        if pk.get("letters") and cmd in ("l1", "r1"):     # pula para a próxima/anterior letra
            first = lambda i: (pk["rows"][i]["name"][:1] or " ").upper()
            cur = first(pk["sel"])
            if cmd == "r1":
                nxt = next((i for i in items[k:] if first(i) != cur), items[-1])
            else:
                prev = [i for i in items[:k] if first(i) != cur]
                nxt = next((i for i in items if prev and first(i) == first(prev[-1])), items[0])
            pk["sel"] = nxt
            return
        row = pk["rows"][pk["sel"]]
        if cmd in ("left", "right") and pk.get("on_lr"):   # opções de ligar/desligar: muda sem fechar
            if row.get("lr"):
                pk["on_lr"](row, 1 if cmd == "right" else -1)
            return
        step = {"up": -1, "down": 1, "left": -6, "right": 6, "l1": -6, "r1": 6}.get(cmd)
        if cmd in ("up", "down"):         # passou do fim volta ao começo (e vice-versa)
            pk["sel"] = items[(k + step) % len(items)]
        elif step:                        # pulos de página param na ponta
            pk["sel"] = items[max(0, min(len(items) - 1, k + step))]
        elif cmd == "back":
            self.picker = None
            if pk.get("on_back"):
                pk["on_back"]()
        elif cmd == "ok":
            pk["on_ok"](pk["rows"][pk["sel"]])
        elif cmd == "x" and pk.get("on_x"):
            pk["on_x"](pk["rows"][pk["sel"]])
        elif cmd == "start" and pk.get("on_start"):
            pk["on_start"](pk["rows"][pk["sel"]])

    def draw_picker(self, dt):
        g, pk = self.g, self.picker
        app = pk.get("app")               # lista de um app (Vídeos, Notas): tela cheia, como as Músicas
        if app:
            a1, a2 = app
            self.draw_bg(dt)
            g.rrect(22, 22, 40, 40, 12, a1, a2)
            g.icon(pk["icon"], 30, 30, 24, ON_TEXT)
            g.text("Bold", 22, pk["title"][:22], 74, 22, TEXT)
            g.text("Regular", 12, pk.get("sub", "")[-34:], 75, 49, MUTED)
            self.draw_status()
            mx, my, mw, mh = 16, 0, W - 32, H
            g.rrect(16, 74, W - 32, 352, 18, alpha(GLASS, 14))
            ty, th = 80, 340
        else:
            g.rrect(0, 0, W, H, 0, (5, 7, 20, 190), feather=0)
            mx, my, mw, mh = 24, 20, W - 48, H - 40
            g.rrect(mx, my, mw, mh, 22, MODAL_A, MODAL_B)
            g.stroke(mx, my, mw, mh, 22, ink(25))
            a1, a2 = self.accent
            g.rrect(mx + 20, my + 16, 36, 36, 12, a1, a2)
            g.icon(pk["icon"], mx + 28, my + 24, 20, ON_TEXT)
            title = pk["title"]
            while g.measure("Bold", 18, title)[0] > mw - 100 and len(title) > 8:
                title = "…" + title[2:]          # caminhos longos: mostra o fim
            g.text("Bold", 18, title, mx + 68, my + 22, TEXT)
            ty, th = my + 66, mh - 66 - 44
        rows = pk["rows"]
        hs = [34 if "head" in r else 40 for r in rows]
        ys = [sum(hs[:i]) for i in range(len(rows))]
        # rola para manter a linha escolhida visível (com o título do grupo)
        sel_y, sel_h = ys[pk["sel"]], hs[pk["sel"]]
        if sel_y - pk["top"] < 40:
            pk["top"] = max(0, sel_y - 40)
        elif sel_y + sel_h - pk["top"] > th:
            pk["top"] = sel_y + sel_h - th
        pk["scroll"] = approach(pk["scroll"], pk["top"], dt, 18)
        g.clip(mx, ty, mw, th)
        for i, r in enumerate(rows):
            y = ty + ys[i] - pk["scroll"]
            if y + hs[i] < ty or y > ty + th:
                continue
            if "head" in r:
                g.text("SemiBold", 11, r["head"].upper(), mx + 30, y + 12, FAINT)
                if r.get("tag"):
                    tw = g.measure("Bold", 9, r["tag"])[0] + 14
                    g.rrect(mx + mw - 40 - tw, y + 9, tw, 18, 9, alpha(r["tagc"], 60))
                    g.text("Bold", 9, r["tag"], mx + mw - 40 - tw / 2, y + 18.5, TEXT, "c", "m")
                continue
            on = i == pk["sel"]
            if on:
                g.rrect(mx + 16, y + 2, mw - 44, 36, 12, a1, a2)
            x = mx + 30
            if r.get("icon"):
                g.icon(r["icon"], x, y + 11, 18, ON_TEXT if on else MUTED)
                x += 28
            g.text("SemiBold" if on else "Regular", 14, r["name"], x, y + 10, ON_TEXT if on else TEXT)
            if r.get("right"):
                lab, c = r["right"]
                lw = g.measure("SemiBold", 11, lab)[0]
                g.circle(mx + mw - 60 - lw, y + 20, 4, c)
                g.text("SemiBold", 11, lab, mx + mw - 50 - lw, y + 13, ON_TEXT if on else c)
        g.clip()
        total = sum(hs)
        if total > th:
            bh = max(30, th * th / total)
            by = ty + (th - bh) * min(1, pk["scroll"] / max(1, total - th))
            g.rrect(mx + mw - 14, ty, 4, th, 2, ink(18))
            g.rrect(mx + mw - 14, by, 4, bh, 2, alpha(a1, 220))
        extra = pk.get("hints")
        if extra is None:
            extra = [("L1/R1", omni_i18n._("ui_hint_letter"))] if pk.get("letters") else [("LR", omni_i18n._("ui_hint_skip"))]
        if app:
            self.draw_footer_at(H - 29, [("A", pk["ok_label"])] + extra + [("B", omni_i18n._("ui_back"))], center=W / 2)
            return
        self.draw_footer_at(my + mh - 30, [("A", pk["ok_label"])] + extra, mx + 24)
        self.draw_footer_at(my + mh - 30, [("B", omni_i18n._("ui_back"))], mx + mw - 110)

    # --- ferramentas do Omni36OS ---

    def tool_list(self):
        """Programas de tela cheia que continuam fora do launcher (PortMaster)."""
        if FAKE:
            return [{"path": "/opt/system/Tools/PortMaster.sh", "name": "PortMaster",
                      "desc": omni_i18n._("tx_port_store")}]
        if not getattr(self, "tools_cache", None):
            self.tools_cache = omni_tools.tools()
        return self.tools_cache

    def _ferramentas(self):
        ts = self.tool_list()
        self.tool_count = len(ts) + 1
        out = [("info", omni_i18n._("ui_tools_status_tip"))]
        return {"nivel": "ok", "achados": out, "acoes": []} if FAKE else omni_checks.finish(out, [], {})

    def ask_tool(self, t):
        self.modal = {"title": t["name"], "icon": "adjustments", "sel": 0, "buttons": [omni_i18n._("ui_open"), omni_i18n._("ui_back")],
                      "text": t["desc"] + "\n" + omni_i18n._("tx_opens_full"),
                      "fn": lambda: self.run_tool(t)}

    def run_tool(self, t):
        if self.busy_game():
            return
        if FAKE:
            self.toast = (f"Abriria {t['name']}", "ok", self.t + 3)
            return
        omni.write_text(omni.HANDOFF, f"tool:ferramentas:{t['path']}")
        self.running = False          # o launch-direct.sh roda o programa e reabre o Omni36OS

    def pendrive_tip(self, mounted):
        """Dica de Montar/Desmontar = o estado do pendrive (reconhecido ou não). Relida a cada abertura."""
        if FAKE:
            return omni_i18n._("ui_pendrive_fake_mounted" if mounted else "ui_pendrive_fake_unmounted")
        try:
            return omni_tools.pendrive_status()
        except Exception:
            return omni_i18n._("ui_pendrive_fallback_tip")

    def native(self, name, busy=omni_i18n._("ui_working")):
        """Ferramenta reescrita em Python (omni_tools.NATIVE): roda aqui e mostra o resultado."""
        if FAKE and name in ("usb_mount", "usb_umount"):
            self.fake_usb = name == "usb_mount"
        fake = {"usb_mount": "Pendrive (vfat) montado em /mnt/usbdrive", "usb_umount": "Pendrive desmontado: pode tirar"}
        fn = (lambda: fake.get(name, "teste")) if FAKE else (lambda: omni_tools.run_native(name))
        self.worker(fn, self._sys_done, busy=busy)

    def _sys_done(self, res):
        """Resultado de uma ferramenta do sistema: aviso curto ou janela, e a página relê o estado."""
        txt = omni_i18n._("ui_error_prefix").format(error=res) if isinstance(res, Exception) else str(res)
        bad = isinstance(res, Exception) or omni_i18n.is_failure(txt)
        if len(txt) > 60:
            self.modal = {"title": omni_i18n._("ui_modal_ready") if not bad else omni_i18n._("ui_modal_attention"), "icon": "alert-triangle" if bad else "check",
                          "buttons": ["OK"], "sel": 0, "text": txt}
        else:
            self.toast = (txt, "aviso" if bad else "ok", self.t + 3.5)
        if self.page:
            keep = self.item_sel          # rótulos que dependem do estado (montar/desmontar) mudam
            self.items = self.build_items(self.page)
            self.item_sel = min(keep, len(self.items) - 1)
            self.reload_findings(quiet=True)

    def live_refresh(self):
        """Subpáginas com estado vivo (rede USB, calibração) se releem sozinhas."""
        every = LIVE.get(self.page)
        if not every or self.busy or self.t < getattr(self, "live_at", 0):
            return
        self.live_at = self.t + every
        self.reload_findings(quiet=True)

    # --- teclado na tela (a lógica é a do omni_teclado, igual em todo o sistema) ---

    def keyboard(self, title, on_done, secret=False, value="", hint="", locked=False, texto=False):
        """Teclado do Omni36OS: direcional escolhe, A digita, B apaga, X espaço, Y letras/símbolos,
        Start confirma, Select cancela. locked: tela da trava (não dá para cancelar; o power
        abre Energia). texto: linhas longas (bloco de notas)."""
        self.kbd = {"title": title, "fn": on_done, "hint": hint, "locked": locked,
                    "tk": omni_teclado.Teclado(value, secret, self.NOTE_LIMIT if texto else 64, multiline=texto)}

    KBD_FIELD_W = W - 32 - 72             # largura do texto no campo de várias linhas

    def kbd_input(self, cmd):
        k = self.kbd
        tk = k["tk"]
        if tk.multiline and cmd in ("l1", "r1"):      # cursor para o fim da linha de cima ou de baixo
            spans = self.text_spans(tk.value, self.KBD_FIELD_W, "Medium", 15)
            cur = next((i for i, (a, b) in enumerate(spans) if a <= tk.pos <= b), len(spans) - 1)
            nxt = max(0, min(len(spans) - 1, cur + (1 if cmd == "r1" else -1)))
            tk.set_pos(spans[nxt][1])
            return
        res = tk.input(cmd)
        if res == "cancel" and not k.get("locked"):   # travado: nada (Energia é pelo botão de power)
            self.kbd = None
        elif res == "ok":
            self.kbd = None
            k["fn"](k["tk"].value)

    def draw_keyboard(self, dt):
        g, k = self.g, self.kbd
        tk = k["tk"]
        a1, a2 = self.accent
        if k.get("locked"):               # travado: nada do que está atrás aparece
            self.draw_bg(dt)
        else:
            g.rrect(0, 0, W, H, 0, (5, 7, 20, 190), feather=0)
        multi = tk.multiline
        mx, my, mw, mh = (16, 12, W - 32, H - 24) if multi else (40, 40, W - 80, H - 80)
        g.rrect(mx, my, mw, mh, 22, MODAL_A, MODAL_B)
        g.stroke(mx, my, mw, mh, 22, ink(25))
        g.rrect(mx + 20, my + 14, 32, 32, 10, a1, a2) if multi else g.rrect(mx + 20, my + 16, 36, 36, 12, a1, a2)
        g.icon("notes" if multi else "lock" if k.get("locked") else "keyboard", mx + 26 if multi else mx + 28,
               my + 20 if multi else my + 24, 20, ON_TEXT)
        g.text("Bold", 17, k["title"], mx + 64 if multi else mx + 68, my + 19 if multi else my + 23, TEXT)
        if multi:
            ky = self.draw_kbd_page(tk, mx, my, mw, a1)
        else:
            ky = None
        if not multi:                     # campo de uma linha
            shown = "•" * len(tk.value) if tk.secret else tk.value
            g.rrect(mx + 20, my + 64, mw - 40, 40, 12, ink(16))
            g.stroke(mx + 20, my + 64, mw - 40, 40, 12, alpha(a1, 160))
            while shown and g.measure("SemiBold", 17, shown)[0] > mw - 80:
                shown = shown[1:]
            tw = g.text("SemiBold", 17, shown, mx + 34, my + 84.5, TEXT, "l", "m") if shown else 0
            if int(self.t * 2) % 2 == 0:
                g.rrect(mx + 36 + tw, my + 74, 2, 21, 1, a1)
            if k["hint"] and not tk.value:
                g.text("Regular", 13, k["hint"], mx + 44, my + 84.5, FAINT, "l", "m")
        # teclas
        ky, kh, gap = (ky, 31, 6) if multi else (my + 120, 36, 7)
        rows = tk.rows()
        for r, row in enumerate(rows):
            ws = tk.widths(row, r == len(rows) - 1, mw - 40, gap)
            x = mx + 20
            for c, key in enumerate(row):
                on = r == tk.r and c == tk.c
                label = tk.label(key)
                act = key == "shift" and (tk.shift != "off" or tk.symbols)
                if on:
                    g.rrect(x, ky, ws[c], kh, 10, a1, a2)
                else:
                    g.rrect(x, ky, ws[c], kh, 10, alpha(a1, 70) if act else ink(18))
                g.text("SemiBold", 15 if len(label) == 1 else 12, label, x + ws[c] / 2, ky + kh / 2 + 0.5,
                       ON_TEXT if on else TEXT, "c", "m")
                if key == "shift" and tk.shift == "lock" and not tk.symbols:   # travada: um traço embaixo
                    g.rrect(x + ws[c] / 2 - 10, ky + kh - 7, 20, 3, 1.5, ON_TEXT if on else a1)
                x += ws[c] + gap
            ky += kh + gap
        if multi:
            hints = [("B", omni_i18n._("ui_hint_erase"), TEXT), ("X", omni_i18n._("ui_hint_space"), TEXT),
                     ("Y", omni_i18n._("ui_hint_letters") if tk.symbols else omni_i18n._("ui_hint_symbols"), TEXT),
                     ("L1/R1", omni_i18n._("ui_hint_line"), TEXT), ("START", omni_i18n._("ui_hint_save"), TEXT),
                     ("SELECT", omni_i18n._("ui_hint_exit"), TEXT)]
        else:
            hints = [("A", omni_i18n._("ui_hint_type"), TEXT), ("B", omni_i18n._("ui_hint_erase"), TEXT),
                     ("X", omni_i18n._("ui_hint_space"), TEXT),
                     ("Y", omni_i18n._("ui_hint_letters") if tk.symbols else omni_i18n._("ui_hint_symbols"), TEXT),
                     ("START", omni_i18n._("ui_hint_ok"), TEXT),
                     *([] if k.get("locked") else [("SELECT", omni_i18n._("ui_hint_cancel"), TEXT)])]
        self.draw_footer_at(my + mh - 28, hints, center=W / 2)

    def draw_kbd_page(self, tk, mx, my, mw, a1):
        """Campo de várias linhas (bloco de notas): o texto quebra na largura e sobe como numa máquina
        de escrever, sempre com a linha do cursor à vista. Devolve onde as teclas começam."""
        g = self.g
        fy, lines, lh = my + 54, 5, 22
        g.rrect(mx + 20, fy, mw - 40, lines * lh + 16, 12, ink(16))
        g.stroke(mx + 20, fy, mw - 40, lines * lh + 16, 12, alpha(a1, 160))
        text = tk.value
        spans = self.text_spans(text, self.KBD_FIELD_W, "Medium", 15)
        cur = next((i for i, (a, b) in enumerate(spans) if a <= tk.pos <= b), len(spans) - 1)
        top = max(0, min(cur - (lines - 1), len(spans) - lines))   # o cursor fica na última linha à vista
        if cur < top:
            top = cur
        for k in range(top, min(len(spans), top + lines)):
            a, b = spans[k]
            y = fy + 8 + (k - top) * lh
            g.text("Medium", 15, text[a:b], mx + 34, y, TEXT)
            if k == cur and int(self.t * 2) % 2 == 0:
                cx = mx + 35 + g.measure("Medium", 15, text[a:tk.pos])[0]
                g.rrect(cx, y + 1, 2, 19, 1, a1)
        if len(spans) > lines:
            g.text("Regular", 11, omni_i18n._("ui_files_line_count").format(current=cur + 1, total=len(spans)), mx + mw - 30, fy + lines * lh + 22, FAINT, "r")
        if not text:
            g.text("Regular", 13, omni_i18n._("ui_note_placeholder"), mx + 44, fy + 8 + 10, FAINT, "l", "m")
        return fy + lines * lh + 40

    def _hint_glyph_w(self, letter):
        if letter in ("A", "B", "X", "Y"):
            return 24
        if letter in ("LR", "UD"):
            return 36
        return self.g.measure("Bold", 9, letter)[0] + 12 + 6

    def localize_hints(self, hints):
        aliases = {
            "Letra": "ui_hint_letter", "Pular": "ui_hint_skip", "Apagar": "ui_hint_erase",
            "Espaço": "ui_hint_space", "Letras": "ui_hint_letters", "Símbolos": "ui_hint_symbols",
            "Linha": "ui_hint_line", "Salvar": "ui_hint_save", "Sair": "ui_hint_exit",
            "Digitar": "ui_hint_type", "OK": "ui_hint_ok", "Cancelar": "ui_hint_cancel",
            "Colar": "ui_hint_clipboard_paste", "Opções": "ui_hint_options", "Pasta": "ui_hint_folder",
            "Escolher": "ui_hint_choose", "Ajustar": "ui_hint_adjust", "Confirmar": "ui_hint_confirm",
            "Desfazer": "ui_hint_undo", "De novo": "ui_hint_repeat", "Continuar": "ui_hint_continue",
            "Pausar": "ui_hint_pause", "Editar": "ui_hint_edit", "Rolar": "ui_hint_scroll",
            "Página": "ui_hint_page", "Fechar": "ui_hint_close", "Mudar": "ui_hint_change",
            "Abrir": "ui_hint_open", "Tocar": "ui_hint_play", "Tocar tudo": "ui_hint_play_all",
            "Tocando": "ui_hint_now_playing", "Música": "ui_hint_music", "Jogar": "ui_hint_play_game",
            "Voltar": "ui_hint_back", "Energia": "ui_hint_power", "Analógico": "ui_hint_analog",
            "Pular página": "ui_hint_jump", "Lista": "ui_hint_playback_list", "Visual": "ui_hint_visualizer",
            "Mostrar/esconder": "ui_hint_show_hide", "Outra imagem": "ui_hint_other_image",
            "10 s": "ui_hint_seek_10s", "−1 min": "ui_hint_seek_minus_min", "+1 min": "ui_hint_seek_plus_min",
            "−10 s": "ui_hint_seek_minus_10", "+10 s": "ui_hint_seek_plus_10",
        }
        for key, translations in omni_i18n.TRANSLATIONS.items():
            if key.startswith("ui_hint_"):
                for label in translations.values():
                    aliases.setdefault(label, key)
        out = []
        for hint in hints:
            key = aliases.get(hint[1])
            out.append((hint[0], omni_i18n._(key) if key else hint[1], *hint[2:]))
        return out

    def hints_width(self, hints):
        return sum(self._hint_glyph_w(h[0]) + self.g.measure("Medium", 12, h[1])[0] + 16 for h in hints) - 16

    def draw_footer_at(self, y, hints, x=None, center=None):
        """Legenda com a arte de cada botão: A/B/X/Y (círculo), LR/UD (setas do direcional) ou o nome
        numa pílula (START, L1/R1...). `center`: centraliza a linha nesse x."""
        g = self.g
        hints = self.localize_hints(hints)
        if center is not None:
            x = center - self.hints_width(hints) / 2
        for h in hints:
            letter, label = h[0], h[1]
            c = h[2] if len(h) > 2 else TEXT
            w = self._hint_glyph_w(letter)
            if letter in ("A", "B", "X", "Y"):
                self.btn_glyph(x, y - 2, letter, c)
            elif letter in ("LR", "UD"):
                g.rrect(x, y - 1, 30, 19, 9.5, ink(40))
                if letter == "LR":
                    g.chevron(x + 9, y + 8.5, 6, TEXT, left=True)
                    g.chevron(x + 21, y + 8.5, 6, TEXT)
                else:
                    g.chevron_v(x + 9, y + 8.5, 6, TEXT, up=True)
                    g.chevron_v(x + 21, y + 8.5, 6, TEXT)
            else:
                pw = w - 6
                g.rrect(x, y, pw, 17, 8, ink(40))
                g.text("Bold", 9, letter, x + pw / 2, y + 9, TEXT, "c", "m")
            x += w + g.text("Medium", 12, label, x + w, y + 8.5, MUTED, "l", "m") + 16

    def ask_password(self):
        def second(new):
            if len(new) < 3:
                self.toast = (omni_i18n._("ui_password_min_length"), "aviso", self.t + 3.5)
                return

            def check(again):
                if again != new:
                    self.toast = (omni_i18n._("ui_passwords_mismatch"), "aviso", self.t + 3.5)
                    return
                fn = (lambda: "teste") if FAKE else (lambda: omni_sistema.change_password(new))
                self.worker(fn, self._sys_done, busy=omni_i18n._("ui_password_changing"))
            self.keyboard(omni_i18n._("ui_password_repeat"), check, secret=True)
        self.keyboard(omni_i18n._("ui_password_prompt"), second, secret=True, hint=omni_i18n._("ui_password_hint"))

    # --- jogador, trava e Samba ---

    def first_screens(self):
        """No boot: a trava (se ligada) e depois o nome do jogador (só na primeira vez)."""
        def after_lock():
            if HUB not in ("boot", ""):
                return
            news = self.unseen_news()
            if not self.player:
                self.ask_language(lambda: self.ask_name(first=True))
            elif news:
                self.read(omni_i18n._("tx_welcome").format(version=omni_version()), "refresh", news_text(news))
        locked = (os.environ.get("OMNI_TRAVA") == "1") if FAKE else omni_sistema.lock_on()
        if locked and RESUME == "":
            self.lock_screen(after_lock)
        else:
            after_lock()

    def unseen_news(self):
        """Primeiro boot de uma versão nova: as novidades dela (só dela). Guarda a versão como vista."""
        cur = omni_version()
        if FAKE:
            seen = os.environ.get("OMNI_VISTA", cur)
        else:
            seen = omni.read_text(SEEN_FILE, "").strip()
            omni.save_file(SEEN_FILE, cur)
        if seen == cur:
            return []
        return [n for n in omni_help.NOVIDADES if n[0] == cur]      # só a versão recém-instalada

    def ask_reset(self):
        def go():
            def done(res):
                self.player = ""
                apply_theme("escuro")
                self.g.flush()
                self.open_page("geral")
                self.toast = (str(res), "ok", self.t + 3)
                self.ask_language(lambda: self.ask_name(first=True))
            self.worker((lambda: "Sistema zerado.") if FAKE else omni_sistema.reset_custom, done, busy=omni_i18n._("ui_reset_busy"))
        self.warn(omni_i18n._("tx_reset_title"), omni_i18n._("tx_reset_text"), go, secs=5,
                  risk=omni_i18n._("tx_reset_risk"),
                  undo=omni_i18n._("tx_reset_undo"))

    def lock_screen(self, then):
        def check(pw):
            ok = (pw == os.environ.get("OMNI_TRAVA_SENHA", "1234")) if FAKE else omni_sistema.lock_check(pw)
            if ok:
                self.toast = ((omni_i18n._("ui_hello_player").format(player=self.player) if self.player
                               else omni_i18n._("ui_hello_unlocked")), "ok", self.t + 3)
                then()
            else:
                self.toast = (omni_i18n._("ui_password_wrong"), "problema", self.t + 3)
                self.lock_screen(then)
        self.keyboard(omni_i18n._("ui_lock_password_prompt"), check, secret=True, locked=True,
                      hint=omni_i18n._("ui_lock_password_hint"))

    def ask_language(self, then):
        """Primeiro boot: escolhe o idioma antes do nome. Cada opção vem no próprio idioma; B mantém o atual."""
        rows = [{"name": "Português (Brasil)", "lang": "pt-BR"}, {"name": "English", "lang": "en"}]

        def pick(row):
            self.picker = None
            D.set("idioma", row["lang"])
            then()
        self.show_list("Idioma / Language", "adjustments", rows, pick, "OK",
                       start=1 if omni_i18n.get_lang() == "en" else 0)
        self.picker["on_back"] = then

    def ask_name(self, first=False):
        def done(name):
            name = " ".join(name.split())[:20]
            if not name:
                if first:
                    self.toast = (omni_i18n._("ui_player_no_name_yet"), "ok", self.t + 4)
                return
            self.player = name if FAKE else omni_sistema.set_player_name(name)
            self.toast = (omni_i18n._("ui_player_pleasure").format(player=self.player), "ok", self.t + 3.5)
            if self.page:
                keep = self.item_sel
                self.items = self.build_items(self.page)
                self.item_sel = min(keep, len(self.items) - 1)
        self.keyboard(omni_i18n._("ui_player_name_prompt") if first else omni_i18n._("ui_player_name_title"), done,
                      value=self.player, hint=omni_i18n._("ui_player_greeting_hint"))

    # --- Wi-Fi ---

    def wifi_run(self, fn, busy):
        def done(res):
            self._sys_done(res)
            if self.page == "rede":
                keep = self.item_sel
                self.items = self.build_items("rede")
                self.item_sel = min(keep, len(self.items) - 1)
                self.reload_findings(quiet=True)
        self.worker(fn, done, busy=busy)

    def wifi_toggle(self, on):
        if FAKE:
            self.fake_wifi = on
        self.wifi_run((lambda: omni_i18n._("msg_wifi_on" if on else "msg_wifi_off")) if FAKE else
                      (lambda: omni_sistema.wifi_set(on)),
                      omni_i18n._("ui_wifi_turning_on" if on else "ui_wifi_turning_off"))

    def tether_toggle(self, on):
        if FAKE:
            self.fake_tether = on
        self.wifi_run((lambda: omni_i18n._("msg_tether_on" if on else "msg_tether_off")) if FAKE else
                      (lambda: omni_sistema.ancoragem_set(on)),
                      omni_i18n._("ui_tether_busy"))

    def wifi_connect(self, rede, senha=None):
        self.wifi_run((lambda: omni_i18n._("ui_wifi_connected").format(network=rede)) if FAKE else
                      (lambda: omni_sistema.wifi_connect(rede, senha)),
                      omni_i18n._("ui_network_connecting").format(network=rede))

    def wifi_scan(self):
        def done(nets):
            if isinstance(nets, Exception) or not nets:
                self.toast = (omni_i18n._("ui_wifi_none_found"), "aviso", self.t + 3.5)
                return
            if self.page == "rede":           # o Wi-Fi pode ter sido ligado agora: a página mostra o estado novo
                self.items = self.build_items("rede")
                self.recheck("rede")
            rows = [{"name": n["rede"], "icon": "lock" if n["senha"] else "wifi", "net": n,
                     "right": (omni_i18n._("ui_wifi_connected_label") if n["atual"] else omni_i18n._("ui_wifi_saved_label") if n["salva"] else f"{n['sinal']}%", MUTED)}
                    for n in nets]

            def ok(row):
                n = row["net"]
                self.picker = None
                if n["senha"] and not n["salva"]:
                    self.keyboard(omni_i18n._("ui_wifi_password").format(network=n["rede"]),
                                  lambda pw: pw and self.wifi_connect(n["rede"], pw),
                                  secret=True, hint=omni_i18n._("ui_wifi_password_hint"))
                else:
                    self.wifi_connect(n["rede"])
            self.show_list(omni_i18n._("ui_network_nearby_title"), "wifi", rows, ok,
                           omni_i18n._("ui_wifi_connect_button"))
        fake = [{"rede": "Casa", "sinal": 72, "senha": True, "atual": True, "salva": True},
                {"rede": "Vizinho 5G", "sinal": 40, "senha": True, "atual": False, "salva": False},
                {"rede": "Café aberto", "sinal": 28, "senha": False, "atual": False, "salva": False}]
        self.worker((lambda: fake) if FAKE else omni_sistema.wifi_scan, done, busy=omni_i18n._("ui_wifi_searching"))

    def wifi_saved(self):
        def done(names):
            if isinstance(names, Exception) or not names:
                self.toast = (omni_i18n._("ui_wifi_none_saved"), "aviso", self.t + 3.5)
                return
            rows = [{"name": n, "icon": "wifi"} for n in names]

            def ok(row):
                self.picker = None
                self.modal = {"title": row["name"], "icon": "wifi", "sel": 0, "buttons": [omni_i18n._("ui_connect"), omni_i18n._("ui_forget"), omni_i18n._("ui_back")],
                              "text": omni_i18n._("ui_wifi_open_connect"),
                              "fns": [lambda: self.wifi_connect(row["name"]),
                                      lambda: self.wifi_run((lambda: omni_i18n._("ui_wifi_forgotten").format(network=row["name"])) if FAKE else
                                                            (lambda: omni_sistema.wifi_forget(row["name"])),
                                                            omni_i18n._("ui_wifi_forgetting")),
                                      lambda: None]}
            self.show_list(omni_i18n._("ui_network_saved_title"), "device-floppy", rows, ok,
                           omni_i18n._("ui_wifi_choose_button"))
        self.worker((lambda: ["Casa", "Trabalho"]) if FAKE else omni_sistema.wifi_saved, done,
                    busy=omni_i18n._("ui_wifi_reading_saved"))

    def ask_samba(self):
        def first(new):
            if len(new) < 3:
                self.toast = (omni_i18n._("ui_password_min_length"), "aviso", self.t + 3.5)
                return

            def again(rep):
                if rep != new:
                    self.toast = (omni_i18n._("ui_passwords_mismatch"), "aviso", self.t + 3.5)
                    return
                fn = (lambda: "teste") if FAKE else (lambda: omni_sistema.samba_password(new))
                self.worker(fn, self._sys_done, busy=omni_i18n._("ui_samba_password_busy"))
            self.keyboard(omni_i18n._("ui_samba_password_repeat"), again, secret=True)
        self.keyboard(omni_i18n._("ui_samba_password_new"), first, secret=True,
                      hint=omni_i18n._("ui_samba_password_hint"))

    def ask_lock(self):
        locked = (os.environ.get("OMNI_TRAVA") == "1") if FAKE else omni_sistema.lock_on()

        def refresh(res):
            self._sys_done(res)
            if self.page:
                keep = self.item_sel
                self.items = self.build_items(self.page)
                self.item_sel = min(keep, len(self.items) - 1)
        if locked:
            def off():
                def check(pw):
                    ok = True if FAKE else omni_sistema.lock_check(pw)
                    if not ok:
                        self.toast = (omni_i18n._("ui_password_wrong_lock"), "problema", self.t + 3.5)
                        return
                    self.worker((lambda: "teste") if FAKE else omni_sistema.lock_clear, refresh, busy=omni_i18n._("ui_lock_disabling_busy"))
                self.keyboard(omni_i18n._("ui_name_current_password"), check, secret=True)
            self.modal = {"title": omni_i18n._("ui_password_lock"), "icon": "lock", "sel": 0, "buttons": [omni_i18n._("ui_off"), omni_i18n._("ui_back")],
                          "text": omni_i18n._("ui_lock_enabled_text"), "fn": off}
            return

        def first(pw):
            if len(pw) < 3:
                self.toast = (omni_i18n._("ui_password_min_length"), "aviso", self.t + 3.5)
                return

            def again(rep):
                if rep != pw:
                    self.toast = (omni_i18n._("ui_passwords_mismatch"), "aviso", self.t + 3.5)
                    return
                self.worker((lambda: "teste") if FAKE else (lambda: omni_sistema.lock_set(pw)), refresh,
                            busy=omni_i18n._("ui_lock_enabling"))
            self.keyboard(omni_i18n._("ui_name_repeat_password"), again, secret=True)
        self.modal = {"title": omni_i18n._("ui_password_lock"), "icon": "lock", "sel": 0, "buttons": [omni_i18n._("ui_on"), omni_i18n._("ui_back")],
                      "text": omni_i18n._("ui_lock_disabled_text"),
                      "fn": lambda: self.keyboard(omni_i18n._("ui_lock_password_title"), first, secret=True)}

    # --- teste do controle ---

    PAD_NAMES = {0: "A", 1: "B", 2: "X", 3: "Y", 4: "SELECT", 6: "START", 7: "L3", 8: "R3", 9: "L1", 10: "R1",
                 11: "CIMA", 12: "BAIXO", 13: "ESQUERDA", 14: "DIREITA", 5: "GUIDE", 15: "MISC"}

    def open_pad(self):
        self.pad = {"down": set(), "axes": [0] * 6, "last": omni_i18n._("ui_pad_prompt"), "exit_at": None, "count": 0}

    def pad_event(self, kind, num, val, now):
        p = self.pad
        if kind == "btn":
            if val:
                p["down"].add(num)
                p["count"] += 1
                name = self.PAD_NAMES.get(num) or omni_i18n._("ui_pad_button").format(number=num)
                p["last"] = f"{name}  (SDL {num})"
            else:
                p["down"].discard(num)
            both = {4, 6} <= p["down"]
            p["exit_at"] = (p["exit_at"] or now + 1.0) if both else None
        else:
            p["axes"][num] = val
            if num >= 4 and abs(val) > 8000:
                p["last"] = f"{'L2' if num == 4 else 'R2'}  (eixo {num}: {val})"

    def pad_tick(self, now):
        p = self.pad
        if p["exit_at"] and now >= p["exit_at"]:
            self.pad = None
            self.held.clear()
            self.toast = (omni_i18n._("ui_pad_test_done").format(count=p['count']), "ok", self.t + 3)

    def draw_pad(self, dt):
        g, p = self.g, self.pad
        a1, a2 = self.accent
        g.rrect(0, 0, W, H, 0, (5, 7, 20, 200), feather=0)
        mx, my, mw, mh = 24, 20, W - 48, H - 40
        g.rrect(mx, my, mw, mh, 22, MODAL_A, MODAL_B)
        g.stroke(mx, my, mw, mh, 22, ink(25))
        g.rrect(mx + 20, my + 16, 36, 36, 12, a1, a2)
        g.icon("device-gamepad-2", mx + 28, my + 24, 20, ON_TEXT)
        g.text("Bold", 18, omni_i18n._("ui_card_button_test"), mx + 68, my + 22, TEXT)
        d = p["down"]
        lit = lambda b: (a1 if b in d else ink(22))
        txt = lambda b: ON_TEXT if b in d else MUTED
        # ombros
        ax = p["axes"]
        for x, b, lab in ((mx + 40, 9, "L1"), (mx + mw - 130, 10, "R1")):
            g.rrect(x, my + 70, 90, 26, 10, lit(b))
            g.text("Bold", 12, lab, x + 45, my + 83.5, txt(b), "c", "m")
        for x, k, lab in ((mx + 140, 4, "L2"), (mx + mw - 230, 5, "R2")):
            on = ax[k] > 8000
            g.rrect(x, my + 70, 90, 26, 10, a1 if on else ink(22))
            g.text("Bold", 12, lab, x + 45, my + 83.5, ON_TEXT if on else MUTED, "c", "m")
        # direcional
        cx, cy = mx + 120, my + 190
        for b, dx, dy in ((11, 0, -1), (12, 0, 1), (13, -1, 0), (14, 1, 0)):
            g.rrect(cx - 18 + dx * 38, cy - 18 + dy * 38, 36, 36, 9, lit(b))
        g.rrect(cx - 18, cy - 18, 36, 36, 9, ink(12))
        # ABXY (posição do R36S: A à direita, B embaixo, X em cima, Y à esquerda)
        bx, by = mx + mw - 120, my + 190
        for b, dx, dy in ((0, 1, 0), (1, 0, 1), (2, 0, -1), (3, -1, 0)):
            g.circle(bx + dx * 40, by + dy * 40, 19, lit(b))
            g.text("Bold", 14, self.PAD_NAMES[b], bx + dx * 40, by + dy * 40 + 0.5, txt(b), "c", "m")
        # select / start
        for x, b in ((W / 2 - 80, 4), (W / 2 + 10, 6)):
            g.rrect(x, my + 150, 70, 22, 11, lit(b))
            g.text("Bold", 10, self.PAD_NAMES[b], x + 35, my + 161.5, txt(b), "c", "m")
        # analógicos
        for k, (sx, b) in enumerate(((W / 2 - 75, 7), (W / 2 + 75, 8))):
            sy = my + 290
            g.circle(sx, sy, 44, ink(14))
            g.stroke(sx - 44, sy - 44, 88, 88, 44, ink(30))
            g.circle(sx, sy, 44 * 0.12, ink(20))            # zona morta aproximada
            vx, vy = ax[k * 2] / 32768, ax[k * 2 + 1] / 32768
            g.circle(sx + vx * 34, sy + vy * 34, 15, a1 if b in d else a2)
            g.text("Regular", 10, f"{vx:+.2f} {vy:+.2f}", sx, sy + 56, MUTED, "c")
        g.text("SemiBold", 13, p["last"], W / 2, my + 222, TEXT, "c", "m")
        self.draw_footer_at(my + mh - 33, [("SELECT + START", omni_i18n._("ui_hint_hold_exit"))], center=W / 2)

    # --- arquivos ---

    def open_files(self, path=None, start=None):
        if path is None:
            roots = [r for r in (["/roms", "/roms2", "/mnt/usbdrive"] if not FAKE else ["/roms", "/roms2"])
                     if FAKE or os.path.ismount(r) or (r == "/roms" and os.path.isdir(r))]   # ROMS2 só montado
            names = {"/roms": omni_i18n._("tx_card1") + " (/roms)", "/roms2": omni_i18n._("tx_card2") + " (/roms2)",
                 "/mnt/usbdrive": omni_i18n._("tx_pendrive") + " (/mnt/usbdrive)"}
            rows = [{"name": names[r], "icon": "device-sd-card" if r != "/mnt/usbdrive" else "usb", "path": r,
                     "dir": True} for r in roots]
            self.files_at = None
            self.show_list(omni_i18n._("ui_card_option_files"), "folder", rows, lambda r: self.open_files(r["path"]), omni_i18n._("ui_hint_open"))
            self.picker["hints"] = []
            return
        self.files_at = path
        items = ([("ports", True, 0), ("Daytona USA.sh", False, 2400)] if FAKE else omni_sistema.listdir(path))
        rows = [{"name": "..", "icon": "arrow-up", "up": True}]
        rows += [{"name": n, "icon": "folder" if d else "file", "dir": d, "path": os.path.join(path, n), "img": is_image(n) and not d,
                  "right": None if d else (omni_sistema.human(sz) if not FAKE else f"{sz} B", MUTED)}
                 for n, d, sz in items]
        clip = getattr(self, "clip", None)
        self.show_list(path, "folder", rows, self.file_ok, omni_i18n._("ui_hint_open"), start)
        pk = self.picker
        pk["on_back"] = lambda: self.file_up()
        pk["on_x"] = self.file_menu
        pk["on_start"] = self.folder_menu
        pk["hints"] = [("START", omni_i18n._("ui_hint_clipboard_paste"))] if clip else [("X", omni_i18n._("ui_hint_options")), ("START", omni_i18n._("ui_hint_folder"))]

    def file_up(self):
        path = self.files_at
        if not path or path in ("/roms", "/roms2", "/mnt/usbdrive"):
            self.open_files()
            return
        parent = os.path.dirname(path)
        self.open_files(parent)
        rows = self.picker["rows"]
        self.picker["sel"] = next((i for i, r in enumerate(rows) if r.get("path") == path), 0)

    def file_ok(self, r):
        if r.get("up"):
            self.file_up()
        elif r.get("dir"):
            self.open_files(r["path"])
        elif r.get("img"):
            self.open_viewer(r["path"])
        elif r["name"].lower().endswith(omni_musica.EXT):
            self.open_music_file(r["path"])
        elif omni_video.is_video(r["name"]):
            self.play_video(r["path"])
        elif is_text(r["name"]):
            self.open_note(r["path"])
        else:
            self.file_menu(r)

    # --- ver imagens (Arquivos) ---

    def open_viewer(self, path, pics=None, back=None):
        """Imagem em tela cheia. Esquerda/direita: as outras imagens da pasta (ou `pics`, na ordem
        dada); A: mostra/esconde o nome; B: volta à pasta (ou chama `back(caminho)`)."""
        folder = os.path.dirname(path)
        if pics is None:
            try:
                pics = sorted((n for n in os.listdir(folder) if is_image(n)), key=str.lower)
            except OSError:
                pics = [os.path.basename(path)]
        name = os.path.basename(path)
        self.viewer = {"dir": folder, "pics": pics, "i": pics.index(name) if name in pics else 0, "back": back,
                       "info": True, "info_t": self.t, "sel": self.picker["sel"] if self.picker else 0}
        self.picker = None

    def viewer_input(self, cmd):
        v = self.viewer
        if cmd in ("left", "right", "l1", "r1") and len(v["pics"]) > 1:
            v["i"] = (v["i"] + (1 if cmd in ("right", "r1") else -1)) % len(v["pics"])
            v["info"], v["info_t"] = True, self.t
        elif cmd == "ok":
            v["info"], v["info_t"] = not v["info"], self.t
        elif cmd == "back":
            cur = os.path.join(v["dir"], v["pics"][v["i"]])
            self.viewer = None
            if v.get("back"):
                v["back"](cur)
                return
            self.open_files(v["dir"], v["sel"])
            rows = self.picker["rows"] if self.picker else []
            k = next((i for i, r in enumerate(rows) if r.get("path") == cur), None)
            if k is not None:
                self.picker["sel"] = k

    def draw_viewer(self, dt):
        g, v = self.g, self.viewer
        g.rrect(0, 0, W, H, 0, (0, 0, 0, 255), feather=0)
        path = os.path.join(v["dir"], v["pics"][v["i"]])
        if not g.picture(path, 0, 0, W, H):
            g.icon("file", W / 2 - 24, H / 2 - 40, 48, MUTED)
            g.text("Medium", 14, omni_i18n._("ui_image_file_open_error"), W / 2, H / 2 + 24, TEXT, "c", "m")
        k = 1.0 if v["info"] else 0.0
        if v["info"] and self.t - v["info_t"] > 3:          # a legenda some sozinha; A traz de volta
            k = max(0.0, 1 - (self.t - v["info_t"] - 3) / 0.4)
        if k > 0:
            g.rrect(0, 0, W, 46, 0, (0, 0, 0, int(150 * k)), feather=0)
            g.text("SemiBold", 13, v["pics"][v["i"]], 16, 23, alpha(TEXT, 255 * k), "l", "m")
            g.text("Medium", 12, omni_i18n._("ui_video_position_count").format(current=v['i'] + 1, total=len(v['pics'])), W - 16, 23, alpha(MUTED, 255 * k), "r", "m")
            g.rrect(0, H - 40, W, 40, 0, (0, 0, 0, int(150 * k)), feather=0)
            self.draw_footer_at(H - 29, [("LR", omni_i18n._("ui_hint_other_image")), ("A", omni_i18n._("ui_hint_show_hide")), ("B", omni_i18n._("ui_back"))],
                                center=W / 2)

    # --- Aplicativos > Imagens (capturas de tela) ---

    def shot_folders(self):
        """[(nome, pasta)] com capturas: a do menu (/roms/imagens) e a pasta imagens de cada port
        (o FN + Y num jogo grava em <pasta do jogo>/imagens), nos dois cartões."""
        if FAKE:
            base = os.environ.get("OMNI_IMAGENS", os.path.join(HERE, "imagens", "capturas"))
            cands = [(omni_i18n._("tx_omni_menu"), base)]
        else:
            cands = [(omni_i18n._("tx_omni_menu"), SHOT_DIR)]
            for card in ("/roms", "/roms2"):
                if card == "/roms2" and not os.path.ismount(card):
                    continue
                for d in sorted(glob.glob(f"{card}/ports/*/imagens")):
                    cands.append((os.path.basename(os.path.dirname(d)), d))
        out, seen = [], set()
        for name, d in cands:
            real = os.path.realpath(d)
            if real in seen:
                continue
            seen.add(real)
            try:
                pics = [f for f in os.listdir(d) if is_image(f)]
            except OSError:
                continue
            if pics:
                newest = max(os.path.getmtime(os.path.join(d, f)) for f in pics)
                out.append((name, d, len(pics), newest))
        out.sort(key=lambda x: -x[3])
        return out

    def open_images(self, folder=None, start=None):
        """Capturas de tela: as pastas (a mais nova primeiro) e, dentro, as imagens; A abre em tela
        cheia (esquerda/direita passam), X apaga."""
        if folder is None:
            groups = self.shot_folders()
            if not groups:
                self.toast = (omni_i18n._("tx_no_shot"), "aviso", self.t + 4)
                return
            if len(groups) == 1 and start is None:
                return self.open_images(groups[0][1])
            rows = [{"name": n, "icon": "folder", "path": d,
                     "right": (omni_i18n._("tx_images" if c != 1 else "tx_image").format(count=c) + " · " + time.strftime("%d/%m", time.localtime(t)), MUTED)}
                    for n, d, c, t in groups]
            self.show_list(omni_i18n._("ui_card_images"), "photo-search", rows, lambda r: self.open_images(r["path"]), omni_i18n._("ui_hint_open"), start)
            self.picker.update(app=IMAGE_COLORS, sub=omni_i18n._("tx_shots"), hints=[])
            return
        try:
            pics = [f for f in os.listdir(folder) if is_image(f)]
        except OSError:
            pics = []
        pics.sort(key=lambda f: -os.path.getmtime(os.path.join(folder, f)))
        if not pics:
            self.picker = None
            self.open_images()
            return
        rows = [{"name": os.path.splitext(f)[0], "icon": "photo-search", "path": os.path.join(folder, f),
                 "right": (time.strftime("%d/%m %H:%M", time.localtime(os.path.getmtime(os.path.join(folder, f)))), MUTED)}
                for f in pics]
        groups = self.shot_folders()
        many = len(groups) > 1
        title = next((n for n, d, *_ in groups if d == folder), omni_i18n._("ui_card_images")) if many else omni_i18n._("ui_card_images")
        k = next((i for i, r in enumerate(rows) if r["path"] == start), None) if isinstance(start, str) else start

        def show(r):
            self.open_viewer(r["path"], pics=pics, back=lambda cur: self.open_images(folder, cur))
        self.show_list(title, "photo-search", rows, show, omni_i18n._("ui_view"), k)
        self.picker.update(app=IMAGE_COLORS, sub=folder, hints=[("X", omni_i18n._("ui_note_erase"))])
        self.picker["on_x"] = lambda r: self.image_delete(r, folder)
        if many:
            self.picker["on_back"] = lambda: self.open_images(start=0)

    def image_delete(self, r, folder):
        def go():
            try:
                os.remove(r["path"])
            except OSError as e:
                self.toast = (omni_i18n._("ui_cannot_delete").format(error=e.strerror), "problema", self.t + 3.5)
            self.open_images(folder)
        self.modal = {"title": omni_i18n._("ui_image_delete_confirm"), "icon": "trash", "sel": 1,
                      "buttons": [omni_i18n._("btn_delete"), omni_i18n._("btn_cancel")],
                      "text": omni_i18n._("ui_note_delete_text").format(name=r['name']), "fns": [go, lambda: None]}

    # --- Aplicativos > Músicas ---

    def open_music(self):
        """Tocador: a lista (pastas e músicas da pasta) e a tela Tocando, com a visualização."""
        if not hasattr(self, "music_lib"):
            self.music_lib = omni_musica.Library()
        cfg = music_cfg()
        here = omni_musica.roots() if not FAKE else [(os.environ.get("OMNI_MUSICAS", "/tmp/omni36os-musicas"), "Cartão 1")]
        self.music = {"mode": "lista", "stack": [] if len(here) != 1 else [here[0]], "roots": here, "rows": [],
                      "sel": 0, "top": 0.0, "spec": [0.0] * omni_musica.BANDS, "peaks": [0.0] * omni_musica.BANDS,
                      "vis": cfg["vis"], "last": self.t, "off": False, "phase": 0.0,
                      "player": getattr(self, "music_player", None)}
        if not self.music["player"]:
            self.music["player"] = self.music_player = omni_musica.Player(gfx.sdl)
        self.music_rows()

    def music_rows(self, keep=None):
        m = self.music
        if not m["stack"]:
            m["rows"] = [{"dir": p, "name": n} for p, n in m["roots"]]
            m["sel"] = 0
            return
        path = m["stack"][-1][0]

        def read():
            li = self.music_lib.listing(path)
            self.music_lib.save()
            return li

        def done(li):
            if isinstance(li, Exception) or not self.music:
                return
            rows = [{"dir": os.path.join(path, d), "name": d} for d in li["dirs"]]
            rows += [{"song": os.path.join(path, s["f"]), "name": s["t"], "artist": s["a"]} for s in li["songs"]]
            m["rows"] = rows
            m["sel"] = next((i for i, r in enumerate(rows) if keep and r.get("dir") == keep), 0)
        self.worker(read, done, busy=omni_i18n._("ui_songs_reading"))

    def music_play(self, start_song=None):
        m, path = self.music, self.music["stack"][-1][0]
        deep = music_cfg()["sub"]

        def make():
            return self.music_lib.playlist(path, deep)

        def done(pl):
            if isinstance(pl, Exception) or not pl or not self.music:
                self.toast = (omni_i18n._("ui_music_empty"), "aviso", self.t + 3)
                return
            i = next((k for k, s in enumerate(pl) if s[0] == start_song), 0)
            if m["player"].play(pl, i):
                m["mode"], m["last"] = "tocando", self.t
            else:
                self.toast = (m["player"].error or omni_i18n._("ui_play_failed"), "problema", self.t + 4)
        self.worker(make, done, busy=omni_i18n._("ui_build_menu_busy") if deep else None)

    def music_close(self):
        self.music_screen(True)
        self.music["player"].close()
        self.music = None

    def music_screen(self, on):
        """Apaga ou acende a luz da tela (a música continua)."""
        self.music["off"] = not on
        self.backlight(on)

    def backlight(self, on):
        if FAKE:
            return
        for p in glob.glob("/sys/class/backlight/*/bl_power"):
            try:
                with open(p, "w") as f:
                    f.write("0" if on else "4")
            except OSError:
                pass

    def ssh_mode_on(self):
        self.ssh_off = True
        self.combo = set()
        self.combo_used = False
        self.backlight(False)

    def ssh_mode_wake(self):
        self.ssh_off = False
        self.combo_used = True
        self.backlight(True)
        self.toast = (omni_i18n._("ui_ssh_mode_off"), "ok", self.t + 2.5)

    def ssh_button(self, b, down):
        if b in (4, 6):
            (self.combo.add if down else self.combo.discard)(b)
            if {4, 6} <= self.combo:
                self.ssh_mode_wake()

    def music_input(self, cmd):
        m, pl = self.music, self.music["player"]
        m["last"] = self.t
        if m["off"]:                      # tela apagada: o botão só acende
            self.music_screen(True)
            return
        if m["mode"] == "opcoes":
            self.music_options_input(cmd)
            return
        if m["mode"] == "tocando":
            if cmd == "start":
                m["back_to"], m["mode"], m["osel"] = "tocando", "opcoes", 0
            elif cmd == "ok":
                pl.toggle()
            elif cmd in ("left", "right"):
                pl.step(1 if cmd == "right" else -1)
            elif cmd in ("l1", "r1"):
                pl.seek(10 if cmd == "r1" else -10)
            elif cmd == "y":
                order = list(VIS_NAMES)
                m["vis"] = order[(order.index(m["vis"]) + 1) % len(order)]
                self.toast = (VIS_NAMES[m["vis"]], "ok", self.t + 2)
                music_save(vis=m["vis"])
            elif cmd in ("back", "x"):
                m["mode"] = "lista"
            return
        rows = m["rows"]
        if cmd in ("up", "down", "l1", "r1") and rows:
            step = {"up": -1, "down": 1, "l1": -6, "r1": 6}[cmd]
            m["sel"] = max(0, min(len(rows) - 1, m["sel"] + step))
        elif cmd == "ok" and rows:
            r = rows[m["sel"]]
            if "dir" in r:
                m["stack"].append((r["dir"], r["name"]))
                self.music_rows()
            else:
                self.music_play(r["song"])
        elif cmd == "y" and m["stack"]:
            self.music_play()
        elif cmd == "x" and pl.current():
            m["mode"] = "tocando"
        elif cmd == "start":
            m["back_to"], m["mode"], m["osel"] = "lista", "opcoes", 0
        elif cmd == "back":
            if len(m["stack"]) > (1 if len(m["roots"]) == 1 else 0):
                left = m["stack"].pop()[0]
                self.music_rows(keep=left)
            else:
                self.music_close()

    # --- abrir pelo Arquivos ---

    def open_music_file(self, path):
        """Uma música escolhida no Arquivos: o tocador abre na pasta dela, tocando a partir dela."""
        self.open_music()
        folder = os.path.dirname(path)
        self.music["stack"] = [(folder, os.path.basename(folder))]
        self.music_rows(keep=None)
        self.music_play(start_song=path)

    # --- Vídeos ---

    def video_roots(self):
        if FAKE:
            return [(os.environ.get("OMNI_VIDEOS", "/tmp/omni36os-videos"), "Cartão 1")]
        return omni_video.roots()

    def open_videos(self, path=None, start=None):
        """Lista das pastas de vídeo (como no Arquivos): A entra numa pasta ou toca o vídeo, B volta."""
        roots = self.video_roots()
        if path is None and len(roots) == 1:
            path = roots[0][0]
        if path is None:
            if not roots:
                self.toast = (omni_i18n._("ui_video_empty_folder"), "aviso", self.t + 4)
                return
            rows = [{"name": n, "icon": "device-sd-card", "path": p, "dir": True} for p, n in roots]
            self.show_list(omni_i18n._("ui_card_videos"), "movie", rows, lambda r: self.open_videos(r["path"]), omni_i18n._("ui_hint_open"))
            self.picker.update(hints=[], app=VIDEO_COLORS, sub=omni_i18n._("ui_folder_select"))
            return
        top = path in [p for p, _ in roots]
        try:
            names = sorted(os.listdir(path), key=str.lower)
        except OSError:
            names = []
        dirs = [n for n in names if not n.startswith(".") and os.path.isdir(os.path.join(path, n))]
        vids = [n for n in names if omni_video.is_video(n)]
        rows = [] if top and len(roots) == 1 else [{"name": "..", "icon": "arrow-up", "up": True}]
        rows += [{"name": n, "icon": "folder", "dir": True, "path": os.path.join(path, n)} for n in dirs]
        rows += [{"name": n, "icon": "movie", "path": os.path.join(path, n)} for n in vids]
        if not rows:
            self.picker = None
            self.toast = (omni_i18n._("ui_video_empty"), "aviso", self.t + 4)
            return
        title = omni_i18n._("ui_card_videos") if top else os.path.basename(path)
        self.show_list(title, "movie", rows, lambda r: self.video_pick(path, r), omni_i18n._("ui_hint_open"), start)
        self.picker.update(hints=[], app=VIDEO_COLORS, sub=path)
        if not (top and len(roots) == 1):
            self.picker["on_back"] = lambda: self.open_videos(None if top else os.path.dirname(path))

    def video_pick(self, path, r):
        if r.get("up"):
            roots = [p for p, _ in self.video_roots()]
            self.open_videos(None if path in roots else os.path.dirname(path))
        elif r.get("dir"):
            self.open_videos(r["path"])
        else:
            self.play_video(r["path"])

    def play_video(self, path):
        """Vídeo em tela cheia (ffmpeg): A pausa, esquerda/direita 10 s, L1/R1 1 min, B volta."""
        mp = getattr(self, "music_player", None)
        if mp and mp.current() and not mp.paused:
            mp.toggle()                   # a música para enquanto o vídeo toca
        if not hasattr(self, "video_player"):
            self.video_player = omni_video.Player()
        pl = self.video_player

        def done(ok):
            if ok is True:
                if not FAKE:
                    omni.video_clocks()
                self.video = {"pl": pl, "name": os.path.splitext(os.path.basename(path))[0], "ui": self.t}
            else:
                self.toast = (pl.error or omni_i18n._("ui_video_open_failed"), "problema", self.t + 4)
        self.worker(lambda: pl.open(path), done, busy=omni_i18n._("ui_video_open_busy"))

    def video_input(self, cmd):
        v, pl = self.video, self.video["pl"]
        v["ui"] = self.t
        if cmd == "back":
            pl.close()
            self.video = None
            if not FAKE:
                omni.relax_clocks()
        elif cmd == "ok":
            if pl.ended:
                pl.start(0.0)
            else:
                pl.toggle()
        elif cmd in ("left", "right", "l1", "r1"):
            pl.seek({"left": -10, "right": 10, "l1": -60, "r1": 60}[cmd])

    def draw_video(self, dt):
        g, v = self.g, self.video
        pl = v["pl"]
        g.rrect(0, 0, W, H, 0, (0, 0, 0, 255), feather=0)
        w, h = pl.size
        with pl.lock:
            frame, serial = pl.frame, pl.serial
        if frame is not None:
            g.video(frame, serial, w, h, (W - w) // 2, (H - h) // 2)
        elif pl.ended:
            g.text("Medium", 14, omni_i18n._("ui_video_play_failed"), W / 2, H / 2, TEXT, "c", "m")
        else:
            g.arc(W / 2, H / 2, 26, 4, self.t * 400, self.t * 400 + 280, alpha(hexc("38bdf8"), 255))
        if not (pl.paused or pl.ended or frame is None or self.t - v["ui"] < 3):
            return
        a1, a2 = hexc("38bdf8"), hexc("8b5cf6")
        g.rrect(0, 0, W, 64, 0, (0, 0, 0, 170), feather=0)
        g.text("SemiBold", 16, v["name"][:52], 22, 22, ON_TEXT)
        g.rrect(0, H - 92, W, 92, 0, (0, 0, 0, 170), feather=0)
        tm = lambda x: f"{int(x) // 3600}:{int(x) % 3600 // 60:02d}:{int(x) % 60:02d}" if x >= 3600 else \
            f"{int(x) // 60}:{int(x) % 60:02d}"
        pos, dur = pl.position(), pl.duration()
        bx, by, bw = 72, H - 80, W - 144
        g.rrect(bx, by, bw, 6, 3, (255, 255, 255, 50))
        if dur:
            g.rrect(bx, by, max(6, bw * min(1, pos / dur)), 6, 3, a1, a2)
        g.text("Medium", 12, tm(pos), bx - 12, by + 3, ON_TEXT, "r", "m")
        g.text("Medium", 12, tm(dur) if dur else "--:--", bx + bw + 12, by + 3, ON_TEXT, "l", "m")
        if pl.paused:
            g.circle(W / 2, H / 2, 34, (0, 0, 0, 150))
            g.icon("player-pause", W / 2 - 18, H / 2 - 18, 36, ON_TEXT)
        hints = ([("A", omni_i18n._("ui_hint_repeat"))] if pl.ended else [("A", omni_i18n._("ui_hint_continue") if pl.paused else omni_i18n._("ui_hint_pause"))]) + \
            [("LR", omni_i18n._("ui_hint_seek_10s")), ("L1", omni_i18n._("ui_hint_seek_minus_min")), ("R1", omni_i18n._("ui_hint_seek_plus_min")), ("B", omni_i18n._("ui_back"))]
        self.draw_footer_at(H - 40, [(*h, ON_TEXT) for h in hints], center=W / 2)

    # --- Notas ---

    def notes_dir(self):
        return os.environ.get("OMNI_NOTAS", "/tmp/omni36os-notas") if FAKE else NOTES_DIR

    def open_notes(self, start=None):
        """Bloco de notas: a primeira linha cria uma nota; A abre, X apaga."""
        folder = self.notes_dir()
        try:
            os.makedirs(folder, exist_ok=True)
            names = [n for n in os.listdir(folder) if is_text(n)]
        except OSError:
            names = []
        names.sort(key=lambda n: -os.path.getmtime(os.path.join(folder, n)))
        rows = [{"name": omni_i18n._("ui_new_note"), "icon": "plus", "new": True},
                {"name": omni_i18n._("ui_note_system_logs"), "icon": "folder", "logs": True,
                 "right": (omni_i18n._("ui_readonly"), MUTED)}]
        rows += [{"name": os.path.splitext(n)[0], "icon": "file-text", "path": os.path.join(folder, n),
                  "right": (time.strftime("%d/%m %H:%M", time.localtime(os.path.getmtime(os.path.join(folder, n)))), MUTED)}
                 for n in names]
        self.show_list(omni_i18n._("ui_card_notes"), "notes", rows, self.note_pick, omni_i18n._("ui_open"), start)
        self.picker.update(app=NOTE_COLORS, sub=folder)
        self.picker["on_x"] = self.note_delete
        self.picker["hints"] = [("X", omni_i18n._("ui_note_erase"))] if names else []

    def note_pick(self, r):
        if r.get("logs"):
            self.open_logs()
            return
        if not r.get("new"):
            self.open_note(r["path"])
            return

        def create(name):
            name = "".join(c for c in name.strip() if c not in '/\\:*?"<>|').strip(". ")
            if not name:
                return
            path = os.path.join(self.notes_dir(), name + ".txt")
            if not os.path.exists(path):
                self.note_write(path, "")
            self.open_note(path, edit=True)
        self.keyboard(omni_i18n._("ui_note_name_prompt"), create, hint=omni_i18n._("ui_note_name_hint"))

    # --- Notas > Logs do sistema (só leitura) ---

    def logs_root(self):
        return os.environ.get("OMNI_LOGS", "/tmp/omni36os-logs-sim") if FAKE else omni_logs.ROOT

    def open_logs(self, func=None, start=None, from_page=False):
        """As pastas de /roms/logs (uma por função) e, dentro, os logs, o mais novo primeiro."""
        root = self.logs_root()
        if func is None:
            try:
                funcs = sorted((d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))),
                               key=lambda d: (omni_logs.FUNCS.index(d) if d in omni_logs.FUNCS else 99, d))
            except OSError:
                funcs = []
            rows = []
            for d in funcs:
                try:
                    n = sum(1 for f in os.listdir(os.path.join(root, d)) if not f.startswith("."))
                except OSError:
                    n = 0
                if not n:
                    continue                  # pasta vazia: não aparece
                rows.append({"name": omni_logs.NAMES.get(d, d.capitalize()), "icon": "folder", "func": d,
                             "right": (omni_i18n._("ui_logs_files_count").format(count=n), MUTED)})
            if not rows:
                self.toast = (omni_i18n._("ui_logs_none"), "info", self.t + 3)
                return
            self.show_list(omni_i18n._("ui_logs_title"), "file-text", rows, lambda r: self.open_logs(r["func"]), omni_i18n._("ui_open"), start)
            self.picker.update(app=NOTE_COLORS, sub=root, hints=[])
            self.picker["on_back"] = lambda: self.open_notes(start=1)
            return
        folder = os.path.join(root, func)
        try:
            names = [f for f in os.listdir(folder) if not f.startswith(".") and os.path.isfile(os.path.join(folder, f))]
        except OSError:
            names = []
        names.sort(key=lambda f: -os.path.getmtime(os.path.join(folder, f)))
        rows = [{"name": f, "icon": "file-text", "path": os.path.join(folder, f),
                 "right": (time.strftime("%d/%m %H:%M", time.localtime(os.path.getmtime(os.path.join(folder, f)))), MUTED)}
                for f in names]
        if not rows:
            self.toast = (omni_i18n._("ui_logs_no_report") if func == omni_logs.TESTS else omni_i18n._("ui_folder_empty"), "info", self.t + 3)
            return
        self.show_list(omni_logs.NAMES.get(func, func), "file-text", rows, lambda r: self.open_log(r["path"]),
                       omni_i18n._("ui_open"), start)
        self.picker.update(app=NOTE_COLORS, sub=folder, hints=[])
        if not from_page:                 # atalho (Testar ports): o B volta direto para a página
            self.picker["on_back"] = lambda: self.open_logs()

    LOG_TAIL = 64 * 1024                  # logs grandes: só o fim

    def open_log(self, path):
        """Log para ler (só leitura); dos grandes, só o fim, onde está o mais novo."""
        try:
            size = os.path.getsize(path)
            with open(path, "rb") as f:
                if size > self.LOG_TAIL:
                    f.seek(size - self.LOG_TAIL)
                data = f.read()
        except OSError as e:
            self.toast = (omni_i18n._("ui_cannot_open").format(error=e.strerror), "problema", self.t + 3.5)
            return
        text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")
        text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)          # cores do terminal
        if size > self.LOG_TAIL:
            text = omni_i18n._("ui_read_truncated") + "\n" + text[text.find("\n") + 1:]
        self.note = {"path": path, "text": text, "top": 10 ** 9, "scroll": 0.0, "jump": True,   # abre no fim
                     "notes": False, "ro": True}

    def note_delete(self, r):
        if r.get("new") or r.get("logs"):
            return
        self.modal = {"title": omni_i18n._("ui_note_delete_confirm"), "icon": "trash", "sel": 1,
                      "buttons": [omni_i18n._("btn_delete"), omni_i18n._("btn_cancel")],
                      "text": omni_i18n._("ui_note_delete_text").format(name=r['name']),
                      "fns": [lambda: self.note_remove(r["path"]), lambda: None]}

    def note_remove(self, path):
        try:
            os.remove(path)
        except OSError as e:
            self.toast = (omni_i18n._("ui_cannot_delete").format(error=e.strerror), "problema", self.t + 3.5)
        self.open_notes()

    def note_write(self, path, text):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
        if not FAKE:
            try:
                os.chown(path, 1000, 1000)
            except OSError:
                pass

    NOTE_LIMIT = 20000                    # caracteres que o editor aceita

    def open_note(self, path, edit=False):
        """A nota inteira para ler (cima/baixo rolam, L1/R1 pulam a página); A edita a nota toda."""
        try:
            if os.path.getsize(path) > 256 * 1024:
                self.toast = (omni_i18n._("ui_note_too_large"), "aviso", self.t + 3.5)
                return
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            self.toast = (omni_i18n._("ui_cannot_open").format(error=e.strerror), "problema", self.t + 3.5)
            return
        self.note = {"path": path, "text": text, "top": 0, "scroll": 0.0,
                     "notes": path.startswith(self.notes_dir() + "/")}
        if edit:
            self.note_edit()

    def note_save(self):
        n = self.note
        try:
            self.note_write(n["path"], n["text"])
        except OSError as e:
            self.toast = (omni_i18n._("ui_note_open_error").format(error=e.strerror), "problema", self.t + 3.5)

    def note_edit(self):
        """A nota toda no teclado, como numa máquina de escrever: o texto sobe quando a linha enche.
        L1/R1 levam o cursor para a linha de cima ou de baixo; START salva, SELECT desiste."""
        n = self.note
        if len(n["text"]) > self.NOTE_LIMIT:
            self.toast = (omni_i18n._("ui_note_edit_too_large"), "aviso", self.t + 3.5)
            return

        def done(val):
            n["text"] = val
            self.note_save()
            self.toast = (omni_i18n._("ui_note_saved"), "ok", self.t + 2)
        name = os.path.splitext(os.path.basename(n["path"]))[0] if n["notes"] else os.path.basename(n["path"])
        self.keyboard(name, done, value=n["text"], texto=True)

    def text_spans(self, text, width, weight="Regular", size=14):
        """Quebra o texto em linhas que cabem em `width`: [(início, fim)] em índices do texto.
        O fim não inclui o espaço onde a linha quebrou nem o \\n."""
        key = ("spans", text, width, weight, size)
        hit = self.g.wcache.get(key)
        if hit is not None:
            return hit
        if len(self.g.wcache) > 500:
            self.g.wcache.clear()
        g, out, i = self.g, [], 0
        fits = lambda a, b: g.measure(weight, size, text[a:b])[0] <= width
        for para in text.split("\n"):
            a, end = i, i + len(para)
            if a == end:
                out.append((a, a))
            while a < end:
                if fits(a, end):
                    out.append((a, end))
                    break
                lo, hi = a + 1, end           # maior pedaço que cabe
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    lo, hi = (mid, hi) if fits(a, mid) else (lo, mid - 1)
                cut = text.rfind(" ", a, lo + 1)
                b = cut if cut > a else lo    # quebra no espaço; palavra maior que a linha, no meio
                out.append((a, b))
                a = b + 1 if cut > a else b
            i = end + 1
        self.g.wcache[key] = out
        return out

    def note_input(self, cmd):
        n = self.note
        if cmd == "ok":
            if not n.get("ro"):
                self.note_edit()
        elif cmd == "back":
            self.note = None
            if n["notes"] and self.picker and self.picker.get("title") == omni_i18n._("ui_card_notes"):
                self.open_notes()         # a nota sobe para o topo da lista
        else:
            step = {"up": -1, "down": 1, "l1": -10, "r1": 10, "left": -10, "right": 10}.get(cmd)
            if step:
                n["top"] = max(0, min(n.get("max", 0), n["top"] + step))

    def draw_note(self, dt):
        g, n = self.g, self.note
        a1, a2 = NOTE_COLORS
        g.rrect(22, 22, 40, 40, 12, a1, a2)
        g.icon("notes", 30, 30, 24, ON_TEXT)
        name = os.path.basename(n["path"])
        if n["notes"]:
            name = os.path.splitext(name)[0]
        g.text("Bold", 22, name[:24], 74, 22, TEXT)
        g.text("Regular", 12, os.path.dirname(n["path"])[-34:], 75, 49, MUTED)
        self.draw_status()
        rh, ly, bot = 24, 86, 420
        g.rrect(16, 74, W - 32, 352, 18, alpha(GLASS, 14))
        text = n["text"]
        spans = self.text_spans(text, W - 90)
        vis = int((bot - ly) // rh)
        n["max"] = max(0, len(spans) - vis)
        n["top"] = min(n["top"], n["max"])
        if n.pop("jump", False):
            n["scroll"] = n["top"] * rh
        n["scroll"] = approach(n["scroll"], n["top"] * rh, dt, 18)
        g.clip(16, ly - 4, W - 32, bot - ly + 8)
        first = max(0, int(n["scroll"] // rh) - 1)
        for k in range(first, min(len(spans), first + vis + 3)):
            a, b = spans[k]
            g.text("Regular", 14, text[a:b], 40, ly + k * rh - n["scroll"], TEXT)
        g.clip()
        if n["max"]:                          # barra de rolagem
            th = bot - ly
            bh = max(30, th * vis / len(spans))
            g.rrect(W - 28, ly, 4, th, 2, ink(18))
            g.rrect(W - 28, ly + (th - bh) * n["scroll"] / (n["max"] * rh), 4, bh, 2, alpha(a1, 220))
        if not text.strip():
            g.text("Regular", 13, omni_i18n._("ui_note_empty_hint"), W / 2, 240, MUTED, "c")
        hints = ([] if n.get("ro") else [("A", omni_i18n._("ui_hint_edit"))]) + ([("UD", omni_i18n._("ui_hint_scroll")), ("L1/R1", omni_i18n._("ui_hint_page"))] if n["max"] else []) + [("B", omni_i18n._("ui_hint_close"))]
        self.draw_footer_at(H - 29, hints, center=W / 2)

    MUSIC_OPTIONS = ()

    def music_options(self):
        return ((omni_i18n._("ui_music_visualization"), "wave-sine", "vis", list(VIS_NAMES), VIS_NAMES,
                 omni_i18n._("ui_music_visualization_tip")),
                (omni_i18n._("ui_music_screen_timeout"), "moon", "tela", list(BLANK_NAMES), BLANK_NAMES,
                 omni_i18n._("ui_music_screen_timeout_tip")),
                (omni_i18n._("ui_music_read_subfolders"), "folder", "sub", [False, True], ONOFF,
                 omni_i18n._("ui_music_read_subfolders_tip")))

    def music_options_input(self, cmd):
        """Opções do app Músicas (START): cima/baixo escolhe, esquerda/direita ou A muda, B volta."""
        m = self.music
        n = len(self.MUSIC_OPTIONS)
        if cmd in ("up", "down"):
            m["osel"] = (m["osel"] + (1 if cmd == "down" else -1)) % n
        elif cmd in ("left", "right", "ok"):
            _, _, key, values, _, _ = self.MUSIC_OPTIONS[m["osel"]]
            cur = music_cfg()[key]
            k = values.index(cur) if cur in values else 0
            val = values[(k + (-1 if cmd == "left" else 1)) % len(values)]
            music_save(**{key: val})
            if key == "vis":
                m["vis"] = val
        elif cmd in ("back", "start"):
            m["mode"] = m.get("back_to", "lista")

    def draw_music_options(self, dt, a1, a2):
        g, m = self.g, self.music
        cfg = music_cfg()
        g.rrect(22, 22, 40, 40, 12, a1, a2)
        g.icon("music", 30, 30, 24, ON_TEXT)
        g.text("Bold", 22, omni_i18n._("ui_music_options"), 74, 22, TEXT)
        g.text("Regular", 12, omni_i18n._("ui_card_music_subtitle"), 75, 49, MUTED)
        for i, (label, icon, key, _, names, _) in enumerate(self.MUSIC_OPTIONS):
            y, on = 84 + i * 64, i == m["osel"]
            if on:
                g.rrect(22, y, W - 44, 56, 16, a1, a2)
            else:
                g.rrect(22, y, W - 44, 56, 16, alpha(GLASS, 14))
            c = ON_TEXT if on else TEXT
            g.icon(icon, 40, y + 17, 22, c)
            g.text("Regular", 12, label, 76, y + 10, c if on else MUTED)
            g.text("SemiBold", 15, names.get(cfg[key], str(cfg[key])), 76, y + 27, c)
            g.chevron(W - 56, y + 28, 8, c, left=True)
            g.chevron(W - 40, y + 28, 8, c)
        tipt = self.MUSIC_OPTIONS[m["osel"]][5]
        for k, ln in enumerate(g.wrap("Regular", 13, tipt, W - 80)):
            g.text("Regular", 13, ln, 40, 290 + 20 * k, MUTED)
        self.draw_footer_at(H - 29, [("LR", omni_i18n._("ui_hint_change")), ("B", omni_i18n._("ui_back"))], center=W / 2)

    def draw_music(self, dt):
        g, m = self.g, self.music
        pl = m["player"]
        pl.tick() if pl.ok else None
        blank = music_cfg()["tela"]
        playing = pl.current() and not pl.paused
        if blank and playing and not m["off"] and self.t - m["last"] > blank:
            self.music_screen(False)
        if m["off"] and (self.modal or self.busy):   # o menu de energia por cima acende a tela
            self.music_screen(True)
        if m["off"]:
            g.rrect(0, 0, W, H, 0, (0, 0, 0, 255), feather=0)
            return
        a1, a2 = hexc("f472b6"), hexc("8b5cf6")
        if m["mode"] == "opcoes":
            self.draw_music_options(dt, a1, a2)
        elif m["mode"] == "tocando" and pl.current():
            self.draw_playing(dt, a1, a2)
        else:
            self.draw_music_list(dt, a1, a2)
        self.draw_status()

    def draw_music_list(self, dt, a1, a2):
        g, m, pl = self.g, self.music, self.music["player"]
        g.rrect(22, 22, 40, 40, 12, a1, a2)
        g.icon("music", 30, 30, 24, ON_TEXT)
        where = " / ".join(n for _, n in m["stack"]) or omni_i18n._("ui_folder_select")
        g.text("Bold", 22, omni_i18n._("ui_card_music_subtitle"), 74, 22, TEXT)
        g.text("Regular", 12, where[-34:], 75, 49, MUTED)
        cur = pl.current()
        bot = 370 if cur else 426
        rows, rh, ly = m["rows"], 36, 80
        g.rrect(16, ly - 6, W - 32, bot - ly + 6, 18, alpha(GLASS, 14))
        if not rows:
            msg = (omni_i18n._("ui_no_music_folders")
                   if not m["roots"] else omni_i18n._("ui_music_folder_empty"))
            for k, ln in enumerate(g.wrap("Regular", 13, msg, W - 120)):
                g.text("Regular", 13, ln, W / 2, 200 + 20 * k, MUTED, "c")
        vis = int((bot - ly) // rh)
        want = max(0, min(m["sel"] - vis // 2, len(rows) - vis))
        m["top"] = approach(m["top"], want * rh, dt, 18)
        g.clip(16, ly, W - 32, bot - ly)
        first = max(0, int(m["top"] // rh) - 1)
        for i in range(first, min(len(rows), first + vis + 3)):
            r, y = rows[i], ly + i * rh - m["top"]
            on = i == m["sel"]
            if on:
                g.rrect(24, y, W - 48, rh - 4, 12, a1, a2)
            c = ON_TEXT if on else TEXT
            playing = cur and r.get("song") == cur[0]
            g.icon("folder" if "dir" in r else ("player-play" if playing else "music"), 36, y + 7, 18,
                   c if on else (a1 if playing else MUTED))
            name = r["name"]
            limit = W - 120 - (140 if r.get("artist") else 0)
            while g.measure("Medium", 14, name)[0] > limit and len(name) > 4:
                name = name[:-2]
            g.text("SemiBold" if on else "Medium", 14, name if name == r["name"] else name.rstrip() + "…",
                   64, y + rh / 2 - 2, c, "l", "m")
            if r.get("artist"):
                g.text("Regular", 12, r["artist"][:22], W - 40, y + rh / 2 - 2, c if on else MUTED, "r", "m")
            elif "dir" in r:
                g.chevron(W - 44, y + rh / 2 - 2, 8, c if on else FAINT)
        g.clip()
        if cur:                               # o que está tocando, embaixo
            g.rrect(16, 380, W - 32, 46, 16, alpha(a1, 40), alpha(a2, 40))
            art = self.music_cover(cur[0])
            if not (art and g.picture(art, 24, 386, 34, 34)):
                g.icon("player-pause" if not pl.paused else "player-play", 30, 391, 22, TEXT)
            g.text("SemiBold", 13, cur[1][:48], 66, 392, TEXT)
            g.text("Regular", 11, (cur[2] or omni_i18n._("ui_hint_now_playing"))[:48], 66, 409, MUTED)
            self.draw_spectrum_mini(W - 120, 388, 90, 30, a1)
        hints = [("A", omni_i18n._("ui_hint_open") if rows and "dir" in rows[m["sel"]] else omni_i18n._("ui_hint_play")), ("B", omni_i18n._("ui_back"))]
        if m["stack"]:
            hints.insert(1, ("Y", omni_i18n._("ui_hint_play_all")))
        if cur:
            hints.insert(1, ("X", omni_i18n._("ui_hint_now_playing")))
        hints.insert(-1, ("START", omni_i18n._("ui_hint_options")))
        self.draw_footer_at(H - 29, hints, center=W / 2)

    def music_spectrum(self):
        m, pl = self.music, self.music["player"]
        raw = omni_musica.spectrum(pl.samples(128)) if pl.current() and not pl.paused else [0.0] * omni_musica.BANDS
        # ganho automático: a faixa mais forte dos últimos segundos vira o topo (música baixa ou alta dança igual)
        m["gain"] = max(max(raw), m.get("gain", 0.02) * 0.992, 0.004)
        new = [min(1.0, (r / m["gain"]) ** 0.8) for r in raw]
        m["spec"] = [max(n, o * 0.82) for n, o in zip(new, m["spec"])]
        m["peaks"] = [max(s, p - 0.012) for s, p in zip(m["spec"], m["peaks"])]
        return m["spec"]

    def music_cover(self, song):
        """Caminho da capa da música ("" sem capa; None enquanto procura, fora da tela)."""
        covers = self.music.setdefault("covers", {})
        if song not in covers:
            covers[song] = None
            threading.Thread(target=lambda: covers.__setitem__(song, omni_musica.cover(song)), daemon=True).start()
        return covers[song]

    def draw_spectrum_mini(self, x, y, w, h, c):
        spec = self.music_spectrum()
        bw = w / len(spec)
        v = []
        for k, e in enumerate(spec):
            bh = max(2, h * e)
            x0, x1, y0 = x + k * bw + 1, x + (k + 1) * bw - 1, y + h - bh
            v += quad(x0, y0, x1, y + h, alpha(c, 255), alpha(c, 120))
        self.g.tris(v)

    def draw_playing(self, dt, a1, a2):
        g, m, pl = self.g, self.music, self.music["player"]
        cur = pl.current()
        spec = self.music_spectrum()
        bass = sum(spec[:3]) / 3
        m["phase"] += dt * (0.6 + 2.5 * bass)
        top, vh = 62, 232                    # área da visualização (embaixo da pílula de estado)
        vis = m["vis"]
        if vis == "barras":
            n, x0, w = len(spec) * 2, 40, W - 80
            bw = w / n
            vals = spec[::-1] + spec           # espelhado: graves no meio
            peaks = m["peaks"][::-1] + m["peaks"]
            v = []
            for k, e in enumerate(vals):
                bh = max(4, vh * 0.92 * e)
                xa, xb = x0 + k * bw + 2, x0 + (k + 1) * bw - 2
                v += quad(xa, top + vh - bh, xb, top + vh, alpha(a1, 250), alpha(a2, 200))
                v += quad(xa, top + vh + 4, xb, top + vh + 4 + min(14, bh * 0.2), alpha(a2, 70), alpha(a2, 0))   # reflexo
                py = top + vh - max(4, vh * 0.92 * peaks[k]) - 6
                v += quad(xa, py, xb, py + 3, alpha(TEXT, 220), alpha(TEXT, 220))
            g.tris(v)
        elif vis == "ondas":
            s = pl.samples(128) if not pl.paused else [0.0] * 128
            m["wgain"] = max(max(abs(x) for x in s), m.get("wgain", 0.05) * 0.99, 0.02)
            s = [x / m["wgain"] * 0.38 for x in s]
            g.blob(W / 2, top + vh / 2, 160 + 160 * bass, alpha(a2, 70))
            for layer, (c, amp, off) in enumerate(((a2, 0.6, 0.0), (a1, 1.0, 0.0), (TEXT, 0.35, 1.3))):
                pts = []
                for k, val in enumerate(s):
                    x = 20 + (W - 40) * k / (len(s) - 1)
                    wob = math.sin(k / 9 + m["phase"] * (1 + layer) + off) * 10 * (0.3 + bass)
                    pts.append((x, top + vh / 2 + val * vh * 0.9 * amp + wob))
                g.tris(polyline(pts, 3 if layer == 1 else 2, alpha(c, 230 if layer == 1 else 140)))
        elif vis == "anel":
            cx, cy, r0 = W / 2, top + vh / 2 + 6, 62 + 18 * bass
            g.blob(cx, cy, 150 + 80 * bass, alpha(a1, 80))
            n, v = 48, []
            vals = spec + spec[::-1]
            for k in range(n):
                e = vals[int(k * len(vals) / n)]
                a = 2 * math.pi * k / n + m["phase"] * 0.25
                l = 8 + 70 * e
                ca, sa = math.cos(a), math.sin(a)
                nx, ny = -sa * 3, ca * 3
                p0, p1 = (cx + ca * r0, cy + sa * r0), (cx + ca * (r0 + l), cy + sa * (r0 + l))
                c0, c1 = alpha(a2, 230), alpha(a1, 250)
                v += [(p0[0] - nx, p0[1] - ny, c0), (p0[0] + nx, p0[1] + ny, c0), (p1[0] - nx, p1[1] - ny, c1),
                      (p1[0] - nx, p1[1] - ny, c1), (p0[0] + nx, p0[1] + ny, c0), (p1[0] + nx, p1[1] + ny, c1)]
            g.tris(v)
            g.circle(cx, cy, r0 - 8, a1, a2)
            g.icon("music", cx - 22, cy - 22, 44, ON_TEXT)
        elif vis == "aurora":
            t = m["phase"]
            for k, (c, band) in enumerate(((a1, 0), (a2, 5), (hexc("38bdf8"), 10), (hexc("fbbf24"), 14))):
                e = spec[band]
                x = W / 2 + math.sin(t * (0.5 + k * 0.17) + k * 2) * 200
                y = top + vh / 2 + math.cos(t * (0.4 + k * 0.13) + k) * 80
                g.blob(x, y, 110 + 170 * e, alpha(c, 70 + 120 * e))
        else:                                # capa do álbum (a da pasta ou a embutida no mp3)
            art = self.music_cover(cur[0])
            g.blob(W / 2, top + vh / 2, 190 + 60 * bass, alpha(a1, 90))
            if not (art and g.picture(art, 40, top + 4, W - 80, vh - 8)):
                g.rrect(W / 2 - 80, top + vh / 2 - 80, 160, 160, 32, a1, a2)
                g.icon("music", W / 2 - 36, top + vh / 2 - 36, 72, ON_TEXT)
        # música, artista e tempo
        g.text("Bold", 20, cur[1][:40], W / 2, 314, TEXT, "c")
        sub = cur[2] or os.path.basename(os.path.dirname(cur[0]))
        g.text("Regular", 13, f"{sub[:40]}  ·  {pl.i + 1} de {len(pl.list)}", W / 2, 342, MUTED, "c")
        pos, dur = pl.position(), pl.duration()
        bx, bw, by = 60, W - 120, 378
        g.rrect(bx, by, bw, 6, 3, ink(30))
        if dur > 0:
            g.rrect(bx, by, max(6, bw * min(1, pos / dur)), 6, 3, a1, a2)
        tm = lambda x: f"{int(x) // 60}:{int(x) % 60:02d}"
        g.text("Medium", 11, tm(pos), bx - 8, by + 3, MUTED, "r", "m")
        g.text("Medium", 11, tm(dur) if dur > 0 else "--:--", bx + bw + 8, by + 3, MUTED, "l", "m")
        if pl.paused:
            g.text("SemiBold", 12, omni_i18n._("ui_music_paused"), W / 2, by + 22, a1, "c", "m")
        self.draw_footer_at(H - 29, [("A", omni_i18n._("ui_hint_play") if pl.paused else omni_i18n._("ui_hint_pause")),
                                     ("LR", omni_i18n._("ui_hint_music")), ("L1", omni_i18n._("ui_hint_seek_minus_10")),
                                     ("R1", omni_i18n._("ui_hint_seek_plus_10")), ("Y", omni_i18n._("ui_hint_visualizer")),
                                     ("START", omni_i18n._("ui_hint_options")), ("B", omni_i18n._("ui_hint_playback_list"))], center=W / 2)

    def _fs(self, fn, busy=omni_i18n._("ui_working")):
        here = self.files_at
        sel = self.picker["sel"] if self.picker else 0

        def done(res):
            txt = omni_i18n._("ui_error_prefix").format(error=res) if isinstance(res, Exception) else str(res)
            self.toast = (txt, "problema" if isinstance(res, Exception) else "ok", self.t + 3.5)
            self.open_files(here, sel)
        self.worker((lambda: "teste") if FAKE else fn, done, busy=busy)

    def file_menu(self, r):
        if r.get("up") or "path" not in r:
            return
        path, name = r["path"], os.path.basename(r["path"])

        def rename():
            self.keyboard(f"{omni_i18n._('ui_file_rename_prompt')} {name}", lambda new: self._fs(lambda: omni_sistema.fs_rename(path, new)),
                          value=name)

        def delete():                     # confirma sem contagem; Cancelar vem escolhido
            self.modal = {"title": omni_i18n._("ui_delete_item_confirm").format(name=name), "icon": "trash", "sel": 1,
                          "buttons": [omni_i18n._("ui_file_delete_label"), omni_i18n._("btn_cancel")],
                          "text": omni_i18n._("ui_file_delete_folder_text" if r.get("dir") else "ui_file_delete_text"),
                          "fn": lambda: self._fs(lambda: omni_sistema.fs_delete(path), omni_i18n._("ui_file_delete_busy")),
                          "on_back": back}

        def mark(move):
            self.clip = (path, move)
            key = "ui_file_move_toast" if move else "ui_file_copy_toast"
            self.toast = (omni_i18n._(key).format(name=name), "ok", self.t + 4)
            self.open_files(self.files_at, self.picker["sel"] if self.picker else None)
        self.picker = None
        back = lambda: self.open_files(self.files_at)
        self.modal = {"title": name, "icon": "folder" if r.get("dir") else "file", "sel": 0,
                      "buttons": [omni_i18n._("ui_file_copy_label"), omni_i18n._("ui_file_move_label"),
                                  omni_i18n._("ui_file_rename_label"), omni_i18n._("ui_file_delete_label")],
                      "text": (omni_i18n._("ui_file_folder_label") if r.get("dir") else f"{omni_i18n._('ui_file_file_label')}, {r['right'][0]}") + f"\n{path}",
                      "fns": [lambda: mark(False), lambda: mark(True), rename, delete], "on_back": back}

    def folder_menu(self, _r=None):
        here = self.files_at
        if not here:
            return
        clip = getattr(self, "clip", None)
        btns, fns = [], []
        if clip:
            src, move = clip

            def paste():
                self.clip = None
                self._fs(lambda: omni_sistema.fs_paste(src, here, move),
                         omni_i18n._("ui_file_paste_busy" if move else "ui_file_copy_busy"))
            btns.append(omni_i18n._("ui_card_paste_here"))
            fns.append(paste)
        btns.append(omni_i18n._("ui_file_new_folder"))
        fns.append(lambda: self.keyboard(omni_i18n._("ui_file_new_folder_prompt"), lambda n: self._fs(lambda: omni_sistema.fs_mkdir(here, n))))
        btns.append(omni_i18n._("ui_back"))
        fns.append(lambda: self.open_files(here))
        self.picker = None
        text = omni_i18n._("ui_file_current_folder").format(path=here)
        if clip:
            action = omni_i18n._("ui_file_move_action" if clip[1] else "ui_file_copy_action")
            text += f"\n{action}: {os.path.basename(clip[0])}"
        self.modal = {"title": omni_i18n._("ui_file_this_folder"), "icon": "folder-plus", "sel": 0, "buttons": btns, "fns": fns,
                      "text": text, "on_back": lambda: self.open_files(here)}

    # --- biblioteca (tela inicial) ---

    def lib_lists(self):
        """[(título, ícone, [(sistema, jogo)])]: uma lista só, com todos os ports em ordem de nome."""
        pairs = [(s, g) for s in self.games() for g in s["games"]]
        pairs.sort(key=lambda p: (not p[1].get("fav"), p[1]["name"].lower()))   # favoritos primeiro
        return [("Ports", "device-gamepad-2", pairs)] if pairs else []

    def select_last_played(self):
        """Ao abrir Ports, o destaque fica no último port jogado (o de "Última vez" mais nova)."""
        lists = self.lib_lists()
        if not lists:
            return
        games = lists[0][2]
        try:
            with open(omni_games.LAST) as f:
                path = f.read().strip()
        except (OSError, NameError):     # simulador: sem omni_games
            path = ""
        best = next((i for i, (_s, g) in enumerate(games) if path and g["path"] == path), None)
        if best is None:                  # sem registro próprio: a "Última vez" do ES
            best = max(range(len(games)), key=lambda i: games[i][1].get("last") or "", default=None)
            if best is not None and not games[best][1].get("last"):
                best = None
        if best is not None:
            self.lib.update(sys=0, game=best, top=0.0)

    def library_input(self, cmd):
        lists, lb = self.lib_lists(), self.lib
        if cmd == "back":                 # B: de volta aos cards, com Ports escolhido
            self.view = "menu"
            self.sel = 0
            return
        if not lists:
            return
        lb["sys"] = 0
        games = lists[0][2]
        if cmd in ("up", "down"):
            lb["game"] = (lb["game"] + (1 if cmd == "down" else -1)) % len(games)
        elif cmd in ("left", "right"):     # página de 10 (para nas pontas)
            lb["game"] = max(0, min(len(games) - 1, lb["game"] + (10 if cmd == "right" else -10)))
        elif cmd in ("l1", "r1"):
            first = lambda i: (games[i][1]["name"][:1] or " ").upper()
            k, cur = lb["game"], first(lb["game"])
            if cmd == "r1":
                lb["game"] = next((i for i in range(k, len(games)) if first(i) != cur), len(games) - 1)
            else:
                prev = [i for i in range(k) if first(i) != cur]
                lb["game"] = next((i for i in range(len(games)) if prev and first(i) == first(prev[-1])), 0)
        elif cmd == "ok":            # a lista já mostra capa e descrição: A abre o jogo direto
            s, g = games[min(lb["game"], len(games) - 1)]
            self.play(s, g)

    def meta(self, name, path=""):
        """Ficha do jogo (cache em memória): pasta info do port + PortMaster/Steam.
        Pede a busca na internet uma vez, só com o Wi-Fi conectado; a pasta info manda sobre ela."""
        cache = self.__dict__.setdefault("meta_cache", {})
        if name not in cache:
            net = omni_meta.cached(name)
            loc = omni_meta.local(path)
            cache[name] = (net, dict(net or {}, **loc) if loc else net)
        net, info = cache[name]
        if self.searching(name) and name not in self.__dict__.setdefault("meta_tried", set()):
            self.meta_tried.add(name)
            omni_meta.want(name, path, lambda n: cache.pop(n, None))   # ao terminar, relê do disco
        return info

    def searching(self, name):
        """A capa e a descrição deste port ainda vão ser buscadas agora? Nunca por cima de um jogo
        pausado (o jogo fica com todo o processador), sem Wi-Fi ou com a busca desligada."""
        net = self.__dict__.get("meta_cache", {}).get(name, (None,))[0]
        return net is None and HUB != "jogo" and self.status.get("conectado") and busca_on()

    def draw_library(self, dt, fade):
        g, lb = self.g, self.lib
        lists = self.lib_lists()
        a1, a2 = self.accent
        if not lists:
            g.text("Bold", 20, omni_i18n._("ui_library_no_ports"), W / 2, 200, TEXT, "c")
            g.text("Regular", 13, omni_i18n._("ui_library_no_ports_tip"),
                   W / 2, 232, MUTED, "c")
            self.draw_footer([("B", omni_i18n._("ui_hint_back"), TEXT)])
            return
        title, icon, games = lists[0]
        lb["sys"] = 0
        lb["game"] = min(lb["game"], len(games) - 1)
        rh, bot_y = 30, H - 44
        # jogos (esquerda)
        gx, gw = 16, 250
        g.text("Bold", 20, title, gx + 4, 58, TEXT)
        g.text("Regular", 12, omni_i18n._("ui_library_game_count").format(count=len(games)), gx + 6 + g.measure("Bold", 20, title)[0] + 10, 66, MUTED)
        ly, lh = 92, bot_y - 92
        g.rrect(gx, ly - 6, gw, lh + 6, 18, alpha(GLASS, 14 * fade))
        vis = int(lh // rh)
        want = max(0, min(lb["game"] - vis // 2, len(games) - vis))
        lb["top"] = approach(lb.get("top", 0.0), want * rh, dt, 18)
        g.clip(gx, ly, gw, lh)
        first_row = max(0, int(lb["top"] // rh) - 1)
        for i in range(first_row, min(len(games), first_row + vis + 3)):
            s, game = games[i]
            y = ly + i * rh - lb["top"]
            on = i == lb["game"]
            if on:
                g.rrect(gx + 6, y, gw - 12, rh - 2, 10, a1, a2)
            name = game["name"]
            room = gw - (88 if game.get("fav") else 70)
            while g.measure("Regular", 14, name)[0] > room and len(name) > 6:
                name = name[:-2]
            if name != game["name"]:
                name = name.rstrip() + "…"
            g.text("SemiBold" if on else "Regular", 14, name, gx + 16, y + 6, ON_TEXT if on else TEXT)
            soft = ON_TEXT if on else FAINT
            g.icon("device-sd-card", gx + gw - 40, y + 8, 12, soft)                  # em qual cartão está
            g.text("Medium", 11, card_of(game), gx + gw - 26, y + 8, soft)
            if game.get("fav"):
                g.icon("check", gx + gw - 60, y + 7, 14, soft)                       # favorito
        g.clip()
        if len(games) > vis:
            bh = max(24, lh * vis / len(games))
            by = ly + (lh - bh) * min(1, lb["top"] / max(1, (len(games) - vis) * rh))
            g.rrect(gx + gw - 5, by, 3, bh, 2, alpha(a1, 220))
        # ficha do jogo (direita): capa e dados da Steam + o que o console sabe
        s, game = games[lb["game"]]
        info = self.meta(game["name"], game.get("path", ""))
        px, py, pw, ph = gx + gw + 14, 50, W - (gx + gw + 14) - 16, bot_y - 50
        g.rrect(px, py, pw, ph, 18, alpha(GLASS, 14 * fade))
        cw_, ch_ = pw - 24, round((pw - 24) * 215 / 460)
        cover = info and info.get("capa")
        g.rrect(px + 12, py + 12, cw_, ch_, 12, ink(12))
        if not (cover and g.picture(cover, px + 12, py + 12, cw_, ch_, 255 * fade)):
            g.icon("device-gamepad-2", px + 12 + cw_ / 2 - 24, py + 12 + ch_ / 2 - 30, 48, FAINT)
            if self.searching(game["name"]) and ((info or {}).get("descricao") or game.get("desc")):
                g.text("Regular", 11, omni_i18n._("ui_card_search_image"), px + 12 + cw_ / 2, py + 12 + ch_ / 2 + 30, MUTED, "c")
        y = py + ch_ + 22
        name = (info or {}).get("nome") or game["name"]
        for ln in g.wrap("Bold", 17, name, pw - 28)[:2]:
            g.text("Bold", 17, ln, px + 14, y, TEXT)
            y += 22
        sub = " · ".join(x for x in ((info or {}).get("estudio", "")[:30], (info or {}).get("lancamento", "")) if x)
        if sub:
            g.text("Medium", 11, sub, px + 14, y + 2, a1)
            y += 18
        if (info or {}).get("generos"):
            g.text("Regular", 11, info["generos"], px + 14, y + 2, MUTED)
            y += 18
        desc = (info or {}).get("descricao") or game.get("desc") or (
            (omni_i18n._("ui_searching_description") if cover else omni_i18n._("ui_searching_image_description"))
            if self.searching(game["name"]) else
            omni_i18n._("ui_description_not_found") if self.meta_cache.get(game["name"], (None,))[0] is not None else
            omni_i18n._("ui_auto_search_off") if not busca_on() else
            omni_i18n._("ui_no_description_enable_wifi"))
        local = [omni_i18n._("ui_card_sd_label").format(number=card_of(game))]
        if (info or {}).get("porter"):
            local.append("Port: " + info["porter"][:28])
        if info and "pronto" in info and not info["pronto"]:
            local.append(omni_i18n._("ui_card_port_required_files"))
        if game.get("plays"):
            local.append(omni_i18n._("ui_card_played_count").format(count=game['plays']))
        if game.get("time"):
            local.append(omni_i18n._("ui_card_time_hours_minutes").format(hours=game['time'] // 3600,
                                                                            minutes=game['time'] % 3600 // 60))
        room = int((py + ph - (30 if local else 12) - y - 4) // 17)
        lines = g.wrap("Regular", 12, desc, pw - 28)
        for k, ln in enumerate(lines[:max(0, room)]):
            if k == room - 1 and len(lines) > room:
                ln = ln.rstrip(" .,") + "…"
            g.text("Regular", 12, ln, px + 14, y + 4 + 17 * k, TEXT)
        if local:
            ln = " · ".join(local)
            while g.measure("Medium", 11, ln)[0] > pw - 28 and len(local) > 1:
                local.pop(1)                  # sem espaço: fica o cartão e o mais útil (o fim)
                ln = " · ".join(local)
            g.text("Medium", 11, ln, px + 14, py + ph - 24, FAINT)
        self.draw_footer([("A", omni_i18n._("ui_hint_play_game"), TEXT), ("LR", omni_i18n._("ui_hint_page"), MUTED),
                          ("L1 / R1", omni_i18n._("ui_hint_letter_page"), MUTED),
                          ("B", omni_i18n._("ui_back"), MUTED)])

    def power_menu(self, button=False):
        """Botão de power (Cancelar vem primeiro e apertar o power
        de novo desliga: o power_button.py vê o pedido em aberto)."""
        rows = [{"name": omni_i18n._("ui_power_suspend"), "icon": "clock", "do": "suspend"},
                {"name": omni_i18n._("ui_power_reboot"), "icon": "refresh", "do": "reboot"},
                {"name": omni_i18n._("ui_power_poweroff"), "icon": "power", "do": "poweroff"}]
        if HUB == "jogo" or os.environ.get("OMNI_JOGO") == "1":   # aberto por cima de um jogo
            rows = [{"name": self.hud_label(), "icon": "gauge", "do": "hud", "lr": True},
                    {"name": self.cap_label(), "icon": "battery-2", "do": "cap", "lr": True},
                    {"name": self.mouse_label(), "icon": "device-gamepad-2", "do": "mouse", "lr": True},
                    {"name": omni_i18n._("ui_power_type_text"), "icon": "keyboard", "do": "digitar"},
                    {"name": omni_i18n._("ui_power_screenshot"), "icon": "device-tv", "do": "shot"},
                    {"name": omni_i18n._("ui_power_close_game"), "icon": "x", "do": "close"}] + rows
        if button:
            rows = [{"name": omni_i18n._("ui_power_cancel"), "icon": "x", "do": "cancel"}] + rows

        def done():
            try:
                os.remove(POWER_PRESS)
            except OSError:
                pass

        def back():
            done()
            if getattr(self, "power_return", False):
                self.quit()           # volta para o jogo (que descongela)

        def go(r):
            self.picker = None
            if r["do"] == "cancel":
                return back()
            done()
            if r["do"] in ("hud", "cap", "shot", "close", "mouse"):
                return self.game_action(r["do"])
            if r["do"] == "digitar":
                return self.type_into_game()
            if r["do"] in ("reboot", "poweroff"):
                self.goodbye = "reiniciando" if r["do"] == "reboot" else "desligando"
                self.frame(0)             # a despedida já na tela do launcher, antes de ele fechar
                self.g.present()
            if r["do"] != "cancel" and not FAKE:
                omni.power({"what": r["do"]})
        self.show_list(omni_i18n._("ui_card_power_title"), "power", rows, go, omni_i18n._("ui_hint_choose"))
        if self.picker and rows[0 if not button else 1].get("lr"):
            def lr(r, d):
                self.game_toggle(r["do"], d)
                r["name"] = {"hud": self.hud_label, "cap": self.cap_label, "mouse": self.mouse_label}[r["do"]]()
            self.picker["on_lr"] = lr
            self.picker["hints"] = [("UD", "Escolher"), ("LR", "Mudar")]
        if self.picker and button:
            self.picker["on_back"] = back
            for path in (POWER_PRESS, POWER_PENDING):   # o menu está na tela: outro toque desliga
                try:
                    if path == POWER_PRESS:
                        with open(path, "w") as f:
                            f.write(str(os.getpid()))
                    else:
                        os.remove(path)
                except OSError:
                    pass

    def hud_label(self):
        cur = flag(HUD_FLAG) if not FAKE else getattr(self, "fake_hud", "0")
        return omni_i18n._("ui_counter_label").format(value=HUD_NAMES.get(cur, omni_i18n._("ui_counter_hidden")))

    def mouse_label(self):
        on = omni_mouse.mode_on() if not FAKE else getattr(self, "fake_mouse", False)
        return omni_i18n._("ui_power_mouse_mode").format(state=omni_i18n._("ui_power_on" if on else "ui_power_off"))

    def type_into_game(self):
        """Teclado do Omni36OS por cima do programa: o texto é digitado nele quando ele volta."""
        def done(text):
            if text and not FAKE:
                omni.save_file(omni_mouse.TYPE_FILE, text)
            self.quit()
        self.keyboard(omni_i18n._("tx_type_prog"), done, hint=omni_i18n._("tx_type_prog_hint"), texto=True)

    def cap_label(self):
        on = (flag(CAP_FLAG) not in ("", "0")) if not FAKE else getattr(self, "fake_cap", False)
        return omni_i18n._("ui_power_fps_limit").format(state=omni_i18n._("ui_power_on" if on else "ui_power_off"))

    def game_toggle(self, what, d=1):
        """Esquerda/direita no menu de energia: muda o contador ou o limite sem voltar ao jogo."""
        if FAKE:
            if what == "mouse":
                self.fake_mouse = not getattr(self, "fake_mouse", False)
                return
            if what == "hud":
                self.fake_hud = hud_step(getattr(self, "fake_hud", "0"), d)
            else:
                self.fake_cap = not getattr(self, "fake_cap", False)
            return
        if what == "hud":
            put_flag(HUD_FLAG, hud_step(flag(HUD_FLAG), d))
        elif what == "cap":
            put_flag(CAP_FLAG, "0" if flag(CAP_FLAG) not in ("", "0") else omni_combos.CAP_FPS)
        elif what == "mouse":
            omni_mouse.set_mode(not omni_mouse.mode_on())

    def game_action(self, what):
        """Menu de energia por cima de um jogo: o contador, o limite e a captura são do hud/omni_hud.so
        (arquivos em /dev/shm, valem quando o jogo volta); fechar encerra o jogo congelado."""
        if FAKE:
            self.toast = (f"Teste: {what}", "ok", self.t + 3)
            return
        if what == "hud":
            put_flag(HUD_FLAG, hud_step(flag(HUD_FLAG), 1))   # mesmo ciclo do FN + X
        elif what == "cap":
            put_flag(CAP_FLAG, "0" if flag(CAP_FLAG) not in ("", "0") else omni_combos.CAP_FPS)
        elif what == "mouse":
            omni_mouse.set_mode(not omni_mouse.mode_on())
        elif what == "shot":
            put_flag(SHOT_FLAG, int(time.time() * 1000))   # o jogo volta e salva o primeiro quadro
        elif what == "close":
            import omni_atalho
            omni_atalho.close_game(omni_atalho.game_pids())
        self.quit()                    # volta para o jogo (que descongela) ou para o Omni36OS

    # --- Brilho, contraste e volume ---

    def open_levels(self):
        """Painel por cima da página: esquerda/direita ajusta na hora, A confirma, B volta como estava."""
        items = [Slider(omni_i18n._("ui_level_brightness"), "sun", "brilho", lo=10),
                 Slider(omni_i18n._("ui_level_contrast"), "adjustments", "contraste"),
                 Slider(omni_i18n._("ui_level_volume"), "volume", "volume")]
        self.levels = {"items": items, "sel": 0, "orig": {it.key: it.value for it in items}}

    def levels_input(self, cmd):
        lv = self.levels
        it = lv["items"][lv["sel"]]
        if cmd in ("up", "down"):
            lv["sel"] = (lv["sel"] + (1 if cmd == "down" else -1)) % len(lv["items"])
        elif cmd in ("left", "right"):
            new = max(it.lo, min(100, it.value + (it.step if cmd == "right" else -it.step)))
            if new != it.value:
                it.value = new
                D.set(it.key, new)
                if it.key == "volume":        # a pílula do topo mostra o volume novo na hora
                    self.vol = new
        elif cmd == "ok":
            self.levels = None
            self.reload_findings()            # o painel da esquerda mostra os níveis novos
        elif cmd == "back":                   # desfaz o que mudou desde que o painel abriu
            for x in lv["items"]:
                if x.value != lv["orig"][x.key]:
                    D.set(x.key, lv["orig"][x.key])
                    if x.key == "volume":
                        self.vol = lv["orig"][x.key]
            self.levels = None

    def draw_levels(self, dt):
        g, lv = self.g, self.levels
        g.rrect(0, 0, W, H, 0, (5, 7, 20, 175), feather=0)
        mw, mh = 460, 336
        mx, my = (W - mw) / 2, (H - mh) / 2 - 10
        g.glow(mx, my, mw, mh, 24, alpha(self.accent[0], 60), 26)
        g.rrect(mx, my, mw, mh, 24, MODAL_A, MODAL_B)
        g.stroke(mx, my, mw, mh, 24, ink(25))
        g.rrect(mx + 24, my + 22, 38, 38, 12, self.accent[0], self.accent[1])
        g.icon("adjustments", mx + 32, my + 30, 22, ON_TEXT)
        g.text("Bold", 18, omni_i18n._("ui_build_display_levels"), mx + 74, my + 28, TEXT)
        c1 = self.accent[0]
        for k, it in enumerate(lv["items"]):
            on = k == lv["sel"]
            x, y, w, h = mx + 20, my + 80 + 68 * k, mw - 40, 58
            if on:
                g.rrect(x, y, w, h, 16, self.accent[0], self.accent[1])
            else:
                g.rrect(x, y, w, h, 16, ink(14))
            col = ON_TEXT if on else TEXT
            it.shown = approach(it.shown, it.value, dt, 16)
            g.icon(it.icon, x + 14, y + h / 2 - 11, 22, col)
            g.text("SemiBold", 14, it.label, x + 48, y + 10, col)
            g.text("SemiBold", 14, f"{it.value}%", x + w - 16, y + 10, col, "r")
            bx, by, bw = x + 48, y + 38, w - 64
            g.rrect(bx, by, bw, 6, 3, (255, 255, 255, 70) if on else ink(30))
            g.rrect(bx, by, max(6, bw * it.shown / 100), 6, 3, col if on else c1)
            g.circle(bx + bw * it.shown / 100, by + 3, 8 if on else 5, col)
        self.draw_footer_at(my + mh - 33, [("UD", omni_i18n._("ui_hint_choose")), ("LR", omni_i18n._("ui_hint_adjust")),
                                            ("A", omni_i18n._("ui_hint_confirm")), ("B", omni_i18n._("ui_hint_undo"))],
                            center=W / 2)

    def power_check(self):
        """Sinais do power_button.py: USR1 abre o menu de energia, USR2 mostra o aviso do pânico.
        Também o pedido de captura de tela (FN + Y) do serviço de atalhos."""
        if os.path.exists(UI_SHOT):
            try:
                os.remove(UI_SHOT)
                self.want_shot = True
            except OSError:
                pass
        if self.loading:
            return                    # depois da tela de abertura, para o aviso não sumir nela
        if not FAKE and self.t - getattr(self, "card2_t", 0) > 2:
            self.card2_t = self.t
            if omni.card2_pulled():      # tirado sem ejetar (agora ou durante um jogo): avisa
                self.games_idx = None
                self.card2_alert()
        if self.page == "cartoes" and not FAKE and self.t - getattr(self, "card2_pt", 0) > 2:
            self.card2_pt = self.t       # cartão 2 tirado ou posto com a página aberta: refaz a lista
            st = omni.card2_state()
            if st != getattr(self, "card2_seen", st):
                self.games_idx = None
                self.items = self.build_items("cartoes")
                self.item_sel = min(self.item_sel, len(self.items) - 1)
                self.reload_findings()
            self.card2_seen = st
        if self.want_power:
            self.want_power = False
            self.sheet = self.danger = self.modal = None
            self.power_menu(button=True)
        if self.want_msg or self.t - self.msg_t > 1.5:
            self.want_msg, self.msg_t = False, self.t
            # aviso de bateria fraca na tela e o carregador entrou: o aviso some sozinho
            if self.modal and self.modal.get("bat") and charging_now():
                self.modal = None
                self.toast = (omni_i18n._("tx_loading"), "ok", self.t + 2.5)
                if self.bat_return:
                    self.quit()
            try:
                with open(PANIC_MSG) as f:
                    msg = f.read().strip()
                os.remove(PANIC_MSG)
                if msg:
                    self.toast = (msg, "aviso", self.t + 3.5)
            except OSError:
                pass
            try:                          # bateria: alerta com título e OK, como no iPhone
                with open(BAT_MSG) as f:
                    title, _, text = f.read().strip().partition("\n")
                os.remove(BAT_MSG)
                if title:
                    self.modal = {"title": title, "icon": "battery-2", "sel": 0, "buttons": ["OK"], "text": text,
                                  "bat": title in omni_i18n.TRANSLATIONS["tx_bat_low"].values()}
                    if self.bat_return:   # por cima de uma ferramenta: o OK devolve a tela para ela
                        self.modal.update(fns=[self.quit], on_back=self.quit)
            except OSError:
                pass

    # --- jogos ---

    def flush_source(self):
        res = getattr(self, "source_dirty", None)
        if res is not None:
            self.source_dirty = None
            self.rescan_source(res)

    def rescan_source(self, res):
        """Trocou de onde os jogos são lidos: busca os ports e relê a biblioteca."""
        if isinstance(res, str) and res != "ok":
            self.toast = (res, "aviso", self.t + 4)

        def scan():
            if FAKE:
                time.sleep(1.0)
            idx = self.games(force=True)
            ports = self._testar()
            return idx, ports

        def done(out):
            if isinstance(out, Exception):
                self.toast = (omni_i18n._("ui_games_scan_error").format(error=out), "problema", self.t + 4)
                return
            idx, ports = out
            self.set_result("testar", ports)
            self.lib = {"sys": 0, "game": 0, "top": 0.0, "stop": 0.0}
            n = sum(len(s["games"]) for s in idx)
            self.toast = (omni_i18n._("tx_list_updated").format(games=n, ports=self.port_count), "ok", self.t + 4)
        self.worker(scan, done, busy=omni_i18n._("ui_games_scan_busy"))

    def open_sheet(self, s, g, back=None):
        self.picker = None
        # só a biblioteca joga; no menu do START a ficha é só para ver
        playable = self.view == "lib" and back is None
        self.sheet = {"s": s, "g": g, "sel": 0 if playable else 1, "back": back, "play": playable}

    def sheet_input(self, cmd):
        sh = self.sheet
        if cmd in ("left", "right") and sh["play"]:
            sh["sel"] = 1 - sh["sel"]
        elif cmd == "back" or (cmd == "ok" and sh["sel"] == 1):
            self.sheet = None
            if sh["back"]:
                sh["back"]()
        elif cmd == "ok":
            self.play(sh["s"], sh["g"])

    def open_gfn(self):
        self.open_app("gfn")

    def open_app(self, app):
        """Programa de Aplicativos (/roms/apps): abre como port; ao fechar, volta à página dele."""
        if self.busy_game():
            return
        if FAKE:
            self.toast = (f"Abriria o {omni_apps.APPS[app]['name']}", "ok", self.t + 3)
            return
        omni_games.play("ports", omni_apps.sh_path(app))
        self.running = False          # o launch-direct.sh abre e reabre o Omni36OS

    def play(self, s, g):
        if self.busy_game():
            return
        if FAKE:
            self.toast = (f"Abriria {g['name']}", "ok", self.t + 3)
            return
        try:
            omni.save_file(LIB_POS, json.dumps({k: self.lib[k] for k in ("sys", "game")}))
        except OSError:
            pass
        omni_games.play(s["name"], g["path"])
        self.running = False          # o launch-direct.sh abre o jogo e reabre o Omni36OS na biblioteca

    def draw_sheet(self, dt):
        g, sh = self.g, self.sheet
        s, game = sh["s"], sh["g"]
        G = omni_games if not FAKE else None
        g.rrect(0, 0, W, H, 0, (5, 7, 20, 190), feather=0)
        mx, my, mw, mh = 28, 24, W - 56, H - 48
        g.rrect(mx, my, mw, mh, 22, MODAL_A, MODAL_B)
        g.stroke(mx, my, mw, mh, 22, ink(25))
        a1, a2 = self.accent
        cx, cy, cw, ch = mx + 22, my + 22, 210, mh - 100
        g.rrect(cx, cy, cw, ch, 16, ink(14))
        cover = game.get("cover")
        if not (cover and os.path.exists(cover) and g.picture(cover, cx + 8, cy + 8, cw - 16, ch - 16)):
            g.rrect(cx + cw / 2 - 40, cy + ch / 2 - 40, 80, 80, 24, a1, a2)
            g.icon("device-gamepad-2", cx + cw / 2 - 22, cy + ch / 2 - 22, 44, ON_TEXT)
        tx, tw = cx + cw + 22, mw - cw - 66
        y = cy + 2
        for line in g.wrap("Bold", 18, game["name"], tw)[:3]:
            g.text("Bold", 18, line, tx, y, TEXT)
            y += 24
        g.text("SemiBold", 12, s["full"].upper(), tx, y + 4, alpha(a1, 255))
        y += 30
        facts = [f"{os.path.basename(game['path'])}" + (f" · {G.human_size(game['size'])}" if G else "")]
        if game.get("plays") or game.get("time"):
            facts.append(omni_i18n._("ui_card_game_played").format(count=game.get('plays', 0)) +
                         (f" · {G.human_time(game['time'])}" if G and game.get("time") else ""))
        if game.get("last") and G:
            facts.append(omni_i18n._("ui_card_game_last_played").format(date=G.human_date(game['last'])))
        if game.get("fav"):
            facts.append(omni_i18n._("ui_card_game_favorite"))
        for f in facts:
            for line in g.wrap("Regular", 12, f, tw)[:2]:
                g.text("Regular", 12, line, tx, y, MUTED)
                y += 18
        desc = game.get("desc")
        if desc:
            y += 8
            room = int((my + mh - 70 - y) // 18)
            lines = g.wrap("Regular", 12, " ".join(desc.split()), tw)
            for line in lines[:max(0, room)]:
                g.text("Regular", 12, line, tx, y, TEXT)
                y += 18
        bw, by = (mw - 56) / 2, my + mh - 58
        for k, label in enumerate((omni_i18n._("ui_card_sheet_play"), omni_i18n._("ui_card_sheet_back"))):
            if not sh["play"] and k == 0:
                continue
            bx = mx + 22 + k * (bw + 12) if sh["play"] else mx + 22
            if not sh["play"]:
                bw = mw - 44
            if k == sh["sel"]:
                g.rrect(bx, by, bw, 38, 14, a1, a2)
            else:
                g.rrect(bx, by, bw, 38, 14, ink(22))
            g.text("SemiBold", 13, label, bx + bw / 2, by + 19.5, ON_TEXT if k == sh["sel"] else TEXT, "c", "m")

    # --- teste de ports ---

    def open_picker(self):
        if self.busy_game():
            return
        groups = FAKE_PORTS if FAKE else omni.port_groups()
        res = {} if FAKE else omni.port_results()
        rows = []
        for g in groups:
            rows.append({"head": g["label"], "tag": omni_i18n._("ui_card_test_library_tag"), "tagc": LEVEL["ok"]})
            for p in g["ports"]:
                name = os.path.basename(p)[:-3]
                r = res.get(name)
                right = None
                if r:
                    ok = r[0] == "ok"
                    right = (omni_i18n._("ui_card_test_passed_short" if ok else "ui_card_test_failed_short").format(result=r[1].split(" ")[0]), LEVEL["ok" if ok else "aviso"])
                rows.append({"name": name, "path": p, "right": right})

        def pick(row):
            self.ask(omni_i18n._("tx_test_ask").format(name=row['name']), lambda: self.start_test(row["path"]))
        if not self.show_list(omni_i18n._("ui_choose_port"), "player-play", rows, pick, omni_i18n._("ui_test_port")):
            self.toast = (omni_i18n._("ui_no_ports_installed"), "aviso", self.t + 3)

    def start_test(self, path):
        if FAKE:
            self.toast = (f"Testaria {os.path.basename(os.path.dirname(path)) or path} por 15 s", "ok", self.t + 3)
            return
        res = D.run("test_port", {"path": path})
        if res == "ok":
            self.running = False      # o launch-direct.sh roda o teste e reabre o Omni36OS
        else:
            self.toast = (res, "aviso", self.t + 3.5)

    def show_test_result(self):
        if FAKE:      # OMNI_FAKE_TESTE=falhou|ok mostra um resultado de teste no simulador
            kind = os.environ.get("OMNI_FAKE_TESTE", "")
            if not kind:
                return
            r = {"nome": "TMNTShreddersRevenge", "resultado": kind, "segundos": "2",
                 "relatorio": "/roms/logs/teste de ports/teste_TMNTShreddersRevenge.txt"}
            found = [] if kind == "ok" else [
                {"id": "permissao", "causa": omni_i18n._("tx_fix_perm_c"), "dica": omni_i18n._("tx_fix_perm_t"),
                 "fix": "chmod", "extra": ""}]
            settled = ""
        else:
            r = omni.last_test()
            if not r:
                return
            settled = omni_ports_fix.settle(r["nome"], r["resultado"] == "ok")
            found = [] if r["resultado"] == "ok" or not r["relatorio"] else omni_ports_fix.diagnose(r["relatorio"])
            if found:
                omni_ports_fix.note(r["relatorio"], found)
        buttons, fns = ["OK"], [lambda: None]
        if r["resultado"] == "ok":
            text = omni_i18n._("ui_port_test_description").format(name=r['nome'])
            icon = "check"
        else:
            rel = r["relatorio"].split("/omni36os/", 1)[-1] if r["relatorio"] else ""
            text = omni_i18n._("ui_port_test_closed").format(name=r['nome'], seconds=r['segundos'])
            if found:
                d = found[0]
                text += omni_i18n._("ui_port_test_likely_cause").format(cause=d['causa']) + (f" ({d['extra']})" if d["extra"] else "")
                text += omni_i18n._("ui_port_test_what_to_do").format(tip=d['dica'])
                if d["fix"] and not settled:      # uma tentativa por teste: depois de desfeita, não repete
                    buttons, fns = [omni_i18n._("ui_port_test_fix_button"), omni_i18n._("ui_not_now")], \
                        [lambda: self.fix_and_retest(r, d["fix"]), lambda: None]
            if rel:
                text += omni_i18n._("ui_port_test_report_path").format(path=rel)
            icon = "alert-triangle"
        if settled:
            text = settled + "\n" + text
        self.modal = {"title": omni_i18n._("ui_port_test_title"), "text": text, "icon": icon, "buttons": buttons, "sel": 0, "fns": fns}

    def fix_and_retest(self, r, fix):
        if FAKE:
            self.toast = (omni_i18n._("ui_test_fix_applied"), "ok", self.t + 3)
            return
        def done(script):
            if isinstance(script, Exception) or not script:
                self.toast = (omni_i18n._("ui_test_fix_failed"), "problema", self.t + 3.5)
                return
            self.start_test(script)
        self.worker(lambda: omni_ports_fix.apply(r["relatorio"], fix), done, busy=omni_i18n._("ui_port_fixing"))

    def quit(self):
        self.running = False

    # --- backup ---

    def backup_where(self, module):
        """Pergunta onde salvar: só os lugares disponíveis agora (cartão do sistema sempre; o de jogos e
        o pendrive quando montados). O escolhido vem marcado da próxima vez."""
        opts = ([("Cartão do sistema", "/roms/backup/omni36os", 12.4), ("Pendrive", "/mnt/usbdrive/backup/omni36os", 7.1)]
                if FAKE else omni_backup.places())
        last = None if FAKE else omni_backup.backup_dir()
        rows = [{"name": name, "right": (f"{free:.1f} GB livres", MUTED), "dir": d,
                 "icon": "usb" if "usbdrive" in d else "device-sd-card"} for name, d, free in opts]

        def go(row):
            self.picker = None
            if FAKE:
                self.toast = (f"Teste: salvaria em {row['dir']}", "ok", self.t + 3)
                return
            self.backup_export(module, row["dir"])
        start = next((i for i, r in enumerate(rows) if r["dir"] == last), None)
        self.show_list(omni_i18n._("ui_backup_save_location"), "device-floppy", rows, go, omni_i18n._("ui_backup_save_here"), start)

    def backup_export(self, module, dest=None):
        def done(res):
            if isinstance(res, Exception):
                self.toast = (omni_i18n._("ui_error_prefix").format(error=res), "problema", self.t + 4)
                return
            path, info = res
            if not path:
                self.toast = (info, "aviso", self.t + 3.5)
                return
            self.modal = {"title": omni_i18n._("ui_backup_saved_title"), "icon": "check", "buttons": ["OK"], "sel": 0,
                          "text": omni_i18n._("tx_saved_in").format(info=info, path=path)}
            self.reload_findings()
        self.worker(lambda: omni_backup.export(module, dest=dest), done, busy=omni_i18n._("ui_backup_export_busy"))

    def backup_browse(self, module, path):
        if FAKE:                      # simulador: uma pasta de teste com um backup
            path, entries = path, [{"name": "..", "path": "/roms/backup", "dir": True},
                                   {"name": "omni36os-20261029-120000.tar.gz", "path": path + "/x.tar.gz", "dir": False}]
        else:
            path, entries = omni_backup.browse(path)
        rows = [{"head": path}]
        for e in entries:
            if e["dir"]:
                rows.append({"name": e["name"], "path": e["path"], "dir": True,
                             "icon": "arrow-back-up" if e["name"] == ".." else "folder"})
            else:
                m = {"module": module, "date": "29/10/2026 12:00"} if FAKE else omni_backup.manifest(e["path"]) or {}
                mod = m.get("module")
                ok = mod == module
                right = (m.get("date", "").split(" ")[0] if ok else
                         (omni_backup.MODULES.get(mod, (omni_i18n._("ui_backup_unknown_type"),))[0] if mod else omni_i18n._("ui_backup_unknown_type")),
                         LEVEL["ok" if ok else "info"])
                rows.append({"name": e["name"], "path": e["path"], "dir": False, "ok": ok,
                             "icon": "device-floppy", "right": right})

        def pick(row):
            if row["dir"]:
                self.backup_browse(module, row["path"])
            elif not row["ok"]:
                self.toast = (omni_i18n._("ui_backup_wrong_file").format(module=omni_backup.MODULES[module][0]), "aviso",
                              self.t + 3.5)
            else:
                self.ask(omni_i18n._("tx_import_ask").format(name=row['name']),
                         lambda: self.backup_import(module, row["path"]), danger=True)
        start = next((i for i, r in enumerate(rows) if r.get("ok")), None)   # o backup compatível
        if not self.show_list(f"{omni_i18n._('ui_backup_import_title')} · {path}", "folder", rows, pick,
                              omni_i18n._("ui_hint_open_import"), start):
            self.toast = (omni_i18n._("ui_backup_folder_empty"), "aviso", self.t + 3)

    def backup_import(self, module, path):
        def done(res):
            self.picker = None
            if isinstance(res, Exception):
                self.toast = (omni_i18n._("ui_error_prefix").format(error=res), "problema", self.t + 4)
                return
            text = str(res)
            self.modal = {"title": omni_i18n._("ui_backup_import_title"), "icon": "device-floppy", "buttons": ["OK"], "sel": 0,
                          "text": text}
            if "Reinicie" in text or "Restart" in text:        # snapshot: a versão e os serviços só valem depois de reiniciar
                def reboot():
                    self.goodbye = "reiniciando"
                    self.frame(0)
                    self.g.present()
                    if not FAKE:
                        omni.power({"what": "reboot"})
                self.modal.update(buttons=[omni_i18n._("ui_reboot_now"), omni_i18n._("ui_later")], fns=[reboot, lambda: None])
            self.reload_findings()
        self.worker(lambda: "Teste: nada importado" if FAKE else omni_backup.import_(module, path), done,
                    busy=omni_i18n._("ui_backup_import_busy"))

    # --- atalhos personalizados ---

    def pick_atalho(self):
        combos = D.get("at_combos")
        rows = [{"name": name, "right": (omni_combos.text(combos[k]), MUTED), "icon": icon, "key": k}
                for k, (name, icon, *_x) in omni_combos.ACTIONS.items() if k not in omni_combos.FIXED]
        def go(r):
            self.picker = None
            self.start_capture(r["key"])
        self.show_list(omni_i18n._("ui_card_custom_shortcut"), "keyboard", rows, go, omni_i18n._("ui_shortcut_record"))

    def start_capture(self, key):
        """Grava a tecla que vai com o FN: o jogador aperta uma tecla e o atalho vira FN + ela. No
        console lê o controle direto (o SDL não vê todas as teclas); no simulador, a tecla do teclado."""
        fd = None
        if not FAKE:
            try:
                fd = os.open(PAD_DEV, os.O_RDONLY | os.O_NONBLOCK)
            except OSError:
                self.toast = (omni_i18n._("ui_controller_read_failed"), "problema", self.t + 4)
                return
        self.capture = {"key": key, "fd": fd, "seen": set(), "down": set(), "t0": self.t, "last": self.t}

    def capture_poll(self):
        c = getattr(self, "capture", None)
        if not c:
            return
        if c["fd"] is not None:
            ev = struct.Struct("llHHi")
            try:
                data = os.read(c["fd"], ev.size * 64)
            except BlockingIOError:
                data = b""
            for k in range(0, len(data) - ev.size + 1, ev.size):
                _s, _us, typ, code, val = ev.unpack_from(data, k)
                if typ != 1 or val == 2 or code not in omni_combos.BUTTONS:
                    continue
                if val == 1 and code != omni_combos.FN:
                    c["seen"].add(code)
                    break
        done = bool(c["seen"])
        if done:
            self.finish_capture()
        elif not c["seen"] and self.t - c["t0"] > 8:
            self.end_capture()
            self.toast = (omni_i18n._("ui_shortcut_no_button"), "aviso", self.t + 3)

    def end_capture(self):
        c, self.capture = self.capture, None
        if c and c["fd"] is not None:
            os.close(c["fd"])

    def finish_capture(self):
        c = self.capture
        self.end_capture()
        key, codes = c["key"], [omni_combos.FN, *c["seen"]]
        combos = dict(D.get("at_combos"))
        err = omni_combos.problem(key, codes, combos)
        name = omni_combos.ACTIONS[key][0]
        if err:
            self.modal = {"title": omni_i18n._("ui_shortcut_not_saved"), "icon": "alert-triangle", "buttons": [omni_i18n._("ui_retry"), omni_i18n._("ui_warning_cancel")],
                          "sel": 0, "text": err, "fns": [lambda: self.start_capture(key), lambda: None]}
            return

        def save():
            combos[key] = codes
            D.set("at_combos", combos)
            self.refresh_atalhos(f"{name}: {omni_combos.text(codes)}")
        self.ask(omni_i18n._("tx_use_combo").format(combo=omni_combos.text(codes), name=name), save)

    def reset_combos(self):
        D.set("at_combos", omni_combos.defaults()["combos"])
        self.refresh_atalhos(omni_i18n._("tx_default_btn"))

    def refresh_atalhos(self, msg):
        keep = self.item_sel
        self.items = self.build_items(self.page)
        self.item_sel = min(keep, len(self.items) - 1)
        self.toast = (msg, "ok", self.t + 3.5)

    def draw_capture(self):
        g, c = self.g, self.capture
        g.rrect(0, 0, W, H, 0, (5, 7, 20, 200), feather=0)
        mw, mh = 420, 210
        mx, my = (W - mw) / 2, (H - mh) / 2
        g.glow(mx, my, mw, mh, 22, alpha(self.accent[0], 60), 26)
        g.rrect(mx, my, mw, mh, 22, MODAL_A, MODAL_B)
        g.stroke(mx, my, mw, mh, 22, ink(25))
        g.icon("keyboard", mx + 24, my + 22, 24, alpha(self.accent[0], 255))
        g.text("Bold", 17, omni_i18n._("tx_new_hotkey").format(name=omni_combos.ACTIONS[c['key']][0]), mx + 58, my + 22, TEXT)
        g.text("Medium", 13, omni_i18n._("ui_card_shortcut_capture_prompt"), mx + 24, my + 62, MUTED)
        now = "FN + " + (omni_combos.text(c["seen"]) if c["seen"] else "...")
        g.text("Bold", 26, now, W / 2, my + 118, TEXT, "c", "m")
        left = max(0, 8 - (self.t - c["t0"])) if not c["seen"] else None
        g.text("Medium", 12, omni_i18n._("tx_no_key").format(s=left) if left is not None else "",
               W / 2, my + mh - 30, FAINT, "c")

    def read(self, title, icon, text, links=(), on_close=None):
        """links: [(palavra, função)] — a palavra vira link; ↑↓ levam o foco pelos links na tela e A abre.
        on_close: chamada quando o leitor fecha (ex.: voltar à janela que o abriu)."""
        self.reader = {"title": title, "icon": icon, "text": text, "scroll": 0.0, "top": 0, "links": links, "focus": None,
                       "on_close": on_close}

    def open_credits(self):
        self.read(omni_i18n._("ui_credits_title"), "users", omni_help.creditos_text(),
                  links=[("mpjsilva", self.qr_mpjsilva), ("h1ghland3r", self.qr_h1ghland3r)])

    def qr(self, title, text, image, url):
        self.reader = None
        self.modal = {"title": title, "icon": "users", "sel": 0, "buttons": ["OK"], "text": text,
                      "image": image, "url": url, "fns": [self.open_credits], "on_back": self.open_credits}

    def qr_mpjsilva(self):
        self.qr(omni_i18n._("tx_qr1_t"), omni_i18n._("tx_qr1"),
                "qr-mpjsilva", "github.com/mpjsilva")

    def qr_h1ghland3r(self):
        self.qr("h1ghland3r", omni_i18n._("tx_qr2"),
                "qr-h1ghland3r", "beacons.ai/h1ghland3r")

    def ask(self, text, fn, danger=False, cancel=False):
        if danger:
            return self.warn(omni_i18n._("tx_attention"), text, fn, secs=5)
        self.modal = {"title": omni_i18n._("ui_hint_confirm"), "text": text, "icon": "alert-triangle" if danger else "info-circle",
                      "buttons": [omni_i18n._("tx_yes_do"), omni_i18n._("ui_hint_cancel")], "sel": 1 if danger or cancel else 0, "fn": fn}

    # --- aviso com contagem (estilo "opções perigosas" da Xiaomi) ---

    def ask_overclock(self):
        """A trava de verdade: sem passar por aqui (aviso + 5 toques em A), os limites acima de 1296 MHz
        e 520 MHz nem aparecem nos seletores e são recusados. Se o DTB ainda não tem as frequências,
        acrescenta (o resto vale depois de reiniciar)."""
        def unlock():
            res = omni_sistema.dtb_overclock()
            if omni_i18n.is_failure(res):
                return res
            omni.unlock_oc()
            return (omni_i18n._("tx_oc_unlocked") if res.startswith(("O overclock já", "Overclock is already"))
                    else res + " " + omni_i18n._("tx_oc_restart"))
        run = ((lambda: self.worker(unlock, self._sys_done, busy=omni_i18n._("ui_unlock_overclock_busy"))) if not FAKE else
               (lambda: setattr(self, "toast", ("Teste: passou", "ok", self.t + 3))))

        def go():                     # console com trava por senha: a senha libera o overclock
            if not ((os.environ.get("OMNI_TRAVA") == "1") if FAKE else omni_sistema.lock_on()):
                return run()

            def check(pw):
                ok = (pw == os.environ.get("OMNI_TRAVA_SENHA", "1234")) if FAKE else omni_sistema.lock_check(pw)
                if ok:
                    run()
                else:
                    self.toast = (omni_i18n._("tx_oc_wrong"), "problema", self.t + 3.5)
            self.keyboard(omni_i18n._("tx_oc_pw"), check, secret=True)
        self.warn(omni_i18n._("ui_card_option_unlock_oc"), omni_i18n._("tx_oc_text"), go, 10, True,
                  key=omni_i18n._("ui_card_option_unlock_oc"), risk=omni_i18n._("tx_oc_risk"),
                  undo=BOOT_UNDO + " " + omni_i18n._("ui_danger_dtb_backup_undo"))

    def lock_oc(self):
        self._sys_done("Teste: bloqueado" if FAKE else omni.lock_oc())

    def warn(self, title, text, fn, secs=10, hold=False, key=None, risk="", undo="", back=None):
        """Continuar só acende depois de `secs` s; Cancelar começa escolhido. Com `hold`, ainda é
        preciso apertar A 5 vezes. Quem já passou pelo aviso de `key` nesta sessão não espera de novo."""
        seen = getattr(self, "warned", set())
        self.warned = seen
        if key and key in seen:
            secs, hold = 0, False
        self.danger = {"title": title, "text": text, "risk": risk, "undo": undo, "fn": fn, "back": back,
                       "secs": secs, "hold": hold, "t0": time.monotonic(), "sel": 1, "taps": 0, "tap_t": 0.0, "key": key,
                       "nudge": -9}

    def danger_left(self):
        d = self.danger
        return max(0.0, d["secs"] - (time.monotonic() - d["t0"]))

    def danger_input(self, cmd):
        d = self.danger
        if cmd in ("left", "right"):
            d["sel"] = 1 - d["sel"]
        elif cmd == "back" or (cmd == "ok" and d["sel"] == 1):
            self.danger = None
            if d["back"]:
                d["back"]()
        elif cmd == "ok":
            if self.danger_left() > 0:
                d["nudge"] = time.monotonic()          # ainda não: o botão treme
            elif d["hold"]:
                now = time.monotonic()                 # 5 toques em A; parar por 2 s zera a contagem
                d["taps"] = (d["taps"] if now - d["tap_t"] < 2 else 0) + 1
                d["tap_t"] = now
                if d["taps"] >= 5:
                    self.danger_go()
            else:
                self.danger_go()

    def danger_go(self):
        d = self.danger
        self.danger = None
        if d["key"]:
            self.warned.add(d["key"])
        d["fn"]()

    def draw_danger(self, dt):
        g, d = self.g, self.danger
        red, red2 = hexc("ef4444"), hexc("b91c1c")
        g.rrect(0, 0, W, H, 0, (40, 4, 10, 215), feather=0)
        mx, my, mw, mh = 34, 34, W - 68, H - 68
        g.glow(mx, my, mw, mh, 24, alpha(red, 70), 26)
        g.rrect(mx, my, mw, mh, 24, MODAL_A, MODAL_B)
        g.stroke(mx, my, mw, mh, 24, alpha(red, 120), 1.5)
        g.circle(mx + 52, my + 52, 26, alpha(red, 60))
        g.icon("alert-triangle", mx + 38, my + 38, 28, red)
        g.text("Bold", 20, d["title"], mx + 92, my + 30, TEXT)
        g.text("SemiBold", 11, omni_i18n._("ui_warning_read_before_continue"), mx + 92, my + 58, red)
        y = my + 96
        for label, body, col in (("", d["text"], TEXT), (omni_i18n._("ui_warning_risk_label"), d["risk"], TEXT),
                                 (omni_i18n._("ui_warning_undo_label"), d["undo"], TEXT)):
            if not body:
                continue
            if label:
                g.text("SemiBold", 11, label.upper(), mx + 28, y, FAINT)
                y += 18
            for para in body.split("\n"):
                for line in g.wrap("Regular", 13, para, mw - 56):
                    if y < my + mh - 110:
                        g.text("Regular", 13, line, mx + 28, y, col)
                    y += 19
            y += 8
        left = self.danger_left()
        if d["taps"] and time.monotonic() - d["tap_t"] >= 2:
            d["taps"] = 0                               # demorou: recomeça do zero
        bw, by = (mw - 68) / 2, my + mh - 66
        shake = 6 * math.sin((time.monotonic() - d["nudge"]) * 40) if time.monotonic() - d["nudge"] < 0.35 else 0
        bx = mx + 28 + shake
        ready = left <= 0
        on = d["sel"] == 0
        if ready:
            g.rrect(bx, by, bw, 42, 15, red if on else alpha(red, 90), red2 if on else alpha(red2, 90))
        else:
            g.rrect(bx, by, bw, 42, 15, ink(14))
            if on:
                g.stroke(bx, by, bw, 42, 15, ink(60), 1.5)
        if not ready:
            label = omni_i18n._("ui_warning_continue_count").format(count=int(left) + 1)
            # arco que fecha junto com a contagem
            cx_, cy_ = bx + 26, by + 21
            g.arc(cx_, cy_, 11, 3, -90, -90 + 360 * (1 - left / max(1, d["secs"])), alpha(red, 230))
            g.text("SemiBold", 14, label, bx + bw / 2 + 10, by + 21.5, FAINT, "c", "m")
        elif d["hold"]:
            k = d["taps"] / 5
            if k:
                g.rrect(bx, by, bw * k, 42, 15, (255, 255, 255, 60))
            g.text("SemiBold", 14, omni_i18n._("ui_warning_press_a_five") if not k else omni_i18n._("ui_warning_press_a_more").format(count=5 - d['taps']),
                   bx + bw / 2, by + 21.5, ON_TEXT, "c", "m")
        else:
            g.text("SemiBold", 14, omni_i18n._("ui_warning_continue"), bx + bw / 2, by + 21.5, ON_TEXT, "c", "m")
        cb = mx + 40 + bw
        if d["sel"] == 1:
            g.rrect(cb, by, bw, 42, 15, self.accent[0], self.accent[1])
        else:
            g.rrect(cb, by, bw, 42, 15, ink(22))
        g.text("SemiBold", 14, omni_i18n._("ui_warning_cancel"), cb + bw / 2, by + 21.5, ON_TEXT if d["sel"] == 1 else TEXT, "c", "m")

    # --- entrada ---

    def handle(self, cmd):
        if cmd in ("vleft", "vright"):   # analógico para os lados: fora de uma barra/escolha, navega
            over = (getattr(self, "kbd", None) or getattr(self, "danger", None) or self.reader or self.modal
                    or getattr(self, "levels", None) or getattr(self, "viewer", None)
                    or getattr(self, "sheet", None) or self.picker)
            it = self.items[self.item_sel] if self.page and self.items and not over else None
            if self.page and not over:
                if not isinstance(it, (Slider, Choice)):
                    return                # numa página o analógico só ajusta valores
            else:
                cmd = cmd[1:]
        self.last_input = time.monotonic()
        if self.busy or self.loading:
            return
        if getattr(self, "capture", None):        # gravando um atalho: os botões são do atalho
            if FAKE and cmd in SIM_BUTTONS and cmd != "fn":
                self.capture["seen"].add(SIM_BUTTONS[cmd])
            return
        if getattr(self, "kbd", None) and not self.modal:
            self.kbd_input(cmd)
            return
        if getattr(self, "danger", None):
            self.danger_input(cmd)
            return
        if self.reader:
            r = self.reader
            step = {"up": -1, "down": 1, "left": -8, "right": 8, "l1": -8, "r1": 8}.get(cmd)
            vis = r.get("vis") or []
            if cmd in ("up", "down") and r.get("focus") in vis and \
                    0 <= vis.index(r["focus"]) + step < len(vis):   # próximo link na tela: o foco anda
                r["focus"] = vis[vis.index(r["focus"]) + step]
            elif step:
                r["top"] = max(0, min(r.get("max", 0), r["top"] + step))
            elif cmd == "ok" and r.get("focus") in vis:
                r["links"][r["focus"]][1]()
            elif cmd in ("back", "ok"):
                self.reader = None
                if r.get("on_close"):
                    r["on_close"]()
            return
        if self.modal:
            m = self.modal
            if cmd in ("left", "right") and len(m["buttons"]) > 1:
                m["sel"] = (m["sel"] + (1 if cmd == "right" else -1)) % len(m["buttons"])
            elif cmd == "ok":
                lk = m.get("lock")
                if lk and m["sel"] == lk[0] and self.t < lk[1]:
                    return                    # trava: o botão só vale depois da contagem
                self.modal = None
                if m.get("fns"):
                    m["fns"][m["sel"]]()
                elif m["sel"] == 0 and m.get("fn"):
                    m["fn"]()
            elif cmd == "back":
                self.modal = None
                if m.get("on_back"):
                    m["on_back"]()
            return
        if getattr(self, "video", None):
            self.video_input(cmd)
            return
        if getattr(self, "note", None):
            self.note_input(cmd)
            return
        if getattr(self, "music", None):
            self.music_input(cmd)
            return
        if getattr(self, "viewer", None):
            self.viewer_input(cmd)
            return
        if getattr(self, "levels", None):
            self.levels_input(cmd)
            return
        if getattr(self, "sheet", None):
            self.sheet_input(cmd)
            return
        if self.picker:
            self.picker_input(cmd)
            return
        if self.page is None and self.view == "lib":
            self.library_input(cmd)
            return
        if cmd in ("start", "select"):
            return                        # sem atalhos: Ports é o primeiro card; Energia é o botão de power
        if self.page is None and cmd == "back":
            return                        # tela inicial: B não sai do sistema
        if self.page is None:
            cols, n = COLS, len(CARDS)
            r, c = divmod(self.sel, cols)
            rows = (n + cols - 1) // cols
            in_row = min(cols, n - r * cols)      # a última linha pode ter menos cards
            if cmd == "left":
                self.sel = r * cols + (c - 1) % in_row
            elif cmd == "right":
                self.sel = r * cols + (c + 1) % in_row
            elif cmd in ("up", "down"):
                r = (r + (1 if cmd == "down" else -1)) % rows
                self.sel = min(r * cols + c, n - 1)
            elif cmd == "ok" and CARDS[self.sel][0] == "ports":
                if not FAKE:              # port novo no cartão: confere as pastas (só data, rápido)
                    self.games_idx = omni_games.index()
                self.view = "lib"
                self.select_last_played()
            elif cmd == "ok":
                self.open_page(CARDS[self.sel][0])
            elif cmd == "back":
                self.running = False
            return
        it = self.items[self.item_sel] if self.items else None
        if cmd in ("l1", "r1"):           # rola o diagnóstico (painel da esquerda)
            self.find_top = max(0, min(self.find_max, self.find_top + (1 if cmd == "r1" else -1)))
            return
        if cmd == "up":
            self.item_sel = (self.item_sel - 1) % len(self.items)
        elif cmd == "down":
            self.item_sel = (self.item_sel + 1) % len(self.items)
        elif cmd == "back":
            if self.page in PARENT:       # subpágina: volta ao card de origem
                sub = self.page
                self.open_page(PARENT[sub])
                self.item_sel = next((i for i, x in enumerate(self.items)
                                      if getattr(x, "sub", None) == sub), 0)
            else:
                self.page = None
                self.flush_source()
        elif cmd in ("left", "right") and self.page in TWO_COLS:   # direcional: troca de coluna
            half = (len(self.items) + 1) // 2
            k = self.item_sel + (half if self.item_sel < half else -half)
            self.item_sel = max(0, min(len(self.items) - 1, k))
        elif isinstance(it, Slider) and cmd in ("vleft", "vright"):
            it.value = max(it.lo, min(100, it.value + (it.step if cmd == "vright" else -it.step)))
            D.set(it.key, it.value)
            if it.key == "volume":            # a pílula do topo mostra o volume novo na hora
                self.vol = it.value
        elif isinstance(it, Choice) and cmd in ("left", "right", "vleft", "vright", "ok"):
            it.index = (it.index + (-1 if cmd in ("left", "vleft") else 1)) % len(it.options)
            res = D.set(it.key, it.options[it.index])
            if isinstance(res, str) and res.startswith(("Está quente", "Frequência", "Este sistema", "Ligue a rede", "It is hot", "Frequency", "This system", "Enable USB")):
                cur = D.get(it.key)     # recusado: volta ao valor que está valendo
                it.index = it.options.index(cur) if cur in it.options else 0
                self.toast = (res, "aviso", self.t + 4)
            elif it.key in ("cpu_max", "gpu_max") and "overclock" in str(res):
                self.toast = (str(res) + omni_i18n._("tx_watch_temp"), "aviso", self.t + 3.5)
            if it.key == "gov":
                self.status = D.status()
            if it.key == "tema":
                self.g.flush()
            if it.key == "fonte":         # a busca espera o jogador sair da página: trocar várias
                self.source_dirty = res   # vezes seguidas não relê os cartões a cada toque
            if it.key == "inverter":          # o próprio Omni36OS passa a usar a troca na hora
                self.swap = self.swap_xy = it.options[it.index] == "ligado"
            if (it.key == "remoto" or it.key.startswith("at_")) and isinstance(res, str) and res != "ok":
                self.toast = (res, "ok", self.t + 4)
        elif isinstance(it, Action) and cmd == "ok":
            if it.confirm:
                self.ask(it.confirm, it.fn, it.danger, it.cancel)
            else:
                it.fn()

    def poll(self):
        ev = (C.c_uint8 * 64)()
        now = time.monotonic()
        while gfx.SDL_PollEvent(ev):
            typ = int.from_bytes(bytes(ev[0:4]), "little")
            if typ == 0x100:  # SDL_QUIT
                self.running = False
            elif typ == 0x653:  # controle conectado
                gfx.SDL_GameControllerOpen(int.from_bytes(bytes(ev[8:12]), "little", signed=True))
            elif typ in (0x651, 0x652):   # SDL_CONTROLLERBUTTONDOWN / UP
                if getattr(self, "pad", None):     # teste do controle: todo botão vai para ele
                    self.last_input = now
                    self.pad_event("btn", ev[12], typ == 0x651, now)
                    continue
                self.button(ev[12], typ == 0x651, now)
            elif typ == 0x650:          # SDL_CONTROLLERAXISMOTION
                axis = ev[12]
                val = int.from_bytes(bytes(ev[16:18]), "little", signed=True)
                if getattr(self, "pad", None):
                    self.pad_event("axis", axis, val, now)
                    continue
                if axis in (0, 1):   # eixo X do analógico esquerdo ajusta valores; o direcional navega
                    neg, pos = ("vleft", "vright") if axis == 0 else ("up", "down")
                    for d, on in ((neg, val < -20000), (pos, val > 20000)):
                        self.direction(d, on, now)
            elif typ == 0x401 and FAKE:   # mouse no simulador: esquerdo = A, direito = B
                btn = ev[16]
                mx, my = (int.from_bytes(bytes(ev[o:o + 4]), "little", signed=True) for o in (20, 24))
                if btn == 1 and not self.mouse_pick(mx, my):
                    self.handle("ok")
                elif btn == 3:
                    self.handle("back")
            elif typ == 0x403 and FAKE:   # roda do mouse no simulador: cima/baixo
                wy = int.from_bytes(bytes(ev[20:24]), "little", signed=True)
                if wy:
                    self.handle("up" if wy > 0 else "down")
            elif typ in (0x300, 0x301):  # teclado (para testar no PC)
                sym = int.from_bytes(bytes(ev[20:24]), "little")
                down, rep = typ == 0x300, ev[13]
                if FAKE and down and sym == 0x40000045:   # simulador: F12 = FN + Y (captura de tela)
                    self.want_shot = True
                    continue
                if FAKE and down and sym in (0x40000057, 0x40000056):   # simulador: KP+ / KP- = botões de volume
                    v = D.get("volume")                                   # (no console quem muda é o ogage)
                    D.set("volume", max(0, min(100, v + (10 if sym == 0x40000057 else -10))))
                    self.vol_at = self.t + 0.15
                    for it in (self.items or []) + (self.levels["items"] if getattr(self, "levels", None) else []):
                        if isinstance(it, Slider) and it.key == "volume":
                            it.value = D.get("volume")
                    continue
                if sym in (0x4000007F, 0x40000080, 0x40000081) and not down:
                    self.vol_at = self.t + 0.15   # VOLUP/VOLDOWN/MUTE: o ogage muda o som; relê o volume
                keys = {0x4000004F: "right", 0x40000050: "left", 0x40000051: "down", 0x40000052: "up",
                        0x4000005F: "vleft", 0x40000061: "vright"}   # KP7/KP9: analógico esquerdo
                if sym in keys:
                    if not rep:
                        self.direction(keys[sym], down, now)
                elif down and not rep:
                    # teclado numérico (Num Lock ligado): 2=A, 1=B, 5=X, 4=Y, 6=L1, 3=R1;
                    # Enter=START, Shift direito=SELECT
                    self.handle({0x4000005A: "ok", 0x40000059: "back", 0x4000005D: "x", 0x4000005C: "y",
                                 0x4000005E: "l1", 0x4000005B: "r1", 13: "start", 0x40000058: "start",
                                 0x400000E5: "select"}.get(sym, ""))
                    if FAKE and sym == 0x40000060:   # simulador: KP8 = FN (só na gravação de atalho)
                        self.handle("fn")
                    if FAKE and sym == 0x40000062:   # simulador: KP0 = botão de power
                        self.want_power = True
        for d, nxt in list(self.held.items()):
            if now >= nxt:
                self.handle(d)
                self.held[d] = now + 0.09

    def direction(self, d, on, now):
        if getattr(self, "ssh_off", False):
            return
        if on and d not in self.held:
            self.handle(d)
            self.held[d] = now + 0.35
        elif not on:
            self.held.pop(d, None)

    def button(self, b, down, now):
        if getattr(self, "ssh_off", False):
            self.ssh_button(b, down)
            return
        # SDL: 0 A (direita no R36S), 1 B (baixo), 4 back, 6 start, 9 L1, 10 R1, 11-14 direcional
        dpad = {11: "up", 12: "down", 13: "left", 14: "right"}
        if b in dpad:
            self.direction(dpad[b], down, now)
            return
        if b in (4, 6):
            if down:
                self.combo.add(b)
                self.combo_used = getattr(self, "combo_used", False) or {4, 6} <= self.combo
            else:
                if not getattr(self, "combo_used", False) and self.combo == {b}:
                    self.handle("start" if b == 6 else "select")
                self.combo.discard(b)
                if not self.combo:
                    self.combo_used = False
            return
        ok_b, back_b = (1, 0) if self.swap else (0, 1)
        if b == ok_b:
            self.ok_held = down
        if not down:
            return
        if b in (2, 3):
            self.handle("x" if (b == 2) != self.swap_xy else "y")
        elif b in (9, 10):
            self.handle("l1" if b == 9 else "r1")
        elif b == ok_b:
            self.handle("ok")
        elif b == back_b:
            self.handle("back")

    # --- desenho ---

    def draw_bg(self, dt):
        g = self.g
        g.vgradient(BG_TOP, BG_BOT)
        a1, a2 = self.accent
        t = self.t
        g.blob(120 + math.sin(t * 0.35) * 60, 90 + math.cos(t * 0.27) * 40, 300, alpha(a1, 46))
        g.blob(540 + math.cos(t * 0.3) * 50, 400 + math.sin(t * 0.33) * 40, 320, alpha(a2, 52))
        g.blob(360 + math.sin(t * 0.2) * 120, 240, 220, (90, 70, 200, 22))

    def draw_header(self):
        g = self.g
        # marca
        g.image("logo-64", 22, 18, 30, smooth=True)
        g.text("Bold", 20, "Omni36OS", 62, 18, TEXT)
        self.draw_status()

    def draw_status(self):
        """Pílula de estado (Wi-Fi, volume, bateria, temperatura e hora), no canto de cima."""
        g = self.g
        if self.t - self.status_at > 5:   # relida a cada 5 s em qualquer tela que mostre a pílula
            old = self.status
            self.status, self.status_at = D.status(), self.t
            if (old.get("wifi"), old.get("conectado")) != (self.status.get("wifi"), self.status.get("conectado")):
                self.recheck("rede")      # o Wi-Fi conectou (ou caiu) depois da verificação: sem alerta fantasma
        s = self.status
        hora = time.strftime("%H:%M")
        bat = f"{s['bat']}%"
        temp = f"{s['temp']}°"
        if self.vol_at is not None and self.t >= self.vol_at:   # sem leitura periódica: só no início
            self.vol_at = None                                  # e logo depois dos botões de volume
            v = D.get("volume")
            self.vol = v if isinstance(v, int) else None
        vol = self.vol
        vtxt = f"{vol}%" if vol is not None else ""
        w = (24 + g.measure("SemiBold", 13, vtxt)[0] + 12 if vtxt else 0) + 46 + g.measure("SemiBold", 13, bat)[0] + 36 + g.measure("SemiBold", 13, temp)[0] + 22 + \
            g.measure("SemiBold", 13, hora)[0] + 30
        ancora = s.get("ancoragem") or getattr(self, "fake_tether", False)
        if ancora:
            w += 26
        x = W - 22 - w
        g.rrect(x, 16, w, 34, 17, GLASS_HI)
        cx = x + 14
        if not s["wifi"]:                 # sem adaptador (ou rádio desligado): riscado
            wico, wc = "wifi-off", FAINT
        elif not s["conectado"]:          # adaptador ligado, sem rede: o ícone apagado
            wico, wc = "wifi", FAINT
        else:                             # conectado: as ondas mostram a força do sinal
            sig = s.get("sinal", 100)
            wico, wc = ("wifi-1" if sig < 35 else "wifi-2" if sig < 65 else "wifi"), TEXT
        g.icon(wico, cx, 24, 18, wc)
        cx += 26
        if ancora:                        # internet pela ancoragem USB do celular
            g.icon("anchor", cx, 24, 18, TEXT)
            cx += 26
        if vtxt:                                  # volume do som
            vc = TEXT if vol else FAINT
            g.icon("volume", cx, 24, 18, vc)
            cx += 24 + g.text("SemiBold", 13, vtxt, cx + 22, 33, vc, "l", "m") + 12
        batc = LEVEL["problema"] if s["bat"] < 20 and not s["carregando"] else TEXT
        g.icon("battery-charging" if s["carregando"] else "battery-2", cx, 24, 18, batc)
        cx += 22 + g.text("SemiBold", 13, bat, cx + 22, 33, batc, "l", "m") + 10
        tc = LEVEL["problema"] if s["temp"] > 75 else TEXT
        g.icon("temperature", cx, 24, 18, tc)
        cx += 20 + g.text("SemiBold", 13, temp, cx + 20, 33, tc, "l", "m") + 12
        g.text("SemiBold", 13, hora, cx, 33, TEXT, "l", "m")

    def btn_glyph(self, x, y, letter, c):
        g = self.g
        g.circle(x + 10, y + 10, 10, c)
        g.text("Bold", 11, letter, x + 10, y + 10.5, BG_TOP, "c", "m")

    def draw_footer(self, hints):
        hints = self.localize_hints(hints)
        g = self.g
        x = 22
        for letter, label, c in hints:
            if letter in ("A", "B"):
                self.btn_glyph(x, H - 32, letter, c)
                w = 26
            elif letter == "LR":
                g.rrect(x, H - 32, 40, 20, 10, ink(40))
                g.chevron(x + 12, H - 22, 7, TEXT, left=True)
                g.chevron(x + 28, H - 22, 7, TEXT)
                w = 46
            else:
                pw = g.measure("Bold", 10, letter)[0] + 16
                g.rrect(x, H - 32, pw, 20, 10, ink(40))
                g.text("Bold", 10, letter, x + pw / 2, H - 21.5, TEXT, "c", "m")
                w = pw + 6
            x += w + g.text("Medium", 12, label, x + w, H - 21.5, MUTED, "l", "m") + 18

    def card_subtitle(self, cid):
        return {
            "checkup": self._home_summary(),
            "rede": omni_i18n._("home_network_subtitle"),
            "controles": omni_i18n._("home_controls_subtitle"),
            "geral": omni_i18n._("home_general_subtitle"),
            "sobre": omni_i18n._("home_about_subtitle"),
            "tela": omni_i18n._("home_display_subtitle"),
            "desempenho": omni_i18n._("home_performance_subtitle"),
            "cartoes": omni_i18n._("home_storage_subtitle"),
            "ferramentas": omni_i18n._("home_tools_subtitle"),
            "ports": omni_i18n._("home_ports_subtitle"),
            "apps": omni_i18n._("home_apps_subtitle"),
            "testar": omni_i18n._("home_ports_installed").format(count=self.port_count) if getattr(self, "port_count", 0) else omni_i18n._("home_test_duration"),
        }[cid]

    def _home_summary(self):
        hc = self.home_check
        if not hc:
            return omni_i18n._("home_analyzing")
        n = sum(1 for l, _ in hc["achados"] if l in ("aviso", "problema"))
        return omni_i18n._("home_all_good") if n == 0 else omni_i18n._("home_attention_count").format(count=n)

    def mouse_pick(self, mx, my):
        """Simulador: clique num cartão/item que não está em foco só o seleciona."""
        if self.page is not None:
            hits, cur = getattr(self, "hits_page", []), self.item_sel
        elif self.view == "menu":
            hits, cur = getattr(self, "hits_home", []), self.sel
        else:
            return False
        for k, x, y, w, h in hits:
            if x <= mx < x + w and y <= my < y + h:
                if k == cur:
                    return False
                if self.page is not None:
                    self.item_sel = k
                else:
                    self.sel = k
                return True
        return False

    def draw_home(self, dt, fade):
        if self.view == "lib":
            return self.draw_library(dt, fade)
        g = self.g
        hour = time.localtime().tm_hour
        hello = omni_i18n._("greeting_morning") if 5 <= hour < 12 else omni_i18n._("greeting_afternoon") if 12 <= hour < 18 else omni_i18n._("greeting_evening")
        hello += f", {self.player}!" if self.player else "!"
        g.text("Bold", 26, hello, 22, 66, alpha(TEXT, 255 * fade))
        hc = self.home_check
        if hc:
            lvl = hc["nivel"]
            n = len(self.alerts)
            if n == 0:
                lvl, msg = "ok", omni_i18n._("ui_hud_good_health")
            else:
                lvl = "problema" if any(l == "problema" for l, _ in self.alerts.values()) else "aviso"
                total = sum(k for _, k in self.alerts.values())   # a soma dos pontos dos cards
                msg = omni_i18n._("home_alert_count").format(count=total)
            g.circle(29, 115, 5, alpha(LEVEL[lvl], 255 * fade))
            g.text("Regular", 13, msg, 42, 105, alpha(MUTED, 255 * fade))
        else:
            g.arc(29, 115, 6, 2.5, self.t * 360, self.t * 360 + 270, alpha(MUTED, 255 * fade))
            g.text("Regular", 13, omni_i18n._("home_analyzing_device"), 42, 105, alpha(MUTED, 255 * fade))

        rows = (len(CARDS) + COLS - 1) // COLS
        cw, x0, y0 = 192, 22, 136
        ch, gap = (94, 10) if rows <= 3 else (68, 8)
        col, row = self.sel % COLS, self.sel // COLS
        tx, ty_ = x0 + col * (cw + gap), y0 + row * (ch + gap)
        if self.deliver is None:      # primeira vez na tela: o destaque nasce no card escolhido
            self.deliver, self.sel_x, self.sel_y = self.t, tx, ty_
        self.sel_x = approach(self.sel_x, tx, dt, 18)
        self.sel_y = approach(self.sel_y, ty_, dt, 18)
        # entrega: o destaque cresce do centro do card com um leve passo além (0,7 s)
        dk = min(1.0, (self.t - self.deliver) / 0.7)
        grow = 1 + 2.70158 * (dk - 1) ** 3 + 1.70158 * (dk - 1) ** 2      # ease-out-back
        pos = lambda i: (x0 + (i % COLS) * (cw + gap), y0 + (i // COLS) * (ch + gap))
        self.hits_home = [(i, *pos(i), cw, ch) for i in range(len(CARDS))]
        for i in range(len(CARDS)):
            x, y = pos(i)
            g.rrect(x, y, cw, ch, 18, alpha(GLASS, 14 * fade))
            g.stroke(x, y, cw, ch, 18, ink(18 * fade))
        # o destaque desliza entre os cartões
        sx, sy = self.sel_x, self.sel_y
        pulse = 0.5 + 0.5 * math.sin(self.t * 3)
        a1, a2 = self.accent
        if dk < 1:
            hw, hh = (cw + 4) * max(0.05, grow), (ch + 4) * max(0.05, grow)
            hx, hy = sx - 2 + (cw + 4 - hw) / 2, sy - 3 + (ch + 4 - hh) / 2
            g.glow(hx, hy, hw, hh, 20, alpha(a1, 110 * dk), 20)
            g.rrect(hx, hy, hw, hh, min(20, hh / 2), alpha(a1, 235 * min(1, dk * 2)), alpha(a2, 235 * min(1, dk * 2)))
        else:
            g.sprite(("hl-glow", a1), cw + 4, ch + 4, 20,
                     lambda ox, oy: g.glow(ox, oy, cw + 4, ch + 4, 20, alpha(a1, 110), 20),
                     sx - 2, sy - 3, (0.64 + 0.36 * pulse) * 255 * fade)
            g.sprite(("hl", a1, a2), cw + 4, ch + 4, 1, lambda ox, oy: (
                     g.rrect(ox, oy, cw + 4, ch + 4, 20, alpha(a1, 235), alpha(a2, 235)),
                     g.rrect(ox, oy, cw + 4, (ch + 4) * 0.5, 20, (255, 255, 255, 30), (255, 255, 255, 0))),
                     sx - 2, sy - 3, 255 * fade)
        for i, (cid, title, ic, c1, c2) in enumerate(CARDS):
            x, y = pos(i)
            on = i == self.sel
            lift = -3 if on else 0
            bx, by = x + 14, y + (ch - 46) / 2 + lift
            if on:
                g.rrect(bx, by, 46, 46, 14, (255, 255, 255, 60 * fade))
            else:
                g.rrect(bx, by, 46, 46, 14, alpha(hexc(c1), 255 * fade), alpha(hexc(c2), 255 * fade))
            g.icon(ic, bx + 10, by + 10, 26, alpha(ON_TEXT, 255 * fade))   # sempre sobre cor
            tw = cw - 72 - 10
            size = next((sz for sz in (15, 14, 13, 12) if g.measure("SemiBold", sz, title)[0] <= tw), 12)
            sub = g.wrap("Regular", 11, self.card_subtitle(cid), cw - 82)[:2]
            ty = y + ch / 2 - (size + 4 + 15 * len(sub)) / 2 + lift
            g.text("SemiBold", size, title, x + 72, ty, alpha(ON_TEXT if on else TEXT, 255 * fade))
            if cid in self.alerts:
                lvl, n = self.alerts[cid]
                bc = LEVEL[lvl]
                px_, py_ = bx + 44, by + 2           # no canto do ícone: o texto usa a largura toda
                ring = 0.5 + 0.5 * math.sin(self.t * 4 + i)
                g.sprite(("ring", lvl), 26, 26, 1, lambda ox, oy, bc=bc: g.circle(ox + 13, oy + 13, 13, alpha(bc, 90)),
                         px_ - 13, py_ - 13, 255 * ring * fade)
                g.circle(px_, py_, 10, alpha(bc, 255 * fade))
                g.text("Bold", 11, str(n), px_, py_ + 0.5, alpha(hexc("10142a"), 255 * fade), "c", "m")
            for k, ln in enumerate(sub):
                g.text("Regular", 11, ln, x + 72, ty + size + 6 + 15 * k,
                       alpha(ON_TEXT if on else MUTED, (230 if on else 255) * fade))
        self.draw_footer([("A", omni_i18n._("ui_hint_open"), TEXT), ("POWER", omni_i18n._("ui_hint_power"), MUTED)])

    def page_alerts(self, cid):
        """[(nível, texto)] dos avisos e problemas da página e das subpáginas dela (com o nome da
        subpágina na frente): é o que faz o ponto do card na tela inicial."""
        out = []
        for c in [cid] + [k for k, p in PARENT.items() if p == cid]:
            r = self.results.get(c) or {}
            pre = "" if c == cid else SUBPAGES[c][0] + ": "
            out += [(lv, pre + t) for lv, t in r.get("achados", []) if lv in ("aviso", "problema")]
        return sorted(out, key=lambda x: x[0] != "problema")

    def draw_page(self, dt, fade):
        g = self.g
        cid, title, ic, c1, c2 = card_info(self.page)
        off = 0
        a = 255 * fade
        # título
        g.rrect(22 + off, 66, 44, 44, 14, alpha(hexc(c1), a), alpha(hexc(c2), a))
        g.icon(ic, 32 + off, 76, 24, alpha(ON_TEXT, a))
        g.text("Bold", 22, title, 78 + off, 64, alpha(TEXT, a))
        f = self.findings
        if f:
            lvl = f["nivel"]
            msg = {"ok": omni_i18n._("ui_hud_all_good"), "aviso": omni_i18n._("ui_hud_warnings"),
                   "problema": omni_i18n._("ui_hud_needs_attention")}[lvl]
            if cid in ("geral", "sobre"):
                lvl, msg = "info", f"Omni36OS {omni_version()}"
            alerts = self.page_alerts(cid) if cid in TWO_COLS else []
            if alerts:                    # sem painel: a linha diz qual é o alerta (e de onde vem)
                lvl = "problema" if any(lv == "problema" for lv, _ in alerts) else "aviso"
                msg = alerts[0][1] + (f"  (+{len(alerts) - 1})" if len(alerts) > 1 else "")
                room = W - 40 - (92 + off)
                while g.measure("Medium", 12, msg)[0] > room and len(msg) > 4:
                    msg = msg[:-2].rstrip() + "…"
            g.circle(83 + off, 102, 4, alpha(LEVEL[lvl], a))
            g.text("Medium", 12, msg, 92 + off, 93, alpha(LEVEL[lvl] if alerts else MUTED, a))
        else:
            g.text("Medium", 12, omni_i18n._("ui_usbnet_compat_busy"), 78 + off, 93, alpha(MUTED, a))

        two = cid in TWO_COLS
        # diagnóstico (esquerda); Sistema não tem: as ações ocupam as duas colunas
        px, py, pw, ph = 22 + off, 126, 330, 300
        if two:
            f = None
        if two:
            pass
        elif not f:
            g.rrect(px, py, pw, ph, 20, alpha(GLASS, 14 * fade))
            g.stroke(px, py, pw, ph, 20, ink(16 * fade))
            for k in range(3):
                yy = py + 44 + k * 52
                sh = 0.5 + 0.5 * math.sin(self.t * 4 - k)
                g.rrect(px + 18, yy, pw - 36, 38, 12, ink((10 + 12 * sh) * fade))
        else:
            g.rrect(px, py, pw, ph, 20, alpha(GLASS, 14 * fade))
            g.stroke(px, py, pw, ph, 20, ink(16 * fade))
            g.clip(px, py, pw, ph)
            # Altura de cada item; se não couberem todos, L1/R1 rolam um item por vez.
            top, bottom = py + 14, py + ph - 12
            blocks = []
            sel = self.items[self.item_sel] if self.items else None
            hint = [("dica", sel.tip)] if getattr(sel, "tip", None) else []
            for lvl, txt in hint + f["achados"]:
                lines = g.wrap("Regular", 13, txt, pw - 74)
                blocks.append((lvl, lines, max(40, 14 + 19 * len(lines))))
            offs = [0]
            for *_x, bh in blocks:
                offs.append(offs[-1] + bh + 8)
            room = bottom - top
            if offs[-1] - 8 > room:
                bottom -= 18                          # espaço para o indicador de itens abaixo
                room = bottom - top
            # o último início que ainda mostra o fim da lista
            self.find_max = next((k for k in range(len(blocks)) if offs[-1] - 8 - offs[k] <= room),
                                 len(blocks) - 1) if blocks else 0
            self.find_top = min(self.find_top, self.find_max)
            self.find_scroll = approach(self.find_scroll, offs[self.find_top], dt, 16)
            if abs(self.find_scroll - offs[self.find_top]) < 0.5:
                self.find_scroll = float(offs[self.find_top])
            sc = round(self.find_scroll)              # inteiro: menos geometria nova
            g.clip(px, top, pw, bottom - top)
            # itens que não aparecem inteiros embaixo (o de cima pode aparecer cortado)
            below = sum(1 for k, b in enumerate(blocks) if top + offs[k] - sc + b[2] > bottom + 2)
            for k, (lvl, lines, bh) in enumerate(blocks):
                yy = top + offs[k] - sc
                if yy + bh < top:
                    continue
                if yy >= bottom:
                    break
                c = LEVEL[lvl]
                g.rrect(px + 12, yy, pw - 24, bh, 12, alpha(c, 22 * fade))
                g.circle(px + 32, yy + 20, 11, alpha(c, 230 * fade))
                g.icon(LEVEL_ICON[lvl], px + 24, yy + 12, 16, alpha(hexc("10142a"), a))
                for n, line in enumerate(lines):
                    g.text("Regular", 13, line, px + 52, yy + 8 + 19 * n, alpha(TEXT, a))
            g.clip(px, py, pw, ph)
            if self.find_top > 0:
                label = omni_i18n._("ui_card_find_above").format(count=self.find_top)
                g.text("Medium", 11, label, px + pw - 18, py + ph - 24, alpha(FAINT, a), "r")
            if below:
                label = omni_i18n._("ui_card_find_below").format(count=below)
                g.text("Medium", 12, label, px + 18, py + ph - 24, alpha(FAINT, a))
        g.clip()

        # controles (direita)
        cx, cy, cw = 366 + off * 1.5, 126, 252
        half = (len(self.items) + 1) // 2 if two else len(self.items)
        if two:                                 # 6 linhas por coluna: mais baixas e a partir de mais acima
            cw, cx, cy = (W - 44 - 16) / 2, 22, 116
        xs = [cx if k < half else cx + cw + 16 for k in range(len(self.items))]
        # Altura de cada item: ações com nome longo quebram em linhas (ao lado
        # da etiqueta SUGERIDO, se houver) e o botão cresce para caber tudo.
        gap, tag = 10, omni_i18n._("ui_card_suggested_tag")
        tw = g.measure("Bold", 9, tag)[0] + 14
        # o primeiro botão começa na mesma altura da borda do painel da esquerda (py)
        layout, y = [], cy
        for k, it in enumerate(self.items):
            if k == half:
                y = cy                          # segunda coluna recomeça no topo
            lines = None
            ih = 44 if two else 50
            if isinstance(it, Action):
                lines = g.wrap("SemiBold", 14, it.label, cw - 46 - 14)
                extra = 20 if getattr(it, "suggested", False) else 0   # selo SUGERIDO em cima
                ih = max(44 if two else 50, 16 + 19 * len(lines) + extra)
            layout.append((y, ih, lines))
            y += ih + (5 if two else gap)
        # muitas ações (Geral, Cartões): a coluna rola para o item escolhido caber acima do rodapé
        top, bottom = cy - 4, py + ph
        sy, sh = layout[self.item_sel][:2] if layout else (cy, 50)
        want = max(0, sy + sh - bottom) if sy - cy > 0 else 0
        self.act_off = approach(getattr(self, "act_off", 0), want, dt, 18)
        same = lambda k: (k < half) == (self.item_sel < half)   # só a coluna do item escolhido rola
        layout = [(y - (self.act_off if same(k) else 0), ih, lines) for k, (y, ih, lines) in enumerate(layout)]
        sel_y, sel_h = layout[self.item_sel][:2] if layout else (cy, 50)
        g.clip(cx - 20, top, (xs[-1] if xs else cx) + cw + 40 - cx, bottom - top + 4)
        self.item_y = approach(self.item_y or sel_y, sel_y, dt, 18)
        sel_x = xs[self.item_sel] if xs else cx
        self.item_x = sel_x if not two else approach(getattr(self, "item_x", None) or sel_x, sel_x, dt, 18)
        self.item_h = approach(getattr(self, "item_h", 0) or sel_h, sel_h, dt, 18)
        a1, a2 = self.accent
        ih_ = round(self.item_h)
        g.sprite(("it", a1, a2, ih_), cw, ih_, 16, lambda ox, oy: (
                 g.glow(ox, oy, cw, ih_, 16, alpha(a1, 80), 16),
                 g.rrect(ox, oy, cw, ih_, 16, alpha(a1, 235), alpha(a2, 235))),
                 self.item_x, self.item_y, 255 * fade)
        self.hits_page = [(k, xs[k], y, cw, ih) for k, (y, ih, _) in enumerate(layout) if top <= y + ih / 2 <= bottom]
        for k, it in enumerate(self.items):
            y, ih, lines = layout[k]
            cx = xs[k]
            on = k == self.item_sel
            if not on:
                g.rrect(cx, y, cw, ih, 16, alpha(GLASS, 16 * fade))
            danger = getattr(it, "danger", False)
            icol = LEVEL["problema"] if danger and not on else (ON_TEXT if on else TEXT)
            g.icon(it.icon, cx + 14, y + ih / 2 - 11, 22, alpha(icol, a))
            if isinstance(it, Slider):
                it.shown = approach(it.shown, it.value, dt, 16)
                g.text("SemiBold", 13, it.label, cx + 46, y + 8, alpha(ON_TEXT if on else TEXT, a))
                g.text("SemiBold", 13, f"{it.value}%", cx + cw - 14, y + 8, alpha(ON_TEXT if on else TEXT, a), "r")
                bx, by, bw = cx + 46, y + 33, cw - 60
                g.rrect(bx, by, bw, 6, 3, ((255, 255, 255) if on else INK) + ((70 if on else 30) * fade,))
                g.rrect(bx, by, max(6, bw * it.shown / 100), 6, 3, alpha(TEXT if on else hexc(c1), a))
                g.circle(bx + bw * it.shown / 100, by + 3, 7 if on else 5, alpha(ON_TEXT if on else TEXT, a))
            elif isinstance(it, Choice):
                g.text("Regular", 11, it.label, cx + 46, y + 7, alpha(ON_TEXT if on else MUTED, a))
                val = str(it.names.get(it.options[it.index], it.options[it.index]))
                g.text("SemiBold", 14, val, cx + 46, y + 22, alpha(ON_TEXT if on else TEXT, a))
                if on:
                    g.chevron(cx + cw - 44, y + ih / 2, 9, alpha(ON_TEXT if on else TEXT, a), left=True)
                    g.chevron(cx + cw - 20, y + ih / 2, 9, alpha(ON_TEXT if on else TEXT, a))
            else:
                sug = getattr(it, "suggested", False)
                ty = y + (ih - 19 * len(lines) - (20 if sug else 0)) / 2 + (20 if sug else 0)
                if sug:
                    g.rrect(cx + 46, ty - 21, tw, 16, 8, (255, 255, 255, 60) if on else alpha(LEVEL["aviso"], 70))
                    g.text("Bold", 9, tag, cx + 46 + tw / 2, ty - 12.5, alpha(ON_TEXT if on else TEXT, a), "c", "m")
                for n, ln in enumerate(lines):
                    g.text("SemiBold", 14, ln, cx + 46, ty + 19 * n + 9.5, alpha(ON_TEXT if on else TEXT, a), "l", "m")
        g.clip()
        it = self.items[self.item_sel] if self.items else None
        hints = [("A", omni_i18n._("ui_hint_confirm"), TEXT), ("B", omni_i18n._("ui_back"), MUTED)]
        if isinstance(it, Slider) or (isinstance(it, Choice) and self.page in TWO_COLS):
            hints.insert(1, (omni_i18n._("ui_hint_analog"), omni_i18n._("ui_hint_adjust"), MUTED))   # o direcional fica para navegar
        elif isinstance(it, Choice):
            hints.insert(1, ("LR", omni_i18n._("ui_hint_adjust"), MUTED))
        if f and self.find_max > 0:
            hints.append(("L1 / R1", omni_i18n._("ui_hint_scroll"), MUTED))
        self.draw_footer(hints)

    def draw_overlays(self, dt):
        g = self.g
        if self.picker:
            self.draw_picker(dt)
        if getattr(self, "sheet", None):
            self.draw_sheet(dt)
        if getattr(self, "levels", None):
            self.draw_levels(dt)
        if getattr(self, "viewer", None):
            self.draw_viewer(dt)
        if getattr(self, "danger", None):
            self.draw_danger(dt)
        if getattr(self, "capture", None):
            self.draw_capture()
        if self.busy:
            g.rrect(0, 0, W, H, 0, (5, 7, 20, 170), feather=0)
            g.circle(W / 2, H / 2 - 20, 30, ink(20))
            g.arc(W / 2, H / 2 - 20, 30, 5, self.t * 400, self.t * 400 + 280, alpha(self.accent[0], 255))
            g.text("Medium", 14, self.busy, W / 2, H / 2 + 30, TEXT, "c")
        if self.modal:
            m = self.modal
            g.rrect(0, 0, W, H, 0, (5, 7, 20, 175), feather=0)
            lines = []
            for ln in g.wrap("Regular", 13, m["text"], 380):
                lines.append(ln)
            if len(lines) > 12:                   # texto maior que a caixa: corta com reticências
                lines = lines[:11] + [lines[11].rstrip(".,; ") + "…"]
            img = m.get("image")
            mh = 152 + 19 * len(lines) + (220 if img else 0)
            mx, my, mw = (W - 440) / 2, (H - mh) / 2, 440
            acc = (hexc("ef4444"), hexc("b91c1c")) if m.get("danger") else self.accent   # alerta: vermelho
            g.glow(mx, my, mw, mh, 24, alpha(acc[0], 70 if m.get("danger") else 60), 26)
            g.rrect(mx, my, mw, mh, 24, MODAL_A, MODAL_B)
            g.stroke(mx, my, mw, mh, 24, alpha(acc[0], 120) if m.get("danger") else ink(25), 1.5 if m.get("danger") else 1)
            g.rrect(mx + 24, my + 22, 38, 38, 12, acc[0], acc[1])
            g.icon(m["icon"], mx + 32, my + 30, 22, ON_TEXT)
            g.text("Bold", 18, m["title"], mx + 74, my + 28, TEXT)
            for k, ln in enumerate(lines):
                g.text("Regular", 13, ln, mx + 30, my + 74 + 19 * k, TEXT)
            if img:
                qy = my + 82 + 19 * len(lines)
                g.rrect(W / 2 - 98, qy, 196, 196, 16, (255, 255, 255, 255))
                g.image(img, W / 2 - 88, qy + 10, 176)
                if m.get("url"):
                    g.text("SemiBold", 13, m["url"], W / 2, qy + 204, TEXT, "c")
            bw = (mw - 60 - 12 * (len(m["buttons"]) - 1)) / len(m["buttons"])
            lk = m.get("lock")
            for k, label in enumerate(m["buttons"]):
                bx, by = mx + 30 + k * (bw + 12), my + mh - 54
                locked = lk and k == lk[0] and self.t < lk[1]
                if locked:
                    label = f"{label} ({int(lk[1] - self.t) + 1})"   # contagem da trava
                if locked:
                    g.rrect(bx, by, bw, 38, 14, alpha(acc[0], 60 if k == m["sel"] else 30) if m.get("danger")
                            else ink(40 if k == m["sel"] else 14))
                elif k == m["sel"]:
                    g.rrect(bx, by, bw, 38, 14, acc[0], acc[1])
                else:
                    g.rrect(bx, by, bw, 38, 14, ink(22))
                g.text("SemiBold", 13, label, bx + bw / 2, by + 19.5,
                       ON_TEXT if k == m["sel"] and not locked else alpha(TEXT, 150) if locked else TEXT, "c", "m")
        if self.reader:
            self.draw_reader(dt)
        if getattr(self, "pad", None):
            self.draw_pad(dt)
        if getattr(self, "kbd", None):
            self.draw_keyboard(dt)
        if self.toast:
            txt, lvl, until = self.toast
            left = until - self.t
            if left <= 0:
                self.toast = None
            else:
                k = min(1, left / 0.3, (3.5 - left) / 0.3 + 0.0001 if left > 3.2 else 1)
                tw = min(560, g.measure("Medium", 13, txt)[0] + 70)
                tx, ty = (W - tw) / 2, H - 96 + (1 - k) * 30
                g.rrect(tx, ty, tw, 40, 20, alpha(TOAST, 245 * k))
                g.circle(tx + 22, ty + 20, 9, alpha(LEVEL[lvl], 255 * k))
                g.icon(LEVEL_ICON[lvl], tx + 15, ty + 13, 14, alpha(hexc("10142a"), 255 * k))
                g.text("Medium", 13, txt, tx + 40, ty + 20.5, alpha(TEXT, 255 * k), "l", "m")

    def reader_lines(self, text, width):
        """(peso, tamanho, texto, altura) de cada linha; "# " vira título."""
        key = ("reader", text, width)
        hit = self.g.wcache.get(key)
        if hit is None:
            hit = []
            for para in text.split("\n"):
                if para.startswith("# "):
                    if hit:
                        hit.append(("Regular", 8, "", 8))
                    for ln in self.g.wrap("SemiBold", 15, para[2:], width):
                        hit.append(("SemiBold", 15, ln, 24))
                elif not para.strip():
                    hit.append(("Regular", 8, "", 10))
                else:
                    for ln in self.g.wrap("Regular", 13, para, width):
                        hit.append(("Regular", 13, ln, 20))
            self.g.wcache[key] = hit
        return hit

    def draw_reader(self, dt):
        g, r = self.g, self.reader
        g.rrect(0, 0, W, H, 0, (5, 7, 20, 190), feather=0)
        mx, my, mw, mh = 24, 20, W - 48, H - 40
        g.rrect(mx, my, mw, mh, 22, MODAL_A, MODAL_B)
        g.stroke(mx, my, mw, mh, 22, ink(25))
        a1, a2 = self.accent
        g.rrect(mx + 20, my + 16, 36, 36, 12, a1, a2)
        g.icon(r["icon"], mx + 28, my + 24, 20, ON_TEXT)
        g.text("Bold", 18, r["title"], mx + 68, my + 22, TEXT)
        lines = self.reader_lines(r["text"], mw - 70)
        ty, th = my + 66, mh - 66 - 44
        # rolagem por linha: "top" é a primeira linha visível
        heights = [ln[3] for ln in lines]
        total, fit = sum(heights), 0
        acc = 0
        for h_ in reversed(heights):        # quantas linhas do fim cabem na tela
            if acc + h_ > th:
                break
            acc += h_
            fit += 1
        r["max"] = max(0, len(lines) - fit)
        r["top"] = min(r["top"], r["max"])
        r["scroll"] = approach(r["scroll"], sum(heights[:r["top"]]), dt, 18)
        g.clip(mx, ty, mw, th)
        y = ty - r["scroll"]
        seen, vis = set(), []
        for weight, size, txt, h_ in lines:
            if y + h_ > ty - 30 and y < ty + th and txt:
                g.text(weight, size, txt, mx + 32, y, TEXT)
                for i, (word, _f) in enumerate(r.get("links") or ()):
                    if word not in txt or i in seen:
                        continue
                    seen.add(i)
                    if y >= ty and y + h_ <= ty + th:
                        vis.append(i)
                    pre = txt[:txt.index(word)]
                    lx = mx + 32 + (g.measure(weight, size, pre)[0] if pre else 0)
                    lw = g.measure(weight, size, word)[0]
                    if i == r.get("focus"):    # o link com foco: cheio, como um botão
                        g.rrect(lx - 5, y - 3, lw + 10, size + 10, 6, a1, a2)
                        g.text("SemiBold", size, word, lx, y, ON_TEXT)
                    else:                      # os outros: na cor do card e sublinhados
                        g.rrect(lx - 2, y - 1, lw + 4, size + 6, 4, MODAL_A)
                        g.text("SemiBold", size, word, lx, y, a1)
                        g.rrect(lx, y + size + 3, lw, 1.5, 0.75, a1, feather=0)
            y += h_
        g.clip()
        r["vis"] = vis
        if vis and r.get("focus") not in vis:   # a rolagem levou o foco: vai para o primeiro visível
            r["focus"] = vis[0]
        if total > th:   # barra de rolagem
            bh = max(30, th * th / total)
            by = ty + (th - bh) * (r["scroll"] / max(1, sum(heights[:r["max"]])))
            g.rrect(mx + mw - 14, ty, 4, th, 2, ink(18))
            g.rrect(mx + mw - 14, by, 4, bh, 2, alpha(a1, 220))
        self.draw_footer_at(my + mh - 30, ([("UD", omni_i18n._("ui_hint_scroll")), ("LR", omni_i18n._("ui_hint_jump"))] if r["max"] else []) +   # texto curto: nada a rolar
                            ([("A", omni_i18n._("ui_hint_open"))] if r.get("focus") in (r.get("vis") or ()) else []), mx + 24)
        self.draw_footer_at(my + mh - 30, [("B", omni_i18n._("ui_back"))], mx + mw - 110)

    def frame(self, dt):
        self.t += dt
        if getattr(self, "pad", None):
            self.pad_tick(time.monotonic())
        if self.page and not self.loading:
            self.live_refresh()
        while self.pending:
            done, res, had_busy = self.pending.pop(0)
            if had_busy:
                self.busy = None
            done(res)
        if self.page is None and self.view == "lib":
            tgt = card_info("jogos")
        elif self.page is None:
            tgt = CARDS[self.sel]
        else:
            tgt = card_info(self.page)
        # cor troca de uma vez: uma cor intermediária por quadro refaria a geometria
        self.accent = [hexc(tgt[3]), hexc(tgt[4])]
        self.page_anim = approach(self.page_anim, 1.0 if self.page else 0.0, dt, 12)
        g = self.g
        g.clear()
        if getattr(self, "goodbye", None):   # desligando/reiniciando: só a despedida até o fim
            folder = os.path.expanduser("~/Apps/Omni36OS/telas/out") if FAKE else "/opt/omni36os-telas"
            g.picture(os.path.join(folder, self.goodbye + ".png"), 0, 0, W, H)
            return
        self.draw_bg(dt)
        if self.loading:
            self.draw_loading(dt)
            return
        if not self.warm and not FAKE and os.path.exists(TURBO):
            self.turbo_off()
        app = ((getattr(self, "video", None) and self.draw_video) or (getattr(self, "note", None) and self.draw_note)
               or (getattr(self, "music", None) and self.draw_music))
        if app:                           # app em tela cheia (vídeo, nota, músicas): o menu não aparece por baixo,
            app(dt)                       # nem a lista de onde ele foi aberto (Arquivos, Vídeos, Notas)
            pk, self.picker = self.picker, None
            self.draw_overlays(dt)
            self.picker = pk
            return
        self.draw_header()
        p = self.page_anim
        if p < 0.01 or p > 0.99:
            self.snap = None
        if p < 0.01 and not self.page:
            self.draw_home(dt, 1)
        elif p > 0.99 and self.page:
            self.draw_page(dt, 1)
        else:
            # Transição: cada tela vai inteira (opaca, no lugar) para uma
            # textura, e a GPU só mistura as duas. Mudar o alfa e a posição das
            # formas a cada quadro anularia o cache de geometria.
            # As telas não mudam nesses 0,3 s: desenha uma vez só, no início.
            home, page = g.layer("home"), g.layer("page")
            key = (self.page, self.last_page)
            if self.snap != key:
                self.snap = key
                g.begin_layer(home)
                self.draw_home(dt, 1)
                g.begin_layer(page)
                cur, self.page = self.page, self.page or self.last_page
                self.draw_page(dt, 1)
                self.page = cur
                g.end_layer()
            g.draw_layer(home, -24 * p, 255 * (1 - p))
            g.draw_layer(page, 24 * (1 - p), 255 * p)
        self.draw_overlays(dt)

    def turbo_off(self):
        """Fim do boot: menu na tela e páginas montadas. Tudo volta ao mínimo para o menu."""
        try:
            os.remove(TURBO)
            omni.apply_limits()           # limites de Desempenho (o boot passou no máximo do hardware)
            omni.relax_clocks()
        except OSError:
            pass
        print(f"boot concluído {time.clock_gettime(time.CLOCK_BOOTTIME):.1f} s após ligar: mínimo", file=sys.stderr, flush=True)

    def draw_welcome(self):
        """A boas-vindas do boot (telas/gerar_telas.py + omni_tela.py) redesenhada pixel a pixel: o
        console passa da imagem do boot para a abertura do Omni36OS sem a tela mudar. Sempre nas
        cores do tema escuro, que são as do boot."""
        g = self.g
        g.vgradient(hexc("0b1024"), hexc("140f30"))
        g.blob(50, 10, 260, (*BOOT_CIANO[:3], 40))
        g.blob(610, 490, 260, (*BOOT_ROXO[:3], 40))
        g.glow(W / 2 - 75, 95, 150, 150, 30, alpha(BOOT_CIANO, 70), 40)
        g.image("logo-boas-vindas", W / 2 - 75, 95, 150, smooth=True)
        g.text("Medium", 20, omni_i18n._("ui_welcome_back"), W / 2, 262, hexc("b8bedb"), "c")
        parts = [("Omni", hexc("f4f6ff")), ("36", BOOT_CIANO), ("OS", BOOT_ROXO)]
        x = W / 2 - sum(g.measure("ExtraBold", 48, t)[0] for t, _ in parts) / 2
        for t, c in parts:
            g.text("ExtraBold", 48, t, x, 290, c)
            x += g.measure("ExtraBold", 48, t)[0]
        nome = self.player or omni_i18n._("ui_welcome_player")
        w = 56 + g.measure("SemiBold", 16, nome)[0] + 22          # pílula do tamanho do nome
        x0, y0 = round((W - w) / 2), 370
        g.rrect(x0, y0, w, 50, 25, hexc("1b1f42"))
        g.stroke(x0, y0, w, 50, 25, hexc("2a3060"))
        g.circle(x0 + 26, y0 + 25, 16, BOOT_CIANO)
        g.text("SemiBold", 16, nome[0].upper(), x0 + 26, y0 + 25, hexc("0b1024"), "c", "m")
        g.text("SemiBold", 16, nome, x0 + 56, y0 + 25, hexc("f4f6ff"), "l", "m")

    def draw_loading(self, dt):
        g = self.g
        if self.results and self.warm:
            self.load_label = omni_i18n._("ui_loading_menu")
            self.load_done = self.load_total - len(self.warm)
        elif self.results or self.fast:
            self.load_done = self.load_total
        frac = self.load_done / max(1, self.load_total)
        self.load_shown = approach(self.load_shown, frac, dt, 10)
        self.draw_welcome()
        # a única diferença para a tela do boot: o anel girando em volta do ícone
        g.arc(W / 2, 170, 100, 4, self.t * 300 % 360, self.t * 300 % 360 + 260, alpha(BOOT_CIANO, 230))
        if (self.results or self.fast) and not self.warm and self.load_shown > 0.98:
            self.loading = False
            self.deliver = None           # a entrega do Ports começa agora, com o menu na tela
            self.warm = getattr(self, "warm_later", None) or self.warm
            print(f"menu na tela em {time.monotonic() - self.t_start:.1f} s", file=sys.stderr, flush=True)
            print(f"menu na tela {time.clock_gettime(time.CLOCK_BOOTTIME):.1f} s após ligar", file=sys.stderr, flush=True)
            if not FAKE:                  # o menu abriu: uma atualização recente está aprovada
                omni_update.confirm_ok()
                # adaptador de Wi-Fi preso no modo disco: religa sem ninguém perceber (avisa só se agiu)
                threading.Thread(target=lambda: (lambda r: r and setattr(
                    self, "toast", (r, "aviso" if r.startswith("Erro") else "ok", self.t + 5)))(
                    omni_sistema.wifi_dongle_fix()), daemon=True).start()
                if os.path.exists(omni_sistema.USBNET_PENDING):   # saiu do pendrive para ligar a rede USB
                    self.worker(omni_sistema.usbnet_pending,
                                lambda res: res and not isinstance(res, Exception) and setattr(
                                    self, "toast", (str(res), "aviso" if str(res).startswith("Erro") else "ok", self.t + 5)),
                                busy=omni_i18n._("ui_usbnet_universal_busy"))
                back = omni_update.rolled_back_message()
                if back:
                    self.modal = {"title": omni_i18n._("ui_system_update_rolled_back_title"), "icon": "alert-triangle", "sel": 0,
                                  "buttons": ["OK"], "text": back + "\n" + omni_i18n._("ui_system_update_rolled_back_text")}
            self.first_screens()
            if RESUME == "testar":
                self.sel = next(i for i, c in enumerate(CARDS) if c[0] == "ferramentas")
                self.open_page("testar")
                self.show_test_result()
            elif RESUME in ("biblioteca", "port"):   # voltou de um jogo: a lista no mesmo lugar
                self.view = "lib"
            elif RESUME in [c[0] for c in CARDS]:    # voltou de uma ferramenta do Omni36OS
                self.sel = next(i for i, c in enumerate(CARDS) if c[0] == RESUME)
                self.open_page(RESUME)
            elif RESUME in SUBPAGES:                 # ferramenta aberta de uma subpágina (ex.: RetroArch)
                self.sel = next(i for i, c in enumerate(CARDS) if c[0] == PARENT[RESUME])
                self.open_page(RESUME)
            try:
                os.remove(POWER_PRESS)                   # de um menu que não fechou direito
            except OSError:
                pass
            try:
                if time.time() - os.path.getmtime(POWER_FLAG) < 60:
                    self.want_power = self.power_return = True   # aberto pelo power num jogo
                os.remove(POWER_FLAG)
            except OSError:
                pass

    def prewarm(self):
        """Monta a geometria e o texto de uma página por quadro, fora da tela,
        para a primeira abertura de cada uma não engasgar."""
        if not self.warm or self.page or self.page_anim > 0.01 or not self.results:
            return
        cid = self.warm.pop(0)
        if cid == "home":
            keep = (self.sel, self.sel_x, self.sel_y, self.accent, self.deliver)
            self.deliver = -99.0            # monta o destaque pronto (sem a entrega)
            self.g.begin_layer(self.g.layer("warm"))
            for i, c in enumerate(CARDS):   # destaque, selo e cor de cada cartão
                self.sel, self.accent = i, [hexc(c[3]), hexc(c[4])]
                self.draw_header()
                self.draw_home(0.016, 1)
            self.sel, self.sel_x, self.sel_y, self.accent, self.deliver = keep
            self.g.end_layer()
            return
        saved = (self.page, getattr(self, "items", None), getattr(self, "item_sel", 0),
                 getattr(self, "findings", None), getattr(self, "item_y", 0.0))
        self.page = cid
        self.items = self.build_items(cid) if cid != "cartoes" else []
        self.item_sel, self.findings, self.item_y = 0, self.home_check, 0.0
        self.g.begin_layer(self.g.layer("warm"))
        self.draw_page(0.016, 1)
        self.g.end_layer()
        self.page, self.items, self.item_sel, self.findings, self.item_y = saved

    def run(self):
        demo = [s for s in os.environ.get("OMNI_DEMO", "").split(",") if s]
        shot_dir = os.environ.get("OMNI_SHOT_DIR", ".")
        shots, next_demo = 0, time.monotonic() + 1.0
        last = time.monotonic()
        errors = []                   # horários dos erros recentes
        while self.running:
            try:
                now = time.monotonic()
                dt = min(0.05, now - last)
                last = now
                self.poll()
                self.capture_poll()
                self.power_check()
                if demo and now >= next_demo and not self.busy:
                    cmd = demo.pop(0)
                    next_demo = now + DEMO_STEP
                    if cmd.startswith("wait"):
                        next_demo = now + int(cmd[4:]) / 1000
                    elif cmd == "shot":
                        shots += 1
                        self.frame(dt)
                        self.g.screenshot(os.path.join(shot_dir, f"{shots:02d}.ppm"))
                        self.g.present()
                        continue
                    elif cmd == "power":
                        self.want_power = True
                    elif cmd == "quit":
                        self.running = False
                    elif cmd.startswith("pad:"):       # teste: aperta (ou solta, com -) um botão no teste do controle
                        n = int(cmd[4:])
                        self.pad_event("btn", abs(n), n >= 0 and not cmd[4:].startswith("-"), now)
                    elif cmd.startswith("axis:"):
                        k, v = cmd[5:].split("=")
                        self.pad_event("axis", int(k), int(v), now)
                    elif cmd.startswith("warn:"):      # teste: abre o aviso sem rodar nada
                        secs, hold, risk, undo = DANGER[cmd[5:]]
                        self.warn(cmd[5:], "Teste do aviso.", lambda: setattr(self, "toast", ("teste: passou", "ok", self.t + 3.5)),
                                  secs, hold, risk=risk, undo=undo)
                    elif cmd in ("hold", "release"):
                        self.ok_held = cmd == "hold"
                        if cmd == "hold":
                            self.handle("ok")
                    else:
                        self.handle(cmd)
                self.frame(dt)
                if self.want_shot and getattr(self, "music", None) and self.music["off"]:
                    self.music_screen(True)       # tela apagada no tocador: acende e grava no próximo quadro
                    self.music["last"] = self.t
                elif self.want_shot:
                    self.want_shot = False
                    self.save_shot()
                self.g.present()
                if self.loading or (self.warm and now - self.last_input > 0.6):
                    self.prewarm()             # com o menu aberto, só quando ninguém está apertando nada
                if self.refresh_at and now >= self.refresh_at and not self.busy:
                    self.refresh_at = None
                    self.worker(self.check_all, self._all_checked, quiet=True)
                # Ritmo: 30 quadros/s em uso e 10 parado. A 60 quadros/s sem parar a
                # Omni36OS ocupava 70% de um núcleo e deixava o aparelho perto de 80 °C.
                music = getattr(self, "music", None)
                moving = (getattr(self, "video", None) or self.loading or self.busy or getattr(self, "danger", None) or self.toast or 0.01 < self.page_anim < 0.99
                          or (music and not music["off"] and music["player"].current() and not music["player"].paused)
                          or getattr(self, "kbd", None) or getattr(self, "pad", None)
                          or now - self.last_input < IDLE_AFTER)
                spare = 1 / (FPS_ACTIVE if moving else FPS_IDLE) - (time.monotonic() - now)
                if spare > 0:
                    time.sleep(spare)
            except Exception:
                # Um erro num botão ou num desenho não derruba o Omni36OS: vai para o log, as janelas
                # abertas fecham e a tela segue. Erro sem parar (mais de 10 em 5 s) cai de vez e o
                # launch-direct.sh abre de novo do zero, guardando o log.
                import traceback
                traceback.print_exc()
                sys.stderr.flush()
                now = time.monotonic()
                errors = [t for t in errors if now - t < 5] + [now]
                if len(errors) > 10:
                    raise
                self.picker = self.modal = self.kbd = None
                self.sheet = None
                self.danger = self.busy = None
                self.toast = (omni_i18n._("tx_oops"), "aviso", self.t + 4)
                last = time.monotonic()
        self.save_state()
        gfx.SDL_Quit()


if __name__ == "__main__":
    App().run()
