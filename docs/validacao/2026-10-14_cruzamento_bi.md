# Validação: plataforma × BIs atuais (14/10/2026)

> **Pergunta:** os números da plataforma batem com os dos BIs atuais?
> **Escopo:** todas as fazendas e todos os meses que o BI mostra (jul/2024 a set/2026), com os dados reais dos
> datalakes do BI.
> **Resposta curta:** batem. Toda divergência encontrada tem causa identificada, e a maioria é um defeito do próprio
> BI ou um problema do dado de origem. Não sobrou diferença sem explicação.
>
> **Segunda rodada (§9), com o adapter real lendo os 230 `.xlsm`:** nas 110 fazendas cujo arquivo não mudou desde o
> snapshot do BI, compras, abates, nascimentos, mortes, rebanho médio, área e créditos batem 100%, e os débitos batem
> no total ao centavo. A rodada achou e corrigiu 8 problemas no adapter e no motor. O mais grave: na virada de safra
> a carga apagaria a safra anterior. A carga inicial do histórico (Q6) foi decidida e implementada (§10): com ela,
> as fazendas que viraram de safra voltam a bater com o BI na safra 25/26.
>
> **KPIs da página Movimentação do Gado (§12):** em 300 filtros sorteados, rebanho médio e lotação (cab e UA),
> nascimentos, mortes e compras (realizado e meta) batem 100%; vendas, só A3/A20; o estoque final bate em 93,7%, e o
> resto são as diferenças de estoque mensal já explicadas.
>
> **Página Vendas (§13):** em 900 filtros sorteados, abate (realizado e planejado) bate 100% em cabeças, faturamento,
> preço da @, peso médio e rendimento. Na venda em pé, toda diferença tem causa: venda sem cliente (A3), total vazio
> (A17) e um achado novo, meta com data "DDMM/AAAA" (A20, decisão Q8: fica na quarentena e vai para a aba Pendências).
>
> **Página Compras (§13):** cabeças, investimento, preço do kg e peso médio batem 100%; o preço da @ e o ágio
> diferem só por arredondamento da arroba na planilha (A21) e linha com total errado (A22, agora avisada em Pendências).
>
> **Páginas Nascimentos, Mortes e Transferências (§14):** nascimentos (realizado e meta) e mortes realizadas batem
> 100%, inclusive a mortalidade sobre o rebanho médio e as mortes por causa; a mortalidade sobre nascimentos difere só
> pela regra de acumulado (P3). Nas transferências, as cabeças realizadas batem 100%, e o resto tem causa: A17, A21,
> A22 e dois achados novos de precisão (A23, A24). Pergunta nova: Q10 (ajuste de estoque lançado como morte).
>
> **Página Financeiro (§15):** receitas (realizado e meta) e despesas batem 100%. Desembolso, custeio e os valores por
> cabeça diferem só pela classificação das contas (P4): a plataforma usa a `dim.centro_custo` e a planilha marca as
> contas de outro jeito, sobretudo compra de gado e financiamentos (Q11). Também A20, P2 e A3.
>
> **Página Previsto × Realizado (§16):** a matriz bate nos investimentos e nos outros débitos e créditos; nas demais
> linhas, toda diferença tem causa: o total do BI sem os outros débitos e créditos (P1, a plataforma segue a D1), a
> conta "Culturas - Despesa" fora da classificação do BI (P4) e três defeitos novos do SQL da matriz (A25–A27).
>
> **DMG do próprio Metryx, Serra Dourada (§17):** a plataforma bate com o BI Metryx (4.825 → 5.114), mas o relatório
> de DMG do Metryx mostra 75 cabeças a menos (4.750 → 5.039). Os movimentos do trimestre batem um a um; a diferença
> está toda no saldo de bezerros (34 bezerras e 41 bezerros). **Causa, confirmada na API real (15/10):** depois do
> snapshot de 13/10, alguém lançou no Metryx 75 "mortes" com a causa "AJUSTE DE SALDO", datadas de 30/06/2026. O
> Metryx de hoje já dá exatamente o DMG; o BI vai dar o mesmo na próxima atualização dele. É o caso da Q10 (ajuste
> lançado como morte). A consulta também achou quatro defeitos no payload da API (A29–A32), já corrigidos no
> adapter. Recarregada pela API, a Serra Dourada bate 100% com o DMG, coluna por coluna. Achado menor: A28,
> corrigido na migração 0015 (o movimento que abre uma série nova no estoque deixa de virar "ajuste").

## 1. Como foi feito

- **Lado BI.** O SQL do Power Query de cada tabela foi extraído do dump dos PBIX e executado como está nos bancos
  `DATALAKE_PLAN` e `METRYX`, em modo somente leitura. As medidas DAX foram reproduzidas por cima do resultado:
  - `QTD C` e `Stock Accumulated Final`, só com datas que existem no `dCalendar`;
  - `Saldo Acumulado` (Σ `amountacc` no último dia do mês);
  - somas de cabeças, R$ e kg.
- **Lado plataforma.** Uma ponte lê as mesmas `stg_*` e produz o contrato canônico. Daí em diante passa pelo
  **motor real**, como `app_etl`: de-paras, qualidade, quarentena e função de estoque, gravando num banco descartável
  (`terra_validacao`). As sugestões de categoria do Metryx foram aceitas, simulando o consultor (D6).
- **Comparação.** Por fazenda × mês, com tolerância de R$ 0,01 ou 0,01 cab. Como "filtros sortidos", foram sorteadas
  fazendas e meses e conferidas todas as medidas lado a lado (§6).
- **Recorte do financeiro Metryx.** Para comparar com o BI, ele foi agregado por vencimento e fazenda fiscal, como o
  BI faz. A plataforma usa pagamento e fazenda destino (D2).
- **Consultas para conferir os achados direto no datalake:** `docs/validacao/2026-10-14_consultas_q2_q3.sql`.
- **Para reproduzir:**

  ```bash
  cd backend && .venv/Scripts/python -m validacao.cruzar
  ```

  O resultado bruto, com nomes de clientes, fica em `dados_exemplo/validacao/`, que o git ignora.

## 2. Resultado

### Planilhas (BI "Ciclo Completo"), 205 unidades

| Medida | Pares fazenda×mês | Iguais | % | Σ BI | Σ plataforma |
|---|---:|---:|---:|---:|---:|
| Estoque final (cab) | 3.013 | 2.734 | 90,7% | 13.979.154 | 14.297.942 |
| Compras (cab · R$) | 435 · 420 | 435 · 420 | 100% | 133.634 · R$ 447,4 mi | idem |
| Abate (cab · R$ · kg vivo · kg carcaça) | 853 · 838 · 849 · 845 | 853 · 834 · 849 · 845 | 99,5–100% | 228.858 · R$ 1,403 bi | idem (±R$ 0,02) |
| Em pé (cab · R$ · kg vivo) | 324 · 318 · 320 | todos | 100% | 54.679 · R$ 217,6 mi | idem |
| Nascimentos · mortes (cab) | 859 · 1.236 | todos | 100% | 166.842 · 12.044 | idem |
| Rebanho médio (cab) | 1.516 | 1.516 | 100% | 7.596.069 | 7.596.069 |
| Área total (ha) | 1.614 | 1.614 | 100% | 6.186.985 | 6.186.985 |
| Financeiro créditos (R$) | 995 | 976 | 98,1% | 1.790.804.544 | 1.790.804.544 |
| Financeiro débitos (R$) | 1.426 | 1.138 | 79,8% | 1.875.937.657 | 1.875.937.663 |

### Metryx (BI "Versão Metryx"), 10 clientes e 70 fazendas

| Medida | Pares fazenda×mês | Iguais | % | Σ BI | Σ plataforma |
|---|---:|---:|---:|---:|---:|
| Estoque final (cab) | 1.091 | 1.069 | 98,0% | 3.307.105 | 3.305.936 |
| Compras (cab · R$) | 331 | 331 | 100% | 129.932 · R$ 449,0 mi | idem |
| Abate (cab · R$ · kg vivo · kg carcaça) | 424 | 424 | 100% | 181.122 · R$ 1,154 bi | idem |
| Em pé (cab · R$ · kg vivo) | 126 | 126 | 100% | 14.415 · R$ 46,8 mi | idem |
| Nascimentos · mortes (cab) | 434 · 770 | todos | 100% | 51.335 · 7.151 | idem |
| Rebanho médio (cab) | 1.223 | 1.196 | 97,8% | 3.520.012 | 3.520.026 |
| Financeiro créditos (R$) | 638 | 635 | 99,5% | 1.710.082.774 | 1.710.097.774 |
| Financeiro débitos (R$) | 898 | 756 | 84,2% | 1.658.076.699 | 1.658.079.979 |

## 3. Todas as divergências, com a causa

| Fonte · medida | Pares ≠ | Causa | De quem é |
|---|---:|---|---|
| Planilha · estoque | 135 | 5 fazendas com Saldo Anterior em jun/2024 (fora do `dCalendar`): o BI não soma o saldo inicial (achado A1) | **defeito do BI** |
| Planilha · estoque | 68 | Venda em pé sem cliente: está na `fMovRebanho` (o BI desconta do estoque), mas o Pentaho descarta a linha detalhada (A3); 16 destes pares também têm saldo negativo | **defeito do BI / Pentaho** |
| Planilha · estoque | 34 | Desmame/mudança com um lado sem categoria BI: no BI o animal sai e não entra (A4); a ponte não consegue parear meia operação agregada | dado de origem + limitação da ponte |
| Planilha · estoque | 32 | Saldo Anterior negativo (−5, −4): a plataforma recusa estoque negativo e manda para a quarentena (A6) | dado de origem |
| Planilha · estoque | 10 | 1 compra com quantidade fracionária (0,26 cab) e 1 morte presente na aba detalhada mas ausente da `fMovRebanho` | dado de origem |
| Planilha · abate R$ | 4 | Arredondamento: 1 a 2 centavos | arredondamento |
| Planilha · financeiro | 307 | Só arredondamento (maior diferença: R$ 0,37 por fazenda×mês): o BI soma `float` com fração de centavo; a plataforma guarda centavos (decisão Q4) | arredondamento |
| Metryx · estoque | 22 | Empate de bezerros mamando: o SQL do BI escolhe um registro **qualquer** entre os do mesmo dia (A2). A plataforma usa o primeiro gravado (Q2), a regra que mais coincide com o BI; os 22 restantes caem entre o "menor" e o "maior" possível | **defeito do BI** |
| Metryx · rebanho médio | 27 | 53 registros com rebanho médio **negativo** (1 fazenda): a plataforma recusa (A13) | dado de origem |
| Metryx · financeiro | 141 | 139 por arredondamento (< R$ 1). Mais 4 lançamentos (R$ 18,3 mil) cuja fazenda fiscal não existe pelo nome no `stg_farm`: o BI os descarta (junção por nome), a plataforma os mantém na fazenda destino | defeito do BI |

Com a decisão Q1 implementada (conta fora do plano = "A classificar"), **o financeiro bate com o BI no total**:
planilha +R$ 5,72 em R$ 3,67 bi; Metryx +R$ 18,3 mil em R$ 3,37 bi, que são os 4 lançamentos acima. Antes da Q1 a
diferença era de R$ 354,6 mi, toda em quarentena.

Fluxos (compras, vendas, nascimentos, mortes), rebanho médio e área da planilha batem **100%**. Esses números passaram
pelo contrato, pelos de-paras e pelo loader sem perda.

## 4. Inconsistências encontradas (o que hoje o BI mostra errado ou esconde)

