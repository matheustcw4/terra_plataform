# Layout das páginas do BI (CICLO COMPLETO - BOLETIM MENSAL (6).pbix)

Gerado por `python -m validacao.layout_do_bi`. Posições em px de cada página (a maioria 1920×1080), absolutas. Formas e imagens sem texto ficam de fora.

## MENU 01 (1280×720)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 34 | 528 | 210 | 210 | image |  | TERRA_HORIZONTAL_BR_AZUL918917902708366.png |
| 253 | 361 | 556 | 86 | slicer |  | PROPRIETÁRIO |
| 348 | 361 | 556 | 87 | slicer |  | FAZENDA |
| 427 | 488 | 316 | 44 | textbox |  | SELECIONE A FORMA DE VISUALIZAÇÃO: |
| 501 | 496 | 101 | 39 | actionButton |  | Safra Habilitado |
| 501 | 497 | 101 | 39 | actionButton | sim | Safra Desabilitado |
| 501 | 681 | 100 | 39 | actionButton |  | Cívil Desabilitado |
| 501 | 682 | 101 | 41 | actionButton | sim | Cívil Habilitado |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer |  | Safra |
| 558 | 672 | 246 | 74 | slicer |  | Mês |
| 641 | 769 | 235 | 66 | actionButton |  |  |

## Capa (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 151 | 287 | 296 | 192 | card |  | Min(dCalendar.Safra Abreviada) |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 258 | 890 | 300 | 159 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 663 | 743 | 1177 | 140 | card |  | Analytics Measures.Selected Farm |
| 713 | 0 | 175 | 40 | card |  | Analytics Measures.IN - Data Análise |
| 753 | 0 | 322 | 58 | card |  | Analytics Measures.IN - Periodo Capa |
| 899 | 37 | 256 | 92 | slicer | sim | Ano |
| 936 | 1 | 241 | 70 | image |  | TERRA_HORIZONTAL_BR_AZUL957023210427425.png |
| 941 | 66 | 402 | 58 | card |  | Analytics Measures.IN - Site Terra |
| 943 | 542 | 402 | 58 | card |  | Analytics Measures.IN - Periodo Envio |

## Duplicata de PG1 (1280×1800)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 0 | 99 | 118 | actionButton |  |  |
| 0 | 279 | 727 | 118 | card |  | Analytics Measures.Selected Farm |
| 136 | 2 | 323 | 208 | gauge |  | DESEMBOLSO CABEÇA MÊS |
| 136 | 327 | 323 | 208 | gauge |  | CUSTEIO CABEÇA MÊS |
| 136 | 653 | 323 | 208 | gauge |  | Valor de Venda @ |
| 136 | 977 | 320 | 208 | cardVisual |  | DESEMBOLSO |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 258 | 890 | 300 | 159 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 348 | 2 | 1294 | 304 | lineClusteredColumnComboChart |  | FLUXO DE CAIXA MENSAL |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 655 | 2 | 643 | 327 | clusteredColumnChart |  | REALIZADO X PLANEJADO - RECEITAS |
| 655 | 653 | 643 | 327 | clusteredColumnChart |  | REALIZADO X PLANEJADO - DESEMBOLSO |
| 899 | 37 | 256 | 92 | slicer | sim | Ano |
| 985 | 2 | 1294 | 332 | clusteredColumnChart |  | RELAÇÃO DESEMBOLSO TOTAL |
| 1319 | 2 | 1292 | 478 | clusteredBarChart |  | Realizado x Planejado - Desembolso/cab/mês |

## Previsto x Realizado (1920×1600)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 24 | 335 | 1012 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 144 | 32 | 286 | 118 | image |  | 4d7120e0-00b7-48b1-b9e9-bdef9f45245519933911327.png |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 268 | 4 | 61 | 50 | actionButton |  |  |
| 282 | 483 | 726 | 41 | card |  | Analytics Measures.RL Mensal |
| 282 | 1207 | 696 | 41 | card |  | Analytics Measures.RL Acumulado |
| 323 | 4 | 1909 | 1268 | pivotTable |  | planejadoXRealizado.classificacao, planejadoXRealizado.centro_de_custo_bi, REALIZADO, PLANEJADO, % VARIAÇÃO, REALIZADO ACUMULADO, PLANEJADO ACUMULADO, % VARIAÇÃO ACUMULADA |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 437 | 294 | 257 | 75 | slicer | sim | Safra |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |

## Financeiro (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 510 | 900 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 130 | 33 | 286 | 130 | image |  | 4d7120e0-00b7-48b1-b9e9-bdef9f45245519933911327.png |
| 134 | 1372 | 297 | 165 | cardVisual |  | DESEMBOLSO |
| 138 | 335 | 321 | 165 | gauge |  | DESEMBOLSO CABEÇA MÊS |
| 138 | 679 | 321 | 165 | gauge |  | CUSTEIO CABEÇA MÊS |
| 138 | 1026 | 321 | 165 | gauge |  | Valor de Venda @ |
| 239 | 0 | 62 | 51 | actionButton |  |  |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 258 | 890 | 300 | 159 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 304 | 5 | 1265 | 511 | clusteredColumnChart |  | RELAÇÃO DESEMBOLSO TOTAL |
| 304 | 1274 | 643 | 252 | clusteredColumnChart |  | Realizado x Planejado - Desembolso/cab/mês |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 502 | 515 | 727 | 118 | card |  | Analytics Measures.Selected Farm |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 562 | 1274 | 643 | 252 | clusteredColumnChart |  | REALIZADO X PLANEJADO - DESEMBOLSO |
| 819 | 5 | 1265 | 254 | lineClusteredColumnComboChart |  | FLUXO DE CAIXA MENSAL |
| 819 | 1274 | 643 | 254 | clusteredColumnChart |  | REALIZADO X PLANEJADO - RECEITAS |
| 899 | 37 | 256 | 92 | slicer | sim | Ano |

