# 03 — Pipeline de Planilhas (Pentaho → PostgreSQL): engenharia reversa e especificação do adaptador Python

> Escopo: planilhas `RELATÓRIO - <código> - <fazenda>.xlsm` (clientes que não usam o Metryx), o job Pentaho
> `Job Extract Data - Plan.kjb` e as transformações chamadas, o banco `DATALAKE_PLAN` e a tabela de RLS.
> Data da análise: 14/10/2026. Todas as leituras foram somente leitura (planilha de amostra copiada para o scratchpad,
> `openpyxl` em `read_only`; nenhuma macro executada). Senhas/strings criptografadas dos `.ktr/.kjb` = **[REDACTED]**.
> Nomes de pessoas (proprietários, destinatários, técnicos) foram anonimizados.

---

## 0. Sumário executivo

* **Fonte**: 230 arquivos `.xlsm` (1,67 GB; 5–9,7 MB cada) em `C:\Users\TerraDev\Meu Drive\Relatórios\`, espelhados do
  Google Drive por **rclone** (`gdrive:/Relatórios`, tarefa do Windows "Sync Drive", seg–sex 06:40/09:40/13:10/16:40).
  90 códigos de cliente distintos (até 13 arquivos por código = 1 arquivo por fazenda/unidade).
* **Template**: 32 abas; 22 são lidas pelo Pentaho (`fUnidade` + 11 de realizado + 10 `*PLANEJADO`, em 23 passos Excel Input), 3 abas de lançamentos
  (`fconsumodoacao`, `fmudcategoria`, `fdesmame`) só entram indiretamente via `fMovRebanho` (aba 100% fórmula).
  As colunas de identificação (PROPRIETÁRIO, FAZENDA, RETIRO, CÓDIGO_CLIENTE, PROJETO) existem em todas as abas f*,
  mas são **fórmulas** que apontam para `CADASTROINICIAL!B2:B7`, que por sua vez aponta para `fUnidade!A2:G2`.
* **Pentaho**: 9 transformações sequenciais, todas com o mesmo padrão
  `Excel Input (pasta inteira, sem regex) → Replace in string → Select values (tipagem) → Filter rows (descarta nulos) → Table output (TRUNCATE + INSERT)`.
  Não há Calculator, JavaScript, UDJC, normalizer/denormalizer, lookup ou upsert. Não há unpivot de meses
  (as planilhas já são "longas": uma linha por lançamento/mês).
* **Destino**: PostgreSQL `localhost:5432`, banco `DATALAKE_PLAN`, schema `"DATABASE"`, 23 tabelas `stg_*`
  (realizado, metas/planejado, unidades, área e RLS). Estratégia: **full reload** (truncate + insert) a cada execução.
* **Identidade da fazenda nos fatos**: os fatos **não** carregam o código do cliente (só `stg_area` e `stg_unidades`);
  o vínculo no Power BI é a chave textual `PROP_FAZ = unaccent(replace(concat(proprietário, fazenda),' ',''))`.
* **RLS**: `d_rls.ktr` carrega `Meu Drive\Levantamento Clientes para Power BI.xlsx` (297 linhas: base, código do cliente,
  proprietário, projeto, fazenda, técnico, e-mail técnico/gerente/regional) para `stg_rls`; o Power BI faz unpivot dos 3
  e-mails e aplica `RLS[e-mail] = USERNAME()` com relação `RLS.prop_faz → fUnidades.PROP_FAZ`.
* **Agendamento**: Pentaho Server CE 9.4 (Quartz), cron seg–sex 07:00, 10:00, 13:30, 17:00 (America/Cuiaba). Execução
  bem-sucedida dura ~6–10 min e lê ~13,2 milhões de linhas de Excel para gravar ~227 mil linhas.
* **Fragilidade comprovada**: só 62% (ago/26), 61% (set/26) e 39% (out/26 até dia 14) das execuções terminaram com
  sucesso; entre 05 e 12/10/2026
  o job falhou todos os dias por **uma única célula** (`fAbate`, linha 3, coluna `FATURAMENTO`) de um único arquivo,
  interrompendo todas as transformações seguintes (tabelas já truncadas/recarregadas parcialmente).
* **Recomendação central do adaptador**: processar **por arquivo** (hash SHA-256 + mtime), ler por **nome de cabeçalho
  com aliases** (não por posição), usar **valores em cache** das fórmulas apenas para colunas derivadas que não sabemos
  recalcular, normalizar datas/números no Python, validar por linha (quarentena em vez de abortar o lote), e gravar com
  **substituição atômica por unidade + versão de arquivo** (fatos sem ID natural) ou **upsert por (unidade, competência)**
  (fatos mensais/período), sempre identificando a unidade por `codigo_cliente` + fazenda/retiro normalizados, nunca pelo
  nome do proprietário.

---

## 1. Fontes analisadas

| Item | Caminho | Observação |
|---|---|---|
| Job | `...\Base de Planilhas\TerraDesenvolvimento\Job Extract Data - Plan.kjb` (mod. 20/08/2026) | Também existem `..._nTransf.kjb` (sem transferências) e `..._transf.kjb` (só transferências + RLS) |
| KTRs do job | `TerraDesenvolvimento\fCadastro.ktr, fArea.ktr, fVendas.ktr, fMovGado.ktr, fMetaCompras.ktr, fCompras.ktr, fNascimento.ktr, d_rls.ktr` | `fVendas.ktr.bak_antes_locale_2026-10-12` = versão anterior à correção de locale |
| fTransferências | `...\Metryx + Planilhas\Planilhas\fTransferências.ktr` (é a usada pelo job) | Comparada com `TerraDesenvolvimento\fTransferencias.ktr` (§4.8) |
| Fora do job | `Metryx + Planilhas\Planilhas\fDre.ktr`, `fPlanejamento.ktr` e cópias antigas (`fCompras`, `fMetaCompras`, `fMovGado`, `fNascimento`, `fVendas`) | §4.10 |
| Planilha amostra | `Meu Drive\Relatórios\RELATÓRIO - 85 - ITAPAJÉ - BELA VISTA.xlsm` (7,09 MB, mod. 14/10/2026 00:59) | copiada para `scratchpad\data\sample.xlsm` |
| Pasta inteira | 230 arquivos em `Meu Drive\Relatórios` | varredura de template (cabeçalhos/abas/fUnidade) em todos; varredura de qualidade em 1 a cada 3 (77 arquivos) |
| Fonte RLS | `Meu Drive\Levantamento Clientes para Power BI.xlsx` (aba `Planilha1`) | só estrutura/contagens; e-mails não reproduzidos |
| Execução | Pentaho Server CE 9.4.0.0-343 em `C:\Users\TerraDev\Downloads\Pentaho - Copia\...`; Quartz em `data\hsqldb\quartz.script`; logs `tomcat\logs\pentaho.log*` | JVM com `user.timezone=America/Cuiaba`, `user.language=pt`, `user.country=BR`, `-Xmx6144m` |
| Consumo (contexto) | extração do PBIX "ciclo" feita por outro agente em `scratchpad\pbix_ciclo\` | usada só para confirmar nomes/tipos de colunas no PG e regra de RLS |

Scripts usados (reprodutíveis, somente leitura) em `scratchpad\scripts\`: `p03_dump_kettle.py`, `p03_compact_ktr.py`,
`p03_xlsm_meta.py`, `p03_profile_sheets.py`, `p03_dump_cells.py`, `p03_check_positional.py`, `p03_survey_folder.py`,
`p03_analyze_survey.py`, `p03_quality_scan.py`. Saídas brutas em `scratchpad\out\p03_*`.

---

## 2. Anatomia da planilha

### 2.1 Arquivos e nomes

* Padrão nominal "oficial": `RELATÓRIO - <código> - <rótulo da fazenda>.xlsm`, mas há variações reais:
  `RELATÓRIO - 117- PORTO CYRIACO`, `RELATÓRIO -147-BARRA GRANDE`, `RELATÓRIO- 63-PANAMÁ`, `RELATÓRIO-63-SANTA LAVÍNIA`,
  `RELATÓRIOS - 26 - CRUZEIRO DO SUL`, `RELATÓRIO_35_RANCHO`, `RELATÓRIO - 47- ESTÂNCIA LUCIA .xlsm` (espaço antes da extensão).
  Regex que casa os 230 arquivos **após normalização Unicode NFC**:
  `^RELAT[ÓO]RIOS?\s*[-_]\s*(\d+)\s*[-_]\s*(.+?)\s*\.xlsm$` (grupo 1 = código, grupo 2 = rótulo).
* **9 nomes estão em Unicode NFD** (ex.: `RELATO\u0301RIO - 59 - GRUPO AA - ALTA FLORESTA.xlsm`, visível no log do rclone);
  sem normalizar, `Ó`/`Ã` não casam.
* Há **cópias duplicadas da mesma unidade** com nomes diferentes: `126 - MARANGUAPE` × `MARANGUAPE1`,
  `144 - ATTO SEMENTES.` × `ATTO SEMENTES..`, `22 - BHR AGROPECUÁRIA` × `BHR AGROPECUÁRIA - OK`, `94 - MATER` × `MATER (1)`,
  `15 - GUARÁ 1` × `16 - AGRO ZAFANELLI E SILVEIRA (AZS)` (mesmo proprietário+fazenda; o arquivo do código 15 está com
  `CÓDIGO PROJETO` vazio). O Pentaho deduplica apenas `stg_unidades`; **os fatos dessas cópias entram em dobro**.
* O código no nome bate com `fUnidade!D2` em 229/230 arquivos (o 230º tem o código vazio na planilha).
* Datas de modificação: de 12/09/2025 a 14/10/2026; 97 arquivos alterados em set–out/2026, 23 intocados desde set/2025
  → processamento incremental reduziria >50% do trabalho na maioria das execuções.
* Todos os 230 têm VBA (`xl/vbaProject.bin`, projeto protegido por senha); 19 têm vínculos externos
  (`xl/externalLinks`, ex.: `/Users/<consultor>/Downloads/Relatório de Inventário - BV.xlsx`, usado para o saldo inicial).

### 2.2 Abas (ordem do template) e finalidade

Template majoritário (208/230 arquivos). Variações: 20 arquivos usam `fconsumodoação` e `fmudançacateg` no lugar de
`fconsumodoacao`/`fmudcategoria`; 2 arquivos têm só a ordem das abas diferente. **Não existem tabelas (ListObjects)**;
os intervalos são "faixas pré-formatadas" com fórmulas arrastadas até a linha 1.000/2.000/3.000/10.000.

| # | Aba | Finalidade | Lida pelo Pentaho | Faixa / linhas de template | Proteção |
|---|---|---|---|---|---|
| 0 | `ConsultaPlanoContas` | Plano de contas (débitos/créditos) com classificação DESEMBOLSO/CUSTEIO/TIPO_CUSTEIO/D-C | não (lookup de `fDre`) | A1:G303 | não |
| 1 | `dCategorias` | Dimensão das 15 categorias BI (sexo, grupo, era) + lista SEXO | não | A1:F16 | sim |
| 2 | `BASEPLANODECONTAS` | De-para centro/subcentro "INTTEGRA" (nome local) → "METRYX" (nome padrão) | não (lookup de `fDre`) | A1:F210 | não |
| 3 | `PAINEL DE CONTROLE` | Menu com botões (macros de navegação); sem células | não | — | não |
| 4 | `REALIZADO` | Menu de navegação das abas de realizado | não | — | não |
| 5 | `PREVISTO` | Menu "CADASTRO DAS METAS - PLANEJADO" | não | — | não |
| 6 | `fUnidade` | **Cadastro da unidade** (1 linha) | **fCadastro** | A1:G2 (+ listas K2:L4) | não |
| 7 | `CADASTROINICIAL` | Parâmetros: cabeçalho da unidade, PERÍODO, de-para categoria da fazenda → categoria BI, saldo inicial, calendário de períodos, KPIs | não (alimenta fórmulas) | A2:AG2185 (uso real ~A2:AG74) | sim |
| 8 | `fArea` | Área de pasto/ILP por mês do período | **fArea** | A1:I13 (dim. até 129) | sim |
| 9 | `fDre` | Lançamentos financeiros realizados | **fMovGado.ktr** | A1:N10001 | sim |
| 10 | `fCompras` | Compras de gado | **fMovGado.ktr** e **fCompras.ktr** | A1:T3000 | sim |
| 11 | `fAbate` | Vendas para abate | **fVendas** | A1:X3000 | sim |
| 12 | `fVendaemPe` | Vendas em pé | **fVendas** | A1:T3000 | sim |
| 13 | `fMortes` | Mortes | **fNascimento.ktr** | A1:T3000 | sim |
| 14 | `fNascimento` | Nascimentos | **fNascimento.ktr** | A1:N1001 | sim |
| 15 | `fconsumodoacao` | Consumo/doação de animais | não (só via `fMovRebanho`) | A1:U1001 | sim |
| 16 | `ftranfentrada` | Transferências de entrada (entre fazendas) | **fTransferências** | A1:S3000 | sim |
| 17 | `ftranssaida` | Transferências de saída | **fTransferências** | A1:S2999 | sim |
| 18 | `fmudcategoria` | Mudança de categoria (saída/entrada) | não (só via `fMovRebanho`) | A1:R3000 | sim |
| 19 | `fdesmame` | Desmame (saída bezerro → entrada desmama) | não (só via `fMovRebanho`) | A1:P1000 | sim |
| 20 | `fMovRebanho` | **Movimentação consolidada** categoria × mês × operação (100% fórmula) | **fMovGado.ktr** | A1:J2176 | sim |
| 21 | `fRebanhoMedio` | Rebanho médio mensal por grupo (digitado) | **fMovGado.ktr** | A1:I37 | sim |
| 22 | `fDrePLANEJADO` | Orçamento financeiro (metas) | **fMetaCompras.ktr** | A1:N10001 | sim |
| 23 | `fAreaPLANEJADO` | Área planejada | **fMetaCompras.ktr** | A1:K13 | sim |
| 24 | `fComprasPLANEJADO` | Compras planejadas | **fMetaCompras.ktr** | A1:T1999 | sim |
| 25 | `fAbatePLANEJADO` | Abates planejados | **fMetaCompras.ktr** | A1:X1999 | sim |
| 26 | `fVendaemPePLANEJADO` | Vendas em pé planejadas | **fMetaCompras.ktr** | A1:T1999 | sim |
| 27 | `fMortesPLANEJADO` | Mortes planejadas | **fMetaCompras.ktr** | A1:T1999 | sim |
| 28 | `fNascimentoPLANEJADO` | Nascimentos planejados | **fMetaCompras.ktr** | A1:N1001 | sim |
| 29 | `ftranfentradaPLANEJADO` | Transf. entrada planejadas | **fTransferências** | A1:S1999 | sim |
| 30 | `ftranssaidaPLANEJADO` | Transf. saída planejadas | **fTransferências** | A1:S1999 | sim |
| 31 | `fRebanhoMedioPLANEJADO` | Rebanho médio planejado | **fMetaCompras.ktr** | A1:I37 | sim |

Em todas as abas f*: **linha 1 = cabeçalho**, dados a partir da linha 2, coluna A. A coluna A (`OPERAÇÃO`) vem
**pré-preenchida** com a constante da operação em todas as linhas do template (`COMPRA`, `ABATE`, `EMPÉ`, `MORTE`,
`NASCIMENTO`, `Transf. Entrada`, `Transf. Saida`, `Consumo/Doação`, `Mud. de Categoria`, `DESMAME`) — por isso
"linha não vazia" não significa "linha com dado"; o que define uma linha válida é a coluna-chave (DATA/QTD/VALOR…).

### 2.3 Onde ficam cliente, fazenda e período

| Informação | Célula de origem (entrada) | Propagação |
|---|---|---|
| Projeto/cliente (nome) | `fUnidade!A2` (ex.: `ITAPAJÉ`) | `CADASTROINICIAL!B2` → coluna `PROJETO` de todas as abas f* |
| Proprietário (pessoa/empresa) | `fUnidade!B2` (`<NOME DO PROPRIETÁRIO>`) | `CADASTROINICIAL!B5` → `PROPRIETÁRIO` |
| Fazenda | `fUnidade!C2` (ex.: `BELA VISTA`) | `CADASTROINICIAL!B6` → `FAZENDA` |
| Código do cliente/projeto | `fUnidade!D2` (ex.: `85`, inteiro) | `CADASTROINICIAL!B3` → `CÓDIGO_CLIENTE` |
| Sistema produtivo | `fUnidade!E2` (lista `sistema` = K2:K4: CRIA / RECRIA E ENGORDA / CICLO COMPLETO) | `CADASTROINICIAL!B4` |
| Retiro (sub-unidade) | `fUnidade!F2` (ex.: `BELA VISTA`; vazio em 4 arquivos) | `CADASTROINICIAL!B7` → `RETIRO` |
| Tipo de ano | `fUnidade!G2` (lista `ANO` = L2:L3: CÍVIL / SAFRA) | não usado em fórmulas relevantes |
| **Período ativo** | `CADASTROINICIAL!B8` (lista `PERÍODO` = O9:T9: SAFRA 24/25, SAFRA 25/26, SAFRA 26/27, CIVIL 2025, CIVIL 2026, CIVIL 2027) | define as 12 datas de `fArea`, `fRebanhoMedio`, `fMovRebanho` (e PLANEJADO) via `IFS(...HLOOKUP(B8, O9:T21, N<k>))`; "Saldo Anterior" usa a linha 22 (mês anterior ao início) |
| Código também no nome do arquivo | `RELATÓRIO - <código> - ...` | não usado pelo Pentaho (só gravado em `stg_unidades.filename`) |

Distribuição nos 230 arquivos: PERÍODO = SAFRA 25/26 (102), SAFRA 26/27 (78), CIVIL 2026 (45), SAFRA 24/25 (5);
SISTEMA = CICLO COMPLETO (97), RECRIA E ENGORDA (82), CRIA (50), vazio (1); ANO = SAFRA (186), CÍVIL (43), vazio (1).

> Consequência importante: ao trocar `B8` (ex.: SAFRA 25/26 → 26/27) as abas derivadas por período **re-datam** os
> mesmos valores digitados (área, rebanho médio) e o full reload **apaga o histórico** do período anterior em
> `stg_area`, `stg_frebanhomedio`, `stg_fmovgado` e metas correspondentes. 78 arquivos já estão em SAFRA 26/27.

### 2.4 Abas de configuração

**`fUnidade`** (lida por fCadastro) — A1:G1 = `PROJETO | PROPRIETÁRIO | FAZENDA | CÓDIGO PROJETO | SISTEMA PRODUTIVO | RETIRO | ANO`;
linha 2 = valores literais (entrada). K2:K4 e L2:L3 = listas para validação. Validações: `E2` lista `=sistema`, `G2` lista `=ANO`.
Linhas 3–4 têm valores só em K/L, por isso o Excel Input lê 3 linhas por arquivo (688 linhas para 230 arquivos) e o
filtro `PROJETO IS NOT NULL` deixa 230.

**`CADASTROINICIAL`** (protegida; não lida, mas é o "cérebro" das fórmulas):

| Faixa | Conteúdo | Tipo |
|---|---|---|
| A2:B7 | Rótulos + `=fUnidade!A2/D2/E2/B2/C2/F2` | fórmula |
| B8 | PERÍODO (validação lista `PERÍODO`) | entrada |
| A10:F10 | `CATEGORIA FAZENDA | CATEGORIA BI | SEXO | GRUPO CATEGORIA | ERA | SALDO INICIAL` | cabeçalho |
| A11:A74 (nome `CATFAZ`) | Nome local da categoria usado pela fazenda (ex.: `Desmama Macho`, `Garrote 12 a 24 Meses`, `GARROTES/BOIS`) — é a lista de validação de `CATEG_FAZENDA` em todas as abas f* | entrada |
| B11:B74 | Categoria BI correspondente (validação lista `CATEGORIABI` = `dCategorias!A2:A16`) | entrada |
| C/D/E 11:74 | `IFERROR(VLOOKUP(B, dCategorias, 2/3/4),0)` → SEXO, GRUPO, ERA | fórmula |
| F11:F74 | Saldo inicial do rebanho por categoria (na amostra: `VLOOKUP` em vínculo externo "Relatório de Inventário") | entrada/fórmula externa |
| H11:H22 (nome `OPERAÇÕES` = H11:H18) | Lista de operações: Saldo Anterior, Consumo/Doação, COMPRA, ABATE, EMPÉ, MORTE, NASCIMENTO, DESMAME, Mud. de Categoria, Transf. Entrada, Transf. Saida, SALDO FINAL | literal |
| J11:J12 (`VENDAS`) | Tipo de venda: EM PÉ / ABATE | literal |
| L11:L22 | Saldo calculado por operação (`SUMIF(fMovRebanho!A:A, H, fMovRebanho!C:C)`); `L22 = L11-L12+L13-L14-L15-L16+L17+L18+L19+L20-L21` (regra de sinal do estoque) | fórmula |
| N10:N22 | Índices de linha (2..14) usados no HLOOKUP | literal |
| O9:T9 (`PERÍODO`; `SAFRA`=O9:Q9; `CÍVIL`=R9:T9) | Rótulos dos períodos | literal |
| O10:T21 / O22:T22 | 1º dia de cada um dos 12 meses de cada período / mês anterior ao período | literal (datas) |
| W..Y 10:27 | Painel REALIZADO × PREVISTO: desembolso, DCM (R$/cab/mês = desembolso/rebanho médio/meses), meses decorridos, rebanho médio mensal; `Y9` = data de corte | fórmula/entrada |
| AA/AC 11:22 | Desembolso previsto por mês (`SUMIFS(fDrePLANEJADO, J="DCM", D=mês)`) | fórmula |
| AF/AG 10:57 | Centros de custo BI e soma do DCM realizado por centro | literal/fórmula |

Validações em `CADASTROINICIAL`: `B11:B74` lista `CATEGORIABI`; `B8` lista `PERÍODO`; `Y9` lista `$S$10:$S$22`.

**`dCategorias`** (protegida) — A1:D16 `CATEGORIA BI | SEXO | GRUPO CATEGORIA | ERA` (15 linhas) + F1:F3 lista `SEXO`:

| CATEGORIA BI | SEXO | GRUPO | ERA |
|---|---|---|---|
| BEZERRO | MACHO | BEZERROS | 00-08 |
| MACHOS 8-12 | MACHO | JOVENS | 08-12 |
| MACHOS 13-24 | MACHO | JOVENS | 13-24 |
| MACHOS 25-36 | MACHO | ADULTOS | 25-36 |
| MACHOS + 36 | MACHO | ADULTOS | +36 |
| TOUROS | MACHO | ADULTOS | +36 |
| TOUROS DESCARTES | MACHO | ADULTOS | +36 |
| SINUELO | MACHO | ADULTOS | +36 |
| BEZERRA | FÊMEA | BEZERROS | 00-08 |
| NOVILHAS 8-12 | FÊMEA | JOVENS | 08-12 |
| NOVILHAS 13-24 | FÊMEA | JOVENS | 13-24 |
| NOVILHAS 25-36 | FÊMEA | ADULTOS | 25-36 |
| MATRIZES | FÊMEA | ADULTOS | +36 |
| VACA DESCARTE | FÊMEA | ADULTOS | +36 |
| VACA LEITEIRA | FÊMEA | ADULTOS | +36 |

Cabeçalho idêntico nos 230 arquivos. É a dimensão canônica de categoria (equivale à categoria do Metryx).

**`ConsultaPlanoContas`** — A = conta hierárquica (`3.1.1 - Compra equipamentos…`), B = `MID(A, n, 100)` (nome da
subconta), C = DESEMBOLSO (`DCM`, `REP.`, `Receita Pec`, `Receita Agr`, `Receita outras`, `Financiamentos`, `0`),
D = CUSTEIO (`CCM`, …), E = TIPO_CUSTEIO (`CF`, `CV`, …), F = `D`/`C`. ~240 contas.

**`BASEPLANODECONTAS`** — A `CENTRO DE CUSTO - INTTEGRA` → B `CENTRO DE CUSTO - METRYX` (71 linhas);
D `SUBCENTRO - INTTEGRA` → E/F `SUBCENTRO - METRYX` (209 linhas; E usado quando o centro é "Investimentos em
infraestrutura", F nos demais). Ou seja, **a planilha já traduz o plano de contas local para a nomenclatura do Metryx**
— útil para unificar com o adaptador Metryx.

**`PAINEL DE CONTROLE` / `REALIZADO` / `PREVISTO`** — só formas com macros. O `vbaProject.bin` contém apenas
macros de navegação (`Sheets("…").Select`, `ActiveWindow.ScrollWorkbookTabs`): `UNIDADE`, `INICIAL`, `AREA`, `COMPRAS`,
`ABATES`, `VENDA_EM_PE`, `MORTES`, `NASCIMENTO`, `CONSUMO`, `TRANS_ENTRADA`, `TRANS_SAIDA`, `MUD_CATEG`, `DESMAME`,
`MOVESTOQUE`, `REBANHO_MEDIO`, `FINANCEIRO`, `PLANOCONTAS`, `BASEPLANODECONTAS`, variantes `*PREV`, `VOLTAR*`,
`REALIZADO`, `PREVISTO`. Nenhuma lógica de dados identificada (análise por strings, sem executar; projeto VBA
protegido). O adaptador pode ignorar o VBA.

### 2.5 Abas de fatos — realizado

Legenda: **E** = entrada (digitada pelo cliente/consultor), **F** = fórmula (valor em cache), **K** = constante
pré-preenchida no template. Colunas `PROPRIETÁRIO`, `FAZENDA`, `RETIRO`, `CÓDIGO_CLIENTE`, `PROJETO` são sempre
**F** (`=CADASTROINICIAL!$B$5/$B$6/$B$7/$B$3/$B$2`) e estão presentes até nas linhas vazias do template.
`DATA_ABREV` = `DATE(YEAR(data),MONTH(data),"1")` (1º dia do mês; vira `1900-01-01` quando a data está vazia).
`CATEGORIA_BI` = `IFERROR(VLOOKUP(CATEG_FAZENDA, CADASTROINICIAL!$A$11:$B$74, 2, FALSE), "")` (em `fCompras` o
fallback é `0`). `SEXO` = `VLOOKUP(CATEGORIA_BI, CADASTROINICIAL!B:C)`.

#### `fArea` (12 linhas; uma por mês do período)
| Col | Cabeçalho | Tipo | Origem | Exemplo |
|---|---|---|---|---|
| A | DATA | data (1º do mês) | F (mês do PERÍODO) | 2026-01-01 |
| B | ÁREA_PASTO | número (ha) | E | (vazio na amostra) |
| C | ÁREA_ILP | número (ha) | E (cabeçalho = `SILAGEM` em 2 arquivos e `ILP` em 1) | — |
| D | ÁREA_TOTAL | número | F `=B+C` | 0 |
| E–I | PROPRIETÁRIO, FAZENDA, RETIRO, CÓDIGO_CLIENTE, PROJETO | texto/int | F | BELA VISTA / 85 / ITAPAJÉ |

#### `fDre` (10.000 linhas de template; amostra: 672 lançamentos)
| Col | Cabeçalho | Tipo | Origem | Exemplo |
|---|---|---|---|---|
| A | CENTRO_DE_CUSTO | texto (nome local "INTTEGRA") | E | ADMINISTRAÇÃO |
| B | SUB_CENTRO | texto | E | OUTRAS DESPESAS ADMINISTRATIVAS |
| C | VALOR | número (R$, positivo) | E | 4727.64 |
| D | DATA_PAG | data | E (na amostra sempre dia 1) | 2026-01-01 |
| E | OPERAÇÃO | `D`/`C`/`VERIFICAR` | F `IFERROR(VLOOKUP(G, ConsultaPlanoContas!B:F, 5), "VERIFICAR")` | D |
| F | CENTRO_DE_CUSTO_BI | texto (nome Metryx) | F `VLOOKUP(A, BASEPLANODECONTAS!A:B, 2)` | Suporte à Produção Administração |
| G | SUB_CENTRO_BI | texto | F `VLOOKUP(B, BASEPLANODECONTAS!D:F, 2 ou 3)` | Outras despesas administrativas |
| H | FAZENDA | texto | F | |
| I | PROPRIETÁRIO | texto | F | (atenção: ordem H/I invertida em relação às outras abas) |
| J | DESEMBOLSO | texto (`DCM`, `REP.`, `Receita Pec`, `Financiamentos`, `VERIFICAR`…) | F `VLOOKUP(G, ConsultaPlanoContas!B:E, 2)` | DCM |
| K | CUSTEIO | texto (`CCM`, …) | F | CCM |
| L | TIPO_CUSTEIO | texto (`CF`, `CV`, …) | F | CF |
| M–N | CÓDIGO_CLIENTE, PROJETO | | F | |

#### `fCompras` (2.999 linhas; amostra: 7 compras)
| Col | Cabeçalho | Tipo | Origem | Exemplo |
|---|---|---|---|---|
| A | OPERAÇÃO | texto | K `COMPRA` | COMPRA |
| B | DATA | data | E | 2026-01-01 |
| C | ORIGEM | texto | E | Bela Vista |
| D | CATEG_FAZENDA | texto | E (validação lista `CATFAZ`) | GARROTES/BOIS |
| E | QTD | inteiro (cab) | E (validação decimal 0–10.000.000 em E:G) | 190 |
| F | PESO_VIVO | kg/cab | F `=G/E` (no realizado) / E (no PLANEJADO) | 250.80 |
| G | TOTAL_PESO | kg | E | 47652.2 |
| H | VALOR_CAB | R$/cab | F `=I/E` (realizado) / E (PLANEJADO) | 3444.39 |
| I | VALOR TOTAL | R$ | E | 654434.70 |
| J | VALO_KG | R$/kg | F `IFERROR(H/F,"")` | 13.73 |
| K | VALOR_ARROBA | R$/@ | F `IFERROR(J*30,"")` | 412.01 |
| L | DATA_ABREV | data | F | 2026-01-01 |
| M | CATEGORIA_BI | texto | F (fallback `0`) | MACHOS 13-24 |
| N | SEXO | texto | F | MACHO |
| O | PESO_ARROBA | @/cab | F `=F/30` | 8.36 |
| P–T | PROPRIETÁRIO, FAZENDA, RETIRO, CÓDIGO_CLIENTE, PROJETO | | F | |

#### `fAbate` (2.999 linhas)
A `OPERAÇÃO`=K `ABATE`; E: B `CLIENTE` (frigorífico), C `CATEG_FAZENDA` (lista CATFAZ), D `DATA`, E `QTD`, F `ERA`,
G `PESO_VIVO` (kg/cab), H `RENDIMENTO` (% carcaça), I `PESO_ARROBA` (@/cab), J `VALOR_ARROBA` (R$/@), K `FATURAMENTO` (R$);
F: L `DATA_ABREV`, M `CATEGORIA_BI`, N `SEXO`, O `PESO_MORTO` `=IFERROR(I*15,"")` (kg carcaça/cab), P `PESOVIVO_TOTAL` `=G*E`,
Q `PESOMORTO_TOTAL` `=O*E`, R `VALOR_KG` `=IFERROR(K/P,"")`, S `VALOR_CAB` `=IFERROR(K/E,"")`; T–X identificação.
Validação decimal 0–10.000.000 em E, G, I.

#### `fVendaemPe` (2.999 linhas)
A `OPERAÇÃO`=K `EMPÉ`; E: B `CLIENTE` (comprador), C `DATA`, D `DOCUMENTO` (GTA/NF), E `CATEG_FAZENDA`, F `QTD`,
G `PESO_VIVO`, H `PESOVIVO_TOTAL`, I `VALOR_ARROBA`, J `VALOR_CAB`, K `FATURAMENTO`;
F: L `DATA_ABREV`, M `CATEGORIA_BI`, N `SEXO`, O `VALOR_KG` `=IFERROR(K/H,"")`; P–T identificação.

#### `fMortes` (2.999 linhas; amostra: 29 registros)
A `MORTE`; E: B `DATA`, C `CATEG_FAZENDA` (ex.: `Boi 24 a 36 Meses`), D `CARIMBO_BEZ`, E `QTD`, F `CAUSA`
(ex.: SACRIFICADO, Acidente, Cobra, Desconhecido), G `LOCAL`, H `PESO_VIVO`, I `SAFRA`;
F: J `DATA_ABREV`, K `GRUPO_CATEGORIA`, L `ERA`, M `CATEGORIA_BI`, N `PESO_TOTAL` `=E*H`, O `SEXO`; P–T identificação.

#### `fNascimento` (1.000 linhas; amostra: 4)
A `NASCIMENTO`; E: B `DATA` (dia real, ex.: 2026-07-15), C `CATEG_FAZENDA` (ex.: `Fêmea 00 a 08 Meses`), D `QTD`,
E `SAFRA` (texto `26/27`), F `PESO_NASC` (kg); F: G `DATA_ABREV`, H `CATEGORIA_BI`, I `SEXO`; J–N identificação.

#### `ftranfentrada` / `ftranssaida` (2.999 / 2.998 linhas)
A `Transf. Entrada`/`Transf. Saida`; E: B `DATA`, C `CATEGORIA_FAZENDA` (atenção: nome diferente de `CATEG_FAZENDA`),
D `QTD`, E `PESO_VIVO` (kg/cab), F `TOTAL_PESO` (kg), G `VALOR TOTAL` (R$);
F: H `DATA_ABREV`, I `CATEGORIA_BI`, J `SEXO`, K `PESO_ARROBA` `=E/30`, L `VALOR_CAB` `=IFERROR(G/D,"")`,
M `VALO_KG` `=IFERROR(L/E,"")`, N `VALOR_ARROBA` `=IFERROR(M*30,"")`; O–S identificação.
(PESO_VIVO e TOTAL_PESO são ambos digitados → podem ficar inconsistentes.)

#### `fconsumodoacao`, `fmudcategoria`, `fdesmame` (não lidas diretamente)
* `fconsumodoacao`: A `Consumo/Doação`; E: `DATA, CATEGORIA_FAZENDA, QTD, PESO_VIVO, VALOR_CAB, TIPO, DESTINO` (texto livre,
  pode conter nome de pessoa); F: `VALOR_KG, VALOR_ARROBA, FATURAMENTO, DATA_ABREV, CATEGORIA_BI, SEXO, PESO_TOTAL, PESO_ARROBA` + identificação.
* `fmudcategoria`: E: `DATA, CATEGORIA_FAZENDA_SAÍDA, CATEGORIA_FAZENDA_ENTRADA, QTD, PESO_VIVO, TOTAL_PESO`;
  F: `DATA_ABREV, CATEGORIA_BI_SAÍDA, CATEGORIA_BI_ENTRADA, SEXO, IDADE, PESO_ARROBA` + identificação.
* `fdesmame`: E: `DATA, CATEGORIA_FAZENDA_SAÍDA, CATEGORIA_FAZENDA_ENTRADA, QTD, PESO_VIVO`;
  F: `DATA_ABREV, CATEGORIA_BI_SAÍDA, CATEGORIA_BI_ENTRADA, SEXO, IDADE` + identificação.

#### `fMovRebanho` (2.175 linhas, **100% fórmula**)
Grade fixa = 15 categorias BI × (1 linha "Saldo Anterior" + 12 meses × 12 operações) = 2.175 linhas.
A `OPERAÇÃO` (K), B `DATA` (F: mês do período; Saldo Anterior = mês anterior ao início), C `QTD` (F), D `CATEGORIA_BI` (K),
E `SEXO` (F `VLOOKUP dCategorias`), F–J identificação. Fórmulas de `QTD`:

| OPERAÇÃO | Linhas | QTD |
|---|---|---|
| Saldo Anterior | 15 | `SUMIF(CADASTROINICIAL!B11:B74, cat, CADASTROINICIAL!F11:F74)` |
| Consumo/Doação | 180 | `SUMIFS(fconsumodoacao!D, A=op, L=mês, M=cat)` |
| COMPRA | 180 | `SUMIFS(fCompras!E, A=op, L=mês, M=cat)` |
| ABATE | 180 | `SUMIFS(fAbate!E, …)` |
| EMPÉ | 180 | `SUMIFS(fVendaemPe!F, …)` |
| MORTE | 180 | `SUMIFS(fMortes!E, A=op, J=mês, M=cat)` |
| NASCIMENTO | 180 | `SUMIFS(fNascimento!D, A=op, G=mês, H=cat)` |
| DESMAME | 360 | saída: `-SUMIFS(fdesmame!E, …, H=cat_saída)`; entrada: `+SUMIFS(…, I=cat_entrada)` |
| Mud. de Categoria | 360 | saída: `-SUMIFS(fmudcategoria!E, …, I=cat_saída)`; entrada: `+SUMIFS(…, J=cat_entrada)` |
| Transf. Entrada | 180 | `SUMIFS(ftranfentrada!D, …)` |
| Transf. Saida | 180 | `SUMIFS(ftranssaida!D, …)` |

As quantidades são **positivas** (exceto as metades de saída de DESMAME/Mud. de Categoria); o sinal do estoque é
dado pela operação (`saldo = anterior − consumo + compra − abate − em pé − morte + nascimento + desmame + mud.cat + transf.ent − transf.saída`).
Lançamentos com data fora dos 12 meses do período **não aparecem** em `fMovRebanho` (mas aparecem nas abas de origem).

#### `fRebanhoMedio` (36 linhas = 3 grupos × 12 meses)
A `GRUPO_CATEGORIA` (K: Bezerros/Jovens/Adultos), B `QTD_CAB` (E, cabeças médias no mês, aceita decimal: 1989.3),
C `QTD_UA` (E, geralmente vazio), D `DATA` (F: mês do período), E–I identificação.

### 2.6 Abas de metas (`*PLANEJADO`)

Mesmos cabeçalhos das abas de realizado (confirmado nos 230 arquivos, salvo os desvios do §2.8), com menos linhas
(1.998 nas transacionais; 10.000 em `fDrePLANEJADO`; 12 em `fAreaPLANEJADO`; 36 em `fRebanhoMedioPLANEJADO`).
Diferenças de fórmula: em `fComprasPLANEJADO`, `PESO_VIVO` e `VALOR_CAB` são **entrada** (no realizado são fórmula).
Na amostra, várias abas PLANEJADO contêm exatamente os mesmos lançamentos do realizado (cópia), o que reforça que o
conteúdo planejado é livre e precisa de validação própria.

### 2.7 Nomes definidos, validações, proteção

* **Nomes definidos (globais)**: `ANO`=fUnidade!L2:L3, `sistema`=fUnidade!K2:K4, `CATEGORIABI`=dCategorias!A2:A16,
  `SEXO`=dCategorias!F2:F3, `CATFAZ`=CADASTROINICIAL!A11:A74, `OPERAÇÕES`=CADASTROINICIAL!H11:H18, `VENDAS`=J11:J12,
  `PERÍODO`=O9:T9, `SAFRA`=O9:Q9, `CÍVIL`=R9:T9, `SERRADOURADA`=B7:F7 (vestígio de outro cliente); além de
  `_xlnm._FilterDatabase` (autofiltros) e `Z_…wvu.FilterData` (modos de exibição personalizados), `_xleta.ISERR` (#NAME?).
* **Validações de dados**: listas `CATFAZ` na coluna de categoria da fazenda de todas as abas f*; listas `sistema`/`ANO`
  em fUnidade; `CATEGORIABI`, `PERÍODO` em CADASTROINICIAL; `SEXO` em fconsumodoacao!N; **decimal entre 0 e 10.000.000**
  (`allowBlank`) nas colunas numéricas de entrada (ex.: fCompras!E:G, fAbate!E/G/I, fVendaemPe!F:H, fNascimento!D/F, ftranfentrada!D:E, ftranssaida!I,
  fRebanhoMedio!B:C, fAreaPLANEJADO!B:C). Não há validação de data nem de obrigatoriedade. Validação do Excel é
  contornável por colar/copiar — não substitui validação no carregador.
* **Proteção**: todas as abas f*, `CADASTROINICIAL` e `dCategorias` protegidas (sem senha relevante para leitura).
* **Sem ListObjects, sem Power Query, sem conexões de dados**; 1 `externalLink` na amostra (inventário inicial).
* **VBA**: presente em 100% dos arquivos; hash do `vbaProject.bin` difere em todos (p-code recompilado) → não serve para
  identificar versão do template.

### 2.8 Desvio de template observado nos 230 arquivos

| Aba | Situação | Arquivos | Efeito no Pentaho (leitura posicional) |
|---|---|---|---|
| lista de abas | `fconsumodoação`/`fmudançacateg` (com acento) | 20 | nenhum (abas não lidas) — mas quebra quem ler por nome |
| `fUnidade` | coluna G (`ANO`) sem cabeçalho | 1 | nenhum |
| `fArea` | C1 = `SILAGEM` (2) ou `ILP` (1) em vez de `ÁREA_ILP` | 3 | lido como ÁREA_ILP (semântica diferente!) |
| `fAreaPLANEJADO` | C1 = `SILAGEM` | 2 | idem |
| `fDre` | linha 1 vazia em A:D | 1 | nada (linha 1 é sempre pulada) |
| `fDre` | **dado digitado na linha 1** (`INVESTIMENTOS EM RH`, `TAXAS E IMPOSTOS S/ VENDA`, `' '`) | 3 | o lançamento da linha 1 é **perdido silenciosamente** |
| `fDrePLANEJADO` | linha 1 vazia em A:D | 2 | nada |
| `fDrePLANEJADO` | cabeçalhos com espaço (`CENTRO DE CUSTO`, `DATA PAG`, …) | 1 | nada (posicional) — quebraria leitura por nome sem alias |
| `fComprasPLANEJADO` | R1 = `' '` (cabeçalho RETIRO apagado) | 1 | nenhum |
| `fRebanhoMedioPLANEJADO` | B1 = `3086.7` (dado no cabeçalho) | 1 | valor perdido |
| `fmudcategoria`, `fdesmame` | lixo no cabeçalho (`' a '`, `0`, `2025`) | 3 | nenhum (não lidas) |

As demais 15 abas lidas (`fCompras`, `fAbate`, `fVendaemPe`, `fMortes`, `fNascimento`, `ftranfentrada`, `ftranssaida`,
`fMovRebanho`, `fRebanhoMedio`, `fAbatePLANEJADO`, `fVendaemPePLANEJADO`, `fMortesPLANEJADO`, `fNascimentoPLANEJADO`,
`ftranfentradaPLANEJADO`, `ftranssaidaPLANEJADO`) e `dCategorias` têm cabeçalho **idêntico** nos 230 arquivos.
Conclusão: o template é estável, mas usuários editam a linha 1 — o adaptador deve casar cabeçalhos por nome normalizado
com aliases e, quando não reconhecer, cair para a posição do template **e emitir alerta**, nunca descartar a linha 1 sem checar.

### 2.9 Qualidade de dados (varredura de 77 arquivos = 1 a cada 3, aplicando os mesmos filtros dos KTRs)

| Aba | Linhas que o Pentaho grava | Datas como **texto** | Linhas com conteúdo **descartadas** pelo filtro | Categoria/conta sem mapeamento | Outros |
|---|---|---|---|---|---|
| fCompras | 430 | 18 (1 arq.) | 63 (1 arq., sem DATA) | 4 | 381 com dia ≠ 1 (data real do evento) |
| fAbate | 800 | 29 (3 arq.) | 1 | 0 | inclui o arquivo que derrubou o job em out/26 |
| fVendaemPe | 252 | 0 | **12 (4 arq.) — vendas sem CLIENTE** | 1 | |
| fMortes | 3.001 | 66 (4 arq.) | 0 | 0 | |
| fNascimento | 1.398 | 64 (2 arq.) | 0 | 0 | |
| ftranfentrada / ftranssaida | 370 / 351 | 0 / 9 | 0 | 6 / 0 | |
| fRebanhoMedio | 1.039 | — | — | — | 547 valores decimais (média), 1 número como texto |
| fArea | 1.061 (sem filtro) | — | — | — | 137 linhas **sem DATA** e 497 sem ÁREA_PASTO também gravadas |
| fDre | 58.921 | 607 (4 arq.; ex.: `02/072026`) | 1 | 85 sem centro BI; **286 `VERIFICAR`** | 242 lançamentos com DATA_PAG e **sem VALOR**; 4 negativos |
| fDrePLANEJADO | 16.832 | 570 (2 arq.) | 85 (6 arq.) | 8; 80 `VERIFICAR` | 4 negativos |
| fMortesPLANEJADO | 2.840 | 0 | 62 (4 arq.) | 57 | 1.882 QTD fracionárias (metas em %) |
| fNascimentoPLANEJADO | 388 | 0 | 2 | 53 | 215 QTD fracionárias |
| fAbatePLANEJADO | 516 | 1 | 21 (2 arq.) | 10 | 61 QTD fracionárias |
| ft*PLANEJADO | 61 / 112 | 0 | 0 | 0 | QTD fracionária é **truncada** (Kettle converte para Integer) |

* As datas digitadas como texto são quase todas `dd/mm/aaaa`; entram no `stg_*` misturadas com `aaaa/mm/dd`
  (por isso o Power BI tem `CASE` para os dois formatos e para `DDMMYYYY`/`YYYYMMDD`).
* As abas de lançamento são **cumulativas** (não se limitam ao período): fDre tem lançamentos de 2024 (1.347),
  2025 (25.951) e 2026 (31.016); metas vão até 2027. Só as abas derivadas por período (`fArea`, `fRebanhoMedio`,
  `fMovRebanho`) ficam restritas a 12 meses.
* Em `fMovRebanho` há 657 quantidades negativas no total da amostra (metades de saída de desmame/mudança de categoria) — esperado.
* Nada disso gera erro hoje: ou passa silenciosamente para o BI, ou é descartado silenciosamente, ou (célula
  inconvertível) derruba o job inteiro.

---

## 3. Orquestração atual

### 3.1 Job `Job Extract Data - Plan.kjb`

```
Start ──(incond.)──► Start (2) [MAIL "Start Service"]
   └─► fCadastro ──(sucesso OU falha: hop incondicional)──► fArea ──(incond.)──► fVendas
          └─(falha)► MAIL "Erro na Transform fCadastro"      └─(falha)► MAIL "Erro … fArea"
