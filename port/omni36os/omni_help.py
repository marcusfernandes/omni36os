"""Textos de Geral > Sobre: manual, cuidados, novidades e créditos.
Linhas que começam com "# " viram títulos no leitor."""


# A versão em uso vem do arquivo VERSION. Aqui fica só ela; o histórico completo está no NOVIDADES.md.
NOVIDADES = [
    ('1.16.0', '06/11/2026', [
        'Emuladores (opcional): Ferramentas > Emuladores mostra na biblioteca, depois dos ports, os sistemas do RetroArch com jogos no cartão. X e Y trocam de sistema; o card Ports avisa BIOS faltando.',
        'Imagem com emuladores: sudo EMULADORES=1 imagem/gerar-imagem.sh gera Omni36OS-<versão>-emu.img.xz, com o RetroArch e a opção já ligada. A imagem padrão continua só de ports.',
    ]),
    ('1.15.31', '06/11/2026', [
        'Barra de status: ícone de âncora enquanto a internet chega pela ancoragem USB do celular.',
    ]),
    ('1.15.30', '06/11/2026', [
        'Ancoragem USB: mais celulares Android reconhecidos, com a nova opção Ancoragem celular no card Rede.',
    ]),
    ('1.15.29', '05/11/2026', [
        'Novidades antes de atualizar: a tela agora segue o idioma do console.',
        'Runtimes: corrigido o erro ao baixar quando falta espaço ou o arquivo vem diferente.',
    ]),
    ('1.15.28', '04/11/2026', [
        'Tradução completa para inglês: mensagens, avisos de bateria, diálogos das ferramentas, relatório de teste de ports e modo pendrive seguem o idioma escolhido.',
        'Primeiro boot pergunta o idioma antes do nome do jogador. Redefinir o sistema pergunta de novo.',
        'Em inglês, mensagens de erro não aparecem mais como sucesso.',
    ]),
    ('1.15.27', '02/11/2026', [
        'Wi-Fi: o adaptador não é mais desligado depois de 10 min sem rede (o monitor de Wi-Fi da base desligava o rádio e tirava o driver, e o Wi-Fi não voltava sozinho).',
        'Ports copiados pelo PC com o cartão no leitor aparecem na biblioteca sem precisar de "Atualizar ports".',
        'Limpeza única do sistema, com o menu na tela: tira serviços, pacotes, documentação e idiomas que um sistema só de ports não usa (cerca de 700 MB livres a mais).',
        'Créditos: agradecimento especial ao h1ghland3r, que testou o projeto e reportou os bugs. Os links de Créditos são navegáveis: ↑↓ levam o foco e A abre o QR (GitHub do mpjsilva e links do h1ghland3r).',
    ]),
    ('1.15.26', '01/11/2026', [
        'Ferramentas > Trocar DTB: troca a tela do console sem o PC. Alerta vermelho com trava de 10 s; o console reinicia mostrando "Modo de busca de DTB" e testa as telas uma a uma. O L1 + R1 ao ligar continua valendo.',
        'Catálogo de DTBs do dArkOSen vem com o Omni36OS e é posto em dia sozinho; o aviso de console clone agora vem do modelo e não aparece mais à toa.',
        'Cartões: Ejetar cartão 2 e Montar cartão 2, para tirar e pôr o cartão sem desligar. Tirado sem ejetar, aparece um alerta vermelho (também ao voltar de um jogo).',
        'Sem o cartão 2, nada do ROMS2 aparece: Origem dos jogos, Arquivos, Imagens, runtimes e a Ajuda. A página Cartões se atualiza sozinha quando o cartão entra ou sai.',
        'Ports abre com o último port jogado selecionado.',
        'Testar ports: Ver relatórios (abre no Notas), Runtimes faltando (procura nos ports e, com Wi-Fi, baixa), e o relatório avisa cópia incompleta (arquivos com 0 bytes) e runtime faltando.',
        'Testar ports encerra também o que o port deixa rodando à parte (como o Cuphead); antes o jogo ficava por baixo do menu e a tela piscava.',
        'Atalhos FN acham ports que rodam à parte (Cuphead, Blasphemous). Em port que não aceita o contador de FPS, o limite e a captura, aparece um aviso uma vez por partida.',
        'CAPTURA SALVA aparece embaixo, no centro, e não fica mais sob o monitor de recursos. FN + Y no menu volta a salvar com o File Browser ligado.',
        'Modo pendrive: mostra quando o PC está copiando para o console ou para o PC, e o B não encerra no meio de uma cópia.',
    ]),
    ('1.15.25', '31/10/2026', [
        'Aplicativos ganha Imagens: as capturas de tela (FN + Y) do menu e de cada jogo, a mais nova primeiro. Esquerda/direita passam as imagens; X apaga.',
        'Logs do sistema numa pasta só, no cartão 1: logs/<função> (sistema, ports, pendrive, tela, rede). O relatório do Testar ports vira logs/teste de ports/teste_<nome do port>.txt. Os antigos foram trazidos para lá.',
        'Notas lê os logs: Logs do sistema abre cada log só para leitura, já no fim (o mais novo).',
        'Ferramentas > Atualizar ports: relê a lista de ports, as capas e as descrições quando um port copiado não aparecer.',
        'Wi-Fi: adaptador encaixado com o console ligado e preso no modo disco agora é religado sozinho.',
        'Modo pendrive: respeita a escolha ROMS2 (antes caía em ROMS no boot) e "Partição no PC" só aparece com o cartão 2.',
    ]),
    ('1.15.24', '31/10/2026', [
        'Capa e descrição dos ports pela pasta infos, dentro de ports, com o nome do jogo: para abismo.sh, abismo.txt (descrição) e abismo.png, .jpg ou .webp (capa). Um abismo.json opcional traz nome, estúdio, ano e gêneros.',
        'R36XX: o modo pendrive avisa que o Wi-Fi embutido divide a porta OTG e o PC pode não ver o console; o log do pendrive grava o modelo.',
        'Créditos e textos citam só o dArkOSen como base; o File Browser aparece como Omni36OS.',
    ]),
    ('1.15.23', '31/10/2026', [
        'Modo pendrive vale um boot só: ao ejetar no PC, tirar o cabo ou apertar B, o console devolve o cartão e reinicia sozinho no modo normal, com o Wi-Fi. Qualquer reinício no meio também volta ao normal.',
        'Modo pendrive: o log (/home/ark/usb-disco.log) registra o estado da porta USB enquanto espera o PC, para achar a causa quando o PC não mostra o disco.',
    ]),
    ('1.15.22', '31/10/2026', [
        'Cartão em outro console, com outra tela: quando aparecer "Carregando" ao ligar, aperte e segure L1 + R1 até ouvir um arpejo. A tela do teste entra no lugar e o Omni36OS refaz a escolha da tela, sem precisar do PC.',
    ]),
    ('1.15.21', '31/10/2026', [
        'Botões: o padrão A, B, X e Y como estão escritos vale só para imagens novas, no primeiro boot. Atualizar não muda mais a escolha feita em Controles > Inverter botões.',
    ]),
    ('1.15.20', '31/10/2026', [
        'Botões no padrão: A, B, X e Y fazem o que está escrito neles (o dArkOSen vinha com A e B trocados). Quem quiser trocar usa Controles > Inverter botões.',
        'Aplicativos ganha GeForce NOW (jogos da nuvem) e Moonlight (jogos do seu PC pela rede de casa). Cada um tem Instalar/Atualizar; no GeForce NOW dá para escolher se o FN fica com o sistema ou com ele.',
        'Menu de power num jogo abre na hora. Esquerda/direita mudam o contador, o limite de 30 FPS e o modo mouse sem fechar o menu. Novo: Digitar texto, com o teclado do Omni36OS.',
        'Modo mouse (FN + R3 ou menu de power): analógico direito move, A ou R3 clicam, B é o clique direito, analógico esquerdo rola.',
        'Contador em carrossel no FN + X: FPS; + CPU; + GPU; + RAM usada; esconde.',
        'Power em ports que rodam à parte (como o Gran Turismo) congela o jogo direito: o menu não pisca mais.',
        'Processador e GPU em Automático: sem leitura de FPS, ficam no máximo sem overclock.',
        'Runtimes do PortMaster já vêm na imagem e se atualizam sozinhos quando o Wi-Fi conecta.',
        'Calibrar a bateria: um botão só, que alterna Iniciar/Parar.',
        'Ports novos aparecem na lista sem reabrir o Omni36OS.',
    ]),
    ('1.15.19', '31/10/2026', [
        'Processador e GPU em Automático (Desempenho): no jogo começam no mínimo e sobem um degrau por vez só até o jogo chegar em 60 FPS (ou 30, com o limite do FN + B). A carga da GPU decide quem sobe primeiro. Teto de 1296/520 MHz, ou tudo com o overclock desbloqueado. Imagens novas já vêm assim.',
        'Contador de FPS também em jogos 32 bits (Asphalt e outros), com captura de tela e limite de FPS.',
        'FN + X em ciclo: FPS; depois FPS com a frequência do processador e da GPU na mesma pílula; depois esconde.',
        'Com o FN apertado, a tecla do atalho (FN + X, B, Y) não chega mais ao jogo. Os atalhos do sistema com FN continuam funcionando.',
        'Backup vira snapshot: guarda a versão do Omni36OS, todas as configurações, as redes Wi-Fi, o nome do console, as chaves SSH, o som e o brilho. Importar volta o console exatamente ao ponto do backup e pede para reiniciar.',
    ]),
    ('1.15.18', '31/10/2026', [
        'Runtimes do PortMaster que faltam são baixados da internet antes de abrir o port (não são mais copiados do cartão 2). Sem internet, copie o arquivo pelo PC para tools/PortMaster/libs no cartão do sistema.',
        'Resultado do teste de port: textos longos, como o caminho do relatório, não passam mais da caixa.',
    ]),
    ('1.15.17', '31/10/2026', [
        'Ports pedem o que falta: antes de abrir, o Omni36OS acha os runtimes do PortMaster que o jogo usa (Mono, Godot, Java...) e copia do cartão 2 ou baixa da internet, com barra de progresso. Resolve jogos como TMNT que pediam o Mono mesmo com ele no cartão.',
        'Jogos no cartão 2: a troca de pasta feita durante o jogo é sempre desfeita ao fechar, mesmo se algo do jogo continuar aberto. Antes, os ports do cartão 1 podiam sumir da lista e os do cartão 2 aparecer duas vezes.',
    ]),
    ('1.15.16', '30/10/2026', [
        'Biblioteca de ports: o A abre o jogo direto. A segunda tela (ficha com Jogar e Voltar) saiu, já que a lista mostra a capa e a descrição.',
    ]),
    ('1.15.15', '30/10/2026', [
        'Aviso de bateria fraca também por cima das ferramentas do sistema: a ferramenta congela, o aviso aparece e, no OK (ou ao ligar o carregador), ela continua de onde estava.',
    ]),
    ('1.15.14', '30/10/2026', [
        'Aviso de bateria fraca some sozinho quando o carregador é conectado, e aparece "Carregando".',
        'LED: com o carregador ligado, a bateria fraca não faz mais o LED piscar (vale para cartões novos e imagens novas).',
    ]),
    ('1.15.13', '30/10/2026', [
        'Busca de capas e descrições volta a funcionar em redes cujo roteador não responde às consultas IPv6: o Omni36OS resolve os nomes só em IPv4 (cada site levava uns 6 s só para achar o endereço, e a busca estourava o tempo).',
    ]),
    ('1.15.12', '30/10/2026', [
        'Pílula de estado: o Wi-Fi só aparece conectado com rede e IP de verdade (o adaptador Realtek dizia "ligado" mesmo sem rede).',
        'Adaptador de Wi-Fi Realtek preso no modo "disco" depois do boot (às vezes a troca para placa de Wi-Fi se perde): o Omni36OS percebe e religa sozinho.',
    ]),
    ('1.15.11', '30/10/2026', [
        'Ports do cartão 2 abrem mesmo sem a pasta do jogo no cartão 1: enquanto um deles roda, /roms/ports mostra a pasta ports do cartão 2 (os scripts do PortMaster procuram o jogo lá).',
    ]),
    ('1.15.10', '30/10/2026', [
        'Lista de ports: cada jogo mostra em qual cartão está (ícone de cartão SD com o número 1 ou 2), e a ficha do jogo diz "Cartão 1" ou "Cartão 2".',
    ]),
    ('1.15.9', '30/10/2026', [
        'Tela certa no primeiro boot mais segura: cada teste troca só a tela dentro do DTB original do console. O boot.ini, o u-boot e o resto do hardware nunca são trocados, então uma tela errada só deixa a tela apagada, sem travar o boot.',
        'Tela certa mais rápida: espera 10 s em cada tela e começa logo no início do boot. O pior caso, com 12 telas, caiu de uns 8 para uns 5 minutos.',
        'Durante a busca da tela, o LED pisca em vermelho e verde. A pergunta toca um ding-dong no alto-falante e a confirmação, um arpejo.',
    ]),
    ('1.15.8', '30/10/2026', [
        'Textos curtos (novidades, ajuda) não mostram mais os botões de rolar quando não há nada para rolar.',
    ]),
    ('1.15.7', '30/10/2026', [
        'Procurar atualização mostra as novidades da versão nova antes de instalar (botão Novidades), lidas do GitHub.',
        'Atualizar e Voltar à versão anterior abrem com "Agora não"/"Cancelar" escolhido, para um toque a mais não instalar nada sem querer.',
    ]),
    ('1.15.6', '30/10/2026', [
        'Rede pelo cabo USB: a página mostra qual modo está ligado ("Modo universal: ligado") e quando a rede está desligada.',
        'Compatibilidade da rede USB: o cliente DHCP aparece numa linha só; faltar o dhcpcd não é mais um problema (basta um cliente).',
    ]),
    ('1.15.5', '30/10/2026', [
        'Rede pelo cabo USB e modo pendrive se revezam sozinhos: ligar um desliga o outro, sem aviso para fazer à mão (sair do pendrive reinicia uma vez e a rede USB liga sozinha na volta).',
        'Procurar redes liga o Wi-Fi se ele estiver desligado. Sem adaptador de Wi-Fi, o card Rede só cita isso, sem alerta.',
        'Pílula de estado: o ícone do Wi-Fi mostra a força do sinal, fica apagado sem rede e riscado com o rádio desligado, e se atualiza em todas as telas.',
    ]),
    ('1.15.4', '30/10/2026', [
        'O Omni36OS agora tem licença aberta: GNU GPL v3.0.',
    ]),
    ('1.15.3', '30/10/2026', [
        'Créditos completos em Geral > Sobre: sistema base, PortMaster, gptokeyb, ogage, File Browser, BatteryPlus, SDL2, FFmpeg, fontes, ícones, fontes de dados e a comunidade do R36S, com os links.',
    ]),
    ('1.15.2', '30/10/2026', [
        'Desligar e reiniciar: a tela de despedida aparece direto, sem piscar o menu ou a boas-vindas antes.',
    ]),
    ('1.15.1', '30/10/2026', [
        'Teclado: X dá espaço e Y troca letras e símbolos. A trava das maiúsculas fica só na tecla da tela (dois toques). Vale em todo o sistema.',
    ]),
    ('1.15.0', '30/10/2026', [
        'Notas: abrir mostra a nota inteira para ler, com rolagem. A edita a nota toda, como numa máquina de escrever: o texto sobe quando a linha enche, o teclado ganha Enter e L1/R1 levam o cursor entre as linhas. START salva.',
    ]),
    ('1.14.2', '30/10/2026', [
        'Vídeos e Notas: as listas ficam em tela cheia, como as Músicas, com a pílula de estado (Wi-Fi, volume, bateria, temperatura e hora). O vídeo tocando continua em tela cheia, sem nada por cima. Apagar uma nota pede confirmação, com Cancelar já escolhido.',
    ]),
    ('1.14.1', '30/10/2026', [
        'Manual revisado para o lançamento: apresentação nova, caminhos EASYROMS das pastas de vídeos e notas, Cartões no Verificar tudo, créditos do SDL2 e do FFmpeg, e sem a menção ao RetroArch, que não vem mais no sistema.',
    ]),
    ('1.14.0', '30/10/2026', [
        'Teclado novo, igual em todo o sistema e parecido com o do Android: começa em maiúscula e volta à minúscula depois da primeira letra (e maiúscula de novo depois de ponto), a tecla de maiúsculas trava com dois toques, Y trava direto e X troca letras e símbolos. Senhas começam em minúscula.',
    ]),
    ('1.13.0', '30/10/2026', [
        'Aplicativos ganha Vídeos (tocador simples com os codecs abertos do ffmpeg) e Notas (bloco de notas com teclado e pontuação).',
        'No Arquivos, músicas, vídeos e textos abrem direto no app certo.',
    ]),
    ('1.12.7', '30/10/2026', [
        'O card Armazenamento passa a se chamar Cartões, com a fonte do mesmo tamanho dos outros; legenda Pendrive, espaço e reparo.',
    ]),
    ('1.12.6', '30/10/2026', [
        'O card Tela e som volta a ter esse título (o texto saía do card); a legenda continua com brilho, som e bateria.',
    ]),
    ('1.12.5', '30/10/2026', [
        'Aplicativos mostra só a lista de apps; as opções do Músicas (visualização, apagar a tela e subpastas) ficam dentro do app, no START.',
    ]),
    ('1.12.4', '30/10/2026', [
        'Músicas: a pílula de estado (Wi-Fi, volume, bateria, temperatura e hora) aparece no tocador, o nome da visualização usa o aviso do sistema, e a captura (FN) acende a tela apagada antes de gravar.',
    ]),
    ('1.12.3', '30/10/2026', [
        'Músicas: se o launcher reiniciar com a tela apagada, a luz da tela volta sozinha.',
    ]),
    ('1.12.2', '30/10/2026', [
        'Músicas: visualização Capa do álbum, com a imagem da pasta ou a capa embutida no mp3. A capa também aparece na barra do que está tocando.',
    ]),
    ('1.12.1', '30/10/2026', [
        'Samba com senha: só o usuário omni entra, e a rede mostra apenas Cartão 1 e Cartão 2.',
    ]),
    ('1.12.0', '30/10/2026', [
        'Aplicativos, o card novo: Músicas toca os mp3 das pastas musicas dos cartões, com pastas e subpastas, visualizações (Barras, Ondas, Anel e Aurora) e a tela apagando sozinha enquanto a música toca.',
        'Bateria agora mora em Tela, som e bateria. Ports fica no centro e recebe o destaque toda vez que o menu aparece.',
        'Cada card diz as três coisas que faz.',
    ]),
    ('1.11.11', '30/10/2026', [
        'Texto de Inverter botões mais curto.',
    ]),
    ('1.11.10', '30/10/2026', [
        'Textos do desbloqueio do overclock e da ajuda dos botões revisados.',
    ]),
    ('1.11.9', '30/10/2026', [
        'Com a trava por senha ligada, desbloquear o overclock pede a senha do console.',
    ]),
    ('1.11.8', '30/10/2026', [
        'Overclock com trava de verdade: as velocidades acima de 1296 MHz (processador) e 520 MHz (GPU) só aparecem depois de Desempenho > Desbloquear overclock. Bloquear overclock volta tudo ao padrão.',
    ]),
    ('1.11.7', '30/10/2026', [
        'Ferramentas > Busca automática: liga e desliga a busca de capas e descrições.',
        'A biblioteca diz o que está buscando: imagem e descrição, só a descrição ou só a imagem. O que não foi encontrado não é buscado de novo, e nada é buscado com um jogo aberto.',
    ]),
    ('1.11.6', '30/10/2026', [
        'A busca de capas e descrições só acontece com o Wi-Fi conectado.',
    ]),
    ('1.11.5', '30/10/2026', [
        'Biblioteca: "Buscando a descrição..." e "Descrição não encontrada" no lugar dos textos de ficha.',
    ]),
    ('1.11.4', '30/10/2026', [
        'Descrições pela Wikipédia: texto em português e ano dos ports que o PortMaster e a Steam não têm.',
    ]),
    ('1.11.3', '30/10/2026', [
        'Capas e descrições: quando o PortMaster e a Steam não têm, o Omni36OS procura no DuckDuckGo.',
    ]),
    ('1.11.2', '30/10/2026', [
        'Biblioteca só de ports: lê apenas as pastas ports dos cartões. Pastas de emuladores não aparecem, e a leitura ficou quase instantânea.',
    ]),
    ('1.11.1', '30/10/2026', [
        'Controles: uma opção só, Inverter botões (Ligado/Desligado), troca A com B e X com Y juntos.',
    ]),
    ('1.11.0', '30/10/2026', [
        'Boot mais rápido e sem tela preta: tudo no máximo até o menu ficar pronto (cerca de 3 s a menos) e depois no mínimo. O logo e a boas-vindas seguem direto até o Omni36OS abrir.',
        'Wi-Fi USB sobe sozinho no boot, data, hora e fuso se ajustam quando a internet chega, e o volume fica como você deixou.',
        'Tela e som com painel próprio de brilho, contraste e volume. Troca de A/B e de X/Y em Controles.',
        'FN + Y grava a tela também no menu, na pasta imagens. O Arquivos mostra imagens em tela cheia.',
        'Cartão 2 aparece sozinho. Power sempre abre o menu de energia; FN + power desliga gravando tudo.',
        'Acesso por SSH e pelo navegador com omni/omni. Serviços remotos só ligam com rede.',
        'Visual: ícones próprios, textos com mais contraste, legendas com a arte dos botões e alinhamento ao pixel. O card Rede não fica mais com alerta depois que o Wi-Fi conecta.',
    ]),
]