## Movimentação do Gado (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 510 | 900 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 108 | 345 | 335 | 70 | cardVisual |  | Analytics Measures.IN - Rebanho Médio |
| 111 | 721 | 315 | 78 | cardVisual |  | Analytics Measures.IN - Nascimentos (Label - 2) |
| 112 | 1457 | 352 | 70 | cardVisual |  | Analytics Measures.IN - COMPRA X VENDA |
| 115 | 1098 | 315 | 78 | cardVisual |  | Analytics Measures.IN - Mortes |
| 126 | 711 | 42 | 54 | image |  | sum_icon7677372755924409.png |
| 128 | 324 | 80 | 59 | image |  | bezerro_icon36570149245780714.png |
| 130 | 1088 | 42 | 54 | image |  | sum_icon7677372755924409.png |
| 186 | 542 | 132 | 32 | card |  | Analytics Measures.Mean Month |
| 187 | 1454 | 103 | 35 | card |  | Analytics Measures.IN - Compras (Label 2 ) |
| 189 | 1672 | 132 | 35 | card |  | Sum(pecuarioCompras.qtd) |
| 190 | 325 | 210 | 28 | card |  | Analytics Measures.IN - Rebanho Médio Cab |
| 200 | 1292 | 138 | 30 | card |  | Analytics Measures.Dead Quantity |
| 202 | 1060 | 118 | 30 | card |  | Analytics Measures.IN - Mortes (2) |
| 205 | 702 | 138 | 30 | card |  | Analytics Measures.IN - Nascimentos (Label) |
| 205 | 915 | 138 | 30 | card |  | Analytics Measures.Birth Quantity |
| 217 | 542 | 132 | 32 | card |  | Analytics Measures.UA Median Month |
| 218 | 324 | 194 | 30 | card |  | Analytics Measures.IN - Rebanho Médio UA |
| 221 | 1454 | 194 | 35 | card |  | Analytics Measures.IN - % Meta |
| 223 | 1673 | 132 | 36 | card |  | Analytics Measures.% Purchased Quantity |
| 239 | 0 | 61 | 50 | actionButton |  |  |
| 245 | 1072 | 210 | 30 | card |  | Analytics Measures.IN - % Meta |
| 245 | 1295 | 138 | 30 | card |  | Analytics Measures.% Death x Death Forecast |
| 247 | 323 | 137 | 32 | card |  | Analytics Measures.IN - Lotação Cab |
| 248 | 540 | 132 | 32 | card |  | Analytics Measures.Mean Month Ha |
| 252 | 918 | 138 | 30 | card |  | Analytics Measures.% Birth x Forecast |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 255 | 695 | 210 | 30 | card |  | Analytics Measures.IN - % Meta |
| 257 | 1454 | 81 | 36 | card |  | Analytics Measures.IN - Vendas (Label) |
| 258 | 1670 | 132 | 36 | card |  | Analytics Measures.Amount Saled |
| 280 | 327 | 120 | 31 | card |  | Analytics Measures.IN - Lotação UA |
| 280 | 540 | 132 | 30 | card |  | Analytics Measures.UA Median Ha |
| 290 | 1085 | 155 | 30 | card |  | Analytics Measures.IN - Indice de Mortalidade |
| 291 | 1295 | 131 | 31 | card |  | Analytics Measures.% mORTALITY ( MEAN MONTH) |
| 291 | 1454 | 193 | 36 | card |  | Analytics Measures.IN - % Meta |
| 292 | 1668 | 131 | 34 | card |  | Analytics Measures.% Amount Saled |
| 340 | 0 | 1918 | 365 | clusteredColumnChart |  | ESTOQUE FINAL MENSAL |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 507 | 767 | 257 | 89 | slicer | sim | Mês |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 712 | 0 | 1918 | 365 | clusteredColumnChart |  | ESTOQUE POR CATEGORIA |
| 712 | 1615 | 302 | 142 | cardVisual |  | REBANHO FINAL |