fVendas ─ok─► fMovimentacoes (fMovGado.ktr) ─ok─► fMetas (fMetaCompras.ktr) ─ok─► fCompras ─ok─► fNascimento
        ─ok─► fTransferencias (…\Metryx + Planilhas\Planilhas\fTransferências.ktr) ─ok─► dRls ─ok─► Success ─► MAIL "Execução Concluida"
cada entrada ─(falha)─► MAIL "Erro na Transform <nome>"  (e a cadeia PARA)
```

* Entradas TRANS com `specification_method=filename` (caminhos absolutos `C:\Users\TerraDev\Documents\Pentaho Archives\...`),
  `run_configuration=Pentaho local`, `wait_until_finished=Y`, log `Basic`, sem parâmetros/variáveis.
* `Start` sem agendamento interno (`schedulerType=0`).
* Mail: SMTP `smtp.gmail.com:465` SSL, autenticado com conta Gmail pessoal do desenvolvedor (usuário e senha gravados no
  `.kjb`, senha **[REDACTED]**); destinatário = a mesma conta. Sem anexo de log, sem detalhe do erro no corpo.
* `fCadastro → fArea` e `fArea → fVendas` são **incondicionais**: falha nessas duas não interrompe o job (só manda e-mail);
  a partir de `fVendas`, qualquer falha **interrompe** o restante.
* `Start (2) → fCadastro` é condicionado ao **sucesso do e-mail de início**: se o SMTP do Gmail falhar (há
  `MailConnectException` nos logs), nenhuma transformação roda.
* Variantes: `Job Extract Data - Plan_nTransf.kjb` (sem fTransferencias) e `Job Extract Data - Plan_transf.kjb`
  (só fTransferencias → dRls). Logs de tabela do Kettle (job-log/channel-log) não configurados (sem conexão).

### 3.2 Agendamento e sincronização

| Componente | Detalhe |
|---|---|
| Sincronização de arquivos | Tarefa do Windows **"Sync Drive"** → `C:\Pentaho\testebat.bat` → `rclone sync gdrive:/Relatórios "C:\Users\TerraDev\Meu Drive\Relatórios"` (log em `C:\Pentaho\rclone_log.txt`); gatilhos semanais seg–sex 06:40, 09:40, 13:10, 16:40. Não é o Google Drive for Desktop. |
| Execução do job | Pentaho Server CE 9.4 (Tomcat), iniciado no boot (tarefa "Start PDI"); agendador Quartz (`data\hsqldb\quartz.script`), usuário `Matheus`: `Sc 1` `0 0 7 ? * 2-6`, `Sc 2` `0 0 10 ? * 2-6`, `Sc 3` `0 30 13 ? * 2-6`, `Sc 4` `0 0 17 ? * 2-6` (TZ America/Cuiaba); `schedule 1` (07:00 seg–sáb) **pausado**. |
| Janela | sync às :40/:10 → job 20 min depois. Sem trava: se o rclone atrasar, o Pentaho lê arquivo pela metade/antigo. |
| Duração | execução completa ~6–10 min (ex.: 13/10 07:00:01 → 07:10:18). |
| Histórico (logs) | execuções iniciadas × e-mail de sucesso: jul/25 78×77, jan/26 88×88, mai/26 104×78, ago/26 85×53, set/26 75×46, out/26 (até 14/10) 18×7. Transformações que mais falharam (todas as execuções no servidor): fVendas 152, fTransferências 66, fCadastro 45, fArea 27, fNascimento 22, fMetaCompras 15, fMovGado 11. Erros de conversão de célula: `FATURAMENTO` (114), `QTD` (10), `CÓDIGO PROJETO` (2). |
| Caso real | 05–12/10/2026: todas as execuções pararam em `fVendas` por `Cannot convert field "FATURAMENTO" from cell on sheet 1, row 3, column 11` no arquivo `RELATÓRIO - 10 - ORVALHO DAS FLORES.xlsm` (outros arquivos recorrentes nos erros: `94 - MATER`, `156 - SÃO JOSÉ`, `17 - ARRENDAMENTOS (1)`). Corrigido em 12/10 ~10h ajustando separadores decimais (`fVendas.ktr.bak_antes_locale_2026-10-12`). |

### 3.3 Volumes (execução de 13/10/2026 07:00)

| Transformação / passo de leitura | Linhas lidas do Excel | Linhas gravadas | Tabela |
|---|---|---|---|
| fCadastro / fUnidade | 688 | 225 | stg_unidades |
| fArea / fArea | 3.034 | 3.034 | stg_area |
| fVendas / fVendaemPe | 693.770 | 1.467 | stg_fvendaempe |
| fVendas / fAbate | 693.770 | 2.474 | stg_fvendaabate |
| fMovGado / fRebanhoMedio | 8.506 | 2.722 | stg_frebanhomedio |
| fMovGado / fMovRebanho | 500.250 | 12.177 | stg_fmovgado |
| fMovGado / fCompras | 693.770 | 1.663 | stg_fcompras |
| fMovGado / fDre | 2.320.589 | 130.209 | stg_fdre |
| fMetaCompras / 8 abas PLANEJADO | ≈ 4,39 milhões | 57.221 (rebanho médio 3.842; área 1.532; nascimento 1.272; em pé 474; mortes 7.549; compras 666; abates 1.505; DRE 40.381) | stg_fmetas* |
| fCompras / fCompras (2ª vez) | 693.770 | 1.663 | stg_fcompras (recarregada) |
| fNascimento / fNascimento + fMortes | 230.000 + 693.770 | 4.015 + 6.891 | stg_fnascimento, stg_fmortes |
| fTransferências / 4 abas | 693.770 + 693.542 + 2×459.540 | 1.190 + 1.125 + 179 + 175 | stg_ftransf*, stg_fmeta*transf* |
| d_rls / Planilha1 | 297 | 297 | stg_rls |

≈ 13,2 milhões de linhas lidas para ≈ 227 mil gravadas (≈ 1,7% de aproveitamento), até 4 vezes por dia.

---

## 4. Transformações (na ordem do job)

### 4.0 Semântica Kettle comum (vale para todas)

1. **Excel Input** com `name = C:\Users\TerraDev\Meu Drive\Relatórios`, `filemask` vazio, `include_subfolders=N`,
   `file_required=N` → lê **todos os arquivos da pasta** (qualquer extensão; hoje só há .xlsm). Não há regex de nome,
   não há "Get file names". Motor `SAX_POI` (streaming xlsx); `d_rls` usa `POI`.
2. `header=Y` (pula a linha 1), `startrow=0`, `startcol=0`, `noempty=Y` (pula linhas totalmente vazias),
   `stoponempty=N` (exceto `fCadastro` e `d_rls`: `Y` = para no primeiro buraco), `limit=0`.
3. **Campos são posicionais**: o n-ésimo campo da lista = n-ésima coluna a partir de A. Nome do cabeçalho é ignorado.
   (Conferido: as listas de campos de todos os KTRs batem com a linha 1 da amostra; ver §2.8 para desvios reais.)
   Colunas finais `CÓDIGO_CLIENTE`/`PROJETO` **não são lidas** na maioria das abas (só em `fArea` e nas transferências,
   que as leem mas não gravam).
4. Células de **data lidas como String** viram `yyyy/MM/dd HH:mm:ss.SSS` (máscara padrão do Kettle; JVM em
   America/Cuiaba) e depois um `Replace in string` remove `" 00:00:00.000"` → texto `yyyy/MM/dd`. Quando a célula traz
   hora (ex.: `03:00`, `04:00`, efeito de fuso), o replace não pega — por isso `fTransferências` remove também
   `00:00:00.000`, `04:00:00.000`, `03:00:00.000` (sem o espaço). Textos digitados (ex.: `01/02/2026`) passam como estão.
5. **Números lidos como String** e convertidos no `Select values` dependem do locale (JVM pt_BR, `,` decimal);
   em 12/10/2026 foram explicitados `decimal=','` e `grouping='.'` no `fVendas` após a falha recorrente.
6. **Filter rows** só com destino "falso" (`send_true_to` vazio): linhas que satisfazem a condição são **descartadas**.
7. **Table output**: conexão `DATALAKE_PLAN` (PostgreSQL, host `localhost`, porta 5432, banco `DATALAKE_PLAN`,
   usuário `matheus`; em `fTransferências.ktr` usuário `postgres`; senha **[REDACTED]**), schema `DATABASE`,
   `truncate=Y` (TRUNCATE na inicialização do passo), `commit=1000`, `use_batch=Y`, `ignore_errors=N`,
   `specify_fields=Y` (mapeamento 1:1 stream→coluna, mesmo nome). Sem transação global: falha no meio deixa a tabela
   truncada/parcial.
8. **Nenhum passo tem error handling** (`step_error_handling` vazio); qualquer célula inconvertível aborta a
   transformação inteira (e, a partir de fVendas, o job).

### 4.1 `fCadastro.ktr` → `"DATABASE".stg_unidades`

* **Fonte**: pasta Relatórios, aba `fUnidade`, A:G, campos `PROJETO(String), PROPRIETÁRIO(String), FAZENDA(String),
  CÓDIGO PROJETO(Number), SISTEMA PRODUTIVO(String), RETIRO(String), ANO(String)`; `filefield=filename`
  (acrescenta o caminho completo do arquivo); `stoponempty=Y`.
* **Passos**:
  1. `df_Metas 8 2` (Select values): mantém PROJETO, PROPRIETÁRIO, FAZENDA, CÓDIGO PROJETO, SISTEMA PRODUTIVO, ANO,
     filename; **descarta RETIRO**; tipa tudo como String (PROJETO/PROPRIETÁRIO/FAZENDA/filename 200, CÓDIGO PROJETO 5,
     SISTEMA PRODUTIVO 50, ANO 10).
  2. `Filter rows`: mantém `PROJETO IS NOT NULL` (remove as linhas 3–4 que só têm listas K/L).
  3. `Concat fields`: `propfaz__ = PROPRIETÁRIO || FAZENDA` (sem separador).
  4. `Unique rows (HashSet)` por `propfaz__` (mantém a primeira ocorrência; na execução: 230 → 225, 5 duplicatas).
  5. `Insert fUnidade` (Table output) — TRUNCATE + INSERT.
* **Destino**: `stg_unidades(PROJETO, PROPRIETÁRIO, FAZENDA, "CÓDIGO PROJETO", "SISTEMA PRODUTIVO", ANO, filename, propfaz__)`.
* Observações: código do cliente como texto; ordem de leitura dos arquivos define qual duplicata "vence".

### 4.2 `fArea.ktr` → `stg_area`

* **Fonte**: aba `fArea`, A:I: `DATA(String), ÁREA_PASTO(Number), ÁREA_ILP(Number), ÁREA_TOTAL(String),
  PROPRIETÁRIO, FAZENDA, RETIRO, CÓDIGO_CLIENTE, PROJETO (String)`; `stoponempty=N`.
* **Passos**: `Block this step until steps finish` (aguarda a leitura terminar; sem efeito funcional) →
  `df_Metas 8 2 2` (Select values: DATA String 10; áreas Number; textos 200; CÓDIGO_CLIENTE String 5) →
  `Replace in string`: em DATA remove `" "` (todos os espaços) e depois `"00:00:00.000"` → `yyyy/MM/dd` →
  `Insert fUnidade 2` (TRUNCATE + INSERT).
* **Sem filtro**: grava as 12 linhas/mês de todos os arquivos mesmo com área vazia (3.034 linhas; ÁREA_TOTAL = 0).
* **Destino**: `stg_area("DATA", ÁREA_PASTO, ÁREA_ILP, ÁREA_TOTAL, PROPRIETÁRIO, FAZENDA, RETIRO, CÓDIGO_CLIENTE, PROJETO)`.
  É a única tabela de fato com código do cliente e projeto.

### 4.3 `fVendas.ktr` → `stg_fvendaabate` e `stg_fvendaempe`

Dois fluxos paralelos:

* **Abate**: Excel Input `fAbates` (aba `fAbate`, A:V, 22 campos; tipos de leitura: QTD/PESO_VIVO/PESO_ARROBA/VALOR_ARROBA/
  FATURAMENTO/PESO_MORTO/PESOVIVO_TOTAL/PESOMORTO_TOTAL/VALOR_KG/VALOR_CAB = Number, RENDIMENTO/DATA/DATA_ABREV/demais = String;
  decimal `,` / agrupamento `.`) → `Replace in string` (DATA: remove `" 00:00:00.000"`) → `df_Compras` (Select values:
  OPERAÇÃO 40, CLIENTE 100, CATEG_FAZENDA 100, DATA 25, ERA 40, DATA_ABREV 40, CATEGORIA_BI 100, SEXO 40, textos 100;
  numéricos Number com `,`/`.`) → `Rm Nulls 2` (descarta `DATA IS NULL`) → `insert fAbates` (TRUNCATE + INSERT em
  `STG_FVENDAABATE`).
* **Venda em pé**: Excel Input `fVendaEmPe` (aba `fVendaemPe`, A:R, 18 campos, **todos lidos como String**) →
  `Replace in string 2` (DATA) → `df_Compras 2` (QTD, PESO_VIVO, PESOVIVO_TOTAL, VALOR_ARROBA, VALOR_CAB, FATURAMENTO,
  VALOR_KG → Number com `,`/`.`; DOCUMENTO 100; CLIENTE sem tamanho) → `Rm Nulls 2 2` (**descarta `CLIENTE IS NULL`** —
  venda sem comprador preenchido some, mesmo com data e quantidade) → `insert fVendaEmPe` (`STG_FVENDAEMPE`).
* `DATA_ABREV` não é limpo → fica `yyyy/MM/dd 00:00:00.000`.
* Mudança de 12/10/2026 (vs `.bak_antes_locale`): adicionados `decimal_symbol=','`/`grouping_symbol='.'` em todos os
  campos do Excel Input e do Select values (antes vazios → dependia do default da JVM), após falhas de conversão de
  `FATURAMENTO`. A versão antiga em `Metryx + Planilhas` tinha ainda um terceiro fluxo desabilitado.

### 4.4 `fMovGado.ktr` (entrada "fMovimentacoes") → `stg_fmovgado`, `stg_fcompras`, `stg_frebanhomedio`, `stg_fdre`

Quatro fluxos independentes no mesmo KTR:

| Fluxo | Aba / colunas | Passos | Filtro (descarta) | Destino |
|---|---|---|---|---|
| Movimentação | `fMovRebanho` A:H: OPERAÇÃO, DATA(**Date**), QTD(String), CATEGORIA_BI, SEXO, PROPRIETÁRIO, FAZENDA, RETIRO | `Clear Spaces` (remove espaços de SEXO) → `df_movGado` (DATA → **String 40** ⇒ `yyyy/MM/dd 00:00:00.000`; QTD → **Integer**) | `QTD = 0` | `STG_FMOVGADO` |
| Compras | `fCompras` A:R (DATA como **Timestamp** máscara `dd/MM/yyyy`; QTD, PESO_VIVO, VALOR_CAB, VALOR TOTAL Number; TOTAL_PESO, VALO_KG, VALOR_ARROBA, PESO_ARROBA String) | `Clear Spaces 2` (SEXO) → `df_Compras` (DATA → **Date**; numéricos → Number; textos 40–100) | `DATA IS NULL` | `STG_FCOMPRAS` |
| Rebanho médio | `fRebanhoMedio` A:G: GRUPO_CATEGORIA, QTD_CAB(Number), QTD_UA(Number), DATA(String), PROPRIETÁRIO, FAZENDA, RETIRO | `Clear Spaces 3` (DATA: remove `" 00:00:00.000"`) → `df_RebanhoMedio` (DATA String 20) | `QTD_CAB IS NULL` | `STG_FREBANHOMEDIO` |
| DRE realizado | `fDre` A:L: CENTRO_DE_CUSTO, SUB_CENTRO, VALOR(Number), DATA_PAG(String), OPERAÇÃO, CENTRO_DE_CUSTO_BI, SUB_CENTRO_BI, FAZENDA, PROPRIETÁRIO, DESEMBOLSO, CUSTEIO, TIPO_CUSTEIO | `Clear Spaces 4` (DATA_PAG) → `df_Dre` (DATA_PAG String 25; OPERAÇÃO 50; DESEMBOLSO/CUSTEIO/TIPO_CUSTEIO 20) | `DATA_PAG IS NULL` | `STG_FDRE` |

Observações: `stg_fmovgado."DATA"` fica com sufixo de hora (o Power BI faz `Replace(" 00:00:00.000","")`);
`QTD` como Integer trunca decimais; lançamentos `VERIFICAR` (conta não mapeada) em fDre entram normalmente.

### 4.5 `fMetaCompras.ktr` (entrada "fMetas") → 8 tabelas `stg_fmetas*`

Oito fluxos idênticos em forma: `Excel Input (aba *PLANEJADO)` → `Clear Spaces n` (SEXO sem espaços; DATA e DATA_ABREV
sem `" 00:00:00.000"`) → `Strings cut n` (DATA/DATA_ABREV `substring(0,10)`, gravado num campo homônimo que o Kettle
renomeia para `DATA_1`/`DATA_ABREV_1`) → `df_Metas n` (Select values: renomeia `DATA_1→DATA`, `DATA_ABREV_1→DATA_ABREV`,
tipagem) → `Rm Nulls n` → `Insert` (TRUNCATE + INSERT).

| Aba | Campos lidos (A..) | Filtro (descarta) | Destino |
|---|---|---|---|
| `fComprasPLANEJADO` | 18 (A:R) como fCompras, DATA String | `DATA IS NULL` | `STG_FMETASCOMPRAS` |
| `fAbatePLANEJADO` | 22 (A:V) como fAbate | `QTD IS NULL` | `STG_FMETASABATES` |
| `fVendaemPePLANEJADO` | 18 (A:R), todos String | `QTD IS NULL` | `STG_FMETASEMPE` |
| `fMortesPLANEJADO` | 18 (A:R) | `QTD IS NULL` | `STG_FMETASMORTE` |
| `fNascimentoPLANEJADO` | 12 (A:L) | `QTD IS NULL` | `STG_FMETASNASCIMENTO` |
| `fRebanhoMedioPLANEJADO` | 7 (A:G) | `QTD_CAB IS NULL` | `STG_FMETASREBANHOMEDIO` |
| `fAreaPLANEJADO` | 7 (A:G) — sem CÓDIGO_CLIENTE/PROJETO | `ÁREA_PASTO IS NULL` | `STG_FMETASAREA` |
| `fDrePLANEJADO` | 12 (A:L); limpa também espaços de CUSTEIO/DESEMBOLSO/TIPO_CUSTEIO | `VALOR IS NULL` | `stg_fmetasdre` |

Note a **incoerência de filtros** entre realizado e metas (abate realizado filtra por DATA, meta por QTD; venda em pé
realizada por CLIENTE, meta por QTD; DRE realizado por DATA_PAG, meta por VALOR).

### 4.6 `fCompras.ktr` → `stg_fcompras` (recarga)

Idêntico ao fluxo "Compras" de `fMovGado.ktr` (aba `fCompras`, DATA Timestamp `dd/MM/yyyy` → Date, `Clear Spaces 2`
em SEXO, filtro `DATA IS NULL`, ORIGEM/CATEG_FAZENDA String 40). Como ambos truncam a mesma tabela, a segunda execução
apenas reescreve o mesmo conteúdo (~42 s desperdiçados). Redundância histórica.

### 4.7 `fNascimento.ktr` → `stg_fnascimento` e `stg_fmortes`

* **Nascimento**: aba `fNascimento` A:L (todos String) → `Param Data` (DATA sem `" 00:00:00.000"`) → `df_Nascimento`
  (QTD, PESO_NASC → Number; DATA String 25; SAFRA 10; DATA_ABREV 40 — **não limpo**) → `Rm Nulls` (`QTD IS NULL`) →
  `STG_FNASCIMENTO`.
* **Mortes**: aba `fMortes` A:R (QTD Number; resto String) → `Param Data2` (DATA e DATA_ABREV limpos) → `df_Mortes`
  (QTD, PESO_TOTAL Number; **PESO_VIVO permanece String 100**; CAUSA 500; LOCAL 100) → `Rm Nulls 2` (`QTD IS NULL`) →
  `STG_FMORTES`.

### 4.8 `fTransferências.ktr` (entrada "fTransferencias") → 4 tabelas

* Arquivo usado pelo job: `...\Metryx + Planilhas\Planilhas\fTransferências.ktr` (mod. 28/05/2026, conexão
  `DATALAKE_PLAN` com usuário `postgres`).
* 4 fluxos iguais (`ftranfentrada`, `ftranssaida`, `ftranfentradaPLANEJADO`, `ftranssaidaPLANEJADO`), 19 campos A:S
  (incluindo CÓDIGO_CLIENTE e PROJETO, **lidos mas não gravados**), todos como String; `TOTAL_PESO` e `VALOR TOTAL`
  (e `PESO_VIVO` em `ftranssaidaPLANEJADO`) lidos com formato `#,##0.00` (decimal `,`, milhar `.`).
