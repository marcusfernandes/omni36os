"""Omni36OS — GeForce NOW (OpenNOW-4Handhelds) em Aplicativos.

Instalado em /roms/apps (fora de Ports): OpenNOW.sh + opennow/. install() baixa a release mais
nova do GitHub e preserva opennow/stream.json (ajustes) e opennow/data (login). O .sh original
procura /roms/ports/opennow; a cópia daqui usa a própria pasta.

FN: "sistema" = atalhos FN do Omni valem; "gfn" = com o OpenNOW aberto, o FN vai só para ele
(abre o menu da sessão) e o serviço de atalhos ignora as combinações com FN.
"""
import os

import omni_apps

SH = omni_apps.sh_path("gfn")
FN_CONF = "/home/ark/.config/omni36os/gfn_fn"
PROC = "opennow-handhel"               # comm do opennow-handheld (15 letras)


def installed():
    return omni_apps.installed("gfn")


def version():
    return omni_apps.version("gfn")


def install(log=lambda m: None):
    return omni_apps.install("gfn", log)


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