## Venda Abate (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 510 | 900 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 93 | 1472 | 208 | 73 | cardVisual |  | Analytics Measures.IN - Geral |
| 98 | 962 | 208 | 72 | cardVisual |  | Analytics Measures.IN - Macho |
| 101 | 419 | 210 | 65 | cardVisual |  |   |
| 112 | 1460 | 42 | 54 | image |  | sum_icon7677372755924409.png |
| 121 | 402 | 67 | 49 | image |  | female_icon23078485966194817.png |
| 122 | 938 | 44 | 46 | image |  | male_icon6869846729085312.png |
| 130 | 33 | 286 | 130 | image |  | 4d7120e0-00b7-48b1-b9e9-bdef9f45245519933911327.png |
| 166 | 603 | 136 | 30 | card |  | Analytics Measures.IN - Realizado |
| 166 | 742 | 136 | 30 | card |  | Analytics Measures.IN - Planejado |
| 166 | 1109 | 136 | 30 | card |  | Analytics Measures.IN - Realizado |
| 166 | 1253 | 135 | 30 | card |  | Analytics Measures.IN - Planejado |
| 167 | 1625 | 135 | 30 | card |  | Analytics Measures.IN - Realizado |
| 168 | 1767 | 137 | 30 | card |  | Analytics Measures.IN - Planejado |
| 187 | 1612 | 147 | 33 | card |  | Sum(pecuarioVendaAbate.qtd) |
| 187 | 1758 | 147 | 33 | card |  | Sum(fMetasAbate.qtd) |
| 189 | 1249 | 148 | 32 | card |  | Sum(fMetasAbate.qtd) |
| 190 | 1102 | 148 | 32 | card |  | Sum(pecuarioVendaAbate.qtd) |
| 191 | 592 | 147 | 33 | card |  | Sum(pecuarioVendaAbate.qtd) |
| 191 | 905 | 188 | 30 | card |  | Analytics Measures.IN - Cabeças Vendidas |
| 191 | 1417 | 188 | 30 | card |  | Analytics Measures.IN - Cabeças Vendidas |
| 192 | 734 | 148 | 32 | card |  | Sum(fMetasAbate.qtd) |
| 193 | 394 | 188 | 29 | card |  | Analytics Measures.IN - Cabeças Vendidas |
| 215 | 1102 | 147 | 33 | card |  | Analytics Measures.IN - AVG Live Weight |
| 215 | 1244 | 147 | 32 | card |  | Analytics Measures.IN - AVG Live Weight (Forecast) |
| 215 | 1614 | 147 | 33 | card |  | Analytics Measures.IN - AVG Live Weight |
| 215 | 1756 | 147 | 32 | card |  | Analytics Measures.IN - AVG Live Weight (Forecast) |
| 217 | 592 | 147 | 33 | card |  | Analytics Measures.IN - AVG Live Weight |
| 217 | 734 | 147 | 32 | card |  | Analytics Measures.IN - AVG Live Weight (Forecast) |
| 217 | 900 | 188 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 217 | 1412 | 188 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 219 | 390 | 188 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 239 | 0 | 61 | 50 | actionButton |  |  |
| 242 | 900 | 234 | 38 | card |  | Analytics Measures.IN - Rendimento de Carcaça |
| 242 | 1412 | 234 | 38 | card |  | Analytics Measures.IN - Rendimento de Carcaça |
| 244 | 390 | 234 | 38 | card |  | Analytics Measures.IN - Rendimento de Carcaça |
| 245 | 1104 | 148 | 31 | card |  | Analytics Measures.Rendimento Carcaça |
| 245 | 1244 | 148 | 31 | card |  | Analytics Measures.IN - Rendimento Carcaça (Forecast) |
| 245 | 1616 | 148 | 31 | card |  | Analytics Measures.Rendimento Carcaça |
| 245 | 1756 | 148 | 31 | card |  | Analytics Measures.IN - Rendimento Carcaça (Forecast) |
| 247 | 734 | 148 | 31 | card |  | Analytics Measures.IN - Rendimento Carcaça (Forecast) |
| 248 | 594 | 148 | 31 | card |  | Analytics Measures.Rendimento Carcaça |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 273 | 1102 | 147 | 32 | card |  | Analytics Measures.AVG Price @ Dead Sale |
| 273 | 1244 | 147 | 31 | card |  | Analytics Measures.AVG Price @ Dead Sale - Forecast |
| 273 | 1614 | 147 | 32 | card |  | Analytics Measures.AVG Price @ Dead Sale |
| 273 | 1756 | 147 | 31 | card |  | Analytics Measures.AVG Price @ Dead Sale - Forecast |
| 274 | 898 | 220 | 30 | card |  | Analytics Measures.IN - Valor da @ |
| 274 | 1410 | 220 | 30 | card |  | Analytics Measures.IN - Valor da @ |
| 275 | 592 | 147 | 32 | card |  | Analytics Measures.AVG Price @ Dead Sale |
| 275 | 734 | 147 | 31 | card |  | Analytics Measures.AVG Price @ Dead Sale - Forecast |
| 276 | 388 | 220 | 30 | card |  | Analytics Measures.IN - Valor da @ |
| 328 | 388 | 1520 | 370 | lineClusteredColumnComboChart |  | RELAÇÃO MENSAL - FATURAMENTO |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 353 | 33 | 318 | 72 | cardVisual |  |   |
| 373 | 13 | 60 | 52 | image |  | female_icon23078485966194817.png |
| 428 | 138 | 235 | 45 | card |  | Analytics Measures.Invoicing (Abate) |
| 439 | 9 | 124 | 30 | card |  | Analytics Measures.IN - Faturamento |
| 478 | 138 | 235 | 45 | card |  | Analytics Measures.Incoicing - Forecast (Abate) |
| 484 | 11 | 98 | 26 | card |  | Analytics Measures.IN - Meta |
| 507 | 767 | 257 | 89 | slicer | sim | Mês |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 627 | 33 | 322 | 72 | cardVisual |  | Analytics Measures.IN - Macho |
| 651 | 23 | 44 | 46 | image |  | male_icon6869846729085312.png |
| 698 | 137 | 236 | 54 | card |  | Analytics Measures.Invoicing (Abate) |
| 706 | 388 | 1520 | 370 | lineClusteredColumnComboChart |  | RELAÇÃO MENSAL - VENDA EM CABEÇAS |
| 712 | 11 | 120 | 31 | card |  | Analytics Measures.IN - Faturamento |
| 749 | 135 | 237 | 54 | card |  | Analytics Measures.Incoicing - Forecast (Abate) |
| 760 | 11 | 98 | 31 | card |  | Analytics Measures.IN - Meta |
| 899 | 33 | 324 | 72 | cardVisual |  | Analytics Measures.IN - Geral |
| 914 | 23 | 42 | 54 | image |  | sum_icon7677372755924409.png |
| 970 | 122 | 257 | 50 | card |  | Analytics Measures.Invoicing (Abate) |
| 982 | 8 | 133 | 30 | card |  | Analytics Measures.IN - Faturamento |
| 1019 | 121 | 257 | 50 | card |  | Analytics Measures.Incoicing - Forecast (Abate) |
| 1028 | 15 | 98 | 30 | card |  | Analytics Measures.IN - Meta |