MANUAL = """# O que é o Omni36OS
O Omni36OS é um sistema só de ports para o R36S, feito sobre o dArkOSen. Abre os ports, toca músicas e vídeos, guarda notas e cuida do console: verifica bateria, som, tela, processador e cartões, aponta o que está errado e corrige com um botão.
Não usa inteligência artificial: são verificações e scripts fixos. A internet só é usada para buscar capas e descrições, acertar a hora e procurar atualizações.

# Como usar
Direcional ou analógico: andar pelos cards e opções.
A: abrir ou confirmar. B: voltar. O botão de power abre Energia (suspender, reiniciar, desligar).
L1/R1: rolam o diagnóstico (painel da esquerda) quando ele não cabe; "L1: N acima" e "R1: mais N" mostram o que está escondido. No manual e nas listas, L1/R1 pulam de bloco em bloco.
Nas opções de valor (modo do processador, limites), use esquerda e direita. Em Tela e som, as barras (volume, brilho, contraste) e as escolhas mudam com o analógico esquerdo, e o direcional só navega.
Cada página explica a opção escolhida no topo do painel da esquerda (lâmpada roxa).
Se os botões A e B estiverem trocados no sistema, o Omni36OS segue a mesma troca.

# Pontos de alerta
Um ponto amarelo (aviso) ou vermelho (problema) em um card mostra quantas coisas precisam de atenção ali. Abra o card para ver a causa.
Quando há conserto, ele aparece no topo das ações com a etiqueta SUGERIDO.
As verificações rodam na tela de carregamento. Depois de uma ação, o card verifica de novo sozinho; "Atualizar status" força uma nova leitura.
Geral > "Verificar tudo" junta numa lista só os alertas de todos os cards.

# Ports (card do centro)
O console liga nos cards e entrega o destaque no Ports, no centro: A abre a biblioteca. É uma lista só, com os favoritos primeiro e o resto por nome. Cima/baixo escolhem o port, esquerda/direita pulam de 10 em 10 e L1/R1 pulam de letra. Ao lado aparece a ficha do jogo (capa, estúdio, data, gêneros e descrição); A abre o port e, ao fechar, a lista volta no mesmo lugar. Ao abrir Ports, o destaque já vem no último port jogado.
B volta para os cards. O botão de power abre Energia: suspender, reiniciar ou desligar.
A capa e a descrição vêm da pasta infos, dentro de ports, com o nome do jogo: para abismo.sh, abismo.txt (descrição) e abismo.png, .jpg ou .webp (capa). Depois, com o Wi-Fi conectado, do PortMaster, da Steam, da Wikipédia e do DuckDuckGo, buscados uma vez e guardados no cartão. Ferramentas > Busca automática liga e desliga a busca.

# Tela e som
"Brilho, contraste e volume" abre um painel com as três barras: cima/baixo escolhe, esquerda/direita ajusta na hora, A confirma e B desfaz o que mudou.
"Tema": escuro ou claro, vale na hora e fica salvo.
Brilho: a luz da tela.
Contraste: barra de 0 a 100% (50% é o normal, gamma 1.0); acima de 50% a imagem fica mais contrastada, abaixo mais clara. Vale na hora e fica salvo para o boot; as teclas de atalho de gamma do sistema continuam a partir do valor escolhido.
Volume: o som do console. O último volume fica salvo: ao ligar, o console volta com ele (antes voltava sempre em 40%). "Restaurar áudio" conserta o som quando ele some ou sai pelo lugar errado: põe de volta o arquivo de som do sistema (.asoundrc), aponta a saída para o lugar certo e deixa o volume em 40%.
A saída de som é automática: com o fone encaixado, o som sai só no fone; sem ele, só no alto-falante. A troca acontece na hora e vale também no boot e depois de um jogo que mexa no som.
Cor do LED: verde ou vermelho, também no boot. Com a bateria em 10% ou menos, o LED pisca.
"Detalhes da tela" mostra o modelo da sua tela, diz qual opção escolher no SELECT MODEL ao atualizar o Omni36OS e avisa se o aparelho é um clone.
Cartão em outro console, com outra tela (tela preta ou imagem errada): quando aparecer "Carregando", aperte e segure L1 + R1 até ouvir um arpejo; a tela do teste entra no lugar. O Omni36OS refaz a escolha da tela: a cada tela toca uma campainha e pergunta "Está vendo esta tela?"; aperte qualquer botão quando ela aparecer certa. Sem resposta, passa para a próxima e reinicia sozinho (uns 5 minutos no pior caso). Com a tela funcionando, use Ferramentas > Trocar DTB (o botão Trocar libera depois de 10 segundos): o console reinicia mostrando "Modo de busca de DTB" no lugar do Carregando e começa o teste. Pelo PC também dá: crie o arquivo vazio omni36os-tela/testar na partição BOOT.

# Rede
Data, hora e fuso se acertam sozinhos: na primeira vez que o console pega internet depois de ligar, o Omni36OS descobre o fuso pela conexão, acerta a hora, grava no relógio do console e desliga o serviço de hora até o próximo boot.
"Ligar o Wi-Fi" liga e desliga o adaptador, "Procurar redes" liga o Wi-Fi se ele estiver desligado e lista as redes por perto (com cadeado pede a senha no teclado; START confirma), "Redes salvas" conecta de novo ou esquece uma, "Desconectar" sai da rede atual, "Ancoragem celular" liga ou desliga a internet do celular conectado por USB. O painel mostra a rede, o sinal e o IP do console, e se atualiza sozinho. Na pílula de estado, o ícone do Wi-Fi aparece riscado sem adaptador ou com o rádio desligado, apagado quando está ligado sem rede e, conectado, com as ondas da força do sinal.
"Rede pelo cabo USB": o console vira uma placa de rede no cabo.
- Modo universal: o console dá o IP ao PC. No PC: ssh omni@10.44.44.1.
- Internet pelo PC: o PC compartilha a internet pelo cabo e o console recebe o IP dele.
- Serviços remotos: Ligados ou Desligados (esquerda/direita). Ligados, sobem o Samba e o navegador web de arquivos (usuário e senha: omni); o SSH fica sempre.
A página mostra o IP e os comandos para o PC, e se atualiza sozinha. A rede USB e o modo pendrive usam a mesma porta: ligar um desliga o outro sozinho (sair do pendrive reinicia o console uma vez, e a rede USB liga sozinha na volta).

# Controles
"Testar o controle" mostra o R36S com cada botão aceso ao apertar, os gatilhos L2/R2 e a posição dos analógicos. Para sair, segure SELECT + START por 1 segundo (B também é testado).
"Inverter botões": Ligado troca A com B e X com Y.
"Atalhos": combinações com o botão FN que valem dentro dos jogos (veja Atalhos abaixo).
Botão de power: um toque abre Energia (Cancelar, Suspender, Reiniciar e Desligar); outro toque com o menu aberto desliga com segurança. FN + power desliga na hora, fechando o jogo e gravando tudo antes. Segurar o power por uns 8 s sempre desliga à força: isso é do chip de energia, não do Omni36OS. O botão de reset reinicia por hardware e não pode ser mudado.
"Consertar atalhos" reinicia o serviço que cuida do brilho e do volume pelos botões.
Serviços que falham no boot aparecem aqui. A falha do dmc-governor (ajuste da RAM) tem conserto com um botão; a do systemd-remount-fs é conhecida e inofensiva no Omni36OS.

# Atalhos (dentro de Controles)
Valem com um port aberto. Cada atalho tem Ligado ou Desligado na página, e os botões abaixo são os que estão valendo agora:
«fps»: em ciclo: FPS; FPS e CPU; FPS, CPU e GPU; FPS, CPU, GPU e RAM usada (MB); esconde. Tudo na mesma pílula. O contador fica no canto de cima e mostra quadros por segundo, temperatura e bateria. O FPS fica verde de 50 para cima, amarelo de 28 a 49 e vermelho abaixo disso. A temperatura fica amarela a partir de 65 °C e vermelha a partir de 75 °C. A bateria fica amarela até 30% e vermelha até 15%; carregando, aparece um raio verde.
«limite»: liga ou desliga o limite de 30 FPS. Em jogo leve, economiza bateria e esquenta menos. Um traço roxo no contador mostra que o limite está ligado.
«captura»: captura de tela na pasta imagens dentro da pasta do jogo (ex.: ports/daytona/imagens), em .bmp com o nome do port e a hora, sem o contador. Vale em qualquer cartão. Aparece "CAPTURA SALVA" embaixo, no centro. Fora de um jogo, FN + Y grava a tela do Omni36OS em PNG na pasta imagens do cartão 1 (EASYROMS/imagens); dá para ver em Arquivos.
«fechar» (segure 1 s): fecha o jogo e volta ao Omni36OS. Serve para port travado ou sem opção de sair. Este é fixo.
"Personalizar um atalho": escolha o atalho e aperte a tecla nova; ele vira FN + essa tecla. O Omni36OS recusa o que já é do sistema ou de outro atalho. "Voltar aos botões padrão" desfaz (FN + X, FN + B e FN + Y).
Pelo botão de power, com um jogo aberto: o jogo congela e o menu Energia abre por cima com as mesmas opções (mostrar o contador, limitar a 30 FPS, captura de tela e fechar o jogo), além de suspender, reiniciar e desligar. Captura e contador valem quando o jogo volta.
O sistema (ogage) já usa: FN + cima/baixo e FN + volume para o brilho; FN com L1/R1, esquerda/direita, A, L3 e R3 para ajustes do sistema; SELECT + FN fala a bateria; FN + power desliga gravando tudo.
O contador, o limite e a captura funcionam em ports que desenham com OpenGL ES (a maioria). Ports em 32 bits também. Os que trocam o LD_PRELOAD (como o Cuphead) não aceitam o contador, o limite nem a captura: o atalho mostra um aviso, uma vez por partida. Fechar continua valendo, inclusive em ports que rodam à parte. Com o FN apertado, a tecla do atalho fica só com o Omni36OS: o jogo não a recebe.

# Bateria (dentro de Tela e som)
O painel mostra a carga, se está carregando, o brilho e o modo do processador. Com o brilho alto ou o processador no máximo, aparece a dica de economia com um botão. O processador se ajusta em Desempenho.
Bateria no fim (a porcentagem do R36S não é confiável, por isso os limites são altos): em 30% o Omni36OS sugere conectar o carregador; em 15%, sugere salvar o progresso (num jogo, o contador surge com a bateria em vermelho). Em 10%, sem o carregador, o Omni36OS fecha o jogo dando tempo de ele salvar, grava tudo e desliga, em vez de o console apagar de repente.
"Calibrar a bateria" abre a página da calibração. Calibre quando a porcentagem pular ou o aparelho desligar com carga sobrando:
1. Carregue até o fim e tire o carregador.
2. Toque em "Iniciar a calibração" e use o console normalmente (pode jogar) até ele desligar sozinho. Uma amostra por minuto fica gravada em /usr/local/etc/battery-cal.
3. Ligue, carregue e toque em "Aplicar a curva". A porcentagem passa a seguir a sua bateria.
"Voltar à curva de fábrica" desfaz.

# Aplicativos
"Músicas" toca as músicas (mp3, e também ogg, flac e wav) das pastas musicas dos cartões: EASYROMS/musicas⟦ e, com o cartão 2, ROMS2/musicas⟧. A pasta do cartão 1 é criada sozinha.
Cada pasta mostra as músicas soltas nela e as subpastas; A numa subpasta entra nela, A numa música toca a pasta a partir dela, Y toca a pasta inteira e B volta. Com "Ler subpastas" ligado, tocar uma pasta inclui as músicas das subpastas, nível por nível.
Na tela Tocando: A pausa, esquerda/direita trocam de música, L1/R1 voltam e avançam 10 s, Y troca a visualização e B volta à lista (a música continua; X volta para a tela Tocando). Sair das Músicas para a música.
Opções (START, dentro do app): "Visualização": Capa do álbum (a imagem da pasta, como cover.jpg, ou a capa embutida no mp3), Barras, Ondas, Anel ou Aurora, dançando com o som. "Apagar a tela": com a música tocando e sem apertar nada, a luz da tela apaga em 30 s, 1, 2 ou 5 minutos (ou Manter ligada); qualquer botão acende.
As pastas ficam num índice (nome, título e artista das tags): só a pasta que mudou é lida de novo, e a lista guarda só os caminhos.
"Vídeos" toca os vídeos das pastas videos dos cartões (EASYROMS/videos, criada sozinha⟦, e ROMS2/videos⟧), com os codecs abertos do ffmpeg: mp4, mkv, webm, avi e outros (H.264, H.265, VP8, VP9, AV1, MPEG-4). A pausa, esquerda/direita voltam e avançam 10 s, L1/R1 1 minuto, B volta. Vídeos até 720p rodam bem; acima disso, depende do codec. A música para enquanto o vídeo toca.
"Notas" é um bloco de notas simples: textos na pasta notas do cartão 1 (EASYROMS/notas). Na lista, a primeira linha cria uma nota e X apaga (com confirmação). Abrir uma nota mostra o texto inteiro: cima/baixo rolam e L1/R1 pulam a página. A edita a nota toda, como numa máquina de escrever: o texto quebra sozinho e sobe quando a linha enche, Enter começa uma linha nova, L1/R1 levam o cursor para a linha de cima ou de baixo, START salva e SELECT sai sem salvar.
No Arquivos, abrir uma música, um vídeo ou um texto (txt, md, log, ini, cfg, conf) abre o app certo; B volta para a pasta.

# Desempenho
No menu, o processador, a GPU e a memória ficam no mínimo: o console esfria e a bateria rende. Só um vídeo tocando faz o processador subir conforme a carga. Ao abrir um port, tudo sobe até os limites abaixo; ao voltar, desce de novo.
Limite do processador (nos ports): 1296 MHz é o padrão. De 1368 a 1512 MHz é overclock (OC).
Limite da GPU (nos ports): 520 MHz é o padrão; 600 MHz é overclock.
O overclock só é liberado com o aparelho abaixo de 70 °C. Se ele esquentar com o OC ligado, o Omni36OS sugere voltar ao padrão.
Memória extra (zram): desligada por padrão. 256, 512 ou 768 MB de memória comprimida na RAM, que segura ports pesados que fecham por falta de memória. Vale na hora e nos próximos boots; custa um pouco de processador.
"Liberar overclock" mexe no arquivo de hardware do boot (DTB): libera as frequências de 1368 a 1512 MHz e a GPU de 600 MHz. Tem trava: aviso vermelho com contagem e depois A apertado 5 vezes. Antes de mudar, o Omni36OS guarda uma cópia do DTB. Vale depois de reiniciar; o limite se escolhe em "Limite do processador" e "Limite da GPU".

# Cartões
Tudo sobre onde ficam os jogos: os cartões, o pendrive e a porta USB. As ações que reiniciam ou apagam ficam no fim da página.
⟦"Origem dos jogos": ROMS (cartão 1), ROMS2 (cartão 2) ou ROMS e ROMS2. Ao sair da página depois de trocar (B ou START), o Omni36OS procura os jogos e os ports de novo, uma vez só, e atualiza a biblioteca e o Testar ports. Com as duas, o mesmo sistema dos dois cartões vira uma lista só. Sem o segundo cartão (ROMS2), a opção nem aparece e tudo vem do ROMS. Antes de tirar o cartão 2, use "Ejetar cartão 2": tirado montado, ele pode corromper, e o Omni36OS mostra um alerta vermelho.⟧
⟦"Ejetar cartão 2" grava o que falta e desmonta o cartão 2 para tirar sem desligar; com um cartão posto e desmontado, aparece "Montar cartão 2". A página se atualiza sozinha quando o cartão entra ou sai. Tirado sem ejetar, aparece um alerta vermelho (num jogo, ao voltar ao menu): ponha de volta, monte e use "Verificar e reparar os jogos".⟧
"Detalhe do cartão"⟦ (com dois cartões, "Detalhe dos cartões")⟧: mostra a marca, o tamanho, o espaço livre e o ocupado do cartão inteiro e testa a escrita e a leitura de cada cartão; leva até um minuto. O espaço livre aparece no painel. Cartões genéricos sem marca costumam ser lentos e falhar mais: o detalhe avisa quando o cartão não tem marca identificada (não é alerta).
O Omni36OS avisa quando um cartão passa de 90% de uso ou tem menos de 1 GB livre.
"Verificar e reparar os jogos" reinicia o aparelho e roda o reparo do Omni36OS (fsck.exfat) com o cartão desmontado. Depois o resultado aparece neste card, e o log fica em /boot/sd2_scan.log (segundo cartão) ou /boot/sd1p3_scan.log (só o cartão do sistema).

Modo pendrive:
Liga o modo pendrive: com o cabo de dados no PC, a partição ⟦ROMS2 (cartão 2) ou ⟧ROMS (cartão 1⟦; com dois cartões, escolha em "Partição no PC", que só aparece com o cartão 2⟧) aparece como um pendrive para copiar ports.
Ligar reinicia o aparelho como pendrive. Enquanto estiver ligado, o Wi-Fi não funciona, porque usa a mesma porta. Se a rede USB estiver ligada, ela desliga sozinha.
Ao conectar o PC, o Omni36OS fecha para soltar a partição. Durante a cópia, a tela mostra "COPIANDO PARA O CONSOLE..." ou "COPIANDO PARA O PC...". Com o PC ainda gravando, o B espera a cópia terminar. Ao ejetar no PC, tirar o cabo ou apertar B (ou Select + Start), o console devolve a partição e reinicia sozinho no modo normal, com o Wi-Fi. O modo vale só para aquele boot: qualquer reinício volta ao normal.
"Restaurar boot" volta o arquivo de boot original se algo der errado.
"Limpar lixo do Mac" apaga os arquivos ._ e .DS_Store que o macOS cria ao copiar. Eles aparecem como ports fantasmas na biblioteca. A busca leva até um minuto.
"Montar pendrive" monta um pendrive ligado no OTG em /mnt/usbdrive (FAT, exFAT ou NTFS). Com ele montado, o mesmo botão vira "Desmontar pendrive": use antes de tirar. Com essa opção escolhida, o painel da esquerda diz se o pendrive foi reconhecido, qual é e se já está montado.

# Ferramentas
"Arquivos": navega pelo cartão (/roms⟦, /roms2⟧) e pelo pendrive. A abre a pasta (ou a imagem, em tela cheia: esquerda/direita passa para a próxima, A mostra ou esconde o nome, B volta), B sobe um nível, X abre as opções do item (copiar, mover, renomear, apagar) e START abre as opções da pasta (colar aqui, nova pasta). Músicas, vídeos e textos abrem direto no app de Aplicativos. Para copiar: X > Copiar no item, vá até a pasta de destino e START > Colar aqui. Apagar pede confirmação, com Cancelar já escolhido.
"PortMaster" abre em tela cheia; o Omni36OS volta quando ele fecha. Para copiar, mover, renomear e apagar, use "Arquivos", aqui mesmo no Omni36OS.
As outras ferramentas do sistema ficam nos cards: Testar o controle (Controles), Trocar a senha (Geral > Segurança), Wi-Fi e rede pelo cabo (Rede), pendrive (Cartões), Calibrar a bateria (Tela e som), Liberar overclock (Desempenho). Tudo o que mexe no boot abre um aviso vermelho com contagem; Cancelar fica escolhido desde o início.

# Testar ports (dentro de Ferramentas)
Mostra os ports das pastas escolhidas em Cartões > Origem dos jogos.
Escolha um port e aperte A: o Omni36OS fecha, o port abre como pela biblioteca e, depois de 15 segundos, é encerrado sozinho. O Omni36OS volta com o resultado.
Passou: o port ficou aberto os 15 segundos.
Falhou: o port fechou antes. O relatório fica em logs/teste de ports/teste_<nome do port>.txt, no cartão 1 (dá para ler em Notas > Logs), com a saída do port, os logs da pasta dele, as mensagens do kernel e o estado do sistema.
A lista mostra o último resultado de cada port, e as falhas viram alerta no card.
"Ver relatórios" abre os relatórios no Notas, só para leitura.
"Runtimes faltando" procura nos ports os runtimes do PortMaster que não estão no cartão; com o Wi-Fi conectado, pergunta se quer baixar. O relatório de cada teste também avisa runtime faltando e cópia incompleta (arquivos com 0 bytes, de uma cópia que parou no meio).
O teste encerra também o que o port deixa rodando à parte (como o Cuphead), para o jogo não ficar por baixo do menu.
"Limpar avisos de falha" tira o alerta do card depois que você já viu as falhas. O resultado continua na lista até o port ser testado de novo; se o novo teste falhar, o aviso volta.
Ports com menu próprio (como Daytona USA e NFSU1) passam quando o menu abre: o teste não aperta botões.
Quando o port falha, o Omni36OS lê o relatório e mostra a causa provável (script do Windows, arquivo sem permissão, falta de memória, runtime do PortMaster, biblioteca, glibc, arquivos do jogo, cartão exFAT, travamento). Se houver conserto seguro, aparece "Corrigir e testar de novo": ele corrige (permissão, formato dos scripts ou memória extra) e testa outra vez. Se ainda falhar, a correção é desfeita. O diagnóstico também fica no relatório.

# Geral
O que é seu e do Omni36OS, como nos Ajustes do iPhone, nesta ordem:
"Nome do jogador": aparece na saudação do menu.
"Segurança": senhas e trava (veja abaixo).
"Backup": exporta e importa as configurações (veja Backup abaixo).
"Procurar atualização" (precisa de Wi-Fi): procura uma versão nova no GitHub. Antes de instalar, o Omni36OS baixa e confere tudo; a versão de agora fica guardada. Se a nova não chegar ao menu em 3 tentativas, a anterior volta sozinha e um aviso explica. "Voltar à versão anterior" aparece depois de uma atualização e troca de volta a pedido. Deixe o carregador ligado durante a atualização.
"Verificar tudo": mostra só o que precisa de atenção em todos os cards (tela e som, bateria, desempenho, cartões e serviços), cada linha com o card de origem. Sem alertas, aparece "Tudo certo". O detalhe fica em cada card.
"Sobre": este manual, os cuidados, as novidades de cada versão e os créditos (com os projetos usados como base).
"Redefinir o sistema": volta ao primeiro boot. Apaga o nome do jogador, a trava por senha e o tema, desliga a memória extra (zram) e volta processador (Equilibrado, 1296 MHz), GPU (520 MHz) e atalhos ao padrão; depois pergunta o nome de novo. Ports, jogos, testes e as senhas do sistema e do Samba ficam.

# Segurança (dentro de Geral)
Tudo o que é senha fica aqui. B volta para Geral.
"Trocar a senha" muda a senha do usuário omni (SSH, SFTP e Samba; a senha padrão é omni) com o teclado na tela: direcional escolhe, A digita, B apaga, X dá espaço, Y troca letras e símbolos (as maiúsculas travam com dois toques na tecla da tela), START confirma e SELECT cancela (como no teclado do Android, começa em maiúscula; senha começa em minúscula). A senha é pedida duas vezes.
"Senha do Samba" redefine só a senha das pastas compartilhadas (usuário omni), sem mexer na do SSH.
"Trava por senha": com ela ligada, o console pede a senha ao ligar, antes de mostrar os jogos (o botão de power ainda abre Energia para desligar). A senha fica em texto simples em EASYROMS/senha/senha.txt: esqueceu, abra o cartão no PC e leia. Apagar esse arquivo desliga a trava. Para desligar pelo console, a senha atual é pedida.

# Backup
Geral > Backup > Exportar ou Importar.
O backup é um snapshot do sistema: a versão do Omni36OS, todas as configurações (atalhos, Desempenho, overclock, zram, tela, gamma, som, brilho, troca de botões, músicas), as redes Wi-Fi, o nome do console e as chaves SSH. Jogos, ports e saves ficam de fora (estão nos cartões).
Exportar pergunta onde salvar: cartão do sistema (/roms/backup/omni36os), ⟦segundo cartão (/roms2/backup/omni36os) ou ⟧pendrive (/mnt/usbdrive/backup/omni36os). Só aparece o que está no console agora, e o último lugar escolhido vem marcado. O caminho completo aparece ao terminar.
Importar abre a pasta dos backups; navegue pelas pastas com A ("..": voltar). Cada arquivo mostra de qual módulo é, e só o backup do módulo certo pode ser importado.
Importar volta o console exatamente ao ponto do backup: o que mudou ou surgiu depois é desfeito, inclusive a versão. No fim, o Omni36OS pede para reiniciar. Antes de importar, ele salva o que está valendo agora como "...-antes-de-importar.tar.gz".
Só configurações: saves, estados, cores, shaders, temas e bancos de dados ficam de fora."""

