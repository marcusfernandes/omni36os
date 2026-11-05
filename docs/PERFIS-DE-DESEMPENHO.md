# Perfis de desempenho do Omni36OS (MVP)

O MVP aplica temporariamente limites/governors de CPU, GPU e memória para **ports executados diretamente pelo launcher**, preservando um snapshot e tentando restaurá-lo ao fechar o port ou ao encerrar o launcher. A seleção usa o nome do alvo (`Path.stem`) comparado às chaves de `performance-profiles.json`; sem correspondência, usa `default`.

Exemplo de mapeamento:

```json
"ports": {
  "nome-do-port": "low_gpu"
}
```

O perfil padrão é `native`, sem alterações de clocks; os knobs ausentes são ignorados. Os perfis opt-in incluídos são exemplos: `balanced` limita CPU a até 1296 MHz e GPU a até 520 MHz; `low_gpu` usa esses limites de CPU e limita a GPU a 400 MHz. O gerenciador escolhe um degrau disponível que não ultrapasse o teto configurado nem o teto de segurança compilado. Erros de escrita são registrados e provocam tentativa de restauração.

## Limites e segurança

- A camada não muda resolução interna, não intercepta FBOs e não promete aumento de FPS. Um teto menor pode reduzir consumo/temperatura, mas também pode reduzir desempenho.
- Os comandos da biblioteca de jogos que usam `perfmax/perfnorm` ficam fora desta integração para evitar disputa de propriedade dos clocks.
- A escala EGL permanece desligada por padrão. O módulo `omni_scaler` oferece modos opt-in: `validate` (diagnóstico de swapchain), `cas` (Contrast Adaptive Sharpening em GLES 2.0 de passada única), `sharp` (Sharp Bilinear para pixel art/2D) e `pacing` (estabilizador de cadência de quadros). Nenhum modo é ativado globalmente por padrão.
- Snapshot em arquivo não sobrevive a uma queda de energia; na próxima inicialização deve-se verificar se o sistema restaura os governors. O console não foi alterado nesta etapa.
- Os valores, a restauração e o comportamento visual do scaler ainda precisam ser validados no R36S real, incluindo temperatura, estabilidade, FPS/frame time e retorno ao launcher. Não habilitar perfis específicos de jogo antes dessa medição.

## Scaler e Pacing Opt-in (`omni_scaler.so`)

O hook EGL `omni_scaler.so` (compilado para ARM64) pode ser ativado para testes específicos. No launcher PortMaster do NFSU2, configurar `OMNI_SCALING_MODE=cas` em `nfsu2.cfg` carrega `/opt/omni36os/hud/omni_scaler.so` apenas para esse jogo; a opção não muda clocks e permanece desligada por padrão. A variável `NFSU2_FPS` alimenta o alvo do pacing.

1. **Via Perfil em `performance-profiles.json`**:
   Atribuir o perfil `sharp_cas` ou `smooth_pacing` ao port desejado:
   ```json
   "ports": {
     "meu-jogo": "sharp_cas"
   }
   ```
2. **Via Variáveis de Ambiente no Port**:
   - `OMNI_SCALING=1`
   - `OMNI_SCALING_MODE=cas` (ou `sharp`, `pacing`, `validate`)
   - `OMNI_SCALING_SHARPNESS=0.6` (0.0 a 1.0)
   - `OMNI_SCALING_PACING=1` (estabiliza swap interval a 60 FPS)

3. **Log de Operação**:
   Registrado em `/dev/shm/omni36os-scaler.log` com resolução da superfície EGL, modo e parâmetros aplicados.

## Testes locais

`python3 -m unittest /srv/IA/jamerson/apps/Omni/Omni36OS/omni36os/tests/test_performance_profiles.py` cobre perfis de CPU/GPU e aplicação/limpeza de configurações de escala.
`apps/Omni/Omni36OS/omni36os/port/omni36os/hud/run-scaler-local.sh` compila e valida todos os modos do scaler EGL (`validate`, `cas`, `sharp`, `pacing`) em ambiente EGL surfaceless local.
