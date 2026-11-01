# Omni36OS: melhorias propostas

Levantamento de 01/11/2026 (versão 1.15.26). Ordem dentro de cada seção: do mais importante ao menos.

## 1. Launcher em C (ou C++)

**Dá para portar, sim.** O launcher já é SDL2 puro chamado via ctypes (`gfx.py`); a lógica não depende de nada que só exista em Python. A troca é de linguagem, não de arquitetura.

**Por que vale:** medido no console com o menu parado:

| Processo | Memória (RSS) | Processador |
|---|---|---|
| `omni_ui.py` (menu) | 142 MB | ~20% |
| `omni_atalho.py` (atalhos, sempre ligado) | 29 MB | ~2,4% |

Com 1 GB de RAM, 170 MB fixos pesam. Em C, o menu deve ficar entre 15 e 30 MB, perto de 0% de processador parado. O serviço de atalhos ficaria abaixo de 2 MB.

**Como fazer sem parar o projeto (por etapas):**

1. **`omni_atalho` primeiro:** é pequeno (~580 linhas), roda o tempo todo, inclusive nos jogos, e é só evdev + arquivos em `/dev/shm`. É o maior ganho por linha portada, e não mexe na interface.
2. **Núcleo de desenho e laço do menu:** `gfx.py` + o laço de `omni_ui.py` em C com SDL2, SDL2_ttf e SDL2_image. Os textos e as regras dos cards podem vir de arquivos JSON, para não ficarem presos ao código.
3. **Funções de sistema como ferramentas separadas:** o que hoje está em `omni.py`, `omni_sistema.py` e `omni_checks.py` pode continuar em Python ou shell, chamado só quando precisa. O Python sai da memória quando a tarefa termina.
4. **Por último**, os apps (Músicas, Vídeos, Imagens, Notas).

**Cuidados:**
- `omni_ui.py` tem ~5.300 linhas: é o maior trabalho. Fazer em etapas evita reescrever tudo de uma vez.
- Os 33 testes atuais são em Python: o modo `OMNI_DEMO` + prints deve continuar existindo na versão em C, para os testes valerem nas duas.
- C++ com SDL2 é mais simples de manter que C puro para a interface (listas, textos, estados).

## 2. Desempenho e consumo

- **Menu parado sem redesenhar:** hoje o laço desenha a tela continuamente. Redesenhar só quando algo muda (botão, animação, relógio por minuto) reduz o processador parado para perto de zero, mesmo antes de portar para C.
- **Atalhos sem polling:** o `omni_atalho` acorda periodicamente. Com `select()`/`poll()` só no controle e um timer longo para a bateria, ele dorme de verdade.
- **Conferência do cartão 2:** hoje é a cada 2 s no menu (custo quase zero). Com o redesenho sob demanda, passar para o próximo toque ou para eventos do udev.
- **Medir o boot com `systemd-analyze` a cada versão** e guardar o número no NOVIDADES, para pegar regressões.

## 3. Confiabilidade

- **Testes no console automatizados:** um script por SSH que abre cada card pelo `OMNI_DEMO`, tira prints e compara com o esperado. Pegaria erros como o Trocar DTB que não reiniciava e o PortMaster sumindo ao ejetar, que só apareceram no aparelho.
- **Regra de processos:** tudo que pare o launcher precisa rodar em `systemd-run` (lição do Trocar DTB). Um teste pode procurar `systemctl stop omni36os-launcher` fora de `systemd-run`.
- **`pgrep -f` com o próprio padrão:** nos scripts de deploy e no código, o `pgrep -f` acha o próprio comando. Usar `[a]bc` ou `pgrep -x`.
- **Lista única de "não é jogo":** File Browser, Samba, SSH e outros serviços estão numa lista (`BACKGROUND` em `omni_atalho.py`). Melhor marcar o que é jogo (o launcher já sabe o que abriu) do que listar o que não é.
- **Log de travamento no boot seguinte:** quando o console é desligado à força, gravar no próximo boot o que estava rodando, com o `journalctl -b -1`, em `/roms/logs/sistema/`.

## 4. Base própria (sair da dependência do dArkOSen)

- **Primeiro passo:** listar exatamente o que vem do dArkOSen e é usado: kernel, DTBs, ogage, PortMaster, scripts de boot e `Scan_SD`. Muita coisa já foi substituída.
- **Kernel:** o R36XX mostrou o limite. O ArchR resolve o USB OTG com um patch de kernel (`usb_switch_gpio`). Com kernel próprio, dá para trazer esse patch e outros.
- **Imagem própria a partir do Debian:** o `gerar-imagem.sh` já tira o que não é usado; o passo seguinte é montar a imagem do zero (debootstrap + kernel + DTBs), sem partir da imagem do dArkOSen.
- **DTBs:** o catálogo já vem com o Omni36OS. Acompanhar o dArkOSen e o ROCKNIX para os modelos novos.

## 5. Experiência do usuário

- **Tradução:** separar todos os textos (cards, ajuda, avisos) num arquivo por idioma (pt-BR, en, es). Começar pelo menu e pela Ajuda.
- **Primeira vez guiada:** depois do nome, um tour curto: onde ficam os ports, o FN, como instalar pelo PortMaster.
- **Port de sistema próprio (Cuphead, Asphalt Xtreme):** mostrar na ficha do port que ele não aceita o contador e a captura do Omni36OS, antes de o jogador tentar.
- **Busca na biblioteca** por nome com o teclado, para quem tem muitos ports.
- **Tempo de jogo e "jogados recentemente"** na biblioteca (o Omni36OS já grava o último port).
- **Avisos de cópia em andamento** (pendrive) também no Samba e no File Browser.

## 6. Projeto e comunidade

- **Página de compatibilidade de ports:** o Testar ports já gera relatórios. Com o consentimento do jogador, juntar os resultados (port, versão, passou ou falhou) numa lista pública.
- **Canal de retorno:** um modelo de issue no GitHub com o relatório do Testar ports e o log do sistema anexados.
- **Guia para contribuir:** o `DESENVOLVIMENTO.md` já explica o simulador; falta um "primeiro passo" curto e as regras de código.
- **Versões mais espaçadas:** várias versões por dia dificultam saber o que cada console tem. Juntar em versões semanais, com uma versão de teste para quem quiser antes.

## 7. Segurança

- **Senha padrão `omni`/`omni` no SSH:** pedir para trocar no primeiro boot, ou deixar o SSH desligado até o jogador ligar.
- **File Browser com acesso a `/`:** limitar a `/roms` e `/roms2`.
- **Atualizações:** conferir a assinatura da tag ou um hash publicado, além de baixar do GitHub.