CUIDADOS = """# Antes de qualquer coisa
Faça backup do cartão do sistema no PC de vez em quando. Uma imagem do cartão inteiro salva você de quase qualquer problema.

# Pendrive USB
Sempre ejete o pendrive no PC antes de tirar o cabo. Tirar no meio de uma cópia pode corromper os arquivos.
Não desligue o console enquanto ele estiver ligado no PC.
⟦Com segundo cartão, prefira compartilhar /roms2. Sem ele, o⟧⟪O⟫ PC recebe /roms (a partição de jogos do cartão do sistema): copie só para as pastas de jogos e ports.
Se o console não voltar ao normal, use "Restaurar boot" em Cartões (último item).

# Verificar e reparar o cartão
O aparelho reinicia e passa alguns minutos verificando. Não desligue nem tire o cartão nessa hora.
O reparo apaga entradas corrompidas: se o cartão já estava com erros, algum arquivo danificado pode sumir. Tenha backup.

# Restaurar e atualizar
Antes de atualizar o Omni36OS, copie a partição BOOT do cartão para o PC e veja em Tela e som > "Detalhes da tela" qual modelo escolher.

# Primeiro boot
Na primeira vez que liga, o Omni36OS acerta a tela sozinho: se aparecer "Está vendo esta tela?", aperte qualquer botão. Se a tela ficar apagada, não desligue: ele testa a próxima tela e reinicia sozinho (cada tentativa leva menos de um minuto). Se nenhuma for confirmada, volta tudo como estava.
Para refazer depois, crie pelo PC o arquivo omni36os-tela/testar na partição BOOT do cartão.

# Overclock
Overclock é usar o chip acima do que a fábrica garante. Pode causar travamentos e, com o tempo, desgaste maior.
O kernel do Omni36OS protege o aparelho: freia a 70 °C, limita a 85 °C e desliga a 115 °C. Mesmo assim, se travar ou fechar jogos sozinho, volte para 1296 MHz (CPU) e 520 MHz (GPU).
O Omni36OS não libera o overclock com o aparelho acima de 70 °C.

# Bateria e calor
Evite o overclock com a bateria fraca ou o aparelho quente.
Com a bateria fraca, carregue antes de usar o pendrive ou atualizar.

# Cartões
Cartões genéricos falham mais. Se um cartão aparecer como lento ou sem marca, mantenha backup dos seus saves.

# Teste de ports
O teste abre o port de verdade e o encerra à força depois de 15 segundos. Ports que gravam configuração ou save logo ao abrir podem perder o que estava sendo gravado; teste com o save já em backup.
Durante o teste não aperte botões: o port recebe os comandos.
Se o port travar a tela, segure o botão de ligar para reiniciar; o resultado não é gravado nesse caso.

# Backup e importação
Importar volta também a versão do Omni36OS à do backup. Depois, "Procurar atualização" traz a versão nova de novo, se quiser.
Guarde cópias dos backups fora do console (no PC, pelo pendrive).

# Ao desligar
Desligue pelo menu Energia (botão de power), nunca segurando o power: pelo menu, o Omni36OS grava tudo e desmonta o boot antes de desligar.
Para fechar um port travado, use SELECT + START (segure 1 s) antes de pensar em desligar à força."""

