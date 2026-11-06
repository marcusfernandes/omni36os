#!/bin/bash
# Omni36OS para clones do R36S (R36Max 720x720 e os outros do arkos4clone), com emuladores.
#
#   sudo imagem/gerar-imagem-clone.sh <dArkOS4Clone.img> <Omni36OS oficial.img>
#        -> Omni36OS-<versão>-clone.img.xz (ao lado da imagem do dArkOS4Clone, ou em $OUT)
#
# Base: a imagem do dArkOS4Clone (https://github.com/lcdyk0517/arkos4clone): kernel, DTBs dos clones,
# seletor de console (dtb_selector_* na partição BOOT, roda no PC depois de gravar), RetroArch,
# emuladores e PortMaster. O clone.sh dela continua rodando a cada boot (botões, atalhos, RetroArch).
# Por cima entram o launcher deste repositório, os serviços e as telas do Omni36OS (tirados da imagem
# oficial). O que no Omni36OS mexe no DTB do R36S (teste de tela, Trocar DTB, overclock, pendrive)
# fica de fora ou desligado. As telas de 640x480 vão centradas na tela do aparelho (omni36os-tela).
set -euo pipefail

REPO=$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)
CLONE=${1:?uso: $0 <dArkOS4Clone.img> <Omni36OS oficial.img>}
OFICIAL=${2:?uso: $0 <dArkOS4Clone.img> <Omni36OS oficial.img>}
VER=$(cat "$REPO/port/omni36os/VERSION")
OUT=${OUT:-$(dirname "$(readlink -f "$CLONE")")}
IMG="$OUT/Omni36OS-$VER-clone.img"
MNT=/mnt/omni36os-clone

[ "$(id -u)" = 0 ] || { echo "Rode com sudo."; exit 1; }
# btrfs não monta duas cópias com o mesmo UUID: a imagem base não pode estar montada
for f in "$CLONE" "$OFICIAL"; do
  losetup -j "$f" | grep -q . && { echo "Desmonte e solte $f (losetup -d) antes."; exit 1; }
done
mkdir -p "$OUT" "$MNT/boot" "$MNT/root" "$MNT/ofi"

echo "== copiando a imagem do dArkOS4Clone"
cp --sparse=always "$CLONE" "$IMG"
LOOP=$(losetup -f --show -P "$IMG")
OLOOP=$(losetup -f --show -P -r "$OFICIAL")
limpar() {
  sync
  umount "$MNT/boot" "$MNT/root" "$MNT/ofi" 2>/dev/null || true
  losetup -d "$LOOP" "$OLOOP" 2>/dev/null || true
}
trap limpar EXIT
mount "${LOOP}p1" "$MNT/boot"
mount -o compress=zlib:1 "${LOOP}p2" "$MNT/root"
mount -o ro "${OLOOP}p2" "$MNT/ofi"
R="$MNT/root"; B="$MNT/boot"; O="$MNT/ofi"; H="$R/home/ark"
[ -f "$B/clone.sh" ] && [ -x "$R/usr/local/bin/console_detect" ] || { echo "Não é a imagem do dArkOS4Clone."; exit 1; }
[ -f "$O/opt/omni36os/VERSION" ] && [ -d "$O/opt/omni36os-telas" ] || { echo "Não é a imagem oficial do Omni36OS."; exit 1; }

