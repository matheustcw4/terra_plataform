# MODEL DUMP: CICLO COMPLETO - BOLETIM MENSAL (6).pbix

## Tables & columns (schema)

### Analytics Measures
Column:Int64
### Categorias
categoria_bi:string, gender:string
### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28
Date:datetime64[ns], Ano:Int64, MonthNo:Int64, Mês:string, QuarterNo:Int64, Trimestre:string, Dia:Int64
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04
Date:datetime64[ns], Ano:Int64, MonthNo:Int64, Mês:string, QuarterNo:Int64, Trimestre:string, Dia:Int64
### Parâmetro - Data
Parâmetro - Data:string, Parâmetro - Data Campos:string, Parâmetro - Data Pedido:Int64
### RLS
base:string, CÓDIGO DO CLIENTE:string, proprietÁrio:string, cliente:string, NOME DO PROJETO (FAZENDA):string, tÉcnico:string, prop_faz:string, tipo-email:string, e-mail:string
### Tabela
TipoVenda:string
### dCalendar
Data:datetime64[ns], Ano:Int64, Mês:Int64, Nome do Mês:string, Classificador Mês-Ano:Int64, mesano:string, anosafra:string, OrdemSafra:Int64, safra:string, OrdemAnoSafra:Int64, Safra Abreviada:string
### fArea
DATA:datetime64[ns], Área_pasto:Float64, Área_ilp:Float64, Área_total:Float64, proprietÁrio:string, fazenda:string, retiro:string, cÓdigo_cliente:string, projeto:string, PROP_FAZ:string
### fMetasAbate
operaÇÃo:string, cliente:string, categ_fazenda:string, DATA_OLD:string, qtd:Float64, era:string, peso_vivo:Float64, rendimento:Float64, peso_arroba:Float64, valor_arroba:Float64, faturamento:Float64, data_abrev:string, categoria_bi:string, sexo:string, peso_morto:Float64, pesovivo_total:Float64, pesomorto_total:Float64, valor_kg:Float64, valor_cab:Float64, proprietÁrio:string, fazenda:string, retiro:string, Peso Morto Total:Float64, prop_faz:string, Total de @:Float64, DATA:datetime64[ns]
### fMetasCompras
operaÇÃo:string, DATA:datetime64[ns], origem:string, categ_fazenda:string, qtd:Float64, peso_vivo:Float64, total_peso:Float64, valor_cab:Float64, VALOR TOTAL:Float64, valo_kg:Float64, valor_arroba:Float64, data_abrev:string, categoria_bi:string, sexo:string, peso_arroba:Float64, proprietÁrio:string, fazenda:string, retiro:string, PROP_FAZ:string, prop_faz 2:string
### fMetasDre
centro_de_custo:string, sub_centro:string, valor:Float64, data_pag_old:string, operaÇÃo:string, centro_de_custo_bi:string, sub_centro_bi:string, fazenda:string, proprietÁrio:string, desembolso-CAT:string, custeio-CAT:string, tipo_custeio-CAT:string, Desembolso:Float64, F/V:string, Custeio:Float64, prop_faz:string, data_pag:datetime64[ns]
### fMetasEmPe
operaÇÃo:string, cliente:string, DATA_OLD:string, documento:string, categ_fazenda:string, qtd:Float64, peso_vivo:Float64, pesovivo_total:Float64, valor_arroba:Float64, valor_cab:Float64, faturamento:Float64, data_abrev:string, categoria_bi:string, sexo:string, valor_kg:Float64, proprietÁrio:string, fazenda:string, retiro:string, Peso Morto:Float64, prop_faz:string, Total de @:Float64, Peso Total:Float64, DATA:datetime64[ns]
### fMetasMortes
operaÇÃo:string, DATA:datetime64[ns], categ_fazenda:string, carimbo_bez:string, qtd:Float64, causa:string, LOCAL:string, peso_vivo:Float64, safra:string, data_abrev:string, grupo_categoria:string, era:string, categoria_bi:string, peso_total:Float64, sexo:string, proprietÁrio:string, fazenda:string, retiro:string, prop_faz:string
### fMetasNascimentos
operaÇÃo:string, DATA:datetime64[ns], categ_fazenda:string, qtd:Float64, safra:string, peso_nasc:Float64, data_abrev:string, categoria_bi:string, sexo:string, proprietÁrio:string, fazenda:string, retiro:string, prop_faz:string
### fMetasRebanhoMedio
grupo_categoria:string, qtd_cab:Float64, qtd_ua:Float64, DATA:datetime64[ns], proprietÁrio:string, fazenda:string, retiro:string, prop_faz:string
### fMetasTransferencias
operaÇÃo:string, DATA:datetime64[ns], categoria_fazenda:string, qtd:Float64, peso_vivo:Float64, total_peso:Float64, VALOR TOTAL:Float64, data_abrev:string, categoria_bi:string, sexo:string, peso_arroba:Float64, valor_cab:Float64, valo_kg:Float64, valor_arroba:Float64, proprietÁrio:string, fazenda:string, retiro:string, prop_faz:string, Peso Total @:Float64
### fMovGado
Nascimento:object, Morte:object, Inicial:Float64, Vendas:Float64, Type Operation:string, Mudança de Categoria (Saída):object, Mudança de Categoria (Entrada):object, Origin Ordenated:object, QTD C:Float64, OPERAÇÃO:string, QTD:Float64, categoria_bi:string, sexo:string, proprietÁrio:string, fazenda:string, retiro:string, DATA:datetime64[ns], prop_faz:string
### fTransferencias
operaÇÃo:string, DATA:datetime64[ns], categoria_fazenda:string, qtd:Float64, peso_vivo:Float64, total_peso:Float64, VALOR TOTAL:Float64, data_abrev:string, categoria_bi:string, sexo:string, peso_arroba:Float64, valor_cab:Float64, valo_kg:Float64, valor_arroba:Float64, proprietÁrio:string, fazenda:string, retiro:string, prop_faz:string, Peso Total @:Float64
### fUnidades
proprietÁrio:string, fazenda:string, projeto:string, SISTEMA PRODUTIVO:string, PROP_FAZ:string, CÓDIGO PROJETO:string, ano:string, filename:string
### financeiroDre
Type Operation:object, Desembolso:Float64, Custeio:Float64, Class subcenter:object, valor:Float64, data_pag:datetime64[ns], operaÇÃo:string, centro_de_custo_bi:string, sub_centro_bi:string, fazenda:string, proprietÁrio:string, desembolso-CAT:string, custeio-CAT:string, tipo_custeio-CAT:string, F/V:string, mes:string, ano:string, prop_faz:string, Classificacao:string, Meta C:object, Valor C:Float64
### pecuarioCompras
Paid:object, operaÇÃo:string, DATA:datetime64[ns], origem:string, categ_fazenda:string, qtd:Float64, peso_vivo:Float64, total_peso:Float64, valor_cab:Float64, VALOR TOTAL:Float64, valo_kg:Float64, valor_arroba:Float64, data_abrev:string, categoria_bi:string, sexo:string, peso_arroba:Float64, proprietÁrio:string, fazenda:string, retiro:string, Total de @:Float64, prop_faz:string
### pecuarioMortes
era:string, safra:string, forecast:Int64, operaÇÃo:string, categ_fazenda:string, carimbo_bez:string, qtd:Float64, causa:string, LOCAL:string, peso_vivo:string, data_abrev:string, grupo_categoria:string, categoria_bi:string, peso_total:Float64, sexo:string, proprietÁrio:string, fazenda:string, retiro:string, prop_faz:string, DATA:datetime64[ns], operaÇÃo_ktl:string, categ_fazenda_ktl:string
### pecuarioNascimento
operaÇÃo:string, DATA:datetime64[ns], categ_fazenda:string, qtd:Float64, safra:string, peso_nasc:Float64, data_abrev:string, categoria_bi:string, sexo:string, proprietÁrio:string, fazenda:string, retiro:string, prop_faz:string
### pecuarioRebanhoMedioMensal
farm:string, Forecast:Float64, grupo_categoria:string, qtd_cab:Float64, qtd_ua:Float64, DATA:datetime64[ns], proprietÁrio:string, fazenda:string, retiro:string, prop_faz:string
### pecuarioVendaAbate
Total Value:object, teste:object, Peso Morto Total:Float64, Total de @:Float64, tipovenda:string, operaÇÃo:string, cliente:string, categ_fazenda:string, DATA:datetime64[ns], qtd:Float64, era:string, peso_vivo:Float64, rendimento:Float64, peso_arroba:Float64, valor_arroba:Float64, faturamento:Float64, categoria_bi:string, sexo:string, peso_morto:Float64, pesovivo_total:Float64, pesomorto_total:Float64, valor_kg:Float64, valor_cab:Float64, proprietÁrio:string, fazenda:string, retiro:string, mes:string, ano:string, qtd_meta_diluida:Float64, qtd_meta_mensal:Float64, diluicao_meta:Int64, meta_diluida:Float64, meta_mensal:Float64, prop_faz:string
### pecuarioVendaEmPe
Total de @:Float64, tipovenda:string, Peso Total:Float64, operaÇÃo:string, cliente:string, DATA:datetime64[ns], categ_fazenda:string, qtd:Float64, peso_vivo:Float64, pesovivo_total:Float64, valor_arroba:Float64, valor_cab:Float64, faturamento:Float64, categoria_bi:string, sexo:string, valor_kg:Float64, proprietÁrio:string, fazenda:string, retiro:string, Peso Morto:Float64, mes:string, ano:string, qtd_meta_diluida:Float64, qtd_meta_mensal:Float64, diluicao_meta:Int64, meta_diluida:Float64, meta_mensal:Float64, prop_faz:string
### planejadoXRealizado
prop_faz:string, proprietÁrio:string, fazenda:string, centro_de_custo_bi:string, data:datetime64[ns], meta:Float64, realizado:Float64, Classificacao2:string, F/V:Int64, Valor C:Float64, Meta C:Float64, classificacao:string

## Row-count / cardinality stats (top)

                                                  TableName                      ColumnName  Cardinality  Dictionary  HashIndex  DataSize         ModifiedTime StructureModifiedTime