* `Clear Spaces 2*`: SEXO sem espaços; DATA sem `00:00:00.000`, `04:00:00.000`, `03:00:00.000`; remove `.` de
  `VALOR TOTAL` e `TOTAL_PESO` (separador de milhar gerado pelo formato) → `df_Compras*` (DATA String 10;
  CATEGORIA_FAZENDA 50; QTD **Integer**; numéricos Number; DATA_ABREV 40) → filtro `DATA IS NULL` → Table output.
* Destinos: `STG_FTRANSFENTRADA`, `STG_FTRANSFSAIDA`, `STG_FMETASTRANSFENTRADA`, `STG_FMETATRANSFSAIDA` (sic: "METATRANSF").
* **Comparação com `TerraDesenvolvimento\fTransferencias.ktr`** (mod. 13/08/2026): mesma topologia, tabelas e filtros;
  diferenças: usuário de conexão `matheus` (vs `postgres`), **não** tem o formato `#,##0.00` nem a remoção do `.` em
  `VALOR TOTAL`/`TOTAL_PESO`. Ou seja, a versão "Metryx + Planilhas" é a evolução com correção de separador e é a que o
  job usa; a de TerraDesenvolvimento está desatualizada. Recomenda-se descartar uma delas (mesmo nome sem acento gera confusão).