echo "== instalando o Omni36OS $VER"
rsync -a --delete --exclude __pycache__ --exclude imagens --exclude logs "$REPO/port/omni36os/" "$R/opt/omni36os/"
chmod +x "$R"/opt/omni36os/*.sh "$R/opt/omni36os/omni36os-start"
chown -R 1000:1000 "$R/opt/omni36os"

# Fora também o que a oficial roda cedo no boot (omni36os-turbo e omni36os-boas-vindas no sysinit,
# boas-vindas no welcome-message): no R36Max o boot travava antes do firstboot. O omni36os-turbo
# dos clones (só CPU) fica para o desligar; o omni36os-diag grava /boot/omni36os-diag.txt.
# arquivos de sistema da imagem oficial (lista fechada). Fora: firstboot.service (o do clone roda o
# clone.sh a cada boot), omni36os-painel (teste de tela do R36S), perfmax/perfnorm/finish.sh/pause.sh
# (os do clone são outros: recebem só as mudanças do Omni36OS, abaixo), o USB do boot.ini do R36S.
SIS=(etc/hostname etc/hosts etc/hostapd/hostapd.conf
     etc/NetworkManager/conf.d/omni36os-usb0.conf etc/NetworkManager/dispatcher.d/90-omni36os-remoto
     etc/omni36os etc/sysctl.d/90-omni36os.conf etc/samba/smb.conf
     etc/systemd/system/omni36os-atalho.service etc/systemd/system/omni36os-launcher.service
     etc/systemd/system/omni36os-tela-saida.service
     etc/systemd/system/omni36os-hora.service etc/systemd/system/omni36os-wifi-boot.service
     etc/systemd/system/multi-user.target.wants/omni36os-atalho.service
     etc/systemd/system/multi-user.target.wants/omni36os-launcher.service
     etc/systemd/system/multi-user.target.wants/omni36os-tela-saida.service
     etc/systemd/system/multi-user.target.wants/omni36os-wifi-boot.service
     etc/systemd/system/nmbd.service.d
     etc/systemd/system/remote-autostart.service.d
     etc/systemd/system/remote-autostart.service
     etc/systemd/system/multi-user.target.wants/remote-autostart.service
     etc/update-motd.d/00-header etc/update-motd.d/10-help-text
     usr/local/bin/omni36os-hora usr/local/bin/omni36os-volume usr/local/bin/omni36os-wifi-boot
     usr/local/bin/BaRT_QuickMode.sh usr/local/bin/arkos_ap_mode.sh
     usr/local/bin/b_swap.sh usr/local/bin/Scan_SD1p3.sh usr/local/bin/Scan_SD2.sh
     usr/local/bin/wifi_enable.sh usr/local/bin/wifi_disable.sh usr/local/bin/zram_autostart.sh
     usr/share/plymouth/themes/text.plymouth opt/omni36os-telas)
for f in "${SIS[@]}"; do
  [ -e "$O/$f" ] || [ -L "$O/$f" ] || { echo "   AVISO: falta na imagem oficial: $f"; continue; }
  mkdir -p "$R/$(dirname "$f")"
  rm -rf "${R:?}/$f"
  cp -a "$O/$f" "$R/$(dirname "$f")/"
  case "$f" in
    usr/local/bin/b_swap.sh) chown -Rh 1000:1000 "$R/$f" ;;
    *) chown -Rh 0:0 "$R/$f" ;;
  esac
done
rm -f "$R/etc/omni36os/overclock"
install -m755 -o0 -g0 "$REPO/port/omni36os/omni36os-start" "$R/usr/local/bin/omni36os-start"
install -m755 -o0 -g0 "$REPO/imagem/clone/omni36os-tela" "$R/usr/local/bin/omni36os-tela"
install -m755 -o0 -g0 "$REPO/imagem/clone/omni36os-turbo" "$R/usr/local/bin/omni36os-turbo"
install -m755 -o0 -g0 "$REPO/imagem/clone/omni36os-diag" "$R/usr/local/bin/omni36os-diag"
install -m644 -o0 -g0 "$REPO/imagem/clone/omni36os-diag.service" "$R/etc/systemd/system/omni36os-diag.service"
ln -sf /etc/systemd/system/omni36os-diag.service "$R/etc/systemd/system/sysinit.target.wants/omni36os-diag.service"

echo "== launcher no lugar do EmulationStation"
rm -f "$R/etc/systemd/system/multi-user.target.wants/emulationstation.service"
mv "$R/etc/systemd/system/emulationstation.service" "$R/etc/systemd/system/emulationstation.service.omni36os-orig"
ln -s /dev/null "$R/etc/systemd/system/emulationstation.service"

echo "== perfmax, perfnorm e finish.sh com as telas do Omni36OS"
P="$R/usr/local/bin"
sed -i 's|image-viewer /roms/launchimages/loading.jpg &|/usr/local/bin/omni36os-tela carregando \&|' "$P/perfmax" "$P/perfnorm"
grep -q "game-running" "$P/perfmax" || sed -i '1a touch /tmp/game-running' "$P/perfmax"
grep -q "game-running" "$P/perfnorm" || sed -i '1a rm -f /tmp/game-running' "$P/perfnorm"
sed -i 's|^echo ondemand > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor$|echo "$(. /etc/cpu-settings.conf 2>/dev/null; echo ${GOV:-ondemand})" > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor  # Omni36OS|' "$P/perfnorm"
sed -i -e 's|sudo systemctl stop emulationstation$|sudo systemctl stop emulationstation omni36os-launcher|' \
       -e 's|printf "\\n\\n\\n\\n\\n\\n\\n      PEACE!" >> /dev/tty1|sudo /usr/local/bin/omni36os-tela desligando; sleep 1|' "$P/finish.sh"
grep -q "omni36os-tela carregando" "$P/perfmax" || { echo "perfmax sem a tela de carregando."; exit 1; }

echo "== botão de power com o menu de energia do Omni36OS"
grep -q "Omni36OS: botão de power" "$P/pause.sh" || cp -a "$P/pause.sh" "$P/pause.sh.omni36os-orig"
python3 -B -c "import sys; sys.path.insert(0, '$REPO/port/omni36os'); import omni; print(omni.POWER_WRAP, end='')" \
  | sed "s|^H=.*|H=/opt/omni36os/power_button.py|" > "$P/pause.sh"
chmod 755 "$P/pause.sh"
grep -q "^H=/opt/omni36os/power_button.py" "$P/pause.sh" || { echo "Desvio do power não foi gravado."; exit 1; }

echo "== padrões de fábrica"
mkdir -p "$R/etc/omni36os" "$H/.config/omni36os"
echo 1 > "$R/etc/omni36os/cpu_auto"
echo 1 > "$R/etc/omni36os/gpu_auto"
touch "$R/etc/omni36os/botoes-iniciais"
echo ligados > "$H/.config/omni36os/emuladores"
install -m644 -o 1000 -g 1000 "$REPO/imagem/filebrowser.db" "$H/.config/filebrowser.db"
chown -R 1000:1000 "$H/.config/omni36os"
touch "$R/var/log/omni36os.log"

echo "== devolvendo o espaço livre"
fstrim -v "$R" || true
fstrim -v "$B" || true
df -h "$R" | tail -1
limpar
trap - EXIT

[ "${NOXZ:-0}" = 1 ] && { echo "== sem compressão (NOXZ=1): $IMG"; exit 0; }
echo "== comprimindo"
rm -f "$IMG.xz"
xz -T0 -6 -v "$IMG"
[ -n "${SUDO_UID:-}" ] && chown "$SUDO_UID:${SUDO_GID:-$SUDO_UID}" "$IMG.xz"
ls -la "$IMG.xz"
sha256sum "$IMG.xz" | tee "$IMG.xz.sha256"
