#!/usr/bin/env python3
"""Omni36OS — diagnósticos por regras fixas (sem IA).

Cada verificação coleta fatos com as ferramentas de omni.py e devolve achados
(nível, texto) e as ações sugeridas. Níveis: "ok", "info", "aviso", "problema"
("info" não conta como alerta).

Uso: omni_checks.py [verificação]   (sem argumento lista as verificações)
"""
import glob
import json
import os
import shutil
import sys

import omni
import omni_audio
import omni_i18n

_ = omni_i18n._

TEMP_QUENTE = 75      # °C: acima disso o aparelho está aquecendo
BATERIA_BAIXA = 20    # %

# --- Ações (o único jeito de uma verificação mudar algo no aparelho) ---

ACTION_KEYS = {
    "economizar_bateria": ("action_economizar", lambda: omni.set_preferred_governor({"governor": "powersave"})),
    "baixar_brilho": ("action_brilho", lambda: omni.set_screen_brightness({"value": 30})),
    "restaurar_audio": ("action_audio", omni.restore_audio),
    "ligar_pendrive": ("action_pendrive_on", omni.usb_on),
    "desligar_pendrive": ("action_pendrive_off", omni.usb_off),
    "fix_dmc": ("action_fix_ram", omni.fix_dmc),
    "limpar_mac": ("action_limpar_mac", omni.clean_mac_junk),
    "cpu_padrao": ("action_cpu_padrao", lambda: omni.set_cpu_max({"mhz": omni.CPU_SAFE_MHZ})),
}
ACTIONS = {name: (_(key), fn) for name, (key, fn) in ACTION_KEYS.items()}

ESPACO_POUCO_PCT = 90   # % de uso do cartão
ESPACO_POUCO_GB = 1.0


def run_action(name):
    return ACTIONS[name][1]() if name in ACTIONS else _("check_nothing_to_do")


# --- Fatos ---

def battery_facts():
    return {
        "bateria_pct": int(omni.read_text("/sys/class/power_supply/battery/capacity", "0")),
        "bateria_estado": omni.read_text("/sys/class/power_supply/battery/status"),
    }


def cpu_facts():
    temp = omni.read_text("/sys/class/thermal/thermal_zone0/temp", "0")
    return {
        "temperatura_c": int(temp) // 1000 if temp.isdigit() else None,
        # o que vale no menu do ES (dentro do Omni36OS o ES sempre deixa "performance")
        "governador": omni.get_preferred_governor(),
        "freq_mhz": int(omni.read_text(f"{omni.CPUFREQ}/scaling_cur_freq", "0")) // 1000,
        "cpu_max_mhz": omni.get_cpu_max(),
        "gpu_max_mhz": omni.get_gpu_max(),
    }


def audio_facts():
    route = ""
    for line in omni.amixer("sget", "Playback Path").splitlines():
        if line.strip().startswith("Item0:"):
            route = line.split("'")[1]
    asound, backup = omni.read(f"{omni.HOME}/.asoundrc"), omni.read(f"{omni.HOME}/.asoundrcbak")
    return {
        "volume_pct": omni.get_volume(),
        "saida_audio": route,
        # automático (omni_audio): HP com o fone encaixado, SPK sem; sem detecção do fone, o do sistema
        "saida_esperada": omni_audio.expected_path() or omni.device_alsa_path(),
        # O perfmax do Omni36OS apaga o .asoundrc ao abrir qualquer port (o Omni36OS
        # inclusive) e o perfnorm o devolve ao sair: ausente é o normal aqui.
        "asoundrc_padrao": asound is None or backup is None or asound == backup,
    }


def sd_facts():
    cards = []
    mounts = omni.mmc_mounts()
    for dev in sorted(glob.glob("/sys/block/mmcblk*/device")):
        blk = dev.split("/")[3]
        manfid = int(omni.read_text(f"{dev}/manfid", "0"), 16)
        cards.append({
            "codigo": f"0x{manfid:02x}", "nome": omni.read_text(f"{dev}/name"), "blk": blk,
            "cartao": "sistema" if "/" in mounts.get(blk, []) else "jogos",
            "fabricante": omni.SD_VENDORS.get(manfid, "desconhecido"),
            "tamanho_gb": round(int(omni.read_text(f"/sys/block/{blk}/size", "0")) * 512 / 1e9, 1),
        })
    return {"cartoes": cards}


def card_free_gb(blk):
    """Espaço livre do cartão inteiro: a soma das partições montadas dele (cada uma contada uma vez)."""
    seen, free = set(), 0
    for mnt in omni.mmc_mounts().get(blk, []):
        try:
            dev = os.stat(mnt).st_dev
            if dev not in seen:
                seen.add(dev)
                free += shutil.disk_usage(mnt).free
        except OSError:
            continue
    return round(free / 1e9, 1) if seen else None