## Venda em Pé (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 510 | 900 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 96 | 1498 | 210 | 70 | cardVisual |  | Analytics Measures.IN - Geral |
| 100 | 952 | 210 | 86 | cardVisual |  | Analytics Measures.IN - Macho |
| 101 | 419 | 210 | 65 | cardVisual |  |   |
| 121 | 402 | 67 | 49 | image |  | female_icon23078485966194817.png |
| 130 | 33 | 286 | 130 | image |  | 4d7120e0-00b7-48b1-b9e9-bdef9f45245519933911327.png |
| 165 | 1113 | 136 | 30 | card |  | Analytics Measures.IN - Realizado |
| 165 | 1251 | 136 | 30 | card |  | Analytics Measures.IN - Planejado |
| 165 | 1627 | 136 | 30 | card |  | Analytics Measures.IN - Realizado |
| 165 | 1765 | 136 | 30 | card |  | Analytics Measures.IN - Planejado |
| 166 | 603 | 136 | 30 | card |  | Analytics Measures.IN - Realizado |
| 166 | 742 | 136 | 30 | card |  | Analytics Measures.IN - Planejado |
| 190 | 1101 | 147 | 33 | card |  | Sum(pecuarioVendaEmPe.qtd) |
| 190 | 1615 | 147 | 33 | card |  | Sum(pecuarioVendaEmPe.qtd) |
| 190 | 1757 | 148 | 32 | card |  | Sum(fMetasEmPe.qtd) |
| 191 | 592 | 147 | 33 | card |  | Sum(pecuarioVendaEmPe.qtd) |
| 191 | 1243 | 148 | 32 | card |  | Sum(fMetasEmPe.qtd) |
| 191 | 1418 | 188 | 29 | card |  | Analytics Measures.IN - Cabeças Vendidas |
| 192 | 734 | 148 | 32 | card |  | Sum(fMetasEmPe.qtd) |
| 192 | 904 | 188 | 29 | card |  | Analytics Measures.IN - Cabeças Vendidas |
| 193 | 394 | 188 | 29 | card |  | Analytics Measures.IN - Cabeças Vendidas |
| 216 | 1101 | 147 | 33 | card |  | Analytics Measures.IN - AVG Live Weight (Em Pe) |
| 216 | 1243 | 147 | 32 | card |  | Analytics Measures.IN - AVG Live Weight (Em Pe - Forecast) |
| 216 | 1615 | 147 | 33 | card |  | Analytics Measures.IN - AVG Live Weight (Em Pe) |
| 216 | 1757 | 147 | 32 | card |  | Analytics Measures.IN - AVG Live Weight (Em Pe - Forecast) |
| 217 | 592 | 147 | 33 | card |  | Analytics Measures.IN - AVG Live Weight (Em Pe) |
| 217 | 734 | 147 | 32 | card |  | Analytics Measures.IN - AVG Live Weight (Em Pe - Forecast) |
| 218 | 899 | 188 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 218 | 1413 | 188 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 219 | 390 | 188 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 235 | 1411 | 146 | 47 | card |  | Analytics Measures.IN - Preço do KG |
| 236 | 897 | 146 | 47 | card |  | Analytics Measures.IN - Preço do KG |
| 237 | 388 | 146 | 47 | card |  | Analytics Measures.IN - Preço do KG |
| 239 | 0 | 61 | 50 | actionButton |  |  |
| 246 | 1243 | 148 | 31 | card |  | Analytics Measures.AVG Price KG Sale Venda em Pe - Forecast |
| 246 | 1617 | 148 | 31 | card |  | Analytics Measures.AVG Price KG Sale Venda em Pe |
| 246 | 1757 | 148 | 31 | card |  | Analytics Measures.AVG Price KG Sale Venda em Pe - Forecast |
| 247 | 734 | 148 | 31 | card |  | Analytics Measures.AVG Price KG Sale Venda em Pe - Forecast |
| 247 | 1103 | 148 | 31 | card |  | Analytics Measures.AVG Price KG Sale Venda em Pe |
| 248 | 594 | 148 | 31 | card |  | Analytics Measures.AVG Price KG Sale Venda em Pe |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 274 | 1102 | 147 | 32 | card |  | Analytics Measures.AVG Price @ Sale Venda em Pe |
| 274 | 1243 | 147 | 31 | card |  | Analytics Measures.AVG Price @ Sale Venda em Pe - Forecast |
| 274 | 1411 | 220 | 30 | card |  | Analytics Measures.IN - Valor da @ |
| 274 | 1616 | 147 | 32 | card |  | Analytics Measures.AVG Price @ Sale Venda em Pe |
| 274 | 1757 | 147 | 31 | card |  | Analytics Measures.AVG Price @ Sale Venda em Pe - Forecast |
| 275 | 592 | 147 | 32 | card |  | Analytics Measures.AVG Price @ Sale Venda em Pe |
| 275 | 734 | 147 | 31 | card |  | Analytics Measures.AVG Price @ Sale Venda em Pe - Forecast |
| 275 | 897 | 220 | 30 | card |  | Analytics Measures.IN - Valor da @ |
| 276 | 388 | 220 | 30 | card |  | Analytics Measures.IN - Valor da @ |
| 328 | 388 | 1520 | 370 | lineClusteredColumnComboChart |  | RELAÇÃO MENSAL - FATURAMENTO |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 353 | 24 | 318 | 72 | cardVisual |  |   |
| 373 | 4 | 60 | 52 | image |  | female_icon23078485966194817.png |
| 429 | 149 | 235 | 45 | card |  | Analytics Measures.Invoicing (Em Pe ) |
| 439 | 12 | 124 | 30 | card |  | Analytics Measures.IN - Faturamento |
| 478 | 149 | 235 | 45 | card |  | Analytics Measures.Incoicing - Forecast (Em Pe) |
| 480 | 3 | 143 | 34 | card |  | Analytics Measures.IN - Faturamento Planejado |
| 507 | 767 | 257 | 89 | slicer | sim | Mês |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 627 | 23 | 322 | 72 | cardVisual |  | Analytics Measures.IN - Macho |
| 651 | 13 | 44 | 46 | image |  | male_icon6869846729085312.png |
| 697 | 149 | 236 | 54 | card |  | Analytics Measures.Invoicing (Em Pe ) |
| 706 | 388 | 1520 | 370 | lineClusteredColumnComboChart |  | RELAÇÃO MENSAL - VENDA EM CABEÇAS |
| 713 | 1 | 136 | 30 | card |  | Analytics Measures.IN - Faturamento |
| 750 | 149 | 237 | 53 | card |  | Analytics Measures.Incoicing - Forecast (Em Pe) |
| 758 | 1 | 137 | 33 | card |  | Analytics Measures.IN - Faturamento Planejado |
| 899 | 27 | 324 | 72 | cardVisual |  | Analytics Measures.IN - Geral |
| 914 | 17 | 42 | 54 | image |  | sum_icon7677372755924409.png |
| 970 | 131 | 256 | 50 | card |  | Analytics Measures.Invoicing (Em Pe ) |
| 982 | 2 | 140 | 30 | card |  | Analytics Measures.IN - Faturamento |
| 1019 | 131 | 257 | 50 | card |  | Analytics Measures.Incoicing - Forecast (Em Pe) |
| 1028 | 9 | 130 | 31 | card |  | Analytics Measures.IN - Faturamento Planejado |

