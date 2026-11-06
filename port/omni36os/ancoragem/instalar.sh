#!/bin/bash
# Omni36OS: instala a ancoragem USB (ver README.md). Roda como root a cada início do launcher
# e só mexe no que está diferente. Fora do kernel 4.4.189, não faz nada.
[ "$(uname -r)" = 4.4.189 ] || exit 0
D="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
M=/lib/modules/4.4.189/updates/cdc_ether.ko
R=/etc/udev/rules.d/90-omni-ancoragem.rules
B=/usr/local/sbin/omni-ancoragem-bind.sh
C=/etc/NetworkManager/system-connections/omni-ancoragem.nmconnection
N=/etc/NetworkManager/conf.d/omni36os-usb0.conf

# O módulo só vale para o kernel de onde saiu: outro build com o mesmo nome pode ter structs diferentes.
# Sem ele, só a classe EF/04/01 fica de fora; as demais usam os módulos originais.
O=/lib/modules/4.4.189/kernel/drivers/net/usb/cdc_ether.ko
if [ "$(md5sum "$O" 2>/dev/null | cut -d' ' -f1)" = 4102f89016d3347164790db1222e1349 ]; then
    if ! cmp -s "$D/cdc_ether.ko" "$M"; then
        mkdir -p "${M%/*}"
        cp "$D/cdc_ether.ko" "$M"
        /sbin/depmod -a 4.4.189
        /sbin/modprobe -r rndis_host cdc_ether 2>/dev/null   # em uso: vale no próximo boot
    fi
elif [ -f "$M" ]; then
    rm -f "$M"
    /sbin/depmod -a 4.4.189
fi
cmp -s "$D/omni-ancoragem-bind.sh" "$B" || install -m755 "$D/omni-ancoragem-bind.sh" "$B"
if ! cmp -s "$D/90-omni-ancoragem.rules" "$R"; then
    install -m644 "$D/90-omni-ancoragem.rules" "$R"
    udevadm control --reload
fi
if [ -f "$N" ] && grep -q 'interface-name:usb0' "$N"; then
    sed -i -E 's/interface-name:usb0;?//; s/;$//' "$N"
    nmcli general reload conf 2>/dev/null
fi
if ! nmcli -t -f NAME connection show 2>/dev/null | grep -qx omni-ancoragem && [ ! -f "$C" ]; then
    nmcli connection add type ethernet con-name omni-ancoragem ifname '*' \
        match.driver rndis_host,cdc_ether,cdc_ncm ipv4.method auto ipv4.route-metric 100 \
        ipv6.method disabled connection.autoconnect yes >/dev/null
fi
exit 0
