#!/usr/bin/env python3
"""Omni36OS — limpeza única do que veio da base (dArkOSen) e um sistema só de ports não usa.

Roda uma vez por versão da limpeza (marca em /var/lib/omni36os-update/limpeza-<N>), pelo serviço de
atalhos, com o menu na tela (nunca durante um jogo). Chega aos consoles pela atualização do Omni e às
imagens novas no primeiro boot.

  - serviços do EmulationStation/RetroArch que ficaram rodando: param, desligam e são mascarados;
  - pacotes de compilar e o Java (apt-get purge, sem internet; o dpkg continua sabendo o que há);
  - documentação e traduções que não são pt-BR nem inglês;
  - sobras de emuladores.

O LLVM/clang fica (drivers de vídeo e o HUD de 32 bits) e as vozes ficam (SELECT + FN fala a bateria).
Log em /roms/logs/sistema/limpeza.log.
"""
import glob
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

VERSION = 1
MARK = f"/var/lib/omni36os-update/limpeza-{VERSION}"
SERVICES = ("fn-menu-watcher", "es-status-daemon")
PACKAGES = ("openjdk-21-jre-headless", "default-jre-headless", "rustc", "cargo", "libstd-rust-dev",
            "libstd-rust-1.85", "cmake", "cmake-data", "gcc", "gcc-12", "gcc-14", "gcc-14-aarch64-linux-gnu",
            "gcc-aarch64-linux-gnu", "cpp", "cpp-12", "cpp-14", "cpp-14-aarch64-linux-gnu", "cpp-aarch64-linux-gnu")
PATHS = ("/opt/dsperate", "/usr/local/bin/freej2me.sh", "/usr/local/bin/freej2me_files")
KEEP_LANG = ("pt", "pt_BR", "en", "en_US", "en_GB", "locale.alias")


def done():
    return os.path.exists(MARK)


def log(msg):
    try:
        import omni_logs
        path = omni_logs.path("sistema", "limpeza.log")
    except Exception:
        path = "/tmp/omni36os-limpeza.log"
    with open(path, "a") as f:
        f.write(time.strftime("%d/%m %H:%M:%S ") + msg + "\n")


def free_mb():
    st = os.statvfs("/")
    return st.f_bavail * st.f_frsize // (1 << 20)


def run(stop=lambda: False):
    """Faz a limpeza. stop(): um jogo abriu (para entre as etapas e tenta de novo depois)."""
    if done():
        return
    before = free_mb()
    log(f"início: {before} MB livres")
    for s in SERVICES:
        subprocess.run(["systemctl", "disable", "--now", s], capture_output=True)
        subprocess.run(["systemctl", "mask", s], capture_output=True)
    log("serviços parados e mascarados: " + ", ".join(SERVICES))
    if stop():
        return
    have = subprocess.run(["dpkg-query", "-W", "-f", "${Package}\n", *PACKAGES], capture_output=True,
                          text=True).stdout.split()
    if have:
        env = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}
        sim = subprocess.run(["apt-get", "-s", "purge", *have], capture_output=True, text=True, env=env).stdout
        gone = [l.split()[1] for l in sim.splitlines() if l.startswith(("Purg", "Remv"))]
        extra = [p for p in gone if p not in PACKAGES and p not in ("ant", "ant-optional", "libtool", "libtool-bin",
                                                                     "x11-xserver-utils")]
        if extra:                        # sairia algo fora do previsto: não mexe nos pacotes
            log("pacotes NÃO removidos: levaria junto " + ", ".join(extra))
        else:
            r = subprocess.run(["apt-get", "-y", "purge", *have], capture_output=True, text=True, env=env)
            log(f"apt-get purge ({len(gone)} pacotes): " + ("ok" if r.returncode == 0 else r.stderr.strip()[-300:]))
            if r.returncode:
                return                    # tenta de novo na próxima abertura
    if stop():
        return
    shutil.rmtree("/usr/share/doc", ignore_errors=True)
    os.makedirs("/usr/share/doc", exist_ok=True)
    for d in glob.glob("/usr/share/locale/*") + glob.glob("/usr/share/man/*"):
        name = os.path.basename(d)
        if os.path.isdir(d) and name not in KEEP_LANG and not name.startswith(("man", "pt", "en")):
            shutil.rmtree(d, ignore_errors=True)
    for p in PATHS:
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        elif os.path.exists(p):
            os.remove(p)
    os.makedirs(os.path.dirname(MARK), exist_ok=True)
    with open(MARK, "w") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S\n"))
    log(f"fim: {free_mb()} MB livres ({free_mb() - before} MB a mais)")


if __name__ == "__main__":
    run()
    print(open(MARK).read() if done() else "não concluída (veja limpeza.log)")