## Compras (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 510 | 900 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 135 | 1190 | 209 | 71 | cardVisual |  | Analytics Measures.IN - Geral |
| 136 | 34 | 283 | 131 | image |  | 4d7120e0-00b7-48b1-b9e9-bdef9f45245519933911327.png |
| 137 | 779 | 209 | 71 | cardVisual |  | Analytics Measures.IN - Macho |
| 140 | 348 | 182 | 64 | cardVisual |  |   |
| 148 | 1726 | 190 | 90 | cardVisual |  | Analytics Measures.@ AVG Price Purchase |
| 158 | 339 | 59 | 51 | image |  | female_icon23078485966194817.png |
| 159 | 1560 | 185 | 80 | card |  | Analytics Measures.IN - Valor da @ Compra |
| 203 | 1287 | 134 | 30 | card |  | Analytics Measures.IN - Realizado |
| 204 | 1413 | 136 | 28 | card |  | Analytics Measures.IN - Planejado |
| 205 | 465 | 134 | 30 | card |  | Analytics Measures.IN - Realizado |
| 206 | 591 | 136 | 28 | card |  | Analytics Measures.IN - Planejado |
| 206 | 876 | 134 | 30 | card |  | Analytics Measures.IN - Realizado |
| 207 | 1002 | 136 | 28 | card |  | Analytics Measures.IN - Planejado |
| 229 | 1138 | 174 | 29 | card |  | Analytics Measures.IN - Cabeças Compradas |
| 230 | 315 | 174 | 29 | card |  | Analytics Measures.IN - Cabeças Compradas |
| 230 | 1287 | 137 | 33 | card |  | Sum(pecuarioCompras.qtd) |
| 230 | 1414 | 129 | 33 | card |  | Sum(fMetasCompras.qtd) |
| 231 | 726 | 174 | 29 | card |  | Analytics Measures.IN - Cabeças Compradas |
| 232 | 464 | 137 | 33 | card |  | Sum(pecuarioCompras.qtd) |
| 232 | 591 | 129 | 33 | card |  | Sum(fMetasCompras.qtd) |
| 233 | 875 | 137 | 33 | card |  | Sum(pecuarioCompras.qtd) |
| 233 | 1002 | 129 | 33 | card |  | Sum(fMetasCompras.qtd) |
| 239 | 0 | 61 | 50 | actionButton |  |  |
| 239 | 1724 | 190 | 90 | card |  | Analytics Measures.Ágio |
| 241 | 1570 | 165 | 80 | card |  | Analytics Measures.IN - Ágio |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 257 | 1307 | 100 | 34 | card |  | Analytics Measures.IN AVG - Peso Médio de Compra |
| 259 | 485 | 100 | 34 | card |  | Analytics Measures.IN AVG - Peso Médio de Compra |
| 260 | 896 | 100 | 34 | card |  | Analytics Measures.IN AVG - Peso Médio de Compra |
| 260 | 1143 | 169 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 261 | 321 | 169 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 261 | 1429 | 105 | 29 | card |  | Analytics Measures.IN AVG - Peso Médio de Compra (Forecast) |
| 262 | 606 | 105 | 29 | card |  | Analytics Measures.IN AVG - Peso Médio de Compra (Forecast) |
| 262 | 732 | 169 | 30 | card |  | Analytics Measures.IN - Peso Médio |
| 263 | 1017 | 105 | 29 | card |  | Analytics Measures.IN AVG - Peso Médio de Compra (Forecast) |
| 287 | 1306 | 98 | 35 | card |  | Analytics Measures.AVG Purchase Price KG |
| 289 | 484 | 98 | 35 | card |  | Analytics Measures.AVG Purchase Price KG |
| 290 | 895 | 98 | 35 | card |  | Analytics Measures.AVG Purchase Price KG |
| 290 | 1143 | 120 | 30 | card |  | Analytics Measures.IN - Preço do KG |
| 291 | 321 | 120 | 30 | card |  | Analytics Measures.IN - Preço do KG |
| 291 | 1425 | 104 | 29 | card |  | Analytics Measures.AVG Purchase Price KG (Forecast) |
| 292 | 602 | 104 | 29 | card |  | Analytics Measures.AVG Purchase Price KG (Forecast) |
| 292 | 732 | 120 | 30 | card |  | Analytics Measures.IN - Preço do KG |
| 293 | 1013 | 104 | 29 | card |  | Analytics Measures.AVG Purchase Price KG (Forecast) |
| 328 | 34 | 318 | 72 | cardVisual |  |   |
| 330 | 381 | 1533 | 365 | lineClusteredColumnComboChart |  | RELAÇÃO DESEMBOLSO DE COMPRAS |
| 347 | 14 | 60 | 52 | image |  | female_icon23078485966194817.png |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 403 | 139 | 235 | 45 | card |  | Analytics Measures.Total Paid |
| 413 | 10 | 124 | 30 | card |  | Analytics Measures.IN - Inv Realizado |
| 452 | 139 | 235 | 45 | card |  | Analytics Measures.Total Paid - Forecast |
| 460 | 6 | 133 | 34 | card |  | Analytics Measures.IN - Inv Planejado |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 598 | 30 | 322 | 72 | cardVisual |  | Analytics Measures.IN - Macho |
| 622 | 20 | 44 | 46 | image |  | male_icon6869846729085312.png |
| 669 | 134 | 236 | 54 | card |  | Analytics Measures.Total Paid |
| 684 | 8 | 133 | 31 | card |  | Analytics Measures.IN - Inv Realizado |
| 713 | 380 | 1533 | 363 | lineClusteredColumnComboChart |  | RELAÇÃO CABEÇAS COMPRADAS |
| 720 | 132 | 237 | 54 | card |  | Analytics Measures.Total Paid - Forecast |
| 730 | 9 | 130 | 30 | card |  | Analytics Measures.IN - Inv Planejado |
| 889 | 32 | 324 | 72 | cardVisual |  | Analytics Measures.IN - Geral |
| 904 | 22 | 42 | 54 | image |  | sum_icon7677372755924409.png |
| 960 | 121 | 257 | 50 | card |  | Analytics Measures.Total Paid |
| 972 | 7 | 133 | 30 | card |  | Analytics Measures.IN - Inv Realizado |
| 1009 | 121 | 257 | 50 | card |  | Analytics Measures.Total Paid - Forecast |
| 1018 | 3 | 139 | 30 | card |  | Analytics Measures.IN - Inv Planejado |

