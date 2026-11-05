"""Atalhos dentro dos jogos (Controles > Atalhos): o que existe, os botões padrão e os nomes.

Fonte única para o serviço (omni_atalho.py), o Omni36OS (omni_ui.py), o omni.py e o manual.
Os botões são códigos evdev do controle do R36S (rk3326-r36s-linux.dtb).
"""

import omni_i18n

FN, SELECT, START = 708, 704, 705
BUTTONS = {708: "FN", 704: "SELECT", 705: "START", 310: "L1", 311: "R1", 312: "L2", 313: "R2", 706: "L3",
           707: "R3", 305: "A", 304: "B", 307: "X", 308: "Y", 544: "tx_up", 545: "tx_down", 546: "tx_left",
           547: "tx_right", 115: "Vol+", 114: "Vol-"}
ORDER = list(BUTTONS)            # ordem em que os nomes aparecem: FN primeiro, direcional por último

# chave: (nome, ícone, tipo, botões padrão, ligado por padrão). "toque" age quando a combinação
# fecha; "segurar" pede a combinação parada por 1 s. Personalizar troca só a tecla que vai com o
# FN; o de sair do jogo (FIXED) é sempre SELECT + START.
ACTIONS = {
    "fps": (omni_i18n._("combo_action_fps"), "gauge", "toque", [FN, 307], True),
    "limite": (omni_i18n._("combo_action_limit"), "battery-2", "toque", [FN, 304], True),
    "captura": (omni_i18n._("combo_action_capture"), "device-tv", "toque", [FN, 308], True),
    "fechar": (omni_i18n._("combo_action_close"), "x", "segurar", [SELECT, START], True),
}
CAP_FPS = 30
FIXED = {"fechar"}

# o que o ogage (serviço do dArkOSen) já faz com o FN: um atalho novo não pode usar
SYSTEM = [({FN, 544}, "tx_owner_bright"), ({FN, 545}, "tx_owner_bright"), ({FN, 546}, "tx_owner_gamma"), ({FN, 547}, "tx_owner_gamma"),
          ({FN, 115}, "tx_owner_bright"), ({FN, 114}, "tx_owner_bright"), ({FN, 310}, "tx_owner_system"), ({FN, 311}, "tx_owner_system"),
          ({FN, 305}, "tx_owner_system"), ({FN, 706}, "tx_owner_system"), ({FN, 707}, "tx_owner_system"),
          ({SELECT, FN}, "tx_owner_battery")]


def defaults():
    return {**{k: a[4] for k, a in ACTIONS.items()}, "combos": {k: list(a[3]) for k, a in ACTIONS.items()}}


def normalize(c):
    """Escolhas gravadas (inclusive de versões anteriores) -> {chave: bool, "combos": {...}}."""
    out = defaults()
    c = c if isinstance(c, dict) else {}
    for k in ACTIONS:
        v = c.get(k, out[k])
        if k == "fps" and isinstance(v, str):            # 1.5.0 antiga: "fn" | "sempre" | "desligado"
            v = v != "desligado"
        elif k == "limite" and not isinstance(v, bool):   # 1.5.0 antiga: 0 | 30 | 45
            v = bool(v)
        out[k] = bool(v)
    for k, cb in (c.get("combos") or {}).items():
        if k in ACTIONS and k not in FIXED and isinstance(cb, list) and len(cb) >= 2 and all(b in BUTTONS for b in cb):
            out["combos"][k] = cb
    return out


def text(codes):
    """[708, 307] -> "FN + X"."""
    return " + ".join(omni_i18n._(BUTTONS[b]) for b in sorted(set(codes), key=ORDER.index))


def problem(key, codes, combos):
    tr = omni_i18n._
    """Por que essa combinação não serve (ou None)."""
    s = set(codes)
    if key in FIXED:
        return tr("combo_fixed")
    if len(s) < 2:
        return omni_i18n._("tx_pick_key")
    if 116 in s:
        return tr("combo_power")
    if s == {SELECT, START} or s == {FN, SELECT, START}:
        return tr("combo_exit_fixed")
    for cb, what in SYSTEM:
        if s == cb:
            return tr("combo_system").format(combo=text(cb), owner=tr(what))
    for k, cb in combos.items():
        if k != key and set(cb) == s:
            return tr("combo_duplicate").format(combo=text(cb), action=ACTIONS[k][0])
    return None


def tip(key, combos):
    t = text(combos[key])
    return omni_i18n._("combo_tip_" + key).format(combo=t, fps=CAP_FPS)