CREDITOS = """# Omni36OS
Sistema só de ports para o R36S, feito por mpjsilva, com a ajuda do Claude (Anthropic) no desenvolvimento. Licença GNU GPL v3.0. github.com/mpjsilva/omni36os

# Agradecimento especial
h1ghland3r, youtuber que tornou o projeto possível: obrigado pelo tempo que você dedicou testando o projeto e reportando os bugs xD. beacons.ai/h1ghland3r

# Sistema base
dArkOSen, de djparentx: a imagem usada como base do Omni36OS, com o catálogo de telas dos modelos R36, a ferramenta de calibração da bateria (que o Omni36OS reescreveu), o patch do DTB e o desligamento seguro. github.com/djparentx/dArkOSen-R36S

# Ports e ferramentas
PortMaster e sua comunidade: a loja de ports, os ports e os dados dos jogos. github.com/PortsMaster/PortMaster-GUI
gptokeyb: o controle como teclado e mouse nos ports. github.com/PortsMaster/gptokeyb
ogage: as teclas de atalho do sistema, que vêm no dArkOSen.
File Browser: o navegador de arquivos pela rede. github.com/filebrowser/filebrowser
BatteryPlus, de Mikhailzrick. github.com/Mikhailzrick/knubat.components

# Bibliotecas e programas livres
SDL2, SDL2_ttf, SDL2_image e SDL2_mixer, licença zlib: tela, controles, fontes, imagens e músicas. libsdl.org
FFmpeg, licença LGPL/GPL: os vídeos. ffmpeg.org
Debian, Linux, NetworkManager, Samba, systemd e todo o software livre por baixo.
Fonte Poppins, licença OFL: github.com/itfoundry/Poppins
Ícones Tabler, licença MIT: github.com/tabler/tabler-icons

# Dados da biblioteca
Steam (capas e descrições), Wikipédia (descrições em português; texto sob CC BY-SA 4.0) e DuckDuckGo (imagens quando as outras fontes não têm).

# Comunidade
A comunidade do R36S, que documenta modelos, telas, clones e consertos e torna este projeto possível. Obrigado!"""