## Nascimentos (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 510 | 900 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 93 | 947 | 182 | 80 | cardVisual |  | Analytics Measures.IN - Macho |
| 93 | 1470 | 182 | 80 | cardVisual |  | Analytics Measures.IN - Geral |
| 100 | 401 | 182 | 64 | cardVisual |  |   |
| 113 | 1458 | 42 | 55 | image |  | sum_icon7677372755924409.png |
| 118 | 392 | 59 | 51 | image |  | female_icon23078485966194817.png |
| 118 | 929 | 45 | 48 | image |  | male_icon6869846729085312.png |
| 130 | 33 | 286 | 130 | image |  | 4d7120e0-00b7-48b1-b9e9-bdef9f45245519933911327.png |
| 164 | 1074 | 135 | 30 | card |  | Analytics Measures.IN - Realizado |
| 164 | 1598 | 135 | 30 | card |  | Analytics Measures.IN - Realizado |
| 165 | 541 | 135 | 30 | card |  | Analytics Measures.IN - Realizado |
| 166 | 1227 | 138 | 28 | card |  | Analytics Measures.IN - Planejado |
| 166 | 1750 | 138 | 28 | card |  | Analytics Measures.IN - Planejado |
| 168 | 693 | 138 | 28 | card |  | Analytics Measures.IN - Planejado |
| 189 | 1102 | 132 | 32 | card |  | Sum(pecuarioNascimento.qtd) |
| 189 | 1625 | 132 | 32 | card |  | Sum(pecuarioNascimento.qtd) |
| 190 | 568 | 132 | 32 | card |  | Sum(pecuarioNascimento.qtd) |
| 191 | 907 | 195 | 30 | card |  | Analytics Measures.IN - Nascimentos (Label - 2) |
| 191 | 1239 | 132 | 32 | card |  | Sum(fMetasNascimentos.qtd) |
| 191 | 1430 | 195 | 30 | card |  | Analytics Measures.IN - Nascimentos (Label - 2) |
| 191 | 1762 | 132 | 32 | card |  | Sum(fMetasNascimentos.qtd) |
| 193 | 373 | 195 | 30 | card |  | Analytics Measures.IN - Nascimentos (Label - 2) |
| 193 | 706 | 132 | 32 | card |  | Sum(fMetasNascimentos.qtd) |
| 226 | 1102 | 132 | 32 | card |  | Analytics Measures.IN - % Male Birth |
| 226 | 1625 | 132 | 32 | card |  | Analytics Measures.% Birth x Forecast |
| 228 | 568 | 132 | 32 | card |  | Analytics Measures.IN - % Female Birth |
| 229 | 909 | 195 | 30 | card |  | Analytics Measures.IN - Nascimentos |
| 229 | 1432 | 195 | 30 | card |  | Analytics Measures.IN - Nascimentos |
| 230 | 376 | 195 | 30 | card |  | Analytics Measures.IN - Nascimentos |
| 239 | 0 | 61 | 50 | actionButton |  |  |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 289 | 4 | 1910 | 399 | lineClusteredColumnComboChart |  | NASCIMENTOS - REALIZADO X PLANEJADO - MENSAL |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 689 | 4 | 1910 | 387 | lineClusteredColumnComboChart |  | NASCIMENTOS - REALIZADO X PLANEJADO - ACUMULADO |

## Mortes (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 510 | 900 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 130 | 33 | 286 | 130 | image |  | 4d7120e0-00b7-48b1-b9e9-bdef9f45245519933911327.png |
| 131 | 1540 | 240 | 70 | cardVisual |  | Analytics Measures.IN - Geral |
| 134 | 745 | 240 | 70 | cardVisual |  | Analytics Measures.IN - Jovens |
| 134 | 1143 | 240 | 70 | cardVisual |  | Analytics Measures.IN - Adultos |
| 151 | 1536 | 42 | 53 | image |  | sum_icon7677372755924409.png |
| 151 | 1737 | 144 | 56 | card |  | Analytics Measures.Dead Quantity |
| 154 | 942 | 144 | 56 | card |  | Analytics Measures.Dead Quantity |
| 154 | 1123 | 80 | 62 | image |  | boi_icon4418355708302577.png |
| 154 | 1340 | 144 | 56 | card |  | Analytics Measures.Dead Quantity |
| 159 | 719 | 96 | 52 | image |  | Jovem_icon5669957791527793.png |
| 162 | 1843 | 44 | 39 | card |  | Analytics Measures.IN - Cabeças |
| 165 | 1048 | 44 | 39 | card |  | Analytics Measures.IN - Cabeças |
| 165 | 1445 | 44 | 39 | card |  | Analytics Measures.IN - Cabeças |
| 199 | 331 | 240 | 70 | cardVisual |  | Analytics Measures.IN - Bezerro |
| 209 | 1737 | 132 | 32 | card |  | Analytics Measures.% mORTALITY ( MEAN MONTH) |
| 211 | 1520 | 240 | 30 | card |  | Analytics Measures.IN - Mortalidade sobre Rebanho Médio |
| 212 | 942 | 132 | 32 | card |  | Analytics Measures.% mORTALITY ( MEAN MONTH) |
| 212 | 1339 | 132 | 32 | card |  | Analytics Measures.% mORTALITY ( MEAN MONTH) |
| 214 | 725 | 240 | 30 | card |  | Analytics Measures.IN - Mortalidade sobre Rebanho Médio |
| 214 | 1123 | 240 | 30 | card |  | Analytics Measures.IN - Mortalidade sobre Rebanho Médio |
| 219 | 310 | 80 | 59 | image |  | bezerro_icon36570149245780714.png |
| 219 | 528 | 144 | 56 | card |  | Analytics Measures.Dead Quantity |
| 230 | 634 | 44 | 39 | card |  | Analytics Measures.IN - Cabeças |
| 239 | 0 | 61 | 50 | actionButton |  |  |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 271 | 1532 | 97 | 35 | card |  | Analytics Measures.IN - Meta |
| 272 | 1735 | 132 | 32 | card |  | Analytics Measures.Dead Quantity - Forecast |
| 274 | 735 | 92 | 33 | card |  | Analytics Measures.IN - Meta |
| 274 | 940 | 132 | 32 | card |  | Analytics Measures.Dead Quantity - Forecast |
| 274 | 1133 | 95 | 33 | card |  | Analytics Measures.IN - Meta |
| 274 | 1337 | 132 | 32 | card |  | Analytics Measures.Dead Quantity - Forecast |
| 277 | 528 | 132 | 32 | card |  | Analytics Measures.% mORTALITY ( MEAN MONTH) |
| 279 | 311 | 240 | 30 | card |  | Analytics Measures.IN - Mortalidade sobre Rebanho Médio |
| 308 | 528 | 132 | 32 | card |  | Analytics Measures.% Mortality |
| 309 | 312 | 194 | 30 | card |  | Analytics Measures.IN - Mortalidade sobre Nascimento |
| 330 | 1145 | 770 | 742 | clusteredBarChart |  | Causa Morte |
| 331 | 2 | 1138 | 338 | lineClusteredColumnComboChart |  | REALIZADO X PLANEJADO - ACUMULADO GERAL |
| 339 | 308 | 107 | 32 | card |  | Analytics Measures.IN - Meta |
| 339 | 525 | 132 | 32 | card |  | Analytics Measures.Dead Quantity - Forecast |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 734 | 2 | 1138 | 338 | lineClusteredColumnComboChart |  | MORTES - REALIZADO X PLANEJADO - MENSAL |

