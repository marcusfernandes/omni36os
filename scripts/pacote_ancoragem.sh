#!/bin/bash
# Gera dist/omni36os-ancoragem-<versão>.zip: extrair na pasta ports e abrir "Atualizar Ancoragem".
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"
V=$(cat "$R/port/omni36os/VERSION")
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$T/omni36os-ancoragem" "$R/dist"
cp "$R/instalador-ancoragem/Atualizar Ancoragem.sh" "$T/"
git -C "$R" ls-files -z port/omni36os | (cd "$R" && tar --null -T - --transform 's|^port/||' -czf "$T/omni36os-ancoragem/omni36os.tar.gz")
Z="$R/dist/omni36os-ancoragem-$V.zip"
rm -f "$Z"
python3 -c 'import shutil,sys; shutil.make_archive(sys.argv[1][:-4], "zip", sys.argv[2])' "$Z" "$T"
echo "$Z"