MANUAL_EN = """# What is Omni36OS
Omni36OS is a ports-only system for the R36S, based on dArkOSen. It launches ports, plays music and videos, stores notes, and takes care of the console: it checks the battery, sound, screen, processor, and cards, points out problems, and fixes them with one button.
It does not use artificial intelligence: it uses fixed checks and scripts. The internet is used only to find covers and descriptions, set the time, and check for updates.

# How to use
D-pad or analog stick: move through cards and options.
A: open or confirm. B: go back. The power button opens Power (suspend, restart, shut down).
L1/R1: scroll the diagnostic panel on the left when it does not fit; “L1: N above” and “R1: N more” show what is hidden. In the manual and lists, L1/R1 jump from section to section.
For value options (processor mode, limits), use left and right. In Display & Sound, the bars (volume, brightness, contrast) and choices are changed with the left analog stick; the D-pad only navigates.
Each page explains the selected option at the top of the left panel (purple lightbulb).
If the system has A and B swapped, Omni36OS follows the same swap.

# Alert indicators
A yellow (warning) or red (problem) dot on a card shows how many items need attention. Open the card to see the cause.
When a fix is available, it appears at the top of the actions with the SUGGESTED label.
Checks run on the loading screen. After an action, the card checks again automatically; “Refresh status” forces a new check.
General > “Check Everything” combines alerts from all cards in one list.

# Ports (center card)
The console starts on the cards and places focus on Ports in the center: A opens the library. It is a single list, with favorites first and the rest alphabetically. Up/down selects a port, left/right skips 10 at a time, and L1/R1 skip by letter. The game details appear beside it (cover, studio, date, genres, and description); A launches the port and, when it closes, the list returns to the same place. When Ports opens, focus is already on the last port played.
B returns to the cards. The power button opens Power: suspend, restart, or shut down.
The cover and description come from the infos folder inside ports, named after the game: for abismo.sh, abismo.txt (description) and abismo.png, .jpg, or .webp (cover). They may also come from PortMaster, Steam, Wikipedia, and DuckDuckGo when Wi-Fi is connected; they are fetched once and saved on the card. Tools > Automatic Search turns searching on and off.

# Display & Sound
“Brightness, contrast, and volume” opens a panel with all three bars: up/down selects, left/right adjusts immediately, A confirms, and B undoes the change.
“Theme”: dark or light; takes effect immediately and is saved.
Brightness: screen backlight.
Contrast: 0–100% bar (50% is normal, gamma 1.0); above 50% the image has more contrast, below it is brighter. Takes effect immediately and is saved for boot; the system gamma shortcut keys continue from the chosen value.
Volume: console sound. The last volume is saved: the console starts at that volume (it used to always start at 40%). “Restore audio” fixes missing sound or sound coming from the wrong output: restores the system sound file (.asoundrc), points output to the right place, and sets volume to 40%.
Sound output is automatic: with headphones plugged in, sound comes only through the headphones; without them, only through the speaker. The switch happens immediately and also applies at boot and after a game changes sound settings.
LED color: green or red, including at boot. At 10% battery or less, the LED blinks.
“Screen details” shows your screen model, tells you which option to choose in SELECT MODEL when updating Omni36OS, and warns if the device is a clone.
Card used in another console with a different screen (black screen or wrong image): when “Loading” appears, hold L1 + R1 until you hear an arpeggio; the test screen replaces it. Omni36OS detects the screen again: each screen plays a chime and asks “Can you see this screen?”; press any button when it appears correctly. With no response, it tries the next one and restarts automatically (about 5 minutes in the worst case). Once the screen works, use Tools > Change DTB (the Change button unlocks after 10 seconds): the console restarts showing “DTB search mode” instead of Loading and starts the test. You can also do this from a PC: create the empty file omni36os-tela/testar on the BOOT partition.

# Network
Date, time, and time zone are set automatically: the first time the console gets internet after startup, Omni36OS determines the time zone from the connection, sets the time, writes it to the console clock, and stops the time service until the next boot.
“Turn Wi-Fi on” enables or disables the adapter; “Scan for networks” turns Wi-Fi on if it is off and lists nearby networks (a lock means a password is required; enter it with the keyboard and press START to confirm); “Saved networks” reconnects or forgets one; “Disconnect” leaves the current network; “Phone tethering” turns the internet of a USB-connected phone on or off. The panel shows the network, signal, and console IP and refreshes automatically. In the status pill, the Wi-Fi icon is crossed out when there is no adapter or the radio is off, dim when on but not connected, and shows signal-strength waves when connected.
“USB cable network”: the console becomes a network adapter over the cable.
- Universal mode: the console gives the PC an IP. On the PC: ssh omni@10.44.44.1.
- Internet via PC: the PC shares its internet over the cable and the console receives its IP.
- Remote services: On or Off (left/right). When On, Samba and the web file browser start (username and password: omni); SSH is always available.
The page shows the IP and commands for the PC and refreshes automatically. USB networking and flash-drive mode use the same port: enabling one automatically disables the other (leaving flash-drive mode restarts the console once, and USB networking turns on automatically afterward).

# Controls
“Test controller” shows the R36S with each button lit when pressed, the L2/R2 triggers, and analog stick positions. To exit, hold SELECT + START for 1 second (B is tested too).
“Swap buttons”: On swaps A with B and X with Y.
“Shortcuts”: combinations with the FN button that work inside games (see Shortcuts below).
Power button: one press opens Power (Cancel, Suspend, Restart, and Shut Down); pressing it again with the menu open safely shuts down. FN + power shuts down immediately, closing the game and saving everything first. Holding power for about 8 seconds always forces shutdown: this is handled by the power chip, not Omni36OS. The reset button restarts the hardware and cannot be changed.
“Fix shortcuts” restarts the service that controls brightness and volume with the buttons.
Services that fail at boot appear here. The dmc-governor failure (RAM tuning) can be fixed with one button; the systemd-remount-fs failure is known and harmless in Omni36OS.

# Shortcuts (under Controls)
They work while a port is open. Each shortcut can be enabled or disabled on the page; the buttons below are the ones currently assigned:
«fps»: cycles through FPS; FPS and CPU; FPS, CPU, and GPU; FPS, CPU, GPU, and used RAM (MB); hidden. All appear in the same pill. The counter is in the top corner and shows frames per second, temperature, and battery. FPS is green at 50 and above, yellow from 28 to 49, and red below that. Temperature is yellow from 65 °C and red from 75 °C. Battery is yellow at 30% or below and red at 15% or below; while charging, a green lightning bolt appears.
«limite»: toggles the 30 FPS limit. In a lightweight game, this saves battery and reduces heat. A purple line on the counter indicates the limit is on.
«captura»: takes a screenshot in the images folder inside the game folder (e.g. ports/daytona/imagens), as a .bmp named with the port and time, without the counter. Works on any card. “SCREENSHOT SAVED” appears at the bottom center. Outside a game, FN + Y saves an Omni36OS screen capture as PNG in the images folder on card 1 (EASYROMS/imagens); it can be viewed in Files.
«fechar» (hold for 1 s): closes the game and returns to Omni36OS. Use for a frozen port or one with no exit option. This shortcut is fixed.
“Customize a shortcut”: choose the shortcut and press the new key; it becomes FN + that key. Omni36OS rejects keys already used by the system or another shortcut. “Restore default buttons” undoes this (FN + X, FN + B, and FN + Y).
Using the power button while a game is open: the game freezes and the Power menu appears over it with the same options (show counter, limit to 30 FPS, screenshot, and close game), as well as suspend, restart, and shut down. Screenshot and counter settings apply when the game resumes.
The system (ogage) already uses: FN + up/down and FN + volume for brightness; FN with L1/R1, left/right, A, L3, and R3 for system controls; SELECT + FN speaks the battery level; FN + power shuts down after saving everything.
The counter, limit, and screenshot work in ports that render with OpenGL ES (most of them), including 32-bit ports. Ports that replace LD_PRELOAD (such as Cuphead) do not support the counter, limit, or screenshot: the shortcut displays a warning once per play session. Close still works, including for ports that run separately. While FN is held, the shortcut key is reserved for Omni36OS and the game does not receive it.

# Battery (under Display & Sound)
The panel shows charge, whether the battery is charging, brightness, and processor mode. When brightness is high or the processor is at maximum, a one-button power-saving suggestion appears. Adjust the processor in Performance.
Low battery (the R36S percentage is unreliable, so the thresholds are high): at 30%, Omni36OS suggests connecting the charger; at 15%, it suggests saving progress (in a game, the counter appears with the battery in red). At 10%, without a charger, Omni36OS closes the game and gives it time to save, saves everything, and shuts down instead of letting the console switch off suddenly.
“Calibrate battery” opens the calibration page. Calibrate if the percentage jumps or the device shuts down with charge remaining:
1. Charge fully and unplug the charger.
2. Tap “Start calibration” and use the console normally (you can play) until it shuts down by itself. One sample per minute is saved in /usr/local/etc/battery-cal.
3. Turn it on, charge it, and tap “Apply curve”. The percentage will then track your battery.
“Restore factory curve” undoes this.

# Apps
“Music” plays music (mp3, as well as ogg, flac, and wav) from the cards’ music folders: EASYROMS/musicas⟦ and, with card 2, ROMS2/musicas⟧. The card 1 folder is created automatically.
Each folder shows the tracks directly inside it and its subfolders; A on a subfolder opens it, A on a track plays the folder starting at that track, Y plays the entire folder, and B goes back. With “Read subfolders” on, playing a folder includes tracks from subfolders, one level at a time.
On the Now Playing screen: A pauses, left/right changes tracks, L1/R1 skips back/forward 10 seconds, Y changes the visualization, and B returns to the list (music continues; X returns to Now Playing). Leaving Music stops playback.
Options (START, inside the app): “Visualization”: Album Cover (folder image such as cover.jpg, or cover embedded in the mp3), Bars, Waves, Ring, or Aurora, reacting to the sound. “Turn screen off”: while music plays and no buttons are pressed, the screen backlight turns off after 30 seconds, 1, 2, or 5 minutes (or Keep on); any button turns it back on.
Folders are indexed (name, title, and artist from tags): only changed folders are read again, and the list stores only paths.
“Videos” plays videos from the cards’ videos folders (EASYROMS/videos, created automatically⟦, and ROMS2/videos⟧), using ffmpeg’s open codecs: mp4, mkv, webm, avi, and others (H.264, H.265, VP8, VP9, AV1, MPEG-4). A pauses, left/right skips back/forward 10 seconds, L1/R1 skips 1 minute, and B goes back. Videos up to 720p play well; above that, performance depends on the codec. Music stops while a video is playing.
“Notes” is a simple notepad: text files in the notes folder on card 1 (EASYROMS/notas). In the list, the first line creates a note and X deletes one (with confirmation). Opening a note shows the entire text: up/down scrolls and L1/R1 skips a page. A edits the whole note, like a typewriter: text wraps automatically and moves up when a line fills; Enter starts a new line; L1/R1 move the cursor to the line above or below; START saves and SELECT exits without saving.
In Files, opening music, a video, or text (txt, md, log, ini, cfg, conf) opens the appropriate app; B returns to the folder.

# Performance
In the menu, the processor, GPU, and memory stay at minimum: the console stays cool and battery lasts longer. Only video playback makes the processor scale with load. When a port opens, everything rises to the limits below; when you return, it drops again.
Processor limit (in ports): 1296 MHz is standard. 1368 to 1512 MHz is overclock (OC).
GPU limit (in ports): 520 MHz is standard; 600 MHz is overclock.
Overclock is available only when the device is below 70 °C. If it gets hot with OC on, Omni36OS suggests returning to standard settings.
Extra memory (zram): off by default. 256, 512, or 768 MB of compressed RAM helps heavy ports that close due to lack of memory. Takes effect immediately and on future boots; uses a little processor power.
“Unlock overclock” changes the boot hardware file (DTB): unlocks 1368 to 1512 MHz and 600 MHz GPU. It has a lockout: a red warning with a countdown, then press A five times. Omni36OS saves a copy of the DTB before changing it. Takes effect after restarting; choose the limit in “Processor limit” and “GPU limit”.

# Cards
Everything about where games are stored: cards, flash drive, and USB port. Actions that restart or erase are at the bottom of the page.
⟦“Game source”: ROMS (card 1), ROMS2 (card 2), or ROMS and ROMS2. After changing it, leaving the page (B or START) makes Omni36OS scan games and ports again once and updates the library and Test Ports. With both selected, games from both cards appear in one list. Without the second card (ROMS2), this option does not appear and everything comes from ROMS. Before removing card 2, use “Eject card 2”: removing it while mounted can corrupt it, and Omni36OS displays a red warning.⟧
⟦“Eject card 2” saves pending data and unmounts card 2 so it can be removed without shutting down; when a card is inserted but unmounted, “Mount card 2” appears. The page refreshes automatically when the card is inserted or removed. If removed without ejecting, a red warning appears (when returning from a game, if applicable): reinsert it, mount it, and use “Check and repair games”.⟧
“Card details”⟦ (“Cards details” with two cards)⟧: shows the make, capacity, free space, and used space for the entire card, and tests reading and writing on each card; this takes up to a minute. Free space appears in the panel. Generic unbranded cards are often slow and more prone to failure: details warns when the card’s brand cannot be identified (this is not an alert).
Omni36OS warns when a card is over 90% full or has less than 1 GB free.
“Check and repair games” restarts the device and runs Omni36OS repair (fsck.exfat) with the card unmounted. The result then appears on this card, and the log is saved to /boot/sd2_scan.log (second card) or /boot/sd1p3_scan.log (system card only).

Flash-drive mode:
Turn on flash-drive mode: with the data cable connected to a PC, the ⟦ROMS2 (card 2) or ⟧ROMS (card 1⟦; with two cards, choose under “Partition on PC”, which appears only when card 2 is present⟧) partition appears as a flash drive for copying ports.
Enabling it restarts the device in flash-drive mode. Wi-Fi does not work while it is enabled because it uses the same port. If USB networking is on, it is disabled automatically.
When the PC connects, Omni36OS closes to release the partition. During copying, the screen shows “COPYING TO CONSOLE...” or “COPYING TO PC...”. If the PC is still writing, B waits for the copy to finish. Ejecting on the PC, unplugging the cable, or pressing B (or Select + Start) returns the partition to the console and restarts it automatically in normal mode, with Wi-Fi. The mode applies only to that boot: any restart returns to normal mode.
“Restore boot” restores the original boot file if something goes wrong.
“Clean Mac junk” deletes ._ and .DS_Store files created by macOS when copying. They appear as phantom ports in the library. The scan takes up to a minute.
“Mount flash drive” mounts a flash drive connected to OTG at /mnt/usbdrive (FAT, exFAT, or NTFS). Once mounted, the same button becomes “Unmount flash drive”: use it before removal. With this option selected, the left panel shows whether the flash drive was detected, what it is, and whether it is mounted.

# Tools
“Files”: browses the card (/roms⟦, /roms2⟧) and flash drive. A opens a folder (or an image full-screen: left/right moves to the next one, A shows or hides the name, B goes back); B goes up one level; X opens item options (copy, move, rename, delete); START opens folder options (paste here, new folder). Music, videos, and text open directly in the appropriate Apps app. To copy: X > Copy on the item, go to the destination folder, then START > Paste here. Deletion requires confirmation, with Cancel selected by default.
“PortMaster” opens full-screen; Omni36OS returns when it closes. To copy, move, rename, or delete, use “Files” here in Omni36OS.
Other system tools are in the cards: Test controller (Controls), Change password (General > Security), Wi-Fi and USB cable network (Network), flash drive (Cards), Battery calibration (Display & Sound), Unlock overclock (Performance). Anything that changes boot opens a red warning with a countdown; Cancel is selected from the start.

# Test Ports (under Tools)
Shows ports from the folders selected in Cards > Game source.
Choose a port and press A: Omni36OS closes, the port launches as it does from the library, and is ended automatically after 15 seconds. Omni36OS returns with the result.
Passed: the port stayed open for 15 seconds.
Failed: the port closed earlier. The report is saved in logs/teste de ports/teste_<port name>.txt on card 1 (read it in Notes > Logs), with the port output, logs from its folder, kernel messages, and system state.
The list shows each port’s latest result, and failures become alerts on the card.
“View reports” opens reports in Notes, read-only.
“Missing runtimes” searches ports for PortMaster runtimes that are not on the card; when Wi-Fi is connected, it asks whether to download them. Each test report also warns about missing runtimes and incomplete copies (0-byte files from a copy that stopped midway).
The test also ends processes a port leaves running separately (such as Cuphead), so the game is not left running underneath the menu.
“Clear failure warnings” removes the card alert after you have seen the failures. The result stays in the list until the port is tested again; if the new test fails, the warning returns.
Ports with their own menus (such as Daytona USA and NFSU1) pass when the menu opens: the test does not press buttons.
When a port fails, Omni36OS reads the report and shows the likely cause (Windows script, file without permission, out of memory, PortMaster runtime, library, glibc, game files, exFAT card, crash). If a safe fix is available, “Fix and test again” appears: it fixes the issue (permissions, script format, or extra memory) and tests again. If it still fails, the fix is undone. The diagnosis is also included in the report.

# General
What belongs to you and Omni36OS, like the iPhone Settings app, in this order:
“Player name”: appears in the menu greeting.
“Security”: passwords and lock (see below).
“Backup”: exports and imports settings (see Backup below).
“Check for update” (requires Wi-Fi): checks GitHub for a new version. Before installing, Omni36OS downloads and verifies everything; the current version is kept. If the new version does not reach the menu after 3 attempts, the previous version is restored automatically and a warning explains why. “Revert to previous version” appears after an update and reverts on request. Keep the charger connected during the update.
“Check Everything”: shows only items needing attention across all cards (display and sound, battery, performance, cards, and services), with each line showing its source card. If there are no alerts, “All clear” appears. Details are on each card.
“About”: this manual, care guide, release notes for each version, and credits (including projects used as a base).
“Reset system”: returns to the first-boot state. Clears the player name, password lock, and theme; disables extra memory (zram); and restores the processor (Balanced, 1296 MHz), GPU (520 MHz), and shortcuts to defaults; then asks for the name again. Ports, games, tests, and system and Samba passwords are kept.

# Security (under General)
All password settings are here. B returns to General.
“Change password” changes the omni user password (SSH, SFTP, and Samba; default password is omni) using the on-screen keyboard: D-pad selects, A types, B deletes, X inserts a space, Y switches letters and symbols (uppercase locks with two taps on the on-screen key), START confirms, and SELECT cancels (like the Android keyboard, it starts in uppercase; passwords start in lowercase). The password is requested twice.
“Samba password” resets only the shared-folder password (user omni), without changing the SSH password.
“Password lock”: when enabled, the console asks for the password at startup before showing games (the power button still opens Power to shut down). The password is stored in plain text at EASYROMS/senha/senha.txt: if you forget it, open the card on a PC and read it. Deleting this file disables the lock. To disable it on the console, the current password is required.

# Backup
General > Backup > Export or Import.
The backup is a system snapshot: Omni36OS version, all settings (shortcuts, Performance, overclock, zram, display, gamma, sound, brightness, button swap, music), Wi-Fi networks, console name, and SSH keys. Games, ports, and saves are excluded (they are on the cards).
Export asks where to save: system card (/roms/backup/omni36os), ⟦second card (/roms2/backup/omni36os), or ⟧flash drive (/mnt/usbdrive/backup/omni36os). Only locations currently available on the console appear, and the last selected location is selected. The full path appears when finished.
Import opens the backup folder; navigate through folders with A (“..” goes back). Each file shows which module it belongs to, and only a backup for the correct module can be imported.
Import restores the console exactly to the backup point: anything changed or added afterward is undone, including the version. At the end, Omni36OS asks you to restart. Before importing, it saves the current state as “...-antes-de-importar.tar.gz”.
Settings only: saves, states, cores, shaders, themes, and databases are excluded."""