### 4.9 `d_rls.ktr` (entrada "dRls") → `stg_rls`

Ver §6.

### 4.10 Fora do job (para referência)

* **`fDre.ktr`** (Metryx + Planilhas): lê a aba `fDre` (A:N, 14 campos incluindo CÓDIGO_CLIENTE e PROJETO) de **todos os
  arquivos de `G:\Meu Drive\Financeiro`** (planilhas financeiras de clientes Metryx), filtra `DATA_PAG IS NULL`, e grava
  com TRUNCATE em `"DATABASE".STG_DRE_PLN` de **outro banco** (`METRYX`, localhost). Ou seja, existe um fluxo de DRE em
  planilha também para clientes do Metryx (FINANCEIRO = EXCEL na planilha de RLS).
* **`fPlanejamento.ktr`**: cópia do `fMetaCompras.ktr` (sem transferências) lendo `G:\Meu Drive\Planejamento` e gravando
  em `METRYX."DATABASE".STG_{DREPREVISTO, AREAPREVISTO, COMPRASPREVISTO, MORTESPREVISTO, NASCIMENTOPREVISTO,
  REBANHOMEDIOPREVISTO, VENDAEMPEPREVISTO}_PLN` e `STG_ABATES_PREVISTO_PLAN` → metas em planilha para clientes Metryx
  (ORÇAMENTO = EXCEL).