0                                        Analytics Measures                          Column            1           0          0       152  2024-10-22 15:56:15   2024-10-22 15:56:15
1                                                Categorias                    categoria_bi           15         601          0       152  2025-01-18 13:15:00   2025-01-18 13:15:00
2                                                Categorias                          gender            2         163          0       152  2025-01-20 12:01:41   2025-01-20 12:01:41
3    DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                            Date            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
4    DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                             Ano            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
5    DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                         MonthNo            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
6    DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                             Mês            1         147          0       152  2024-10-21 20:15:01   2024-10-21 20:14:53
7    DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                       QuarterNo            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
8    DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                       Trimestre            1         143          0       152  2024-10-21 20:15:01   2024-10-21 20:14:53
9    DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                             Dia            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
10      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                            Date         1096        8808          0      1904  2026-07-10 16:58:06   2025-01-08 11:39:16
11      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                             Ano            3          52          0       152  2026-07-10 16:58:06   2025-01-08 11:39:16
12      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                         MonthNo           12          88          0       696  2026-07-10 16:58:06   2025-01-08 11:39:16
13      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                             Mês           12         397          0       696  2026-07-10 16:58:06   2025-01-08 11:39:16
14      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                       QuarterNo            4          56          0       152  2026-07-10 16:58:06   2025-01-08 11:39:16
15      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                       Trimestre            4         203          0       152  2026-07-10 16:58:06   2025-01-08 11:39:16
16      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                             Dia           31         164          0       880  2026-07-10 16:58:06   2025-01-08 11:39:16
17                                         Parâmetro - Data                Parâmetro - Data            2         163          0       152  2025-06-06 00:06:26   2025-06-06 00:05:49
18                                         Parâmetro - Data         Parâmetro - Data Campos            2         229          0       152  2025-06-06 00:06:26   2025-06-06 00:05:49
19                                         Parâmetro - Data         Parâmetro - Data Pedido            2           0       1133       152  2025-06-06 00:06:26   2025-06-06 00:05:48
20                                                      RLS                            base           11         291          0       584  2025-05-28 13:58:25   2025-05-28 13:58:25
21                                                      RLS               CÓDIGO DO CLIENTE          116        2313          0       920  2025-05-28 13:58:25   2025-05-28 13:58:25
22                                                      RLS                    proprietÁrio          117        6977          0       920  2025-05-28 13:58:25   2025-05-28 13:58:25
23                                                      RLS                         cliente          119        4485          0       920  2025-05-28 13:58:25   2025-05-28 13:58:25
24                                                      RLS       NOME DO PROJETO (FAZENDA)          249        8007          0      1016  2025-05-28 13:58:25   2025-05-28 13:58:25
25                                                      RLS                         tÉcnico           26         843          0       728  2025-05-28 13:58:25   2025-05-28 13:58:25
26                                                      RLS                        prop_faz          296        7288          0      1144  2025-05-28 13:58:25   2025-05-28 13:58:25
27                                                      RLS                      tipo-email            3         223          0       152  2025-05-28 13:58:25   2025-05-28 13:58:25
28                                                      RLS                          e-mail           36        3157          0       672  2025-05-28 13:58:25   2025-05-28 13:58:25
29                                                   Tabela                       TipoVenda            2         163          0       152  2024-11-05 22:57:09   2024-11-05 22:57:09
30                                                dCalendar                            Data          836        6728          0      1264  2026-09-11 20:00:00   2025-01-08 11:39:16
31                                                dCalendar                             Ano            3          52          0       152  2024-10-22 15:31:44   2024-10-22 15:30:53
32                                                dCalendar                             Mês           12          88          0       568  2024-10-22 15:31:44   2024-10-22 15:30:53
33                                                dCalendar                     Nome do Mês           12         397          0       568  2024-10-23 12:22:55   2024-10-23 12:22:55
34                                                dCalendar           Classificador Mês-Ano           28         152          0       704  2026-07-10 16:58:06   2024-10-22 17:21:40
35                                                dCalendar                          mesano           28         739          0       704  2025-05-29 16:54:55   2025-05-29 16:54:55
36                                                dCalendar                        anosafra           28         907          0       704  2025-05-03 14:42:15   2025-05-03 14:37:58
37                                                dCalendar                      OrdemSafra           12          88          0       568  2025-05-03 14:37:07   2025-05-03 14:37:07
38                                                dCalendar                           safra            3         231          0       152  2025-05-03 14:37:07   2025-05-03 14:37:07
39                                                dCalendar                   OrdemAnoSafra           28         152          0       704  2025-05-03 14:41:47   2025-05-03 14:41:47
40                                                dCalendar                 Safra Abreviada            3         183          0       152  2026-07-10 16:58:06   2026-01-16 19:20:27
41                                                    fArea                            DATA           36         328          0      2344  2025-09-26 00:39:40   2025-09-26 00:46:22
42                                                    fArea                      Área_pasto          204        1672          0      1696  2025-09-26 00:39:40   2025-09-26 00:39:40
43                                                    fArea                        Área_ilp           28         264          0       216  2025-09-26 00:39:40   2025-09-26 00:39:40
44                                                    fArea                      Área_total          217        1776          0      1696  2025-09-26 00:39:40   2025-09-26 00:39:40
45                                                    fArea                    proprietÁrio           92        5491          0      1960  2025-09-26 00:39:40   2025-09-26 00:39:40
46                                                    fArea                         fazenda          196        6319          0      2896  2025-09-26 00:39:40   2025-09-26 00:39:40
47                                                    fArea                          retiro          184        5803          0      2816  2025-09-26 00:39:40   2025-09-26 00:39:40
48                                                    fArea                  cÓdigo_cliente           90        1819          0      1960  2025-09-26 00:39:40   2025-09-26 00:39:40
49                                                    fArea                         projeto           93        3513          0      1960  2025-09-26 00:39:40   2025-09-26 00:39:40
50                                                    fArea                        PROP_FAZ          224       16247          0      2896  2025-09-26 00:39:40   2025-09-26 00:39:40
51                                              fMetasAbate                        operaÇÃo            1         143          0       152  2025-01-24 18:52:19   2025-01-24 18:52:19
52                                              fMetasAbate                         cliente           41        1813          0       440  2025-01-24 18:52:19   2025-01-24 18:52:19
53                                              fMetasAbate                   categ_fazenda          164        7435          0      1792  2025-01-24 18:52:19   2025-01-24 18:52:19
54                                              fMetasAbate                        DATA_OLD          179        5491          0      1792  2026-03-09 13:17:49   2025-01-24 18:53:49
55                                              fMetasAbate                             qtd          490        3960          0      1912  2025-01-24 18:52:19   2025-01-24 18:52:19
56                                              fMetasAbate                             era           13         431          0       208  2025-01-24 18:52:19   2025-01-24 18:52:19
57                                              fMetasAbate                       peso_vivo          328        2664          0      1936  2025-01-24 18:52:19   2025-01-24 18:52:19
58                                              fMetasAbate                      rendimento          170        1400          0      1376  2025-01-24 18:52:19   2025-01-24 18:52:19
59                                              fMetasAbate                     peso_arroba          409        3312          0      2024  2025-01-24 18:52:19   2025-01-24 18:52:19
60                                              fMetasAbate                    valor_arroba          319        2592          0      2024  2025-01-24 18:52:19   2025-01-24 18:52:19
61                                              fMetasAbate                     faturamento         1120        9000          0      2600  2025-01-24 18:52:19   2025-01-24 18:52:19
62                                              fMetasAbate                      data_abrev           30        1023          0      1240  2025-01-24 18:52:19   2025-01-24 18:52:19
63                                              fMetasAbate                    categoria_bi           11         493          0       824  2025-01-24 18:52:19   2025-01-24 18:52:19
64                                              fMetasAbate                            sexo            2         163          0       392  2025-01-24 18:52:19   2025-01-24 18:52:19
65                                              fMetasAbate                      peso_morto          408        3304          0      2024  2025-01-24 18:52:19   2025-01-24 18:52:19
66                                              fMetasAbate                  pesovivo_total         1022        8216          0      2200  2025-01-24 18:52:19   2025-01-24 18:52:19
67                                              fMetasAbate                 pesomorto_total         1088        8744          0      2616  2025-01-24 18:52:19   2025-01-24 18:52:19
68                                              fMetasAbate                        valor_kg          627        5056          0      2200  2025-01-24 18:52:19   2025-01-24 18:52:19
69                                              fMetasAbate                       valor_cab          730        5880          0      2200  2025-01-24 18:52:19   2025-01-24 18:52:19
70                                              fMetasAbate                    proprietÁrio           67        4211          0      1176  2025-01-24 18:52:19   2025-01-24 18:52:19
71                                              fMetasAbate                         fazenda          106        3563          0      1368  2025-01-24 18:52:19   2025-01-24 18:52:19
72                                              fMetasAbate                          retiro           99        3223          0      1312  2025-01-24 18:52:19   2025-01-24 18:52:19
73                                              fMetasAbate                Peso Morto Total         1088        8744          0      2616  2026-06-19 20:33:55   2025-01-31 18:36:38
74                                              fMetasAbate                        prop_faz          115        8899          0      1368  2025-05-26 11:47:56   2025-05-26 11:47:56
75                                              fMetasAbate                      Total de @         1091        8768          0      2616  2026-06-19 20:33:55   2026-01-17 13:38:38
76                                              fMetasAbate                            DATA          178        1464          0      1792  2026-03-09 13:17:51   2026-03-09 13:22:19
77                                            fMetasCompras                        operaÇÃo            1         145          0       152  2025-01-24 17:53:47   2025-01-24 17:53:47
78                                            fMetasCompras                            DATA          138        1144          0       848  2025-01-24 17:57:46   2025-01-24 17:53:47
79                                            fMetasCompras                          origem          135        7199          0       488  2025-01-24 17:53:47   2025-01-24 17:53:47
80                                            fMetasCompras                   categ_fazenda          109        4861          0       768  2025-01-24 17:53:47   2025-01-24 17:53:47
81                                            fMetasCompras                             qtd          212        1736          0       848  2025-01-24 17:53:47   2025-01-24 17:53:47
82                                            fMetasCompras                       peso_vivo          240        1960          0       848  2025-01-24 17:53:47   2025-01-24 17:53:47
83                                            fMetasCompras                      total_peso          420        3400          0       952  2025-01-24 17:53:47   2025-01-24 17:53:47
84                                            fMetasCompras                       valor_cab          330        2680          0       952  2025-01-24 17:53:47   2025-01-24 17:53:47
85                                            fMetasCompras                     VALOR TOTAL          470        3800          0       952  2025-01-24 17:53:47   2025-01-24 17:53:47
86                                            fMetasCompras                         valo_kg          300        2440          0       952  2025-01-24 17:53:47   2025-01-24 17:53:47
87                                            fMetasCompras                    valor_arroba          300        2440          0       952  2025-01-24 17:53:47   2025-01-24 17:53:47
88                                            fMetasCompras                      data_abrev           28         963          0       616  2025-01-24 17:53:47   2025-01-24 17:53:47
89                                            fMetasCompras                    categoria_bi           14         557          0       416  2025-01-24 17:53:47   2025-01-24 17:53:47
90                                            fMetasCompras                            sexo            3         179          0       264  2025-01-24 17:53:47   2025-01-24 17:53:47
91                                            fMetasCompras                     peso_arroba          238        1944          0       848  2025-01-24 17:53:47   2025-01-24 17:53:47
92                                            fMetasCompras                    proprietÁrio           55        3475          0       616  2025-01-24 17:53:47   2025-01-24 17:53:47
93                                            fMetasCompras                         fazenda           76        2645          0       672  2025-01-24 17:53:47   2025-01-24 17:53:47
94                                            fMetasCompras                          retiro           71        2413          0       672  2025-01-24 17:53:47   2025-01-24 17:53:47
95                                            fMetasCompras                        PROP_FAZ           79        6211          0       672  2025-05-23 03:06:55   2025-05-23 03:06:55
96                                            fMetasCompras                      prop_faz 2           79        6211          0       672  2025-07-01 16:43:15   2025-07-01 16:43:15
97                                                fMetasDre                 centro_de_custo           61        3037          0      1760  2025-01-31 17:08:30   2025-01-31 17:08:30
98                                                fMetasDre                      sub_centro          229       12209          0      7216  2025-01-31 17:08:30   2025-01-31 17:08:30
99                                                fMetasDre                           valor        14288      114344          0     91680  2025-01-31 17:08:30   2025-01-31 17:08:30
100                                               fMetasDre                    data_pag_old           97        3031          0     40560  2026-03-09 13:17:51   2025-01-31 17:10:39
101                                               fMetasDre                        operaÇÃo            3         175          0       160  2025-01-31 17:08:30   2025-01-31 17:08:30
102                                               fMetasDre              centro_de_custo_bi           34        1867          0      1168  2025-01-31 17:08:30   2025-01-31 17:08:30
103                                               fMetasDre                   sub_centro_bi          117        7005          0      4608  2025-01-31 17:08:30   2025-01-31 17:08:30
104                                               fMetasDre                         fazenda          116        3887          0     35856  2025-01-31 17:08:30   2025-01-31 17:08:30
105                                               fMetasDre                    proprietÁrio           69        4249          0     30144  2025-01-31 17:08:30   2025-01-31 17:08:30
106                                               fMetasDre                  desembolso-CAT            8         335          0       264  2025-01-31 17:08:30   2025-01-31 17:08:30
107                                               fMetasDre                     custeio-CAT            7         317          0       240  2025-01-31 17:08:30   2025-01-31 17:08:30
108                                               fMetasDre                tipo_custeio-CAT            8         329          0       264  2025-01-31 17:08:30   2025-01-31 17:08:30
109                                               fMetasDre                      Desembolso        12277       98256          0     83240  2026-06-19 20:33:55   2025-01-31 17:44:33
110                                               fMetasDre                             F/V            4         281          0       168  2026-06-19 20:33:55   2025-01-31 17:45:50
111                                               fMetasDre                         Custeio        10991       87968          0     71936  2026-06-19 20:33:55   2025-01-31 17:46:19
112                                               fMetasDre                        prop_faz          126        9467          0     35856  2025-05-26 11:47:56   2025-05-26 11:47:56
113                                               fMetasDre                        data_pag           78         664          0     40560  2026-03-09 13:17:51   2026-03-09 13:18:33
114                                              fMetasEmPe                        operaÇÃo            1         143          0       152  2025-01-24 19:06:38   2025-01-24 19:06:38
115                                              fMetasEmPe                         cliente           19        1089          0       192  2025-01-24 19:06:38   2025-01-24 19:06:38
116                                              fMetasEmPe                        DATA_OLD           68        2159          0       576  2026-03-09 13:17:50   2025-01-24 19:09:30
117                                              fMetasEmPe                       documento            1           0          0       152  2025-01-24 19:06:38   2025-01-24 19:06:38
118                                              fMetasEmPe                   categ_fazenda           97        4829          0       576  2025-01-24 19:06:38   2025-01-24 19:06:38
119                                              fMetasEmPe                             qtd          157        1296          0       624  2025-01-24 19:06:38   2025-01-24 19:06:38
120                                              fMetasEmPe                       peso_vivo          108         904          0       576  2025-01-24 19:06:38   2025-01-24 19:06:38
121                                              fMetasEmPe                  pesovivo_total          239        1952          0       624  2025-01-24 19:06:38   2025-01-24 19:06:38
122                                              fMetasEmPe                    valor_arroba          111         928          0       576  2025-01-24 19:06:38   2025-01-24 19:06:38
123                                              fMetasEmPe                       valor_cab          164        1352          0       624  2025-01-24 19:06:38   2025-01-24 19:06:38
124                                              fMetasEmPe                     faturamento          251        2048          0       624  2025-01-24 19:06:38   2025-01-24 19:06:38
125                                              fMetasEmPe                      data_abrev           25         873          0       464  2025-01-24 19:06:38   2025-01-24 19:06:38
126                                              fMetasEmPe                    categoria_bi           12         499          0       344  2025-01-24 19:06:38   2025-01-24 19:06:38
127                                              fMetasEmPe                            sexo            2         163          0       248  2025-01-24 19:06:38   2025-01-24 19:06:38
128                                              fMetasEmPe                        valor_kg          155        1280          0       624  2025-01-24 19:06:38   2025-01-24 19:06:38
129                                              fMetasEmPe                    proprietÁrio           38        2461          0       440  2025-01-24 19:06:38   2025-01-24 19:06:38
130                                              fMetasEmPe                         fazenda           49        1701          0       528  2025-01-24 19:06:38   2025-01-24 19:06:38
131                                              fMetasEmPe                          retiro           43        1479          0       528  2025-01-24 19:06:38   2025-01-24 19:06:38
132                                              fMetasEmPe                      Peso Morto          239        1952          0       624  2026-06-19 20:33:55   2025-01-31 18:34:27
133                                              fMetasEmPe                        prop_faz           53        4203          0       528  2025-05-26 11:47:56   2025-05-26 11:47:56
134                                              fMetasEmPe                      Total de @          239        1952          0       624  2026-06-19 20:33:55   2026-01-17 12:38:18
135                                              fMetasEmPe                      Peso Total          239        1952          0       624  2026-06-19 20:33:55   2026-01-17 12:41:08
136                                              fMetasEmPe                            DATA           66         568          0       576  2026-03-09 13:17:51   2026-03-09 13:18:56
137                                            fMetasMortes                        operaÇÃo            1         143          0       152  2025-01-31 16:52:53   2025-01-31 16:52:53
138                                            fMetasMortes                            DATA          238        1944          0      7656  2025-01-31 16:52:53   2025-01-31 16:54:30
139                                            fMetasMortes                   categ_fazenda          374       16729          0      7976  2025-01-31 16:52:53   2025-01-31 16:52:53
140                                            fMetasMortes                     carimbo_bez           13         361          0       160  2025-01-31 16:52:53   2025-01-31 16:52:53
141                                            fMetasMortes                             qtd          399        3232          0      7368  2025-01-31 16:52:53   2025-01-31 16:52:53
142                                            fMetasMortes                           causa           36        1333          0       480  2025-01-31 16:52:53   2025-01-31 16:52:53
143                                            fMetasMortes                           LOCAL           66        2597          0       288  2025-01-31 16:52:53   2025-01-31 16:52:53
144                                            fMetasMortes                       peso_vivo          336        2728          0      2696  2025-01-31 16:52:53   2025-01-31 16:52:53
145                                            fMetasMortes                           safra            6         253          0       400  2025-01-31 16:52:53   2025-01-31 16:52:53
146                                            fMetasMortes                      data_abrev           30        1023          0      5152  2025-01-31 16:52:53   2025-01-31 16:52:53
147                                            fMetasMortes                 grupo_categoria            3         195          0       848  2025-01-31 16:52:53   2025-01-31 16:52:53
148                                            fMetasMortes                             era            5         219          0      1200  2025-01-31 16:52:53   2025-01-31 16:52:53
149                                            fMetasMortes                    categoria_bi           15         601          0      1576  2025-01-31 16:52:53   2025-01-31 16:52:53
150                                            fMetasMortes                      peso_total          397        3216          0      2720  2025-01-31 16:52:53   2025-01-31 16:52:53
151                                            fMetasMortes                            sexo            2         163          0       640  2025-01-31 16:52:53   2025-01-31 16:52:53
152                                            fMetasMortes                    proprietÁrio           64        3969          0      4272  2025-01-31 16:52:53   2025-01-31 16:52:53
153                                            fMetasMortes                         fazenda          106        3569          0      6152  2025-01-31 16:52:53   2025-01-31 16:52:53
154                                            fMetasMortes                          retiro           96        3139          0      5944  2025-01-31 16:52:53   2025-01-31 16:52:53
155                                            fMetasMortes                        prop_faz          112        8587          0      6152  2025-05-26 11:47:56   2025-05-26 11:47:56
156                                       fMetasNascimentos                        operaÇÃo            1         153          0       152  2025-01-24 20:26:50   2025-01-24 20:26:50
157                                       fMetasNascimentos                            DATA           96         808          0      1312  2025-01-24 20:26:50   2025-01-29 20:19:53
158                                       fMetasNascimentos                   categ_fazenda           73        3417          0      1312  2025-01-24 20:26:50   2025-01-24 20:26:50
159                                       fMetasNascimentos                             qtd          426        3448          0      1640  2025-01-24 20:26:50   2025-01-24 20:26:50
160                                       fMetasNascimentos                           safra           12         381          0       344  2025-01-24 20:26:50   2025-01-24 20:26:50
161                                       fMetasNascimentos                       peso_nasc           25         240          0       240  2025-01-24 20:26:50   2025-01-24 20:26:50
162                                       fMetasNascimentos                      data_abrev           28         963          0      1024  2025-01-24 20:26:50   2025-01-24 20:26:50
163                                       fMetasNascimentos                    categoria_bi            2         171          0       472  2025-01-24 20:26:50   2025-01-24 20:26:50
164                                       fMetasNascimentos                            sexo            2         163          0       472  2025-01-24 20:26:50   2025-01-24 20:26:50
165                                       fMetasNascimentos                    proprietÁrio           53        3359          0      1024  2025-01-24 20:26:50   2025-01-24 20:26:50
166                                       fMetasNascimentos                         fazenda           81        2687          0      1248  2025-01-24 20:26:50   2025-01-24 20:26:50
167                                       fMetasNascimentos                          retiro           73        2369          0      1248  2025-01-24 20:26:50   2025-01-24 20:26:50
168                                       fMetasNascimentos                        prop_faz           87        6751          0      1248  2025-05-26 11:47:56   2025-05-26 11:47:56
169                                      fMetasRebanhoMedio                 grupo_categoria            3         195          0       400  2025-01-31 17:14:26   2025-01-31 17:14:26
170                                      fMetasRebanhoMedio                         qtd_cab         2952       23656          0      6024  2025-01-31 17:14:26   2025-01-31 17:14:26
171                                      fMetasRebanhoMedio                          qtd_ua         2021       16208          0      4096  2025-01-31 17:14:26   2025-01-31 17:14:26
172                                      fMetasRebanhoMedio                            DATA           36         328          0      3240  2025-01-31 17:14:26   2025-01-31 17:22:12
173                                      fMetasRebanhoMedio                    proprietÁrio           71        4401          0      2696  2025-01-31 17:14:26   2025-01-31 17:14:26
174                                      fMetasRebanhoMedio                         fazenda          120        4029          0      3584  2025-01-31 17:14:26   2025-01-31 17:14:26
175                                      fMetasRebanhoMedio                          retiro          111        3625          0      3328  2025-01-31 17:14:26   2025-01-31 17:14:26
176                                      fMetasRebanhoMedio                        prop_faz          130        9925          0      4016  2025-05-26 11:47:56   2025-05-26 11:47:56
177                                    fMetasTransferencias                        operaÇÃo            2         199          0       152  2026-04-22 21:27:59   2026-04-22 21:27:59
178                                    fMetasTransferencias                            DATA           89         752          0       560  2026-04-22 21:27:59   2026-04-23 01:44:27
179                                    fMetasTransferencias               categoria_fazenda           74        3439          0       560  2026-04-22 21:27:59   2026-04-22 21:27:59
180                                    fMetasTransferencias                             qtd          183           0       4205       896  2026-04-22 21:27:59   2026-04-22 21:27:59
181                                    fMetasTransferencias                       peso_vivo          167        1376          0       616  2026-04-22 21:27:59   2026-04-22 21:27:59
182                                    fMetasTransferencias                      total_peso          254           0       4333      2016  2026-04-22 21:27:59   2026-04-22 21:27:59
183                                    fMetasTransferencias                     VALOR TOTAL          323        2624          0       680  2026-04-22 21:27:59   2026-04-22 21:27:59
184                                    fMetasTransferencias                      data_abrev           28        1691          0       456  2026-04-22 21:27:59   2026-04-22 21:27:59
185                                    fMetasTransferencias                    categoria_bi           12         499          0       384  2026-04-22 21:27:59   2026-04-22 21:27:59
186                                    fMetasTransferencias                            sexo            2         163          0       264  2026-04-22 21:27:59   2026-04-22 21:27:59
187                                    fMetasTransferencias                     peso_arroba          164        1352          0       616  2026-04-22 21:27:59   2026-04-22 21:27:59
188                                    fMetasTransferencias                       valor_cab          163        1344          0       616  2026-04-22 21:27:59   2026-04-22 21:27:59
189                                    fMetasTransferencias                         valo_kg          184        1512          0       616  2026-04-22 21:27:59   2026-04-22 21:27:59
190                                    fMetasTransferencias                    valor_arroba          184        1512          0       616  2026-04-22 21:27:59   2026-04-22 21:27:59
191                                    fMetasTransferencias                    proprietÁrio           25        1497          0       352  2026-04-22 21:27:59   2026-04-22 21:27:59
192                                    fMetasTransferencias                         fazenda           55        1863          0       464  2026-04-22 21:27:59   2026-04-22 21:27:59
193                                    fMetasTransferencias                          retiro           51        1703          0       464  2026-04-22 21:27:59   2026-04-22 21:27:59
194                                    fMetasTransferencias                        prop_faz           57        4159          0       464  2026-04-22 21:27:59   2026-04-22 21:27:59
195                                    fMetasTransferencias                    Peso Total @          297        2416          0       680  2026-06-19 20:33:55   2026-04-26 14:37:37
196                                                fMovGado                      Nascimento            1           0          0       152  2025-01-22 16:30:53   2024-11-01 01:03:48
197                                                fMovGado                           Morte            1           0          0       152  2025-01-22 16:30:53   2024-11-01 01:08:31
198                                                fMovGado                         Inicial          759           0      16525      4664  2026-06-19 20:33:55   2024-11-01 01:10:46
199                                                fMovGado                          Vendas            1          48          0       152  2026-06-19 20:33:55   2024-11-01 01:11:20
..                                                      ...                             ...          ...         ...        ...       ...                  ...                   ...
202                                                fMovGado  Mudança de Categoria (Entrada)            1           0          0       152  2025-01-22 16:30:53   2024-11-01 01:18:25
203                                                fMovGado                Origin Ordenated            1           0          0       152  2025-01-22 16:30:53   2024-11-01 01:36:03
204                                                fMovGado                           QTD C         1750           0      32925     18832  2026-06-19 20:33:55   2025-01-16 19:52:12
205                                                fMovGado                        OPERAÇÃO           11         453          0      1392  2025-01-17 00:28:05   2025-01-17 00:27:01
206                                                fMovGado                             QTD         1611           0      32893     17200  2025-01-17 00:27:01   2025-01-17 00:27:01
207                                                fMovGado                    categoria_bi           15         601          0      5408  2025-01-17 00:27:01   2025-01-17 00:27:01
208                                                fMovGado                            sexo            2         163          0      1480  2025-01-17 00:27:01   2025-01-17 00:27:01
209                                                fMovGado                    proprietÁrio           91        5451          0      9000  2025-01-17 00:27:01   2025-01-17 00:27:01
210                                                fMovGado                         fazenda          191        6145          0     11512  2025-01-17 00:27:01   2025-01-17 00:27:01
211                                                fMovGado                          retiro          180        5657          0     10832  2025-01-17 00:27:01   2025-01-17 00:27:01
212                                                fMovGado                            DATA           28         264          0      6968  2025-01-17 01:59:05   2025-01-18 11:59:56
213                                                fMovGado                        prop_faz          215       15659          0     11512  2025-05-26 13:17:18   2025-05-26 13:17:18
214                                         fTransferencias                        operaÇÃo            2         199          0       392  2026-04-22 01:30:19   2026-04-22 01:30:19
215                                         fTransferencias                            DATA          337        2736          0      2960  2026-04-22 01:30:19   2026-04-22 21:30:41
216                                         fTransferencias               categoria_fazenda          234       11189          0      2264  2026-04-22 01:30:19   2026-04-22 01:30:19
217                                         fTransferencias                             qtd          350           0       8365      4080  2026-04-22 01:30:19   2026-04-22 01:30:19
218                                         fTransferencias                       peso_vivo          573        4624          0      3280  2026-04-22 01:30:19   2026-04-22 01:30:19
219                                         fTransferencias                      total_peso         1088           0      16877      9560  2026-04-22 01:30:19   2026-04-22 01:30:19
220                                         fTransferencias                     VALOR TOTAL          967           0      16781      7312  2026-04-22 01:30:19   2026-04-22 01:30:19
221                                         fTransferencias                      data_abrev           23        1411          0      1720  2026-04-22 01:30:19   2026-04-22 01:30:19
222                                         fTransferencias                    categoria_bi           15         601          0      1208  2026-04-22 01:30:19   2026-04-22 01:30:19
223                                         fTransferencias                            sexo            2         163          0       416  2026-04-22 01:30:19   2026-04-22 01:30:19
224                                         fTransferencias                     peso_arroba          571        4608          0      3280  2026-04-22 01:30:19   2026-04-22 01:30:19
225                                         fTransferencias                       valor_cab          756        6088          0      2536  2026-04-22 01:30:19   2026-04-22 01:30:19
226                                         fTransferencias                         valo_kg          561        4528          0      2224  2026-04-22 01:30:19   2026-04-22 01:30:19
227                                         fTransferencias                    valor_arroba          561        4528          0      2224  2026-04-22 01:30:19   2026-04-22 01:30:19
228                                         fTransferencias                    proprietÁrio           50        2983          0      1112  2026-04-22 01:30:19   2026-04-22 01:30:19
229                                         fTransferencias                         fazenda          132        4141          0      1992  2026-04-22 01:30:19   2026-04-22 01:30:19
230                                         fTransferencias                          retiro          121        3735          0      1744  2026-04-22 01:30:19   2026-04-22 01:30:19
231                                         fTransferencias                        prop_faz          147       10479          0      1992  2026-04-22 01:30:19   2026-04-22 01:30:19
232                                         fTransferencias                    Peso Total @         1185        9520          0      3904  2026-06-19 20:33:55   2026-04-26 14:35:13
233                                               fUnidades                    proprietÁrio           92        5491          0       344  2025-05-27 00:54:37   2025-01-18 13:15:00
234                                               fUnidades                         fazenda          196        6319          0       376  2025-01-18 13:15:00   2025-01-18 13:15:00
235                                               fUnidades                         projeto           93        3513          0       344  2025-04-27 23:00:48   2025-04-27 23:00:48
236                                               fUnidades               SISTEMA PRODUTIVO            3         221          0       168  2025-04-27 23:00:48   2025-04-27 23:00:48
237                                               fUnidades                        PROP_FAZ          224       16247          0       376  2025-05-27 00:54:37   2025-05-27 00:54:37
238                                               fUnidades                  CÓDIGO PROJETO           88        1785          0       344  2025-06-06 15:53:32   2025-06-06 15:53:32
239                                               fUnidades                             ano            2         163          0       160  2025-06-06 15:53:32   2025-06-06 15:53:32
240                                               fUnidades                        filename          224       16553          0       376  2026-06-19 20:14:40   2026-06-19 20:14:40
241                                           financeiroDre                  Type Operation            1           0          0       152  2025-01-22 16:30:53   2024-11-01 03:44:42
242                                           financeiroDre                      Desembolso        28275      226240          0     80304  2026-06-20 22:38:11   2024-11-05 23:01:09
243                                           financeiroDre                         Custeio        24677      197456          0     68280  2026-06-20 22:38:11   2024-11-05 23:45:00
244                                           financeiroDre                 Class subcenter            1           0          0       152  2025-01-22 16:30:53   2024-11-09 00:39:13
245                                           financeiroDre                           valor        31304      250472          0     90616  2025-01-18 13:15:00   2025-01-18 13:15:00
246                                           financeiroDre                        data_pag          676        5448          0     60072  2025-01-18 13:15:00   2025-01-20 11:50:29
247                                           financeiroDre                        operaÇÃo            3         175          0       168  2025-01-18 13:15:00   2025-01-18 13:15:00
248                                           financeiroDre              centro_de_custo_bi           52        2621          0      1384  2025-01-18 13:15:00   2025-01-18 13:15:00
249                                           financeiroDre                   sub_centro_bi          149        8699          0      5304  2025-01-18 13:15:00   2025-01-18 13:15:00
250                                           financeiroDre                         fazenda          173        5635          0     41120  2025-01-18 13:15:00   2025-01-18 13:15:00
251                                           financeiroDre                    proprietÁrio           91        5413          0     30672  2025-01-18 13:15:00   2025-01-18 13:15:00
252                                           financeiroDre                  desembolso-CAT            9         363          0       216  2025-01-18 13:15:00   2025-01-18 13:15:00
253                                           financeiroDre                     custeio-CAT            8         345          0       184  2025-01-18 13:15:00   2025-01-18 13:15:00
254                                           financeiroDre                tipo_custeio-CAT            9         357          0       320  2025-01-18 13:15:00   2025-01-18 13:15:00
255                                           financeiroDre                             F/V            5         315          0       304  2026-06-20 22:38:11   2025-01-20 14:09:03
256                                           financeiroDre                             mes           14         319          0     21936  2025-01-23 19:35:44   2025-01-23 19:35:44
257                                           financeiroDre                             ano            7         249          0      3944  2025-01-23 19:35:44   2025-01-23 19:35:44
258                                           financeiroDre                        prop_faz          196       14159          0     41280  2025-05-26 13:17:18   2025-05-26 13:17:18
259                                           financeiroDre                   Classificacao            6         337          0       664  2026-06-20 22:38:11   2025-11-24 18:53:29
260                                           financeiroDre                          Meta C            1           0          0       152  2026-06-20 22:38:10   2025-11-24 18:53:52
261                                           financeiroDre                         Valor C        31491      251968          0     90616  2026-06-20 22:38:11   2025-11-24 18:54:01
262                                         pecuarioCompras                            Paid            1           0          0       152  2025-01-22 16:30:53   2024-10-22 16:21:53
263                                         pecuarioCompras                        operaÇÃo            1         145          0       152  2025-01-17 01:11:50   2025-01-17 01:11:50
264                                         pecuarioCompras                            DATA          374        3032          0      2104  2025-08-29 20:05:01   2025-01-24 17:57:18
265                                         pecuarioCompras                          origem          787       16506          0      2432  2025-01-17 01:11:50   2025-01-17 01:11:50
266                                         pecuarioCompras                   categ_fazenda          194        8983          0      1376  2025-01-17 01:11:50   2025-01-17 01:11:50
267                                         pecuarioCompras                             qtd          270           0       4293      2888  2025-01-17 01:11:50   2025-01-17 01:11:50
268                                         pecuarioCompras                       peso_vivo          880        7080          0      2432  2025-01-17 01:11:50   2025-01-17 01:11:50
269                                         pecuarioCompras                      total_peso         1402       11256          0      2888  2025-01-17 01:11:50   2025-01-17 01:11:50
270                                         pecuarioCompras                       valor_cab         1023        8224          0      2432  2025-01-17 01:11:50   2025-01-17 01:11:50
271                                         pecuarioCompras                     VALOR TOTAL         1374       11032          0      2888  2025-01-17 01:11:50   2025-01-17 01:11:50
272                                         pecuarioCompras                         valo_kg         1219        9792          0      2888  2025-01-17 01:11:50   2025-01-17 01:11:50
273                                         pecuarioCompras                    valor_arroba         1219        9792          0      2888  2025-01-17 01:11:50   2025-01-17 01:11:50
274                                         pecuarioCompras                      data_abrev           22        1355          0      1288  2025-01-17 01:11:50   2025-01-17 01:11:50
275                                         pecuarioCompras                    categoria_bi           15         593          0       272  2025-01-17 01:11:50   2025-01-17 01:11:50
276                                         pecuarioCompras                            sexo            3         179          0       160  2025-01-17 01:11:50   2025-01-17 01:11:50
277                                         pecuarioCompras                     peso_arroba          878        7064          0      2432  2025-01-17 01:11:50   2025-01-17 01:11:50
278                                         pecuarioCompras                    proprietÁrio           67        4163          0      1248  2025-01-17 01:11:50   2025-01-17 01:11:50
279                                         pecuarioCompras                         fazenda           99        3413          0      1392  2025-01-17 01:11:50   2025-01-17 01:11:50
280                                         pecuarioCompras                          retiro           91        3057          0      1392  2025-01-17 01:11:50   2025-01-17 01:11:50
281                                         pecuarioCompras                      Total de @         1426       11448          0      2888  2026-06-19 20:33:55   2025-05-07 17:50:03
282                                         pecuarioCompras                        prop_faz          105        7885          0      1392  2025-05-26 13:17:18   2025-05-26 13:17:18
283                                          pecuarioMortes                             era            5         219          0      2288  2024-10-21 20:14:53   2024-10-21 20:14:53
284                                          pecuarioMortes                           safra           25         779          0      1320  2024-10-21 20:14:53   2024-10-21 20:14:53
285                                          pecuarioMortes                        forecast           27         148          0       512  2026-06-19 20:33:55   2024-10-31 19:28:34
286                                          pecuarioMortes                        operaÇÃo            1         143          0       152  2025-01-18 11:41:32   2025-01-18 11:41:32
287                                          pecuarioMortes                   categ_fazenda          467        9662          0      7136  2025-01-18 11:41:32   2025-01-18 11:41:32
288                                          pecuarioMortes                     carimbo_bez          217        9961          0      2160  2025-01-18 11:41:32   2025-01-18 11:41:32
289                                          pecuarioMortes                             qtd           27         256          0       512  2025-01-18 11:41:32   2025-01-18 11:41:32
290                                          pecuarioMortes                           causa          308       11837          0      6744  2025-01-18 11:41:32   2025-01-18 11:41:32
291                                          pecuarioMortes                           LOCAL          978       13702          0      5656  2025-01-18 11:41:32   2025-01-18 11:41:32
292                                          pecuarioMortes                       peso_vivo          493        9871          0      6584  2025-06-26 09:54:01   2025-01-18 11:41:32
293                                          pecuarioMortes                      data_abrev           28         963          0      4800  2025-01-18 11:41:32   2025-01-18 11:41:32
294                                          pecuarioMortes                 grupo_categoria            3         195          0      1528  2025-01-18 11:41:32   2025-01-18 11:41:32
295                                          pecuarioMortes                    categoria_bi           15         601          0      3240  2025-01-18 11:41:32   2025-01-18 11:41:32
296                                          pecuarioMortes                      peso_total          632        5096          0      7632  2025-01-18 11:41:32   2025-01-18 11:41:32
297                                          pecuarioMortes                            sexo            2         163          0      1688  2025-01-18 11:41:32   2025-01-18 11:41:32
298                                          pecuarioMortes                    proprietÁrio           88        5307          0      3744  2025-01-18 11:41:32   2025-01-18 11:41:32
299                                          pecuarioMortes                         fazenda          164        5389          0      5240  2025-01-18 11:41:32   2025-01-18 11:41:32
300                                          pecuarioMortes                          retiro          154        4943          0      5008  2025-01-18 11:41:32   2025-01-18 11:41:32
301                                          pecuarioMortes                        prop_faz          185       13789          0      5248  2025-05-26 13:17:18   2025-05-26 13:17:18
302                                          pecuarioMortes                            DATA          628        5064          0      9456  2025-06-02 14:26:08   2025-06-02 14:26:36
303                                          pecuarioMortes                    operaÇÃo_ktl            1           0          0       152  2026-04-22 16:04:49   2026-04-22 16:04:49
304                                          pecuarioMortes               categ_fazenda_ktl            1           0          0       152  2026-04-22 16:04:49   2026-04-22 16:04:49
305                                      pecuarioNascimento                        operaÇÃo            1         153          0       152  2025-01-18 11:21:24   2025-01-18 11:21:24
306                                      pecuarioNascimento                            DATA          397        3216          0      4784  2025-01-18 12:30:29   2025-01-20 11:51:31
307                                      pecuarioNascimento                   categ_fazenda          110        5297          0      3016  2025-01-18 11:21:24   2025-01-18 11:21:24
308                                      pecuarioNascimento                             qtd          253           0       4309      3280  2025-01-18 11:21:24   2025-01-18 11:21:24
309                                      pecuarioNascimento                           safra           13         399          0       640  2025-01-18 11:21:24   2025-01-18 11:21:24
310                                      pecuarioNascimento                       peso_nasc           36         328          0       424  2025-01-18 11:21:24   2025-01-18 11:21:24
311                                      pecuarioNascimento                      data_abrev           28        1691          0      2616  2025-01-18 11:21:24   2025-01-18 11:21:24
312                                      pecuarioNascimento                    categoria_bi            3         203          0      1000  2025-01-18 11:21:24   2025-01-18 11:21:24
313                                      pecuarioNascimento                            sexo            2         163          0       640  2025-01-18 11:21:24   2025-01-18 11:21:24
314                                      pecuarioNascimento                    proprietÁrio           72        4381          0      1960  2025-01-18 11:21:24   2025-01-18 11:21:24
315                                      pecuarioNascimento                         fazenda          131        4351          0      2728  2025-01-18 11:21:24   2025-01-18 11:21:24
316                                      pecuarioNascimento                          retiro          119        3889          0      2264  2025-01-18 11:21:24   2025-01-18 11:21:24
317                                      pecuarioNascimento                        prop_faz          141       10813          0      2728  2025-05-26 13:17:18   2025-05-26 13:17:18
318                              pecuarioRebanhoMedioMensal                            farm            1         163          0       152  2026-06-19 20:33:55   2024-10-31 16:34:05
319                              pecuarioRebanhoMedioMensal                        Forecast         2199       17632          0      4640  2026-06-19 20:33:55   2024-10-31 19:25:15
320                              pecuarioRebanhoMedioMensal                 grupo_categoria            3         195          0       472  2025-01-18 12:28:46   2025-01-18 12:28:46
321                              pecuarioRebanhoMedioMensal                         qtd_cab         2199       17632          0      4640  2025-01-18 12:28:46   2025-01-18 12:28:46
322                              pecuarioRebanhoMedioMensal                          qtd_ua         1737       13936          0      3360  2025-01-18 12:28:46   2025-01-18 12:28:46
323                              pecuarioRebanhoMedioMensal                            DATA           35         320          0      2144  2025-01-18 12:28:46   2025-01-18 12:29:26
324                              pecuarioRebanhoMedioMensal                    proprietÁrio           91        5451          0      1768  2025-01-18 12:28:46   2025-01-18 12:28:46
325                              pecuarioRebanhoMedioMensal                         fazenda          188        6077          0      2952  2025-01-18 12:28:46   2025-01-18 12:28:46
326                              pecuarioRebanhoMedioMensal                          retiro          177        5609          0      2720  2025-01-18 12:28:46   2025-01-18 12:28:46
327                              pecuarioRebanhoMedioMensal                        prop_faz          211       15443          0      2952  2025-05-26 13:35:51   2025-05-26 13:35:51
328                                      pecuarioVendaAbate                     Total Value            1           0          0       152  2025-01-22 16:30:53   2024-10-22 21:25:20
329                                      pecuarioVendaAbate                           teste            1           0          0       152  2025-01-22 16:30:53   2024-10-31 23:05:14
330                                      pecuarioVendaAbate                Peso Morto Total         2144       17192          0      4328  2026-06-19 20:33:55   2024-11-02 13:11:58
331                                      pecuarioVendaAbate                      Total de @         2149       17232          0      4328  2026-06-19 20:33:55   2024-11-02 13:14:13
332                                      pecuarioVendaAbate                       tipovenda            1         143          0       152  2026-06-19 20:33:55   2024-11-05 22:55:45
333                                      pecuarioVendaAbate                        operaÇÃo            1         143          0       152  2025-01-18 11:50:32   2025-01-18 11:50:32
334                                      pecuarioVendaAbate                         cliente          205       10371          0      2632  2025-01-18 11:50:32   2025-01-18 11:50:32
335                                      pecuarioVendaAbate                   categ_fazenda          232       11227          0      2696  2025-01-18 11:50:32   2025-01-18 11:50:32
336                                      pecuarioVendaAbate                            DATA          466        3768          0      3136  2025-01-20 19:25:02   2025-01-18 11:50:32
337                                      pecuarioVendaAbate                             qtd          289           0       8341      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
338                                      pecuarioVendaAbate                             era           27         683          0       312  2025-01-18 11:50:32   2025-01-18 11:50:32
339                                      pecuarioVendaAbate                       peso_vivo         1531       12288          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
340                                      pecuarioVendaAbate                      rendimento          945        7600          0      3632  2025-01-18 11:50:32   2025-01-18 11:50:32
341                                      pecuarioVendaAbate                     peso_arroba         1176        9448          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
342                                      pecuarioVendaAbate                    valor_arroba         1553       12464          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
343                                      pecuarioVendaAbate                     faturamento         2257       18096          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
344                                      pecuarioVendaAbate                    categoria_bi           13         553          0      1040  2025-01-18 11:50:32   2025-01-18 11:50:32
345                                      pecuarioVendaAbate                            sexo            2         163          0       440  2025-01-18 11:50:32   2025-01-18 11:50:32
346                                      pecuarioVendaAbate                      peso_morto         1175        9440          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
347                                      pecuarioVendaAbate                  pesovivo_total         2209       17712          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
348                                      pecuarioVendaAbate                 pesomorto_total         2144       17192          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
349                                      pecuarioVendaAbate                        valor_kg         2147       17216          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
350                                      pecuarioVendaAbate                       valor_cab         2173       17424          0      4328  2025-01-18 11:50:32   2025-01-18 11:50:32
351                                      pecuarioVendaAbate                    proprietÁrio           84        5017          0      1896  2025-01-18 11:50:32   2025-01-18 11:50:32
352                                      pecuarioVendaAbate                         fazenda          143        4677          0      2120  2025-01-18 11:50:32   2025-01-18 11:50:32
353                                      pecuarioVendaAbate                          retiro          132        4213          0      2008  2025-01-18 11:50:32   2025-01-18 11:50:32
354                                      pecuarioVendaAbate                             mes           12         291          0       928  2025-01-22 16:31:55   2025-01-22 16:31:55
355                                      pecuarioVendaAbate                             ano            2         159          0       176  2025-01-22 16:31:55   2025-01-22 16:31:55
356                                      pecuarioVendaAbate                qtd_meta_diluida          255        2080          0      1704  2025-01-22 17:39:54   2025-01-22 17:39:54
357                                      pecuarioVendaAbate                 qtd_meta_mensal          245        2000          0      1712  2025-01-22 17:39:54   2025-01-22 17:39:54
358                                      pecuarioVendaAbate                   diluicao_meta           27         148          0      1192  2025-01-22 17:39:54   2025-01-22 17:39:54
359                                      pecuarioVendaAbate                    meta_diluida          313        2544          0      1904  2025-01-22 17:39:54   2025-01-22 17:39:54
360                                      pecuarioVendaAbate                     meta_mensal          305        2480          0      1936  2025-01-22 17:39:54   2025-01-22 17:39:54
361                                      pecuarioVendaAbate                        prop_faz          156       11595          0      2208  2025-05-26 13:17:18   2025-05-26 13:17:18
362                                       pecuarioVendaEmPe                      Total de @         1032        8296          0      2496  2026-06-19 20:33:55   2024-11-02 13:28:14
363                                       pecuarioVendaEmPe                       tipovenda            1         143          0       152  2026-06-19 20:33:55   2024-11-05 22:56:03
364                                       pecuarioVendaEmPe                      Peso Total         1032        8296          0      2496  2026-06-19 20:33:55   2025-01-11 12:25:22
365                                       pecuarioVendaEmPe                        operaÇÃo            1         141          0       152  2025-01-18 11:50:32   2025-01-18 11:50:32
366                                       pecuarioVendaEmPe                         cliente          692       17302          0      2104  2025-01-18 11:50:32   2025-01-18 11:50:32
367                                       pecuarioVendaEmPe                            DATA          288        2344          0      1824  2025-01-20 19:24:35   2025-01-18 11:50:32
368                                       pecuarioVendaEmPe                   categ_fazenda          203       10573          0      1496  2025-01-18 11:50:32   2025-01-18 11:50:32
369                                       pecuarioVendaEmPe                             qtd          158           0       4205      1448  2025-01-18 11:50:32   2025-01-18 11:50:32
370                                       pecuarioVendaEmPe                       peso_vivo          751        6048          0      2104  2025-01-18 11:50:32   2025-01-18 11:50:32
371                                       pecuarioVendaEmPe                  pesovivo_total         1032        8296          0      2496  2025-01-18 11:50:32   2025-01-18 11:50:32
372                                       pecuarioVendaEmPe                    valor_arroba         1121        9008          0      2496  2025-01-18 11:50:32   2025-01-18 11:50:32
373                                       pecuarioVendaEmPe                       valor_cab          681        5488          0      2104  2025-01-18 11:50:32   2025-01-18 11:50:32
374                                       pecuarioVendaEmPe                     faturamento          900        7240          0      2104  2025-01-18 11:50:32   2025-01-18 11:50:32
375                                       pecuarioVendaEmPe                    categoria_bi           14         577          0       768  2025-01-18 11:50:32   2025-01-18 11:50:32
376                                       pecuarioVendaEmPe                            sexo            2         163          0       392  2025-01-18 11:50:32   2025-01-18 11:50:32
377                                       pecuarioVendaEmPe                        valor_kg         1131        9088          0      2496  2025-01-18 11:50:32   2025-01-18 11:50:32
378                                       pecuarioVendaEmPe                    proprietÁrio           52        3201          0       792  2025-01-18 11:50:32   2025-01-18 11:50:32
379                                       pecuarioVendaEmPe                         fazenda           74        2537          0       864  2025-01-18 11:50:32   2025-01-18 11:50:32
380                                       pecuarioVendaEmPe                          retiro           67        2295          0       840  2025-01-18 11:50:32   2025-01-18 11:50:32
381                                       pecuarioVendaEmPe                      Peso Morto         1032        8296          0      2496  2026-06-19 20:33:55   2025-01-20 21:07:01
382                                       pecuarioVendaEmPe                             mes           12         291          0       416  2025-01-23 01:00:51   2025-01-23 01:00:51
383                                       pecuarioVendaEmPe                             ano            2         159          0       160  2025-01-23 01:00:51   2025-01-23 01:00:51
384                                       pecuarioVendaEmPe                qtd_meta_diluida           70         600          0       616  2025-01-23 01:00:51   2025-01-23 01:00:51
385                                       pecuarioVendaEmPe                 qtd_meta_mensal           62         536          0       568  2025-01-23 01:00:51   2025-01-23 01:00:51
386                                       pecuarioVendaEmPe                   diluicao_meta           22         128          0       504  2025-01-23 01:00:51   2025-01-23 01:00:51
387                                       pecuarioVendaEmPe                    meta_diluida           73         624          0       616  2025-01-23 01:00:51   2025-01-23 01:00:51
388                                       pecuarioVendaEmPe                     meta_mensal           70         600          0       616  2025-01-23 01:00:51   2025-01-23 01:00:51
389                                       pecuarioVendaEmPe                        prop_faz           78        6013          0       864  2025-05-26 13:17:18   2025-05-26 13:17:18
390                                     planejadoXRealizado                        prop_faz          195       14107          0     26584  2025-11-29 19:29:39   2025-11-29 19:29:39
391                                     planejadoXRealizado                    proprietÁrio           91        5413          0     21920  2025-11-29 19:29:39   2025-11-29 19:29:39
392                                     planejadoXRealizado                         fazenda          173        5629          0     26584  2025-11-29 19:29:39   2025-11-29 19:29:39
393                                     planejadoXRealizado              centro_de_custo_bi           53        2651          0      3312  2025-11-29 19:29:39   2025-11-29 19:29:39
394                                     planejadoXRealizado                            data           39         352          0     18568  2025-11-29 19:29:39   2025-11-29 19:44:40
395                                     planejadoXRealizado                            meta         6886       55128          0     41152  2025-11-29 19:29:39   2025-11-29 19:29:39
396                                     planejadoXRealizado                       realizado        10373       83024          0     42224  2025-11-29 19:29:39   2025-11-29 19:29:39
397                                     planejadoXRealizado                  Classificacao2            6         337          0       480  2026-06-19 20:33:55   2025-11-29 19:30:18
398                                     planejadoXRealizado                             F/V            1           0          0       152  2026-06-19 20:33:55   2025-11-29 19:40:13
399                                     planejadoXRealizado                         Valor C        10373       83024          0     42224  2026-06-19 20:33:55   2025-11-29 19:41:17
400                                     planejadoXRealizado                          Meta C         6886       55128          0     41152  2026-06-19 20:33:55   2025-11-29 19:42:14
401                                     planejadoXRealizado                   classificacao            7         375          0       480  2025-11-30 15:02:02   2025-11-30 15:02:02