## Transferências (1920×1080)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 510 | 900 | 118 | cardVisual |  | Analytics Measures.Selected Farm |
| 6 | 1582 | 335 | 80 | cardVisual |  | Analytics Measures.IN - TRANSFERÊNCIAS |
| 130 | 33 | 286 | 130 | image |  | 4d7120e0-00b7-48b1-b9e9-bdef9f45245519933911327.png |
| 231 | 0 | 61 | 50 | actionButton |  |  |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 271 | 6 | 667 | 78 | cardVisual |  | Analytics Measures.IN - Macho |
| 271 | 1248 | 667 | 78 | cardVisual |  |   |
| 344 | 1269 | 59 | 51 | image |  | female_icon23078485966194817.png |
| 347 | 1381 | 267 | 45 | card |  | Analytics Measures.IN - Entrada |
| 347 | 1649 | 259 | 45 | card |  | Analytics Measures.IN - Saida |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 349 | 28 | 45 | 48 | image |  | male_icon6869846729085312.png |
| 349 | 139 | 267 | 45 | card |  | Analytics Measures.IN - Entrada |
| 349 | 407 | 259 | 45 | card |  | Analytics Measures.IN - Saida |
| 403 | 1373 | 135 | 30 | card |  | Analytics Measures.IN - Realizado |
| 403 | 1507 | 134 | 30 | card |  | Analytics Measures.IN - Planejado |
| 405 | 138 | 135 | 30 | card |  | Analytics Measures.IN - Realizado |
| 405 | 273 | 134 | 30 | card |  | Analytics Measures.IN - Planejado |
| 405 | 1642 | 135 | 30 | card |  | Analytics Measures.IN - Realizado |
| 405 | 1775 | 133 | 30 | card |  | Analytics Measures.IN - Planejado |
| 406 | 408 | 135 | 30 | card |  | Analytics Measures.IN - Realizado |
| 406 | 540 | 133 | 30 | card |  | Analytics Measures.IN - Planejado |
| 433 | 1373 | 133 | 32 | card |  | Analytics Measures.IN QTD Transfer |
| 433 | 1508 | 133 | 33 | card |  | Analytics Measures.IN QTD Transfer Forecast |
| 435 | 13 | 69 | 31 | card |  | Analytics Measures.IN - Quantidade |
| 435 | 139 | 133 | 32 | card |  | Analytics Measures.IN QTD Transfer |
| 435 | 273 | 133 | 33 | card |  | Analytics Measures.IN QTD Transfer Forecast |
| 435 | 1255 | 69 | 31 | card |  | Analytics Measures.IN - Quantidade |
| 437 | 1641 | 133 | 32 | card |  | Analytics Measures.IN QTD Transfer |
| 437 | 1776 | 133 | 33 | card |  | Analytics Measures.IN QTD Transfer Forecast |
| 438 | 407 | 133 | 32 | card |  | Analytics Measures.IN QTD Transfer |
| 438 | 542 | 133 | 33 | card |  | Analytics Measures.IN QTD Transfer Forecast |
| 465 | 1373 | 133 | 33 | card |  | Analytics Measures.IN - AVG Weight Transfer |
| 466 | 1508 | 133 | 33 | card |  | Analytics Measures.IN - AVG Weight Transfer Forecast |
| 467 | 17 | 132 | 30 | card |  | Analytics Measures.IN Peso Médio |
| 467 | 139 | 133 | 33 | card |  | Analytics Measures.IN - AVG Weight Transfer |
| 467 | 1258 | 132 | 30 | card |  | Analytics Measures.IN Peso Médio |
| 468 | 273 | 133 | 33 | card |  | Analytics Measures.IN - AVG Weight Transfer Forecast |
| 469 | 1641 | 133 | 33 | card |  | Analytics Measures.IN - AVG Weight Transfer |
| 470 | 407 | 133 | 33 | card |  | Analytics Measures.IN - AVG Weight Transfer |
| 470 | 1776 | 133 | 33 | card |  | Analytics Measures.IN - AVG Weight Transfer Forecast |
| 471 | 542 | 133 | 33 | card |  | Analytics Measures.IN - AVG Weight Transfer Forecast |
| 497 | 14 | 109 | 32 | card |  | Analytics Measures.IN Valor@ |
| 497 | 1256 | 109 | 32 | card |  | Analytics Measures.IN Valor@ |
| 498 | 1374 | 133 | 33 | card |  | Analytics Measures.IN - AVG Price @ Transfer |
| 499 | 140 | 133 | 33 | card |  | Analytics Measures.IN - AVG Price @ Transfer |
| 499 | 1508 | 133 | 33 | card |  | Analytics Measures.IN - AVG Price @ Transfer Forecas |
| 501 | 273 | 133 | 33 | card |  | Analytics Measures.IN - AVG Price @ Transfer Forecas |
| 501 | 1642 | 133 | 33 | card |  | Analytics Measures.IN - AVG Price @ Transfer |
| 503 | 408 | 133 | 33 | card |  | Analytics Measures.IN - AVG Price @ Transfer |
| 503 | 1776 | 133 | 33 | card |  | Analytics Measures.IN - AVG Price @ Transfer Forecas |
| 504 | 542 | 133 | 33 | card |  | Analytics Measures.IN - AVG Price @ Transfer Forecas |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 541 | 5 | 1909 | 534 | lineClusteredColumnComboChart |  | REALIZADO X PLANEJADO |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |

## PG3 (1280×1600)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 0 | 99 | 118 | actionButton |  |  |
| 0 | 279 | 727 | 118 | card |  | Analytics Measures.Selected Farm |
| 129 | 2 | 504 | 56 | textbox |  | NASCIMENTOS |
| 200 | 3 | 337 | 257 | cardVisual |  | Realizado, Planejado |
| 209 | 344 | 240 | 240 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 209 | 576 | 240 | 240 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 209 | 808 | 240 | 240 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 209 | 1039 | 240 | 240 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 264 | 348 | 230 | 115 | cardVisual |  | Analytics Measures.Birth Quantity |
| 264 | 580 | 232 | 115 | cardVisual |  | Analytics Measures.Birth Quantity |
| 264 | 814 | 228 | 115 | cardVisual |  | Analytics Measures.% Mortality |
| 264 | 1046 | 228 | 115 | cardVisual |  | Analytics Measures.% Birth x Forecast (Year) |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 361 | 365 | 199 | 49 | textbox |  | Nascimento Macho |
| 361 | 596 | 199 | 49 | textbox |  | Nascimento Fêmea |
| 361 | 834 | 199 | 49 | textbox |  | % Mortalidade |
| 361 | 1059 | 199 | 50 | textbox |  | % Nascimentos |
| 455 | 2 | 1275 | 324 | lineClusteredColumnComboChart |  | RELAÇÃO DE NASCIMENTOS |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 779 | 0 | 496 | 54 | textbox |  | MORTALIDADE |
| 861 | 2 | 639 | 736 | clusteredBarChart |  | Causa Morte |
| 861 | 644 | 633 | 246 | lineClusteredColumnComboChart |  | PREVISTO X REALIZADO ACUMULADO BEZERROS |
| 1107 | 644 | 633 | 246 | lineClusteredColumnComboChart |  | PREVISTO X REALIZADO ACUMULADO JOVENS |
| 1353 | 644 | 633 | 246 | lineClusteredColumnComboChart |  | PREVISTO X REALIZADO ACUMULADO ADULTOS |