| # | Achado | Tamanho | Onde |
|---|---|---|---|
| A1 | **O estoque do BI de planilhas ignora o saldo inicial de quem começa antes de jul/2024**: o Saldo Anterior fica datado fora do calendário do PBIX | **11.362 cab** a menos, todos os meses: 35 · ÁGUA SANTA (1.101), 153 · LAÇADOR (2.080), 153 · SANTA MARIA (2.489), 27 · NELORE MOCHO CV (5.086), 84 · GALOPEIRA (606) | BI Ciclo |
| A2 | **O estoque Metryx de bezerros mamando é não determinístico**: há 164 casos com dois registros no mesmo dia e valores diferentes (o saldo e um zero), e o SQL `fSaldoGado` pega qualquer um (`row_number` sem desempate). O número do BI pode mudar sem nenhum dado mudar | 52 fins de mês no histórico (29 na janela; Σ 517 cab) | BI Metryx |
| A3 | **Estoque e vendas do BI de planilhas não fecham**: venda em pé sem cliente entra no estoque (via `fMovRebanho`), mas o Pentaho a descarta das vendas | 1.105 cab estão no estoque e faltam nas vendas; 192 no sentido contrário (categoria sem BI); líquido 913 (ex.: 141 · FAZENDA DE ENGORDA 523; 100 · IPIRANGA 288; 24 · AGRO BELA VISTA 143) | Pentaho |
| A4 | **Animais que somem no BI de planilhas**: desmame/mudança em que a categoria de destino (ou de origem) não está mapeada no CADASTROINICIAL. Sai de uma categoria e não entra em nenhuma | desmame −263 cab, mudança −194 cab (ex.: 18 · SAN RAFAEL 188; 129 · CHÃO PANTANEIRO 204; 66 · SANTA NICE 57) | planilha |
| A5 | **Movimentações invisíveis por categoria local não mapeada**: o BI não as conta no estoque e não avisa | **8.640 cab** em 48 combinações fazenda/operação/categoria/mês, em todo o histórico das abas (ex.: 254 · FAZENDA MARCA R, 1.854 de transferência de saída; 111 · ÁGUA AZUL, 1.775 de transferência de saída; 85 · BELA VISTA, 646 de compra) | planilha |
| A6 | Saldo Anterior **negativo** | 3 fazendas, −36 cab (227 · CANGALHA, 63 · SANTA LAVÍNIA, 71 · FORTALEZA E SANTA MARIA) | planilha |
| A7 | **Valores absurdos no financeiro Metryx**: o `financeiroDre` do BI não filtra (só o P×R filtra), então a página Financeiro soma esses valores | 79 lançamentos ≥ R$ 1 bi, somando ≈ R$ 2 × 10¹⁸ (erro de escala na origem) | Metryx / BI |
| A8 | **Centros de custo fora do plano unificado**: o BI soma em receitas/despesas, mas a classificação fica "VERIFICAR" (fora do P×R) | Metryx: Apicultura, Cerrado, Imobiliária, Milho, Silagens e Forrageiras, Transportadora Itapajé, Receitas Apicultura e as grafias **"Outro débitos/créditos" × "Outros Débitos"**, total R$ 364,9 mi em 25 contas; planilha: R$ 0,7 mi em 19 contas. Depois da Q1 entram como "A classificar" | Metryx / planilha |
| A9 | **`morte-pecuario` usa outro id de retiro**: inteiro legado ("224") no lugar do uuid usado pelos demais endpoints (o nome bate) | 7.358 mortes (100% delas) | API Metryx |
| A10 | **`weightTotal` da compra Metryx é peso por cabeça** na maioria dos registros, e o BI o trata como total (`valo_kg = valor ÷ (qtd × weightTotal)`, mas `peso_arroba = weightTotal ÷ 15`) | 1.865 de 2.297 compras com < 20 kg/cab se fosse total | API Metryx / BI |
| A11 | Preços implausíveis | ex.: venda em pé de 54 cab por **R$ 162** (FAZENDA CMI, jan/2026); R$/kg fora de 4–40: planilha 167 vendas em pé e 61 compras; Metryx 108 compras e 18 vendas em pé | origem |
| A12 | "Consumo" no Metryx: só a causa `Consumo Abate` é tratada como consumo; `Consumo Acidente` (148), `Consumo Doação` (13), `CONSUMO` (11), `Abate para consumo…` (5) ficam como morte | 177 registros | BI Metryx |
| A13 | Rebanho médio Metryx **negativo** | 53 registros, 1 fazenda | Metryx |
| A14 | Código do cliente gravado como texto **"24,0"** em `stg_unidades` (vírgula decimal) | todas as unidades | Pentaho |

## 5. O que mudou na plataforma por causa desta validação

- **Regra de saldo do Metryx** (`app/etl/adapters/metryx/saldo.py`): reprodução do `fSaldoGado`, validada contra o SQL
  do BI no histórico inteiro (1.946 de 1.998 fins de mês iguais; o resto é A2). O desempate dos bezerros passou a ser
  explícito (`desempate_mamando`). Há testes unitários para cada ramo.
- **Sugestão de categoria BI para o Metryx** (`categoria.py`): 260 das 261 categorias receberam sugestão.
- **Qualidade**:
  - lançamento ou venda com valor ≥ R$ 1 bi vai para a quarentena (`VALUE_OUT_OF_RANGE`, por causa de A7);
  - peso 0 conta como "não informado" e deixou de gerar 3.351 alertas falsos em mortes.
- **Para o adapter Metryx real** (registrado na ponte):
  - resolver o retiro das mortes (A9);
  - aplicar a regra do `weightTotal` da compra (A10);
  - tratar o estorno negativo como natureza invertida.
- **Para o adapter de planilhas real**:
  - toda categoria tem checkpoint no início do PERÍODO (0 quando a planilha não informa), porque o Pentaho descarta os
    zeros;
  - normalizar o código "24,0" para 24.

- **Conta fora do plano = "A classificar"** (Q1, migração `0011`):
  - o lançamento aponta para o de-para de contas;
  - a classificação é resolvida nas views `fato.v_lancamento_financeiro` / `v_orcamento_financeiro`, com
    `security_invoker`, para valer o RLS de quem consulta;
  - um teste garante que toda view de negócio tem `security_invoker`;
  - o aviso `ACCOUNT_UNCLASSIFIED` informa, por conta, quantas linhas e quanto R$ estão pendentes;
  - a quarentena ficou só para linha que não dá para somar (sem data/valor, sem natureza C/D, valor absurdo).

## 6. Amostra sorteada (filtros sortidos)

Fazendas e meses sorteados (semente fixa) com todas as medidas lado a lado. Nenhuma diferença na amostra.

### Planilhas

| Fazenda | Mês | Medida | BI | Plataforma | Dif |
|---|---|---|---:|---:|---:|
| 46 · CARIOCA | 2026-09 | Estoque final (cab) | 80 | 80 |  |
| 117 · MIMOSO | 2025-12 | Estoque final (cab) | 2.190 | 2.190 |  |
| 133 · SANTA ROSA | 2025-06 | Estoque final (cab) | 16.958 | 16.958 |  |
| 133 · SANTA ROSA | 2026-01 | Estoque final (cab) | 22.489 | 22.489 |  |
| 133 · SANTA ROSA | 2026-01 | Abate (cab) | 72 | 72 |  |
| 133 · SANTA ROSA | 2026-01 | Abate (R$) | 357.079 | 357.079 |  |
| 133 · SANTA ROSA | 2026-01 | Abate (kg vivo) | 38.125 | 38.125 |  |
| 133 · SANTA ROSA | 2026-01 | Abate (kg carcaça) | 19.062 | 19.062 |  |
| 133 · SANTA ROSA | 2026-01 | Nascimentos (cab) | 40 | 40 |  |
| 133 · SANTA ROSA | 2026-01 | Mortes (cab) | 29 | 29 |  |
| 133 · SANTA ROSA | 2026-01 | Rebanho médio (cab) | 22.590 | 22.590 |  |
| 133 · SANTA ROSA | 2026-01 | Área total (ha) | 10.427 | 10.427 |  |
| 133 · SANTA ROSA | 2026-01 | Financeiro créditos (R$) | 357.079 | 357.079 |  |
| 133 · SANTA ROSA | 2026-01 | Financeiro débitos (R$) | 1.174.432 | 1.174.432 |  |
| 47 · ALEGRETE | 2025-11 | Estoque final (cab) | 1.380 | 1.380 |  |
| 47 · ALEGRETE | 2025-11 | Em pé (cab) | 230 | 230 |  |
| 47 · ALEGRETE | 2025-11 | Em pé (R$) | 632.500 | 632.500 |  |
| 47 · ALEGRETE | 2025-11 | Em pé (kg vivo) | 43.240 | 43.240 |  |
| 47 · ALEGRETE | 2025-11 | Nascimentos (cab) | 1 | 1 |  |
| 47 · ALEGRETE | 2025-11 | Mortes (cab) | 6 | 6 |  |
| 47 · ALEGRETE | 2025-11 | Rebanho médio (cab) | 2.689 | 2.689 |  |
| 47 · ALEGRETE | 2025-11 | Área total (ha) | 3.478 | 3.478 |  |
| 47 · ALEGRETE | 2025-11 | Financeiro créditos (R$) | 632.500 | 632.500 |  |
| 47 · ALEGRETE | 2025-11 | Financeiro débitos (R$) | 307.159 | 307.159 |  |

### Metryx

| Fazenda | Mês | Medida | BI | Plataforma | Dif |
|---|---|---|---:|---:|---:|
| Mimoso (Metryx 7fb9) | 2025-09 | Rebanho médio (cab) | 159 | 159 |  |
| Mimoso (Metryx 7fb9) | 2026-07 | Rebanho médio (cab) | 159 | 159 |  |
| Fazenda Leonardo (Metryx d92a) | 2025-09 | Estoque final (cab) | 300 | 300 |  |
| Fazenda Leonardo (Metryx d92a) | 2025-09 | Rebanho médio (cab) | 300 | 300 |  |
| Fazenda Leonardo (Metryx d92a) | 2025-11 | Estoque final (cab) | 300 | 300 |  |
| Fazenda Leonardo (Metryx d92a) | 2025-11 | Rebanho médio (cab) | 300 | 300 |  |
| FAZENDA CMI (Metryx a1eb) | 2025-01 | Estoque final (cab) | 1.871 | 1.871 |  |
| FAZENDA CMI (Metryx a1eb) | 2025-01 | Mortes (cab) | 11 | 11 |  |
| FAZENDA CMI (Metryx a1eb) | 2025-01 | Rebanho médio (cab) | 1.876 | 1.876 |  |
| FAZENDA CMI (Metryx a1eb) | 2025-01 | Financeiro débitos (R$) | 16.538 | 16.538 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Estoque final (cab) | 3.240 | 3.240 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Compras (cab) | 652 | 652 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Compras (R$) | 2.190.536 | 2.190.536 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Em pé (cab) | 54 | 54 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Em pé (R$) | 162 | 162 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Em pé (kg vivo) | 16.200 | 16.200 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Mortes (cab) | 3 | 3 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Rebanho médio (cab) | 3.013 | 3.013 |  |
| FAZENDA CMI (Metryx a1eb) | 2026-01 | Financeiro débitos (R$) | 4.465.569 | 4.465.569 |  |
| Fazenda Cruz de Malta (Metryx d92a) | 2024-12 | Rebanho médio (cab) | 50 | 50 |  |
| Fazenda Cruz de Malta (Metryx d92a) | 2026-08 | Rebanho médio (cab) | 50 | 50 |  |

## 7. Decisões para você