def detalhes():
    """Detalhe do(s) cartão(ões) (Armazenamento): marca, tamanho e um teste de escrita e leitura em cada um."""
    out = []
    for c in sd_facts()["cartoes"]:
        card = c["cartao"]
        nome = "1" if card == "sistema" else "2"
        path = "/roms" if card == "sistema" else "/roms2"
        fab = c["fabricante"] if c["fabricante"] != "desconhecido" else _("tx_no_brand")
        head = _("tx_card_head").format(name=nome, size=c['tamanho_gb'], maker=fab) + (f" ({c['nome']})" if c["nome"] else "")
        f = {}
        if os.path.ismount(path):
            for line in omni.test_microsd_speed({"path": path}).splitlines():
                if line.strip().startswith(("Escrita", "Leitura", "Write", "Read")):
                    f["w" if line.strip().startswith(("Escrita", "Write")) else "r"] = float(line.split(":")[1].split()[0])
        if "w" not in f:
            out.append(("ok", _("check_card_no_partition").format(number=nome, size=c["tamanho_gb"], brand=fab)))
        elif f["w"] < 10:
            out.append(("problema", _("check_card_slow").format(number=nome, size=c["tamanho_gb"], brand=fab, speed=f["w"])))
        else:
            out.append(("ok", _("check_card_speed").format(number=nome, size=c["tamanho_gb"], brand=fab, write=f["w"], read=f.get("r", 0))))
        livre = card_free_gb(c["blk"])
        if livre is not None:
            ocup = max(0.0, round(c["tamanho_gb"] - livre, 1))
            pct = round(100 * ocup / c["tamanho_gb"]) if c["tamanho_gb"] else 0
            full = pct >= ESPACO_POUCO_PCT or livre < ESPACO_POUCO_GB
            out.append(("aviso" if full else "ok", _("check_card_space").format(number=nome, free=livre, used=ocup)))
        if c["fabricante"] == "desconhecido":
            out.append(("info", _("check_card_unknown_brand").format(number=nome, code=c["codigo"])))
    return finish(out or [("aviso", _("check_no_cards"))], [], {})


def screen_facts():
    live = omni.live_panel() or {}
    entries = list(omni.catalog_panels()) if os.path.isdir(omni.CATALOG) else []
    same = [e for e in entries if e["hash"] == live.get("hash")]
    model = live.get("model", "")
    folders = [e["folder"] for e in same if e["model"] == model or e["model"].startswith(model + " ")]
    return {
        "modelo": model,
        "pastas": sorted(set(folders or [e["folder"] for e in same])),
        "clone": omni.is_clone(model, same),
    }


# --- Regras ---

def check_temp(f, out):
    t = f["temperatura_c"]
    if t is None:
        return
    if t > TEMP_QUENTE:
        out.append(("problema", _("check_temp_hot").format(temperature=t)))
    else:
        out.append(("ok", _("check_temp_normal").format(temperature=t)))


def check_overclock(f, out, acts):
    oc = f["cpu_max_mhz"] > omni.CPU_SAFE_MHZ
    if oc and (f["temperatura_c"] or 0) > TEMP_QUENTE:
        out.append(("aviso", _("check_overclock_hot").format(frequency=f["cpu_max_mhz"])))
        acts.append("cpu_padrao")
    elif oc:
        out.append(("info", _("check_overclock_on").format(frequency=f["cpu_max_mhz"])))


def check_services(out, acts):
    for unit in omni.failed_services():
        txt, fix = omni.KNOWN_FAILS.get(unit, (None, None))
        txt = _(txt) if txt else txt
        if txt and not fix:
            out.append(("info", _( "check_service_known").format(message=txt)))
        elif txt:
            out.append(("aviso", _( "check_service_known").format(message=txt)))
            acts.append(fix)
        else:
            out.append(("aviso", _("check_service_failed").format(service=unit.removesuffix(".service"))))


def check_disk(out):
    nomes = {"sistema": _("check_disk_system"), "roms": _("check_disk_roms"), "jogos": _("check_disk_card2")}
    for name, d in omni.disk_facts().items():
        if d["uso_pct"] >= ESPACO_POUCO_PCT or d["livre_gb"] < ESPACO_POUCO_GB:
            dica = _("check_disk_update_tip") if name == "sistema" else ""
            out.append(("aviso", _("check_disk_full").format(card=nomes[name], used=d["uso_pct"], free=d["livre_gb"], tip=dica)))
        else:
            out.append(("ok", _("check_disk_space").format(card=nomes[name], free=d["livre_gb"], used=d["uso_pct"])))


def check_battery(f, out):
    pct, estado = f["bateria_pct"], f["bateria_estado"]
    carregando = estado in ("Charging", "Full")
    if pct < BATERIA_BAIXA and not carregando:
        out.append(("problema", _("check_battery_low").format(percentage=pct)))
    else:
        out.append(("ok", _("check_battery_level").format(percentage=pct, charging=_("check_charging_suffix") if carregando else ".")))


