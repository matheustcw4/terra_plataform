# Anotação: lotação inflada nos meses sem área (Q13)

> Decisão do usuário em 16/10/2026: **manter a lotação igual ao BI**. Esta anotação registra o efeito para ninguém
> estranhar o número e para a equipe corrigir as planilhas na origem. Dados do banco de validação em 16/10/2026;
> para atualizar as listas, rode `python -m validacao.lotacao_sem_area` (em `backend/`, só leitura).

## O que acontece

A lotação (cabeças por hectare) do cartão "Rebanho Médio" da Movimentação é calculada como no BI: **soma das cabeças
dos meses escolhidos ÷ soma da área desses meses**.

Quando um mês tem gado registrado (rebanho médio) e não tem a área preenchida, as cabeças desse mês entram na conta e a
área não. O resultado é uma lotação **maior que a real**.

Exemplo: 1.000 cabeças todo mês, 500 ha de pasto, área preenchida em só 6 dos 12 meses.

| | Cabeças somadas | Área somada | Lotação |
|---|---|---|---|
| Real | | | 1.000 ÷ 500 = **2,0** |
| Como o BI e a plataforma calculam | 12 meses = 12.000 | 6 meses = 3.000 | **4,0** |

O mesmo acontece no **GRUPO** (todas as fazendas do cliente): se uma das fazendas tem gado e não tem área, as cabeças
dela entram e a área não.

## Como evitar sem mudar o cálculo

Preencher a área de pasto em **todos os meses** e em **todas as fazendas** do cliente: na planilha é a aba `fArea`;
no Metryx são as pastagens cadastradas, e a área vale a partir do primeiro período de uso delas.

## Onde acontece hoje

### Safra 25/26 (jul/2025 a jun/2026): 10 de 150 fazendas com área

| Fazenda | Cliente | Lotação no BI | Só os meses com área | Meses com gado e sem área |
|---|---|---|---|---|
| PRINCESA | OTÁVIO ZUCATO NETO | 6,18 | 2,28 | 7 |
| BELA VISTA | RAUL AMARAL CAMPOS E OUTROS | 3,16 | 1,26 | 6 |
| ESPERANÇA | RAUL AMARAL CAMPOS E OUTROS | 2,18 | 0,91 | 6 |
| HARAS | RAUL AMARAL CAMPOS E OUTROS | 13,25 | 6,16 | 6 |
| SANTA TEREZINHA | RAUL AMARAL CAMPOS E OUTROS | 4,68 | 2,25 | 6 |
| FURNA | RAUL AMARAL CAMPOS E OUTROS | 5,28 | 2,64 | 6 |
| ESTÂNCIA NOVA | WALDEMAR BUOSI FILHO | 1,82 | 0,97 | 5 |
| PARAISO | OTÁVIO ZUCATO NETO | 1,77 | 0,96 | 4 |
| ATTO SEMENTES | ATTO SEMENTES | 3,81 | 3,30 | 2 |
| ÁREA DIVÍNA | OTÁVIO ZUCATO NETO | 0,62 | 0,60 | 1 |

No GRUPO:

| Cliente | Lotação no BI | Só os meses com área | Fazendas com mês sem área |
|---|---|---|---|
| RAUL AMARAL CAMPOS E OUTROS | 3,77 | 1,72 | 5 |
| OTÁVIO ZUCATO NETO | 2,55 | 1,20 | 3 |
| WALDEMAR BUOSI FILHO | 1,82 | 0,97 | 1 |
| ELISABETE TORMENA FABRIS ALBUQUERQUE | 0,44 | 0,24 | 6 |
| CLAUDIO APARECIDO AUDER | 2,68 | 1,56 | 1 |
| MAISTER AGROPECUÁRIA LTDA | 1,27 | 0,91 | 4 |
| ARMANDO GOTTARDI FILHO | 2,13 | 1,58 | 1 |
| ATTO SEMENTES | 3,81 | 3,30 | 1 |

### Safra 26/27 (jul a out/2026): nenhuma fazenda sozinha; 4 GRUPOs

| Cliente | Lotação no BI | Só os meses com área | Fazendas com mês sem área |
|---|---|---|---|
| DANIEL FORTES BUSTAMANTE MARTINS MIGUEL | 13.438,75 | 3.877,50 | 1 |
| CLAUDIO APARECIDO AUDER | 1,91 | 0,61 | 1 |
| ARMANDO GOTTARDI FILHO | 1,10 | 0,99 | 1 |
| GUSTAVO MOTA FRANÇA | 1,07 | 0,99 | 1 |

**Atenção, outro problema:** no cliente DANIEL FORTES, a fazenda PARCERIA tem **0,1 ha** de pasto na planilha em
todos os meses, com 700 a 840 cabeças. O número absurdo vem dessa área, que parece um valor provisório, e não da
regra acima. A planilha precisa da área real.

### Safra 24/25

Nenhum caso (só 6 fazendas têm área nessa safra).

### Metryx

A área vem das pastagens cadastradas (relatório de validação §18). Na Serra Dourada, único cliente Metryx carregado
pela API até agora, as pastagens existem desde jul/2023. O efeito só apareceria escolhendo meses de antes disso.

## Se um dia mudar de ideia

A correção recomendada era contar as cabeças **só dos meses (de cada fazenda) que têm área**, mantendo a área como o
BI conta. Ela muda apenas as linhas acima; as outras fazendas continuam iguais ao BI. Fica em
`backend/app/kpis/movimentacao.py` (`rebanho_e_area`) e precisa ser registrada como defeito do BI que a plataforma não
reproduz (como os da Q3).
