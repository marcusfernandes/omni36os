#!/bin/bash
# Monta output/Omni36OS-<versão>-emu.img.xz sem a cópia do cartão do autor: parte da imagem oficial
# (só ports, Releases do mpjsilva) e traz o RetroArch/emuladores da imagem original do dArkOSen.
#
#   sudo SRC=Omni36OS-1.15.26.img DARK=dArkOSen_R36_10312026.img imagem/gerar-imagem-emu.sh
#
# As duas imagens são lidas sem alteração. O launcher instalado é o deste repositório.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Rode com sudo."; exit 1; }
REPO=$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)

VER=$(cat $REPO/port/omni36os/VERSION)
SRC=$(readlink -f "${SRC:?imagem oficial do Omni36OS (.img)}"); DARK=$(readlink -f "${DARK:?imagem do dArkOSen (.img)}")
mkdir -p "$REPO/../output"; cd "$REPO/../output"; OUT=Omni36OS-$VER-emu.img
EMU_KEEP=${EMU_KEEP:-"retroarch mupen64plus ppsspp ppsspp-2021 drastic advanceddrastic"}
EMU_SYSTEMS=${EMU_SYSTEMS:-"nes fds snes gb gbc gba genesis megadrive mastersystem gamegear segacd sega32x pcengine psx n64 psp nds arcade fbneo mame2003 neogeo atari2600 ngp ngpc wonderswan wonderswancolor bios"}
D=/mnt/dark; E=/mnt/emu
mkdir -p $D $E
mountpoint -q $D || mount -o ro "$(losetup -f --show -r -P $DARK)p2" $D
echo "== copiando a imagem oficial"
cp --sparse=always $SRC $OUT
L=$(losetup -f --show -P $OUT)
trap 'sync; umount $E 2>/dev/null || true; losetup -d $L 2>/dev/null || true' EXIT
mount -o compress=zlib:1 ${L}p2 $E
echo "== RetroArch e emuladores ($EMU_KEEP)"
for d in $EMU_KEEP; do [ -d $D/opt/$d ] && rsync -aHAX $D/opt/$d $E/opt/; done
for f in retrorun retrorun32; do [ -e $D/usr/local/bin/$f ] && cp -a $D/usr/local/bin/$f $E/usr/local/bin/; done
for c in retroarch retroarch32 mupen64plus; do
  [ -d $D/home/ark/.config/$c ] && rsync -aHAX --exclude cheats $D/home/ark/.config/$c $E/home/ark/.config/
done
echo "== roms.tar com as pastas dos sistemas"
T=$(mktemp -d -p "$PWD")
tar -xf $E/roms.tar -C $T
mapfile -t TEM < <(tar -tf $D/roms.tar | awk -F/ 'NF > 2 && $1 == "roms" { print $1 "/" $2 }' | sort -u)
Q=(); for s in $EMU_SYSTEMS; do [[ " ${TEM[*]} " == *" roms/$s "* ]] && Q+=("roms/$s"); done
tar -xf $D/roms.tar -C $T "${Q[@]}"
echo "   ${#Q[@]} pastas: ${Q[*]#roms/}"
tar -cf $E/roms.tar -C $T roms
rm -rf $T
echo "== launcher $VER"
rsync -a --delete --exclude __pycache__ --exclude imagens --exclude logs $REPO/port/omni36os/ $E/opt/omni36os/
chmod +x $E/opt/omni36os/*.sh $E/opt/omni36os/omni36os-start
chown -R 1000:1000 $E/opt/omni36os $E/home/ark/.config
mkdir -p $E/home/ark/.config/omni36os
echo ligados > $E/home/ark/.config/omni36os/emuladores
chown -R 1000:1000 $E/home/ark/.config/omni36os
sync
btrfs filesystem df $E
df -h $E
fstrim -v $E || true
umount $E; losetup -d $L; trap - EXIT; umount $D || true
echo "== comprimindo"
xz -T0 -6 -f -k $OUT
sha256sum $OUT.xz > $OUT.xz.sha256
cat $OUT.xz.sha256; ls -la $OUT.xz
echo BUILD_DONE
