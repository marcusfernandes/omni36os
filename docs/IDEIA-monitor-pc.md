# Ideia: console como monitor extra do PC

Status: só ideia, nada implementado. Objetivo: abrir o app e o PC ganhar um monitor 640×480, com o mínimo de opções.

## Abordagem A — VNC + krfb-virtualmonitor (validação rápida)

- **PC (KDE):** `krfb-virtualmonitor` cria um monitor virtual 640×480 e serve por VNC.
- **Console:** cliente VNC mínimo (SDL2) em tela cheia, só com a tela "Conectando…" e Select+Start para sair.
- **Prós:** quase nada a configurar no PC, rápido de testar.
- **Contras:** fps baixo e sem decodificação por hardware. Serve para painéis, chat e monitoramento.

## Abordagem B — Sunshine + fork do moonlight-embedded (fluida)

**PC (configurar uma vez; script `omni36-monitor-setup.sh`):**
- Um único app "Monitor" no Sunshine, usando `prep-cmd`:
  - ao conectar, cria uma saída virtual 640×480 no KWin, ao lado da tela principal;
  - ao desconectar, remove essa saída (as janelas voltam para a tela principal).
- O Sunshine captura só essa saída.

**Console (fork enxuto do moonlight-embedded):**
- Tirar a lista de apps, as configurações e a interface.
- Fixo no código: app "Monitor", 640×480, 60fps, H.264 por hardware (MPP do RK3326), bitrate baixo (~5 Mbps).
- Descobre o PC por mDNS e lembra o último que funcionou.
- Pareamento automático: o console gera o PIN e manda para a API do Sunshine (`/api/pin`).
- Reconecta sozinho se o Wi-Fi cair.
- Opcional: o analógico vira mouse e L/R viram cliques.

## Observações

- A rede é o dongle Wi-Fi no OTG, então não dá para usar pendrive ou rede USB ao mesmo tempo.
- Caminho sugerido: validar com A primeiro; se a fluidez importar, partir para B.