* Cópias antigas em `Metryx + Planilhas\Planilhas` (`fCompras`, `fMetaCompras`, `fMovGado`, `fNascimento`, `fVendas`,
  jan–abr/2025): apontam para outro servidor/banco (`LKS_ZEUS_DATABASE`, host 192.168.100.33, banco `LKS_DATABASE_ZEUS`)
  e para a pasta `C:\Users\matheus.santos\Downloads\Planilhas Terra\unidades2`; `fMovGado` antigo não tinha os fluxos de
  rebanho médio/DRE. São histórico — não usar.
* Implicação para a plataforma: o adaptador de planilhas deve suportar **3 perfis de pasta** com o mesmo template
  (Relatórios = cliente 100% Excel; Planejamento = só metas; Financeiro = só DRE), escolhidos por cliente conforme as
  colunas `PRODUTIVO/ORÇAMENTO/FINANCEIRO (METRYX OU EXCEL)` da planilha de levantamento.

---

## 5. Esquema PostgreSQL resultante (DDL reconstruída)

Banco `DATALAKE_PLAN` em `localhost:5432`, schema `"DATABASE"` (maiúsculo, entre aspas). DDL **inferida** dos metadados
Kettle (tipos/tamanhos do último Select values) e confirmada parcialmente pelas consultas do Power BI (nomes como o
PG os dobra: o PG converte para minúsculas só letras ASCII de identificadores sem aspas — daí `operaÇÃo`,
`proprietÁrio`, `Área_pasto`, `cÓdigo_cliente`, `tÉcnico`; nomes com espaço, palavras reservadas e `"DATA"` ficaram
entre aspas e maiúsculos). Não há PK, FK, índices nem constraints conhecidos (TRUNCATE + INSERT puro).
Conferir com `\d "DATABASE".stg_*` antes de usar como verdade.