| # | Decisão | Opções | Recomendação |
|---|---|---|---|
| Q1 | Conta (centro de custo) fora do plano unificado | **Decidido: "A classificar"** (14/10). Implementado na migração `0011`: o lançamento aponta para `dim.plano_contas_map`, a conta desconhecida nasce pendente e `fato.v_lancamento_financeiro` mostra "A classificar"; classificar depois reclassifica o histórico sem recarga | — |
| Q2 | Desempate dos bezerros mamando (A2) | **Decidido: manter a regra do BI** (14/10). Como o SQL do BI não tem desempate, a plataforma usa a regra que mais coincide com ele: o **primeiro registro gravado** (ordem do JSON da API). Resultado: 98,0% dos fins de mês idênticos ao BI ("maior" 97,4%, "menor" 97,7%, "último" 97,1%); os 40 restantes são empates que nem o BI reproduz entre duas atualizações | — |
| Q3 | Defeitos do BI que a plataforma **não** reproduz (A1, A3, A4, A5) | **Decidido** (14/10). A1: o estoque **conta** o saldo inicial anterior a jul/2024 (essas 5 fazendas ficam acima do BI, com nota na homologação). A3: venda em pé sem cliente **entra no estoque e nas vendas**, com aviso; requisito do adapter de planilhas, que não pode descartar a linha como o Pentaho. A4/A5: já é a regra do BI (categoria sem mapeamento fica fora do estoque), mais o aviso `CATEGORY_UNMAPPED` e a correção automática do histórico ao mapear. Origem e consultas em `2026-10-14_consultas_q2_q3.sql` | — |
| Q4 | Precisão do R$ no canônico | **Decidido: centavos (2 casas)** (14/10). Na paridade com o BI, diferença de até R$ 1 por fazenda×mês é arredondamento | — |
| Q5 | Centros novos do Metryx (A8) | **Decidido** (14/10): os centros mapeados já existem no plano. Centro novo criado no Metryx entra como "A classificar" (aviso `ACCOUNT_UNCLASSIFIED`) e a equipe classifica quando precisar. Nada de mapeamento automático por grafia parecida | — |
| Q6 | Carga inicial do histórico das planilhas que já viraram de safra (A15) | **Decidido** (14/10): histórico até 06/2026 a partir do snapshot do datalake, com a mesma identidade do adapter (código do projeto + fazenda); daí em diante, o adapter real. Implementado: `python -m app.etl planilhas-historico` (§10) | — |
| Q7 | Linha com total vazio (A17) | (a) calcular quantidade × valor por cabeça; (b) somar 0, como o BI | **(a)**, já implementado (mesma linha da Q3: não reproduzir defeito do BI). São 3 linhas nas fazendas comparáveis |
| Q8 | Meta com data digitada "DDMM/AAAA", ex.: `0108/2025` (A20, §13) | **Decidido (15/10): (a)**. A linha fica na quarentena e aparece na aba **Pendências** do painel (arquivo, aba, linha e o que está escrito), para o consultor corrigir na planilha; a carga seguinte a traz para os números. Opção descartada: (b) ler como o SQL das metas do BI | **(a)**: a plataforma não adivinha data (mesma regra da A18, em que o BI descarta). São 5 linhas de meta em 3 fazendas: AGRO PM (128 cab em 07/2025) e as duas planilhas do projeto 87, PALMEIRAS e PALMEIRAS PECUÁRIA, com as mesmas metas (61 cab em 08/2025 e 18,9 cab de abate em 06/2026). Com (a), o planejado delas fica menor que no BI até a correção |
| Q9 | O mesmo cliente nas duas fontes, com grafias diferentes: no menu "Cliente" aparecem "Gustavo Mota França" (customer do Metryx) e "GUSTAVO MOTA FRANÇA" (proprietário da planilha). São 6 casos: Armando Gottardi Filho, Gustavo Mota França, Gustavo Nakai de Magalhães e Ribeiro, Maria Cecília Ribeiro Junqueira de Andrade e Outros, Pedro de Sousa Junqueira Netto e Outros, Rene Eugênio Migliavacca | **Decidido (15/10/2026): manter separado.** As planilhas saem no futuro e, por ora, ficam ao lado do Metryx para validar os números; o MENU tem o filtro **Origem** (Integração Planilhas | Metryx) e o cliente aparece uma vez em cada origem. Sem de-para de clientes por enquanto | — |
| Q10 | Ajuste de estoque lançado como morte (§14): causas como "AJUSTE DE AUDITORIA 25/26", "AJUSTE DE SALDO", "AJUSTE SISTEMA" e "AJUSTE ESTOQUE" em mais de 20 fazendas, nas duas fontes. Os maiores: MAISTER AGROPECUÁRIA LTDA (planilha, CONDOMINIO), 738 cab em 06/2026; Agropecuária Maister LTDA (Metryx), 666 das 1.389 mortes da safra 25/26. Os dois BIs contam tudo como morte, e a mortalidade sobe junto | (a) manter como o BI: toda morte lançada é morte; (b) de-para de causa de morte (dimensão preenchida pela equipe, como `dim.categoria_map`) com a marca "ajuste de inventário": a linha continua saindo do estoque, mas sai das mortes e da mortalidade e aparece como ajuste | **(b)**: a classificação vem de uma dimensão (nunca do texto da causa) e reclassifica o histórico sem recarga. Até a decisão, a plataforma faz (a), igual ao BI |
| Q11 | Que contas entram no desembolso e no custeio (§15; completa a D3 da proposta). A plataforma classifica pela `dim.centro_custo` (doc 01 §5.5: um único de-para, editável), que hoje segue o `mapa` do BI Metryx; a planilha classifica cada conta de outro jeito. Nas planilhas, isso põe o desembolso 63,6% acima do BI (R$ 1,82 bi × R$ 1,11 bi) e o custeio 1,8% acima. Quase tudo vem de dois centros: **Rebanho Investimento** (compra de gado; a planilha marca "REP.", reposição, fora do desembolso; +R$ 474 mi) e **Financiamentos débitos** (a planilha deixa fora; +R$ 216 mi). Menores: Culturas - Despesa (+R$ 17 mi no desembolso e no custeio) | (a) manter a dimensão como está (o `mapa` do BI Metryx); (b) seguir a planilha: Rebanho Investimento vira reposição (`eh_reposicao`: fica no gráfico "Relação desembolso total", fora do cartão de desembolso e do por cabeça) e Financiamentos débitos sai do desembolso; (c) classificar por subconta (`dim.subcentro`), como a planilha faz | **(b)**: é a regra da consultoria nas planilhas (o Ciclo Completo é a referência dos técnicos) e separa reposição de gado, que a página Compras já analisa à parte. Muda o número das fazendas Metryx em relação ao BI Metryx, o que também precisa do seu aceite. Até a decisão, a plataforma faz (a) |
| Q13 | Lotação quando um mês com rebanho não tem área (§18) | **Decidido (16/10): manter igual ao BI** (Σ cabeças ÷ Σ área dos meses escolhidos). As cabeças do mês sem área entram e a lotação sobe. Na safra 25/26, 10 de 150 fazendas com área têm esse caso (ex.: PRINCESA 6,18 no BI × 2,28 só com os meses que têm área), mais 8 GRUPOs; na 26/27, 4 GRUPOs. A lista, o exemplo e como evitar (preencher a área em todos os meses) estão na anotação [2026-10-16_lotacao_meses_sem_area.md](2026-10-16_lotacao_meses_sem_area.md); `python -m validacao.lotacao_sem_area` refaz a lista | A recomendação era contar as cabeças só dos meses que têm área; o usuário preferiu ficar igual ao BI e ser avisado. A anotação aponta também a fazenda PARCERIA, com 0,1 ha de pasto na planilha |
| Q12 | **Respondida (15/10) pela consulta à API real (§17):** são 75 "mortes" com a causa "AJUSTE DE SALDO", lançadas no Metryx depois de 13/10 com data de 30/06/2026; o Metryx de hoje já bate com o DMG. Recarregada pela API (adapter corrigido para A29–A32), a plataforma bate 100% com o DMG; o BI se corrige na próxima atualização dele (o tratamento dessas mortes é a Q10). Pergunta original: DMG do Metryx com 75 bezerros a menos que o balanço pecuário do próprio Metryx (§17): Serra Dourada, 34 bezerras e 41 bezerros dos lotes nascidos em 12/25 (retiro ITIRATUPÃ) e 02/23. A plataforma e o BI Metryx seguem o balanço pecuário | (a) a equipe confere no Metryx os bezerros desses lotes (pelo balanço, 74 bezerras e 47 bezerros do lote 12/25 ainda sem desmame em 30/09, mais 4 bezerras nascidas em 02/23) e, se não existem, lança a baixa no Metryx; a carga seguinte corrige a plataforma e o BI; (b) com a sua autorização, um GET na API real (`balanco-pecuario` e `saldo-inical-pecuario`, da allow-list) da Serra Dourada, para ver se o dado de hoje já difere do snapshot de 13/10 e se o saldo inicial da API dá o número do DMG; (c) se o Metryx confirmar que o DMG está certo e o balanço está atrasado, levar ao suporte do Metryx (o balanço é a fonte do estoque nos dois BIs) | **(a) e depois (b)**: (a) não depende de código e resolve a fazenda; (b) diz se o problema é de uma fazenda ou do endpoint, e se a plataforma deveria ler o saldo de outro endpoint. Até lá, a plataforma segue o BI Metryx, a referência combinada |

## 8. O que esta validação ainda não cobre

- **Planejado (metas)** e **Previsto × Realizado**: a camada de KPIs ainda não existe.
- **Medidas derivadas** (preço médio da @, lotação, UA, R$/cab/mês): também dependem da camada de KPIs. Como as bases
  batem, a próxima etapa é comparar as fórmulas.
- **Transferências do Metryx**: o Pentaho não extrai, então não há com o que comparar.
- **Metryx pela API de verdade**: as duas rodadas usaram a ponte (`stg_*` → JSON no formato da API → normalizador de
  produção). Falta a primeira chamada real (precisa de autorização e token de teste).
- **Safra 25/26 das 55 planilhas que viraram**: só existe no snapshot (Q6); não há arquivo atual para comparar.

## 9. Segunda rodada: adapter real nos 230 `.xlsm` (14/10, noite)

### Como foi feito

- As 230 planilhas de `G:\Meu Drive\Relatórios` foram copiadas, só leitura e com a data de modificação preservada,
  para `dados_exemplo/planilhas/` (fora do git). Ler direto do Drive custa ~30 s por arquivo.
- **Adapter de planilhas real** (`AdapterPlanilha`) e **motor real**, gravando no banco descartável. O Metryx passou
  de novo pela ponte e pelo normalizador de produção, com o mesmo resultado da §2.
- **Janela 07/2024–07/2026.** O datalake do BI de planilhas é um snapshot do começo de ago/2026, com dados até 07/2026.
- Para reproduzir:

  ```bash
  cd backend
  .venv/Scripts/python -m validacao.cruzar --ate 2026-07
  .venv/Scripts/python -m validacao.classificar --snapshot 2026-08-01 --ate 2026-07
  ```

### O que mudou na pasta desde o snapshot (não é diferença de cálculo)

- **55 planilhas viraram para a safra 26/27 começando do zero**: só trazem lançamentos de 07/2026 em diante. Foram
  salvas entre ago e out/2026 (11 em agosto, 34 em setembro, 10 em outubro). A safra 25/26 delas não está mais em
  arquivo nenhum da pasta (achado A15, decisão Q6).
- **96 fazendas têm o arquivo salvo depois de 01/08**: as 55 acima, mais correções e meses novos.
- **14 fazendas novas.** Exemplos: 111 · REBANHO PO, RECRIA e TERMINAÇÃO; 395 · SANTA VERA e SERRANA; 84 · BELA VISTA.
- **3 fazendas do BI sem correspondente na pasta de hoje**:
  - 120 · ÁGUA FRIA: arquivo removido;
  - 71 · FORTALEZA E SANTA MARIA: virou FORTALEZA;
  - 15 · GUARÁ 1: a planilha 26/27 foi montada a partir da de outra fazenda (A19); agora ela não carrega e mostra o
    motivo.
- **Várias cópias "(1)" substituíram o arquivo original.**
- **4 pares de arquivo em dobro da mesma fazenda**: 126 · MARANGUAPE/MARANGUAPE1, 144 · ATTO SEMENTES, 22 · BHR,
  94 · MATER. Vale o mais recente.

Por isso o placar geral da planilha (estoque 55%, fluxos ~47%) mede a pasta de hoje contra o snapshot, não o adapter.
O número que mede o adapter é o das fazendas cujo arquivo não mudou.

### Resultado nas 110 fazendas com arquivo inalterado desde o snapshot

| Medida | Pares fazenda×mês | Iguais | % | Σ BI | Σ plataforma |
|---|---:|---:|---:|---:|---:|
| Estoque final (cab) | 1.444 | 1.314 | 91,0% | 5.579.369 | 5.737.036 |
| Compras (cab · R$) | 142 · 138 | todos | 100% | 38.860 · R$ 122,7 mi | idem |
| Abate (cab · R$ · kg vivo · kg carcaça) | 323 · 319 · 322 · 319 | todos | 100% | 69.455 · R$ 414,2 mi | idem (±R$ 0,01) |
| Em pé (cab · R$ · kg vivo) | 147 · 140 · 144 | 143 · 136 · 138 | 95,8–97,3% | 27.131 · R$ 102,9 mi | 27.569 · R$ 104,3 mi |
| Nascimentos · mortes (cab) | 395 · 551 | todos | 100% | 72.152 · 6.047 | idem |
| Rebanho médio (cab) | 658 | 658 | 100% | 2.743.138 | 2.743.138 |
| Área total (ha) | 660 | 660 | 100% | 3.160.322 | 3.160.322 |
| Financeiro créditos (R$) | 416 | 416 | 100% | 575.797.219 | 575.797.219 |
| Financeiro débitos (R$) | 640 | 545 | 85,2% | 654.148.138,00 | 654.148.139,54 |

