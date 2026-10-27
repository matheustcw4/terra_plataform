-- Consultas para conferir os achados da validação de 14/10/2026 (docs/validacao/2026-10-14_cruzamento_bi.md).
-- Somente leitura. Rodar no Postgres do datalake do BI: Q2 no banco METRYX; Q3 no banco DATALAKE_PLAN.


-- =====================================================================================================================
-- Q2 (banco METRYX) — empate de bezerros mamando: mesma coorte, mesmo dia, dois saldos diferentes.
-- O SQL fSaldoGado do BI escolhe UM desses registros sem critério (row_number sem desempate).
-- =====================================================================================================================

-- Q2.1 Todos os casos (esperado hoje: 164 linhas em 17 fazendas)
SELECT b.idcustomer, b.farmname, b.retironame, b.owner, b.category, b.birth, b.harvest, b.date,
       count(*)                                          AS registros,
       min(b.amount)                                     AS menor,
       max(b.amount)                                     AS maior,
       string_agg(b.amount::text, ' | ' ORDER BY b.ctid) AS valores_na_ordem_gravada
FROM "DATABASE".stg_balanco_pecuario b
JOIN "DATABASE".stg_category c ON c.idcategory = b.uuidcategory
WHERE (c.categorygroup LIKE '%Bezerros Mamando%' OR c.categorygroup LIKE '%Bezerras Mamando%')
GROUP BY b.idcustomer, b.farmname, b.retironame, b.owner, b.category, b.birth, b.harvest, b.date
HAVING count(*) > 1 AND min(b.amount) <> max(b.amount)
ORDER BY b.farmname, b.category, b.date, b.birth;

-- Q2.2 Um caso concreto: '3) Fazenda Junqueira', '04) Bezerro M', 31/01/2024.
-- Cada coorte tem um registro 0 e um com o saldo no mesmo dia. Os dias seguintes mostram qual é o real:
-- 09/23: 202 em 31/01 -> 201 em 01/02 | 11/23: 113 -> 112 em 01/02 | 07/23: 116 -> 115 em 05/03.
SELECT b.birth, b.harvest, b.date, b.amount, b.owner, b.retironame, b.anosafra, b.ctid AS ordem_gravada
FROM "DATABASE".stg_balanco_pecuario b
WHERE b.farmname = '3) Fazenda Junqueira'
  AND b.category = '04) Bezerro M'
  AND b.date BETWEEN '2023-12-01' AND '2024-03-31'
ORDER BY b.birth, b.harvest, b.date, b.ctid;


-- =====================================================================================================================
-- Q3 (banco DATALAKE_PLAN) — de onde vêm os erros do BI de planilhas.
-- stg_fmovgado = aba fMovRebanho da planilha (100% fórmula, SUMIFS das abas de lançamento por CATEGORIA_BI e mês);
-- é dela que o BI calcula o ESTOQUE. As stg_f* detalhadas (vendas, compras…) alimentam os CARDS do BI.
-- =====================================================================================================================

