"""Omni36OS — onde ficam os logs: /roms/logs/<função>/ no cartão 1 (EASYROMS), para ler pelo PC
ou pelo app Notas (Notas > Logs do sistema).

  sistema/          launcher.log (saída do launcher), falhas.log (quedas do launcher)
  ports/            port.log (saída do último port), dependencias.log (runtimes baixados)
  teste de ports/   teste_<nome do port>.txt (último relatório do Testar ports)
  pendrive/         pendrive.log (modo pendrive)
  tela/             teste_de_tela.log (escolha da tela, L1+R1)
  rede/             rede_usb.log (rede pelo cabo USB)

Sem o /roms montado (ainda no boot, ou entregue ao PC no modo pendrive) cai em /tmp/omni36os-logs.
Os scripts em shell usam os mesmos caminhos (ver LOGS em launch-direct.sh e usb_pendrive.sh).
"""
import os
import re
import shutil

ROOT = "/roms/logs"
FALLBACK = "/tmp/omni36os-logs"
TESTS = "teste de ports"
FUNCS = ("sistema", "ports", TESTS, "pendrive", "tela", "rede")
NAMES = {"sistema": "Sistema", "ports": "Ports", TESTS: "Teste de ports", "pendrive": "Pendrive",
         "tela": "Tela", "rede": "Rede"}


def root():
    return ROOT if os.path.ismount("/roms") or os.environ.get("OMNI_LOGS_ANY") else FALLBACK


def folder(func):
    """Pasta da função, criada na hora (dono ark, para o PC e o Notas lerem)."""
    d = os.path.join(root(), func)
    try:
        os.makedirs(d, exist_ok=True)
        for p in (os.path.dirname(d), d):
            try:
                os.chown(p, 1000, 1000)
            except OSError:
                pass
    except OSError:
        pass
    return d


def path(func, name):
    return os.path.join(folder(func), name)


def safe(name):
    """Nome de port que serve de nome de arquivo (mesma regra do port_test.sh)."""
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip() or "port"


def test_report(name):
    return path(TESTS, f"teste_{safe(name)}.txt")


def migrate(omni_dir="/opt/omni36os"):
    """Uma vez: traz os logs dos lugares antigos para /roms/logs. Os relatórios do teste de ports
    (logs/<port>/<data>.txt) viram teste_<port>.txt com o mais novo; os antigos saem."""
    if not os.path.ismount("/roms"):
        return
    # o teste de tela roda cedo no boot, às vezes antes do /roms: o que ele gravou no /boot vem para cá
    _append("/boot/omni36os-tela/log.txt", "tela", "teste_de_tela.log")
    mark = os.path.join(ROOT, ".migrado")
    if os.path.exists(mark):
        return
    old = os.path.join(omni_dir, "logs")
    try:
        for d in sorted(os.listdir(old)):
            full = os.path.join(old, d)
            if not os.path.isdir(full):
                continue
            reps = sorted(f for f in os.listdir(full) if f.endswith(".txt"))
            if reps:
                shutil.copyfile(os.path.join(full, reps[-1]), test_report(d))
            shutil.rmtree(full, ignore_errors=True)
    except OSError:
        pass
    for src, func, name in (("/home/ark/usb-disco.log", "pendrive", "pendrive.log"),
                            ("/var/log/omni36os-crash.log", "sistema", "falhas.log")):
        _append(src, func, name)
    try:
        open(mark, "w").close()
    except OSError:
        pass


def _append(src, func, name):
    try:
        if os.path.isfile(src):
            with open(src, "rb") as a, open(path(func, name), "ab") as b:
                b.write(a.read())
            os.remove(src)
    except OSError:
        pass