```sql
CREATE SCHEMA IF NOT EXISTS "DATABASE";

-- Dimensão unidade (fCadastro)
CREATE TABLE "DATABASE".stg_unidades (
  projeto               varchar(200),
  "proprietÁrio"        varchar(200),
  fazenda               varchar(200),
  "CÓDIGO PROJETO"      varchar(5),      -- código do cliente, como texto
  "SISTEMA PRODUTIVO"   varchar(50),
  ano                   varchar(10),     -- 'CÍVIL' | 'SAFRA'
  filename              varchar(200),    -- caminho completo do .xlsm
  propfaz__             text             -- proprietário||fazenda (chave de dedup)
);

-- Área mensal (fArea) — única com código/projeto
CREATE TABLE "DATABASE".stg_area (
  "DATA"            varchar(10),         -- 'yyyy/MM/dd'
  "Área_pasto"      double precision,
  "Área_ilp"        double precision,
  "Área_total"      double precision,
  "proprietÁrio"    varchar(200),
  fazenda           varchar(200),
  retiro            varchar(200),
  "cÓdigo_cliente"  varchar(5),
  projeto           varchar(200)
);

-- Vendas para abate (fVendas)  | metas: stg_fmetasabates (mesmas colunas; "DATA"/data_abrev varchar(20))
CREATE TABLE "DATABASE".stg_fvendaabate (
  "operaÇÃo" varchar(40), cliente varchar(100), categ_fazenda varchar(100),
  "DATA" varchar(25),                    -- 'yyyy/MM/dd'
  qtd double precision, era varchar(40), peso_vivo double precision, rendimento double precision,
  peso_arroba double precision, valor_arroba double precision, faturamento double precision,
  data_abrev varchar(40),                -- 'yyyy/MM/dd 00:00:00.000'
  categoria_bi varchar(100), sexo varchar(40), peso_morto double precision,
  pesovivo_total double precision, pesomorto_total double precision, valor_kg double precision,
  valor_cab double precision, "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- Vendas em pé (fVendas) | metas: stg_fmetasempe (idem)
CREATE TABLE "DATABASE".stg_fvendaempe (
  "operaÇÃo" varchar(40), cliente text, "DATA" varchar(25), documento varchar(100),
  categ_fazenda varchar(100), qtd double precision, peso_vivo double precision,
  pesovivo_total double precision, valor_arroba double precision, valor_cab double precision,
  faturamento double precision, data_abrev varchar(40), categoria_bi varchar(100), sexo varchar(40),
  valor_kg double precision, "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- Movimentação consolidada (fMovGado.ktr / aba fMovRebanho)
CREATE TABLE "DATABASE".stg_fmovgado (
  "operaÇÃo" varchar(40),
  "DATA" varchar(40),                    -- 'yyyy/MM/dd 00:00:00.000'
  qtd bigint,
  categoria_bi varchar(50), sexo varchar(40),
  "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- Compras (fMovGado.ktr e fCompras.ktr) | metas: stg_fmetascompras ("DATA"/data_abrev como texto)
CREATE TABLE "DATABASE".stg_fcompras (
  "operaÇÃo" varchar(40), "DATA" timestamp, origem varchar(100), categ_fazenda varchar(100),
  qtd double precision, peso_vivo double precision, total_peso double precision,
  valor_cab double precision, "VALOR TOTAL" double precision, valo_kg double precision,
  valor_arroba double precision, data_abrev varchar(40), categoria_bi varchar(50), sexo varchar(40),
  peso_arroba double precision, "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- Rebanho médio | metas: stg_fmetasrebanhomedio
CREATE TABLE "DATABASE".stg_frebanhomedio (
  grupo_categoria varchar(50), qtd_cab double precision, qtd_ua double precision,
  "DATA" varchar(20), "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- DRE realizado | metas: stg_fmetasdre (data_pag varchar(20), "operaÇÃo" varchar(10))
CREATE TABLE "DATABASE".stg_fdre (
  centro_de_custo varchar(100), sub_centro varchar(100), valor double precision,
  data_pag varchar(25),                  -- 'yyyy/MM/dd' (ou texto digitado)
  "operaÇÃo" varchar(50), centro_de_custo_bi varchar(100), sub_centro_bi varchar(100),
  fazenda varchar(100), "proprietÁrio" varchar(100),
  desembolso varchar(20), custeio varchar(20), tipo_custeio varchar(20)
);

-- Nascimentos | metas: stg_fmetasnascimento
CREATE TABLE "DATABASE".stg_fnascimento (
  "operaÇÃo" varchar(50), "DATA" varchar(25), categ_fazenda varchar(100), qtd double precision,
  safra varchar(10), peso_nasc double precision, data_abrev varchar(40), categoria_bi varchar(50),
  sexo varchar(40), "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- Mortes | metas: stg_fmetasmorte
CREATE TABLE "DATABASE".stg_fmortes (
  "operaÇÃo" varchar(100), "DATA" varchar(25), categ_fazenda varchar(100), carimbo_bez text,
  qtd double precision, causa varchar(500), "LOCAL" varchar(100) /* provável: reservado */,
  peso_vivo varchar(100) /* sic: texto */, safra varchar(20), data_abrev varchar(40),
  grupo_categoria varchar(40), era varchar(20), categoria_bi varchar(40), peso_total double precision,
  sexo varchar(40), "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- Transferências (4 tabelas com o mesmo layout):
--   stg_ftransfentrada, stg_ftransfsaida, stg_fmetastransfentrada, stg_fmetatransfsaida
CREATE TABLE "DATABASE".stg_ftransfentrada (
  "operaÇÃo" varchar(40), "DATA" varchar(10), categoria_fazenda varchar(50), qtd bigint,
  peso_vivo double precision, total_peso double precision, "VALOR TOTAL" double precision,
  data_abrev varchar(40), categoria_bi varchar(40), sexo varchar(40), peso_arroba double precision,
  valor_cab double precision, valo_kg double precision, valor_arroba double precision,
  "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- Metas de área (sem código/projeto)
CREATE TABLE "DATABASE".stg_fmetasarea (
  "DATA" varchar(20), "Área_pasto" double precision, "Área_ilp" double precision,
  "Área_total" double precision, "proprietÁrio" varchar(100), fazenda varchar(100), retiro varchar(100)
);

-- RLS
CREATE TABLE "DATABASE".stg_rls (
  base varchar(10), "CÓDIGO DO CLIENTE" varchar(10), "proprietÁrio" varchar(100), cliente varchar(100),
  "NOME DO PROJETO (FAZENDA)" varchar(100), "tÉcnico" varchar(100), email varchar(60),
  "EMAIL - GERENTE" varchar(60), "email- REGIONAL" varchar(60)
);
```

Lista completa de tabelas gravadas pelo job (23): `stg_unidades, stg_area, stg_fvendaabate, stg_fvendaempe,
stg_fmovgado, stg_fcompras, stg_frebanhomedio, stg_fdre, stg_fmetasarea, stg_fmetascompras, stg_fmetasdre,
stg_fmetasmorte, stg_fmetasnascimento, stg_fmetasrebanhomedio, stg_fmetasabates, stg_fmetasempe, stg_fnascimento,
stg_fmortes, stg_ftransfentrada, stg_ftransfsaida, stg_fmetastransfentrada, stg_fmetatransfsaida, stg_rls`.

**Como o Power BI consome** (útil para manter compatibilidade na transição): todas as consultas criam
`PROP_FAZ = unaccent(REPLACE(concat("proprietÁrio", fazenda), ' ', ''))` e relacionam fatos ↔ `fUnidades` ↔ `RLS`
por essa chave; datas textuais são saneadas no SQL/M (`SUBSTRING("DATA" FROM 1 FOR 10)`, `Replace(" 00:00:00.000","")`,
e nas metas um `CASE` que tenta `YYYYMMDD`/`DDMMYYYY` — sinal de datas digitadas como texto); `pecuarioVendaAbate`/
`pecuarioVendaEmPe` fazem join realizado × meta por (proprietário, fazenda, ano, mês) e diluem a meta mensal;
`Categorias` = `SELECT DISTINCT categoria_bi, sexo FROM stg_fmovgado`.

---

## 6. `d_rls`: como o mapeamento de RLS é construído

* **Fonte**: `C:\Users\TerraDev\Meu Drive\Levantamento Clientes para Power BI.xlsx`, aba `Planilha1`, cabeçalho na linha 1,
  `stoponempty=Y` (uma linha em branco no meio **corta** o resto silenciosamente), motor POI.
* **Campos (posicionais)**: `BASE, CÓDIGO DO CLIENTE (Number), PROPRIETÁRIO, CLIENTE, NOME DO PROJETO (FAZENDA), TÉCNICO,
  EMAIL, EMAIL - GERENTE, email- REGIONAL`. A planilha atual tem como cabeçalhos `BASE | CÓDIGO DO CLIENTE | PROPRIETÁRIO |
  PROJETO | FAZENDA | TÉCNICO | EMAIL | EMAIL - GERENTE | email- REGIONAL | PRODUTIVO (METRYX OU EXCEL) | ORÇAMENTO (METRYX OU EXCEL) |
  FINANCEIRO (METRYX OU EXCEL)` — os nomes mudaram (CLIENTE→PROJETO, NOME DO PROJETO (FAZENDA)→FAZENDA) e há 3 colunas
  novas, mas como a leitura é posicional o carregamento continua funcionando (as 3 novas são ignoradas).
* **Passos**: `df_Nascimento` (Select values; tudo String: BASE 10, CÓDIGO 10, nomes 100, e-mails 60) → `Insert dRls`
  (TRUNCATE + INSERT em `"DATABASE".stg_rls`). Sem filtro, sem trim, sem validação de e-mail.
* **Conteúdo (14/10/2026)**: 297 linhas; 11 bases regionais (GO, MT1, MT2, RO, TO, MS1–MS4, PR, PRG); 116 códigos de cliente;
  253 fazendas; 26 técnicos; e-mails **todos do domínio interno da consultoria** (técnico, gerente, regional) — o RLS é
  para a equipe interna, não para o cliente final; 54 e-mails têm **espaço no final** (risco de não casar com o login).
  Colunas novas: PRODUTIVO = METRYX (149) / EXCEL (143) / SIGA (3); ORÇAMENTO = EXCEL (194) / METRYX (89) / NÃO TEM (12);
  FINANCEIRO = EXCEL (171) / METRYX (123) / SIGA (1) — com grafias inconsistentes (`Metryx`/`METRYX`, `Excel`/`EXCEL`).
* **Cruzamento**: todos os 90 códigos presentes nos nomes de arquivo existem na planilha de RLS; 13 códigos marcados
  PRODUTIVO=EXCEL não têm arquivo na pasta Relatórios.
* **Uso no Power BI**: a consulta `RLS` acrescenta `PROP_FAZ = unaccent(replace(concat(proprietário, "NOME DO PROJETO (FAZENDA)"),' ',''))`,
  faz unpivot das 3 colunas de e-mail em (`tipo-email`, `e-mail`) e a regra é `RLS[e-mail] = USERNAME()`; relação
  `RLS.prop_faz → fUnidades.PROP_FAZ` (M:1, filtro bidirecional). Portanto o RLS depende de o texto
  proprietário+fazenda digitado na planilha de levantamento ser igual ao digitado em `fUnidade` de cada arquivo.
* **Para a nova plataforma**: substituir por tabelas `usuario`, `cliente`, `unidade`, `usuario_unidade(papel)` mantidas
  pela API, com políticas RLS do PostgreSQL usando `current_setting('app.user_id')`; a planilha de levantamento pode ser
  importada uma vez (seed) por `codigo_cliente` + nome de fazenda normalizado, com relatório de não-casados.

---

## 7. Tratamento de erros, logging, agendamento e fraquezas

### 7.1 O que existe
* E-mail por transformação em caso de falha e e-mail de sucesso no fim (assunto genérico; sem anexo de log).
* Log padrão do Pentaho Server (`tomcat\logs\pentaho.log`, rotação diária) com contagens I/O/R/W por passo.
* Agendamento Quartz no Pentaho Server + rclone agendado no Windows.

### 7.2 Fraquezas (com evidência)
1. **Full reload de 230 arquivos × 23 leituras de aba, até 4×/dia** (~13,2 mi linhas lidas para ~227 mil úteis; ~1,7 GB
   relidos por execução, cada arquivo é aberto 23 vezes). Sem detecção de mudança.
2. **Uma célula ruim derruba tudo**: sem error handling; `strict` de conversão; falhas recorrentes de `FATURAMENTO`,
   `QTD`, `CÓDIGO PROJETO`; 05–12/10/2026 com BI desatualizado por um único arquivo.
3. **TRUNCATE sem transação**: em falha, tabelas ficam vazias/parciais; `fCadastro`/`fArea` falhos não param o job;
   já uma falha do e-mail de início impede toda a carga.
4. **Leitura posicional**: colunas inseridas/movidas no template corrompem dados sem erro; dado digitado na linha 1 é perdido
   (3 arquivos em fDre, 1 em fRebanhoMedioPLANEJADO); `ÁREA_ILP` = "SILAGEM" em 3 arquivos.
5. **Sem regex de arquivo**: qualquer arquivo na pasta é lido (inclusive cópias `(1)`, `- OK`, `MARANGUAPE1`), gerando
   **fatos duplicados** (5 pares de duplicatas hoje); qualquer arquivo não-Excel/temporário quebraria o job.
6. **Identidade frágil**: fatos sem código do cliente; chave textual proprietário+fazenda (com `unaccent`/remoção de espaço
   no BI) — mudar a grafia do proprietário quebra vínculo com unidade e RLS; proprietário é dado pessoal usado como chave.