Diferenças que sobram nessas fazendas, todas com causa:

| Medida | Pares ≠ | Causa |
|---|---:|---|
| Estoque | 98 | As mesmas da §3: A1 (saldo de jun/2024), saldo negativo, compra fracionária |
| Estoque | 24 | 35 · ÁGUA SANTA. Os 1.101 cab do A1 (decisão Q3), mais 3 + 3 touros de uma mudança para "Touros Reprodução", categoria fora do CADASTROINICIAL: saem e não entram, como no BI (A4). A ponte não conseguia reproduzir isso; o adapter consegue |
| Estoque | 8 | 304 · BELLA ALIANÇA SEDE: saldo inicial com **meia cabeça** (389,5 e 435,5 no CADASTROINICIAL); o BI mostra o número inteiro (A16) |
| Em pé | 11 | Venda sem cliente agora aparece nas vendas (decisão Q3/A3): 100 · IPIRANGA (123 + 165 cab, os 288 do A3), 108 · ÁGUAS CLARAS (84), 67 · PADRE PIO (66) |
| Em pé | 3 | Linha com total vazio (A17): 149 · HORIZONTE (faturamento vazio, 1 × R$ 1.675), 96 · Cáceres (peso total vazio, 7 × 621 kg), 54 · MORRO AZUL (1 × 452 kg). O BI soma 0; a plataforma calcula (Q7) |
| Débitos | 95 | Arredondamento (Q4): Σ difere R$ 1,54 em R$ 654 mi |

**36 diferenças de estoque da ponte sumiram.** São as do A3: a ponte não tinha a linha detalhada da venda sem cliente,
e o adapter tem.

### Problemas que a rodada real achou, todos corrigidos e com teste

| # | Problema | Efeito | Correção |
|---|---|---|---|
| 1 | **A virada de safra apagaria o histórico**: `mov_animal`, `lancamento` e o planejado substituíam a fazenda inteira | a primeira carga da planilha 26/27 (começada do zero) apagaria toda a safra 25/26 da fazenda | `Particao.desde`: o arquivo só substitui do início do PERÍODO em diante, recuado até a linha mais antiga que ele traz (sem duplicar quando a planilha é cumulativa). Regra registrada no `CLAUDE.md` |
| 2 | Linha do modelo sem nenhum número ia para a quarentena | 9.004 linhas falsas em 49 arquivos (8.461 só em `fmudcategoria`) | ignorada; quarentena só para linha com número que não dá para somar (ex.: quantidade sem data) |
| 3 | Célula formatada como hora (`datetime.time`) não cabia no JSON do bruto | derrubava **o job inteiro** | valor convertido; falha ao gravar o bruto agora derruba só aquela unidade |
| 4 | `OPERAÇÃO = VERIFICAR` era "resgatada" pelo `ConsultaPlanoContas` | R$ 1,21 mi de "Aporte de capital" (89 · SAN FRANCISCO) e outros somavam onde o BI não soma | VERIFICAR vai para a quarentena, como no BI; o plano de contas só é consultado quando a coluna está vazia |
| 5 | Kg do abate: o adapter priorizava quantidade × peso por cabeça | 19 · TICO TICO e outros divergiam do BI | a coluna de total da planilha primeiro (é o que o BI soma); quantidade × valor por cabeça só se ela estiver vazia |
| 6 | Data digitada errada virava outra data (`05/11/225` lida como 05/11/2022) | 100 · IPIRANGA com nascimentos a mais | a data tem de ser o texto inteiro; senão a linha vai para a quarentena (o BI a descarta sem avisar) |
| 7 | Arquivo em dobro: o resultado dependia da ordem alfabética, e o ignorado ficava com versão "erro" | o arquivo velho carregava primeiro e só era ignorado na carga seguinte | o adapter entrega o mais recente primeiro; a unidade fica `ignorada` e a versão `extraida` |
| 8 | Planilha montada a partir da de outra fazenda: `fUnidade` sem código e com o nome de outra fazenda | 15 · GUARÁ 1 criava a fazenda fantasma "15 · AGRO ZAFANELLI E SILVEIRA (AZS)" com os dados da GUARÁ | sem código **e** com nome sem nenhuma palavra em comum com o nome do arquivo: a unidade não carrega (`ErroIdentidade`, "corrija o fUnidade"); só o nome diferente gera o aviso `FARM_LABEL_MISMATCH` (1 caso legítimo: 283 · WV AGRONEGÓCIOS, empresa × fazenda ARIZONA E MODAZA) |

Depois das correções, reprocessar as 227 versões a partir do bruto guardado (`raw.payload`) levou 54 s, sem reler os
arquivos. A quarentena final da planilha tem 825 linhas:

- 752 `NATURE_UNKNOWN`: VERIFICAR, que o BI também não soma;
- 58 `REQUIRED_MISSING`: quantidade sem data, data digitada errada, linha de total;
- 15 outras.

### Achados novos

| # | Achado | Tamanho | Onde |
|---|---|---|---|
| A15 | **Na virada de safra a planilha recomeça do zero.** Como o BI recarrega tudo a partir dos arquivos, na próxima atualização do datalake **o próprio BI perde a safra 25/26 dessas fazendas**. Hoje ela só existe no snapshot | 55 de 230 planilhas | planilha / Pentaho |
| A16 | Saldo inicial com fração de cabeça no CADASTROINICIAL | 304 · BELLA ALIANÇA SEDE (+1 cab) | planilha |
| A17 | Linha com total vazio (faturamento ou peso total) e valor por cabeça preenchido: o BI soma 0 | 3 linhas nas fazendas comparáveis | planilha / BI |
| A18 | Data digitada errada (`05/11/225`, `24/11/250`): o BI descarta a linha sem avisar | 3 linhas em 100 · IPIRANGA (13 cab) | planilha |
| A19 | Planilha da safra nova montada a partir da de outra fazenda, sem atualizar o `fUnidade`. O BI juntaria os dados à fazenda errada | 15 · GUARÁ 1 (fUnidade da 16 · AGRO ZAFANELLI E SILVEIRA) | planilha |

## 10. Carga do histórico (Q6) e terceira conferência (14/10, noite)

### Como funciona

- **Comando** (carga única, roda depois de `planilhas`):

  ```bash
  python -m app.etl planilhas-historico --ate 2026-06
  ```

  O adapter fica em `backend/app/etl/adapters/planilha/historico.py`. Ele lê as `stg_*` do datalake do BI (só
  leitura, `DATALAKE_PLAN_URL`), incluindo o planejado (`stg_fmetas*`).
- **Mesma identidade do adapter de planilhas**: fonte `planilha` e fazenda = código do projeto + fazenda.
- **Fronteira, por fazenda e entidade.** O histórico só entra antes do que os arquivos já carregados cobrem, pela
  mesma regra do `desde`: o menor entre o início do PERÍODO e o mês mais antigo das linhas do arquivo. A partição do
  histórico usa o recorte novo `Particao.ate` (o espelho do `desde`), então não toca no que é do arquivo.
- **Estoque.** O snapshot só tem o saldo por categoria BI, então o histórico usa categorias próprias (`BI:<categoria>`).
  No dia do saldo inicial do arquivo, essas categorias fecham em 0, e dali em diante vale o saldo da planilha. A
  diferença entre o estoque calculado e o saldo informado aparece como ajuste de inventário no mês da passagem.
- **No fim, as planilhas são reprocessadas por cima** a partir do bruto guardado, e o arquivo tem a palavra final
  (inclusive no nome da fazenda).
- **Fazenda sem planilha** (arquivo removido, renomeado ou recusado) recebe o histórico inteiro, com o aviso
  `HISTORY_WITHOUT_FILE`. Se a planilha dela aparecer depois, basta rodar o comando de novo.
- **Testes** (`tests/test_historico.py`):
  - a passagem do estoque para a planilha;
  - nada duplica onde o arquivo já cobre;
  - o planejado entra;
  - a ordem não importa: rodar o histórico antes da planilha e de novo depois dá o mesmo resultado;
  - o histórico não conta como arquivo em dobro.

### Resultado no banco de validação

- **214 fazendas do snapshot em 36 s, sem erro.** 3 ficaram sem planilha: 120 · ÁGUA FRIA, 71 · FORTALEZA E SANTA
  MARIA (virou FORTALEZA) e 15 · GUARÁ 1 (recusada pela regra de identidade, A19).
- **Invariantes conferidos direto no banco**:
  - 0 sobreposições entre histórico e planilha em fluxos, financeiro, orçamento, rebanho médio e área (58 fazendas têm
    os dois nos fluxos realizados);
  - 0 categorias do histórico com saldo depois do saldo inicial do arquivo, ou seja, nada conta em dobro no estoque.

Placar geral da planilha contra o BI, todas as fazendas, até 06/2026:

| Medida | Pares | Iguais | % | Σ BI | Σ plataforma |
|---|---:|---:|---:|---:|---:|
| Estoque final (cab) | 2.477 | 2.033 | 82,1% | 11.208.697 | 11.172.789 |
| Compras (cab) | 468 | 414 | 88,5% | 132.760 | 144.419 |
| Abate (cab) | 886 | 817 | 92,2% | 224.038 | 235.260 |
| Em pé (cab) | 334 | 311 | 93,1% | 54.679 | 53.663 |
| Nascimentos · mortes (cab) | 881 · 1.276 | 821 · 1.188 | 93,2% · 93,1% | 166.670 · 12.019 | 166.436 · 11.881 |
| Rebanho médio (cab) | 1.583 | 1.495 | 94,4% | 7.549.716 | 7.882.905 |
| Área total (ha) | 1.565 | 1.503 | 96,0% | 6.061.091 | 6.039.697 |
| Financeiro créditos · débitos (R$) | 1.037 · 1.485 | 947 · 1.105 | 91,3% · 74,4% | 1,740 bi · 1,845 bi | 1,837 bi · 1,868 bi |

Sem o histórico, os mesmos números ficavam em ~47–55%. As diferenças caíram de 8.592 para 1.701 e se dividem assim:

- **0 "só no BI"**: as fazendas sem planilha agora têm histórico.
- **323 "só na plataforma"**: fazendas novas, que o BI não tem.
- **1.133 em 87 fazendas cuja planilha mudou depois do snapshot**: lançamentos atrasados e correções. É daí que vem a
  maior parte dos totais acima do BI.
- **201 já explicadas na §3** (A1 etc.).
- **44 já explicadas na §9** (A3, A16, A17).

Nas 63 fazendas que não tinham mais a safra 25/26 no arquivo, as diferenças de 07/2025 a 05/2026 caíram cerca de 90%.
Exemplos: abate 383 → 36, área 679 → 25, estoque 693 → 111, créditos 403 → 33. Conferi a origem de cada diferença que
sobrou:

- **133 vêm do histórico** e são arredondamento de centavos (Q4).
- **174 vêm da planilha**: dado que o consultor lançou depois do snapshot. Ex.: compras de 02/2026 nas fazendas
  85 · ITAPAJÉ.
- **229 são meses que o arquivo atual cobre, mas onde ele não tem mais o lançamento que o BI mostra.** Ex.: 283 · WV
  AGRONEGÓCIOS; as fazendas 85 · ITAPAJÉ, no CIVIL 2026, sem área. A plataforma segue o arquivo de hoje.

As 107 fazendas com arquivo inalterado continuam com fluxos, rebanho médio, área e créditos 100% iguais: o histórico
não mexeu nelas.

## 11. Planilha enviada em dobro (15/10)

**Problema no BI:** a mesma planilha chega duas vezes com nomes diferentes e o Pentaho soma as duas. No snapshot de
agosto não havia nenhum caso, mas a pasta de hoje tem 4 pares da mesma fazenda:

