#!/bin/bash
set -eu
HERE="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
BUILD="$HERE/.build-local"
mkdir -p "$BUILD"
trap 'rm -f "$BUILD/scaler-local-test" "$BUILD/omni_scaler.so"' EXIT

gcc -O2 -Wall -Wextra -o "$BUILD/scaler-local-test" "$HERE/scaler-local-test.c" \
    $(pkg-config --cflags --libs egl glesv2)

gcc -fPIC -shared -O2 -Wall -Wextra -Werror -nostdlib -fno-builtin \
    -Wno-builtin-declaration-mismatch \
    -o "$BUILD/omni_scaler.so" "$HERE/omni_scaler.c" -ldl

echo "== Teste local do hook EGL do scaler =="
echo "Biblioteca: $BUILD/omni_scaler.so"
rm -f /dev/shm/omni36os-scaler.log
echo "Backend EGL:"
eglinfo -p surfaceless 2>/dev/null | sed -n '1,28p' || true
echo
echo "Executando teste GLES2 com OMNI_SCALING=1 e modo validate..."
OMNI_SCALING=1 OMNI_SCALING_MODE=validate \
    LD_PRELOAD="$BUILD/omni_scaler.so" "$BUILD/scaler-local-test"
if [ -s /dev/shm/omni36os-scaler.log ]; then
    cat /dev/shm/omni36os-scaler.log
else
    echo "ERRO: hook carregou, mas não registrou modo validate."
    exit 1
fi
rm -f /dev/shm/omni36os-scaler.log

echo "Executando teste GLES2 com modo cas (AMD CAS) e nitidez 0.75..."
OMNI_SCALING=1 OMNI_SCALING_MODE=cas OMNI_SCALING_SHARPNESS=0.75 \
    LD_PRELOAD="$BUILD/omni_scaler.so" "$BUILD/scaler-local-test"
if [ -s /dev/shm/omni36os-scaler.log ]; then
    cat /dev/shm/omni36os-scaler.log
else
    echo "ERRO: hook carregou, mas não registrou modo cas."
    exit 1
fi
rm -f /dev/shm/omni36os-scaler.log

echo "Executando teste GLES2 com modo sharp (Sharp Bilinear)..."
OMNI_SCALING=1 OMNI_SCALING_MODE=sharp OMNI_SCALING_SHARPNESS=0.30 \
    LD_PRELOAD="$BUILD/omni_scaler.so" "$BUILD/scaler-local-test"
if [ -s /dev/shm/omni36os-scaler.log ]; then
    cat /dev/shm/omni36os-scaler.log
else
    echo "ERRO: hook carregou, mas não registrou modo sharp."
    exit 1
fi
rm -f /dev/shm/omni36os-scaler.log

echo "Executando teste GLES2 com frame pacing ativo (modo pacing)..."
OMNI_SCALING=1 OMNI_SCALING_MODE=pacing OMNI_SCALING_TARGET_FPS=60 \
    LD_PRELOAD="$BUILD/omni_scaler.so" "$BUILD/scaler-local-test"
if [ -s /dev/shm/omni36os-scaler.log ]; then
    cat /dev/shm/omni36os-scaler.log
else
    echo "ERRO: hook carregou, mas não registrou modo pacing."
    exit 1
fi
rm -f /dev/shm/omni36os-scaler.log