def check_audio(f, out):
    if f["volume_pct"] == 0:
        out.append(("problema", _("check_volume_zero")))
    elif f["volume_pct"] < 20:
        out.append(("aviso", _("check_volume_low").format(percentage=f["volume_pct"])))
    else:
        out.append(("ok", _("check_volume_level").format(percentage=f["volume_pct"])))
    # A saída (fone ou alto-falante) não vira alerta: o omni36os-atalho a corrige sozinho em 1 s.
    nome = {"HP": _("check_audio_route_headphones"), "SPK": _("check_audio_route_speaker"), "SPK_HP": _("check_audio_route_both")}
    if f["saida_audio"]:
        out.append(("ok", _("check_audio_route").format(route=nome.get(f["saida_audio"], "via " + f["saida_audio"]))))
    if not f["asoundrc_padrao"]:
        out.append(("aviso", _("check_audio_config_changed")))


def checkup():
    """Resumo: só o que precisa de atenção, de todos os cards (cada card mostra o seu em detalhe)."""
    parts = [(_("check_bateria"), bateria())]
    a, b = sem_som(), atualizar()
    parts.append((_("check_tela_som"), finish(a["achados"] + b["achados"], a["acoes"], {})))
    f = cpu_facts()
    out, acts = [], []
    check_temp(f, out)
    check_overclock(f, out, acts)
    parts.append((_("check_desempenho"), finish(out, acts, f)))
    out = []
    check_disk(out)        # cartão sem marca não é alerta: só aparece no "Detalhe do cartão"
    parts.append((_("check_armazenamento"), finish(out, [], {})))
    out, acts = [], []
    check_services(out, acts)
    parts.append((_("check_servicos"), finish(out, acts, {})))
    found, acts = [], []
    for card, r in parts:
        found += [(lvl, f"{card}: {txt}") for lvl, txt in r["achados"] if lvl in ("aviso", "problema")]
        acts += [x for x in r["acoes"] if x not in acts]
    if not found:
        found.append(("ok", _("check_tudo_certo")))
    found.append(("info", _("check_detalhe_card")))
    return finish(found, acts, {})


def bateria():
    # o seletor do processador fica em Desempenho; aqui só a dica de economia
    f = {**battery_facts(), **cpu_facts(), "brilho_pct": omni.get_brightness()}
    out, acts = [], []
    check_battery(f, out)
    if f["brilho_pct"] > 60:
        out.append(("aviso", _("check_brightness_high").format(percentage=f["brilho_pct"])))
        acts.append("baixar_brilho")
    else:
        out.append(("ok", _("check_brightness_level").format(percentage=f["brilho_pct"])))
    out.append(("ok", _("check_battery_cpu_tip")))
    return finish(out, acts, f)


def sem_som():
    f = audio_facts()
    out, acts = [], []
    check_audio(f, out)
    if not f["asoundrc_padrao"]:
        acts.append("restaurar_audio")
    return finish(out, acts, f)


def atualizar():
    f = screen_facts()
    out = []
    if f["clone"]:
        out.append(("problema", _("check_clone")))
    return finish(out, [], f)


def pc():
    f = omni.usb_facts()
    warn = []
    if omni.usb_net_active():
        warn.append(("info", _("check_usb_network_warning")))
    if omni.wifi_on_otg():
        warn.append(("aviso", _("check_usb_wifi_warning")))
    part = f["particao_para_o_pc"]
    livre = f["livre_gb"].get(part)
    espaco = f" ({livre} GB livres)" if livre is not None else ""
    if f["modo_pendrive_ligado"]:
        out = [("ok", _("check_usb_mode_on").format(partition=part, space=espaco)),
               ("ok", _("check_usb_copy_instructions")),
               ("info", _("check_usb_wifi_off"))]
        return finish(warn + out, ["desligar_pendrive"], f)
    out = [("ok", _("check_usb_mode_will_appear").format(partition=part, space=espaco)),
           ("info", _("check_usb_reboot")),
           ("info", _("check_usb_mac_tip"))]
    return finish(warn + out, ["ligar_pendrive"], f)


ORDER = {"problema": 0, "aviso": 1, "ok": 2, "info": 3}


def finish(out, acts, facts):
    out = sorted(out, key=lambda a: ORDER.get(a[0], 9))   # alertas primeiro
    worst = "ok"
    for lvl, _ in out:
        if lvl == "problema" or (lvl == "aviso" and worst == "ok"):
            worst = lvl
    return {"nivel": worst, "achados": out, "acoes": acts, "fatos": facts}


CHECKS = {
    "checkup": checkup, "bateria": bateria, "sem_som": sem_som,
    "atualizar": atualizar, "pc": pc,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n".join(CHECKS))
    else:
        print(json.dumps(CHECKS[sys.argv[1]](), ensure_ascii=False, indent=1))