CUIDADOS_EN = """# Before anything else
Back up the system card to a PC from time to time. An image of the entire card can save you from almost any problem.

# USB flash drive
Always eject the flash drive on the PC before unplugging the cable. Removing it during a copy can corrupt files.
Do not turn off the console while it is connected to the PC.
⟦With a second card, prefer sharing /roms2. Without one, the⟧⟪The⟫ PC receives /roms (the games partition on the system card): copy only to the games and ports folders.
If the console does not return to normal, use “Restore boot” in Cards (last item).

# Check and repair the card
The device restarts and spends a few minutes checking. Do not turn it off or remove the card during this time.
Repair deletes corrupted entries: if the card already had errors, a damaged file may disappear. Keep a backup.

# Restore and update
Before updating Omni36OS, copy the card’s BOOT partition to a PC and check Display & Sound > “Screen details” to see which model to choose.

# First boot
The first time it starts, Omni36OS detects the screen automatically: if “Can you see this screen?” appears, press any button. If the screen stays black, do not turn it off: it tests the next screen and restarts automatically (each attempt takes less than a minute). If none is confirmed, everything is restored to how it was.
To run this again later, create the file omni36os-tela/testar on the card’s BOOT partition using a PC.

# Overclock
Overclocking means using the chip above the level guaranteed by the manufacturer. It can cause crashes and, over time, increased wear.
The Omni36OS kernel protects the device: it throttles at 70 °C, limits performance at 85 °C, and shuts down at 115 °C. Even so, if it freezes or games close by themselves, return to 1296 MHz (CPU) and 520 MHz (GPU).
Omni36OS does not enable overclock when the device is above 70 °C.

# Battery and heat
Avoid overclocking when the battery is low or the device is hot.
When the battery is low, charge it before using flash-drive mode or updating.

# Cards
Generic cards fail more often. If a card is reported as slow or unbranded, keep backups of your saves.

# Port testing
The test launches the actual port and forcibly ends it after 15 seconds. Ports that write configuration or save data as soon as they launch may lose what they were writing; test only after backing up the save.
Do not press buttons during the test: the port receives the inputs.
If the port freezes the screen, hold the power button to restart; in this case, no result is saved.

# Backup and import
Import also restores the Omni36OS version from the backup. Afterward, “Check for update” can install the newer version again if you want.
Keep copies of backups outside the console (on a PC, using the flash drive).

# When shutting down
Shut down through the Power menu (power button); never hold the power button. Through the menu, Omni36OS saves everything and unmounts boot before shutting down.
To close a frozen port, use SELECT + START (hold for 1 s) before considering a forced shutdown."""