7. **Datas como texto** em formatos mistos (`yyyy/MM/dd`, `yyyy/MM/dd 00:00:00.000`, texto digitado, horas 03:00/04:00
   por fuso) e dependência de TZ/locale da JVM (America/Cuiaba, pt_BR) para números.
8. **Filtros inconsistentes** (venda em pé exige CLIENTE; abate exige DATA; metas exigem QTD); sem validação de
   categoria não mapeada (`CATEGORIA_BI` = `0`/vazio), conta `VERIFICAR`, datas fora de faixa, valores negativos.
9. **Dependência de valores em cache**: tudo que é fórmula (categoria BI, sexo, fMovRebanho, DRE classificado, identificação)
   vem do cache gravado pelo Excel; arquivo salvo por ferramenta que não recalcula ⇒ valores velhos/vazios.
10. **Histórico perdido ao trocar o PERÍODO** (abas derivadas por período re-datam e o full reload apaga meses anteriores).
11. **Caminhos absolutos hardcoded** (`C:\Users\TerraDev\...`, `G:\Meu Drive\...` em outros KTRs), dois arquivos
    `fTransferencias` divergentes, `fCompras` carregado duas vezes, credenciais SMTP pessoais no `.kjb`, usuários de banco
    diferentes (`matheus`/`postgres`), servidor Pentaho rodando de `Downloads\Pentaho - Copia`.
12. **Sem trava entre rclone e Pentaho** (janela fixa de 20 min); sem verificação de que o sync terminou.
13. **Observabilidade pobre**: sem tabela de execução, sem métricas por arquivo, e-mail sem causa; o usuário do BI não sabe
    que os dados estão parciais.
14. **RLS**: `stoponempty=Y`, e-mails com espaço, vínculo por texto livre, planilha manual sem versionamento.

---

## 8. Especificação do adaptador Python de planilhas

### 8.1 Visão geral

```
[Drive] --(rclone/Drive API, já existente)--> pasta local/bucket
   └─ Discovery: lista *.xlsm, normaliza NFC, aplica regex, extrai código/rótulo
   └─ Change detection: (size, mtime) → se mudou, SHA-256; compara com ingest.source_file
   └─ Para cada arquivo novo/alterado (paralelo, 4–8 workers):
        1. Fingerprint do template (abas + cabeçalhos) → template_version ou "unknown"
        2. Lê fUnidade/CADASTROINICIAL → identifica unidade (codigo_cliente, fazenda, retiro) + período + de-para de categorias
        3. Lê cada aba de fatos por NOME de cabeçalho (aliases), só as colunas de entrada + derivadas necessárias
        4. Normaliza/valida linha a linha → linhas ok + issues (erro/aviso)
        5. Grava em uma transação por arquivo: staging → merge nas tabelas canônicas (replace-by-file ou upsert)
        6. Registra ingest.run / ingest.file_version / ingest.issue
   └─ Ao final: refresh de views de compatibilidade (stg_*) e notificação (resumo por arquivo)
```

Bibliotecas: `openpyxl` (read_only=True, data_only=True para valores; uma segunda abertura `data_only=False` só quando
precisar distinguir fórmula × literal), `python-calamine` como alternativa mais rápida para leitura de valores
(benchmark recomendado: 7 MB/arquivo, abas de 10k linhas), `pydantic` para os modelos de linha, `psycopg 3` com `COPY`
para staging. Nunca executar VBA; nunca gravar no arquivo de origem.

### 8.2 Descoberta e detecção de mudança

* Entrada configurável por **perfil de pasta**: `relatorios` (template completo), `planejamento` (só abas PLANEJADO),
  `financeiro` (só fDre); cada perfil define as abas habilitadas.
* Nome: `unicodedata.normalize("NFC", nome)`; regex `^RELAT[ÓO]RIOS?\s*[-_]\s*(\d+)\s*[-_]\s*(.+?)\s*\.xlsm$`;
  ignorar `~$*`, `desktop.ini`, `*.tmp`, `*.gdoc`; nomes fora do padrão → issue `FILE_NAME_UNPARSED` (não processa).
* Tabela `ingest.source_file(id, path_nfc, codigo_from_name, label_from_name, size, mtime, sha256, drive_file_id NULL,
  first_seen, last_seen, status)`. Regra: se `(size, mtime)` iguais ao último processado com sucesso → pula;
  senão calcula SHA-256; se hash igual → só atualiza mtime; se diferente → processa e cria `ingest.file_version`.
  (Se migrar para Google Drive API: usar `md5Checksum`/`modifiedTime`/`id` do Drive e dispensar o rclone.)
* Estabilidade: só processar arquivo com `mtime` mais antigo que N segundos (ex.: 120 s) e que abra como zip válido
  (evita ler arquivo sendo escrito pelo sync); arquivo removido da pasta → marcar `status='removed'` e **inativar** os
  dados da unidade (soft-delete), não apagar imediatamente.
* Duplicatas: se dois arquivos resolvem para a mesma unidade (mesmo `codigo_cliente` + fazenda + retiro normalizados),
  processar só o de `mtime` mais recente e emitir `DUPLICATE_UNIT_FILE` (hoje: MARANGUAPE/MARANGUAPE1, ATTO SEMENTES./..,
  BHR AGROPECUÁRIA/– OK, MATER/(1), GUARÁ 1×AZS); permitir override manual (`ingest.file_override`: ignorar arquivo X).

### 8.3 Identidade da unidade e chaves

* `cliente.codigo` = `fUnidade!D2` (inteiro). Validar: igual ao código do nome do arquivo; se vazio, usar o do nome e
  emitir aviso `CODE_MISSING_IN_SHEET`; se divergente → erro `CODE_MISMATCH` (não carrega).
* `unidade` (fazenda/retiro) = `(cliente_id, fazenda_norm, retiro_norm)`, onde `_norm` = NFC, trim, colapsar espaços,
  upper, (opcional) sem acento. `retiro` vazio → `retiro = fazenda` (padrão observado). Guardar o texto original.
* `proprietario` vira **atributo** da unidade (dado pessoal; não usar como chave). Para compatibilidade com o Power BI
  atual, expor `prop_faz_legacy = unaccent(replace(proprietario||fazenda,' ',''))` numa view.
* Cada linha de fato recebe `unidade_id`, `source_file_version_id`, `source_sheet`, `source_row` (número da linha Excel)
  — rastreabilidade e chave técnica.

### 8.4 Mapeamento aba → entidade canônica

Convenção: ler as colunas de **entrada**; para colunas derivadas, preferir **recalcular** em Python (fórmulas simples e
conhecidas) e comparar com o cache (divergência > tolerância → aviso `CACHE_MISMATCH`). Só usar cache quando não for
possível recalcular (ex.: abas 100% fórmula).

| Aba (perfil) | Entidade/tabela canônica | Grão | Colunas de entrada usadas | Derivados (recalcular) | Chave de carga |
|---|---|---|---|---|---|
| `fUnidade` (+ `CADASTROINICIAL!B8`) | `core.unidade` (+ `unidade_periodo`) | 1/arquivo | PROJETO, PROPRIETÁRIO, FAZENDA, CÓDIGO PROJETO, SISTEMA PRODUTIVO, RETIRO, ANO, PERÍODO | tipo_periodo (SAFRA/CIVIL), data_inicio/fim do período | upsert `(cliente_id, fazenda_norm, retiro_norm)` |
| `CADASTROINICIAL!A11:F74` | `core.categoria_fazenda_map` | categoria local | CATEGORIA FAZENDA, CATEGORIA BI, SALDO INICIAL | sexo/grupo/era via `dCategorias` | replace por unidade |
| `dCategorias` | `core.categoria_bi` (seed global) | categoria | 4 colunas | — | upsert por nome; divergência do seed → aviso `TEMPLATE_DIM_DRIFT` |
| `ConsultaPlanoContas`, `BASEPLANODECONTAS` | `core.plano_contas_*` (seed global, alinhado ao Metryx) | conta | todas | — | upsert; divergência → aviso |
| `fArea` / `fAreaPLANEJADO` | `fato.area_mensal(cenario='realizado'/'planejado')` | unidade × mês | DATA, ÁREA_PASTO, ÁREA_ILP | area_total | **upsert `(unidade, cenario, competencia)`**; não apagar meses fora do período |
| `fRebanhoMedio` / `...PLANEJADO` | `fato.rebanho_medio_mensal` | unidade × grupo × mês | GRUPO_CATEGORIA, QTD_CAB, QTD_UA, DATA | — | upsert `(unidade, cenario, grupo, competencia)` |
| `fCompras` / `...PLANEJADO` | `fato.mov_animal(tipo='COMPRA')` | lançamento | DATA, ORIGEM, CATEG_FAZENDA, QTD, TOTAL_PESO, VALOR TOTAL (+PESO_VIVO, VALOR_CAB no planejado) | categoria_bi, sexo, peso_vivo=total_peso/qtd, valor_cab, valor_kg, valor_arroba=valor_kg×30, peso_arroba=peso_vivo/30, competencia | replace-by-(unidade, cenario, tipo) por versão de arquivo |
| `fAbate` / `...PLANEJADO` | `fato.mov_animal(tipo='ABATE')` | lançamento | CLIENTE, CATEG_FAZENDA, DATA, QTD, ERA, PESO_VIVO, RENDIMENTO, PESO_ARROBA, VALOR_ARROBA, FATURAMENTO | peso_morto=peso_arroba×15, pesovivo_total, pesomorto_total, valor_kg, valor_cab | idem |
| `fVendaemPe` / `...PLANEJADO` | `fato.mov_animal(tipo='VENDA_EM_PE')` | lançamento | CLIENTE, DATA, DOCUMENTO, CATEG_FAZENDA, QTD, PESO_VIVO, PESOVIVO_TOTAL, VALOR_ARROBA, VALOR_CAB, FATURAMENTO | valor_kg | idem |
| `fMortes` / `...PLANEJADO` | `fato.mov_animal(tipo='MORTE')` + `causa`, `local`, `carimbo_bez`, `safra` | lançamento | DATA, CATEG_FAZENDA, CARIMBO_BEZ, QTD, CAUSA, LOCAL, PESO_VIVO, SAFRA | grupo, era, peso_total | idem |
| `fNascimento` / `...PLANEJADO` | `fato.mov_animal(tipo='NASCIMENTO')` + `safra`, `peso_nasc` | lançamento | DATA, CATEG_FAZENDA, QTD, SAFRA, PESO_NASC | categoria_bi, sexo | idem |
| `ftranfentrada` / `ftranssaida` (+PLANEJADO) | `fato.mov_animal(tipo='TRANSF_ENTRADA'/'TRANSF_SAIDA')` | lançamento | DATA, CATEGORIA_FAZENDA, QTD, PESO_VIVO, TOTAL_PESO, VALOR TOTAL | peso_arroba, valor_cab, valo_kg, valor_arroba | idem |
| `fconsumodoacao` (novo) | `fato.mov_animal(tipo='CONSUMO_DOACAO')` | lançamento | DATA, CATEGORIA_FAZENDA, QTD, PESO_VIVO, VALOR_CAB, TIPO, DESTINO (pseudonimizar) | … | idem; aceitar alias `fconsumodoação` |
| `fmudcategoria`, `fdesmame` (novo) | `fato.mov_animal(tipo='MUD_CATEGORIA'/'DESMAME')` com `categoria_saida`/`categoria_entrada` | lançamento | DATA, CAT_SAÍDA, CAT_ENTRADA, QTD, PESO_VIVO, TOTAL_PESO | categorias BI | idem; alias `fmudançacateg` |
| `fMovRebanho` | `fato.estoque_mov_mensal` (**derivado**) | unidade × categoria × mês × operação | — (100% fórmula) | **recalcular a partir de `mov_animal` + saldo inicial**; ler o cache só para reconciliação (`MOVREBANHO_RECON_DIFF`) | materializar por SQL/view; não carregar do Excel em regime |
| `fDre` / `fDrePLANEJADO` | `fato.lancamento_financeiro(cenario)` | lançamento | CENTRO_DE_CUSTO, SUB_CENTRO, VALOR, DATA_PAG | operacao D/C, centro/subcentro BI, desembolso, custeio, tipo_custeio via `core.plano_contas_*` (mesma lógica dos VLOOKUPs) | replace-by-(unidade, cenario) por versão |

Modelo sugerido para `fato.mov_animal` (unifica 8 abas e encaixa no adaptador Metryx):
`(id bigserial, unidade_id, cenario ('realizado'|'planejado'), tipo, data date, competencia date (1º do mês), categoria_fazenda text,
categoria_bi_id, categoria_saida_bi_id NULL, qtd numeric(12,2), peso_vivo_kg numeric, peso_total_kg numeric, rendimento numeric,
peso_arroba numeric, valor_arroba numeric, valor_total numeric(14,2), valor_cab numeric, contraparte text (CLIENTE/ORIGEM/DESTINO),
documento text, era text, causa text, local text, safra text, origem_sistema ('planilha'|'metryx'), source_file_version_id,
source_sheet, source_row, created_at)`.

### 8.5 Regras de parsing/normalização

* **Datas**: aceitar `datetime`/`date` (descartar hora; se hora ∉ {00:00} → aviso `DATE_HAS_TIME`, e se ≥ 20:00 considerar
  arredondar para o dia seguinte, padrão de fuso −3/−4); número serial Excel (int/float entre 30000 e 60000) →
  `date(1899,12,30)+n`; texto: `dd/mm/aaaa`, `dd/mm/aa`, `aaaa-mm-dd`, `aaaa/mm/dd`, `ddmmaaaa`, `aaaammdd` (mesma
  heurística que o BI já usa) → aviso `DATE_FROM_TEXT`; `1900-01-01`/vazio = sem data. Faixa válida configurável
  (ex.: 2015-01-01 … hoje+3 anos para planejado; realizado ≤ hoje+31 dias) → fora: erro `DATE_OUT_OF_RANGE`.
  `competencia = date.replace(day=1)`. Nunca depender de TZ da máquina.
