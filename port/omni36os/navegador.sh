#!/bin/bash
# Navegador do Omni36OS: Cog (WPE WebKit) direto na tela, sem ambiente gráfico.
# Modo mouse (FN + R3 ou menu de energia) e "Digitar texto" (menu de energia) vêm do omni_atalho.py.
HERE="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
URL="${1:-https://lite.duckduckgo.com/lite/}"
# libgbm do Mali sem as funções novas que o WebKit pede (lib/gbm_compat.c)
export LD_PRELOAD="$HERE/lib/gbm_compat.so${LD_PRELOAD:+:$LD_PRELOAD}"
export WEBKIT_DISABLE_COMPOSITING_MODE=0 COG_PLATFORM_DRM_VIDEO_MODE=640x480
export XDG_DATA_HOME=/roms/apps/navegador XDG_CACHE_HOME=/roms/apps/navegador/cache
mkdir -p "$XDG_CACHE_HOME"
exec cog -P drm --scale=1.0 "$URL" > /tmp/omni36os-navegador.log 2>&1
