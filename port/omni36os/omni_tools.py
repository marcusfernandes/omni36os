"""Ferramentas simples reescritas em Python (NATIVE) e os programas de tela cheia (APPS).

As ferramentas maiores (senha, rede USB, calibração, DTB, arquivos) ficam em
omni_sistema.py e abrem como subpáginas do launcher.
"""
import os
import shutil
import subprocess

import omni
import omni_i18n

ROOT = "/opt/system"
HOME = omni.HOME


def fix_hotkeys(_a=None):
    bak = "/etc/systemd/system/ogage.service.bak"
    run = lambda *a: subprocess.run(["systemctl", *a], capture_output=True)
    run("stop", "ogage")
    if os.path.exists(bak):           # nem toda imagem traz a cópia: sem ela, só religa o serviço
        shutil.copy2(bak, "/etc/systemd/system/ogage.service")
    run("daemon-reload")
    run("enable", "ogage")
    r = run("start", "ogage")
    return omni_i18n._("msg_hotkeys_restarted") if r.returncode == 0 else omni_i18n._("msg_hotkeys_failed")


def usb_mount(_a=None):
    if not os.path.exists("/dev/sda1"):
        return omni_i18n._("msg_pendrive_not_connected")
    os.makedirs("/mnt/usbdrive", exist_ok=True)
    fs = subprocess.run(["lsblk", "-no", "FSTYPE", "/dev/sda1"], capture_output=True, text=True).stdout.strip()
    fs = "ntfs-3g" if fs == "ntfs" else fs
    r = subprocess.run(["mount", "-t", fs, "/dev/sda1", "/mnt/usbdrive", "-o", "uid=1002"], capture_output=True)
    return omni_i18n._("msg_pendrive_mounted").format(fs=fs) if r.returncode == 0 else \
        omni_i18n._("msg_mount_failed")


def usb_umount(_a=None):
    r = subprocess.run(["umount", "/mnt/usbdrive"], capture_output=True)
    os.sync()
    return omni_i18n._("msg_pendrive_unmounted") if r.returncode == 0 else omni_i18n._("msg_no_pendrive_mounted")


def pendrive_status(_a=None):
    """Estado do pendrive, na dica de Montar/Desmontar (Armazenamento): reconhecido ou não, e qual é."""
    try:
        if omni.usb_facts()["modo_pendrive_ligado"]:
            return omni_i18n._("msg_pendrive_not_recognized_mode")
    except OSError:
        pass
    out = subprocess.run(["lsblk", "-dnro", "NAME,TRAN,SIZE,VENDOR,MODEL"], capture_output=True, text=True).stdout
    disks = [l.split(None, 4) for l in out.splitlines() if l.split()[1:2] == ["usb"]]
    if not disks:
        return omni_i18n._("msg_no_pendrive_found")
    name, _tran, size, *rest = disks[0] + [""] * 2
    label = " ".join(x.replace("\\x20", " ").strip() for x in rest if x).strip() or "Pendrive"
    size = size.replace(",", ".").replace("G", " GB").replace("M", " MB")
    fs = subprocess.run(["lsblk", "-no", "FSTYPE", f"/dev/{name}1"], capture_output=True, text=True).stdout.strip()
    txt = omni_i18n._("msg_pendrive_recognized").format(label=label, size=size) + (f", {fs.upper()}" if fs else "") + "."
    if os.path.ismount("/mnt/usbdrive"):
        free_gb = shutil.disk_usage('/mnt/usbdrive').free / 1e9
        return txt + " " + omni_i18n._("msg_pendrive_mounted_info").format(free_gb=free_gb)
    return txt + " " + omni_i18n._("msg_pendrive_ready_to_mount")


NATIVE = {"fix_hotkeys": fix_hotkeys, "usb_mount": usb_mount, "usb_umount": usb_umount}

# Programas de tela cheia que continuam fora do launcher (o resto virou subpágina:
# ver omni_sistema.py). Abrem pelo handoff tool: do launch-direct.sh.
APPS = {
    "Tools/PortMaster.sh": ("PortMaster", omni_i18n._("desc_portmaster")),
}


def tools():
    """Programas de tela cheia que existem neste sistema."""
    return [{"path": os.path.join(ROOT, rel), "name": name, "desc": desc}
            for rel, (name, desc) in APPS.items() if os.path.isfile(os.path.join(ROOT, rel))]


def run_native(name):
    return NATIVE[name]()