- 126 · MARANGUAPE / MARANGUAPE1;
- 144 · ATTO SEMENTES / ATTO SEMENTES.;
- 22 · BHR / BHR - OK;
- 94 · MATER / MATER (1).

Na próxima atualização, o BI mostraria essas 4 fazendas em dobro.

**Na plataforma, duas regras, das duas o mais recente (data de modificação do arquivo) vale:**

| Regra | Pega | Aviso |
|---|---|---|
| Mesma fazenda (código do projeto + FAZENDA do fUnidade) | cópia exata e também versão antiga salva com outro nome | `DUPLICATE_UNIT_FILE`. Diz se o conteúdo é idêntico ou diferente e quantas linhas cada um tem. Avisa com **ATENÇÃO** quando o ignorado tem mais linhas que o mantido |
| Mesmos bytes (sha256) | cópia exata, mesmo quando ela viraria outra fazenda (ex.: fUnidade sem código e código errado no nome da cópia) | `DUPLICATE_CONTENT`. Se a cópia antiga já tinha sido carregada, saem só as linhas que ela gravou |

- O adapter entrega os arquivos do mais recente para o mais antigo, então a cópia já sai ignorada na primeira carga.
- O arquivo ignorado é relido a cada carga: se o mantido sumir, ele volta a valer.
- **Resultado nos 4 pares reais:** são versões diferentes, não cópias. O mantido é sempre o mais completo (ex.: MATER (1)
  com 3.127 linhas contra 1.822). Nenhum arquivo é idêntico byte a byte.

**Riscos:**

1. **A data de modificação decide.** Se alguém abrir e salvar a cópia antiga, ela passa a ser "a mais recente" e
   substitui a versão boa. Mitigação: o aviso compara as duas versões e marca ATENÇÃO quando a ignorada tem mais
   linhas. A equipe confere e apaga o arquivo errado, e na carga seguinte a versão certa volta sozinha.
2. **Fazenda legitimamente dividida em dois arquivos** (ex.: um por retiro, com a mesma FAZENDA no fUnidade): a regra
   da mesma fazenda manteria só um. Hoje não acontece em nenhum dos 230 arquivos. Se passar a acontecer, a identidade
   tem de incluir o retiro, e as partições também.
3. **A regra dos mesmos bytes não tem risco de perder dado**: as duas cópias são idênticas. Ela é estreita, porém:
   abrir e salvar no Excel muda os bytes, e aí só a regra da mesma fazenda pega.
4. **Comparação com o BI:** onde o BI soma em dobro, a plataforma vai mostrar menos que ele, e isso é o certo.

## 12. KPIs da página Movimentação do Gado (15/10)

**Pergunta:** os cartões que a plataforma mostra na página Movimentação do Gado (a mesma página do BI, refeita a partir
dele em 15/10) batem com as medidas do BI de planilhas, em filtros como o consultor usa?

**Como foi feito** (`python -m validacao.cruzar_kpis --sorteios 300 --semente 7`):
- 300 filtros sorteados: 1 a 3 fazendas do mesmo cliente e um período de 1 a 12 meses entre 07/2024 e 06/2026;
- só as 110 fazendas cujo arquivo não mudou desde o snapshot do BI (as outras diferem por dado novo, §9);
- lado plataforma: a mesma função que atende `GET /dashboards/movimentacao` (`app/kpis/movimentacao.py`);
- lado BI: as medidas dos cartões da página ("Stock Accumulated Final", "Mean Month", "UA Median Month",
  "Mean Month Ha", "UA Median Ha", "Birth Quantity", "Dead Quantity", compras e "Amount Saled") reproduzidas sobre o
  SQL do PBIX, e as metas pelas tabelas `fMetasNascimentos`, `fMetasMortes`, `fMetasCompras`, `fMetasAbate` e
  `fMetasEmPe`.

**Resultado:**

| Medida | Batem |
|---|---|
| Rebanho médio (cab e UA) e lotação (cab/ha e UA/ha) | 300/300 (100%) cada |
| Nascimentos, mortes e compras: realizado e planejado | 300/300 (100%) cada |
| Vendas (abate + em pé), realizado | 290/300 (96,7%): só A3 (venda em pé sem cliente: PADRE PIO, IPIRANGA, ÁGUAS CLARAS) |
| Vendas, planejado | 299/300 (99,7%): só A20 (meta "0108/2025" da PALMEIRAS PECUÁRIA, §13) |
| Estoque final | 281/300 (93,7%) |

**As diferenças de estoque são todas as já conhecidas do estoque mensal**, nenhuma nova vinda do cálculo dos KPIs:
- A1 (saldo do BI negativo por movimentação antes do saldo inicial): ÁGUA SANTA, grupo GALOPEIRA/PRINCESA/AREA
  DIVINA e LAÇADOR. O BI mostra estoque negativo (ex.: −554 cab); a plataforma conta o saldo inicial;
- A16 (BELLA ALIANÇA, +1 cab);
- SANTA NICE (+57) e FAZENDA MARCA R (+2): a mesma diferença mensal já aparecia nas duas rodadas anteriores (ponte e
  adapter real), em meses que o arquivo cobre.

**Diferença de regra, a favor da plataforma:** o "Mean Month" do BI conta os meses pelo número do mês, sem o ano
(P2). Com períodos de até 12 meses, como nos sorteios, dá o mesmo; acima disso o BI erra e a plataforma não.

## 13. Páginas Vendas (abate e em pé) e Compras (15/10)

**Pergunta:** os cards e o quadro por sexo das páginas Venda Abate, Venda em Pé e Compras batem com o BI de
planilhas?

**Como foi feito** (`python -m validacao.cruzar_compras_e_vendas --sorteios N --semente S`):
- o mesmo sorteio do §12 (1 a 3 fazendas do mesmo cliente, 1 a 12 meses, as 110 fazendas estáveis);
- lado plataforma: as funções que atendem `GET /dashboards/vendas` e `GET /dashboards/compras` (`app/kpis/vendas.py`,
  `compras.py`, com as contas comuns em `lotes.py`);
- lado BI: as linhas de `pecuarioVendaAbate`/`pecuarioVendaEmPe`/`pecuarioCompras` (realizado) e
  `fMetasAbate`/`fMetasEmPe`/`fMetasCompras` (planejado), pelo SQL do PBIX, com as medidas DAX: @ do abate e da compra
  = Σ(peso_arroba × qtd); @ em pé = Σ kg vivo ÷ 30; preço da @, preço do kg, peso médio, rendimento de carcaça e ágio
  como no BI; o recorte por sexo pela coluna `sexo`;
- cada sorteio conta uma vez por recorte (GERAL, MACHO, FÊMEA) e cenário em que algum lado teve venda.

**Resultado** (duas amostras: 300 sorteios com semente 7 e 600 com semente 11; desde 15/10 o sorteio parte de uma
lista de fazendas em ordem fixa, então a mesma semente dá sempre os mesmos filtros):

| Medida | Abate realizado | Abate planejado | Em pé realizado | Em pé planejado |
|---|---|---|---|---|
| Cabeças | 100% | 100% | 88,5–92,0% (A3) | 96,2–98,2% (A20) |
| Faturamento | 100% | 100% | 92,5–94,5% (A3, A17) | 96,2–98,2% (A20) |
| Preço da @ | 100% | 100% | 84,5–87,6% (A3, A17) | 98,6–99,1% (A20) |
| Peso médio vivo | 100% | 100% | 87,0–88,5% (A3, A17) | 98,6–99,1% (A20) |
| Rendimento de carcaça / preço do kg | 100% | 100% | 84,5–87,6% (A3, A17) | 98,6–99,1% (A20) |

| Compras | Realizado | Planejado |
|---|---|---|
| Cabeças e investimento | 100% | 100% |
| Preço do kg e peso médio | 100% | 97,2–100% (A17) |
| Preço da @ de compra | 92,1–96,2% (A21, A22, A17) | 96,1–98,6% (A22) |
| Ágio | 86,9–94,4% (A3, A17, A21, A22) | — (o BI não tem ágio planejado) |

**Nenhuma diferença sem explicação.** O script classifica cada uma:
- **A3** (já decidido na Q3): venda em pé sem cliente. O Pentaho descarta a linha, e o BI não a mostra nas vendas,
  embora a desconte do estoque. A plataforma mostra (ex.: 100 · IPIRANGA, 288 cab; 67 · PADRE PIO, 66 cab);
- **A17** (já decidido na Q7): faturamento ou peso total vazio com valor por cabeça preenchido. O BI soma 0; a
  plataforma calcula (ex.: 149 · HORIZONTE, 1 novilha de R$ 1.675 em 20/09/2025);
- **A20** (achado novo, decisão Q8): meta com data digitada "DDMM/AAAA" (`0108/2025`, `0107/2025`, `0106/2026`). O SQL
  das metas do BI tira a barra e lê 01/08/2025; a plataforma põe a linha na quarentena ("sem data válida"), com aviso.
- **A21** (achado novo): a arroba da compra arredondada na planilha. O BI soma PESO_ARROBA (2 casas) × QTD; a
  plataforma usa o kg vivo ÷ 30 (ex.: 6,13 × 31 = 190,03 @ contra 5.700 ÷ 30 = 190,00 @). Diferença abaixo de 1% no
  preço da @ (nos sorteios, até 0,03%). A forma do cálculo é livre e a da plataforma é a exata;
- **A22** (achado novo): linha com o total diferente do valor por cabeça × QTD. Ex.: meta da ÁGUA SANTA com 500
  cabeças de 270 kg e TOTAL_PESO de 270.000 kg, o dobro. O BI acerta a @ por usar a coluna por cabeça; a plataforma
  usa o total (como o próprio BI faz no peso médio). A carga agora avisa (`TOTAL_INCONSISTENT`: total e valor por
  cabeça × QTD diferindo mais de 5%) e a linha aparece em Pendências para ser corrigida. No banco de validação: 113
  linhas em 30 fazendas.

Conferência também na tela, com o painel aberto: MARAJÓ (4 fazendas, jul–ago/2025, abate) e ESTÂNCIA NOVA
(jul/2025–jun/2026, em pé com metas) mostraram os mesmos números do BI em todos os recortes.

**Achados novos** (para a tabela de achados; A23 e A24 vêm do §14):

| # | Achado | Tamanho | Origem |
|---|---|---|---|
| A20 | Meta com data digitada sem a primeira barra ("0108/2025"). O SQL das metas do BI lê só os dígitos (DDMMAAAA) e acerta; o do realizado não (A18) | 5 linhas de meta em 3 fazendas: AGRO PM, PALMEIRAS e PALMEIRAS PECUÁRIA (as duas do projeto 87 têm as mesmas metas, salvas com 2 minutos de diferença; o BI também as trata como duas fazendas, e só a PALMEIRAS PECUÁRIA tem realizado) | planilha |
| A21 | Arroba da compra arredondada na planilha (PESO_ARROBA com 2 casas): o BI soma a coluna arredondada | diferença de até 0,03% no preço da @ de compra | planilha |
| A22 | Total diferente do valor por cabeça × QTD (ex.: TOTAL_PESO dobrado) | 113 linhas em 30 fazendas (aviso `TOTAL_INCONSISTENT`, em Pendências) | planilha |
| A23 | Transferência planejada com QTD fracionária (meta calculada na planilha): o ETL do BI trunca para inteiro, mesmo com a coluna do datalake em `double precision` (234,58 → 234) | 6 dos 300 sorteios; PANADERO e KEGE RANCH → DONA LUIZA | BI (ETL) |
| A24 | QTD com mais de 3 casas na planilha (meta de morte de 0,55856 cabeça): o canônico guarda 3 casas por linha | 2 dos 300 sorteios, 0,012 cabeça em 9 a 10 meses (ÁGUAS CLARAS) | plataforma (precisão) |

## 14. Páginas Nascimentos, Mortes e Transferências (15/10)

**Pergunta:** os quadros e os gráficos das páginas Nascimentos, Mortes e Transferências batem com o BI de planilhas?