* **Números**: aceitar `int/float`; texto → remover espaços/`R$`/`%`, detectar formato pt-BR (`1.234,56`) vs en
  (`1234.56`) pela posição do último separador; `"-"`, `""` → nulo; erro de fórmula (`#DIV/0!`, `#N/A`, `#VALUE!`) → nulo +
  aviso `FORMULA_ERROR_CELL`. QTD: inteiro esperado (permitir decimal só em rebanho médio). Percentuais (`RENDIMENTO`):
  aceitar 0–1 ou 0–100 e normalizar para fração com aviso se ambíguo.
* **Textos**: NFC, trim, colapsar espaços, remover NBSP; `SEXO` → {MACHO, FÊMEA} (aceitar `FEMEA`, `F`, `M`);
  categorias comparadas por forma normalizada (upper sem acento), mantendo o texto original.
* **Categoria**: resolver `CATEG_FAZENDA` → categoria BI pelo `categoria_fazenda_map` da própria unidade (A11:B74);
  sem mapeamento → erro de linha `CATEGORY_UNMAPPED` (a linha vai para quarentena, o restante carrega).
* **Plano de contas**: resolver `(CENTRO_DE_CUSTO, SUB_CENTRO)` pelos seeds; sem mapeamento ou `VERIFICAR` →
  `ACCOUNT_UNMAPPED` (quarentena; não somar no DRE).
* **Constantes de linha**: ignorar colunas PROPRIETÁRIO/FAZENDA/RETIRO/CÓDIGO_CLIENTE/PROJETO das abas f* (usar a
  identidade do §8.3); se o cache divergir da identidade da unidade → aviso `ROW_IDENTITY_MISMATCH` (indica cópia de
  linhas entre planilhas).

### 8.6 Validações (novas)

| Código | Nível | Regra |
|---|---|---|
| `TEMPLATE_UNKNOWN` | erro de arquivo | abas obrigatórias ausentes ou cabeçalho irreconhecível após aliases |
| `HEADER_ROW_HAS_DATA` | aviso + recuperação | linha 1 parece dado (datas/números nos campos de cabeçalho) → tratar linha 1 como dado e usar cabeçalho do template |
| `CODE_MISMATCH` / `CODE_MISSING_IN_SHEET` | erro / aviso | §8.3 |
| `DUPLICATE_UNIT_FILE` | aviso | §8.2 |
| `REQUIRED_MISSING` | erro de linha | linha com conteúdo (qualquer coluna de entrada) sem DATA ou QTD (ou VALOR/DATA_PAG no DRE). Substitui os filtros silenciosos do Kettle; ex.: venda em pé sem CLIENTE vira **aviso**, não descarte |
| `DATE_OUT_OF_RANGE`, `DATE_FROM_TEXT`, `DATE_HAS_TIME` | erro / aviso / aviso | §8.5 |
| `NEGATIVE_VALUE` | erro de linha | QTD, pesos, valores < 0 (exceto colunas assinadas) |
| `INCONSISTENT_TOTALS` | aviso | `|peso_vivo×qtd − total_peso| / total_peso > 2%`; idem `valor_cab×qtd` vs total; `peso_arroba×15 ≈ peso_vivo×rendimento` |
| `OUTLIER` | aviso | peso_vivo fora de 20–900 kg/cab; valor/@ fora de faixa configurável; rendimento fora de 40–65% |
| `CATEGORY_UNMAPPED`, `ACCOUNT_UNMAPPED` | erro de linha | §8.5 |
| `PERIOD_CHANGED` | aviso | PERÍODO diferente da versão anterior → não apagar meses antigos (§8.7) |
| `MOVREBANHO_RECON_DIFF` | aviso | estoque recalculado ≠ cache de `fMovRebanho` por (categoria, mês, operação) |
| `STALE_CACHE` | aviso | colunas derivadas vazias com entradas preenchidas (arquivo salvo sem recálculo) |

Política: erro de **arquivo** → nada daquele arquivo é alterado (mantém a versão anterior, marca `stale`); erro de
**linha** → linha em `ingest.quarantine_row` (com valores brutos e motivo), demais linhas carregam. Um arquivo nunca
derruba o lote. Resumo por arquivo/consultor enviado por e-mail/painel (com link para as linhas em quarentena).

### 8.7 Idempotência e estratégia de gravação

* **Lançamentos (sem ID natural na planilha)**: para cada `(unidade_id, cenario, tipo_entidade)` presente no arquivo,
  em **uma transação**: `DELETE` das linhas da versão anterior desse arquivo/unidade + `INSERT` (via `COPY` para tabela
  temporária e `INSERT … SELECT`). Re-executar com o mesmo hash não faz nada; re-executar com outro hash substitui
  atomicamente. Chave técnica de deduplicação dentro da versão: `(source_file_version_id, source_sheet, source_row)`.
  Opcional para auditoria: `row_hash = sha1(campos de entrada normalizados)` para detectar alterações linha a linha entre
  versões (diff de versões no painel).
* **Mensais/período** (área, rebanho médio): `INSERT … ON CONFLICT (unidade_id, cenario, [grupo,] competencia) DO UPDATE`
  — meses ausentes da versão atual **permanecem** (preserva histórico quando o PERÍODO muda). Registrar
  `source_file_version_id` por linha para saber de onde veio cada mês.
* **Dimensões** (unidade, mapas de categoria/conta): upsert pela chave natural; mapas por unidade substituídos por versão.
* **Estoque/movimentação**: view materializada/tabela derivada recalculada por unidade após cada carga
  (`saldo_inicial` + Σ movimentos com sinal por tipo, por categoria × mês), substituindo `stg_fmovgado`.
* **Concorrência**: advisory lock por `unidade_id` (`pg_advisory_xact_lock`) para impedir duas cargas simultâneas da
  mesma unidade (ex.: duplicata de arquivo). Lock global do job para não sobrepor execuções agendadas.
* **RLS na carga**: o processo de ingestão usa um papel com `BYPASSRLS` (ou define `app.user_id` de serviço); as
  tabelas canônicas têm políticas por `unidade_id ∈ usuario_unidade(current_setting('app.user_id'))`.

### 8.8 Drift de template

* **Fingerprint**: `sha1(json(sorted(abas) + {aba: [cabeçalhos normalizados]}))` → tabela `ingest.template_version
  (fingerprint, first_seen, status: known|tolerated|unknown, notas)`. Hoje há **16 fingerprints** distintos nos 230
  arquivos (200 no principal, 15 no das abas acentuadas, demais com 1–2 arquivos — desvios do §2.8).
* **Leitura por nome** com dicionário de aliases por aba/campo (YAML versionado), ex.:
  `ÁREA_ILP: [ÁREA_ILP, AREA_ILP, ILP]` (e `SILAGEM` → **campo distinto** `area_silagem`, não ILP);
  `CENTRO_DE_CUSTO: [CENTRO_DE_CUSTO, CENTRO DE CUSTO]`; `DATA_PAG: [DATA_PAG, DATA PAG]`;
  `CATEGORIA_FAZENDA: [CATEGORIA_FAZENDA, CATEG_FAZENDA]`; abas: `fconsumodoacao: [fconsumodoacao, fconsumodoação]`,
  `fmudcategoria: [fmudcategoria, fmudançacateg]`. Normalização de cabeçalho: NFC, upper, sem acento, `[\s_-]+ → _`.
* **Fallback posicional**: se um cabeçalho obrigatório não casar, mas o fingerprint estiver a ≤ 2 diferenças do template
  conhecido e a coluna na posição esperada tiver o tipo esperado nas primeiras N linhas → usar posição + aviso
  `HEADER_POSITIONAL_FALLBACK`. Caso contrário → `TEMPLATE_UNKNOWN`.
* **Colunas extras** desconhecidas: ignorar com aviso (log do fingerprint); **colunas ausentes** opcionais → nulo.
* **Mudança de versão do template oficial**: manter `template_spec_vN.yaml` (abas, colunas, tipos, obrigatoriedade,
  fórmulas esperadas) e testes de contrato com um arquivo-modelo por versão; publicar uma célula/propriedade de versão
  no próprio template (ex.: nome definido `TEMPLATE_VERSION` ou `docProps/custom.xml`) para não depender só do fingerprint.

### 8.9 Desempenho

* Abrir cada arquivo **uma vez** e ler todas as abas necessárias (hoje: 23 aberturas por arquivo).
* Ler só até a última linha com dado de entrada (parar após K linhas consecutivas sem nenhuma coluna de entrada
  preenchida; as abas têm 1.000–10.000 linhas de template, a maioria vazias exceto colunas K/F).
* Paralelizar por arquivo (processos). Estimativa: ~5–7 s/arquivo com openpyxl read_only para todas as abas →
  230 arquivos ≈ 3–4 min com 8 workers no full load; incremental típico (≤ 30 arquivos alterados) < 1 min.

### 8.10 Compatibilidade na transição (Power BI atual)

* Criar views `"DATABASE".stg_*` (mesmos nomes/colunas/formatos de texto do §5) sobre as tabelas canônicas, incluindo
  as esquisitices necessárias (`"DATA"` como `to_char(data,'YYYY/MM/DD')`, `stg_fmovgado."DATA"` com sufixo
  `' 00:00:00.000'`, `"proprietÁrio"`), para desligar o Pentaho sem mexer no PBIX; depois migrar o BI/React para as
  tabelas canônicas.
* Teste de aceitação ("golden"): rodar o adaptador e o Pentaho sobre o mesmo snapshot da pasta e comparar, por tabela,
  contagens e somas por (prop_faz, mês, operação/categoria); diferenças esperadas e documentadas: duplicatas removidas,
  linhas antes descartadas silenciosamente (linha 1, CLIENTE vazio), meses preservados após troca de período.

### 8.11 Configuração exemplo (trecho)

```yaml
profiles:
  relatorios:
    path: "${DRIVE_ROOT}/Relatórios"
    filename_regex: '^RELAT[ÓO]RIOS?\s*[-_]\s*(?P<codigo>\d+)\s*[-_]\s*(?P<rotulo>.+?)\s*\.xlsm$'
    sheets: [fUnidade, CADASTROINICIAL, fArea, fDre, fCompras, fAbate, fVendaemPe, fMortes, fNascimento,
             fconsumodoacao, ftranfentrada, ftranssaida, fmudcategoria, fdesmame, fRebanhoMedio,
             fDrePLANEJADO, fAreaPLANEJADO, fComprasPLANEJADO, fAbatePLANEJADO, fVendaemPePLANEJADO,
             fMortesPLANEJADO, fNascimentoPLANEJADO, ftranfentradaPLANEJADO, ftranssaidaPLANEJADO, fRebanhoMedioPLANEJADO]
  planejamento: {path: "${DRIVE_ROOT}/Planejamento", sheets: ["*PLANEJADO"]}
  financeiro:   {path: "${DRIVE_ROOT}/Financeiro",   sheets: [fDre]}
sheets:
  fCompras:
    entity: mov_animal
    tipo: COMPRA
    cenario: realizado
    header_row: 1
    key_columns: [DATA, QTD]          # linha "tem conteúdo" se qualquer entrada preenchida; obrigatórias: DATA, QTD
    columns:
      DATA:          {type: date, required: true}
      ORIGEM:        {type: text, target: contraparte}
      CATEG_FAZENDA: {type: text, required: true, aliases: [CATEGORIA_FAZENDA], resolve: categoria_fazenda_map}
      QTD:           {type: int, required: true, min: 1}
      TOTAL_PESO:    {type: decimal, target: peso_total_kg, min: 0}
      VALOR TOTAL:   {type: decimal, target: valor_total, min: 0}
    derived:
      peso_vivo_kg: "peso_total_kg / qtd"
      valor_cab:    "valor_total / qtd"
      valor_kg:     "valor_cab / peso_vivo_kg"
      valor_arroba: "valor_kg * 30"
      peso_arroba:  "peso_vivo_kg / 30"
    cache_check: {PESO_VIVO: peso_vivo_kg, VALOR_CAB: valor_cab}   # compara com valor em cache (tolerância 0.5%)
```

### 8.12 Pseudocódigo do núcleo

```python
def ingest_file(path: Path, profile: Profile, db: Conn) -> FileResult:
    meta = discover(path)                                   # NFC, regex, size/mtime
    if not changed(meta, db): return FileResult.skipped(meta)
    meta.sha256 = sha256_file(path)
    if same_hash(meta, db): touch(meta, db); return FileResult.unchanged(meta)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True, keep_links=False)
    tpl = fingerprint(wb, profile)                          # TEMPLATE_UNKNOWN -> FileResult.failed
    unit = read_unit(wb["fUnidade"], wb["CADASTROINICIAL"], meta)  # código, fazenda, retiro, período, mapa categorias
    issues, batches = [], {}
    for sheet_spec in profile.sheets_for(tpl):
        rows, sheet_issues = read_sheet(wb, sheet_spec, unit)    # por nome+aliases, normaliza, valida, deriva
        batches[sheet_spec.entity_key] = rows; issues += sheet_issues
    with db.transaction():
        db.advisory_lock(unit.key)
        fv = register_file_version(meta, tpl, unit)
        for key, rows in batches.items():
            write(key, unit, fv, rows)                      # replace-by-version ou upsert mensal
        save_issues(fv, issues); recompute_stock(unit)
    return FileResult.loaded(meta, counts(batches), issues)
```

---

## 9. Pendências e pontos a confirmar

1. Conferir a DDL real (`\d+ "DATABASE".stg_*`) — tipos foram inferidos (ex.: se `"DATA"` de `stg_fcompras` é `timestamp`
   ou `date`; se `"LOCAL"` está entre aspas). Não houve acesso ao banco nesta análise.
2. Confirmar com o time se `fconsumodoacao`, `fmudcategoria`, `fdesmame` devem virar fatos próprios (hoje só existem
   agregados em `stg_fmovgado`).
3. Definir regra oficial para duplicatas de arquivo e para o arquivo `15 - GUARÁ 1` (código vazio; mesma unidade do 16).
4. Confirmar semântica de `ÁREA_ILP` vs `SILAGEM` nos 3 arquivos divergentes.
5. Decidir se o estoque (fMovRebanho) passa a ser 100% recalculado na plataforma (recomendado) ou continua vindo do cache.
6. Decidir onde rodará o adaptador (servidor atual com rclone vs. Google Drive API direto) e o destino das planilhas
   `Planejamento`/`Financeiro` de clientes Metryx (banco `METRYX`, hoje fora do job).
7. Planilha de RLS: normalizar valores `METRYX/EXCEL/SIGA` e trims de e-mail antes de importar como seed.
