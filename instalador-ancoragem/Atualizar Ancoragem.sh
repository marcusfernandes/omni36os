#!/bin/bash
# Omni36OS: instala por port a versão que acompanha este arquivo (pasta omni36os-ancoragem) e reinicia o launcher.
[ "$(id -u)" = 0 ] || exec sudo bash "$(readlink -f "$0")"
AQUI="$(dirname "$(readlink -f "$0")")"
PACOTE="$AQUI/omni36os-ancoragem"
P="$PACOTE/omni36os.tar.gz"   # tar: a pasta ports pode não guardar permissões
OMNI=/opt/omni36os
STATE=/var/lib/omni36os-update

msg() { printf '\033c\n\n  %s\n' "$1" > /dev/tty1 2>/dev/null; echo "$1"; }
falha() { msg "Erro: $1"; sleep 6; exit 1; }

[ "$(uname -r)" = 4.4.189 ] || falha "Kernel não compatível."
[ -f "$OMNI/VERSION" ] || falha "Omni36OS não encontrado."
para=$(tar -xzOf "$P" omni36os/VERSION 2>/dev/null) || falha "Pasta omni36os-ancoragem incompleta."
de=$(cat "$OMNI/VERSION")

if [ "$(printf '%s\n%s\n' "$de" "$para" | sort -V | tail -1)" = "$de" ]; then
    msg "Omni36OS $de já está atualizado. Aplicando a ancoragem..."
else
    msg "Instalando Omni36OS $para..."
    rm -rf "$OMNI.new"
    mkdir "$OMNI.new"
    tar -xzf "$P" -C "$OMNI.new" --strip-components=1 --no-same-owner || { rm -rf "$OMNI.new"; falha "Sem espaço para instalar."; }
    [ -d "$OMNI/logs" ] && cp -a "$OMNI/logs" "$OMNI.new/"
    mkdir -p "$STATE"
    printf '{"de": "%s", "para": "%s", "quando": %s}' "$de" "$para" "$(date +%s)" > "$STATE/pending"
    echo 0 > "$STATE/tries"
    sync
    rm -rf "$OMNI.prev"
    mv "$OMNI" "$OMNI.prev" && mv "$OMNI.new" "$OMNI" || falha "Não foi possível trocar a versão."
    sync
fi

bash "$OMNI/ancoragem/instalar.sh"
rm -rf "$PACOTE" "$AQUI/Atualizar Ancoragem.sh"
sync
msg "Pronto. Reiniciando o launcher..."
sleep 2
systemd-run --no-block --collect --unit "omni36os-update-$(date +%s)" \
    bash -c "sleep 1; systemctl restart omni36os-atalho omni36os-launcher" >/dev/null
exit 0