**Como foi feito** (`python -m validacao.cruzar_zootecnico --sorteios N --semente S`):
- o mesmo sorteio do §12 (1 a 3 fazendas do mesmo cliente, 1 a 12 meses, as 110 fazendas estáveis);
- lado plataforma: as funções que atendem `GET /dashboards/nascimentos`, `/mortes` e `/transferencias`
  (`app/kpis/nascimentos.py`, `mortes.py`, `transferencias.py`, com as contas comuns em `lotes.py`);
- lado BI, pelo SQL do PBIX e com o recorte pela coluna da própria tabela, como os filtros dos cards:
  `pecuarioNascimento`/`fMetasNascimentos` (por `sexo`); `pecuarioMortes`/`fMetasMortes` e
  `pecuarioRebanhoMedioMensal` (por `grupo_categoria`; as causas por `causa`); `fTransferencias`/`fMetasTransferencias`
  (entrada e saída pela coluna `operação`, recorte por `sexo`). Medidas DAX: "IN - % Female/Male Birth" (nascimentos
  do sexo ÷ total), "% mORTALITY ( MEAN MONTH)" (mortes ÷ "Mean Month" do grupo: Σ cabeças ÷ meses com rebanho > 0),
  "% Mortality" (mortes acumuladas ÷ nascimentos acumulados), "IN - AVG Weight Transfer" (Σ peso ÷ Σ qtd) e
  "IN - AVG Price @ Transfer" (Σ valor ÷ Σ(peso_arroba × qtd));
- cada sorteio conta uma vez por recorte e cenário em que algum lado tem número.

**Resultado** (300 sorteios, semente 7):

| Nascimentos | Realizado | Planejado |
|---|---|---|
| Cabeças (Geral, Macho, Fêmea) | 100% | 100% |
| Parte do sexo no total | 100% | — |

| Mortes | Realizado | Planejado |
|---|---|---|
| Cabeças (Geral, Bezerros, Jovens, Adultos) | 100% | 99,4% (A24) |
| Mortalidade sobre o rebanho médio do grupo | 100% | — |
| Mortalidade dos bezerros sobre os nascimentos | 73,9% (P3) | — |
| Mortes por causa (a lista inteira) | 100% | — |

| Transferências | Entrada realizado | Entrada planejado | Saída realizado | Saída planejado |
|---|---|---|---|---|
| Cabeças | 100% | 95,1% (A23) | 100% | 96,4% (A23) |
| Peso médio | 97,6% (A17) | 94,2% (A23) | 95,4% (A17) | 96,2% (A23) |
| Preço da @ | 97,5% (A21, A22) | 78,9% (A21, A23) | 98,7% (A21) | 96,2% (A23) |

**Nenhuma diferença sem explicação.** O script classifica cada uma:
- **P3** (já catalogado: um único conceito de acumulado): o "% Mortality" do BI divide as mortes de bezerros do
  período pelos nascimentos acumulados desde janeiro (período dentro de um ano civil) ou desde o início do calendário
  (período que pega dois anos). A plataforma divide pelos nascimentos do mesmo período. As 23 diferenças batem quando
  o número do BI é refeito com os nascimentos do período. O gráfico acumulado de nascimentos segue a mesma regra;
- **A17, A21, A22**, como no §13: peso total vazio (A17), arroba arredondada na planilha (A21) e total errado na linha
  (A22);
- **A23** (achado novo): meta de transferência com QTD fracionária. O ETL do BI trunca para inteiro, embora a coluna
  do datalake seja `double precision`: na PANADERO, a meta de entrada de 05/2025 tem 234,58 cabeças na planilha e 234
  no BI; na transferência KEGE RANCH → DONA LUIZA, 156,465 vira 156. A plataforma guarda o número da planilha, e o
  peso médio e o preço da @ do planejado mudam junto;
- **A24** (achado novo): QTD com mais de 3 casas na planilha (metas de morte calculadas por fórmula, ex.: 0,55856
  cabeça por linha na ÁGUAS CLARAS). O canônico guarda 3 casas por linha (`numeric(14,3)`); somados 9 a 10 meses, a
  diferença é de 0,012 cabeça e não aparece na tela, que mostra cabeças inteiras.

Regras da plataforma nesta página (o script aplica a mesma regra dos dois lados):
- causa de morte: o texto da fonte sem espaços nas pontas e em maiúsculas; vazia vira "NÃO INFORMADO", o texto que as
  planilhas já usam (o BI mostra a vazia à parte, como "(Em branco)");
- morte de categoria ainda sem de-para entra só no Geral (nada some do total).

Conferência na tela, com o painel aberto: AUGUSTO VIDIGAL (grupo, safra 25/26) nas três páginas, e um grupo Metryx
(Agropecuária Maister LTDA) pela API.

**Observação para a Q10:** a página Mortes mostrou causas como "AJUSTE DE AUDITORIA 25/26" (Metryx) e "AJUSTE DE
SALDO", "AJUSTE SISTEMA" (planilhas), que são ajustes de estoque lançados como morte. Os dois BIs contam essas linhas
como morte; a plataforma também, até a decisão da Q10 (§7).

## 15. Página Financeiro (15/10)

**Pergunta:** os números da página Financeiro batem com o BI de planilhas?

**Como foi feito** (`python -m validacao.cruzar_financeiro --sorteios N --semente S`):
- o mesmo sorteio do §12 (300 sorteios, semente 7, nas 110 fazendas estáveis);
- lado plataforma: a função que atende `GET /dashboards/financeiro` (`app/kpis/financeiro.py`);
- lado BI: as linhas de `financeiroDre` e `fMetasDre` (o SQL do PBIX), `pecuarioRebanhoMedioMensal`,
  `fMetasRebanhoMedio` e as vendas, com as medidas DAX: "Revenues" (créditos com tipo Receita Pec ou Agr), "Expenses
  Graph" (débitos), "Balance" (todas as receitas − débitos), "Outlay" (contas DCM), "Costing" (contas CCM),
  "head outlay accumulated" e "Costing head Accumulated" (valor ÷ rebanho médio ÷ nº de meses), "AVG Price @ (Em Pe +
  Abate)" e o desembolso por centro com DCM e REP.;
- cada medida do BI é somada também pela regra da plataforma (classificação de `dim.centro_custo` pelo nome do
  centro, estorno virando crédito, débito − crédito nas contas de desembolso e custeio). Quando a plataforma bate com
  essa soma e não com a do BI, a diferença é só a classificação da conta (P4).

**Resultado** (300 sorteios, semente 7):

| Medida | Realizado | Planejado |
|---|---|---|
| Receitas (pecuária + agricultura) | 100% | 100% |
| Despesas (fluxo de caixa) | 100% | — |
| Saldo (fluxo de caixa) | 64,2% (P4) | — |
| Desembolso | 18,2% (P4) | 32,1% (P4, A20) |
| Custeio | 75,0% (P4) | 62,6% (P4, A20) |
| Desembolso por cabeça por mês | 15,4% (P4) | 25,6% (P4, P2, A20) |
| Custeio por cabeça por mês | 74,8% (P4) | 54,5% (P4, P2, A20) |
| Desembolso por centro de custo | 59,5% (P4) | — |
| Preço da @ vendida | 92,8% (A3) | 99,1% (A20) |

**Nenhuma diferença sem explicação.** O script classifica cada uma:
- **P4** (catalogado: dois de-paras de conta divergentes; a plataforma tem um só, `dim.centro_custo`): a plataforma
  bate com as mesmas linhas somadas pela classificação da dimensão. As maiores diferenças: "Rebanho Investimento"
  (compra de gado), que a planilha marca como reposição (REP., fora do desembolso) e a dimensão como desembolso; e
  "Financiamentos débitos", fora do desembolso na planilha e dentro na dimensão. No total das planilhas: desembolso
  R$ 1,82 bi pela dimensão × R$ 1,11 bi no BI (+63,6%), custeio +1,8%. O saldo também muda, porque a planilha classifica
  algumas outras receitas por subconta. A decisão está na Q11 (§7), junto com a D3;
- **A20**: meta do DRE com a data digitada errada ("01/092025", AGRO SERINGUEIRA TOCANTINS, R$ 6.050). O SQL das
  metas do BI corrige; a carga põe a linha na quarentena ("valor sem data de pagamento") e ela aparece em Pendências;
- **P2**: por cabeça planejado num período sem rebanho realizado. O BI divide a meta pelos meses com rebanho
  REALIZADO e fica vazio; a plataforma divide pelo rebanho planejado;
- **A3**: preço da @ vendida com venda em pé sem cliente (como no §13).

Regras da plataforma nesta página (`app/kpis/financeiro.py`):
- desembolso e custeio = débitos − créditos nas contas marcadas: o crédito numa conta de despesa é estorno e abate,
  como o valor negativo que o BI soma;
- o saldo do fluxo de caixa soma todas as receitas, inclusive as outras, como a linha do BI (a barra de receitas
  mostra só pecuária e agricultura, também como o BI: docs/analises/01 §8.1, item 7);
- uma linha de meta sem a coluna CENTRO_DE_CUSTO_BI é classificada pela tradução da própria planilha
  (BASEPLANODECONTAS); o BI a deixa sem classificação (ex.: "SILAGEM" da ITAÚBA, R$ 61 mil de meta).

Conferência na tela, com o painel aberto: AGROPECUÁRIA SERINGUEIRA TOCANTINS (safra 25/26), e um grupo Metryx
(Agropecuária Maister LTDA) pela API.

## 16. Página Previsto × Realizado (15/10)

**Pergunta:** a matriz do DRE (realizado × planejado por classificação e conta, no mês e no acumulado) bate com o BI?