CREDITOS_EN = """# Omni36OS
Ports-only system for the R36S, created by mpjsilva, with help from Claude (Anthropic) during development. GNU GPL v3.0 license. github.com/mpjsilva/omni36os

# Special thanks
h1ghland3r, the YouTuber who made the project possible: thank you for the time you spent testing the project and reporting bugs xD. beacons.ai/h1ghland3r

# Base system
dArkOSen by djparentx: the image used as the basis for Omni36OS, with the screen catalog for R36 models, the battery calibration tool (rewritten by Omni36OS), the DTB patch, and safe shutdown. github.com/djparentx/dArkOSen-R36S

# Ports and tools
PortMaster and its community: the ports storefront, ports, and game data. github.com/PortsMaster/PortMaster-GUI
gptokeyb: controller input as a keyboard and mouse in ports. github.com/PortsMaster/gptokeyb
ogage: system shortcut keys, included with dArkOSen.
File Browser: network file browser. github.com/filebrowser/filebrowser
BatteryPlus by Mikhailzrick. github.com/Mikhailzrick/knubat.components

# Free libraries and programs
SDL2, SDL2_ttf, SDL2_image, and SDL2_mixer, zlib license: display, controls, fonts, images, and music. libsdl.org
FFmpeg, LGPL/GPL license: videos. ffmpeg.org
Debian, Linux, NetworkManager, Samba, systemd, and all the free software underneath.
Poppins font, OFL license: github.com/itfoundry/Poppins
Tabler icons, MIT license: github.com/tabler/tabler-icons

# Library data
Steam (covers and descriptions), Wikipedia (descriptions in Portuguese; text under CC BY-SA 4.0), and DuckDuckGo (images when the other sources have none).

# Community
The R36S community, which documents models, screens, clones, and repairs and makes this project possible. Thank you!"""



