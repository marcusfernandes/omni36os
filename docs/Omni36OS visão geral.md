# Omni36OS: visão geral

Explicação do que o Omni36OS é e do que ele já faz, na versão 1.15.27 (02/11/2026). Para os detalhes técnicos, veja o [README](../README.md), o [DESENVOLVIMENTO](DESENVOLVIMENTO.md) e a [REFERENCIA](REFERENCIA.md).

## A ideia

O R36S é um console portátil barato (RK3326, 1 GB de RAM) que costuma rodar sistemas de emulação. O Omni36OS faz outra escolha: é um sistema **só de ports**, jogos de PC e homebrew portados para Linux ARM (Stardew Valley, Celeste, Half-Life, Cuphead…), instalados pelo PortMaster.

Sem emulação, sai tudo o que não é usado (EmulationStation, RetroArch, núcleos, emuladores, Kodi). Sobra memória e processador para os ports, e o sistema fica mais simples de entender e de cuidar.

A base é o [dArkOSen](https://github.com/djparentx/dArkOSen-R36S) (Debian trixie, aarch64). Por cima dela vem um launcher próprio, em português, feito para os botões do console: nada pede teclado, PC ou terminal.

## Como é usar

1. **Ligar:** logo e "Carregando" contínuos até o menu, sem telas pretas no meio.
2. **Menu:** nove cards numa grade 3×3, com **Ports** no centro, já destacado.
3. **Jogar:** Ports abre a biblioteca, com capa, estúdio, data, gêneros e descrição de cada jogo, e o último port jogado já selecionado. A abre o jogo; ao fechar, volta ao mesmo lugar.
4. **Dentro do jogo**, atalhos com FN: contador de FPS com temperatura, bateria, CPU, GPU e RAM; limite de 30 FPS; captura de tela; e fechar o jogo (SELECT + START segurado). O power congela o jogo e abre o menu de energia por cima.

## Os cards

| Card | Para que serve |
|---|---|
| **Tela e som** | Brilho, volume, contraste, tema claro e escuro, cor do LED, detalhes da tela e calibração da bateria |
| **Rede** | Wi-Fi (procurar, conectar, redes salvas) e rede pelo cabo USB |
| **Controles** | Testar o controle, personalizar os atalhos FN, botão de power |
| **Desempenho** | Menu sempre no mínimo (esfria e poupa bateria); limites de CPU e GPU nos ports; memória extra (zram); overclock com trava |
| **Ports** | A biblioteca |
| **Aplicativos** | Músicas, Vídeos, Imagens (capturas de tela), Notas (também lê os logs), GeForce NOW, Moonlight |
| **Cartões** | De onde vêm os jogos, ejetar e montar o cartão 2, detalhe e teste de velocidade dos cartões, modo pendrive, pendrive no OTG, verificar e reparar |
| **Ferramentas** | Arquivos, Testar ports, Atualizar ports, PortMaster, Trocar DTB |
| **Geral** | Nome, segurança e trava por senha, backup, atualização, Verificar tudo, Sobre (Manual, Cuidados, Novidades, Créditos com links em QR) |

Cada card **se verifica sozinho** e mostra os pontos de alerta. Quando há conserto seguro, ele aparece como um botão marcado "SUGERIDO".

## O que o diferencia

- **Tela certa sem PC:** no primeiro boot, o Omni36OS testa os modelos de tela possíveis; você só aperta um botão quando a imagem aparece. Cartão levado para outro console: Ferramentas > Trocar DTB (ou L1 + R1 ao ligar) refaz a busca.
- **Testar ports:** abre o port por 15 s e, se falhar, diz a causa provável e corrige o que é seguro, com desfazer. Avisa cópia incompleta e runtime faltando, e baixa os runtimes que faltam.
- **Cuidado com o cartão e a bateria:**
  - desligar e reiniciar gravam tudo antes;
  - com 10% de bateria, fecha o jogo dando tempo de salvar e desliga;
  - o cartão 2 sai e entra sem desligar (Ejetar e Montar), com alerta vermelho se sair sem ejetar;
  - o modo pendrive mostra a cópia em andamento e não encerra no meio dela.
- **Atualização pelo próprio console** (Geral > Procurar atualização), com volta automática para a versão anterior se a nova não abrir.
- **Sistema enxuto:** uma limpeza única tira o que veio da base e não serve a ports (serviços, pacotes, idiomas) e desliga o monitor de Wi-Fi da base, que desligava o adaptador.
- **Logs num lugar só:** `logs/<função>` no cartão 1, legíveis pelo Notas ou pelo PC.

## Por baixo

- **Launcher:** Python 3 + SDL2 (via ctypes), em `/opt/omni36os`. Roda num laço (`launch-direct.sh`) que abre o menu, executa o que ele pediu (jogo, teste, ferramenta) e volta.
- **Serviços:**
  - `omni36os-launcher`: o menu;
  - `omni36os-atalho`: os atalhos FN, a bateria crítica e os runtimes;
  - `omni36os-painel`: o teste de tela;
  - `usb-disco`: o modo pendrive.
- **HUD nos jogos:** uma biblioteca (`omni_hud.so`, e `omni_hud32.so` para jogos de 32 bits) que entra no jogo por LD_PRELOAD e desenha o contador e a captura.
- **Atualização:** troca só `/opt/omni36os`, pelo GitHub (tags `omni-vX.Y.Z`).
- **Imagem:** `imagem/gerar-imagem.sh` parte da imagem do dArkOSen, tira o que não é de ports e instala o Omni36OS.

## Onde estamos

- **Funciona e foi testado no console:** tudo o que está acima, num R36S de teste (tela R36S-V12 Panel 4, com dois cartões).
- **Limitações conhecidas:**
  - ports que trocam o LD_PRELOAD (Cuphead) não aceitam o contador nem a captura do Omni36OS;
  - o R36XX ainda não tem o modo pendrive funcionando (depende de um ajuste de kernel);
  - só português, por enquanto.
- **Próximos passos:** veja [Omni36OS melhorias propostas](Omni36OS%20melhorias%20propostas.md):
  - launcher em C;
  - menor consumo parado;
  - base própria;
  - tradução;
  - comunidade.