**Como foi feito** (`python -m validacao.cruzar_previsto --sorteios N --semente S`):
- o mesmo sorteio do §12 (300 sorteios, semente 7, nas 110 fazendas estáveis);
- lado plataforma: a função que atende `GET /dashboards/previsto_realizado` (`app/kpis/previsto_realizado.py`);
- lado BI: a tabela `planejadoXRealizado` (o SQL do PBIX), por classificação (inclusive a linha sintética
  "B - DESEMBOLSO"), no último mês do período ("Valor/Meta Último Mês Selecionado") e no acumulado ("Value/Meta
  Accumulated"); o resultado como o total da matriz do BI (receitas − investimentos − custeio);
- para explicar as diferenças, as linhas de `financeiroDre`/`fMetasDre` somadas como o BI soma ("bruto", sem o join da
  matriz) e pela regra da plataforma ("recalculado"); cada linha que soma diferente é marcada com a causa, e a
  diferença de uma classificação é atribuída à causa que mais pesou nela.

**Resultado** (300 sorteios, semente 7; % de sorteios iguais):

| Classificação | Realizado mês | Realizado acumulado | Planejado mês | Planejado acumulado |
|---|---|---|---|---|
| A - Receitas | 100% | 98,3% (A26) | 92,3% (A25) | 94,2% (A25) |
| B - Desembolso | 76,7% (P4, A26) | 62,8% (P4, A26, A20) | 82,7% (P4, A25, A26, A27) | 72,5% (P4, A25, A26, A27, P9) |
| C - Investimentos | 99,0% (A26) | 95,1% (A26) | 100% | 100% |
| D - Custeio | 76,7% (P4, A26) | 64,2% (P4, A26, A20) | 82,7% (P4, A25, A26, A27) | 72,5% (P4, A25, A26, A27, P9) |
| E - Outros créditos | 100% | 93,1% (A26) | 100% | 100% |
| F - Outros débitos | 100% | 100% | 100% | 100% |
| Resultado | 50,5% (P1, linhas) | 35,8% (P1, linhas) | 61,4% (P1, linhas) | 53,4% (P1, linhas) |

**Nenhuma diferença sem explicação.** As causas:
- **P1** (catalogado): o total da matriz do BI subtrai "E - OUTROS DÉBITOS", que não existe (a classificação é
  "F - OUTROS DÉBITOS"), e deixa os outros créditos e débitos de fora. A plataforma faz receitas + outros créditos −
  (investimentos + custeio + outros débitos), a recomendação da D1, ainda pendente (`TODO(D1)`);
- **P4** (catalogado): "Culturas - Despesa" não está no CASE de classificação do SQL do BI (fica sem classificação);
  a `dim.centro_custo` a põe no custeio. Nas planilhas: R$ 18 mi no realizado e R$ 11 mi nas metas;
- **P9** (catalogado): o join do `planejadoXRealizado` perde meta ou duplica realizado (1 sorteio);
- **A20**: meta com a data digitada errada, na quarentena (§15);
- **A25** (achado novo): a matriz do BI soma o débito e o crédito de uma conta do mesmo lado: um débito numa conta
  de receita (ex.: compra de gado lançada em "Rebanho") aumenta a receita, e um crédito numa conta de despesa aumenta
  a despesa. A plataforma põe cada um do seu lado (crédito − débito nas receitas; débito − crédito nas despesas). Nas
  planilhas: R$ 7 mi no realizado e R$ 79 mi nas metas, quase tudo débito em conta de receita;
- **A26** (achado novo): a matriz soma as linhas com operação VERIFICAR (conta fora do plano), que as medidas do
  Financeiro do próprio BI não somam; a plataforma as põe na quarentena e elas aparecem em Pendências. Nas planilhas:
  R$ 15 mi no realizado e R$ 9 mi nas metas;
- **A27** (achado novo): a matriz descarta as linhas sem CENTRO_DE_CUSTO_BI; a plataforma as classifica pela tradução
  da própria planilha (BASEPLANODECONTAS) ou como "A classificar". Nas planilhas: R$ 6 mi no realizado e R$ 14 mi
  nas metas;
- **"nas linhas"**: no resultado, a diferença que sobra depois do P1 vem das classificações, já explicadas acima.

| # | Achado | Tamanho | Origem |
|---|---|---|---|
| A25 | Matriz do Previsto × Realizado soma débito e crédito da mesma conta do mesmo lado | R$ 7 mi (realizado) e R$ 79 mi (metas) nas planilhas | BI (SQL) |
| A26 | Matriz soma as linhas VERIFICAR, que o Financeiro do BI não soma | R$ 15 mi e R$ 9 mi; na plataforma ficam em Pendências | BI (SQL) |
| A27 | Matriz descarta as linhas sem CENTRO_DE_CUSTO_BI | R$ 6 mi e R$ 14 mi | BI (SQL) |

Regras da plataforma nesta página (`app/kpis/previsto_realizado.py`): "mensal" = o último mês do período escolhido;
acumulado = o período (P3); contas neutras e "A classificar" mostram a soma dos dois lados e não entram no resultado;
o semáforo segue a regra do BI ("Icon"), com o limiar de `dim.parametro` (3%), e não aparece sem planejado.

Conferência na tela, com o painel aberto: AGROPECUÁRIA SERINGUEIRA TOCANTINS (safra 25/26), com o custeio aberto
por conta.

## 17. DMG do próprio Metryx × plataforma: Serra Dourada, jul–set/2026 (15/10)

**Pergunta:** o "Relatório de DMG" do Metryx (Serra Dourada, 01/07 a 30/09/2026, todos os retiros), trazido pela
equipe, mostra saldo anterior de 4.750 cabeças e final de 5.039; a plataforma mostra 4.825 e 5.114. Por quê?

**Como foi feito:** o DMG, lido do PDF, comparado com:
- a plataforma: `fato.estoque_mensal` e `fato.mov_animal` da fazenda Metryx no banco de validação;
- o BI Metryx: o SQL `fSaldoGado` do PBIX rodado no datalake METRYX (snapshot de 13/10);
- uma razão por lote de nascimento, feita com as tabelas do datalake que o BI lê: `stg_nascimentos` −
  `stg_mortes` − `stg_desmames`, comparada com o último registro de `stg_balanco_pecuario` em cada data;
- a planilha do consultor para a mesma fazenda ("SERRA DOURADA", origem Integração Planilhas).

**Resultado:**

| | DMG do Metryx | Plataforma | BI Metryx |
|---|---|---|---|
| Saldo anterior (30/06) | 4.750 | 4.825 | 4.825 |
| BEZERRA FEMEA em 30/06 | 444 | 478 | 478 |
| BEZERRO MACHO em 30/06 | 259 | 300 | 300 |
| As outras 12 categorias do DMG, em 30/06 e em 30/09 | — | iguais ao DMG | iguais ao DMG |
| Movimentos do trimestre: nascimentos 1.001, compras 7, vendas 663 (abate 340 e em pé 323), mortes 50, consumo 6, desmames 652 | — | iguais | iguais |
| Saldo final (30/09) | 5.039 | 5.114 | 5.114 |

**Causa:** a diferença está toda no saldo de bezerros (+34 bezerras e +41 bezerros = 75) e passa intacta do saldo
anterior para o final, porque os movimentos do período batem um a um. Não é diferença de cálculo:
1. **A plataforma é igual ao BI Metryx.** As duas usam a mesma regra (`fSaldoGado` sobre o balanço pecuário), a
   referência combinada para o estoque Metryx.
2. **Os dados que o Metryx exporta fecham entre si.** Em todo lote nascido desde 2025, nascimentos − mortes −
   desmames é igual ao balanço pecuário, em 30/06 e em 30/09. Pelo que o Metryx exporta, a fazenda tinha 478
   bezerras e 300 bezerros em 30/06. O DMG tem 75 a menos, e nenhum movimento exportado explica isso.
3. **Onde estão os 75.** Os desmames do trimestre são os mesmos no DMG (399 fêmeas, 253 machos) e esvaziam os lotes
   10/25 e 11/25. Por isso, a diferença só cabe nos lotes que ainda têm bezerro em 30/09:
   - o lote nascido em **12/25 no retiro ITIRATUPÃ**: transferido da SEDE em 30/04 e sem registro no balanço até
     01/07 (fêmeas) e 19/08 (machos). Em 30/09, o balanço ainda mostra 74 bezerras e 47 bezerros desse lote sem
     desmame;
   - **4 bezerras nascidas em 02/23**: com 3 anos, ainda na categoria de bezerra; último registro em 30/04/2026.

   O DMG deixa só 44 bezerras e 6 bezerros nesses lotes.
4. **A planilha do consultor confirma.** A safra 25/26 fechou junho com 478 bezerras (igual ao Metryx exportado) e
   330 bezerros (o consultor digitou 230 desmames de machos em maio; o Metryx tem 260). A safra 26/27 abre com
   444/259, o DMG. Na planilha, a plataforma mostra esse salto como ajuste de inventário em 06/2026 (−34 e −71).

**Conclusão até aqui:** alguma coisa no Metryx tira esses 75 bezerros do DMG com data até 30/06, e os dados de 13/10
não diziam o quê (Q12).

**Consulta à API real (15/10, autorizada pelo usuário, só GETs da allow-list, token do cliente cifrado no banco
`terra`):** os 12 endpoints pecuários desse cliente, comparados com o datalake de 13/10.
- **Causa:** o Metryx de hoje tem 3 lançamentos de morte que o datalake não tinha, todos datados de 30/06/2026, no
  retiro ITIRATUPÃ, com a causa **"AJUSTE DE SALDO"**:
  - 30 bezerras do lote 12/25;
  - 4 bezerras (as nascidas em 02/23);
  - 41 bezerros do lote 12/25.

  O balanço pecuário ganhou os registros correspondentes, em 30/06 (lote 12/25: 269 → 239 bezerras e 293 → 252
  bezerros; lote 02/23: 4 → 0), e os registros seguintes do lote baixaram o mesmo tanto. Nascimentos, desmames e
  vendas são idênticos ao datalake.
- **Resultado:** pela regra da plataforma (último registro de cada lote), o balanço de hoje dá exatamente o DMG: 444
  bezerras e 259 bezerros em 30/06, 522 e 499 em 30/09. Somando o saldo de implantação (`saldo-inical-pecuario`,
  30/06/2023) com todos os movimentos, o total também dá o do DMG: 4.750 e 5.039. A plataforma e o BI Metryx vão
  mostrar o mesmo número quando carregarem o dado novo. Nenhum cálculo muda.
- **Atenção:** o acerto entrou como morte. Como o BI, a plataforma vai contar 75 mortes de bezerros em 06/2026, e a
  mortalidade sobe junto. É exatamente o caso da Q10: com a opção (b), essas linhas viram "ajuste de inventário" e
  saem da mortalidade.
- **O saldo inicial da API** é o de implantação da fazenda (30/06/2023, 14 linhas, sem bezerros), e não um saldo por
  data. Não serve para conferir o DMG de um período.

Achados no payload real da API, **todos corrigidos no adapter** em 15/10, com testes no formato real
(`tests/test_metryx.py`):

| # | Achado | Efeito sem a correção | Correção |
|---|---|---|---|
| A29 | `mudanca-categoria-pecuario` devolve `idCustomer` errado: os 166 itens são da Serra Dourada (mesma fazenda, mesmo nome de cliente e dono), mas trazem outro id de cliente | A trava de segurança do adapter (item de outro cliente) derruba a carga inteira do cliente | Só nesse endpoint (`confere_pela_fazenda` na allow-list), o item vale se a fazenda dele for do cliente; o endpoint `fazenda` é conferido antes, pelo `idCustomer`, sem exceção. Nos outros endpoints, `idCustomer` diferente continua bloqueando |
| A30 | `venda-pecuario` e `compra-pecuario` vêm sem `idFarm`, apesar do OpenAPI; a transferência vem sem o id da fazenda de destino | A fazenda sai pelo nome (aviso `FARM_BY_NAME`), contra a regra de identidade por id | A fazenda sai pelo `idRetiro` (cada retiro tem a sua fazenda nos endpoints de cadastro, balanço, nascimento e desmame) |
| A31 | `transferencia-animal-pecuario`: as transferências antigas (49 de 86, de 07/2023 a 10/2025) vêm sem quantidade; as novas (desde 11/2024) vêm com ela. Nenhuma traz o retiro de origem | Sem quantidade: 98 linhas na quarentena, que o consultor não tem como corrigir. Sem o retiro de origem: a saída cai numa série sem retiro, que nenhum balanço corrige, e o estoque da fazenda desce 6.079 cabeças (foi o que a primeira recarga mostrou) | Sem quantidade: fica de fora, com um aviso só (`TRANSFER_WITHOUT_AMOUNT`). Sem o retiro de origem, dentro da mesma fazenda: as duas pontas ficam sem retiro e se anulam (o balanço de cada retiro mostra a troca); entre fazendas, a saída fica de fora |
| A32 | `mudanca-categoria-pecuario` repete cada desmame (115 dos 166 itens: mesma data, categorias, retiro e quantidade) e traz o `idRetiro` legado (inteiro), como a morte | O desmame entra em dobro (e um ajuste para compensar); a mudança cai num retiro fantasma, sem balanço, e as categorias BI ficam erradas (bezerro negativo, desmama inflada) | A mudança que repete um desmame fica de fora (aviso `CATEGORY_CHANGE_IS_WEANING`); o retiro legado é trocado pelo uuid do retiro de mesmo nome, como na morte |

**Recarga da Serra Dourada pela API real (15/10):** adapter de produção, só esse cliente, no banco de validação.
- **Primeira tentativa (A28–A30 já corrigidos):** quebrou o estoque, que ficou em 346 em 30/06 e −1.040 em 30/09.
  Foi o que revelou a segunda parte do A31 e o A32.
- **Depois das correções:** reprocessei a mesma versão guardada, sem chamar a API de novo. Usei `ignorar_guarda`,
  porque a guarda de volume segurou a troca de 166 por 51 mudanças, e a queda era legítima: desfazia a tentativa
  anterior. Os dois retiros fantasmas que essa tentativa criou ("620" e "613", sem nenhum dado) foram apagados.
- **Resultado: o trimestre bate 100% com o DMG, coluna por coluna, com ajuste zero em todas as categorias:**
  - saldo anterior 4.750; saldo final 5.039;
  - compras 7, nascimentos 1.001;
  - transferências 1.675 de entrada e 1.675 de saída;
  - mudanças de categoria 20 de entrada e 20 de saída;
  - desmames 652 de entrada e 652 de saída;
  - vendas 663, mortes 50, consumo 6.

  As 75 "mortes" de ajuste entram em 06/2026 (mortes da fazenda: 497 → 572; ver Q10).

**Achados menores deste cruzamento:**
- **A28 (plataforma), corrigido na migração 0015.** Uma compra que abria uma série nova (retiro × categoria) aparecia
  no estoque como "ajuste", e não como "compra". Caso real: 7 TOURO NELORE comprados em 07/07 para a SEDE, com o
  primeiro registro de touro na SEDE em 31/07. A causa estava em `fato.recalcular_estoque_mensal`: a função
  descartava os fluxos anteriores ao primeiro checkpoint de cada série, porque eles "já estão nele". A regra serve
  para o histórico de antes do saldo inicial, mas erra quando a série nasce do próprio movimento.

  Regra nova: o estoque da fazenda começa no **primeiro checkpoint da fazenda**. A série que ainda não aparece nele
  começa em zero, e o primeiro checkpoint dela corrige o que não fechar. Testes: `tests/test_estoque.py`; com a
  regra antiga, os dois testes novos falham como o caso real (compra 0, ajuste 7). Efeito no banco de validação,
  comparado com o estoque gravado antes da troca:
  - **Metryx:** nenhum saldo muda. Em 122 linhas (36 fazendas), o "ajuste" vira o movimento certo: compra,
    nascimento, entrada por desmame, abate, venda, morte. Isso tira 2.187 cabeças do ajuste. Na Serra Dourada,
    julho fica com compra 7 e ajuste 0, e o estoque continua 4.825 → 5.114. O cruzamento com o BI Metryx não muda
    (992 de 1.012 fazenda × mês iguais).
  - **Planilhas:** duas séries do histórico (Q6) sem saldo anterior perdiam a safra 25/26 inteira. Eram as categorias
    do histórico, que só recebem checkpoint 0 na virada para o arquivo:
    - SANTA LAVÍNIA, BEZERRO: 1.793 nascimentos que não apareciam no estoque;
    - CANGALHA, BEZERRA: 12 nascimentos.

    Com a regra nova, as duas fazendas se aproximam do BI Ciclo Completo:
    - SANTA LAVÍNIA chegava a ficar 1.728 cabeças abaixo dele (10.331 × 8.603 em 12/2025) e agora fica +27 em
      todos os meses;
    - CANGALHA oscilava entre −4 e +6 e agora fica +5 constante.

    As diferenças constantes já existiam e vêm de outra causa. O placar fazenda × mês não muda (2.140 de 2.692), e
    os KPIs da Movimentação (§12) dão a mesma saída. Três meses dessas séries ficam negativos (−4 e −1) porque o
    próprio histórico lança desmame antes de nascimento naquele retiro; o BI soma do mesmo jeito.
- **Mudanças de categoria.** Exemplos: 5 VACA → VACA DESCARTE e 15 NOVILHA DESCARTE → VACA DESCARTE. O datalake
  não as traz: `stg_mudanca_categoria` está vazia, porque o job do Pentaho que a carregaria é órfão (relatório 04).
  Por isso, no banco de validação, elas aparecem como ajuste entre categorias, com soma zero. Na carga pela API, o
  adapter já lê `mudanca-categoria-pecuario`, e elas viram fluxo.

## 18. Área de pasto do Metryx e lotação (16/10)

Pedido do usuário: a lotação cab/ha para os clientes Metryx, **sem a UA** por enquanto (o usuário vai pedir aos
desenvolvedores do Metryx que a API traga a UA).

- **Fonte:** `utilizacao-pasto`, que o Pentaho já extrai para `stg_area` (só a Serra Dourada tem dado hoje: 124
  períodos de 121 pastagens) e que o BI Metryx não usa. O BI Metryx calcula a lotação com uma área fixa de 500 ha e a
  UA fixa em 0 (P10). Por isso não há número do BI com que bater.
- **Regra:** a área do mês é a das pastagens de uso Pecuária no último dia do mês, valendo para cada pastagem o período
  mais recente que já começou. Na API o fim de um período é o começo do seguinte, e a regra conta a pastagem uma vez
  só. A área total vai para a lotação, como pasto + ILP na planilha; a produtiva fica guardada à parte. Os meses vão do
  primeiro período cadastrado até o último mês do rebanho médio. Código em `adapters/metryx/pasto.py`, testes em
  `tests/test_metryx.py` e no teste de equivalência.
- **Serra Dourada (ensaio sobre a `stg_area`):** pastagens desde jul/2023; 4.512 ha de pasto até jun/2026 e 5.726 ha a
  partir de jul/2026 (o retiro ITIRATUPÃ cresceu). A soma das áreas produtivas dá 2.866 ha, mas ela vem 0 em várias
  pastagens grandes, e por isso não é a base da lotação.
- **Planilha × Metryx da mesma fazenda:** a planilha da Serra Dourada informa 3.262 ha de pasto, abaixo dos 4.512 a
  5.726 ha do Metryx. Vale a equipe conferir qual área o consultor usa (só parte dos retiros? só a área útil?). Se for a
  produtiva, basta trocar o campo em `pasto.py`.
- **Meses com rebanho e sem área (Q13, decidido em 16/10: manter igual ao BI):** a lotação segue a fórmula do BI (Σ
  cabeças ÷ Σ área dos meses escolhidos), validada em 300/300 filtros (§12). Quando um mês com rebanho não tem área,
  as cabeças dele entram e a área não, e a lotação sobe:
  - na safra 25/26, 10 de 150 fazendas com área têm esse caso, mais 8 GRUPOs;
  - no Metryx, acontece ao escolher meses de antes do primeiro período de pasto.

  Os casos estão na anotação [2026-10-16_lotacao_meses_sem_area.md](2026-10-16_lotacao_meses_sem_area.md).
- **Carga real (16/10, com autorização do usuário):** a Serra Dourada foi recarregada pela API no banco de
  validação, só com os GETs da allow-list. O `utilizacao-pasto` respondeu 200: o token tem a permissão
  `UTILIZACAO_PASTO`; sem ela, a API responderia 403 e a área ficaria como estava, com um aviso.
  - Mudou só a área: 47 meses, de jul/2023 a mai/2027, porque o rebanho médio do Metryx vem até mai/2027. Movimentos,
    inventário, rebanho médio, lançamentos e estoque ficaram com as mesmas contagens e somas, e os avisos do job são
    os de antes.
  - Na tela (Movimentação, cliente Maria Cecília no Metryx):

    | Período | Lotação Cab | Conta |
    |---|---|---|
    | Safra 25/26 | **1,26** | 5.669 cab ÷ 4.512 ha |
    | Safra 26/27 (jul–out) | **0,93** | 5.310 cab ÷ 5.726 ha |

  - "Rebanho Médio UA" e "Lotação UA" seguem com traço.
  - A planilha da mesma fazenda dá 1,62 e 1,11, com 3.262 ha de pasto (ver o item acima).

## 19. Grupo U6 pela API real (20/10)

Pedido do usuário, que via diferenças no grupo U6 (cliente "GRUPO U6 - UEHARA": U6 BONITO, U6 PARTE IV, V e VI).
Até aqui o U6 vinha do datalake do Pentaho (ponte de validação), que não muda desde 14/10. O usuário passou o token do
cliente, cadastrado cifrado no banco de validação. A carga foi só com os GETs da allow-list.

- **A33: 401 num endpoint opcional.** O token do U6 não tem permissão para `transferencia-animal-pecuario` nem para
  `utilizacao-pasto`. A API responde **401** nesse caso, e não 403. O adapter tratava todo 401 como token inválido:
  abortava a carga e marcava a credencial como inválida. Agora:
  - 401 num endpoint obrigatório (`fazenda`, `categoria`, chamados primeiro) continua invalidando a credencial;
  - 401 num opcional, com o token já aceito, deixa só aquele endpoint de fora. Os dados dele ficam como estavam, e a
    carga registra o aviso `ENDPOINT_NOT_LOADED`.

  Teste: `test_401_num_endpoint_opcional_e_falta_de_permissao`.
- **O que mudou no banco:**
  - estoque: igual em todos os meses e categorias (8.718 em mar/2026, 8.235 em set/2026), porque segue o balanço do
    Metryx, que já estava em dia;
  - mudanças de categoria: agora entram como movimento, 220 lançamentos com 13.291 cabeças. Antes eram "ajuste de
    inventário", porque a `stg_mudanca_categoria` do datalake vem vazia (§17); 277 que repetiam um desmame ficaram de
    fora (A31);
  - financeiro: 75 lançamentos novos de out/2026 (R$ 623 mil de crédito e R$ 222 mil a mais de débito);
  - retiros: 8, antes 4, porque a ponte não tinha o endpoint `retiro`;
  - nascimentos, mortes, desmames, vendas, compras e rebanho médio: iguais.
- **O que continua diferente por fazenda:** as transferências entre as fazendas do grupo. Sem a permissão do endpoint,
  elas aparecem como "ajuste de inventário" em cada fazenda e se anulam no GRUPO. Exemplos: mar/2026 −76 no U6 BONITO e
  +76 no U6 PARTE V; jul/2026 +62/−62; ago/2026 −70/+70; set/2026 −73/+72 (BONITO/PARTE V). Para a página
  Transferências e o estoque por fazenda baterem com o Metryx, o token do U6 precisa da permissão do endpoint de
  transferências; para a lotação, da permissão `UTILIZACAO_PASTO`.
- A credencial do U6 está só no banco `terra_validacao`; no banco `terra` precisa ser cadastrada de novo
  (`python -m app.etl metryx-credencial`).

## 20. Metryx: bater sempre com o Metryx (20/10)

Decisão do usuário, 20/10/2026: **os clientes Metryx têm de bater SEMPRE com os relatórios do próprio Metryx**, e não
com o BI Metryx. As planilhas não mudam: as duas regras abaixo ficam só no adapter do Metryx.

Origem: o "Consolidado Pecuário" do grupo U6 exportado do Metryx em 20/10 (maio/2026) tinha 1 bezerra e 1 morte a
menos que o painel, que seguia o BI. Defeitos do BI que a plataforma deixa de reproduzir:

| # | Regra do BI Metryx | Regra do Metryx (adotada) | Exemplo |
|---|---|---|---|
| P16 | Bezerros mamando ("MESMA CHAVE"): cada mês vale o **maior** saldo do lote daquele mês em diante | No fim do mês vale o **último** saldo conhecido do lote, como o inventário do Metryx (`saldo.py`) | U6 PARTE V, lote 10/25: zera em 20/05 (desmame de 91) e tem 1 bezerra de novo em 20/06. O BI punha essa bezerra já em maio (32); o Metryx mostra 31 |
| P17 | Só a causa "Consumo Abate" é consumo; "Consumo Acidente" e "Doação" contam como morte | Causa "Consumo ..." ou "Doação" é consumo/doação, como o Consolidado Pecuário (`eh_consumo_ou_doacao` em `normalizar.py`) | U6 PARTE IV, 09/05: N2 com "Consumo Acidente". Mortes de maio: 13 no BI, 12 no Metryx |

A causa "Doação" segue o nome da seção do relatório ("Consumo e Doação"). Ainda falta ver num mês que tenha doação.
A causa "Ajuste de saldo" continua como morte (Q10).

**Reprocessamento** do banco de validação a partir do bruto guardado, sem chamar a API (a versão mais nova de cada um
dos 10 clientes Metryx):
- 395 cabeças passaram de morte para consumo/doação;
- 80 de 1.309 meses-fazenda mudaram de estoque, sempre para baixo, onde o "maior daqui em diante" inflava os bezerros.
  Exemplos: Ilha Bela set/2025 6.741 → 5.758; Santo André set/2025 5.074 → 4.540.

**Conferência com o Metryx depois da mudança:**

| | Metryx | Plataforma |
|---|---|---|
| U6, mai/2026: estoque inicial e final | 8.218 e 7.593 | 8.218 e 7.593 |
| U6, mai/2026: bezerras no fim do mês | 291 | 291 |
| U6, mai/2026: mortes e consumo/doação | 12 e 2 | 12 e 2 |
| Serra Dourada: estoque em 30/06 e 30/09/2026 (DMG) | 4.750 e 5.039 | 4.750 e 5.039 |
| Serra Dourada: mortes e consumo, jul–set (DMG) | 50 e 6 | 50 e 6 |

Daqui em diante a paridade com o BI Metryx (cruzamentos §12–§16) fica diferente nesses meses-fazenda. Isso é o
esperado: a referência dos clientes Metryx passou a ser o próprio Metryx.