-- A1 Saldo inicial invisível no estoque do BI.
-- Origem: planilha com PERÍODO = SAFRA 24/25 (CADASTROINICIAL!B8) -> o "Saldo Anterior" (CADASTROINICIAL coluna F)
-- é datado no mês anterior ao período (01/06/2024). O calendário do PBIX começa em 01/07/2024
-- (#date(2024,7,1) no Power Query), então essa linha não casa com nenhuma data e fica fora do estoque.
-- Esperado hoje: 5 fazendas, 11.362 cab.
SELECT u."CÓDIGO PROJETO" AS codigo, m.fazenda, left(m."DATA", 10) AS data_do_saldo, sum(m.qtd) AS saldo_inicial_cab
FROM "DATABASE".stg_fmovgado m
LEFT JOIN "DATABASE".stg_unidades u ON u."proprietÁrio" = m."proprietÁrio" AND u.fazenda = m.fazenda
WHERE m."operaÇÃo" = 'Saldo Anterior' AND m."DATA" < '2024/07/01'
GROUP BY 1, 2, 3
ORDER BY 4 DESC;

-- A3 Venda em pé que baixa o estoque mas não aparece nas vendas do BI.
-- Origem: linha da aba fVendaemPe sem CLIENTE. A fMovRebanho (Excel) soma a linha; o Pentaho (fVendas.ktr, passo
-- "Filter rows") descarta linha sem cliente, então ela não chega a stg_fvendaempe nem aos cards de venda.
-- diferenca > 0: está no estoque e falta nas vendas (A3); < 0: está nas vendas e não no estoque (categoria sem BI).
WITH mov AS (SELECT "proprietÁrio" AS p, fazenda, left("DATA", 7) AS mes, sum(qtd) AS cab
             FROM "DATABASE".stg_fmovgado WHERE "operaÇÃo" = 'EMPÉ' GROUP BY 1, 2, 3),
     det AS (SELECT "proprietÁrio" AS p, fazenda, left(data_abrev, 7) AS mes, sum(qtd) AS cab
             FROM "DATABASE".stg_fvendaempe GROUP BY 1, 2, 3)
SELECT u."CÓDIGO PROJETO" AS codigo, coalesce(mov.fazenda, det.fazenda) AS fazenda, coalesce(mov.mes, det.mes) AS mes,
       coalesce(mov.cab, 0) AS cab_no_estoque, coalesce(det.cab, 0) AS cab_nas_vendas,
       coalesce(mov.cab, 0) - coalesce(det.cab, 0) AS diferenca
FROM mov
JOIN det USING (p, fazenda, mes)
LEFT JOIN "DATABASE".stg_unidades u ON u."proprietÁrio" = mov.p AND u.fazenda = mov.fazenda
WHERE coalesce(mov.cab, 0) <> coalesce(det.cab, 0)
UNION ALL
SELECT u."CÓDIGO PROJETO", mov.fazenda, mov.mes, mov.cab, 0, mov.cab        -- mês sem nenhuma venda detalhada
FROM mov
LEFT JOIN det USING (p, fazenda, mes)
LEFT JOIN "DATABASE".stg_unidades u ON u."proprietÁrio" = mov.p AND u.fazenda = mov.fazenda
WHERE det.cab IS NULL
ORDER BY diferenca DESC;

-- A4 Animais que "somem" em desmame / mudança de categoria.
-- Origem: abas fdesmame / fmudcategoria com a categoria de ENTRADA (ou de saída) da fazenda sem correspondência em
-- CADASTROINICIAL!A11:B74 -> CATEGORIA_BI vazia -> a fMovRebanho só soma o lado mapeado. Deveria fechar em 0.
SELECT u."CÓDIGO PROJETO" AS codigo, m.fazenda, m."operaÇÃo" AS operacao, left(m."DATA", 7) AS mes,
       sum(m.qtd) FILTER (WHERE m.qtd < 0) AS saidas,
       sum(m.qtd) FILTER (WHERE m.qtd > 0) AS entradas,
       sum(m.qtd)                          AS cab_que_somem
FROM "DATABASE".stg_fmovgado m
LEFT JOIN "DATABASE".stg_unidades u ON u."proprietÁrio" = m."proprietÁrio" AND u.fazenda = m.fazenda
WHERE m."operaÇÃo" IN ('DESMAME', 'Mud. de Categoria')
GROUP BY 1, 2, 3, 4
HAVING sum(m.qtd) <> 0
ORDER BY 7;

-- A5 Lançamentos fora do estoque do BI por categoria da fazenda não mapeada (sem CATEGORIA_BI válida).
-- Origem: CATEG_FAZENDA digitada na aba de lançamento sem linha correspondente em CADASTROINICIAL!A11:B74.
-- Ex.: 254 · FAZENDA MARCA R, "GARROTES NELORE 12 A 24": 1.854 cab de transferência de saída que não saem do estoque.
WITH lanc AS (
    SELECT 'COMPRA' AS op, "proprietÁrio" AS p, fazenda, categ_fazenda AS categoria_da_fazenda, categoria_bi, data_abrev, qtd FROM "DATABASE".stg_fcompras
    UNION ALL SELECT 'ABATE', "proprietÁrio", fazenda, categ_fazenda, categoria_bi, data_abrev, qtd FROM "DATABASE".stg_fvendaabate
    UNION ALL SELECT 'EMPÉ', "proprietÁrio", fazenda, categ_fazenda, categoria_bi, data_abrev, qtd FROM "DATABASE".stg_fvendaempe
    UNION ALL SELECT 'MORTE', "proprietÁrio", fazenda, categ_fazenda, categoria_bi, data_abrev, qtd FROM "DATABASE".stg_fmortes
    UNION ALL SELECT 'NASCIMENTO', "proprietÁrio", fazenda, categ_fazenda, categoria_bi, data_abrev, qtd FROM "DATABASE".stg_fnascimento
    UNION ALL SELECT 'Transf. Entrada', "proprietÁrio", fazenda, categoria_fazenda, categoria_bi, data_abrev, qtd FROM "DATABASE".stg_ftransfentrada
    UNION ALL SELECT 'Transf. Saida', "proprietÁrio", fazenda, categoria_fazenda, categoria_bi, data_abrev, qtd FROM "DATABASE".stg_ftransfsaida
)
SELECT u."CÓDIGO PROJETO" AS codigo, l.fazenda, l.op AS operacao, l.categoria_da_fazenda, l.categoria_bi,
       left(l.data_abrev, 7) AS mes, sum(l.qtd) AS cab_fora_do_estoque
FROM lanc l
LEFT JOIN "DATABASE".stg_unidades u ON u."proprietÁrio" = l.p AND u.fazenda = l.fazenda
WHERE coalesce(l.categoria_bi, '') NOT IN ('BEZERRO', 'MACHOS 8-12', 'MACHOS 13-24', 'MACHOS 25-36', 'MACHOS + 36',
      'TOUROS', 'TOUROS DESCARTES', 'SINUELO', 'BEZERRA', 'NOVILHAS 8-12', 'NOVILHAS 13-24', 'NOVILHAS 25-36',
      'MATRIZES', 'VACA DESCARTE', 'VACA LEITEIRA')
GROUP BY 1, 2, 3, 4, 5, 6
HAVING sum(l.qtd) > 0
ORDER BY 7 DESC;
