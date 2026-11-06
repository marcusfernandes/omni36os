# Ancoragem USB (Android)

O kernel 4.4.189 não reconhece essa classe como RNDIS. Sem fonte do kernel, a solução é:

- `cdc_ether.ko`: original com a checagem de `usbnet_generic_cdc_bind` alterada (.text 0x3e8–0x3ff, offset de arquivo 0x450): aceita EF/01/01 e também EF/04/01. Só é instalado se o módulo original tiver md5 4102f890…. Vai em `/lib/modules/4.4.189/updates/`, seguido de `depmod -a 4.4.189`.
- `omni-ancoragem-bind.sh` em `/usr/local/sbin/` e `90-omni-ancoragem.rules` em `/etc/udev/rules.d/`: vinculam o celular ao `rndis_host` via `new_id`, com 1630:0042 como referência de `driver_info`.
- Perfil `omni-ancoragem` do NetworkManager: métrica 100, Wi-Fi fica como reserva.

`usbnet_generic_cdc_bind` vem do `cdc_ether.ko`, então ele precisa estar carregado antes do `rndis_host`.

`instalar.sh` aplica tudo isso. O `launch-direct.sh` o chama a cada início do launcher, então atualizações do Omni36OS levam a ancoragem junto. O Wi-Fi continua ativo e assume se o cabo sair. Ao trocar de celular ou reconectar, pode ser preciso ligar a ancoragem de novo no aparelho.

Cobertura: RNDIS E0/01/03, EF/01/01, EF/04/01 e 02/02/FF, CDC-ECM e CDC-NCM. Testado apenas no POCO F7 Pro (EF/04/01).

Instalador por port: `scripts/pacote_ancoragem.sh` gera o zip em `dist/`.