## Relationships

                 FromTableName FromColumnName ToTableName  ToColumnName  IsActive Cardinality CrossFilteringBehavior  FromKeyCount  ToKeyCount  RelyOnReferentialIntegrity
0           pecuarioVendaAbate      tipovenda      Tabela     TipoVenda         1         M:1                 Single             4         NaN                           0
1            pecuarioVendaEmPe      tipovenda      Tabela     TipoVenda         1         M:1                 Single             4         NaN                           0
2                     fMovGado           DATA   dCalendar          Data         1         M:1                 Single            31         NaN                           0
3           pecuarioVendaAbate           DATA   dCalendar          Data         1         M:1                 Single           469         NaN                           0
4            pecuarioVendaEmPe           DATA   dCalendar          Data         1         M:1                 Single           291         NaN                           0
5   pecuarioRebanhoMedioMensal           DATA   dCalendar          Data         1         M:1                 Single            38         NaN                           0
6           pecuarioNascimento   categoria_bi  Categorias  categoria_bi         1         M:1                 Single             6         NaN                           0
7           pecuarioVendaAbate   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            16         NaN                           0
8            pecuarioVendaEmPe   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            17         NaN                           0
9              pecuarioCompras   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            18         NaN                           0
10              pecuarioMortes   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            18         NaN                           0
11                    fMovGado   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            18         NaN                           0
12               financeiroDre       data_pag   dCalendar          Data         1         M:1                 Single           679         NaN                           0
13          pecuarioNascimento           DATA   dCalendar          Data         1         M:1                 Single           400         NaN                           0
14             pecuarioCompras           DATA   dCalendar          Data         1         M:1                 Single           377         NaN                           0
15               fMetasCompras           DATA   dCalendar          Data         1         M:1                 Single           141         NaN                           0
16                 fMetasAbate   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            14         NaN                           0
17                  fMetasEmPe   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            15         NaN                           0
18                 fMetasAbate       operaÇÃo      Tabela     TipoVenda         1         M:1                 Single             4         NaN                           0
19                  fMetasEmPe       operaÇÃo      Tabela     TipoVenda         1         M:1                 Single             4         NaN                           0
20           fMetasNascimentos           DATA   dCalendar          Data         1         M:1                 Single            99         NaN                           0
21                fMetasMortes           DATA   dCalendar          Data         0         M:1                 Single           241         NaN                           0
22          fMetasRebanhoMedio           DATA   dCalendar          Data         0         M:1                 Single            39         NaN                           0
23          fMetasRebanhoMedio       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           133         NaN                           0
24                   fMetasDre       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           129         NaN                           0
25                fMetasMortes       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           115         NaN                           0
26           fMetasNascimentos       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single            90         NaN                           0
27               fMetasCompras       PROP_FAZ   fUnidades      PROP_FAZ         1         M:1                 Single            82         NaN                           0
28                  fMetasEmPe       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single            56         NaN                           0
29  pecuarioRebanhoMedioMensal       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           214         NaN                           0
30              pecuarioMortes       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           188         NaN                           0
31          pecuarioNascimento       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           144         NaN                           0
32          pecuarioVendaAbate       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           159         NaN                           0
33           pecuarioVendaEmPe       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single            81         NaN                           0
34                    fMovGado       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           218         NaN                           0
35             pecuarioCompras       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           108         NaN                           0
36               financeiroDre       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           199         NaN                           0
37                 fMetasAbate       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           118         NaN                           0
38                         RLS       prop_faz   fUnidades      PROP_FAZ         1         M:1                   Both           299         NaN                           0
39              pecuarioMortes           DATA   dCalendar          Data         1         M:1                 Single           631         NaN                           0
40                       fArea       PROP_FAZ   fUnidades      PROP_FAZ         1         M:1                 Single           227         NaN                           0
41                       fArea           DATA   dCalendar          Data         1         M:1                 Single            39         NaN                           0
42         planejadoXRealizado       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           198         NaN                           0
43         planejadoXRealizado           data   dCalendar          Data         1         M:1                 Single            42         NaN                           0
44                   fMetasDre       data_pag   dCalendar          Data         0         M:1                 Single            81         NaN                           0
45                  fMetasEmPe           DATA   dCalendar          Data         1         M:1                 Single            69         NaN                           0
46                 fMetasAbate           DATA   dCalendar          Data         1         M:1                 Single           181         NaN                           0
47             fTransferencias   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            18         NaN                           0
48             fTransferencias       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single           150         NaN                           0
49        fMetasTransferencias   categoria_bi  Categorias  categoria_bi         1         M:1                 Single            15         NaN                           0
50        fMetasTransferencias       prop_faz   fUnidades      PROP_FAZ         1         M:1                 Single            60         NaN                           0
51             fTransferencias           DATA   dCalendar          Data         1         M:1                 Single           340         NaN                           0
52        fMetasTransferencias           DATA   dCalendar          Data         1         M:1                 Single            92         NaN                           0

## RLS

  TableName   RoleName  RoleDescription          FilterExpression  State  MetadataPermission
0       RLS  Regra RLS              NaN  RLS[e-mail] = USERNAME()      1                   0

## Calculated tables

### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28
```dax
Calendar(Date(2015,1,1), Date(2015,1,1))
```
### Analytics Measures
```dax
Row("Column", BLANK())
```
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04
```dax
Calendar(Date(Year(MIN('dCalendar'[Data])), 1, 1), Date(Year(MAX('dCalendar'[Data])), 12, 31))
```
### Parâmetro - Data
```dax
{
    ("CÍVIL", NAMEOF('dCalendar'[Nome do Mês]), 0),
    ("SAFRA", NAMEOF('dCalendar'[mesano]), 1)
}
```

## Calculated columns

### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28[Ano]
```dax
YEAR([Date])
```
### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28[MonthNo]
```dax
MONTH([Date])
```
### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28[Mês]
```dax
FORMAT([Date], "MMMM")
```
### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28[QuarterNo]
```dax
INT(([MonthNo] + 2) / 3)
```
### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28[Trimestre]
```dax
"Qtr " & [QuarterNo]
```
### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28[Dia]
```dax
DAY([Date])
```
### pecuarioCompras[Paid]
```dax
pecuarioCompras[kgValue] * pecuarioCompras[totalWeight]
```
### dCalendar[Classificador Mês-Ano]
```dax

100 * dCalendar[Ano] + dCalendar[Mês]
```
### pecuarioVendaAbate[Total Value]
```dax
pecuarioVendaAbate[valueWeight] * pecuarioVendaAbate[weightAvg]
```
### pecuarioRebanhoMedioMensal[farm]
```dax
"FAZENDA EXEMPLO"
```
### pecuarioRebanhoMedioMensal[Forecast]
```dax
(pecuarioRebanhoMedioMensal[qtd_cab] * 0.1) + pecuarioRebanhoMedioMensal[qtd_cab]
```
### pecuarioMortes[forecast]
```dax
int((pecuarioMortes[qtd] * 0.8) +  pecuarioMortes[qtd])
```
### pecuarioVendaAbate[teste]
```dax
pecuarioVendaAbate[valueWeight] / 15
```
### fMovGado[Nascimento]
```dax
IF(pecuarioDMG[origin] = "Nascimento",fMovGado[amount],0)
```
### fMovGado[Morte]
```dax
IF(pecuarioDMG[origin] = "Morte",fMovGado[amount],0)
```
### fMovGado[Inicial]
```dax
IF(fMovGado[OPERAÇÃO] = "Saldo Anterior",fMovGado[QTD C],0)
```
### fMovGado[Vendas]
```dax
IF(fMovGado[OPERAÇÃO] = "Venda",fMovGado[QTD C],0)
```
### fMovGado[Type Operation]
```dax

IF(fMovGado[QTD] < 0 ,"Saída",
    IF(
        fMovGado[OPERAÇÃO] IN {  "ABATE",
                                    "Consumo/Doação",
                                    "MORTE",
                                    "EMPÉ",
                                    "Transf. Saida"},"Saída","Entrada"
    )
)
```
### fMovGado[Mudança de Categoria (Saída)]
```dax
IF(pecuarioDMG[originEnum] = "CATEGORY_CHANGE_OUT",fMovGado[amount],0)
```
### fMovGado[Mudança de Categoria (Entrada)]
```dax
IF(pecuarioDMG[originEnum] = "CATEGORY_CHANGE_IN",fMovGado[amount],0)
```
### fMovGado[Origin Ordenated]
```dax

SWITCH(fMovGado[origin],"Saldo Anterior", "1 - Saldo Anterior", "Compra", "2 - Compra")
```
### financeiroDre[Type Operation]
```dax
financeiroDre[Credito/Debito]
```
### pecuarioVendaAbate[Peso Morto Total]
```dax
pecuarioVendaAbate[pesomorto_total]
```
### pecuarioVendaAbate[Total de @]
```dax
pecuarioVendaAbate[peso_arroba] * pecuarioVendaAbate[qtd]
```
### pecuarioVendaEmPe[Total de @]
```dax
pecuarioVendaEmPe[pesovivo_total] / 30
```
### pecuarioVendaAbate[tipovenda]
```dax
"Abate"
```
### pecuarioVendaEmPe[tipovenda]
```dax
"Em Pe"
```
### financeiroDre[Desembolso]
```dax
IF(financeiroDre[desembolso-CAT]="DCM",'financeiroDre'[valor] *-1,0)
```
### financeiroDre[Custeio]
```dax
IF(financeiroDre[custeio-CAT] = "CCM" ,'financeiroDre'[valor] ,0)
```
### financeiroDre[Class subcenter]
```dax

IF('financeiroDre'[subCenter] IN {
                                                    "Compra equipamentos informática, telefonia e comunicação",
                                                    "Novas instalações pecuárias",
                                                    "Novas instalações residenciais",
                                                    "Novas construções, barracões e outros",
                                                    "Novos móveis e eletrodomésticos",
                                                    "Nova rede elétrica",
                                                    "Projetos, medições e outros",
                                                    "Reflorestamento",
                                                    "Solo, contenções, destoca e recuperação",
                                                    "Compra veículos, tratores e implementos",
                                                    "Formação de pasto",
                                                    "Imóveis rurais e urbanos",
                                                    "Investimento em segurança",
                                                    "Nova rede hidráulica",
                                                    "Novas cercas",
                                                    "Novas estradas e pontes",
                                                    "Novas ferramentas e equipamentos",
                                                    " Cursos e treinamentos",
                                                    " Eventos e presentes",
                                                    " Benefícios à funcionarios",
                                                    " Uniformes e EPI",
                                                    " Compra de aves",
                                                    " Compra suínos",
                                                    " Compra tropa de serviço",
                                                    " Compra tropa reprodução",
                                                    " Compra de ovinos"
                                                },"INVESTIMENTOS",
                                                IF('financeiroDre'[subCenter] IN {
                                                        " Aluguéis e Condomínios",
                                                        " Comunicação e energia da fazenda",
                                                        " Contabilidade, jurídico, consultorias e sistemas",
                                                        " Deslocamento, alimentação e hospedagem",
                                                        " Despesa financeira",
                                                        " Despesas casa sede",
                                                        " Outras despesas administrativas",
                                                        " Horta, pomar e jardins",
                                                        " Manutenção rede elétrica",
                                                        " Manutenção rede hidráulica",
                                                        " Manutenção de cercas",
                                                        " Manutenção, construções, barracões e outros",
                                                        " Manutenção em segurança",
                                                        " Manutenção estradas e pontes",
                                                        " Manutenção ferramentas e equipamentos",
                                                        " Manutenção informática",
                                                        " Manutenção instalações pecuárias",
                                                        " Manutenção instalações residenciais",
                                                        " Manutenção móveis e eletrodomésticos",
                                                        " Combustíveis",
                                                        " Manutenção e conserto de máquinas e implementos",
                                                        " Seguros, impostos, multas e outros",
                                                        " Custeio de aves",
                                                        " Custeio tropa reprodução",
                                                        " Ovinos",
                                                        " Suínos",
                                                        " Taxas e impostos",
                                                        " Taxas e impostos. S/Venda",
                                                        " Taxas e impostos S/Lucro",
                                                        " Taxas, Impostos Sobre Propriedade, ITR, IPTU"
                                                    },"MAO DE OBRA PERMANENTE",
                                                    IF('financeiroDre'[subCenter] IN {
                                                            " Colheita e transporte",
                                                            " Corretivos, fertilizantes e adubos",
                                                            " Defensivos",
                                                            " Despesas comerciais e outras",
                                                            " Parceria agrícola",
                                                            " Sementes/Mudas, tratamentos e serviços",
                                                            " Energia para irrigação agrícola",
                                                            " Aluguel de Máquinas Terceirizadas",
                                                            " Preparo de Solo "
                                                            },"DESPESAS COM ATIVIDADES PRODUTIVAS",
                                                            IF('financeiroDre'[subCenter] IN {
                                                                    "Colheita e transporte",
                                                                    "Corretivos, fertilizantes e adubos",
                                                                    "Defensivos",
                                                                    "Despesas comerciais e outras",
                                                                    "Parceria agrícola",
                                                                    "Sementes/Mudas, tratamentos e serviços",
                                                                    "Energia para irrigação agrícola",
                                                                    "Aluguel de Máquinas Terceirizadas",
                                                                    "Preparo de Solo ",
                                                                    "Arrendamento de pastagem"	,
                                                                    "Manutenção de pastagem",                                                                           
                                                                    "Despesas comercias, fretes e comissões"	,
                                                                    "Identificação animal e rastreamento"	,
                                                                    "Nutrição"	,
                                                                    "Reprodução"	,
                                                                    "Sanidade"	,
                                                                    "Melhoramento genético"	,
                                                                    "Energia para irrigação pecuária"
                                                                    },"DESPESAS COM ATIVIDADES PRODUTIVAS","DEMAIS DESPESAS"
                                                            )
                                                        )
                                                )
)
```
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04[Ano]
```dax
YEAR([Date])
```
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04[MonthNo]
```dax
MONTH([Date])
```
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04[Mês]
```dax
FORMAT([Date], "MMMM")
```
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04[QuarterNo]
```dax
INT(([MonthNo] + 2) / 3)
```
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04[Trimestre]
```dax
"Qtr " & [QuarterNo]
```
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04[Dia]
```dax
DAY([Date])
```
### pecuarioVendaEmPe[Peso Total]
```dax
pecuarioVendaEmPe[pesovivo_total]
```
### fMovGado[QTD C]
```dax
IF(fMovGado[QTD] < 0, fMovGado[QTD], IF(fMovGado[Type Operation] = "Entrada",fMovGado[QTD],fMovGado[QTD] * -1))
```
### financeiroDre[F/V]
```dax
IF(financeiroDre[tipo_custeio-CAT] IN {"Receita Pec","Receita outras","Receita Agr"}, "A - RECEITAS",
        IF(financeiroDre[tipo_custeio-CAT] = "CF","B - CUSTO FIXO",
            IF(financeiroDre[tipo_custeio-CAT] = "CV","C - CUSTO VARIAVEL",
                IF(financeiroDre[tipo_custeio-CAT] = "Financiamentos","D - FINANCIAMENTOS","VERIFICAR"

                )
            )
        )
    )
```
### pecuarioVendaEmPe[Peso Morto]
```dax
pecuarioVendaEmPe[pesovivo_total] / 30
```
### fMetasDre[Desembolso]
```dax
IF(fmetasDre[desembolso-CAT]="DCM",'fmetasDre'[valor] *-1,0)
```
### fMetasDre[F/V]
```dax
IF(fMetasDre[tipo_custeio-CAT] IN {"Receita Pec","Receita outras","Receita Agr"}, "A - RECEITAS",
        IF(fMetasDre[tipo_custeio-CAT] = "CF","B - CUSTO FIXO",
            IF(fMetasDre[tipo_custeio-CAT] = "CV","C - CUSTO VARIAVEL",
                IF(fMetasDre[tipo_custeio-CAT] = "Financiamentos","D - FINANCIAMENTOS","VERIFICAR"

                )
            )
        )
    )
```
### fMetasDre[Custeio]
```dax
IF(fmetasDre[custeio-CAT] = "CCM" ,'fmetasDre'[valor] ,0)
```
### fMetasEmPe[Peso Morto]
```dax
fMetasEmPe[pesovivo_total] / 30
```
### fMetasAbate[Peso Morto Total]
```dax
fMetasAbate[pesomorto_total]
```
### pecuarioCompras[Total de @]
```dax
pecuarioCompras[peso_arroba] * pecuarioCompras[qtd]
```
### financeiroDre[Classificacao]
```dax

SWITCH(financeiroDre[centro_de_custo_bi],
        "Arrendamento","A - RECEITAS",
        "Cultura - Receita","A - RECEITAS",
        "Rebanho","A - RECEITAS",
        "Receitas financeiras","A - RECEITAS",
        "Receitas outros","A - RECEITAS",
        "Receitas Parque de máquinas","A - RECEITAS",
        "Vendas outros animais","A - RECEITAS",
        "Investimentos em infraestrutura","B - INVESTIMENTOS",
        "Investimentos em outros animais","B - INVESTIMENTOS",
        "Investimentos em RH","B - INVESTIMENTOS",
        "Rebanho Investimento","B - INVESTIMENTOS",
        "Algodão","C - CUSTEIO",
        "Aveia","C - CUSTEIO",
        "Feno","C - CUSTEIO",
        "Forrageiras e Culturas Anuais","C - CUSTEIO",
        "Insumos do rebanho","C - CUSTEIO",
        "Manutenção da fazenda","C - CUSTEIO",
        "Mão de Obra Geral","C - CUSTEIO",
        "Mão de Obra Permanente Administração","C - CUSTEIO",
        "Mão de Obra Permanente Cultura","C - CUSTEIO",
        "Mão de Obra Permanente Manutenção da Fazenda","C - CUSTEIO",
        "Mão de Obra Permanente Parque de Máquinas","C - CUSTEIO",
        "Mão de Obra Permanente Rebanho","C - CUSTEIO",
        "Milho Safrinha","C - CUSTEIO",
        "Milho Verão","C - CUSTEIO",
        "Outros animais","C - CUSTEIO",
        "Pastagens","C - CUSTEIO",
        "Silagem de Capiaçu","C - CUSTEIO",
        "Silagem de Capim","C - CUSTEIO",
        "Silagem de Milheto","C - CUSTEIO",
        "Silagem de Milho","C - CUSTEIO",
        "Silagem de Sorgo","C - CUSTEIO",
        "Soja","C - CUSTEIO",
        "Sorgo Grão","C - CUSTEIO",
        "Suporte à Produção Administração","C - CUSTEIO",
        "Suporte à Produção Parque de máquinas","C - CUSTEIO",
        "Taxas e impostos","C - CUSTEIO",
        "Empréstimos sócios crédito","D - OUTROS CRÉDITOS",
        "Financiamentos créditos","D - OUTROS CRÉDITOS",
        "Dividendos","E - OUTROS DÉBITOS",
        "Empréstimos sócios débito","E - OUTROS DÉBITOS",
        "Financiamentos débitos","E - OUTROS DÉBITOS",
        "Outros Débitos","E - OUTROS DÉBITOS",
        "Almoxarifado","",
        "Aporte de capital","",
        "Prejuízo Administração","",
        "Venda de Imóveis",""
)
```
### financeiroDre[Meta C]
```dax
IF(financeiroDre[F/V] <> "A - RECEITAS",financeiroDre[meta] * -1,financeiroDre[meta])
```
### financeiroDre[Valor C]
```dax
IF(financeiroDre[F/V] <> "A - RECEITAS",financeiroDre[valor] * -1,financeiroDre[valor])
```
### planejadoXRealizado[Classificacao2]
```dax

SWITCH(planejadoXRealizado[centro_de_custo_bi],
        "Arrendamento","A - RECEITAS",
        "Cultura - Receita","A - RECEITAS",
        "Rebanho","A - RECEITAS",
        "Receitas financeiras","A - RECEITAS",
        "Receitas outros","A - RECEITAS",
        "Receitas Parque de máquinas","A - RECEITAS",
        "Vendas outros animais","A - RECEITAS",
        "Investimentos em infraestrutura","B - INVESTIMENTOS",
        "Investimentos em outros animais","B - INVESTIMENTOS",
        "Investimentos em RH","B - INVESTIMENTOS",
        "Rebanho Investimento","B - INVESTIMENTOS",
        "Algodão","C - CUSTEIO",
        "Aveia","C - CUSTEIO",
        "Feno","C - CUSTEIO",
        "Forrageiras e Culturas Anuais","C - CUSTEIO",
        "Insumos do rebanho","C - CUSTEIO",
        "Manutenção da fazenda","C - CUSTEIO",
        "Mão de Obra Geral","C - CUSTEIO",
        "Mão de Obra Permanente Administração","C - CUSTEIO",
        "Mão de Obra Permanente Cultura","C - CUSTEIO",
        "Mão de Obra Permanente Manutenção da Fazenda","C - CUSTEIO",
        "Mão de Obra Permanente Parque de Máquinas","C - CUSTEIO",
        "Mão de Obra Permanente Rebanho","C - CUSTEIO",
        "Milho Safrinha","C - CUSTEIO",
        "Milho Verão","C - CUSTEIO",
        "Outros animais","C - CUSTEIO",
        "Pastagens","C - CUSTEIO",
        "Silagem de Capiaçu","C - CUSTEIO",
        "Silagem de Capim","C - CUSTEIO",
        "Silagem de Milheto","C - CUSTEIO",
        "Silagem de Milho","C - CUSTEIO",
        "Silagem de Sorgo","C - CUSTEIO",
        "Soja","C - CUSTEIO",
        "Sorgo Grão","C - CUSTEIO",
        "Suporte à Produção Administração","C - CUSTEIO",
        "Suporte à Produção Parque de máquinas","C - CUSTEIO",
        "Taxas e impostos","C - CUSTEIO",
        "Empréstimos sócios crédito","D - OUTROS CRÉDITOS",
        "Financiamentos créditos","D - OUTROS CRÉDITOS",
        "Dividendos","E - OUTROS DÉBITOS",
        "Empréstimos sócios débito","E - OUTROS DÉBITOS",
        "Financiamentos débitos","E - OUTROS DÉBITOS",
        "Outros Débitos","E - OUTROS DÉBITOS",
        "Almoxarifado","",
        "Aporte de capital","",
        "Prejuízo Administração","",
        "Venda de Imóveis",""
)
```
### planejadoXRealizado[F/V]
```dax
/*IF(planejadoXRealizado[tipo_custeio-CAT] IN {"Receita Pec","Receita outras","Receita Agr"}, "A - RECEITAS",
        IF(planejadoXRealizado[tipo_custeio-CAT] = "CF","B - CUSTO FIXO",
            IF(planejadoXRealizado[tipo_custeio-CAT] = "CV","C - CUSTO VARIAVEL",
                IF(planejadoXRealizado[tipo_custeio-CAT] = "Financiamentos","D - FINANCIAMENTOS","VERIFICAR"

                )
            )
        )
    )*/
    --planejadoXRealizado[custeio]
```
### planejadoXRealizado[Valor C]
```dax

planejadoXRealizado[realizado]
--IF(planejadoXRealizado[F/V] <> "A - RECEITAS",planejadoXRealizado[realizado] * -1,planejadoXRealizado[realizado])
```
### planejadoXRealizado[Meta C]
```dax

planejadoXRealizado[meta]

--IF(planejadoXRealizado[F/V] <> "A - RECEITAS",planejadoXRealizado[meta] * -1,planejadoXRealizado[meta])
```
### dCalendar[Safra Abreviada]
```dax
MID(dCalendar[safra],9,5)
```
### fMetasEmPe[Total de @]
```dax
fMetasEmPe[pesovivo_total] / 30
```
### fMetasEmPe[Peso Total]
```dax
fMetasEmPe[pesovivo_total]
```
### fMetasAbate[Total de @]
```dax
fMetasAbate[peso_arroba] * fMetasAbate[qtd]
```
### fTransferencias[Peso Total @]
```dax
fTransferencias[peso_arroba] * fTransferencias[qtd]
```
### fMetasTransferencias[Peso Total @]
```dax
fMetasTransferencias[peso_arroba] * fMetasTransferencias[qtd]
```

## Measures

### Analytics Measures[Purchased Quantity]  folder=Purchase Measures
```dax

CALCULATE(SUM(pecuarioCompras[qtd]))
```
### Analytics Measures[Total Paid]  folder=Purchase Measures
```dax

CALCULATE(SUM(pecuarioCompras[VALOR TOTAL]))+0
```
### Analytics Measures[Purchase Quantity]  folder=Purchase Measures
```dax
COUNTROWS(pecuarioCompras)
```
### Analytics Measures[Dead KG Amount]  folder=Dead Measures
```dax

CALCULATE(SUM(pecuarioMortes[peso_total]))
```
### Analytics Measures[Dead Quantity]  folder=Dead Measures
```dax
SUM(pecuarioMortes[qtd])
```
### Analytics Measures[Birth Quantity]  folder=Birth Measures
```dax
CALCULATE(SUM(pecuarioNascimento[qtd]))+0
```
### Analytics Measures[Average Birth Weight]  folder=Birth Measures
```dax
CALCULATE(SUM(pecuarioNascimento[peso_nasc])) /  CALCULATE(SUM(pecuarioNascimento[qtd])) 
```
### Analytics Measures[Expenses]  folder=Finance Measures
```dax
CALCULATE(
                     SUM('financeiroDre'[valor]),
                     'financeiroDre'[operaÇÃo]="D"--,
                    -- pecuarioRebanhoMedioMensal[amount] > 0
                     ) * -1
```
### Analytics Measures[Revenues]  folder=Finance Measures
```dax
CALCULATE(SUM('financeiroDre'[valor]),'financeiroDre'[operaÇÃo]="C",financeiroDre[tipo_custeio-CAT] IN {"Receita Pec", "Receita Agr"})
```
### Analytics Measures[Balance]  folder=Finance Measures
```dax
[All Revenues] + [Expenses]
```
### Analytics Measures[% Resultado]  folder=Finance Measures
```dax
DIVIDE([Balance],[Expenses]*-1)
```
### Analytics Measures[Finance Indicator]  folder=Finance Measures
```dax

IF([% Resultado] > 0, 1, 
   IF([% Resultado] < 0, -1, 0))
```
### Analytics Measures[Amount Saled]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaEmPe[qtd])+SUM(pecuarioVendaAbate[qtd])
```
### Analytics Measures[Invoicing]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaEmPe[Faturamento])+SUM(pecuarioVendaAbate[Faturamento])
```
### Analytics Measures[AVG Price @ Dead Sale]  folder=IN - Medidas Abate
```dax

CALCULATE(SUM(pecuarioVendaAbate[Faturamento]) / (SUM(pecuarioVendaAbate[Total de @])))
```
### Analytics Measures[AVG Price @ Sale Venda em Pe]  folder=IN - Medidas Venda Em Pe
```dax

CALCULATE(SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[Total de @]))+0
```
### Analytics Measures[AVG Ticket Dead Sale]  folder=IN - Medidas Abate
```dax
SUM(pecuarioVendaAbate[Faturamento]) / SUM(pecuarioVendaAbate[qtd])
```
### Analytics Measures[AVG Ticket Sale]  folder=IN - Medidas Venda Em Pe
```dax
SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[qtd])
```
### Analytics Measures[Expenses Graph]  folder=Finance Measures
```dax
CALCULATE(SUM('financeiroDre'[valor]),'financeiroDre'[operaÇÃo]="D") 
```
### Analytics Measures[Accumulated Death]  folder=Dead Measures
```dax

 VAR calc1 = 
   CALCULATE(
        [Dead Quantity],
        FILTER(
            ALL(dCalendar),  // Remove todos os filtros da tabela de calendário
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  // Garante que o cálculo seja feito apenas dentro do ano corrente
        )
    )
VAR calc2 = 
    CALCULATE(
        [Dead Quantity],
        FILTER(
            ALL(dCalendar),  // Remove todos os filtros de data
            dCalendar[Data] <= MAX(dCalendar[Data])  // Inclui todas as datas até a data máxima no contexto
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)
```
### Analytics Measures[Const Death]  folder=Dead Measures
```dax

    CALCULATE(
        [Dead Quantity],
            ALLEXCEPT(dCalendar,dCalendar[Ano])

    )
```
### Analytics Measures[Count of Selected Years]  folder=Dead Measures
```dax

    CALCULATE(
        DISTINCTCOUNT(dCalendar[Ano]),
        ALLSELECTED(dCalendar)
    )
```
### Analytics Measures[% Death Accumulated]  folder=Dead Measures
```dax
DIVIDE([Accumulated Death],[Const Death])
```
### Analytics Measures[head outlay mOm]  folder=Head Outlay
```dax

(CALCULATE(DIVIDE([Outlay],[Mean Month])) * -1) / [Count of Selected Month]
```
### Analytics Measures[head outlay accumulated]  folder=Head Outlay
```dax

(DIVIDE([Expenses Accumulated], [Mean Month Accumulated - Aux (Desembolso)], 0) *-1) / [Count of Selected Month] + 0
```
### Analytics Measures[Expenses Accumulated]  folder=Head Outlay
```dax

VAR UltimoDiaDoMesContexto = MAX('dCalendar'[Data]) 
VAR DataLimite = EOMONTH(UltimoDiaDoMesContexto, 0)

RETURN
CALCULATE(
    [Outlay],
    FILTER(
        ALLSELECTED('dCalendar'),
        'dCalendar'[Data] <= DataLimite
    )
)
```
### Analytics Measures[Mean Month]  folder=Head Outlay
```dax
CALCULATE( SUM(pecuarioRebanhoMedioMensal[qtd_cab]) / [Count of Selected Month])
```
### Analytics Measures[Mean Month Accumulated]  folder=Head Outlay
```dax

 VAR calc1 = 
   CALCULATE(
        [Mean Month],
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Mean Month],
        FILTER(
            ALLSELECTED(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2) / [Count of Selected Month]
```
### Analytics Measures[head outlay mOm (forecast)]  folder=Head Outlay
```dax

(CALCULATE(DIVIDE([Outlay Forecast],[Mean Month - forecast])) * -1) / [Count of Selected Month]
```
### Analytics Measures[Dead Quantity forecast]  folder=Dead Measures
```dax

CALCULATE(SUM(fMetasMortes[qtd]),USERELATIONSHIP(dCalendar[Data],fMetasMortes[DATA]))
```
### Analytics Measures[% Forecast Indicator]  folder=Dead Measures
```dax
DIVIDE([Dead Quantity forecast],SUM(pecuarioRebanhoMedioMensal[forecast]))
```
### Analytics Measures[% Realized Indicator]  folder=Dead Measures
```dax
DIVIDE([Dead Quantity],SUM(pecuarioRebanhoMedioMensal[qtd_cab]))
```
### Analytics Measures[Dead Quantity Accumulated]  folder=Dead Measures
```dax

    CALCULATE(
        [Dead Quantity],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )

            
```
### Analytics Measures[% Realized Indicator Accumulated]  folder=Dead Measures
```dax

DIVIDE([Dead Quantity Accumulated], ([Mean Month Accumulated]/[Count Mean Month Accumulated]), 0) 
```
### Analytics Measures[Dead Quantity Accumulated - Forecast]  folder=Dead Measures
```dax

    CALCULATE(
        [Dead Quantity forecast],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[Mean Month Accumulated - Forecast]  folder=Head Outlay
```dax

    CALCULATE(
        SUM(pecuarioRebanhoMedioMensal[Forecast]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        ),pecuarioRebanhoMedioMensal[Forecast] <> BLANK()
    )
```
### Analytics Measures[% Forecast Indicator Accumulated]  folder=Dead Measures
```dax

CALCULATE(DIVIDE([Dead Quantity Accumulated - Forecast], ([Mean Month Accumulated - Forecast]/[Count Mean Month Accumulated]), 0) )
```
### Analytics Measures[Total de @]  folder=IN - General Sales Measures
```dax

[Arroba Value] * [Amount Saled]
```
### Analytics Measures[Arroba Value]  folder=IN - General Sales Measures
```dax
--SUM(pecuarioVendaAbate[ArrobaAVG]) + SUM(pecuarioVendaEmPe[arrobaAvg])
```
### Analytics Measures[Amount Saled - Forecast]  folder=IN - General Sales Measures
```dax


VAR calc1 = CALCULATE(SUM(fMetasAbate[qtd]))

VAR calc2 = CALCULATE(SUM(fMetasEmPe[qtd]))

RETURN calc1+calc2
```
### Analytics Measures[Incoicing - Forecast]  folder=IN - General Sales Measures
```dax


VAR calc1 = CALCULATE(SUM(fMetasAbate[faturamento]))

VAR calc2 = CALCULATE(SUM(fMetasEmPe[faturamento]))

RETURN calc1+calc2
```
### Analytics Measures[% Death x Death Forecast]  folder=Dead Measures
```dax
DIVIDE([Dead Quantity],[Dead Quantity forecast])
```
### Analytics Measures[Dead Quantity (Teens)]  folder=Dead Measures
```dax
CALCULATE(SUM(pecuarioMortes[qtd]),pecuarioMortes[grupo_categoria] = "JOVENS")
```
### Analytics Measures[Dead Quantity (Adults)]  folder=Dead Measures
```dax
CALCULATE(SUM(pecuarioMortes[qtd]),pecuarioMortes[grupo_categoria] = "ADULTOS")
```
### Analytics Measures[Dead Quantity (Calves)]  folder=Dead Measures
```dax
CALCULATE(SUM(pecuarioMortes[qtd]),pecuarioMortes[grupo_categoria] = "BEZERROS")
```
### Analytics Measures[head outlat accumulated - forecast]  folder=Head Outlay
```dax

(DIVIDE([Expenses Accumulated - Forecast], [Mean Month Accumulated - Aux (Desembolso) - Forecast], 0) *-1) / [Count of Selected Month] + 0
```
### Analytics Measures[Mean Month - forecast]  folder=Head Outlay
```dax

CALCULATE(
        SUM(fMetasRebanhoMedio[qtd_cab]) / [Count of Selected Month],
        USERELATIONSHIP(dCalendar[Data],fMetasRebanhoMedio[DATA])
        )
```
### Analytics Measures[Stock]  folder=Stock Measures
```dax
SUM(fMovGado[QTD C])
```
### Analytics Measures[Stock Accumulated Inicial]  folder=Stock Measures
```dax

    CALCULATE(
        [Stock],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] < EOMONTH(MIN(dCalendar[Data]), -1) + 1
            
        )
    )
```
### Analytics Measures[Stock Accumulated Final]  folder=Stock Measures
```dax

