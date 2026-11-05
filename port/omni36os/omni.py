#!/usr/bin/env python3
"""Omni36OS — diagnóstico e ajustes do R36S. Só stdlib.

Uso: omni.py <ferramenta> ['{"arg": valor}']   (sem argumentos lista as ferramentas)
"""
import configparser
import glob
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import time

import omni_i18n

DT = "/proc/device-tree"
DSI = "dsi@ff450000"
CATALOG = "/boot/dtb"
DEVICES_INI = f"{CATALOG}/r36_devices.ini"
HOME = "/home/ark"
BACKLIGHT = "/sys/class/backlight/backlight"
CPUFREQ = "/sys/devices/system/cpu/cpufreq/policy0"


def read(path, default=None):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return default


def read_text(path, default="N/A"):
    data = read(path)
    return data.split(b"\x00")[0].decode(errors="replace").strip() if data else default


def write_text(path, value):
    with open(path, "w") as f:
        f.write(str(value))


def save_file(path, value):
    """Grava uma configuração sem risco de ficar pela metade: o R36S apaga quando a bateria
    acaba, e um arquivo truncado perderia a escolha. Escreve ao lado, força ao cartão e troca de
    uma vez (os.replace é atômico). Mantém dono e permissões do arquivo antigo. Não serve para
    /sys e /proc: lá vai write_text."""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    try:
        with open(tmp, "w") as f:
            f.write(value if isinstance(value, str) else str(value))
            f.flush()
            os.fsync(f.fileno())
        try:
            st = os.stat(path)
            os.chown(tmp, st.st_uid, st.st_gid)
            os.chmod(tmp, st.st_mode & 0o7777)
        except OSError:
            pass
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    try:                                   # a troca do nome também precisa chegar ao cartão
        fd = os.open(d, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def clamp_pct(value):
    return max(0, min(100, int(value)))


# --- Device tree ---

def fdt_props(blob, wanted):
    """Lê um DTB e devolve {caminho_do_nó: {prop: bytes}} para os nós em `wanted`.

    `wanted(path)` decide se as propriedades do nó são guardadas.
    """
    magic, _, off_struct, off_strings = struct.unpack_from(">4I", blob, 0)
    if magic != 0xD00DFEED:
        return {}
    pos, stack, nodes = off_struct, [], {}
    while True:
        (token,) = struct.unpack_from(">I", blob, pos)
        pos += 4
        if token == 1:  # BEGIN_NODE
            end = blob.index(b"\x00", pos)
            stack.append(blob[pos:end].decode(errors="replace"))
            pos = (end + 4) & ~3
        elif token == 2:  # END_NODE
            stack.pop()
        elif token == 3:  # PROP
            length, nameoff = struct.unpack_from(">II", blob, pos)
            pos += 8
            path = "/" + "/".join(stack[1:])
            if wanted(path):
                name_end = blob.index(b"\x00", off_strings + nameoff)
                name = blob[off_strings + nameoff:name_end].decode()
                nodes.setdefault(path, {})[name] = blob[pos:pos + length]
            pos = (pos + length + 3) & ~3
        elif token == 4:  # NOP
            continue
        else:  # END
            return nodes


def is_panel_node(path):
    return path.startswith(f"/{DSI}/panel") and path.count("/") == 2


def panel_signature(model, props):
    return {
        "model": model,
        "compatible": props.get("compatible", b"").split(b"\x00")[0].decode(errors="replace"),
        "hash": hashlib.sha256(props.get("panel-init-sequence", b"")).hexdigest(),
    }


def live_panel():
    model = read_text(f"{DT}/model")
    nodes = sorted(glob.glob(f"{DT}/{DSI}/panel*"))
    if not nodes:
        return None
    props = {name: read(f"{nodes[0]}/{name}", b"") for name in ("compatible", "panel-init-sequence")}
    return panel_signature(model, props)


DTB_PACKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dtb")      # catálogos de DTB do dArkOSen que vêm na atualização


def ensure_dtb_catalog():
    """Completa /boot/dtb com o catálogo mais novo do dArkOSen que veio na atualização (dtb/*.tar.xz):
    pastas novas e DTBs que mudaram, mais o r36_devices.ini. Não apaga nada nem mexe no DTB em uso
    (/boot/rk3326-r36s-linux.dtb). Roda uma vez por catálogo (marca /boot/dtb/.omni-catalogo)."""
    import tarfile
    import tempfile
    packs = sorted(glob.glob(os.path.join(DTB_PACKS, "dArkOSen-*.tar.xz")))
    if not packs or not os.path.isdir(CATALOG):
        return ""
    pack = packs[-1]
    name = os.path.basename(pack)
    mark = os.path.join(CATALOG, ".omni-catalogo")
    if read_text(mark, "").strip() == name:
        return ""
    added = changed = 0
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(pack) as tf:
            tf.extractall(tmp, filter="data")
        src = os.path.join(tmp, "dtb")
        for root_dir, _dirs, files in os.walk(src):
            rel = os.path.relpath(root_dir, src)
            dest_dir = os.path.normpath(os.path.join(CATALOG, rel))
            for f in files:
                a, b = os.path.join(root_dir, f), os.path.join(dest_dir, f)
                new = read(a, b"")
                old = read(b, None)
                if old == new:
                    continue
                os.makedirs(dest_dir, exist_ok=True)
                with open(b + ".tmp", "wb") as fh:
                    fh.write(new)
                os.replace(b + ".tmp", b)
                if old is None:
                    added += 1
                else:
                    changed += 1
    with open(mark, "w") as fh:
        fh.write(name + "\n")
    os.sync()
    return f"catálogo de DTB {name}: {added} novos, {changed} atualizados"


def model_variant(model):
    """Variante do aparelho pelo modelo do DTB em uso (r36_devices.ini do dArkOSen); None se o
    modelo não está lá. A tela sozinha não diz: o teste de tela pode ter trazido o painel de outro DTB."""
    if not model or not os.path.exists(DEVICES_INI):
        return None
    ini = configparser.ConfigParser(strict=False, interpolation=None)
    ini.read(DEVICES_INI, encoding="utf-8")
    for sec in ini.sections():
        if sec == model or model.startswith(sec + " ") or sec.startswith(model + " "):
            return ini[sec].get("variant", "unknown")
    return None


def is_clone(model, same):
    """Clone: pelo modelo quando o catálogo o conhece; senão, só se todos os DTBs com a mesma tela forem clone."""
    v = model_variant(model)
    if v is not None:
        return v in ("clone", "soysauce")
    return bool(same) and all(e["variant"] in ("clone", "soysauce") for e in same)


def catalog_panels():
    variants = {}
    if os.path.exists(DEVICES_INI):
        ini = configparser.ConfigParser(strict=False, interpolation=None)
        ini.read(DEVICES_INI, encoding="utf-8")
        variants = {s: ini[s].get("variant", "unknown") for s in ini.sections()}

    for dtb in sorted(glob.glob(f"{CATALOG}/*/*/rk3326-*-linux.dtb")):
        nodes = fdt_props(read(dtb, b""), lambda p: p == "/" or is_panel_node(p))
        panels = [p for p in sorted(nodes) if p != "/"]
        if not panels:
            continue
        model = nodes.get("/", {}).get("model", b"").split(b"\x00")[0].decode(errors="replace")
        entry = panel_signature(model, nodes[panels[0]])
        entry["folder"] = os.path.relpath(os.path.dirname(dtb), CATALOG)
        entry["variant"] = variants.get(os.path.basename(entry["folder"]), entry["folder"].split("/")[0])
        yield entry


def detect_hardware_and_screen(_args=None):
    tr = omni_i18n._
    live = live_panel()
    if not live:
        return f"{tr('ui_hardware_device')}: {read_text(DT + '/model')}\n{tr('ui_hardware_panel')}: {tr('ui_hardware_node_missing')}"

    lines = [
        f"{tr('ui_hardware_device')}: {live['model']}",
        f"{tr('ui_hardware_controller')}: {live['compatible']}",
        f"{tr('ui_hardware_screen_signature')}: {live['hash'][:16]}",
        "",
    ]
    if not os.path.isdir(CATALOG):
        lines.append(tr('ui_hardware_catalog_missing'))
        return "\n".join(lines)

    entries = list(catalog_panels())
    same_screen = [e for e in entries if e["hash"] == live["hash"]]
    exact = [e for e in same_screen if e["model"] == live["model"]]
    # Os DTBs do catálogo costumam ter um sufixo no modelo ("R36S-V21 2024-12-18 2550")
    prefix = [e for e in same_screen if e["model"].startswith(live["model"] + " ")]
    same = [e for e in same_screen if e not in exact and e not in prefix]

    if exact:
        lines.append(tr("ui_hardware_select_model_exact"))
        lines += [f"  {e['folder']}" for e in exact]
    elif prefix:
        lines.append(tr("ui_hardware_select_model_prefix"))
        lines.append(tr("ui_hardware_same_model_screen"))
        lines += [f"  {e['folder']}" for e in prefix]
    elif same:
        lines.append(tr("ui_hardware_model_unlisted"))
        lines += [f"  {e['folder']}" for e in same]
    else:
        lines.append(tr("ui_hardware_custom_dtb"))

    if is_clone(live.get("model", ""), exact or prefix or same):
        lines += ["", tr("ui_hardware_clone_warning")]
    lines += ["", tr("ui_hardware_backup_boot")]
    return "\n".join(lines)


# --- Cartões SD ---

SD_VENDORS = {0x03: "SanDisk"}


def mmc_mounts():
    mounts = {}
    with open("/proc/mounts") as f:
        for line in f:
            dev, mnt = line.split()[:2]
            if dev.startswith("/dev/mmcblk"):
                blk = dev[5:].split("p")[0]
                mounts.setdefault(blk, []).append(mnt.replace("\\040", " "))
    return mounts


def check_microsd_info(_args=None):
    mounts = mmc_mounts()
    lines = []
    for dev in sorted(glob.glob("/sys/block/mmcblk*/device")):
        blk = dev.split("/")[3]
        manfid = int(read_text(f"{dev}/manfid", "0"), 16)
        sectors = int(read_text(f"/sys/block/{blk}/size", "0"))
        lines += [
            f"{blk}:",
            omni_i18n._("tx_sd_maker").format(maker=SD_VENDORS.get(manfid, omni_i18n._("tx_sd_unknown").format(id=manfid))),
            omni_i18n._("tx_sd_name").format(name=read_text(dev + '/name'), date=read_text(dev + '/date')),
            omni_i18n._("tx_sd_size").format(size=sectors * 512 / 1e9),
            omni_i18n._("tx_sd_mounted").format(where=', '.join(mounts.get(blk, ['-']))),
        ]
    return "\n".join(lines) or omni_i18n._("tx_no_card")


def test_microsd_speed(args):
    """Grava e lê 64 MB no ponto de montagem informado (nunca em /tmp, que é RAM)."""
    target = args.get("path", "/roms")
    if not any(target in m for m in mmc_mounts().values()):
        return omni_i18n._("tx_not_sd").format(target=target)
    test_file = os.path.join(target, ".omni_speedtest.bin")
    size_mb = 64
    block = os.urandom(1024 * 1024)
    try:
        start = time.monotonic()
        with open(test_file, "wb") as f:
            for _ in range(size_mb):
                f.write(block)
            f.flush()
            os.fsync(f.fileno())
        write_s = time.monotonic() - start

        write_text("/proc/sys/vm/drop_caches", 3)
        start = time.monotonic()
        with open(test_file, "rb") as f:
            while f.read(1024 * 1024):
                pass
        read_s = time.monotonic() - start
    except OSError as e:
        return omni_i18n._("tx_test_fail").format(error=e)
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

    write_mbs, read_mbs = size_mb / write_s, size_mb / read_s
    verdict = "OK" if write_mbs >= 10 else omni_i18n._("tx_slow_card")
    return omni_i18n._("tx_speed_report").format(
        target=target, size=size_mb, w=write_mbs, r=read_mbs, verdict=verdict)


# --- Sistema ---

def get_system_status(_args=None):
    temp = read_text("/sys/class/thermal/thermal_zone0/temp", "")
    temp_c = f"{int(temp) // 1000}°C" if temp.isdigit() else "N/A"
    bright = int(read_text(f"{BACKLIGHT}/brightness", "0"))
    maxb = int(read_text(f"{BACKLIGHT}/max_brightness", "1")) or 1
    freq = read_text(f"{CPUFREQ}/scaling_cur_freq", "0")
    return omni_i18n._("tx_status").format(
        pct=read_text('/sys/class/power_supply/battery/capacity'), state=read_text('/sys/class/power_supply/battery/status'),
        temp=temp_c, mhz=int(freq) // 1000, gov=read_text(CPUFREQ + '/scaling_governor'),
        bright=round(bright * 100 / maxb), vol=get_volume())


def get_brightness(_args=None):
    maxb = int(read_text(f"{BACKLIGHT}/max_brightness", "1")) or 1
    return round(int(read_text(f"{BACKLIGHT}/brightness", "0")) * 100 / maxb)


def set_screen_brightness(args):
    pct = clamp_pct(args["value"])
    maxb = int(read_text(f"{BACKLIGHT}/max_brightness", "160"))
    write_text(f"{BACKLIGHT}/brightness", max(1, round(pct / 100 * maxb)))
    return omni_i18n._("tx_brightness").format(pct=pct)


def amixer(*args):
    return subprocess.run(["amixer", "-c", "0", *args], capture_output=True, text=True).stdout


def get_volume(_args=None):
    for line in amixer("sget", "Playback").splitlines():
        if "[" in line and "%]" in line:
            return int(line.split("[")[1].split("%")[0])
    return 0


def set_system_volume(args):
    pct = clamp_pct(args["value"])
    amixer("-q", "sset", "Playback", f"{pct}%")
    return f"Volume: {pct}%"


def get_cpu_governors(_args=None):
    return read_text(f"{CPUFREQ}/scaling_available_governors", "").split()


# O ES põe a CPU em "performance" (perfmax) ao abrir qualquer port, o Omni36OS
# inclusive, e o perfnorm volta o modo quando o port fecha. O Omni36OS guarda
# o modo e o limite de frequência em /etc/cpu-settings.conf (o CPU Manager e o
# R36 Tuner usam o mesmo arquivo; o cpu-governor.service o aplica no boot).
# O Omni36OS grava ali também e faz o perfnorm ler dali: um lugar só para tudo.
CPU_CONF = "/etc/cpu-settings.conf"
GPU_CONF = "/etc/gpu-settings.conf"
DMC_CONF = "/etc/dmc-settings.conf"
GOV_PREF = f"{HOME}/.config/omni36os/governor"   # versões até 1.5.0 (migrado)
PERFNORM = "/usr/local/bin/perfnorm"
PERFNORM_ORIG = "echo ondemand > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"
PERFNORM_OLD = ('echo "$(cat /home/ark/.config/omni36os/governor 2>/dev/null || echo ondemand)" '
                "> /sys/devices/system/cpu/cpufreq/policy0/scaling_governor  # Omni36OS")
PERFNORM_SAB = ('echo "$(. /etc/cpu-settings.conf 2>/dev/null; echo ${GOV:-ondemand})" '
                "> /sys/devices/system/cpu/cpufreq/policy0/scaling_governor  # Omni36OS")
GPU_DEV = "/sys/class/devfreq/ff400000.gpu"
CPU_SAFE_MHZ = 1296      # padrão do Omni36OS; acima disso é overclock
GPU_SAFE_MHZ = 520
OC_FLAG = "/etc/omni36os/overclock"   # existe = overclock desbloqueado (aviso + 5 toques em Desempenho)
OC_MAX_TEMP = 70         # °C: não libera overclock acima disso (1º ponto de corte do kernel)
CPU_AUTO_FLAG = "/etc/omni36os/cpu_auto"   # existe = "Limite do processador" em Automático (omni_cpuauto.py)
GPU_AUTO_FLAG = "/etc/omni36os/gpu_auto"   # o mesmo para o "Limite da GPU"


def read_conf(path):
    out = {}
    for line in read_text(path, "").splitlines():
        k, sep, v = line.strip().partition("=")
        if sep and k and not k.startswith("#"):
            out[k.strip()] = v.strip().strip('"')
    return out


def write_conf(path, **values):
    """Troca só as chaves pedidas, mantendo as outras linhas do arquivo."""
    lines, seen = [], set()
    for line in read_text(path, "").splitlines():
        k = line.split("=", 1)[0].strip()
        if k in values:
            lines.append(f"{k}={values[k]}")
            seen.add(k)
        elif line.strip():
            lines.append(line)
    lines += [f"{k}={v}" for k, v in values.items() if k not in seen]
    write_text(path, "\n".join(lines) + "\n")


def temp_c():
    t = read_text("/sys/class/thermal/thermal_zone0/temp", "0")
    return int(t) // 1000 if t.isdigit() else 0


def get_preferred_governor(_args=None):
    gov = read_conf(CPU_CONF).get("GOV")
    if not gov and os.path.exists(GOV_PREF):
        gov = read_text(GOV_PREF)
    return gov or "ondemand"


def patch_perfnorm():
    """Faz o perfnorm ler o modo de /etc/cpu-settings.conf (backup em perfnorm.omni36os-bak)."""
    text = (read(PERFNORM) or b"").decode()
    if PERFNORM_SAB in text:
        return True
    old = PERFNORM_OLD if PERFNORM_OLD in text else PERFNORM_ORIG if PERFNORM_ORIG in text else None
    if not old:
        return False
    if not os.path.exists(PERFNORM + ".omni36os-bak"):
        shutil.copy2(PERFNORM, PERFNORM + ".omni36os-bak")
    write_text(PERFNORM, text.replace(old, PERFNORM_SAB, 1))
    return True


def migrate_cpu_settings():
    """Versões antigas do Omni36OS guardavam o modo em ~/.config/omni36os/governor."""
    if os.path.exists(GOV_PREF):
        if "GOV" not in read_conf(CPU_CONF):
            write_conf(CPU_CONF, GOV=read_text(GOV_PREF))
        os.remove(GOV_PREF)
    if PERFNORM_OLD in (read(PERFNORM) or b"").decode():
        patch_perfnorm()


def set_preferred_governor(args):
    name = args["governor"]
    if name not in get_cpu_governors():
        return omni_i18n._("tx_gov_unavailable").format(options=', '.join(get_cpu_governors()))
    write_conf(CPU_CONF, GOV=name)
    if not patch_perfnorm():
        return omni_i18n._("tx_mode_saved").format(name=name)
    return omni_i18n._("tx_cpu_on_return").format(name=name)


def relax_clocks(_args=None):
    """Menu = mínimo: CPU, GPU e memória no modo economia (a menor frequência) enquanto o Omni36OS
    está na tela. Um menu não precisa de mais, e assim o console esfria e a bateria rende. Os limites
    de Desempenho só valem nos ports: o launch-direct.sh põe tudo em desempenho até eles ao abrir um
    port, e o Omni36OS volta ao mínimo quando o port fecha. Sem o modo economia, o mais próximo."""
    _governors(((f"{CPUFREQ}/scaling_governor", ("powersave", "conservative", "ondemand")),
                (f"{GPU_DEV}/governor", ("powersave", "simple_ondemand")),
                ("/sys/class/devfreq/dmc/governor", ("powersave", "dmc_ondemand", "simple_ondemand"))))


def video_clocks(_args=None):
    """Vídeo tocando: o ffmpeg decodifica no processador, então CPU e memória sobem conforme a carga
    (sem passar dos limites de Desempenho). relax_clocks volta ao mínimo quando o vídeo fecha."""
    _governors(((f"{CPUFREQ}/scaling_governor", ("schedutil", "ondemand", "performance")),
                ("/sys/class/devfreq/dmc/governor", ("dmc_ondemand", "simple_ondemand", "performance"))))


def _governors(pairs):
    """O primeiro governador de cada lista que o sistema tiver."""
    for path, govs in pairs:
        try:
            avail = read_text(path.rsplit("/", 1)[0] + ("/scaling_available_governors" if "cpufreq" in path
                                                         else "/available_governors"), "").split()
            gov = next((g for g in govs if g in avail), None)
            if gov:
                write_text(path, gov)
        except OSError:
            pass


# --- Overclock (CPU e GPU) ---

def oc_unlocked(_args=None):
    return os.path.exists(OC_FLAG)


def unlock_oc(_args=None):
    os.makedirs(os.path.dirname(OC_FLAG), exist_ok=True)
    write_text(OC_FLAG, time.strftime("%d/%m/%Y %H:%M") + "\n")


def lock_oc(_args=None):
    """Bloqueia de novo: tira a marca e volta os dois limites ao padrão."""
    try:
        os.remove(OC_FLAG)
    except FileNotFoundError:
        pass
    if not cpu_auto():                   # no Automático o teto já desce sozinho para o padrão
        set_cpu_max({"mhz": CPU_SAFE_MHZ})
    if not gpu_auto():
        set_gpu_max({"mhz": GPU_SAFE_MHZ})
    return omni_i18n._("tx_oc_locked_limits")


def apply_limits(_args=None):
    """Limites de Desempenho no hardware (fim do boot: até lá o omni36os-turbo deixa tudo no máximo).
    Bloqueado, nada passa do padrão, mesmo que a configuração diga outra coisa."""
    cpu = auto_ceiling() if cpu_auto() else int(read_conf(CPU_CONF).get("FREQ", CPU_SAFE_MHZ * 1000)) // 1000
    gpu = gpu_auto_ceiling() if gpu_auto() else int(read_conf(GPU_CONF).get("FREQ", GPU_SAFE_MHZ * 1000000)) // 1000000
    if not oc_unlocked():
        cpu, gpu = min(cpu, CPU_SAFE_MHZ), min(gpu, GPU_SAFE_MHZ)
    for path, val in ((f"{CPUFREQ}/scaling_max_freq", cpu * 1000), (f"{GPU_DEV}/max_freq", gpu * 1000000)):
        try:
            write_text(path, val)
        except OSError:
            pass


def cpu_freqs(_args=None):
    """Opções do "Limite do processador": 0 é Automático, depois os limites fixos."""
    top = int(read_text(f"{CPUFREQ}/cpuinfo_max_freq", "0")) // 1000
    if not oc_unlocked():
        top = min(top, CPU_SAFE_MHZ)
    avail = [int(f) // 1000 for f in read_text(f"{CPUFREQ}/scaling_available_frequencies", "").split()]
    return [0] + ([f for f in sorted(set(avail)) if CPU_SAFE_MHZ <= f <= top] or [CPU_SAFE_MHZ])


def cpu_auto(_args=None):
    return os.path.exists(CPU_AUTO_FLAG)


def auto_ceiling():
    """Teto do Automático: com overclock desbloqueado, tudo o que o processador tem; bloqueado
    (ou quente demais para overclock), o padrão."""
    top = int(read_text(f"{CPUFREQ}/cpuinfo_max_freq", "0")) // 1000 or CPU_SAFE_MHZ
    if not oc_unlocked() or temp_c() >= OC_MAX_TEMP:
        top = min(top, CPU_SAFE_MHZ)
    return top


def auto_steps():
    """Degraus do Automático: do mínimo do processador até o teto."""
    top = auto_ceiling()
    avail = sorted({int(f) // 1000 for f in read_text(f"{CPUFREQ}/scaling_available_frequencies", "").split()})
    return [f for f in avail if f <= top] or [top]


def get_cpu_max(_args=None):
    if cpu_auto():
        return 0
    return int(read_text(f"{CPUFREQ}/scaling_max_freq", "0")) // 1000


def set_cpu_max(args):
    mhz = int(args["mhz"])
    if mhz == 0:
        os.makedirs(os.path.dirname(CPU_AUTO_FLAG), exist_ok=True)
        write_text(CPU_AUTO_FLAG, "1\n")
        write_text(f"{CPUFREQ}/scaling_max_freq", auto_ceiling() * 1000)
        return omni_i18n._("tx_cpu_auto")
    if mhz > CPU_SAFE_MHZ and not oc_unlocked():
        return omni_i18n._("tx_oc_locked")
    if mhz not in cpu_freqs():
        return omni_i18n._("tx_freq_unavailable").format(mhz=mhz)
    if mhz > CPU_SAFE_MHZ and temp_c() >= OC_MAX_TEMP:
        return omni_i18n._("tx_too_hot").format(temp=temp_c(), limit=OC_MAX_TEMP)
    try:
        os.remove(CPU_AUTO_FLAG)
    except FileNotFoundError:
        pass
    write_conf(CPU_CONF, FREQ=mhz * 1000)
    write_text(f"{CPUFREQ}/scaling_max_freq", mhz * 1000)
    return omni_i18n._("tx_cpu_upto").format(mhz=mhz) + (" (overclock)" if mhz > CPU_SAFE_MHZ else "")


def gpu_freqs(_args=None):
    """Opções do "Limite da GPU": 0 é Automático, depois os limites fixos."""
    top = 10 ** 6 if oc_unlocked() else GPU_SAFE_MHZ
    return [0] + sorted(int(f) // 1000000 for f in read_text(f"{GPU_DEV}/available_frequencies", "").split()
                        if int(f) // 1000000 <= top)


def gpu_auto(_args=None):
    return os.path.exists(GPU_AUTO_FLAG)


def gpu_auto_ceiling():
    """Teto do Automático da GPU: 520 MHz bloqueado (ou quente demais), tudo desbloqueado."""
    top = max((int(f) // 1000000 for f in read_text(f"{GPU_DEV}/available_frequencies", "").split()),
              default=GPU_SAFE_MHZ)
    if not oc_unlocked() or temp_c() >= OC_MAX_TEMP:
        top = min(top, GPU_SAFE_MHZ)
    return top


def gpu_auto_steps():
    top = gpu_auto_ceiling()
    avail = sorted({int(f) // 1000000 for f in read_text(f"{GPU_DEV}/available_frequencies", "").split()})
    return [f for f in avail if f <= top] or [top]


def gpu_load():
    """Ocupação da GPU em % ("37@400000000Hz" no devfreq), -1 se não der para ler."""
    try:
        return int(read_text(f"{GPU_DEV}/load", "").split("@")[0])
    except ValueError:
        return -1


def get_gpu_max(_args=None):
    if gpu_auto():
        return 0
    return int(read_text(f"{GPU_DEV}/max_freq", "0")) // 1000000


def set_gpu_max(args):
    mhz = int(args["mhz"])
    if mhz == 0:
        os.makedirs(os.path.dirname(GPU_AUTO_FLAG), exist_ok=True)
        write_text(GPU_AUTO_FLAG, "1\n")
        write_text(f"{GPU_DEV}/max_freq", gpu_auto_ceiling() * 1000000)
        return omni_i18n._("tx_gpu_auto")
    if mhz > GPU_SAFE_MHZ and not oc_unlocked():
        return omni_i18n._("tx_oc_locked")
    if mhz not in gpu_freqs():
        return omni_i18n._("tx_freq_unavailable").format(mhz=mhz)
    if mhz > GPU_SAFE_MHZ and temp_c() >= OC_MAX_TEMP:
        return omni_i18n._("tx_too_hot").format(temp=temp_c(), limit=OC_MAX_TEMP)
    try:
        os.remove(GPU_AUTO_FLAG)
    except FileNotFoundError:
        pass
    write_conf(GPU_CONF, FREQ=mhz * 1000000)
    write_text(f"{GPU_DEV}/max_freq", mhz * 1000000)
    return omni_i18n._("tx_gpu_upto").format(mhz=mhz) + (" (overclock)" if mhz > GPU_SAFE_MHZ else "")


def zram_facts(_args=None):
    size = read_text("/sys/block/zram0/disksize", "0")
    stat = read_text("/sys/block/zram0/mm_stat", "").split()
    return {"zram_mb": int(size) // 1048576 if size.isdigit() else 0,
            "zram_usado_mb": int(stat[0]) // 1048576 if stat else 0}


# --- Serviços do sistema ---

# Falhas conhecidas: o que significam e se o Omni36OS sabe consertar.
KNOWN_FAILS = {
    "dmc-governor.service": ("tx_fail_dmc", "fix_dmc"),
    "systemd-remount-fs.service": ("tx_fail_remount", None),
}


def failed_services(_args=None):
    r = subprocess.run(["systemctl", "--failed", "--no-legend", "--plain"], capture_output=True, text=True)
    return [line.split()[0] for line in r.stdout.splitlines() if line.strip()]


def fix_dmc(_args=None):
    freqs = sorted(int(f) for f in read_text("/sys/class/devfreq/dmc/available_frequencies", "").split())
    if not freqs:
        return omni_i18n._("tx_no_ram_freq")
    write_conf(DMC_CONF, FREQ=freqs[-1])
    subprocess.run(["systemctl", "reset-failed", "dmc-governor.service"], capture_output=True)
    r = subprocess.run(["systemctl", "restart", "dmc-governor.service"], capture_output=True, text=True)
    if r.returncode:
        return omni_i18n._("tx_fix_failed").format(error=r.stderr.strip() or omni_i18n._("tx_service_failed_again"))
    return omni_i18n._("tx_ram_fixed").format(mhz=freqs[-1] // 1000000)


# --- Espaço e limpeza ---

def disk_facts(_args=None):
    out = {}
    for name, path in (("sistema", "/"), ("roms", "/roms"), ("jogos", "/roms2")):
        if path != "/" and not os.path.ismount(path):
            continue
        u = shutil.disk_usage(path)
        out[name] = {"livre_gb": round(u.free / 1e9, 1), "usado_gb": round(u.used / 1e9, 1),
                     "uso_pct": round(100 * u.used / u.total)}
    return out


MAC_JUNK = (".DS_Store", ".Trashes", ".Spotlight-V100", ".fseventsd")


def mac_junk(roots=("/roms", "/roms2")):
    """Arquivos que o macOS cria ao copiar: ._nome (resource forks) e pastas de índice.
    O find é bem mais rápido que os.walk nos cartões cheios do R36S."""
    roots = [r for r in roots if os.path.ismount(r)]
    if not roots:
        return []
    names = []
    for n in MAC_JUNK:
        names += ["-name", n, "-o"]
    r = subprocess.run(["find", *roots, "(", *names, "-name", "._*", ")", "-prune", "-print"],
                       capture_output=True, text=True)
    return [p for p in r.stdout.splitlines() if p]


def clean_mac_junk(_args=None):
    junk = mac_junk()
    for path in junk:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                os.remove(path)
            except OSError:
                pass
    os.sync()
    return omni_i18n._("tx_mac_removed").format(count=len(junk)) if junk else omni_i18n._("tx_mac_none")


# --- Verificação de cartão (roda no boot, com o cartão desmontado) ---

# O Omni36OS roda /boot/recovery.sh no boot (recovery-check.service) e os scripts
# de scan se apagam ao terminar. Os logs ficam em /boot.
SCANS = {"roms2": ("/usr/local/bin/Scan_SD2.sh", "/boot/sd2_scan.log", "SD2 scan result:"),
         "roms": ("/usr/local/bin/Scan_SD1p3.sh", "/boot/sd1p3_scan.log", "SD1p3 scan result:")}


def schedule_scan(args):
    # sem segundo cartão, os jogos ficam na partição /roms do cartão do sistema
    src, _log, _ = SCANS[args.get("part") or ("roms2" if os.path.ismount("/roms2") else "roms")]
    if not os.path.exists(src):
        return omni_i18n._("tx_no_checker")
    # Sem o "umount -l" do original: desmontar "preguiçoso" deixa a partição em uso, e o fsck -y
    # numa partição em uso pode estragar o cartão. Se não desmontar, o script não repara (só registra).
    with open(src) as f:
        script = f.read().replace(' || umount -l "$MP" 2>>"$LOG_FILE"', "")
    save_file("/boot/recovery.sh", script)
    os.chmod("/boot/recovery.sh", 0o755)
    os.sync()
    subprocess.Popen(["sh", "-c", "sleep 2; reboot"])
    return omni_i18n._("tx_rebooting_check")


def last_scan(_args=None):
    out = {}
    for part, (_src, log, marker) in SCANS.items():
        text = read_text(log, "")
        res = next((ln.split(":", 1)[1].strip() for ln in text.splitlines() if ln.startswith(marker)), None)
        if res:
            out[part] = {"resultado": res, "quando": time.strftime("%d/%m/%Y", time.localtime(os.path.getmtime(log)))}
    return out


# --- Tela: gamma e LED ---

GAMMA_CONF = "/etc/gamma-settings.conf"


def get_gamma(_args=None):
    cur = read_text("/dev/shm/CURRENT_GAMMA", "") or read_conf(GAMMA_CONF).get("GAMMA", "1.0")
    try:
        return round(float(cur), 1)
    except ValueError:
        return 1.0


def set_gamma(args):
    g = round(min(1.8, max(0.5, float(args["value"]))), 1)
    tone = read_text("/dev/shm/CURRENT_TONE", "") or read_conf(GAMMA_CONF).get("TONE", "")
    cmd = ["/usr/local/bin/gamma", "-s", str(g)] + (["-t", tone] if tone else [])
    subprocess.run(cmd, capture_output=True)
    write_conf(GAMMA_CONF, GAMMA=g)         # o gamma-persist.service aplica no boot
    write_text("/dev/shm/CURRENT_GAMMA", g)  # e as teclas de atalho continuam daqui
    os.chmod("/dev/shm/CURRENT_GAMMA", 0o666)
    return f"Gamma {g}"


LED_GPIO = "/sys/class/gpio/gpio77/value"
LED_FIX = "/usr/local/bin/fix_power_led"


def get_led(_args=None):
    return "vermelho" if read(LED_FIX) == read(LED_FIX + ".red") else "verde"


def set_led(args):
    """Igual aos scripts Change LED to Red/Green do Omni36OS, sem reiniciar o ES."""
    color = args["color"]
    suf = {"vermelho": "red", "verde": "green"}[color]
    if not os.path.exists(f"{LED_FIX}.{suf}"):
        return omni_i18n._("tx_no_led")
    if not os.path.exists("/sys/class/gpio/gpio77"):
        write_text("/sys/class/gpio/export", "77")
        write_text("/sys/class/gpio/gpio77/direction", "out")
    write_text(LED_GPIO, "1" if suf == "red" else "0")
    shutil.copy(f"{LED_FIX}.{suf}", LED_FIX)                       # cor no boot
    warn = "/usr/local/bin/batt_life_warning.py"
    if os.path.exists(f"{warn}.{suf}"):
        shutil.copy(f"{warn}.{suf}", warn)                         # pisca com bateria baixa
        subprocess.run(["systemctl", "restart", "batt_led"], capture_output=True)
    return f"LED {color}"


# --- Teste de ports ---

OMNI_DIR = os.path.dirname(os.path.abspath(__file__))
PORT_DIRS = ("/roms2/ports", "/roms/ports")
PORT_RESULTS = os.path.join(OMNI_DIR, "logs", "resultados.txt")
TEST_RESULT = "/tmp/omni36os-test-result"


ES_SYSTEMS = "/etc/emulationstation/es_systems.cfg"


def es_ports_dir():
    """Pasta de ports que o ES mostra. O Omni36OS deixa os jogos em /roms (cartão do
    sistema) ou /roms2 (segundo cartão), e o "Switch to SD2" troca isso no
    es_systems.cfg; a fonte da verdade é o <path> do sistema "ports"."""
    text = read_text(ES_SYSTEMS, "")
    for block in text.split("<system>")[1:]:
        if "<name>ports</name>" in block and "<path>" in block:
            return block.split("<path>", 1)[1].split("</path>", 1)[0].strip().rstrip("/")
    return "/roms2/ports" if os.path.ismount("/roms2") else "/roms/ports"


# De onde os jogos e ports são lidos: roms (cartão do sistema), roms2 (segundo cartão) ou ambos.
GAME_SOURCE = f"{HOME}/.config/omni36os/fonte_jogos"
GAME_SOURCES = ("roms", "roms2", "ambos")


def get_game_source(_args=None):
    v = read_text(GAME_SOURCE, "").strip()
    return v if v in GAME_SOURCES else "roms"


CARD2 = "/dev/mmcblk1p1"


def card2_gone():
    """Cartão 2 tirado sem ejetar: o /roms2 continua "montado" sem aparelho. Solta (umount -l) para
    o sistema todo deixar de ver o ROMS2. Chamado ao ler a biblioteca e a página Cartões."""
    if os.path.ismount("/roms2") and not os.path.exists(CARD2):
        subprocess.run(["umount", "-l", "/roms2"], capture_output=True)
        return True
    return False


CARD2_MARK = "/run/omni36os-cartao2"      # "montado" ou "ejetado": dura até o boot (sobrevive aos jogos)


def card2_pulled():
    """O cartão 2 saiu sem Ejetar desde a última olhada? (o systemd desmonta sozinho quando o aparelho
    some, então vale a marca: estava montado, não foi ejetado e agora não está). Uma resposta por retirada."""
    try:
        with open(CARD2_MARK) as f:
            mark = f.read().strip()
    except OSError:
        mark = ""
    if os.path.ismount("/roms2") and os.path.exists(CARD2):
        if mark != "montado":
            write_text(CARD2_MARK, "montado")
        return False
    card2_gone()
    if mark == "montado" and not os.path.ismount("/roms2"):
        write_text(CARD2_MARK, "fora")
        return True
    return False


def card2_state():
    """"montado", "fora" (cartão no slot, desmontado) ou "sem" (nenhum cartão 2)."""
    card2_gone()
    if os.path.ismount("/roms2"):
        return "montado"
    return "fora" if os.path.exists(CARD2) else "sem"


def card2_eject(_args=None):
    """Cartões > Ejetar cartão 2: grava o que falta e desmonta, para tirar sem desligar."""
    if not os.path.ismount("/roms2"):
        return omni_i18n._("tx_card2_unmounted")
    os.sync()
    # só o que vem do cartão 2: o /opt/system/Tools (PortMaster) é bind de /roms/tools, do cartão 1, e fica
    with open("/proc/mounts") as f:
        extra = [l.split()[1] for l in f if l.split()[0] == CARD2 and l.split()[1] != "/roms2"]
    extra += ["/roms/ports"] if os.path.ismount("/roms/ports") else []     # bind de port do cartão 2
    for m in extra:
        subprocess.run(["umount", m], capture_output=True)
    # o compartilhamento de rede (Samba) segura o cartão enquanto um PC está conectado: para e volta depois
    smb = subprocess.run(["systemctl", "is-active", "--quiet", "smbd"]).returncode == 0
    if smb:
        subprocess.run(["systemctl", "stop", "smbd"], capture_output=True)
    r = subprocess.run(["umount", "/roms2"], capture_output=True, text=True)
    if smb:
        subprocess.run(["systemctl", "start", "smbd"], capture_output=True)
    if r.returncode:
        busy = subprocess.run(["fuser", "-m", "/roms2"], capture_output=True, text=True).stdout.split()
        names = sorted({os.path.basename(cmdline_of(p)) for p in busy if cmdline_of(p)})[:3]
        return omni_i18n._("tx_card2_busy").format(names=f" ({', '.join(names)})" if names else "")
    tools_back()
    os.sync()
    try:
        write_text(CARD2_MARK, "ejetado")
    except OSError:
        pass
    return omni_i18n._("tx_card2_ejected")


def card2_mount(_args=None):
    """Cartões > Montar cartão 2: monta em /roms2 (mesmas opções do launch-direct.sh)."""
    if os.path.ismount("/roms2"):
        return omni_i18n._("tx_card2_mounted_already")
    if not os.path.exists(CARD2):
        return omni_i18n._("tx_card2_none")
    fs = subprocess.run(["lsblk", "-no", "FSTYPE", CARD2], capture_output=True, text=True).stdout.strip()
    if not fs:
        return omni_i18n._("tx_card2_nopart")
    os.makedirs("/roms2", exist_ok=True)
    if fs == "ext4":
        cmd = ["mount", "-t", "ext4", "-o", "noatime", CARD2, "/roms2"]
    else:
        cmd = ["mount", "-t", "ntfs-3g" if fs == "ntfs" else fs, "-o",
               "umask=0000,iocharset=utf8,uid=1000,gid=1000,noatime", CARD2, "/roms2"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        return omni_i18n._("tx_mount_error").format(error=(r.stderr or '').strip()[:80])
    tools_back()
    return omni_i18n._("tx_card2_mounted")


def tools_back():
    """O PortMaster fica em /opt/system/Tools (bind do fstab): sem ele, nenhum port abre."""
    if not os.path.ismount("/opt/system/Tools"):
        subprocess.run(["mount", "/opt/system/Tools"], capture_output=True)


def cmdline_of(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().split(b"\0")[0].decode(errors="replace")
    except OSError:
        return ""


def game_roots():
    """Raízes valendo agora; /roms2 só entra se estiver montado."""
    card2_gone()
    want = {"roms": ["/roms"], "roms2": ["/roms2"], "ambos": ["/roms", "/roms2"]}[get_game_source()]
    got = [r for r in want if r == "/roms" or os.path.ismount(r)]
    return got or ["/roms"]             # escolheu ROMS2 e ele saiu: volta ao ROMS


def set_game_source(args):
    v = args.get("source")
    if v not in GAME_SOURCES:
        return omni_i18n._("tx_bad_option")
    write_text(GAME_SOURCE, v + "\n")
    try:
        os.chown(GAME_SOURCE, 1000, 1000)
    except OSError:
        pass
    if v != "roms" and not os.path.ismount("/roms2"):
        return omni_i18n._("tx_saved_no_roms2")
    return "ok"


def port_groups(_args=None):
    """Ports das pastas escolhidas em "Origem dos jogos", sem o próprio Omni36OS."""
    out = []
    for root in game_roots():
        d = f"{root}/ports"
        if not os.path.isdir(d):
            continue
        ports = sorted((p for p in glob.glob(f"{d}/*.sh") + glob.glob(f"{d}/*.SH")
                        if os.path.basename(p) != "Omni36OS.sh"), key=lambda p: os.path.basename(p).lower())
        card = omni_i18n._("tx_games_card") if root == "/roms2" else omni_i18n._("tx_system_card_l")
        if ports:
            out.append({"dir": d, "label": f"{d} ({card})", "es": True, "ports": ports})
    return out


def list_ports(_args=None):
    return [p for g in port_groups() for p in g["ports"]]


def port_results(_args=None):
    """nome -> (resultado, data, segundos), do último teste de cada port."""
    out = {}
    for line in read_text(PORT_RESULTS, "").splitlines():
        parts = line.split("|")
        if len(parts) == 4:
            out[parts[0]] = (parts[1], parts[2], parts[3])
    return out


# Avisos limpos: "nome|data" de falhas já vistas. Elas somem do alerta do card,
# mas o resultado continua na lista; um teste novo (outra data) volta a avisar.
PORT_ACKS = os.path.join(OMNI_DIR, "logs", "avisos_limpos.txt")


def port_acks(_args=None):
    return set(read_text(PORT_ACKS, "").splitlines())


def clear_port_alerts(_args=None):
    fails = [f"{n}|{r[1]}" for n, r in port_results().items() if r[0] == "falhou"]
    if not fails:
        return omni_i18n._("tx_no_fail_notice")
    os.makedirs(os.path.dirname(PORT_ACKS), exist_ok=True)
    write_text(PORT_ACKS, "\n".join(sorted(set(fails))) + "\n")
    return omni_i18n._("tx_notices_cleared").format(count=len(fails))


def last_test(_args=None):
    """Resultado do teste que acabou de rodar (o Omni36OS.sh reabre o Omni36OS depois)."""
    lines = read_text(TEST_RESULT, "").splitlines()
    if len(lines) < 3:
        return None
    os.remove(TEST_RESULT)
    return {"nome": lines[0], "resultado": lines[1], "segundos": lines[2],
            "relatorio": lines[3] if len(lines) > 3 else ""}


def test_port(args):
    path = args["path"]
    if path not in list_ports():
        return omni_i18n._("tx_port_not_found")
    write_text(HANDOFF, "test:" + path)
    return "ok"


# Launcher como shell do sistema (Omni36OS sem ES): sempre instalado junto do sistema
SHELL_UNIT = "/etc/systemd/system/multi-user.target.wants/omni36os-launcher.service"
SHELL = os.path.exists(SHELL_UNIT)
HOTKEY_UNIT = "/etc/systemd/system/omni36os-atalho.service"


def _systemctl(*args):
    return subprocess.run(["systemctl", *args], capture_output=True, text=True)


ATALHOS_CONF = f"{HOME}/.config/omni36os/atalhos.json"   # ver omni_atalho.py
# Restart=always sem limite: um erro no boot não pode deixar o console sem os atalhos até reiniciar
HOTKEY_UNIT_TEXT = ("[Unit]\nDescription=Omni36OS: atalhos com FN durante os jogos\nAfter=omni36os-launcher.service\n"
                    "StartLimitIntervalSec=0\n\n"
                    f"[Service]\nExecStart=/usr/bin/python3 {OMNI_DIR}/omni_atalho.py\nRestart=always\nRestartSec=2\n"
                    "Nice=10\n\n[Install]\nWantedBy=multi-user.target\n")


def get_atalhos(_args=None):
    import omni_combos
    try:
        with open(ATALHOS_CONF) as f:
            return omni_combos.normalize(json.load(f))
    except (OSError, ValueError):
        return omni_combos.defaults()


def set_atalho(args):
    """Guarda uma escolha de Sistema > Atalhos e avisa o serviço (ele relê na hora)."""
    c = get_atalhos()
    if args["key"] not in c:
        return omni_i18n._("tx_bad_hotkey")
    c[args["key"]] = args["value"]
    save_file(ATALHOS_CONF, json.dumps(c))
    if read_text(HOTKEY_UNIT, "") != HOTKEY_UNIT_TEXT:      # unidade antiga (do tempo do ES) ou faltando
        write_text(HOTKEY_UNIT, HOTKEY_UNIT_TEXT)
        _systemctl("daemon-reload")
        _systemctl("enable", "omni36os-atalho.service")
        _systemctl("restart", "omni36os-atalho.service")
    else:
        _systemctl("kill", "-s", "HUP", "omni36os-atalho.service")
    return omni_i18n._("tx_hotkeys_updated")


def power(args):
    """Reiniciar, desligar ou suspender (menu Energia). Como o finish.sh do Omni36OS: o ES
    fecha (grava as listas), o /boot é desmontado e tudo é gravado antes; num job à parte do
    systemd, porque parar o ES (o hub) fecha o Omni36OS junto."""
    what = args["what"]
    if what not in ("reboot", "poweroff", "suspend"):
        return omni_i18n._("tx_bad_option")
    os.sync()
    if what == "suspend":
        subprocess.Popen(["systemctl", "suspend"])
        return "ok"
    # a despedida vai para o framebuffer antes de o launcher fechar: é ela (e não a boas-vindas do
    # boot) que o vídeo mostra no instante em que ele solta a tela
    tela = f"/usr/local/bin/omni36os-tela {'reiniciando' if what == 'reboot' else 'desligando'}"
    subprocess.run(["systemd-run", "--no-block", "--collect", "--unit", f"omni36os-power-{int(time.time())}",
                    "bash", "-c", f"{tela}; systemctl stop emulationstation omni36os-launcher; {tela}; "
                                  "mountpoint -q /boot && umount /boot; "
                                  f"sync; sleep 1; systemctl {what}"])
    return "ok"


# --- Botão de power ---

# No toque curto do power o ogage do Omni36OS chama o pause.sh (suspende, ou desliga com a
# opção "trocar power e suspender"; o finish.sh é de outro gatilho e fica como está). Ligado,
# o pause.sh passa antes pelo power_button.py (menu de energia; FN + power = pânico); se ele
# falhar ou não tratar o toque, o original (guardado em pause.sh.omni36os-orig) roda como sempre.
PAUSE = "/usr/local/bin/pause.sh"
PAUSE_ORIG = PAUSE + ".omni36os-orig"
FINISH = "/usr/local/bin/finish.sh"          # a 1.4.0 trocava este por engano
FINISH_ORIG = FINISH + ".omni36os-orig"
POWER_MARK = "# Omni36OS: botão de power"
POWER_WRAP = f"""#!/bin/bash
{POWER_MARK}. Original em {PAUSE_ORIG}; Controles > Botão de power desfaz.
H={OMNI_DIR}/power_button.py
if [ -f "$H" ] && timeout 8 python3 -B "$H"; then exit 0; fi
exec bash {PAUSE_ORIG}
"""
POWER_NAMES = {"desligar": "Como no Omni36OS", "menu": "Menu de energia"}


def _unwrap(path, orig):
    if POWER_MARK in read_text(path, "") and os.path.exists(orig):
        shutil.copy2(orig, path + ".tmp")
        os.replace(path + ".tmp", path)
        os.remove(orig)


def get_power_button(_args=None):
    return "menu" if POWER_MARK in read_text(PAUSE, "") else "desligar"


def set_power_button(args):
    mode = args["mode"]
    if mode not in POWER_NAMES:
        return omni_i18n._("tx_bad_mode")
    _unwrap(FINISH, FINISH_ORIG)
    cur = read_text(PAUSE, "")
    if mode == "menu":
        if POWER_MARK not in cur:
            if not cur.startswith("#!"):
                return omni_i18n._("tx_no_pause")
            shutil.copy2(PAUSE, PAUSE_ORIG)
        if cur != POWER_WRAP:                # também quando o Omni36OS muda de pasta
            write_text(PAUSE + ".tmp", POWER_WRAP)
            os.chmod(PAUSE + ".tmp", 0o755)
            os.replace(PAUSE + ".tmp", PAUSE)
        return omni_i18n._("tx_power_menu")
    _unwrap(PAUSE, PAUSE_ORIG)
    return omni_i18n._("tx_power_omni")


# --- Troca de botões (Controles) ---

# A e B: o b_swap.sh do dArkOSen (alterna a cada chamada; marca /var/cache/Switch_AB) muda PortMaster,
# teclado virtual, ES e companhia; o Omni36OS lê a mesma marca. X e Y não existiam no dArkOSen: o
# Omni36OS troca X e Y no mapa do controle do PortMaster (é o que os ports usam) e marca
# /var/cache/Switch_XY. ensure_swap_xy() refaz a troca se uma atualização do PortMaster trouxer o
# mapa original de volta.
AB_FLAG, XY_FLAG = "/var/cache/Switch_AB", "/var/cache/Switch_XY"
B_SWAP = "/usr/local/bin/b_swap.sh"
PAD_GUID = "190000004b4800000011000000010000,"
PM_DBS = ("/roms/tools/PortMaster/gamecontrollerdb.txt", "/roms2/tools/PortMaster/gamecontrollerdb.txt")


def get_swap_ab(_args=None):
    return os.path.exists(AB_FLAG)


def set_swap_ab(args):
    on = bool(args["on"])
    if on != get_swap_ab():
        if not os.path.exists(B_SWAP):
            return omni_i18n._("tx_no_ab")
        subprocess.run(["bash", B_SWAP], capture_output=True, timeout=30)
    return omni_i18n._("tx_ab_swapped") if get_swap_ab() else omni_i18n._("tx_ab_default")


def get_swap_xy(_args=None):
    return os.path.exists(XY_FLAG)


def _pm_xy(swapped):
    """No mapa do PortMaster, X e Y do R36S ficam b2/b3 (padrão) ou b3/b2 (trocados)."""
    want = {"x": "b3", "y": "b2"} if swapped else {"x": "b2", "y": "b3"}
    for db in PM_DBS:
        text = read_text(db, "")
        if PAD_GUID not in text:
            continue
        lines = text.splitlines(keepends=True)
        for k, ln in enumerate(lines):
            if ln.startswith(PAD_GUID):
                parts = ln.rstrip("\n").split(",")
                for j, p in enumerate(parts):
                    key, _, _val = p.partition(":")
                    if key in want and _:
                        parts[j] = f"{key}:{want[key]}"
                lines[k] = ",".join(parts) + ("\n" if ln.endswith("\n") else "")
        new = "".join(lines)
        if new != text:
            write_text(db + ".tmp", new)
            os.replace(db + ".tmp", db)


def set_swap_xy(args):
    on = bool(args["on"])
    _pm_xy(on)
    if on:
        write_text(XY_FLAG, "1\n")
    elif os.path.exists(XY_FLAG):
        os.remove(XY_FLAG)
    return omni_i18n._("tx_xy_swapped") if on else omni_i18n._("tx_xy_default")


def ensure_swap_xy(_args=None):
    _pm_xy(get_swap_xy())


BUTTONS_FIRST_FLAG = "/etc/omni36os/botoes-iniciais"   # só a imagem nova traz (gerar-imagem.sh)


def ensure_default_buttons(_args=None):
    """Primeiro boot de uma imagem nova: A, B, X e Y como estão escritos nos botões (o dArkOSen vem
    com A/B trocados). Atualizações não trazem a marca, então nunca mexem na escolha do usuário."""
    if not os.path.exists(BUTTONS_FIRST_FLAG):
        return None
    out = []
    if get_swap_ab():
        out.append(set_swap_ab({"on": False}))
    if get_swap_xy():
        out.append(set_swap_xy({"on": False}))
    os.remove(BUTTONS_FIRST_FLAG)
    return "; ".join(out) or omni_i18n._("tx_already_default")


# --- Conflitos com outros scripts ---

def usb_net_active(_args=None):
    """A rede USB (Rede pelo cabo USB, g_ether) usa a mesma porta OTG que o pendrive."""
    mods = read_text("/proc/modules", "")
    return any(m in mods.split() for m in ("g_ether", "g_cdc", "g_multi")) or os.path.exists("/sys/class/net/usb0")


# Programas de tela cheia (PortMaster): o Omni36OS fecha, o launch-direct.sh
# roda o programa e reabre o Omni36OS. As outras ferramentas viraram subpáginas.
HANDOFF = "/tmp/omni36os-next"


def set_cpu_governor(args):
    name = args["governor"]
    if name not in get_cpu_governors():
        return omni_i18n._("tx_gov_unavailable").format(options=', '.join(get_cpu_governors()))
    write_text(f"{CPUFREQ}/scaling_governor", name)
    return omni_i18n._("tx_governor").format(name=name)


# --- Restaurações ---

def device_alsa_path():
    if os.path.exists(DEVICES_INI):
        ini = configparser.ConfigParser(strict=False, interpolation=None)
        ini.read(DEVICES_INI, encoding="utf-8")
        hardware = read_text(f"{DT}/model")
        if ini.has_section(hardware):
            return ini[hardware].get("alsa_path", "SPK_HP")
    return "SPK_HP"


def restore_audio(_args=None):
    """Repete o que o Omni36OS faz: perfnorm (.asoundrc), fixvolume.sh (rota) e boot_volume.sh (40%)."""
    lines = []
    backup = f"{HOME}/.asoundrcbak"
    if os.path.exists(backup):
        shutil.copy(backup, f"{HOME}/.asoundrc")
        os.chown(f"{HOME}/.asoundrc", 1000, 1000)
        lines.append(omni_i18n._("tx_asound_restored"))
    import omni_audio
    route = omni_audio.expected_path() or device_alsa_path()   # automático: fone ou alto-falante
    amixer("-q", "cset", "name=Playback Path", route)
    amixer("-q", "sset", "Playback", "40%")
    lines += [omni_i18n._("tx_audio_out").format(route=route), "Volume: 40%"]
    return "\n".join(lines)


# --- Pendrive USB (porta OTG) ---
# O trabalho fica em usb_pendrive.sh, instalado em /home/ark/usb-disco.sh: o
# serviço de boot roda de lá porque /roms2 é desmontada enquanto o PC a usa.

USB_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usb_pendrive.sh")
USB_BIN = f"{HOME}/usb-disco.sh"


def usb_install():
    if read(USB_SRC) != read(USB_BIN):
        shutil.copy(USB_SRC, USB_BIN)
        os.chmod(USB_BIN, 0o755)
        os.chown(USB_BIN, 1000, 1000)


def usb_run(*args):
    usb_install()
    r = subprocess.run([USB_BIN, *args], capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def model():
    """Modelo do DTB em uso (ex.: "R36S-V21 2024-12-18 2544", "R36XX-V21 2024-12-18")."""
    return read_text("/proc/device-tree/model", "").strip("\0").strip()


def wifi_on_otg():
    """R36XX: o Wi-Fi embutido fica na mesma linha USB da porta OTG; o PC não vê o console por ela."""
    return model().upper().startswith("R36XX")


def usb_facts(_args=None):
    part = usb_run("part") or ("roms2" if os.path.ismount("/roms2") else "roms")
    dtb = subprocess.run(["fdtget", "-t", "s", "/boot/rk3326-r36s-linux.dtb", "/usb@ff300000", "dr_mode"],
                         capture_output=True, text=True).stdout.strip()
    free = {}
    for p in ("roms", "roms2"):
        if os.path.ismount(f"/{p}"):
            st = os.statvfs(f"/{p}")
            free[p] = round(st.f_bavail * st.f_frsize / 1e9, 1)
    return {
        "modelo": model(),
        # o DTB volta ao normal logo que o modo pendrive sobe (vale um boot): conta a porta de agora
        "modo_pendrive_ligado": dtb == "peripheral" or read_text("/proc/device-tree/usb@ff300000/dr_mode", "").strip("\0").strip() == "peripheral",
        "particao_para_o_pc": part,
        "livre_gb": free,
        "wifi_usb_conectado": os.path.exists("/sys/class/net/wlan0"),
    }


def usb_status(_args=None):
    return usb_run("status")


def usb_set_partition(args):
    return usb_run("part", args["part"])


def usb_on(_args=None):
    """Liga o modo pendrive. A rede USB usa a mesma porta: se estiver ligada, sai antes, sozinha."""
    if usb_net_active():
        import omni_sistema
        omni_sistema.usbnet_stop()
    return usb_run("on")


def usb_off(_args=None):
    return usb_run("off")


def dtb_retest(_args=None):
    """Ferramentas > Trocar DTB: o mesmo teste de tela do L1 + R1 ao ligar. Marca o pedido no /boot
    (o omni36os-painel.service roda o teste no boot seguinte) e reinicia."""
    if not os.path.exists("/etc/systemd/system/omni36os-painel.service") and \
            not os.path.exists("/lib/systemd/system/omni36os-painel.service"):
        return omni_i18n._("tx_no_screen_test")
    d = "/boot/omni36os-tela"
    os.makedirs(d, exist_ok=True)
    busca_screen(d)
    with open(f"{d}/testar", "w") as f:
        f.write("Ferramentas\n")
    os.sync()
    # sem o launcher na frente, a tela de busca fica até o reinício (e o U-Boot mostra a mesma)
    # numa unidade à parte (systemd-run): dentro do launcher, parar o launcher matava este comando
    # antes do reboot e o console ficava parado com a tela apagada
    subprocess.Popen(["systemd-run", "--no-block", "--collect", "--unit", f"omni36os-busca-dtb-{int(time.time())}",
                      "sh", "-c", f"sleep 1; systemctl stop omni36os-launcher; "
                                  f"dd if={d}/busca.raw of=/dev/fb0 bs=2560 conv=notrunc 2>/dev/null; "
                                  "sleep 2; systemctl reboot"])
    return omni_i18n._("tx_rebooting_dtb")


def busca_screen(d):
    """Tela "Modo de busca de DTB" no lugar do Carregando enquanto a busca durar: vira o logo.bmp do
    U-Boot (o original fica em logo.bmp.orig; o omni_painel.py devolve no fim) e busca.raw, que o
    teste e o initrd desenham. Feita do PNG que vem na atualização (telas/busca-dtb.png)."""
    png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telas", "busca-dtb.png")
    if not os.path.exists(png):
        return
    ff = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", png]
    subprocess.run(ff + ["-pix_fmt", "bgra", "-f", "rawvideo", f"{d}/busca.raw"], capture_output=True)
    if subprocess.run(ff + ["-pix_fmt", "bgr24", f"{d}/busca.bmp"], capture_output=True).returncode == 0:
        if not os.path.exists(f"{d}/logo.bmp.orig") and os.path.exists("/boot/logo.bmp"):
            shutil.copyfile("/boot/logo.bmp", f"{d}/logo.bmp.orig")
        shutil.copyfile(f"{d}/busca.bmp", "/boot/logo.bmp")


def usb_restore(_args=None):
    return usb_run("restore")


# --- Gerenciamento de ports (launcher como shell principal) ---

PORTS_MOD = os.path.join(OMNI_DIR, "ports.py")


def _import_ports_mod():
    """Importa ports.py dinamicamente (evita dependência circular)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("omni_ports", PORTS_MOD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def list_ports_detailed(_args=None):
    """Lista todos os ports com metadados (ícone, histórico, executável)."""
    mod = _import_ports_mod()
    return mod.list_ports_summary()


def launch_port_direct(args):
    """
    Lança um port diretamente sem EmulationStation.
    args: {"path": "/caminho/do/port"}
    """
    mod = _import_ports_mod()
    ports = {p["path"]: p for p in mod.find_ports()}
    port_path = args.get("path", "")
    if port_path not in ports:
        return False, omni_i18n._("tx_port_not_found_path").format(path=port_path)
    return mod.launch_port(ports[port_path])


def get_ports_history(_args=None):
    """Retorna histórico de ports jogados (caminho -> timestamp)."""
    mod = _import_ports_mod()
    return mod.load_history()


# --- Executor (usado pela interface e por omni_checks.py) ---

TOOLS = {
    "detect_hardware_and_screen": detect_hardware_and_screen,
    "check_microsd_info": check_microsd_info,
    "test_microsd_speed": test_microsd_speed,
    "get_system_status": get_system_status,
    "get_brightness": get_brightness,
    "set_screen_brightness": set_screen_brightness,
    "get_volume": get_volume,
    "set_system_volume": set_system_volume,
    "get_cpu_governors": get_cpu_governors,
    "set_cpu_governor": set_cpu_governor,
    "get_preferred_governor": get_preferred_governor,
    "set_preferred_governor": set_preferred_governor,
    "restore_audio": restore_audio,
    "cpu_freqs": cpu_freqs, "get_cpu_max": get_cpu_max, "set_cpu_max": set_cpu_max,
    "gpu_freqs": gpu_freqs, "get_gpu_max": get_gpu_max, "set_gpu_max": set_gpu_max,
    "zram_facts": zram_facts, "failed_services": failed_services, "fix_dmc": fix_dmc,
    "disk_facts": disk_facts, "clean_mac_junk": clean_mac_junk,
    "schedule_scan": schedule_scan, "last_scan": last_scan,
    "get_gamma": get_gamma, "set_gamma": set_gamma, "get_led": get_led, "set_led": set_led,
    "usb_net_active": usb_net_active,
    "list_ports": list_ports, "port_groups": port_groups, "port_results": port_results, "power": power, "clear_port_alerts": clear_port_alerts, "test_port": test_port,
    "usb_facts": usb_facts,
    "usb_status": usb_status,
    "usb_set_partition": usb_set_partition,
    "usb_on": usb_on,
    "usb_off": usb_off,
    "usb_restore": usb_restore,
    "list_ports_detailed": list_ports_detailed,
    "launch_port_direct": launch_port_direct,
    "get_ports_history": get_ports_history,
}


def run_tool(call):
    tool = TOOLS.get(call.get("tool"))
    if not tool:
        return omni_i18n._("tx_bad_command")
    try:
        result = tool(call.get("args", {}))
    except (KeyError, ValueError, OSError) as e:
        return omni_i18n._("ui_error_prefix").format(error=e)
    return " ".join(result) if isinstance(result, list) else str(result)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        print(run_tool({"tool": sys.argv[1], "args": args}))
    else:
        print("\n".join(TOOLS))