## Duplicata de PG2 (1280×1600)

| y | x | largura | altura | tipo | oculto | título / campos |
|---|---|---|---|---|---|---|
| 0 | 0 | 99 | 118 | actionButton |  |  |
| 0 | 279 | 727 | 118 | card |  | Analytics Measures.Selected Farm |
| 108 | 2 | 504 | 56 | textbox |  | VENDAS E ABATES |
| 176 | 330 | 322 | 275 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 176 | 646 | 322 | 275 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 176 | 959 | 322 | 275 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 190 | 2 | 320 | 120 | cardVisual |  | Faturamento Realizado |
| 195 | 988 | 262 | 97 | cardVisual |  | Analytics Measures.Peso em @ |
| 197 | 673 | 262 | 98 | cardVisual |  | Sum(pecuarioVendaAbate.qtd) |
| 203 | 359 | 262 | 98 | cardVisual |  | Sum(pecuarioVendaEmPe.qtd) |
| 253 | 361 | 556 | 86 | slicer | sim | PROPRIETÁRIO |
| 275 | 1056 | 166 | 51 | textbox |  | Peso Médio de @ |
| 277 | 731 | 166 | 50 | textbox |  | CBS - Venda Abate |
| 283 | 417 | 166 | 50 | textbox |  | CBS - Venda em Pé |
| 301 | 988 | 262 | 87 | cardVisual |  | Analytics Measures.Rendimento Carcaça |
| 309 | 2 | 320 | 121 | cardVisual |  | Faturamento Planejado |
| 312 | 672 | 263 | 87 | cardVisual |  | Analytics Measures.AVG Price @ Dead Sale |
| 316 | 359 | 262 | 87 | cardVisual |  | Analytics Measures.AVG Price KG Sale Venda em Pe |
| 348 | 361 | 556 | 87 | slicer | sim | FAZENDA |
| 371 | 1034 | 204 | 64 | textbox |  | Rendimento de Carcaça  				 Abate |
| 374 | 682 | 240 | 50 | textbox |  | Valor da @ |
| 380 | 374 | 235 | 50 | textbox |  | Valor do KG |
| 457 | 2 | 633 | 238 | lineClusteredColumnComboChart |  | RELAÇÃO FATURAMENTO |
| 457 | 644 | 633 | 238 | clusteredColumnChart |  | RELAÇÃO POR SEXO - VENDA EM CABEÇAS |
| 507 | 767 | 257 | 89 | slicer | sim | Mês |
| 517 | 1058 | 178 | 117 | slicer | sim | Parâmetro - Data.Parâmetro - Data |
| 558 | 361 | 256 | 92 | slicer | sim | Ano |
| 558 | 362 | 256 | 74 | slicer | sim | Safra |
| 558 | 672 | 246 | 74 | slicer | sim | Mês |
| 703 | 2 | 1275 | 277 | clusteredColumnChart |  | RELAÇÃO MENSAL - VENDA EM CABEÇAS |
| 980 | 0 | 504 | 41 | textbox |  | MOVIMENTAÇÕES DO REBANHO |
| 1031 | 426 | 215 | 148 | cardVisual |  | NASCIMENTOS |
| 1037 | 851 | 209 | 154 | cardVisual |  | CABEÇAS VENDIDAS |
| 1037 | 1061 | 209 | 154 | cardVisual |  | CABEÇAS COMPRADAS |
| 1039 | 416 | 240 | 221 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 1039 | 1052 | 228 | 221 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 1040 | 205 | 241 | 221 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 1041 | 0 | 235 | 213 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 1041 | 625 | 241 | 221 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 1041 | 836 | 240 | 221 | image |  | Design_sem_nome_(28)6276116030067768.png |
| 1056 | 20 | 195 | 72 | cardVisual |  | Analytics Measures.Mean Month |
| 1056 | 221 | 195 | 72 | cardVisual |  | Analytics Measures.Mean Month Ha |
| 1058 | 637 | 117 | 111 | cardVisual |  | MORTES |
| 1060 | 713 | 150 | 111 | cardVisual |  | ÍNDICE MORT. |
| 1121 | 230 | 195 | 33 | textbox |  | LOTAÇÃO CAB/HA |
| 1123 | 20 | 195 | 33 | textbox |  | REBANHO MÉDIO CAB |
| 1140 | 225 | 193 | 66 | cardVisual |  | Analytics Measures.UA Median Ha |
| 1150 | 644 | 205 | 49 | cardVisual |  | Analytics Measures.% Death x Death Forecast |
| 1150 | 1061 | 209 | 49 | cardVisual |  | Analytics Measures.% Purchased Quantity |
| 1152 | 12 | 193 | 65 | cardVisual |  | Analytics Measures.UA Median Month |
| 1152 | 851 | 207 | 51 | cardVisual |  | Analytics Measures.% Amount Saled |
| 1160 | 443 | 182 | 45 | cardVisual |  | Analytics Measures.% Birth x Forecast |
| 1193 | 1080 | 172 | 37 | textbox |  | % EM RELAÇÃO A META |
| 1195 | 447 | 174 | 31 | textbox |  | % EM RELAÇÃO A META |
| 1197 | 23 | 195 | 33 | textbox |  | REBANHO MÉDIO UA |
| 1197 | 875 | 162 | 37 | textbox |  | % EM RELAÇÃO A META |
| 1199 | 230 | 195 | 33 | textbox |  | LOTAÇÃO UA/HA |
| 1199 | 665 | 164 | 34 | textbox |  | % EM RELAÇÃO A META |
| 1277 | 2 | 1275 | 320 | clusteredColumnChart |  | ESTOQUE POR CATEGORIA |
| 1285 | 1015 | 254 | 94 | cardVisual |  | REBANHO FINAL |
| 1363 | 808 | 264 | 238 | image |  | Design_sem_nome_(25)5111219274726155.png |