CALCULATE(
    [Stock],
    FILTER(
        ALL(dCalendar), -- Remove filtros de dCalendar, permitindo acumular dados retroativos
        dCalendar[Data] <= MAX(dCalendar[Data])
    )
)
```
### Analytics Measures[Buy]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "COMPRA")
```
### Analytics Measures[Sell]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] IN {"EMPÉ","ABATE"})
```
### Analytics Measures[Birth]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "NASCIMENTO")
```
### Analytics Measures[Change Category entry]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Mud. de Categoria", fMovGado[Type Operation] = "Entrada")
```
### Analytics Measures[Death]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "MORTE")
```
### Analytics Measures[comsuption / donation]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Consumo/Doação")
```
### Analytics Measures[Weaning Exit]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "DESMAME",fMovGado[Type Operation] = "Saída")
```
### Analytics Measures[Change Category exit]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Mud. de Categoria", fMovGado[Type Operation] = "Saída")
```
### Analytics Measures[Weaning Entry]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Desmame",fMovGado[Type Operation] = "Entrada")
```
### Analytics Measures[Invoicing Accumulated]  folder=IN - General Sales Measures
```dax

    CALCULATE(
        [Invoicing],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )

/* Invoicing Accumulated = 
VAR calc1 =
    CALCULATE(
        SUM(pecuarioVendaAbate[Total Value]),
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )

VAR calc2 =
    CALCULATE(
        SUM(pecuarioVendaEmPe[totalValue]),
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )

RETURN calc1+calc2*/
```
### Analytics Measures[Forecast Accumulated]  folder=IN - General Sales Measures
```dax

    CALCULATE(
        [Incoicing - Forecast],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[Amount Head Saled Accumulated]  folder=IN - General Sales Measures
```dax

    CALCULATE(
        [Amount Saled],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[Amount Head Saled - Forecast Accumulated]  folder=IN - General Sales Measures
```dax

    CALCULATE(
        [Amount Saled - Forecast],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[Count Mean Month]  folder=Dead Measures
```dax

 VAR calc1 = 
   CALCULATE(
        COUNTROWS(pecuarioRebanhoMedioMensal),
        FILTER(
            ALL(dCalendar),  // Remove todos os filtros da tabela de calendário
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  // Garante que o cálculo seja feito apenas dentro do ano corrente
        )
    )
VAR calc2 = 
    CALCULATE(
        COUNTROWS(pecuarioRebanhoMedioMensal),
        FILTER(
            ALL(dCalendar),  // Remove todos os filtros de data
            dCalendar[Data] <= MAX(dCalendar[Data])  // Inclui todas as datas até a data máxima no contexto
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)
```
### Analytics Measures[Count Mean Month Accumulated]  folder=Head Outlay
```dax

   CALCULATE(
        DISTINCTCOUNT(dCalendar[mesano]),
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) --&&
           -- YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
/*
 VAR calc1 = 
   CALCULATE(
        DISTINCTCOUNT(dCalendar[mesano]),
        FILTER(
            ALL(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        DISTINCTCOUNT(dCalendar[mesano]),
        FILTER(
            ALL(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)*/
```
### Analytics Measures[Rendimento Carcaça]  folder=IN - Medidas Abate
```dax
SUM(pecuarioVendaAbate[pesomorto_total]) / SUM(pecuarioVendaAbate[pesovivo_total])
```
### Analytics Measures[Peso em @ Abate]  folder=IN - Medidas Abate
```dax

(SUM(pecuarioVendaAbate[Peso Morto Total]) / 15 ) / SUM(pecuarioVendaAbate[qtd])
```
### Analytics Measures[AVG Price @]  folder=IN - General Sales Measures
```dax
[AVG Price @ Dead Sale] + [AVG Price @ Sale Venda em Pe]
```
### Analytics Measures[Peso em @ Em Pe]  folder=IN - Medidas Venda Em Pe
```dax

(SUM( pecuarioVendaEmPe[pesovivo_total])/30) / SUM(pecuarioVendaEmPe[qtd])+0
```
### Analytics Measures[Peso em @]  folder=IN - General Sales Measures
```dax


VAR totalArroba = (SUM(pecuarioVendaAbate[Peso Morto Total]) / 15) + (SUM( pecuarioVendaEmPe[pesovivo_total])/30)

VAR totalCabecaVendida = SUM(pecuarioVendaAbate[qtd]) + SUM(pecuarioVendaEmPe[qtd])


RETURN totalArroba / totalCabecaVendida
```
### Analytics Measures[Outlay]  folder=Finance Measures
```dax

CALCULATE(SUM(financeiroDre[Desembolso])) +0
```
### Analytics Measures[% Atingido Faturamento]  folder=IN - General Sales Measures
```dax
DIVIDE([Invoicing],[Incoicing - Forecast]) + 0
```
### Analytics Measures[Rebanho Median Month]  folder=nan
```dax
--DIVIDE([],[Count Mean Month Accumulated])
```
### Analytics Measures[UA Median Month]  folder=Purchase Measures
```dax
[Mean Month Accumulated - UA]
```
### Analytics Measures[Mean Month Accumulated - UA]  folder=Head Outlay
```dax

 VAR calc1 = 
   CALCULATE(
        [Mean Month - UA],
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Mean Month - UA],
        FILTER(
            ALLSELECTED(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2) / [Count of Selected Month]
```
### Analytics Measures[Mean Month - UA]  folder=Head Outlay
```dax
SUM(pecuarioRebanhoMedioMensal[qtd_ua])
```
### Analytics Measures[Costing]  folder=Head Outlay
```dax
SUM('financeiroDre'[Custeio])
```
### Analytics Measures[Costing Accumulated]  folder=Head Outlay
```dax

VAR UltimoDiaDoMesContexto = MAX(dCalendar[Data])
VAR DataLimite = EOMONTH(UltimoDiaDoMesContexto, 0)

RETURN
    CALCULATE(
        [Costing],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= DataLimite
        )
    )
```
### Analytics Measures[Costing head Accumulated]  folder=Head Outlay
```dax

DIVIDE([Costing Accumulated], ([Mean Month Accumulated - Aux (Desembolso)]), 0) / [Count of Selected Month] + 0
```
### Analytics Measures[Costing Head accumulated - forecast]  folder=Head Outlay
```dax

DIVIDE([Costing Accumulated - Forecast], ([Mean Month Accumulated - Aux (Desembolso) - Forecast]), 0) / [Count of Selected Month] + 0
```
### Analytics Measures[AVG Price @ (Em Pe + Abate)]  folder=IN - General Sales Measures
```dax

VAR fat = SUM(pecuarioVendaAbate[Faturamento]) + SUM(pecuarioVendaEmPe[Faturamento])

VAR arr = (SUM(pecuarioVendaAbate[Peso Morto Total])/15) + SUM(pecuarioVendaEmPe[Peso Morto])

RETURN fat / arr
```
### Analytics Measures[AVG Price @ Dead Sale - Forecast]  folder=IN - Medidas Abate
```dax

CALCULATE(SUM(fMetasAbate[Faturamento]) / (SUM(fMetasAbate[Total de @])))
```
### Analytics Measures[AVG Price @ Sale Venda em Pe - Forecast]  folder=IN - Medidas Venda Em Pe
```dax

CALCULATE(SUM(fMetasEmPe[Faturamento]) / SUM(fMetasEmPe[Total de @]))+0
```
### Analytics Measures[Birth Quantity - Forecast]  folder=Birth Measures
```dax

CALCULATE(SUM(fMetasNascimentos[qtd]),
         USERELATIONSHIP(dCalendar[Data],fMetasNascimentos[DATA])
         )
```
### Analytics Measures[% Birth x Forecast]  folder=Birth Measures
```dax
DIVIDE([Birth Quantity],[Birth Quantity - Forecast])
```
### Analytics Measures[Birth Quantity Accumulated]  folder=Birth Measures
```dax

 VAR calc1 = 
   CALCULATE(
        [Birth Quantity],
        FILTER(
            ALL(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Birth Quantity],
        FILTER(
            ALL(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)
```
### Analytics Measures[% Mortality]  folder=Dead Measures
```dax
DIVIDE([Dead Quantity Accumulated],[Birth Quantity Accumulated],0)
```
### Analytics Measures[% Amount Saled]  folder=IN - General Sales Measures
```dax
DIVIDE([Amount Saled],[Amount Saled - Forecast])
```
### Analytics Measures[Purchased Quantity - Forecast]  folder=Purchase Measures
```dax

CALCULATE(
        SUM(fMetasCompras[qtd]),
        USERELATIONSHIP(dCalendar[Data],fMetasCompras[DATA])
        )
```
### Analytics Measures[% Purchased Quantity]  folder=Purchase Measures
```dax
DIVIDE([Purchased Quantity],[Purchased Quantity - Forecast])
```
### Analytics Measures[Dead Quantity - Forecast]  folder=Dead Measures
```dax

CALCULATE(SUM(fMetasMortes[qtd]),USERELATIONSHIP(dCalendar[Data],fMetasMortes[DATA]))
```
### Analytics Measures[AVG Price KG Sale Venda em Pe]  folder=IN - Medidas Venda Em Pe
```dax

CALCULATE(SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[Peso Total]))+0
```
### Analytics Measures[MAX AVG Price @ Forecast]  folder=IN - General Sales Measures
```dax
[AVG Price @ (Em Pe + Abate) - Forecast] + [AVG Price @ (Em Pe + Abate) - Forecast] * 0.15
```
### Analytics Measures[AVG Price @ (Em Pe + Abate) - Forecast]  folder=IN - General Sales Measures
```dax


VAR fat = SUM(fMetasAbate[Faturamento]) + SUM(fMetasEmPe[Faturamento])

VAR arr = (SUM(fMetasAbate[Peso Morto Total])/15) + SUM(fMetasEmPe[Peso Morto])

RETURN fat / arr
```
### Analytics Measures[Lotation]  folder=Stock Measures
```dax
[Mean Month Accumulated - UA] / 2911 + 0
```
### Analytics Measures[Lotation - Forecast]  folder=Stock Measures
```dax
[Lotation] + [Lotation] * 0.1
```
### Analytics Measures[Lotation - Forecast - MAX]  folder=Stock Measures
```dax
[Lotation - Forecast] + [Lotation - Forecast] * 0.4
```
### Analytics Measures[Birth Quantity - Forecast - Const]  folder=Birth Measures
```dax

CALCULATE([Birth Quantity - Forecast],ALLEXCEPT(dCalendar,dCalendar[Ano]))
```
### Analytics Measures[% Birth x Forecast (Year)]  folder=Birth Measures
```dax
DIVIDE([Birth Quantity],[Birth Quantity - Forecast - Const])
```
### pecuarioVendaEmPe[Medida]  folder=nan
```dax
nan
```
### fMovGado[Medida 2]  folder=nan
```dax
nan
```
### Analytics Measures[Count of Selected Month]  folder=Dead Measures
```dax

VAR MesesComDados = 
    FILTER(
        VALUES(dCalendar[Mês]),
        CALCULATE( SUM(pecuarioRebanhoMedioMensal[qtd_cab]) ) > 0
    )
RETURN
    COUNTROWS(MesesComDados)
```
### Analytics Measures[Invoicing Abate]  folder=IN - Medidas Abate
```dax
SUM(pecuarioVendaAbate[Faturamento])
```
### fMetasCompras[VALORCALC]  folder=nan
```dax
CALCULATE(SUM(fMetasCompras[VALOR TOTAL]),USERELATIONSHIP(fUnidades[PROPRIETARIO],pecuarioCompras[proprietÁrio]))
```
### Analytics Measures[Mean Month Accumulated - Aux (Desembolso)]  folder=Head Outlay
```dax

 VAR calc1 = 
   CALCULATE(
        [Mean Month],
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Mean Month],
        FILTER(
            ALLSELECTED(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2) 
```
### Analytics Measures[Selected Farm]  folder=nan
```dax

IF(SELECTEDVALUE(fUnidades[fazenda]) = BLANK(),"GRUPO",SELECTEDVALUE(fUnidades[fazenda]))
```
### Analytics Measures[Mean Month Accumulated - Aux (Desembolso) - Forecast]  folder=Head Outlay
```dax

 VAR calc1 = 
   CALCULATE(
        [Mean Month - forecast],
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Mean Month - forecast],
        FILTER(
            ALLSELECTED(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2) 
```
### Analytics Measures[Outlay Forecast]  folder=Finance Measures
```dax

CALCULATE(
        SUM(fMetasDre[Desembolso]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[data_pag])
        )
```
### Analytics Measures[Expenses Accumulated - Forecast]  folder=Head Outlay
```dax

    CALCULATE(
        [Outlay Forecast],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[Costing Forecast]  folder=Head Outlay
```dax

CALCULATE(
        SUM(fMetasDre[Custeio]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[data_pag])
        )
```
### Analytics Measures[Costing Accumulated - Forecast]  folder=Head Outlay
```dax

    CALCULATE(
        [Costing Forecast],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[Birth Quantity Accumulated - Forecast]  folder=Birth Measures
```dax

 VAR calc1 = 
   CALCULATE(
        [Birth Quantity - Forecast],
        FILTER(
            ALL(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Birth Quantity - Forecast],
        FILTER(
            ALL(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)
```
### Analytics Measures[% Atingido Outlay]  folder=Finance Measures
```dax
([Outlay]-[Outlay Forecast])/[Outlay Forecast] --DIVIDE([Outlay],[Outlay Forecast])
```
### Analytics Measures[Color Desemb Cab Mês]  folder=nan
```dax

    IF([head outlay accumulated] > [head outlat accumulated - forecast], "#870000","#008D7D")
```
### Analytics Measures[Color Costing Cab Mês]  folder=nan
```dax

    IF([Costing head Accumulated] > [Costing Head accumulated - forecast], "#870000","#008D7D")
```
### Analytics Measures[Color @ Venda Geral]  folder=nan
```dax

    IF([AVG Price @ (Em Pe + Abate)] > [AVG Price @ (Em Pe + Abate) - Forecast],"#008D7D", "#870000")
```
### Analytics Measures[IN Venda Geral]  folder=nan
```dax

    IF([Invoicing] > [Incoicing - Forecast],1,-1)
```
### Analytics Measures[IN Costing Cab Mês]  folder=nan
```dax

    IF([Costing head Accumulated] > [Costing Head accumulated - forecast], 1,-1)
```
### Analytics Measures[IN Desembolso Cab Mês]  folder=nan
```dax

  IF([head outlay accumulated]> [head outlat accumulated - forecast], -1,1)
```
### Analytics Measures[IN Mean Month]  folder=nan
```dax

    IF([Mean Month] > [Mean Month - forecast],1,-1)
```
### Analytics Measures[Sistema Produção]  folder=nan
```dax
"INFORMATIVO DETALHADO PG1"
```
### Analytics Measures[Revenues Forecast]  folder=Finance Measures
```dax

CALCULATE(
        SUM(fMetasDre[valor]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[data_pag]),
        'fMetasDre'[operaÇÃo]="C",
        fMetasDre[tipo_custeio-CAT] IN {"ReceitasPec","ReceitasAgr","ReceitaPec","ReceitaAgr"}
        )
```
### Analytics Measures[Expenses Forecast]  folder=Finance Measures
```dax

CALCULATE(
        SUM(fMetasDre[valor]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[data_pag]),
        'fMetasDre'[operaÇÃo]="D"
        )
```
### Analytics Measures[Total Paid - Forecast]  folder=Purchase Measures
```dax

CALCULATE(
        SUM(fMetasCompras[VALOR TOTAL]),
        USERELATIONSHIP(dCalendar[Data],fMetasCompras[DATA])
        )+0
```
### Analytics Measures[Purchased Quantity FEMALE]  folder=Purchase Measures
```dax

CALCULATE(
    [Purchased Quantity],
    pecuarioCompras[sexo] = "FÊMEA"
)
```
### Analytics Measures[Purchased Quantity MALE]  folder=Purchase Measures
```dax

CALCULATE(
    [Purchased Quantity],
    pecuarioCompras[sexo] = "MACHO"
)
```
### Analytics Measures[@ AVG Price Purchase]  folder=Purchase Measures
```dax

CALCULATE(SUM(pecuarioCompras[VALOR TOTAL]) / (SUM(pecuarioCompras[Total de @])))
```
### Analytics Measures[% Purchased Value]  folder=Purchase Measures
```dax
DIVIDE([Total Paid],[Total Paid - Forecast])
```
### Analytics Measures[Purchased Quantity - Forecast - TESTE]  folder=Purchase Measures
```dax

CALCULATE(
        SUM(fMetasCompras[qtd]),
        USERELATIONSHIP(fMetasCompras[PROP_FAZ],fUnidades[PROP_FAZ]),
        USERELATIONSHIP(dCalendar[Data],fMetasCompras[DATA])
        )
```
### Analytics Measures[Ágio]  folder=Purchase Measures
```dax

/*
var Fat = CALCULATE(SUM(pecuarioVendaEmPe[Faturamento])+SUM(pecuarioVendaAbate[Faturamento]))
var Quant = CALCULATE(SUM(pecuarioVendaEmPe[qtd])+SUM(pecuarioVendaAbate[qtd]))
var pesoArr = CALCULATE(SUM(pecuarioVendaAbate[Total de @])+SUM(pecuarioVendaEmPe[Total de @]))

RETURN DIVIDE(fat,pesoArr)
*/

var avgArrobaVenda = [AVG Price @ (Em Pe + Abate)]

var avgArrobaCompra = [@ AVG Price Purchase]

RETURN DIVIDE(avgArrobaCompra - avgArrobaVenda,avgArrobaVenda)
```
### Analytics Measures[Mean Month Ha]  folder=Head Outlay
```dax
[Mean Month] / (SUM(fArea[Área_total]) / [Count of Selected Month])
```
### Analytics Measures[UA Median Ha]  folder=Purchase Measures
```dax
[UA Median Month] / (SUM(fArea[Área_total]) / [Count of Selected Month])
```
### Analytics Measures[% mORTALITY ( MEAN MONTH)]  folder=Dead Measures
```dax
[Dead Quantity] / [Mean Month]
```
### Analytics Measures[% Variação]  folder=Finance Measures
```dax

DIVIDE(
                            [Valor Último Mês Selecionado]-[Meta Último Mês Selecionado],[Meta Último Mês Selecionado]
                        )

```
### Analytics Measures[Value Accumulated]  folder=Finance Measures
```dax

VAR LastDate2 = MAX(dCalendar[Data])
VAR IsClassInScope = ISINSCOPE(planejadoXRealizado[classificacao])

RETURN
IF(
    IsClassInScope,
    -- Quando o usuário está vendo uma classificação específica: acumulado simples da própria linha
    CALCULATE(
        SUM(planejadoXRealizado[Valor C]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= LastDate2
        )
    ),
    -- Quando não está em escopo de classificacao: acumulado = Receitas acumuladas - Despesas acumuladas
    VAR ReceitasAcum =
        CALCULATE(
            SUM(planejadoXRealizado[Valor C]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= LastDate2),
            planejadoXRealizado[Classificacao] = "A - RECEITAS"
        )
    VAR DespesasAcum =
        CALCULATE(
            SUM(planejadoXRealizado[Valor C]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= LastDate2),
            planejadoXRealizado[Classificacao] IN {
                "C - INVESTIMENTOS",
                "D - CUSTEIO",
                "E - OUTROS DÉBITOS"
            }
        )
    RETURN
        ReceitasAcum - DespesasAcum
)

```
### Analytics Measures[Meta Accumulated]  folder=Finance Measures
```dax

VAR _MaxDate = MAX(dCalendar[Data])
VAR _IsClassInScope = ISINSCOPE(planejadoXRealizado[classificacao])

RETURN
IF(
    _IsClassInScope,
    -- Acumulado da própria classificação (quando class está no escopo)
    CALCULATE(
        SUM(planejadoXRealizado[Meta C]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= _MaxDate
        )
    ),
    -- Quando não há classificação no escopo: ReceitasAcum - DespesasAcum
    VAR ReceitasAcum =
        CALCULATE(
            SUM(planejadoXRealizado[Meta C]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= _MaxDate),
            planejadoXRealizado[Classificacao] = "A - RECEITAS"
        )
    VAR DespesasAcum =
        CALCULATE(
            SUM(planejadoXRealizado[Meta C]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= _MaxDate),
            planejadoXRealizado[Classificacao] IN {
                "C - INVESTIMENTOS",
                "D - CUSTEIO",
                "E - OUTROS DÉBITOS"
            }
        )
    RETURN
        ReceitasAcum - DespesasAcum
)

```
### Analytics Measures[% Variação Acc Graph]  folder=Finance Measures
```dax

VAR _valor = [%% Variação Acc]
VAR _icone =
    SWITCH(
        TRUE(),
        _valor >= 0, UNICHAR(10004),   -- ✅ check
        _valor < 0, UNICHAR(10060),    -- ❌ X
        BLANK()
    )
RETURN  [%% Variação Acc] 
/*IF(
        NOT ISFILTERED(planejadoXRealizado[centro_de_custo_bi]), 
      
        BLANK(), 
        [%% Variação Acc] 
    )*/
```
### Analytics Measures[% Variação Graph]  folder=Finance Measures
```dax

VAR _valor = [% Variação]
VAR _icone =
    SWITCH(
        TRUE(),
        _valor >= 0, UNICHAR(10004),   -- ✅ check
        _valor < 0, UNICHAR(10060),    -- ❌ X
        BLANK()
    )
RETURN [% Variação]
/*IF(
        NOT ISFILTERED(planejadoXRealizado[centro_de_custo_bi]), 
        -- OU: NOT ISINSCOPE('Sua Tabela'[Sua Coluna de Linha]),
        BLANK(), -- Se for um Total, retorna em branco
        [% Variação] -- Se for o nível de detalhe (Linha), retorna o valor
    )*/

```
### Analytics Measures[%% Variação Acc]  folder=Finance Measures
```dax

                DIVIDE( [Value Accumulated] - [Meta Accumulated],[Meta Accumulated])
```
### Analytics Measures[Icon]  folder=Finance Measures
```dax

--IF(
   -- ISINSCOPE(planejadoXRealizado[centro_de_custo_bi]),
    VAR _var = [% Variação]
    VAR _class = SELECTEDVALUE(planejadoXRealizado[classificacao])
    RETURN
        IF(
            _var <> BLANK(),
            SWITCH(
                TRUE(),
  
                _class = "A - RECEITAS" && _var > 0.03, "VERDE",
                _class = "A - RECEITAS" && _var < -0.03, "VERMELHO",
                _class = "A - RECEITAS" && _var >= -0.03 && _var <= 0.03, "AMARELO",

                _class <> "A - RECEITAS" && _var <= 0 && _var >= -1, "VERDE",
                _class <> "A - RECEITAS" && _var > 0.03, "VERMELHO",
                _class <> "A - RECEITAS" && _var > 0 && _var <= 0.03, "AMARELO",

                BLANK()
            ),
            BLANK()
        )--,
    --BLANK()
--)

```
### Analytics Measures[RL Mensal]  folder=Finance Measures
```dax
"MENSAL"
```
### Analytics Measures[RL Acumulado]  folder=Finance Measures
```dax
"ACUMULADO"
```
### Analytics Measures[Icon Acc]  folder=Finance Measures
```dax

--IF(
 --   ISINSCOPE(planejadoXRealizado[centro_de_custo_bi]),
    VAR _var = [%% Variação Acc]
    VAR _class = SELECTEDVALUE(planejadoXRealizado[Classificacao2])
    RETURN
        IF(
            _var <> BLANK(),
            SWITCH(
                TRUE(),
                _class = "A - RECEITAS" && _var > 0.03, "VERDE",
                _class = "A - RECEITAS" && _var < -0.03, "VERMELHO",
                _class = "A - RECEITAS" && _var >= -0.03 && _var <= 0.03, "AMARELO",

                _class <> "A - RECEITAS" && _var <= 0 && _var >= -1, "VERDE",
                _class <> "A - RECEITAS" && _var > 0.03, "VERMELHO",
                _class <> "A - RECEITAS" && _var > 0 && _var <= 0.03, "AMARELO",

                BLANK()
            ),
            BLANK()
        )--,
--    BLANK()
--)

```
### planejadoXRealizado[Valor Último Mês Selecionado]  folder=nan
```dax


VAR MaxDateSelecionada =
    CALCULATE(
        MAX('dcalendar'[Data]),
        ALLSELECTED('dcalendar')
    )
VAR PrimeiroDiaDoUltimoMes =
    EOMONTH(MaxDateSelecionada, -1) + 1

VAR FiltrosDeData =
    FILTER(
        ALL('dcalendar'), 
        'dcalendar'[Data] >= PrimeiroDiaDoUltimoMes &&
        'dcalendar'[Data] <= MaxDateSelecionada
    )
    
VAR Receitas = 
    CALCULATE(
        SUM('planejadoXRealizado'[Valor C]), 
        FiltrosDeData,
        'planejadoXRealizado'[classificacao] = "A - RECEITAS"
    )

VAR Despesas = 
    CALCULATE(
        SUM('planejadoXRealizado'[Valor C]), 
        FiltrosDeData,
        'planejadoXRealizado'[classificacao] IN {"C - INVESTIMENTOS","D - CUSTEIO","E - OUTROS DÉBITOS"}
    )

RETURN 
    IF(
        ISINSCOPE('planejadoXRealizado'[Classificacao]),
        
        -- Cálculo linha a linha (dentro do escopo)
        CALCULATE(
            SUM('planejadoXRealizado'[Valor C]), 
            FiltrosDeData
        ),
        
        -- Cálculo do Total Final
        -- O COALESCE garante que se Receitas for BLANK, ele usa 0.
        -- Assim a conta fica: 0 - Despesas = -Despesas (o total aparece negativo corretamente)
        COALESCE(Receitas, 0) - COALESCE(Despesas, 0)
    )
```
### planejadoXRealizado[Meta Último Mês Selecionado]  folder=nan
```dax

VAR MaxDateSelecionada =
    CALCULATE(
        MAX('dcalendar'[Data]),
        ALLSELECTED('dcalendar')
    )
VAR PrimeiroDiaDoUltimoMes =
    EOMONTH(MaxDateSelecionada, -1) + 1

VAR FiltrosDeData =
    FILTER(
        ALL(dCalendar),
        dCalendar[Data]>= PrimeiroDiaDoUltimoMes && dCalendar[Data] <=MaxDateSelecionada
    )
RETURN
    IF(
        ISINSCOPE('planejadoXRealizado'[Classificacao]),
        CALCULATE(
            SUM('planejadoXRealizado'[Meta C]), 
            FiltrosDeData
        ),
        CALCULATE(
            SUM('planejadoXRealizado'[Meta C]), 
            FiltrosDeData,
            'planejadoXRealizado'[Classificacao] = "A - RECEITAS"
        ) - 
        CALCULATE(
            SUM('planejadoXRealizado'[Meta C]), 
            FiltrosDeData,
            'planejadoXRealizado'[Classificacao] IN {"C - INVESTIMENTOS","D - CUSTEIO","E - OUTROS DÉBITOS"}
        )
    )

/*
VAR MaxDateSelecionada =
    CALCULATE(
        MAX('dcalendar'[Data]),
        ALLSELECTED('dcalendar')
    )
VAR PrimeiroDiaDoUltimoMes =
    EOMONTH(MaxDateSelecionada, -1) + 1

VAR FiltrosDeData =
    FILTER(
        ALL('dcalendar'), 
        'dcalendar'[Data] >= PrimeiroDiaDoUltimoMes &&
        'dcalendar'[Data] <= MaxDateSelecionada
    )
    
RETURN
    IF(
        ISINSCOPE('planejadoXRealizado'[Classificacao]),
        CALCULATE(
            SUM('planejadoXRealizado'[Valor C]), 
            FiltrosDeData
        ),
        CALCULATE(
            SUM('planejadoXRealizado'[Valor C]), 
            FiltrosDeData,
            'planejadoXRealizado'[Classificacao] <> "D - DESEMBOLSO"
        )
    )
*/
```
### Analytics Measures[All Revenues]  folder=Finance Measures
```dax
CALCULATE(SUM('financeiroDre'[valor]),'financeiroDre'[operaÇÃo]="C",financeiroDre[tipo_custeio-CAT] IN {"Receita Pec", "Receita Agr","Receita outras"})
```
### Analytics Measures[Amount Saled (Abate)]  folder=IN - Medidas Abate
```dax
SUM(pecuarioVendaAbate[qtd])
```
### Analytics Measures[Amount Saled - Forecast (Abate)]  folder=IN - Medidas Abate
```dax


VAR calc1 = CALCULATE(SUM(fMetasAbate[qtd]))


RETURN calc1
```
### Analytics Measures[Invoicing (Abate)]  folder=IN - Medidas Abate
```dax
SUM(pecuarioVendaAbate[Faturamento])+0
```
### Analytics Measures[Incoicing - Forecast (Abate)]  folder=IN - Medidas Abate
```dax


VAR calc1 = CALCULATE(SUM(fMetasAbate[faturamento]))

RETURN calc1+0
```
### Analytics Measures[IN - Name (Abate)]  folder=nan
```dax
"Venda Abate"
```
### Analytics Measures[IN - AVG Live Weight]  folder=IN - Medidas Abate
```dax


VAR calc1 = SUM(pecuarioVendaAbate[qtd])

VAR calc2 = SUM(pecuarioVendaAbate[pesovivo_total])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[IN - Peso Médio Vivo]  folder=IN - Data Labels
```dax
"Peso Médio Vivo"
```
### Analytics Measures[IN - Valor da @]  folder=IN - Data Labels
```dax
"Preço de Venda da @"
```
### Analytics Measures[IN - Rendimento de Carcaça]  folder=IN - Data Labels
```dax
"Rendimento de Carcaça"
```
### Analytics Measures[IN - Fêmea]  folder=IN - Data Labels
```dax
"FÊMEA"
```
### Analytics Measures[IN - Macho]  folder=IN - Data Labels
```dax
"MACHO"
```
### Analytics Measures[IN - Cabeças]  folder=IN - Data Labels
```dax
"Cb"
```
### Analytics Measures[IN - Geral]  folder=IN - Data Labels
```dax
"GERAL"
```
### Analytics Measures[IN - Faturamento]  folder=IN - Data Labels
```dax
"Fat. Realizado"
```
### Analytics Measures[Invoicing (Em Pe )]  folder=IN - Medidas Venda Em Pe
```dax
SUM(pecuarioVendaEmPe[Faturamento])+0
```
### Analytics Measures[Incoicing - Forecast (Em Pe)]  folder=IN - Medidas Venda Em Pe
```dax


VAR calc1 = CALCULATE(SUM(fMetasEmPe[faturamento]))

RETURN calc1+0
```
### Analytics Measures[Amount Saled (Em pe)]  folder=IN - Medidas Venda Em Pe
```dax
SUM(pecuarioVendaEmPe[qtd])
```
### Analytics Measures[Amount Saled - Forecast (Em Pe)]  folder=IN - Medidas Venda Em Pe
```dax


VAR calc1 = CALCULATE(SUM(fMetasEmPe[qtd]))


RETURN calc1
```
### Analytics Measures[IN - Preço do KG]  folder=IN - Data Labels
```dax
"Preço do KG" 
```
### Analytics Measures[IN - AVG Live Weight (Em Pe)]  folder=IN - Medidas Venda Em Pe
```dax


VAR calc1 = SUM(pecuarioVendaEmPe[qtd])

VAR calc2 = SUM(pecuarioVendaEmPe[pesovivo_total])

RETURN DIVIDE(calc2,calc1)+0
```
### Analytics Measures[IN AVG - Peso Médio de Compra]  folder=Purchase Measures
```dax


VAR calc1 = SUM(pecuarioCompras[qtd])

VAR calc2 = SUM(pecuarioCompras[total_peso])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[IN - Meta Valor KG]  folder=IN - Data Labels
```dax
"Meta Valor KG" 
```
### Analytics Measures[IN AVG - Peso Médio de Compra (Forecast)]  folder=Purchase Measures
```dax


VAR calc1 = SUM(fMetasCompras[qtd])

VAR calc2 = SUM(fMetasCompras[total_peso])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[AVG Purchase Price KG]  folder=Purchase Measures
```dax

CALCULATE(SUM(pecuarioCompras[VALOR TOTAL]) / SUM(pecuarioCompras[total_peso]))+0
```
### Analytics Measures[AVG Purchase Price KG (Forecast)]  folder=Purchase Measures
```dax

CALCULATE(SUM(fMetasCompras[VALOR TOTAL]) / SUM(fMetasCompras[total_peso]))+0
```
### Analytics Measures[IN - Ágio]  folder=IN - Data Labels
```dax
"Ágio"
```
### Analytics Measures[IN - Valor da @ Compra]  folder=IN - Data Labels
```dax
"Preço de @ de Compra"
```
### Analytics Measures[IN - Bezerro]  folder=IN - Data Labels
```dax
"BEZERROS"
```
### Analytics Measures[IN - Jovens]  folder=IN - Data Labels
```dax
"JOVENS"
```
### Analytics Measures[IN - Adultos]  folder=IN - Data Labels
```dax
"ADULTOS"
```
### Analytics Measures[IN - Meta]  folder=IN - Data Labels
```dax
"Planejado"
```
### Analytics Measures[IN - Mortalidade sobre Rebanho Médio]  folder=IN - Data Labels
```dax
"% Sobre Rebanho Médio"
```
### Analytics Measures[IN - Mortalidade sobre Nascimento]  folder=IN - Data Labels
```dax
"% Sobre Nascimento"
```
### Analytics Measures[IN - % Male Birth]  folder=Birth Measures
```dax


VAR tot = [Birth Quantity]

VAR qtdmale = CALCULATE([Birth Quantity], pecuarioNascimento[sexo] = "MACHO")

RETURN DIVIDE(qtdmale,tot)
```
### Analytics Measures[IN - % Female Birth]  folder=Birth Measures
```dax


VAR tot = [Birth Quantity]

VAR qtdmale = CALCULATE([Birth Quantity], pecuarioNascimento[sexo] = "FÊMEA")

RETURN DIVIDE(qtdmale,tot)
```
### Analytics Measures[IN - Nascimentos]  folder=IN - Data Labels
```dax
"% Sobre Sobre o Total"
```
### Analytics Measures[IN - Relação a Meta]  folder=IN - Data Labels
```dax
"% Em relação a Meta"
```
### Analytics Measures[IN - Vendas (Geral)]  folder=IN - Data Labels
```dax
"VENDAS"
```
### Analytics Measures[IN - Compras (Label)]  folder=IN - Data Labels
```dax
"COMPRAS"
```
### Analytics Measures[IN - Nascimentos (Label)]  folder=IN - Data Labels
```dax
"Nascimentos"
```
### Analytics Measures[IN - Mortes]  folder=IN - Data Labels
```dax
"MORTES"
```
### Analytics Measures[IN - Compra]  folder=IN - Data Labels
```dax
"Valor Compra"
```
### Analytics Measures[IN - AVG Live Weight (Forecast)]  folder=IN - Medidas Abate
```dax


VAR calc1 = SUM(fMetasAbate[qtd])

VAR calc2 = SUM(fMetasAbate[pesovivo_total])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[IN - Planejado]  folder=IN - Data Labels
```dax
"Planejado"
```
### Analytics Measures[IN - Realizado]  folder=IN - Data Labels
```dax
"Realizado"
```
### Analytics Measures[IN - Rebanho Médio]  folder=IN - Data Labels
```dax
"REBANHO MÉDIO"
```
### Analytics Measures[IN - Rebanho Médio Cab]  folder=IN - Data Labels
```dax
"Rebanho Médio Cab"
```
### Analytics Measures[IN - Rebanho Médio UA]  folder=IN - Data Labels
```dax
"Rebanho Médio UA"
```
### Analytics Measures[IN - Lotação Cab]  folder=IN - Data Labels
```dax
"Lotação Cab"
```
### Analytics Measures[IN - Lotação UA]  folder=IN - Data Labels
```dax
"Lotação UA"
```
### Analytics Measures[IN - % Meta]  folder=IN - Data Labels
```dax
"% Em Relação a Meta"
```
### Analytics Measures[IN - Indice de Mortalidade]  folder=IN - Data Labels
```dax
"Índ. Mortalidade"
```
### Analytics Measures[IN - Mortes (2)]  folder=IN - Data Labels
```dax
"Mortes"
```
### Analytics Measures[IN - Nascimentos (Label - 2)]  folder=IN - Data Labels
```dax
"NASCIMENTOS"
```
### Analytics Measures[IN - Compras (Label 2 )]  folder=IN - Data Labels
```dax
"Compras"
```
### Analytics Measures[IN - Vendas (Label)]  folder=IN - Data Labels
```dax
"Vendas"
```
### Analytics Measures[IN - COMPRA X VENDA]  folder=IN - Data Labels
```dax
"COMPRAS | VENDAS"
```
### Analytics Measures[IN - Data Análise]  folder=IN - Data Labels
```dax
"Análise :"
```
### Analytics Measures[IN - Separador de]  folder=IN - Data Labels
```dax
"de" 
```
### Analytics Measures[IN - Periodo Capa]  folder=IN - Data Labels
```dax

/*
VAR ultmes = MAX(dCalendar[Mês])

VAR ano = MAX(dCalendar[Ano])

RETURN CONCATENATE(ultmes,CONCATENATE(" de ",ano))*/

VAR UltimaData = MAX(dCalendar[Data]) -- Busca a maior data selecionada
RETURN 
FORMAT(UltimaData, "MMMM \d\e yyyy")
```
### Analytics Measures[IN - Site Terra]  folder=IN - Data Labels
```dax
"terradesenvolvimento.com.br"
```
### Analytics Measures[IN - Periodo Envio]  folder=IN - Data Labels
```dax


VAR data = TODAY()

VAR ultmes = FORMAT(data, "MMMM")

VAR ano = YEAR(data)

RETURN CONCATENATE(
                    CONCATENATE("Cuiabá, ",
                                            CONCATENATE(ultmes,CONCATENATE(" de ",ano))),"."
                    )
```
### Analytics Measures[IN - AVG Live Weight (Em Pe - Forecast)]  folder=IN - Medidas Venda Em Pe
```dax


VAR calc1 = SUM(fMetasEmPe[qtd])

VAR calc2 = SUM(fMetasEmPe[pesovivo_total])

RETURN DIVIDE(calc2,calc1)+0
```
### Analytics Measures[AVG Price KG Sale Venda em Pe - Forecast]  folder=IN - Medidas Venda Em Pe
```dax

CALCULATE(SUM(fMetasEmPe[Faturamento]) / SUM(fMetasEmPe[Peso Total]))+0
```
### Analytics Measures[IN - Faturamento Planejado]  folder=IN - Data Labels
```dax
"Fat. Planejado"
```
### Analytics Measures[IN - Inv Realizado]  folder=IN - Data Labels
```dax
"Inv. Realizado"
```
### Analytics Measures[IN - Inv Planejado]  folder=IN - Data Labels
```dax
"Inv. Planejado"
```
### Analytics Measures[IN - Rendimento Carcaça (Forecast)]  folder=IN - Medidas Abate
```dax
SUM(fMetasAbate[pesomorto_total]) / SUM(fMetasAbate[pesovivo_total])
```
### Analytics Measures[IN - Cbs Vendidas]  folder=IN - Data Labels
```dax
"Cabeças Vendidas"
```
### Analytics Measures[IN - Cbs Compradas]  folder=IN - Data Labels
```dax
"Cbs Compradas"
```
### Analytics Measures[Invoicing Accumulated (Abate)]  folder=IN - Medidas Abate
```dax

    CALCULATE(
        SUM(pecuarioVendaAbate[qtd])+0,
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )


```
### Analytics Measures[Amount Saled Accumulated (Em Pe)]  folder=IN - Medidas Venda Em Pe
```dax

    CALCULATE(
        SUM(pecuarioVendaEmPe[qtd])+0,
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )


```
### Analytics Measures[Purchase Quantity Accumulated]  folder=Purchase Measures
```dax

    CALCULATE(
        SUM(pecuarioCompras[qtd])+0,
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )


```
### Analytics Measures[IN - Incoming Transfer]  folder=nan
```dax

CALCULATE(SUM(fTransferencias[qtd]),fTransferencias[operaÇÃo] = "Transf. Entrada")
```
### Analytics Measures[IN - Outgoing Transfer]  folder=nan
```dax

CALCULATE(SUM(fTransferencias[qtd]),fTransferencias[operaÇÃo] = "Transf. Saida")
```
### Analytics Measures[IN - Incoming Transfer - Forecast]  folder=nan
```dax

CALCULATE(SUM(fMetasTransferencias[qtd]),fMetasTransferencias[operaÇÃo] = "Transf. Entrada")
```
### Analytics Measures[IN - Outgoing Transfer - Forecast]  folder=nan
```dax

CALCULATE(SUM(fMetasTransferencias[qtd]),fMetasTransferencias[operaÇÃo] = "Transf. Saida")
```
### Analytics Measures[IN - Entrada]  folder=IN - Data Labels
```dax
"ENTRADA"
```
### Analytics Measures[IN - Saida]  folder=IN - Data Labels
```dax
"SAÍDA"
```
### Analytics Measures[IN - Quantidade]  folder=IN - Data Labels
```dax
"QTD" 
```
### Analytics Measures[Medida 3]  folder=IN - Data Labels
```dax
nan
```
### Analytics Measures[IN Peso Médio]  folder=IN - Data Labels
```dax
"PESO MÉDIO"
```
### Analytics Measures[IN Valor@]  folder=IN - Data Labels
```dax
"VALOR @"
```
### Analytics Measures[IN QTD Transfer Forecast]  folder=Transfer Measures
```dax
SUM(fMetasTransferencias[qtd])
```
### Analytics Measures[IN QTD Transfer]  folder=Transfer Measures
```dax
SUM(fTransferencias[qtd])
```
### Analytics Measures[IN - AVG Price @ Transfer]  folder=Transfer Measures
```dax

CALCULATE(SUM(fTransferencias[VALOR TOTAL]) / (SUM(fTransferencias[Peso Total @])))
```
### Analytics Measures[IN - AVG Price @ Transfer Forecas]  folder=Transfer Measures
```dax

CALCULATE(SUM(fMetasTransferencias[VALOR TOTAL]) / (SUM(fMetasTransferencias[Peso Total @])))
```
### Analytics Measures[IN - AVG Weight Transfer]  folder=Transfer Measures
```dax


VAR calc1 = SUM(fTransferencias[qtd])

VAR calc2 = SUM(fTransferencias[total_peso])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[IN - AVG Weight Transfer Forecast]  folder=Transfer Measures
```dax


VAR calc1 = SUM(fMetasTransferencias[qtd])

VAR calc2 = SUM(fMetasTransferencias[total_peso])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[IN - TRANSFERÊNCIAS]  folder=IN - Data Labels
```dax
"TRANSFERÊNCIAS"
```
### Analytics Measures[head outlat accumulated - forecast graph]  folder=Head Outlay
```dax
[head outlat accumulated - forecast] + ([head outlat accumulated - forecast] * 0.2)
```

## Power Query (M)

### pecuarioNascimento
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT ""operaÇÃo"", categ_fazenda, qtd, safra, peso_nasc, data_abrev, categoria_bi, sexo, ""proprietÁrio"", fazenda, retiro, SUBSTRING(""DATA"" FROM 1 FOR 10) as ""DATA"",unaccent(REPLACE(concat(""proprietÁrio"",fazenda),' ','')) as PROP_FAZ#(lf)#(tab)FROM ""DATABASE"".stg_fnascimento"),
    #"Valor Substituído" = Table.ReplaceValue(Fonte," 00:00:00.000","",Replacer.ReplaceText,{"DATA"}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Valor Substituído",{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### pecuarioRebanhoMedioMensal
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *, unaccent(REPLACE(concat(t0.""proprietÁrio"",t0.fazenda),' ','')) as PROP_FAZ FROM ""DATABASE"".stg_frebanhomedio t0"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### pecuarioVendaAbate
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT#(lf)#(tab)T.""operaÇÃo"",#(lf)#(tab)T.cliente, #(lf)#(tab)T.categ_fazenda, #(lf)#(tab)T.MES,#(lf)#(tab)T.ANO,#(lf)#(tab)SUBSTRING(T.""DATA"" FROM 1 FOR 10) AS ""DATA"", #(lf)#(tab)T.qtd, #(lf)#(tab)CASE #(lf)#(tab)#(tab)WHEN T.DILUICAO_META = 0 THEN 0#(lf)#(tab)#(tab)WHEN T.DILUICAO_META <> 0 THEN T.QTD_META_MENSAL / T.DILUICAO_META#(lf)#(tab)ELSE 0#(lf)#(tab)END AS QTD_META_DILUIDA,#(lf)#(tab)T.QTD_META_MENSAL,#(lf)#(tab)T.DILUICAO_META,#(lf)#(tab)T.era, #(lf)#(tab)T.peso_vivo,#(lf)#(tab)T.rendimento,#(lf)#(tab)T.peso_arroba, #(lf)#(tab)T.valor_arroba,#(lf)#(tab)T.faturamento, #(lf)#(tab)CASE #(lf)#(tab)#(tab)WHEN T.DILUICAO_META = 0 THEN 0#(lf)#(tab)#(tab)WHEN T.DILUICAO_META <> 0 THEN T.META_MENSAL / T.DILUICAO_META#(lf)#(tab)ELSE 0#(lf)#(tab)END AS META_DILUIDA,#(lf)#(tab)T.META_MENSAL,#(lf)#(tab)T.categoria_bi, #(lf)#(tab)T.sexo, #(lf)#(tab)T.peso_morto,#(lf)#(tab)T.pesovivo_total, #(lf)#(tab)T.pesomorto_total, #(lf)#(tab)T.valor_kg, #(lf)#(tab)T.valor_cab, #(lf)#(tab)T.""proprietÁrio"", #(lf)#(tab)T.fazenda, #(lf)#(tab)T.retiro,#(lf)        unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ',''))  as PROP_FAZ#(lf)#(tab)#(lf)FROM#(lf)(#(lf)#(tab)SELECT#(lf)#(tab)*,#(lf)#(tab)COUNT(T1.QTD_META_MENSAL) OVER(partition by T1.""proprietÁrio"", T1.fazenda, T1.ANO, T1.MES) DILUICAO_META#(lf)#(tab)FROM#(lf)#(tab)(#(lf)#(tab)#(tab)SELECT T0.""operaÇÃo"",#(lf)#(tab)#(tab)#(tab)   T0.cliente, #(lf)#(tab)#(tab)#(tab)   T0.categ_fazenda, #(lf)#(tab)#(tab)#(tab)   T1.MES,#(lf)#(tab)#(tab)#(tab)   T1.ANO,#(tab)   #(lf)#(tab)#(tab)#(tab)   T0.""DATA"", #(lf)#(tab)#(tab)#(tab)   T0.qtd, #(lf)#(tab)#(tab)#(tab)   T1.qtd as QTD_META_MENSAL,#(lf)#(tab)#(tab)#(tab)   T0.era, #(lf)#(tab)#(tab)#(tab)   T0.peso_vivo,#(lf)#(tab)#(tab)#(tab)   T0.rendimento,#(lf)#(tab)#(tab)#(tab)   T0.peso_arroba, #(lf)#(tab)#(tab)#(tab)   T0.valor_arroba,#(lf)#(tab)#(tab)#(tab)   T0.faturamento, #(lf)#(tab)#(tab)#(tab)   T1.META AS META_MENSAL,#(lf)#(tab)#(tab)#(tab)   T0.categoria_bi, #(lf)#(tab)#(tab)#(tab)   T0.sexo, #(lf)#(tab)#(tab)#(tab)   T0.peso_morto,#(lf)#(tab)#(tab)#(tab)   T0.pesovivo_total, #(lf)#(tab)#(tab)#(tab)   T0.pesomorto_total, #(lf)#(tab)#(tab)#(tab)   T0.valor_kg, #(lf)#(tab)#(tab)#(tab)   T0.valor_cab, #(lf)#(tab)#(tab)#(tab)   T0.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)   T0.fazenda, #(lf)#(tab)#(tab)#(tab)   T0.retiro#(lf)#(tab)#(tab)FROM ""DATABASE"".stg_fvendaabate T0#(lf)#(lf)#(tab)#(tab)LEFT JOIN #(lf)#(tab)#(tab)(#(lf)#(tab)#(tab) SELECT#(lf)#(tab)#(tab)#(tab)T1.""operaÇÃo"", #(lf)#(tab)#(tab)#(tab)T1.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)T1.fazenda, #(lf)#(tab)#(tab)#(tab)T1.retiro,#(lf)#(tab)#(tab)#(tab)T1.MES,#(lf)#(tab)#(tab)#(tab)T1.ANO,#(lf)#(tab)#(tab)#(tab)SUM(T1.qtd) as qtd, #(lf)#(tab)#(tab)#(tab)SUM(T1.META) AS META#(lf)#(tab)#(tab) FROM(#(lf)#(tab)#(tab)#(tab)SELECT #(lf)#(tab)#(tab)#(tab)#(tab)T1.""operaÇÃo"", #(lf)#(tab)#(tab)#(tab)#(tab)T1.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)#(tab)T1.fazenda, #(lf)#(tab)#(tab)#(tab)#(tab)T1.retiro,#(lf)#(tab)#(tab)#(tab)#(tab)   --T1.cliente, #(lf)#(tab)#(tab)#(tab)#(tab)   --T1.categ_fazenda, #(lf)#(tab)#(tab)#(tab)#(tab)SUBSTRING(T1.""DATA"" FROM 6 FOR 2) AS MES,#(lf)#(tab)#(tab)#(tab)#(tab)SUBSTRING(T1.""DATA"" FROM 1 FOR 4) AS ANO,#(lf)#(tab)#(tab)#(tab)#(tab)T1.""DATA"", #(lf)#(tab)#(tab)#(tab)#(tab)SUM(T1.qtd) as qtd, #(lf)#(tab)#(tab)#(tab)#(tab)   --T1.era, #(lf)#(tab)#(tab)#(tab)#(tab)  -- SUM(T1.peso_vivo) as peso_vivo, #(lf)#(tab)#(tab)#(tab)#(tab)  -- SUM(T1.rendimento) as rendimento, #(lf)#(tab)#(tab)#(tab)#(tab)   --T1.peso_arroba, #(lf)#(tab)#(tab)#(tab)#(tab)   --T1.valor_arroba, #(lf)#(tab)#(tab)#(tab)#(tab)SUM(T1.faturamento) AS META#(lf)#(lf)#(tab)#(tab)#(tab)FROM ""DATABASE"".stg_fmetasabates T1#(lf)#(tab)#(tab)#(tab)GROUP BY#(lf)#(tab)#(tab)#(tab)#(tab)T1.""operaÇÃo"", #(lf)#(tab)#(tab)#(tab)#(tab)T1.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)#(tab)T1.fazenda, #(lf)#(tab)#(tab)#(tab)#(tab)T1.retiro,#(lf)#(tab)#(tab)#(tab)#(tab)T1.""DATA""#(lf)#(tab)#(tab)#(tab))T1#(lf)#(tab)#(tab)#(tab)GROUP BY#(lf)#(tab)#(tab)#(tab)#(tab)T1.""operaÇÃo"", #(lf)#(tab)#(tab)#(tab)#(tab)T1.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)#(tab)T1.fazenda, #(lf)#(tab)#(tab)#(tab)#(tab)T1.retiro,#(lf)#(tab)#(tab)#(tab)#(tab)T1.MES,#(lf)#(tab)#(tab)#(tab)#(tab)T1.ANO#(lf)#(lf)#(tab)#(tab)) T1 ON T1.""proprietÁrio"" = T0.""proprietÁrio"" AND T1.fazenda = T0.fazenda AND  T1.ANO = SUBSTRING(T0.""DATA"" FROM 1 FOR 4) AND T1.MES = SUBSTRING(T0.""DATA"" FROM 6 FOR 2)#(lf)#(tab)#(tab)--WHERE  T0.""proprietÁrio"" = 'ELISA NISHIMURA'#(lf)#(lf)#(tab)) AS T1#(lf)) AS T"),
    #"Valor Substituído" = Table.ReplaceValue(Fonte," 00:00:00.000","",Replacer.ReplaceText,{"DATA"}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Valor Substituído",{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### pecuarioVendaEmPe
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT#(lf)#(tab)T.""operaÇÃo"",#(lf)#(tab)T.cliente, #(lf)#(tab)T.categ_fazenda, #(lf)#(tab)T.MES,#(lf)#(tab)T.ANO,#(lf)#(tab)SUBSTRING(T.""DATA"" FROM 1 FOR 10) AS ""DATA"", #(lf)#(tab)T.qtd, #(lf)#(tab)CASE #(lf)#(tab)#(tab)WHEN T.DILUICAO_META = 0 THEN 0#(lf)#(tab)#(tab)WHEN T.DILUICAO_META <> 0 THEN T.QTD_META_MENSAL / T.DILUICAO_META#(lf)#(tab)ELSE 0#(lf)#(tab)END AS QTD_META_DILUIDA,#(lf)#(tab)T.QTD_META_MENSAL,#(lf)#(tab)T.DILUICAO_META,#(lf)#(tab)--T.era, #(lf)#(tab)T.peso_vivo,#(lf)#(tab)--T.rendimento,#(lf)#(tab)--T.peso_arroba, #(lf)#(tab)T.valor_arroba,#(lf)#(tab)T.faturamento, #(lf)#(tab)CASE #(lf)#(tab)#(tab)WHEN T.DILUICAO_META = 0 THEN 0#(lf)#(tab)#(tab)WHEN T.DILUICAO_META <> 0 THEN T.META_MENSAL / T.DILUICAO_META#(lf)#(tab)ELSE 0#(lf)#(tab)END AS META_DILUIDA,#(lf)#(tab)T.META_MENSAL,#(lf)#(tab)T.categoria_bi, #(lf)#(tab)T.sexo, #(lf)#(tab)--T.peso_morto,#(lf)#(tab)T.pesovivo_total, #(lf)#(tab)--T.pesomorto_total, #(lf)#(tab)T.valor_kg, #(lf)#(tab)T.valor_cab, #(lf)#(tab)T.""proprietÁrio"", #(lf)#(tab)T.fazenda, #(lf)        unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ,#(lf)#(tab)T.retiro#(lf)#(tab)#(lf)FROM#(lf)(#(lf)#(tab)SELECT#(lf)#(tab)*,#(lf)#(tab)COUNT(T1.QTD_META_MENSAL) OVER(partition by T1.""proprietÁrio"", T1.fazenda, T1.ANO, T1.MES) DILUICAO_META#(lf)#(tab)FROM#(lf)#(tab)(#(lf)#(tab)#(tab)SELECT #(lf)#(tab)#(tab)#(tab)   T0.""operaÇÃo"",#(lf)#(tab)#(tab)#(tab)   T0.cliente, #(lf)#(tab)#(tab)#(tab)   T0.categ_fazenda, #(lf)#(tab)#(tab)#(tab)   T1.MES,#(lf)#(tab)#(tab)#(tab)   T1.ANO,#(tab)   #(lf)#(tab)#(tab)#(tab)   T0.""DATA"", #(lf)#(tab)#(tab)#(tab)   T0.qtd, #(lf)#(tab)#(tab)#(tab)   T1.qtd as QTD_META_MENSAL,#(lf)#(tab)#(tab)#(tab)   T0.peso_vivo,#(lf)#(tab)#(tab)#(tab)   T0.pesovivo_total,#(lf)#(tab)#(tab)#(tab)   T0.valor_arroba,#(lf)#(tab)#(tab)#(tab)   T0.valor_cab, #(lf)#(tab)#(tab)#(tab)   T0.faturamento, #(lf)#(tab)#(tab)#(tab)   T1.META AS META_MENSAL,#(lf)#(tab)#(tab)#(tab)   T0.categoria_bi, #(lf)#(tab)#(tab)#(tab)   T0.sexo, #(lf)#(tab)#(tab)#(tab)   T0.valor_kg,#(lf)#(tab)#(tab)#(tab)   T0.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)   T0.fazenda, #(lf)#(tab)#(tab)#(tab)   T0.retiro#(lf)#(tab)#(tab)FROM ""DATABASE"".stg_fvendaempe T0#(lf)#(lf)#(tab)#(tab)LEFT JOIN #(lf)#(tab)#(tab)(#(lf)#(tab)#(tab) SELECT#(lf)#(tab)#(tab)#(tab)T1.""operaÇÃo"", #(lf)#(tab)#(tab)#(tab)T1.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)T1.fazenda, #(lf)#(tab)#(tab)#(tab)T1.retiro,#(lf)#(tab)#(tab)#(tab)T1.MES,#(lf)#(tab)#(tab)#(tab)T1.ANO,#(lf)#(tab)#(tab)#(tab)SUM(T1.qtd) as qtd, #(lf)#(tab)#(tab)#(tab)SUM(T1.META) AS META#(lf)#(tab)#(tab) FROM(#(lf)#(tab)#(tab)#(tab)SELECT #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.""operaÇÃo"", #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.fazenda, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.retiro,#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)   --T1.cliente, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)   --T1.categ_fazenda, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)SUBSTRING(T1.""DATA"" FROM 6 FOR 2) AS MES,#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)SUBSTRING(T1.""DATA"" FROM 1 FOR 4) AS ANO,#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)--T1.""DATA"", #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)SUM(T1.qtd) as qtd, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)   --T1.era, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)  -- SUM(T1.peso_vivo) as peso_vivo, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)  -- SUM(T1.rendimento) as rendimento, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)   --T1.peso_arroba, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)   --T1.valor_arroba, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)SUM(T1.faturamento) AS META#(lf)#(lf)#(tab)#(tab)#(tab)#(tab)FROM ""DATABASE"".stg_fmetasempe T1#(lf)#(tab)#(tab)#(tab)#(tab)--where t1.fazenda = 'CÁCERES'#(lf)#(tab)#(tab)#(tab)#(tab)GROUP BY#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.""operaÇÃo"", #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.fazenda, #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.retiro,#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)T1.""DATA""#(lf)#(tab)#(tab)#(tab))T1#(lf)#(tab)#(tab)#(tab)GROUP BY#(lf)#(tab)#(tab)#(tab)#(tab)T1.""operaÇÃo"", #(lf)#(tab)#(tab)#(tab)#(tab)T1.""proprietÁrio"", #(lf)#(tab)#(tab)#(tab)#(tab)T1.fazenda, #(lf)#(tab)#(tab)#(tab)#(tab)T1.retiro,#(lf)#(tab)#(tab)#(tab)#(tab)T1.MES,#(lf)#(tab)#(tab)#(tab)#(tab)T1.ANO#(lf)#(tab)#(tab)) T1 ON T1.""proprietÁrio"" = T0.""proprietÁrio"" AND T1.fazenda = T0.fazenda AND  T1.ANO = SUBSTRING(T0.""DATA"" FROM 1 FOR 4) AND T1.MES = SUBSTRING(T0.""DATA"" FROM 6 FOR 2)#(lf)#(tab)) AS T1#(lf)) AS T#(lf)--where t.fazenda = 'CÁCERES'#(lf)"),
    #"Valor Substituído" = Table.ReplaceValue(Fonte," 00:00:00.000","",Replacer.ReplaceText,{"DATA"}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Valor Substituído",{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### pecuarioCompras
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ FROM ""DATABASE"".stg_fcompras T#(lf)"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### pecuarioMortes
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,unaccent(REPLACE(concat(T.""proprietÁrio"",T.fazenda),' ','')) as PROP_FAZ,SUBSTRING(T.""DATA"" from 1 for 10) as DATA FROM ""DATABASE"".stg_fmortes T"),
    #"Valor Substituído" = Table.ReplaceValue(Fonte," 00:00:00.000","",Replacer.ReplaceText,{"DATA"}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Valor Substituído",{{"data", type date}}),
    #"Colunas Removidas" = Table.RemoveColumns(#"Tipo Alterado",{"DATA"}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Colunas Removidas",{{"data", "DATA"}})
in
    #"Colunas Renomeadas"
```
### financeiroDre
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "#(lf)SELECT#(lf)#(tab)--T.centro_de_custo,#(lf)#(tab)--T.sub_centro,#(lf)#(tab)SUBSTRING(T.data_pag FROM 1 FOR 10) as data_pag,#(lf)#(tab)SUBSTRING(T.data_pag FROM 6 FOR 2) AS MES,#(lf)#(tab)SUBSTRING(T.data_pag FROM 1 FOR 4) AS ANO,#(lf)#(tab)T.""operaÇÃo"",#(lf)#(tab)T.centro_de_custo_bi,#(lf)#(tab)T.sub_centro_bi,#(lf)#(tab)T.""proprietÁrio"",#(lf)#(tab)T.fazenda,#(lf)        unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ,#(lf)#(tab)T.desembolso,#(lf)#(tab)T.custeio,#(lf)#(tab)T.tipo_custeio,#(lf)#(tab)SUM(T.valor) as valor--,#(lf)#(tab)--T1.meta#(lf)FROM ""DATABASE"".stg_fdre T#(lf)#(tab)-- where T.""proprietÁrio"" ilike '%SERGIO%' and T.data_pag like '%2026/05%' and t.centro_de_custo_bi ilike '%insumo%'#(lf)#(lf)--WHERE T.""proprietÁrio"" = 'CARLA DE FREITAS'#(lf)#(tab) -- AND T.centro_de_custo_bi = 'Dividendos'#(lf)#(tab) -- AND T.sub_centro_bi = 'Salários e Encargos Rebanho'#(lf)#(tab) -- AND SUBSTRING(T.data_pag FROM 6 FOR 2) = '07'#(lf)#(tab) -- AND SUBSTRING(T.data_pag FROM 1 FOR 4) = '2024'#(lf)GROUP BY #(lf)#(tab)T.centro_de_custo,#(lf)#(tab)T.sub_centro,#(lf)#(tab)T.data_pag,#(lf)#(tab)T.""operaÇÃo"",#(lf)#(tab)T.centro_de_custo_bi,#(lf)#(tab)T.sub_centro_bi,#(lf)#(tab)T.""proprietÁrio"",#(lf)#(tab)T.fazenda,#(lf)#(tab)T.desembolso,#(lf)#(tab)T.custeio,#(lf)#(tab)T.tipo_custeio"),
    #"Valor Substituído" = Table.ReplaceValue(Fonte," 00:00:00.000","",Replacer.ReplaceText,{"data_pag"}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Valor Substituído",{{"data_pag", type date}}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Tipo Alterado",{{"desembolso", "desembolso-CAT"}, {"custeio", "custeio-CAT"}, {"tipo_custeio", "tipo_custeio-CAT"}})
in
    #"Colunas Renomeadas"
```
### fMovGado
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ FROM ""DATABASE"".stg_fmovgado t"),
    #"Valor Substituído" = Table.ReplaceValue(Fonte," 00:00:00.000","",Replacer.ReplaceText,{"DATA"}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Valor Substituído",{{"DATA", type date}}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Tipo Alterado",{{"operaÇÃo", "OPERAÇÃO"}, {"qtd", "QTD"}})
in
    #"Colunas Renomeadas"
```
### dCalendar
```m
let
    DataInicio = #date(2024, 7, 1),
    DataFinal = Date.From(DateTime.LocalNow()),
    QuantidadeDias = Duration.Days(DataFinal - DataInicio) + 1,
    ListDate = List.Dates(DataInicio, QuantidadeDias, #duration(1, 0, 0, 0)),
    #"Convertido para Tabela" = Table.FromList(ListDate, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Convertido para Tabela",{{"Column1", type date}}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Tipo Alterado",{{"Column1", "Data"}}),
    #"Ano Inserido" = Table.AddColumn(#"Colunas Renomeadas", "Ano", each Date.Year([Data]), Int64.Type),
    #"Mês Inserido" = Table.AddColumn(#"Ano Inserido", "Mês", each Date.Month([Data]), Int64.Type),
    #"Nome do Mês Inserido" = Table.AddColumn(#"Mês Inserido", "Nome do Mês", each Date.MonthName([Data]), type text),
    #"Coluna Personalizada Adicionada" = Table.AddColumn(#"Nome do Mês Inserido", "mesano", each Text.Combine({Date.ToText([Data], "MMM"), "-", Date.ToText([Data], "yy")}), type text),

    // Cálculo do ano safra (anosafra no formato jul-23/24)
    #"AnoSafra Adicionado" = Table.AddColumn(#"Coluna Personalizada Adicionada", "anosafra", each 
        let
            mes = Date.Month([Data]),
            ano_inicio = if mes >= 7 then Date.Year([Data]) else Date.Year([Data]) - 1,
            ano_fim = Text.End(Text.From(ano_inicio + 1), 2),
            label = Text.Lower(Date.ToText([Data], "MMM")) & "-" & Text.End(Text.From(ano_inicio), 2) & "/" & ano_fim
        in
            label, type text),

    // Ordem da safra (jul = 1, ..., jun = 12)
    #"OrdemSafra Adicionada" = Table.AddColumn(#"AnoSafra Adicionado", "OrdemSafra", each 
        let
            mes = Date.Month([Data]),
            ordem = if mes >= 7 then mes - 6 else mes + 6
        in
            ordem, Int64.Type),

    // Nome da safra completa (ex: Safra 2023/24)
    #"Safra Adicionada" = Table.AddColumn(#"OrdemSafra Adicionada", "safra", each 
        let
            mes = Date.Month([Data]),
            ano_inicio = if mes >= 7 then Date.Year([Data]) else Date.Year([Data]) - 1,
            ano_fim = Text.End(Text.From(ano_inicio+1), 2)
        in
            "Safra " & Text.From(ano_inicio) & "/" & ano_fim, type text),

    // Chave de ordenação completa (ex: 202301 para jul-23/24)
    #"OrdemAnoSafra Adicionada" = Table.AddColumn(#"Safra Adicionada", "OrdemAnoSafra", each 
        let
            mes = Date.Month([Data]),
            ano_inicio = if mes >= 7 then Date.Year([Data]) else Date.Year([Data]) - 1,
            ordem_mes = if mes >= 7 then mes - 6 else mes + 6
        in
            ano_inicio * 100 + ordem_mes, Int64.Type)
in
    #"OrdemAnoSafra Adicionada"
```
### Categorias
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT DISTINCT(CATEGORIA_BI),SEXO FROM ""DATABASE"".STG_FMOVGADO"),
    #"Colunas Renomeadas" = Table.RenameColumns(Fonte,{{"sexo", "gender"}})
in
    #"Colunas Renomeadas"
```
### Tabela
```m
let
    Fonte = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i45WckxKLElVitWJVnLNVQgAsmIB", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [TipoVenda = _t]),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"TipoVenda", type text}})
in
    #"Tipo Alterado"
```
### fUnidades
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ FROM ""DATABASE"".STG_UNIDADES T where t.projeto is not null#(lf)#(lf)"),
    #"Colunas Renomeadas" = Table.RenameColumns(Fonte,{{"prop_faz", "PROP_FAZ"}})
in
    #"Colunas Renomeadas"
```
### fMetasCompras
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ  FROM ""DATABASE"".stg_fmetascompras t#(lf)"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}}),
    #"Coluna Duplicada" = Table.DuplicateColumn(#"Tipo Alterado", "proprietÁrio", "proprietÁrio - Copiar"),
    #"Coluna Duplicada1" = Table.DuplicateColumn(#"Coluna Duplicada", "fazenda", "fazenda - Copiar"),
    #"Colunas Mescladas" = Table.CombineColumns(#"Coluna Duplicada1",{"proprietÁrio - Copiar", "fazenda - Copiar"},Combiner.CombineTextByDelimiter("", QuoteStyle.None),"PROP_FAZ")
in
    #"Colunas Mescladas"
```
### fMetasAbate
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "#(lf)SELECT #(lf)#(tab)CASE #(lf)       WHEN regexp_replace(""DATA"", '[^0-9]', '', 'g') ~ '^[0-9]{7,8}$' THEN#(lf)            CASE #(lf)                -- Tenta formato ISO (YYYYMMDD) - Ex: 18991231 ou 20260101#(lf)                WHEN left(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 4)::int BETWEEN 1800 AND 2100 #(lf)                     AND substring(regexp_replace(""DATA"", '[^0-9]', '', 'g') from 5 for 2)::int BETWEEN 1 AND 12#(lf)                THEN to_date(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 'YYYYMMDD')#(lf)#(lf)                -- Tenta formato Brasileiro (DDMMYYYY) - Ex: 31121899#(lf)                WHEN right(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 4)::int BETWEEN 1800 AND 2100#(lf)                     AND substring(lpad(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 8, '0') from 3 for 2)::int BETWEEN 1 AND 12#(lf)                THEN to_date(lpad(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 8, '0'), 'DDMMYYYY')#(lf)#(lf)                ELSE NULL #(lf)            END#(lf)        ELSE NULL #(lf)    END AS ""DATA_2"",*,#(lf)       unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ#(lf) FROM ""DATABASE"".stg_fmetasabates t"),
    #"Colunas Renomeadas" = Table.RenameColumns(Fonte,{{"DATA", "DATA_OLD"}, {"DATA_2", "DATA"}}),
    #"Valor Substituído" = Table.ReplaceValue(#"Colunas Renomeadas","ABATE","Abate",Replacer.ReplaceText,{"operaÇÃo"})
in
    #"Valor Substituído"
```
### fMetasEmPe
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "#(lf)SELECT #(lf)#(tab)CASE #(lf)       WHEN regexp_replace(""DATA"", '[^0-9]', '', 'g') ~ '^[0-9]{7,8}$' THEN#(lf)            CASE #(lf)                -- Tenta formato ISO (YYYYMMDD) - Ex: 18991231 ou 20260101#(lf)                WHEN left(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 4)::int BETWEEN 1800 AND 2100 #(lf)                     AND substring(regexp_replace(""DATA"", '[^0-9]', '', 'g') from 5 for 2)::int BETWEEN 1 AND 12#(lf)                THEN to_date(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 'YYYYMMDD')#(lf)#(lf)                -- Tenta formato Brasileiro (DDMMYYYY) - Ex: 31121899#(lf)                WHEN right(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 4)::int BETWEEN 1800 AND 2100#(lf)                     AND substring(lpad(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 8, '0') from 3 for 2)::int BETWEEN 1 AND 12#(lf)                THEN to_date(lpad(regexp_replace(""DATA"", '[^0-9]', '', 'g'), 8, '0'), 'DDMMYYYY')#(lf)#(lf)                ELSE NULL #(lf)            END#(lf)        ELSE NULL #(lf)    END AS ""DATA_2"",*,#(lf)       unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ#(lf) FROM ""DATABASE"".stg_fmetasempe t"),
    #"Colunas Renomeadas" = Table.RenameColumns(Fonte,{{"DATA", "DATA_OLD"}, {"DATA_2", "DATA"}}),
    #"Valor Substituído" = Table.ReplaceValue(#"Colunas Renomeadas","EMPÉ","Em Pe",Replacer.ReplaceText,{"operaÇÃo"})
in
    #"Valor Substituído"
```
### fMetasNascimentos
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,#(lf)       unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ#(lf)FROM ""DATABASE"".stg_fmetasnascimento t#(lf)"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### fMetasMortes
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,#(lf)       unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ#(lf) FROM ""DATABASE"".stg_fmetasmorte t#(lf)"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### fMetasDre
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT #(lf)CASE #(lf)        -- 1. Normalização: Remove tudo que não é número#(lf)        WHEN regexp_replace(data_pag, '[^0-9]', '', 'g') ~ '^[0-9]{7,8}$' THEN#(lf)            CASE #(lf)                -- Tenta formato ISO (YYYYMMDD) - Ex: 18991231 ou 20260101#(lf)                WHEN left(regexp_replace(data_pag, '[^0-9]', '', 'g'), 4)::int BETWEEN 1800 AND 2100 #(lf)                     AND substring(regexp_replace(data_pag, '[^0-9]', '', 'g') from 5 for 2)::int BETWEEN 1 AND 12#(lf)                THEN to_date(regexp_replace(data_pag, '[^0-9]', '', 'g'), 'YYYYMMDD')#(lf)#(lf)                -- Tenta formato Brasileiro (DDMMYYYY) - Ex: 31121899#(lf)                WHEN right(regexp_replace(data_pag, '[^0-9]', '', 'g'), 4)::int BETWEEN 1800 AND 2100#(lf)                     AND substring(lpad(regexp_replace(data_pag, '[^0-9]', '', 'g'), 8, '0') from 3 for 2)::int BETWEEN 1 AND 12#(lf)                THEN to_date(lpad(regexp_replace(data_pag, '[^0-9]', '', 'g'), 8, '0'), 'DDMMYYYY')#(lf)#(lf)                ELSE NULL #(lf)            END#(lf)        ELSE NULL #(lf)    END AS data_pag_corrigida,#(lf)#(tab)#(tab)*,#(lf)       unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ#(lf)FROM ""DATABASE"".stg_fmetasdre t#(lf)"),
    #"Valor Substituído" = Table.ReplaceValue(Fonte," 00:00:00.000","",Replacer.ReplaceText,{"data_pag"}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Valor Substituído",{{"desembolso", "desembolso-CAT"}, {"custeio", "custeio-CAT"}, {"tipo_custeio", "tipo_custeio-CAT"}, {"data_pag", "data_pag_old"}, {"data_pag_corrigida", "data_pag"}})
in
    #"Colunas Renomeadas"
```
### fMetasRebanhoMedio
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,#(lf)       unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ#(lf)FROM ""DATABASE"".stg_fmetasrebanhomedio t"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### RLS
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,unaccent(REPLACE(concat(T.""proprietÁrio"",T.""NOME DO PROJETO (FAZENDA)""),' ','')) as PROP_FAZ FROM ""DATABASE"".stg_rls t#(lf)"),
    #"Colunas Não Dinâmicas" = Table.UnpivotOtherColumns(Fonte, {"base", "CÓDIGO DO CLIENTE", "proprietÁrio", "cliente", "NOME DO PROJETO (FAZENDA)", "tÉcnico", "prop_faz"}, "Atributo", "Valor"),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Colunas Não Dinâmicas",{{"Valor", "e-mail"}, {"Atributo", "tipo-email"}}),
    #"Duplicatas Removidas" = Table.Distinct(#"Colunas Renomeadas", {"e-mail", "prop_faz", "tÉcnico", "NOME DO PROJETO (FAZENDA)", "cliente", "proprietÁrio", "CÓDIGO DO CLIENTE", "base"})
in
    #"Duplicatas Removidas"
```
### fArea
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT *,unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ #(lf)FROM ""DATABASE"".STG_AREA T where t.projeto is not null"),
    #"Colunas Renomeadas" = Table.RenameColumns(Fonte,{{"prop_faz", "PROP_FAZ"}}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Colunas Renomeadas",{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### planejadoXRealizado
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", ";WITH prop AS#(lf)(#(lf)#(tab)select#(lf)#(tab)#(tab)t.""proprietÁrio"",#(lf)#(tab)#(tab)t.fazenda,#(lf)#(tab)#(tab)unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ#(lf)#(tab)from ""DATABASE"".stg_unidades t#(lf)#(tab)where t.""proprietÁrio"" is not null#(lf)),#(lf)c_custo AS#(lf)(#(lf)#(tab)SELECT #(lf)#(tab)#(tab)DISTINCT(t.CENTRO_DE_CUSTO_BI) as CENTRO_DE_CUSTO_BI,#(lf)#(tab)#(tab)t1.""proprietÁrio"",#(lf)#(tab)#(tab)t1.fazenda,#(lf)#(tab)#(tab)t1.PROP_FAZ#(lf)#(tab)FROM ""DATABASE"".STG_FDRE t#(lf)#(tab)CROSS JOIN prop t1#(lf)#(tab)WHERE CENTRO_DE_CUSTO_BI IS NOT NULL --and t.CENTRO_DE_CUSTO_BI like '%Rebanho%'#(lf)),#(lf)datas AS#(lf)(#(lf)#(tab)SELECT #(lf)#(tab)#(tab)DISTINCT DATE_TRUNC('month', T.data_padronizada)::DATE AS primeiro_dia_do_mes#(lf)#(tab)#(lf)#(tab)FROM#(lf)#(tab)(#(lf)#(tab)#(tab)SELECT #(lf)#(tab)#(tab)#(tab)CASE#(lf)#(tab)#(tab)#(tab)#(tab)#(lf)#(tab)#(tab)#(tab)#(tab)WHEN SUBSTRING(T.data_pag FROM 1 FOR 10) ~ '^\d{4}/\d{2}/\d{2}$' THEN#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)TO_DATE(SUBSTRING(T.data_pag FROM 1 FOR 10), 'YYYY/MM/DD')#(lf)#(lf)#(tab)#(tab)#(tab)#(lf)#(tab)#(tab)#(tab)#(tab)WHEN SUBSTRING(T.data_pag FROM 1 FOR 10) ~ '^\d{2}/\d{2}/\d{4}$' THEN#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)TO_DATE(SUBSTRING(T.data_pag FROM 1 FOR 10), 'DD/MM/YYYY')#(lf)#(lf)#(tab)#(tab)#(tab)#(tab)ELSE#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)NULL #(lf)#(tab)#(tab)#(tab)END AS data_padronizada#(lf)#(tab)#(tab)#(tab)FROM ""DATABASE"".STG_FDRE T#(lf)#(lf)#(tab)#(tab)#(tab)UNION ALL#(lf)#(lf)#(tab)#(tab)#(tab)SELECT #(lf)#(tab)#(tab)#(tab)CASE#(lf)#(tab)#(tab)#(tab)#(tab)#(lf)#(tab)#(tab)#(tab)#(tab)WHEN SUBSTRING(T.data_pag FROM 1 FOR 10) ~ '^\d{4}/\d{2}/\d{2}$' THEN#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)TO_DATE(SUBSTRING(T.data_pag FROM 1 FOR 10), 'YYYY/MM/DD')#(lf)#(lf)#(tab)#(tab)#(tab)#(tab)WHEN SUBSTRING(T.data_pag FROM 1 FOR 10) ~ '^\d{2}/\d{2}/\d{4}$' THEN#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)TO_DATE(SUBSTRING(T.data_pag FROM 1 FOR 10), 'DD/MM/YYYY')#(lf)#(tab)#(tab)#(tab)#(tab)ELSE#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)NULL #(lf)#(tab)#(tab)#(tab)END AS data_padronizada#(lf)#(tab)#(tab)#(tab)FROM ""DATABASE"".STG_FMETASDRE T#(lf)#(tab)#(lf)#(tab)) T#(lf)#(lf)),#(lf)base as#(lf)(#(lf)#(tab)SELECT#(lf)#(tab)#(tab)C.""proprietÁrio"",#(lf)#(tab)#(tab)C.fazenda,#(lf)#(tab)#(tab)C.prop_faz,#(lf)#(tab)#(tab)C.CENTRO_DE_CUSTO_BI,#(lf)#(tab)#(tab)--C.desembolso,#(lf)#(tab)#(tab)--C.custeio,#(lf)#(tab)#(tab)--C.tipo_custeio,#(lf)#(tab)#(tab)D.primeiro_dia_do_mes#(lf)#(tab)FROM#(lf)#(tab)#(tab)c_custo C#(lf)#(tab)CROSS JOIN#(lf)#(tab)#(tab)datas D#(lf)#(tab)WHERE D.primeiro_dia_do_mes IS NOT NULL#(lf)),#(lf)previsto AS (#(lf)#(lf)SELECT#(tab)#(lf)#(tab)T.centro_de_custo_bi,#(lf)#(tab)T.""proprietÁrio"",#(lf)#(tab)T.fazenda,#(lf)#(tab)T.PROP_FAZ,#(lf)#(tab)DATE_TRUNC('month', T.data_pag)::DATE AS data_pag,#(lf)#(tab)--T.desembolso,#(lf)#(tab)--T.custeio,#(lf)#(tab)--T.tipo_custeio,#(lf)#(tab)T.META#(tab)#(lf)FROM#(lf)(#(lf)#(tab)SELECT#(lf)#(tab)#(tab)T.centro_de_custo_bi,#(lf)#(tab)#(tab)T.""proprietÁrio"",#(lf)#(tab)#(tab)--T.data_pag,#(lf)#(tab)#(tab)CASE#(tab)#(lf)#(tab)#(tab)#(tab)WHEN SUBSTRING(T.data_pag FROM 1 FOR 10) ~ '^\d{4}/\d{2}/\d{2}$' THEN#(lf)#(tab)#(tab)#(tab)#(tab)TO_DATE(SUBSTRING(T.data_pag FROM 1 FOR 10), 'YYYY/MM/DD')#(lf)#(lf)#(lf)#(tab)#(tab)#(tab)WHEN SUBSTRING(T.data_pag FROM 1 FOR 10) ~ '^\d{2}/\d{2}/\d{4}$' THEN#(lf)#(tab)#(tab)#(tab)#(tab)TO_DATE(SUBSTRING(T.data_pag FROM 1 FOR 10), 'DD/MM/YYYY')#(lf)#(lf)#(tab)#(tab)#(tab)ELSE#(lf)#(tab)#(tab)#(tab)#(tab)NULL #(lf)#(tab)#(tab)END AS data_pag,#(lf)#(tab)#(tab)T.fazenda,#(lf)#(tab)    unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ,#(lf)#(tab)#(tab)--T.desembolso,#(lf)#(tab)#(tab)--T.custeio,#(lf)#(tab)#(tab)--T.tipo_custeio,#(lf)#(tab)#(tab)SUM(T.valor) as META#(lf)#(tab)FROM ""DATABASE"".stg_fmetasdre T#(lf)#(tab)GROUP BY#(lf)#(tab)#(tab)T.""proprietÁrio"",#(lf)#(tab)#(tab)T.fazenda,#(lf)#(tab)#(tab)T.centro_de_custo_bi,#(lf)#(tab)#(tab)--T.desembolso,#(lf)#(tab)#(tab)--T.custeio,#(lf)#(tab)#(tab)--T.tipo_custeio,#(lf)#(tab)#(tab)T.data_pag#(lf)#(tab)) T#(lf)),#(lf)realizado AS#(lf)(#(lf)SELECT#(lf)#(tab)T.""operaÇÃo"",#(lf)#(tab)T.centro_de_custo_bi,#(lf)#(tab)T.""proprietÁrio"",#(lf)#(tab)T.fazenda,#(lf)#(tab)T.PROP_FAZ,#(lf)#(tab)DATE_TRUNC('month', T.data_pag)::DATE AS data_pag,#(lf)#(tab)--T.desembolso,#(lf)#(tab)--T.custeio,#(lf)#(tab)--T.tipo_custeio,#(lf)#(tab)T.valor#(lf)#(tab)#(lf)#(tab)#(lf)FROM#(lf)#(tab)(#(lf)#(tab)SELECT#(lf)#(tab)#(tab)CASE#(tab)#(lf)#(tab)#(tab)#(tab)WHEN SUBSTRING(T.data_pag FROM 1 FOR 10) ~ '^\d{4}/\d{2}/\d{2}$' THEN#(lf)#(tab)#(tab)#(tab)#(tab)TO_DATE(SUBSTRING(T.data_pag FROM 1 FOR 10), 'YYYY/MM/DD')#(lf)#(lf)#(lf)#(tab)#(tab)#(tab)WHEN SUBSTRING(T.data_pag FROM 1 FOR 10) ~ '^\d{2}/\d{2}/\d{4}$' THEN#(lf)#(tab)#(tab)#(tab)#(tab)TO_DATE(SUBSTRING(T.data_pag FROM 1 FOR 10), 'DD/MM/YYYY')#(lf)#(lf)#(tab)#(tab)#(tab)ELSE#(lf)#(tab)#(tab)#(tab)#(tab)NULL #(lf)#(tab)#(tab)END AS data_pag,#(lf)#(tab)#(tab)T.""operaÇÃo"",#(lf)#(tab)#(tab)T.centro_de_custo_bi,#(lf)#(tab)#(tab)T.""proprietÁrio"",#(lf)#(tab)#(tab)T.fazenda,#(lf)#(tab)#(tab)unaccent(REPLACE(concat(t.""proprietÁrio"",t.fazenda),' ','')) as PROP_FAZ,#(lf)#(tab)#(tab)--T.desembolso,#(lf)#(tab)#(tab)--T.custeio,#(lf)#(tab)#(tab)--T.tipo_custeio,#(lf)#(tab)#(tab)SUM(T.valor) as valor#(lf)#(tab)FROM ""DATABASE"".stg_fdre T#(lf)#(tab)GROUP BY #(lf)#(tab)#(tab)T.centro_de_custo,#(lf)#(tab)#(tab)--T.sub_centro,#(lf)#(tab)#(tab)T.data_pag,#(lf)#(tab)#(tab)T.""operaÇÃo"",#(lf)#(tab)#(tab)T.centro_de_custo_bi,#(lf)#(tab)#(tab)T.""proprietÁrio"",#(lf)#(tab)#(tab)T.fazenda,#(lf)#(tab)#(tab)--T.desembolso,#(lf)#(tab)#(tab)--T.custeio,#(lf)#(tab)#(tab)--T.tipo_custeio,#(lf)#(tab)#(tab)T.valor#(lf)#(tab)) T#(lf)),#(lf)dados AS #(lf)(#(lf)SELECT#(lf)#(tab)T.PROp_FAZ,#(lf)#(tab)T.""proprietÁrio"",#(lf)#(tab)T.fazenda,#(lf)#(tab)T.centro_de_custo_bi,#(lf)#(tab)CASE#(lf)#(tab)#(tab)WHEN T.centro_de_custo_bi IN (#(lf)#(tab)#(tab)#(tab)'Arrendamento',#(lf)#(tab)#(tab)#(tab)'Cultura - Receita',#(lf)#(tab)#(tab)#(tab)'Rebanho',#(lf)#(tab)#(tab)#(tab)'Receitas financeiras',#(lf)#(tab)#(tab)#(tab)'Receitas outros',#(lf)#(tab)#(tab)#(tab)'Receitas Parque de máquinas',#(lf)#(tab)#(tab)#(tab)'Vendas outros animais'#(lf)#(tab)#(tab)) THEN 'A - RECEITAS'#(lf)#(lf)#(tab)#(tab)WHEN T.centro_de_custo_bi IN (#(lf)#(tab)#(tab)#(tab)'Investimentos em infraestrutura',#(lf)#(tab)#(tab)#(tab)'Investimentos em outros animais',#(lf)#(tab)#(tab)#(tab)'Investimentos em RH',#(lf)#(tab)#(tab)#(tab)'Rebanho Investimento'#(lf)#(tab)#(tab)) THEN 'C - INVESTIMENTOS'#(lf)#(lf)#(tab)#(tab)WHEN T.centro_de_custo_bi IN (#(lf)#(tab)#(tab)#(tab)'Algodão',#(lf)#(tab)#(tab)#(tab)'Aveia',#(lf)#(tab)#(tab)#(tab)'Feno',#(lf)#(tab)#(tab)#(tab)'Forrageiras e Culturas Anuais',#(lf)#(tab)#(tab)#(tab)'Insumos do rebanho',#(lf)#(tab)#(tab)#(tab)'Manutenção da fazenda',#(lf)#(tab)#(tab)#(tab)'Mão de Obra Geral',#(lf)#(tab)#(tab)#(tab)'Mão de Obra Permanente Administração',#(lf)#(tab)#(tab)#(tab)'Mão de Obra Permanente Cultura',#(lf)#(tab)#(tab)#(tab)'Mão de Obra Permanente Manutenção da Fazenda',#(lf)#(tab)#(tab)#(tab)'Mão de Obra Permanente Parque de Máquinas',#(lf)#(tab)#(tab)#(tab)'Mão de Obra Permanente Rebanho',#(lf)#(tab)#(tab)#(tab)'Milho Safrinha',#(lf)#(tab)#(tab)#(tab)'Milho Verão',#(lf)#(tab)#(tab)#(tab)'Outros animais',#(lf)#(tab)#(tab)#(tab)'Pastagens',#(lf)#(tab)#(tab)#(tab)'Silagem de Capiaçu',#(lf)#(tab)#(tab)#(tab)'Silagem de Capim',#(lf)#(tab)#(tab)#(tab)'Silagem de Milheto',#(lf)#(tab)#(tab)#(tab)'Silagem de Milho',#(lf)#(tab)#(tab)#(tab)'Silagem de Sorgo',#(lf)#(tab)#(tab)#(tab)'Soja',#(lf)#(tab)#(tab)#(tab)'Sorgo Grão',#(lf)#(tab)#(tab)#(tab)'Suporte à Produção Administração',#(lf)#(tab)#(tab)#(tab)'Suporte à Produção Parque de máquinas',#(lf)#(tab)#(tab)#(tab)'Taxas e impostos'#(lf)#(tab)#(tab)) THEN 'D - CUSTEIO'#(lf)#(lf)#(tab)#(tab)WHEN T.centro_de_custo_bi IN (#(lf)#(tab)#(tab)#(tab)'Empréstimos sócios crédito',#(lf)#(tab)#(tab)#(tab)'Financiamentos créditos'#(lf)#(tab)#(tab)) THEN 'E - OUTROS CRÉDITOS'#(lf)#(lf)#(tab)#(tab)WHEN T.centro_de_custo_bi IN (#(lf)#(tab)#(tab)#(tab)'Dividendos',#(lf)#(tab)#(tab)#(tab)'Empréstimos sócios débito',#(lf)#(tab)#(tab)#(tab)'Financiamentos débitos',#(lf)#(tab)#(tab)#(tab)'Outros Débitos'#(lf)#(tab)#(tab)) THEN 'F - OUTROS DÉBITOS'#(lf)#(lf)#(tab)#(tab)WHEN T.centro_de_custo_bi IN (#(lf)#(tab)#(tab)#(tab)'Almoxarifado',#(lf)#(tab)#(tab)#(tab)'Aporte de capital',#(lf)#(tab)#(tab)#(tab)'Prejuízo Administração',#(lf)#(tab)#(tab)#(tab)'Venda de Imóveis'#(lf)#(tab)#(tab)) THEN '' -- Retorna string vazia (equivalente ao """" no DAX)#(lf)#(lf)#(tab)#(tab)ELSE NULL -- Valor padrão se não corresponder a nenhuma das opções acima#(lf)#(tab)END AS Classificacao,#(lf)#(tab)--t.desembolso,#(lf)#(tab)--t.custeio,#(lf)#(tab)--t.tipo_custeio,#(lf)#(tab)T.primeiro_dia_do_mes as data,#(lf)#(tab)T1.meta,#(lf)#(tab)#(lf)#(tab)CAST(SUM(T2.valor) as numeric(10,2)) as realizado#(lf)FROM base T#(lf)LEFT JOIN previsto T1 ON T1.PROP_FAZ = T.PROP_FAZ #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)  AND EXTRACT(YEAR FROM T.primeiro_dia_do_mes) = EXTRACT(YEAR FROM T1.data_pag)#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)  AND EXTRACT(MONTH FROM T.primeiro_dia_do_mes) = EXTRACT(MONTH FROM T1.data_pag)#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)  AND T.centro_de_custo_bi = T1.centro_de_custo_bi#(lf)LEFT JOIN realizado T2 ON T2.PROP_FAZ = T.PROP_FAZ #(lf)#(tab)#(tab)#(tab)#(tab)#(tab)  AND EXTRACT(YEAR FROM T.primeiro_dia_do_mes) = EXTRACT(YEAR FROM T2.data_pag)#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)  AND EXTRACT(MONTH FROM T.primeiro_dia_do_mes) = EXTRACT(MONTH FROM T2.data_pag)#(lf)#(tab)#(tab)#(tab)#(tab)#(tab)  AND T.centro_de_custo_bi = T2.centro_de_custo_bi#(lf)where T1.meta is not null or t2.valor is not null --T.""proprietÁrio""  like '%CARLA ROSANA DE FREITAS%'#(lf)--#(tab) #(tab)  AND t.primeiro_dia_do_mes = '2025/10/01' AND T.centro_de_custo_bi like '%infra%'#(lf)#(lf)group by#(lf)#(tab)T.PROp_FAZ,#(lf)#(tab)T.""proprietÁrio"",#(lf)#(tab)T.fazenda,#(lf)#(tab)T.centro_de_custo_bi,#(lf)#(tab)--t.desembolso,#(lf)#(tab)--t.custeio,#(lf)#(tab)--t.tipo_custeio,#(lf)#(tab)T.primeiro_dia_do_mes,#(lf)#(tab)T1.meta#(lf))#(lf)#(lf)SELECT#(lf)#(tab)T.PROP_FAZ,#(lf)#(tab)T.""proprietÁrio"",#(lf)#(tab)T.fazenda,#(lf)#(tab)T.centro_de_custo_bi,#(lf)#(tab)T.classificacao,#(lf)#(tab)t.data,#(lf)#(tab)sum(t.meta) as meta,#(lf)#(tab)t.realizado#(lf)FROM#(lf)(#(lf)#(tab)select#(lf)#(tab)#(tab)*#(lf)#(tab)from dados T#(lf)#(lf)#(tab)union all#(lf)#(lf)#(tab)select#(lf)#(tab)#(tab)T1.PROp_FAZ,#(lf)#(tab)#(tab)T1.""proprietÁrio"",#(lf)#(tab)#(tab)T1.fazenda,#(lf)#(tab)#(tab)'DESEMBOLSO' AS centro_de_custo_bi,#(lf)#(tab)#(tab)'B - DESEMBOLSO' as  Classificacao,#(lf)#(tab)#(tab)--t1.desembolso,#(lf)#(tab)#(tab)--t1.custeio,#(lf)#(tab)#(tab)--t1.tipo_custeio,#(lf)#(tab)#(tab)T1.data,#(lf)#(tab)#(tab)T1.meta,#(lf)#(tab)#(tab)ROUND(T1.realizado::numeric, 2) as realizado#(lf)#(tab)#(tab)--cast(T1.realizado as numeric(10,2)) as realizado #(lf)#(tab)from dados T1#(lf)#(tab)where t1.classificacao in ('C - INVESTIMENTOS','D - CUSTEIO') #(lf)) T #(lf)--WHERE T.fazenda = 'NOVA BAHIA' and T.centro_de_custo_bi = 'Insumos do rebanho'#(lf)GROUP BY#(lf)#(tab)T.PROP_FAZ,#(lf)#(tab)T.""proprietÁrio"",#(lf)#(tab)T.fazenda,#(lf)#(tab)T.centro_de_custo_bi,#(lf)#(tab)T.classificacao,#(lf)#(tab)t.data,#(lf)#(tab)--t.meta,#(lf)#(tab)t.realizado")
in
    Fonte
```
### fTransferencias
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT #(lf)#(tab)""operaÇÃo"", #(lf)#(tab)""DATA"",#(lf)#(tab)categoria_fazenda,#(lf)#(tab)qtd,#(lf)#(tab)peso_vivo,#(lf)#(tab)total_peso, #(lf)#(tab)""VALOR TOTAL"",#(lf)#(tab)data_abrev,#(lf)#(tab)categoria_bi,#(lf)#(tab)sexo,#(lf)#(tab)peso_arroba,#(lf)#(tab)valor_cab, #(lf)#(tab)valo_kg,#(lf)#(tab)valor_arroba,#(lf)#(tab)""proprietÁrio"", #(lf)#(tab)fazenda, #(lf)#(tab)retiro,#(lf)#(tab)unaccent(REPLACE(concat(""proprietÁrio"",fazenda),' ','')) as PROP_FAZ#(lf)FROM ""DATABASE"".stg_ftransfentrada#(lf)#(lf)union all#(lf)#(lf)SELECT #(lf)#(tab)""operaÇÃo"",#(lf)#(tab)""DATA"", #(lf)#(tab)categoria_fazenda, #(lf)#(tab)qtd,#(lf)#(tab)peso_vivo,#(lf)#(tab)total_peso,#(lf)#(tab)""VALOR TOTAL"", #(lf)#(tab)data_abrev, #(lf)#(tab)categoria_bi,#(lf)#(tab)sexo,#(lf)#(tab)peso_arroba,#(lf)#(tab)valor_cab,#(lf)#(tab)valo_kg, #(lf)#(tab)valor_arroba,#(lf)#(tab)""proprietÁrio"",#(lf)#(tab)fazenda, #(lf)#(tab)retiro,#(lf)#(tab)unaccent(REPLACE(concat(""proprietÁrio"",fazenda),' ','')) as PROP_FAZ#(lf)FROM ""DATABASE"".stg_ftransfsaida;"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### fMetasTransferencias
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_PLANILHA", "SELECT #(lf)#(tab)""operaÇÃo"", #(lf)#(tab)""DATA"",#(lf)#(tab)categoria_fazenda,#(lf)#(tab)qtd,#(lf)#(tab)peso_vivo,#(lf)#(tab)total_peso, #(lf)#(tab)""VALOR TOTAL"",#(lf)#(tab)data_abrev,#(lf)#(tab)categoria_bi,#(lf)#(tab)sexo,#(lf)#(tab)peso_arroba,#(lf)#(tab)valor_cab, #(lf)#(tab)valo_kg,#(lf)#(tab)valor_arroba,#(lf)#(tab)""proprietÁrio"", #(lf)#(tab)fazenda, #(lf)#(tab)retiro,#(lf)#(tab)unaccent(REPLACE(concat(""proprietÁrio"",fazenda),' ','')) as PROP_FAZ#(lf)FROM ""DATABASE"".stg_fmetastransfentrada#(lf)#(lf)union all#(lf)#(lf)SELECT #(lf)#(tab)""operaÇÃo"",#(lf)#(tab)""DATA"", #(lf)#(tab)categoria_fazenda, #(lf)#(tab)qtd,#(lf)#(tab)peso_vivo,#(lf)#(tab)total_peso,#(lf)#(tab)""VALOR TOTAL"", #(lf)#(tab)data_abrev, #(lf)#(tab)categoria_bi,#(lf)#(tab)sexo,#(lf)#(tab)peso_arroba,#(lf)#(tab)valor_cab,#(lf)#(tab)valo_kg, #(lf)#(tab)valor_arroba,#(lf)#(tab)""proprietÁrio"",#(lf)#(tab)fazenda, #(lf)#(tab)retiro,#(lf)#(tab)unaccent(REPLACE(concat(""proprietÁrio"",fazenda),' ','')) as PROP_FAZ#(lf)FROM ""DATABASE"".stg_fmetatransfsaida;"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```