# Reviewed English release-note editions; entry order matches NOVIDADES above.
NOVIDADES_EN = {
    '1.16.0': ['Emulators (optional): Tools > Emulators shows in the library, after the ports, the RetroArch systems with games on the card. X and Y switch systems; the Ports card warns about missing BIOS.', 'Image with emulators: sudo EMULADORES=1 imagem/gerar-imagem.sh builds Omni36OS-<version>-emu.img.xz, with RetroArch and the option already on. The default image stays ports-only.'],
    '1.15.31': ['Status bar: anchor icon while the internet comes through USB phone tethering.'],
    '1.15.30': ['USB tethering: more Android phones recognized, with the new Phone tethering option in the Network card.'],
    '1.15.29': ["What's new before updating: the screen now follows the console language.", 'Runtimes: fixed the download error when space runs out or the file does not match.'],
    '1.15.28': ['Full English translation: messages, battery warnings, tool dialogs, port test reports and USB drive mode follow the chosen language.', 'First boot asks for the language before the player name. Reset the system asks again.', 'In English, error messages no longer appear as success.'],
    '1.15.27': ['Wi-Fi: the adapter is no longer powered off after 10 minutes without a network (the base Wi-Fi monitor disabled the radio and removed the driver, preventing Wi-Fi from reconnecting automatically).', 'Ports copied on a PC with the card in a reader now appear in the library without using Refresh Ports.', 'One-time system cleanup, with an on-screen menu: removes services, packages, documentation, and languages not used by a ports-only system (frees about 700 MB more).', "Credits: special thanks to h1ghland3r for testing the project and reporting bugs. Credit links are navigable: ↑↓ move focus and A opens the QR code (mpjsilva's GitHub and h1ghland3r's links)."],
    '1.15.26': ['Tools > Change DTB: change the console screen without a PC. A red warning includes a 10-second hold; the console restarts in ‘DTB search mode’ and tests screens one by one. L1 + R1 at startup still works.', 'The dArkOSen DTB catalog is included with Omni36OS and updates automatically; the clone-console warning is now based on the model and no longer appears unnecessarily.', 'Cards: Eject Card 2 and Mount Card 2 let you remove and insert the card without shutting down. Removing it without ejecting shows a red warning (also when returning from a game).', 'When Card 2 is absent, ROMS2 is hidden everywhere: Game Source, Files, Images, runtimes, and Help. The Cards page refreshes automatically when the card is inserted or removed.', 'Ports opens with the most recently played port selected.', 'Test Ports: View Reports (opens in Notes) and Missing Runtimes (searches ports and downloads over Wi-Fi). Reports now flag incomplete copies (zero-byte files) and missing runtimes.', 'Test Ports also closes processes a port leaves running separately (such as Cuphead); previously the game remained behind the menu and the screen flickered.', 'FN shortcuts now detect ports that run separately (Cuphead, Blasphemous). For ports that do not support the FPS counter, limit, or screenshot, a warning appears once per play session.', 'SCREENSHOT SAVED appears at the bottom center, no longer underneath the resource monitor. FN + Y in the menu works again with the File Browser enabled.', 'USB drive mode shows when the PC is copying to or from the console, and B no longer interrupts a copy in progress.'],
    '1.15.25': ['Apps now includes Images: screenshots (FN + Y) from the menu and each game, newest first. Left/right changes images; X deletes.', 'System logs are collected in one folder on Card 1: logs/<function> (system, ports, USB drive, display, network). Test Ports reports are saved to logs/port test/port_test_<port name>.txt. Older reports were moved there.', 'Notes can read logs: System Logs opens each log read-only at the end (the newest entries).', 'Tools > Refresh Ports rereads the port list, covers, and descriptions when a copied port does not appear.', 'Wi-Fi: an adapter plugged in while the console is on and stuck in disk mode is now re-enabled automatically.', 'USB drive mode respects the ROMS2 selection (previously it fell back to ROMS at startup), and ‘Partition on PC’ only appears when Card 2 is present.'],
    '1.15.24': ['Port covers and descriptions can be supplied in the infos folder inside ports, using the game name: for abismo.sh, use abismo.txt (description) and abismo.png, .jpg, or .webp (cover). An optional abismo.json can provide the name, studio, year, and genres.', 'R36XX: USB drive mode warns that built-in Wi-Fi shares the OTG port, so the PC may not detect the console; the USB-drive log records the model.', 'Credits and text now identify only dArkOSen as the base; File Browser is presented as Omni36OS.'],
    '1.15.23': ['USB drive mode lasts for one boot: ejecting it on the PC, unplugging the cable, or pressing B returns the console to normal mode and restarts it with Wi-Fi. Any restart during this mode also returns to normal.', 'USB drive mode logs USB-port status while waiting for the PC (/home/ark/usb-disco.log), helping diagnose why the PC does not show the drive.'],
    '1.15.22': ['For a card moved to another console or a different screen: when ‘Loading’ appears at startup, hold L1 + R1 until you hear an arpeggio. The test screen replaces it and Omni36OS detects the screen again without a PC.'],
    '1.15.21': ['The default A, B, X, and Y button mapping applies only to new images on first boot. Updating no longer changes the selection made in Controls > Swap Buttons.'],
    '1.15.20': ['Buttons now behave as labeled by default (dArkOSen previously swapped A and B). Swap them in Controls > Swap Buttons if you prefer.', 'Apps now includes GeForce NOW (cloud gaming) and Moonlight (stream games from your PC over your home network). Each has Install/Update; GeForce NOW lets you choose whether FN belongs to the system or to the app.', 'The power menu opens immediately during a game. Left/right adjusts the counter, 30 FPS limit, and mouse mode without closing the menu. New: Type Text using the Omni36OS keyboard.', 'Mouse mode (FN + R3 or the power menu): the right stick moves, A or R3 clicks, B is right-click, and the left stick scrolls.', 'Carousel counter on FN + X: FPS; CPU; GPU; RAM used; hide.', 'Power now freezes separately running ports correctly (such as Gran Turismo); the menu no longer flickers.', 'When FPS cannot be read, CPU and GPU in Automatic mode stay at maximum without overclocking.', 'PortMaster runtimes are included in the image and update automatically when Wi-Fi connects.', 'Battery Calibration now uses one button that toggles between Start and Stop.', 'New ports appear in the list without reopening Omni36OS.'],
    '1.15.19': ['CPU and GPU in Automatic mode (Performance): in games they start at minimum and rise one step at a time only until the game reaches 60 FPS (or 30 with the FN + B limit). GPU load decides which rises first. Maximum is 1296/520 MHz, or unrestricted with overclock unlocked. New images include this setting.', 'The FPS counter now also works in 32-bit games (Asphalt and others), along with screenshots and the FPS limit.', 'FN + X cycles through: FPS; FPS with CPU and GPU frequencies in the same pill; then hidden.', 'While FN is held, the shortcut key (FN + X, B, Y) is no longer sent to the game. Omni36OS system shortcuts using FN continue to work.', 'Backup is now a snapshot: it saves the Omni36OS version, all settings, Wi-Fi networks, console name, SSH keys, sound, and brightness. Restoring returns the console exactly to the backup state and asks you to restart.'],
    '1.15.18': ['Missing PortMaster runtimes are downloaded before launching a port (they are no longer copied from Card 2). Without internet, copy the file from a PC to tools/PortMaster/libs on the system card.', 'Port-test results now keep long text, such as the report path, inside the box.'],
    '1.15.17': ['Ports now fetch missing requirements: before launch, Omni36OS finds the PortMaster runtimes a game uses (Mono, Godot, Java, etc.) and copies them from Card 2 or downloads them, with a progress bar. This fixes games such as TMNT that requested Mono even when it was already on the card.', 'Card 2 games: folder changes made while a game runs are always undone when it closes, even if part of the game remains running. Previously, Card 1 ports could disappear from the list and Card 2 ports could appear twice.'],
    '1.15.16': ['Port library: A now launches the game directly. The second screen (details with Play and Back) was removed because the list already shows the cover and description.'],
    '1.15.15': ['Low-battery warnings now also appear over system tools: the tool pauses, the warning appears, and after OK (or connecting the charger) it continues where it left off.'],
    '1.15.14': ['The low-battery warning now disappears automatically when the charger is connected, and ‘Charging’ is shown.', 'LED: while charging, low battery no longer makes the LED blink (for both new cards and new images).'],
    '1.15.13': ['Cover and description searches now work on networks whose router does not answer IPv6 queries: Omni36OS resolves names using IPv4 only (previously each site took about 6 seconds just to resolve, causing the search to time out).'],
    '1.15.12': ['Status pill: Wi-Fi is shown as connected only when there is a real network connection and IP address (the Realtek adapter reported ‘on’ even with no network).', 'A Realtek Wi-Fi adapter stuck in ‘disk’ mode after boot (sometimes the switch to Wi-Fi mode is lost) is now detected and re-enabled automatically by Omni36OS.'],
    '1.15.11': ['Card 2 ports now launch even without the game folder on Card 1: while one is running, /roms/ports points to the Card 2 ports folder (PortMaster scripts look for the game there).'],
    '1.15.10': ['Port list: each game now shows which card it is on (SD-card icon with number 1 or 2), and game details say ‘Card 1’ or ‘Card 2’.'],
    '1.15.9': ['Safer screen selection on first boot: each test changes only the screen entry in the console’s original DTB. boot.ini, u-boot, and other hardware settings are never replaced, so the wrong screen can blank the display but cannot prevent booting.', 'Faster screen selection: each screen is tested for 10 seconds and the process starts earlier in boot. Worst case with 12 screens dropped from about 8 to about 5 minutes.', 'During screen search, the LED flashes red and green. The prompt plays a ding-dong through the speaker and confirmation plays an arpeggio.'],
    '1.15.8': ["Short pages (What's New, Help) no longer show scrolling buttons when there is nothing to scroll."],
    '1.15.7': ["Check for Update now shows the new version’s release notes before installation (What's New button), fetched from GitHub.", 'Update and Revert to Previous Version now open with ‘Not now’ or ‘Cancel’ selected, preventing accidental installation with one extra press.'],
    '1.15.6': ['USB Network: the page shows which mode is enabled (‘Universal mode: on’) and when networking is off.', 'USB network compatibility: the DHCP client is shown on one line; missing dhcpcd is no longer a problem (only one client is needed).'],
    '1.15.5': ['USB Network and USB drive mode now switch automatically: enabling one disables the other, with no manual warning (leaving USB drive mode restarts once and USB networking turns on automatically afterward).', 'Scan for Networks turns Wi-Fi on if it is off. Without a Wi-Fi adapter, the Network card mentions this without an alert.', 'Status pill: the Wi-Fi icon shows signal strength, dims when disconnected, is crossed out when the radio is off, and updates on every screen.'],
    '1.15.4': ['Omni36OS is now open-source under the GNU GPL v3.0 license.'],
    '1.15.3': ['Complete credits are available under General > About: base system, PortMaster, gptokeyb, ogage, File Browser, BatteryPlus, SDL2, FFmpeg, fonts, icons, data sources, and the R36S community, with links.'],
    '1.15.2': ['Shutdown and restart now show the goodbye screen directly, without briefly flashing the menu or welcome screen first.'],
    '1.15.1': ['Keyboard: X inserts a space and Y switches between letters and symbols. Caps lock is toggled on the on-screen key with a double press. This applies throughout the system.'],
    '1.15.0': ['Notes: opening a note shows the whole text for reading with scrolling. A edits the full note like a typewriter: text scrolls as lines fill, the keyboard includes Enter, L1/R1 move the cursor between lines, and START saves.'],
    '1.14.2': ['Videos and Notes lists are full-screen like Music, with the status pill (Wi-Fi, volume, battery, temperature, and time). Video playback remains full-screen. Deleting a note asks for confirmation, with Cancel selected by default.'],
    '1.14.1': ['The release manual was revised with a new introduction, EASYROMS paths for video and note folders, Cards in Check Everything, SDL2 and FFmpeg credits, and no mention of RetroArch, which is no longer included.'],
    '1.14.0': ['The new keyboard is consistent throughout the system and Android-like: it starts uppercase and returns to lowercase after the first letter (and uppercase again after a period); double-tapping Shift locks it, Y locks it directly, and X switches letters and symbols. Passwords start lowercase.'],
    '1.13.0': ['Apps now includes Videos (a simple player using FFmpeg’s open codecs) and Notes (a text editor with keyboard and punctuation).', 'In Files, music, videos, and text files open directly in the appropriate app.'],
    '1.12.7': ['The Storage card is now called Cards, with a font size matching the other cards and labels for USB drive, space, and repair.'],
    '1.12.6': ['The Display & Sound card title is restored (it had been clipped); the subtitle still mentions brightness, sound, and battery.'],
    '1.12.5': ['Apps now shows only the app list; Music options (visualization, screen-off, and subfolders) are inside the app under START.'],
    '1.12.4': ['Music: the status pill (Wi-Fi, volume, battery, temperature, and time) now appears in the player; visualization names use the system hint, and FN screenshot capture wakes the screen first if it is off.'],
    '1.12.3': ['Music now turns the screen back on automatically if the launcher restarts while the display is off.'],
    '1.12.2': ['Music now has an Album Cover visualization, using folder art or artwork embedded in the MP3. The cover also appears in the now-playing bar.'],
    '1.12.1': ['Password-protected Samba now allows only the omni user, and the network exposes only Card 1 and Card 2.'],
    '1.12.0': ['New Apps card: Music plays MP3s from the cards’ music folders, including subfolders, with visualizations (Bars, Waves, Ring, and Aurora) and automatic screen-off during playback.', 'Battery information now appears under Display & Sound. Ports is centered and highlighted whenever the menu opens.', 'Each card now describes its three functions.'],
    '1.11.11': ['Shortened the Swap Buttons text.'],
    '1.11.10': ['Revised overclock-unlock text and button help.'],
    '1.11.9': ['When the password lock is enabled, unlocking overclock now requires the console password.'],
    '1.11.8': ['Overclock locking is now enforced: CPU speeds above 1296 MHz and GPU speeds above 520 MHz appear only after Performance > Unlock Overclock. Lock Overclock restores defaults.'],
    '1.11.7': ['Tools > Automatic Search now turns cover and description searches on or off.', 'The library now says whether it is searching for an image and description, only a description, or only an image. Missing results are not searched again, and searches do not run while a game is open.'],
    '1.11.6': ['Cover and description searches now run only when Wi-Fi is connected.'],
    '1.11.5': ['The library now shows ‘Searching for description…’ and ‘Description not found’ instead of metadata text.'],
    '1.11.4': ['Wikipedia descriptions are now in Portuguese and include release years for ports without PortMaster or Steam information.'],
    '1.11.3': ['When PortMaster and Steam have no covers or descriptions, Omni36OS now searches DuckDuckGo.'],
    '1.11.2': ['The ports-only library now reads only ports folders on the cards. Emulator folders are excluded, and scanning is nearly instantaneous.'],
    '1.11.1': ['Controls now has one option, Swap Buttons (On/Off), which swaps A/B and X/Y together.'],
    '1.11.0': ['Faster boot with no black screen: everything runs at maximum until the menu is ready (about 3 seconds faster), then switches to minimum. The logo and welcome screen continue directly into Omni36OS.', 'USB Wi-Fi starts automatically at boot; date, time, and time zone are set when internet becomes available, and volume stays at your chosen level.', 'Display & Sound has its own brightness, contrast, and volume panel. A/B and X/Y swapping is in Controls.', 'FN + Y captures the menu screen to the Images folder. Files displays images full-screen.', 'Card 2 appears automatically. Power always opens the power menu; FN + Power shuts down after saving everything.', 'SSH and browser access use omni/omni. Remote services are enabled only when network is available.', 'Visual updates: custom icons, higher-contrast text, button-art hints, and pixel-aligned layout. The Network card no longer shows an alert after Wi-Fi connects.'],
}


def novidades_text():
    """Build localized release notes; use the reviewed English entries when English is active."""
    import omni_i18n
    out = []
    english = omni_i18n.get_lang() == "en"
    for index, (ver, data, itens) in enumerate(NOVIDADES):
        out.append(f"# {'Version' if english else 'Versão'} {ver} ({data})")
        translated = NOVIDADES_EN.get(ver) if english else None
        for item_index, item in enumerate(itens):
            if translated and item_index < len(translated):
                text = translated[item_index]
            else:
                text = item if not english else f"[English translation needed] {item}"
            out.append(f"• {text}")
        out.append("")
    return "\n".join(out).strip()


def roms2_text(text, has=None):
    """⟦…⟧ só vale com o ROMS2 montado; ⟪…⟫ só sem ele. Sem ROMS2, a Ajuda não fala dele."""
    import os
    import re
    if has is None:
        has = os.path.ismount("/roms2")
    text = re.sub(r"⟦(.*?)⟧", r"\1" if has else "", text, flags=re.S)
    text = re.sub(r"⟪(.*?)⟫", "" if has else r"\1", text, flags=re.S)
    return re.sub(r"\n{3,}", "\n\n", text)


def _localized(text, english):
    """Return the Portuguese or English documentation copy for the selected language."""
    import omni_i18n
    return english if omni_i18n.get_lang() == "en" else text


def cuidados_text():
    return roms2_text(_localized(CUIDADOS, CUIDADOS_EN))


def creditos_text():
    return _localized(CREDITOS, CREDITOS_EN)


def manual(combos=None):
    """The guide with currently configured shortcut buttons (Controls > Shortcuts)."""
    import omni_combos
    combos = combos or omni_combos.defaults()["combos"]
    text = _localized(MANUAL, MANUAL_EN)
    for k in omni_combos.ACTIONS:
        text = text.replace(f"«{k}»", omni_combos.text(combos[k]))
    return roms2_text(text)
