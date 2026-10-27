# MODEL DUMP: Projeto Terra - Versão Metryx 12072026 (1).pbix

## Tables & columns (schema)

### Analytics Measures
Column:Int64, Purchased Quantity MALE:Float64
### Categorias
idcustomer:string, customer:string, idcategory:string, category:string, categorygroup:string, agecategory:string, gender:string
### Compras
gender:string, date:datetime64[ns], category:string, amount:Float64, idcustomer:string, customer:string, farmname:string, idretiro:string, retironame:string, owner:string, anosafra:string, provider:string, categoryid:string, weighttotal:Float64, averagevalue:Float64, valueweight:Float64, valuearroba:Float64, totalfaturamento:Float64, harvest:string, birth:string, idpropfaz:string
### DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28
Date:datetime64[ns], Ano:Int64, MonthNo:Int64, Mês:string, QuarterNo:Int64, Trimestre:string, Dia:Int64
### LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3
Date:datetime64[ns], Ano:Int64, MonthNo:Int64, Mês:string, QuarterNo:Int64, Trimestre:string, Dia:Int64
### LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf
Date:datetime64[ns], Ano:Int64, MonthNo:Int64, Mês:string, QuarterNo:Int64, Trimestre:string, Dia:Int64
### LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b
Date:datetime64[ns], Ano:Int64, MonthNo:Int64, Mês:string, QuarterNo:Int64, Trimestre:string, Dia:Int64
### LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04
Date:datetime64[ns], Ano:Int64, MonthNo:Int64, Mês:string, QuarterNo:Int64, Trimestre:string, Dia:Int64
### Parâmetro - Data
Parâmetro - Data:string, Parâmetro - Data Campos:string, Parâmetro - Data Pedido:Int64
### Tabela
TipoVenda:string
### dCalendar
Data:datetime64[ns], Ano:Int64, Mês:Int64, Nome do Mês:string, Classificador Mês-Ano:Int64, mesano:string, anosafra:string, OrdemSafra:Int64, safra:string, OrdemAnoSafra:Int64
### fMetasAbate
pesomorto_total:Float64, idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, idowner:string, ownername:string, idplherdtype:string, plherdtypename:string, idcurrency:string, currencyname:string, month:string, date:datetime64[ns], harvest:string, anosafra:string, idcategory:string, categoryname:string, idanimalgroup:string, animalgroupname:string, age:string, gender:string, amount:Float64, weight:Float64, arrobavalue:Float64, arrobaweight:Float64, value:Float64, totalvalue:Float64, idpropfaz:string, yield:Float64, tipo:string, pesovivo_total:Float64, Total de @:Float64
### fMetasCompras
idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, idowner:string, ownername:string, idplherdtype:string, plherdtypename:string, idcurrency:string, currencyname:string, month:string, date:datetime64[ns], harvest:string, anosafra:string, idcategory:string, categoryname:string, idanimalgroup:string, animalgroupname:string, age:string, gender:string, amount:Float64, weight:Float64, arrobavalue:Float64, arrobaweight:Float64, value:Float64, totalvalue:Float64, idpropfaz:string
### fMetasDre
Desembolso:Float64, F/V:string, Custeio:Float64, idcustomer:string, customer:string, valorprevisto:Float64, valorrealizado:Float64, costcenter:string, uuidcostcenter:string, classname:string, uuidclass:string, subcenter:string, uuidsubcenter:string, product:string, uuidproduct:string, farmname:string, idfarm:string, activity:string, uuidactivity:string, date:datetime64[ns], type:string, classificationanalyticuuid:string, classificationanalyticdescription:string, idpropfaz:string, custeio_cat:string, tipo_custeio_cat:string, desembolso_cat:string
### fMetasEmPe
idpropfaz:string, idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, idowner:string, ownername:string, idplherdtype:string, plherdtypename:string, idcurrency:string, currencyname:string, month:string, date:datetime64[ns], harvest:string, anosafra:string, idcategory:string, categoryname:string, idanimalgroup:string, animalgroupname:string, age:string, gender:string, amount:Float64, weight:Float64, arrobavalue:Float64, arrobaweight:Float64, value:Float64, totalvalue:Float64, yield:Float64, tipo:string, Total de @:Float64, pesovivo_total:Float64, pesomorto_total:Float64
### fMetasMortes
idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, idowner:string, ownername:string, idplherdtype:string, plherdtypename:string, idcurrency:string, currencyname:string, plversioncode:string, plversionname:string, month:string, date:datetime64[ns], harvest:string, anosafra:string, idcategory:string, categoryname:string, idanimalgroup:string, animalgroupname:string, age:string, gender:string, amount:Float64, idpropfaz:string
### fMetasNascimentos
idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, idowner:string, ownername:string, idplherdtype:string, plherdtypename:string, idcurrency:string, currencyname:string, plversioncode:string, plversionname:string, month:Float64, date:datetime64[ns], harvest:string, anosafra:string, idcategory:string, categoryname:string, idanimalgroup:string, animalgroupname:string, age:string, gender:string, amount:Float64, idpropfaz:string
### fMetasRebanhoMedio
idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, owner:string, anosafra:string, amount:Float64, gender:string, idcategory:string, category:string, DATA:datetime64[ns], idpropfaz:string
### fPlanejadoxRealizado
idpropfaz:string, idcustomer:string, idfarm:string, proprietario:string, fazenda:string, costcenter:string, classificacao:string, data:datetime64[ns], meta:Float64, realizado:Float64, Classificacao2:string
### fSaldoGado
farmname:string, retironame:string, owner:string, category:string, UltimaDataMovimentacao:Float64, date:datetime64[ns], data_saldo:datetime64[ns], amountacc:Float64, birth:string, harvest:string, idpropfaz:string
### fUnidades
idcustomer:string, customer:string, idfarm:string, farmname:string, idpropfaz:string
### financeiroDre
Type Operation:object, Desembolso:Float64, Custeio:Float64, Class subcenter:string, F/V:string, idcustomer:string, customer:string, farmfiscal:string, idfarmdestination:string, farmdestination:string, owner:string, idfinancialentrie:string, idpayment:string, anosafra:string, costcenter:string, description:string, code:string, classe:string, subcenter:string, activity:string, doctype:string, conciliationdate:string, datepayment:datetime64[ns], duedate:datetime64[ns], type:string, amountpayable:Float64, amountpaid:Float64, currency:string, status:string, emissiondate:string, parcel:string, idpropfaz:string, custeio_cat:string, tipo_custeio_cat:string, desembolso_cat:string
### pecuarioCompras
Paid:Float64, DATA:datetime64[ns], categ_fazenda:string, qtd:Float64, total_peso:Float64, valor_cab:Float64, VALOR TOTAL:Float64, valo_kg:Float64, valor_arroba:Float64, categoria_bi:string, sexo:string, peso_arroba:Float64, fazenda:string, categoryid:string, idcustomer:string, customer:string, farmname:string, idretiro:string, retironame:string, anosafra:string, provider:string, averagevalue:Float64, valueweight:Float64, Total de @:Float64, idpropfaz:string, proprietArio:string
### pecuarioDesmame
DATA:datetime64[ns], harvest:string, amount:Float64, weight:Float64, gender:string, idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, owner:string, anosafra:string, oldcategory:string, oldcategoryid:string, birthdate:string, newcategory:string, newcategoryid:string, valueweight:Float64, idpropfaz:string
### pecuarioMortes
era:string, safra:string, forecast:Int64, DATA:datetime64[ns], categ_fazenda:string, carimbo_bez:string, qtd:Float64, causa:string, peso_vivo:Float64, grupo_categoria:string, categoria_bi:string, peso_total:Float64, sexo:string, fazenda:string, categoryid:string, pasto:string, enumgroup:string, idfarm:string, idcustomer:string, customer:string, idretiro:string, retironame:string, idpropfaz:string, proprietArio:string
### pecuarioNascimento
idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, owner:string, anosafra:string, idcategory:string, category:string, harvest:string, amount:Float64, gender:string, DATA:datetime64[ns], idpropfaz:string
### pecuarioRebanhoMedioMensal
farm:string, Forecast:object, idcustomer:string, customer:string, idfarm:string, farmname:string, idretiro:string, retironame:string, owner:string, anosafra:string, amount:Float64, gender:string, idcategory:string, category:string, DATA:datetime64[ns], idpropfaz:string
### pecuarioVendaAbate
Total Value:object, teste:object, Peso Morto Total:Float64, Total de @:Float64, tipovenda:string, cliente:string, categ_fazenda:string, DATA:datetime64[ns], qtd:Float64, peso_vivo:Float64, peso_arroba:Float64, valor_arroba:Float64, faturamento:Float64, categoria_bi:string, sexo:string, peso_morto:Float64, pesovivo_total:Float64, pesomorto_total:Float64, valor_kg:Float64, valor_cab:Float64, fazenda:string, retiro:string, idpropfaz:string, proprietArio:string
### pecuarioVendaEmPe
Total de @:Float64, tipovenda:string, Peso Total:Float64, cliente:string, DATA:datetime64[ns], categ_fazenda:string, qtd:Float64, peso_vivo:Float64, pesovivo_total:Float64, valor_arroba:Float64, valor_cab:Float64, faturamento:Float64, categoria_bi:string, sexo:string, valor_kg:Float64, proprietÁrio:string, fazenda:string, retiro:string, Peso Morto:Float64, peso_arroba:Float64, idpropfaz:string

## Row-count / cardinality stats (top)

                                                  TableName                         ColumnName  Cardinality  Dictionary  HashIndex  DataSize         ModifiedTime StructureModifiedTime
0                                        Analytics Measures                             Column            1           0          0       152  2024-10-22 15:56:15   2024-10-22 15:56:15
1                                        Analytics Measures            Purchased Quantity MALE            1           0       1133       152  2026-10-14 14:57:43   2026-05-31 13:38:06
2                                                Categorias                         idcustomer           10         943          0       280  2026-05-01 18:21:59   2026-05-01 18:21:59
3                                                Categorias                           customer           10         747          0       280  2026-05-01 18:21:59   2026-05-01 18:21:59
4                                                Categorias                         idcategory          260        7126          0       448  2026-05-01 18:21:59   2026-05-01 18:21:59
5                                                Categorias                           category          162        7865          0       408  2026-05-01 18:21:59   2026-05-01 18:21:59
6                                                Categorias                      categorygroup            8         415          0       248  2026-05-01 18:21:59   2026-05-01 18:21:59
7                                                Categorias                        agecategory            5         223          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
8                                                Categorias                             gender            2         163          0       184  2026-05-01 18:21:59   2026-05-01 18:21:59
9                                                   Compras                             gender            2         163          0       264  2024-11-09 13:51:42   2024-11-09 13:51:42
10                                                  Compras                               date          661        5328          0      2992  2024-11-09 13:51:42   2026-07-05 16:07:37
11                                                  Compras                           category           81        3983          0      1184  2024-11-09 13:51:42   2024-11-09 13:51:42
12                                                  Compras                             amount          256           0       4309      3560  2024-11-09 13:51:42   2024-11-09 13:51:42
13                                                  Compras                         idcustomer           10         943          0       280  2026-05-01 18:21:59   2026-05-01 18:21:59
14                                                  Compras                           customer           10         747          0       280  2026-05-01 18:21:59   2026-05-01 18:21:59
15                                                  Compras                           farmname           43        1855          0      1072  2026-05-01 18:21:59   2026-05-01 18:21:59
16                                                  Compras                           idretiro           56        4715          0      1096  2026-05-01 18:21:59   2026-05-01 18:21:59
17                                                  Compras                         retironame           40        1531          0       840  2026-05-01 18:21:59   2026-05-01 18:21:59
18                                                  Compras                              owner           33        2221          0       464  2026-05-01 18:21:59   2026-05-01 18:21:59
19                                                  Compras                           anosafra            6         243          0       720  2026-05-01 18:21:59   2026-05-01 18:21:59
20                                                  Compras                           provider          777       17606          0      2992  2026-05-01 18:21:59   2026-05-01 18:21:59
21                                                  Compras                         categoryid           90        7503          0      1184  2026-05-01 18:21:59   2026-05-01 18:21:59
22                                                  Compras                        weighttotal          362           0       8429      2992  2026-05-01 18:21:59   2026-05-01 18:21:59
23                                                  Compras                       averagevalue         1032           0      16725      4416  2026-05-01 18:21:59   2026-05-01 18:21:59
24                                                  Compras                        valueweight           38         344          0      1784  2026-05-01 18:21:59   2026-05-01 18:21:59
25                                                  Compras                        valuearroba          374           0       8397      4416  2026-05-01 18:21:59   2026-05-01 18:21:59
26                                                  Compras                   totalfaturamento         1824           0      33301      8680  2026-05-01 18:21:59   2026-05-01 18:21:59
27                                                  Compras                            harvest            4         203          0       160  2026-05-01 18:21:59   2026-05-01 18:21:59
28                                                  Compras                              birth           16         443          0       176  2026-05-01 18:21:59   2026-05-01 18:21:59
29                                                  Compras                          idpropfaz           45        7053          0      1072  2026-06-14 23:13:07   2026-06-14 23:13:07
30   DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                               Date            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
31   DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                                Ano            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
32   DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                            MonthNo            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
33   DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                                Mês            1         147          0       152  2024-10-21 20:15:01   2024-10-21 20:14:53
34   DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                          QuarterNo            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
35   DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                          Trimestre            1         143          0       152  2024-10-21 20:15:01   2024-10-21 20:14:53
36   DateTableTemplate_921fb57a-bf20-482b-a577-c51ccede3e28                                Dia            1           0       1133       152  2024-10-22 21:19:30   2024-10-21 20:14:53
37      LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3                               Date         4383       35104          0      8912  2026-10-14 14:57:43   2026-05-01 18:21:59
38      LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3                                Ano           12          88          0       152  2026-10-14 14:57:43   2026-05-01 18:21:59
39      LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3                            MonthNo           12          88          0      2336  2026-10-14 14:57:43   2026-05-01 18:21:59
40      LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3                                Mês           12         397          0      2336  2026-10-14 14:57:43   2026-05-01 18:21:59
41      LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3                          QuarterNo            4          56          0       536  2026-10-14 14:57:43   2026-05-01 18:21:59
42      LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3                          Trimestre            4         203          0       536  2026-10-14 14:57:43   2026-05-01 18:21:59
43      LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3                                Dia           31         164          0      3072  2026-10-14 14:57:43   2026-05-01 18:21:59
44      LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf                               Date         1826       14648          0      3072  2026-07-27 21:42:05   2026-05-01 18:21:59
45      LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf                                Ano            5          60          0       152  2026-07-27 21:42:05   2026-05-01 18:21:59
46      LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf                            MonthNo           12          88          0      1064  2026-07-27 21:42:05   2026-05-01 18:21:59
47      LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf                                Mês           12         397          0      1064  2026-07-27 21:42:05   2026-05-01 18:21:59
48      LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf                          QuarterNo            4          56          0       280  2026-07-27 21:42:05   2026-05-01 18:21:59
49      LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf                          Trimestre            4         203          0       280  2026-07-27 21:42:05   2026-05-01 18:21:59
50      LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf                                Dia           31         164          0      1368  2026-07-27 21:42:05   2026-05-01 18:21:59
51      LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b                               Date         1826       14648          0      3072  2026-07-27 21:46:59   2026-07-27 21:46:58
52      LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b                                Ano            5          60          0       152  2026-07-27 21:46:59   2026-07-27 21:46:58
53      LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b                            MonthNo           12          88          0      1064  2026-07-27 21:46:59   2026-07-27 21:46:58
54      LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b                                Mês           12         397          0      1064  2026-07-27 21:46:59   2026-07-27 21:46:58
55      LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b                          QuarterNo            4          56          0       280  2026-07-27 21:46:59   2026-07-27 21:46:58
56      LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b                          Trimestre            4         203          0       280  2026-07-27 21:46:59   2026-07-27 21:46:58
57      LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b                                Dia           31         164          0      1368  2026-07-27 21:46:59   2026-07-27 21:46:58
58      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                               Date         1096        8808          0      1904  2026-07-27 21:42:05   2025-01-08 11:39:16
59      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                                Ano            3          52          0       152  2026-07-27 21:42:05   2025-01-08 11:39:16
60      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                            MonthNo           12          88          0       696  2026-07-27 21:42:05   2025-01-08 11:39:16
61      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                                Mês           12         397          0       696  2026-07-27 21:42:05   2025-01-08 11:39:16
62      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                          QuarterNo            4          56          0       152  2026-07-27 21:42:05   2025-01-08 11:39:16
63      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                          Trimestre            4         203          0       152  2026-07-27 21:42:05   2025-01-08 11:39:16
64      LocalDateTable_f7150c8f-ae21-48e2-b4e4-ff5e4d2e7b04                                Dia           31         164          0       880  2026-07-27 21:42:05   2025-01-08 11:39:16
65                                         Parâmetro - Data                   Parâmetro - Data            2         163          0       152  2026-07-29 19:32:10   2026-07-29 19:32:10
66                                         Parâmetro - Data            Parâmetro - Data Campos            2         229          0       152  2026-07-29 19:38:57   2026-07-29 19:32:10
67                                         Parâmetro - Data            Parâmetro - Data Pedido            2           0       1133       152  2026-07-29 19:32:10   2026-07-29 19:32:08
68                                                   Tabela                          TipoVenda            2         163          0       152  2024-11-05 22:57:09   2024-11-05 22:57:09
69                                                dCalendar                               Data          757        6096          0      1160  2024-10-22 15:30:53   2025-01-08 11:39:16
70                                                dCalendar                                Ano            3          52          0       152  2024-10-22 15:31:44   2024-10-22 15:30:53
71                                                dCalendar                                Mês           12          88          0       528  2024-10-22 15:31:44   2024-10-22 15:30:53
72                                                dCalendar                        Nome do Mês           12         397          0       528  2024-10-23 12:22:55   2024-10-23 12:22:55
73                                                dCalendar              Classificador Mês-Ano           25         140          0       656  2026-07-27 21:42:05   2024-10-22 17:21:40
74                                                dCalendar                             mesano           25         673          0       656  2026-07-14 01:00:35   2026-07-14 01:00:35
75                                                dCalendar                           anosafra           25         823          0       656  2026-07-12 16:07:18   2026-07-12 16:07:18
76                                                dCalendar                         OrdemSafra           12          88          0       528  2026-07-12 16:07:18   2026-07-12 16:07:18
77                                                dCalendar                              safra            3         231          0       152  2026-07-12 16:07:18   2026-07-12 16:07:18
78                                                dCalendar                      OrdemAnoSafra           25         140          0       656  2026-07-12 16:07:18   2026-07-12 16:07:18
79                                              fMetasAbate                    pesomorto_total          323        2624          0       648  2026-07-29 01:53:53   2025-01-31 18:36:38
80                                              fMetasAbate                         idcustomer            6         615          0       232  2026-05-01 18:21:59   2026-05-01 18:21:59
81                                              fMetasAbate                           customer            6         557          0       232  2026-05-01 18:21:59   2026-05-01 18:21:59
82                                              fMetasAbate                             idfarm           14        1271          0       368  2026-05-01 18:21:59   2026-05-01 18:21:59
83                                              fMetasAbate                           farmname           14         667          0       368  2026-05-01 18:21:59   2026-05-01 18:21:59
84                                              fMetasAbate                           idretiro           14        1271          0       368  2026-05-01 18:21:59   2026-05-01 18:21:59
85                                              fMetasAbate                         retironame            8         337          0       312  2026-05-01 18:21:59   2026-05-01 18:21:59
86                                              fMetasAbate                            idowner           10         943          0       304  2026-05-01 18:21:59   2026-05-01 18:21:59
87                                              fMetasAbate                          ownername           10         777          0       304  2026-05-01 18:21:59   2026-05-01 18:21:59
88                                              fMetasAbate                       idplherdtype           13        1189          0       368  2026-05-01 18:21:59   2026-05-01 18:21:59
89                                              fMetasAbate                     plherdtypename            9         409          0       368  2026-05-01 18:21:59   2026-05-01 18:21:59
90                                              fMetasAbate                         idcurrency            1         135          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
91                                              fMetasAbate                       currencyname            1         141          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
92                                              fMetasAbate                              month           12         273          0       368  2026-05-01 18:21:59   2026-05-01 18:21:59
93                                              fMetasAbate                               date           43         384          0       496  2026-07-05 15:53:58   2026-07-05 16:07:16
94                                              fMetasAbate                            harvest            7         263          0       312  2026-05-01 18:21:59   2026-05-01 18:21:59
95                                              fMetasAbate                           anosafra            7         263          0       312  2026-05-01 18:21:59   2026-05-01 18:21:59
96                                              fMetasAbate                         idcategory           12         277          0       312  2026-05-01 18:21:59   2026-05-01 18:21:59
97                                              fMetasAbate                       categoryname           12         797          0       312  2026-05-01 18:21:59   2026-05-01 18:21:59
98                                              fMetasAbate                      idanimalgroup            5         183          0       232  2026-05-01 18:21:59   2026-05-01 18:21:59
99                                              fMetasAbate                    animalgroupname            5         309          0       232  2026-05-01 18:21:59   2026-05-01 18:21:59
100                                             fMetasAbate                                age            4         203          0       232  2026-05-01 18:21:59   2026-05-01 18:21:59
101                                             fMetasAbate                             gender            2         163          0       168  2026-05-01 18:21:59   2026-05-01 18:21:59
102                                             fMetasAbate                             amount          224           0       4237       848  2026-05-01 18:21:59   2026-05-01 18:21:59
103                                             fMetasAbate                             weight           50           0       1133       728  2026-05-01 18:21:59   2026-05-01 18:21:59
104                                             fMetasAbate                        arrobavalue           65           0       1165      1016  2026-05-01 18:21:59   2026-05-01 18:21:59
105                                             fMetasAbate                       arrobaweight           65           0       1141       648  2026-05-01 18:21:59   2026-05-01 18:21:59
106                                             fMetasAbate                              value          114           0       2173      1312  2026-05-01 18:21:59   2026-05-01 18:21:59
107                                             fMetasAbate                         totalvalue          325           0       8317      1888  2026-05-01 18:21:59   2026-05-01 18:21:59
108                                             fMetasAbate                          idpropfaz           14        2279          0       368  2026-06-14 23:13:07   2026-06-14 23:13:07
109                                             fMetasAbate                              yield           18         184          0       232  2026-07-24 20:57:46   2026-07-24 20:57:46
110                                             fMetasAbate                               tipo            1         143          0       152  2026-07-24 20:57:46   2026-07-24 20:57:46
111                                             fMetasAbate                     pesovivo_total          313           0       8301      1312  2026-07-29 01:53:36   2026-07-29 01:48:48
112                                             fMetasAbate                         Total de @          317        2576          0       648  2026-07-29 02:21:53   2026-07-29 02:21:20
113                                           fMetasCompras                         idcustomer            5         533          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
114                                           fMetasCompras                           customer            5         445          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
115                                           fMetasCompras                             idfarm            9         861          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
116                                           fMetasCompras                           farmname            9         479          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
117                                           fMetasCompras                           idretiro            9         861          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
118                                           fMetasCompras                         retironame            6         281          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
119                                           fMetasCompras                            idowner            6         615          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
120                                           fMetasCompras                          ownername            6         485          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
121                                           fMetasCompras                       idplherdtype            9         861          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
122                                           fMetasCompras                     plherdtypename            6         329          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
123                                           fMetasCompras                         idcurrency            1         135          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
124                                           fMetasCompras                       currencyname            1         141          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
125                                           fMetasCompras                              month           12         273          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
126                                           fMetasCompras                               date           25         240          0       232  2026-05-01 18:21:59   2026-07-08 00:04:00
127                                           fMetasCompras                            harvest            4         203          0       176  2026-05-01 18:21:59   2026-05-01 18:21:59
128                                           fMetasCompras                           anosafra            4         203          0       176  2026-05-01 18:21:59   2026-05-01 18:21:59
129                                           fMetasCompras                         idcategory           13         291          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
130                                           fMetasCompras                       categoryname           13         847          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
131                                           fMetasCompras                      idanimalgroup            7         207          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
132                                           fMetasCompras                    animalgroupname            7         393          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
133                                           fMetasCompras                                age            5         223          0       192  2026-05-01 18:21:59   2026-05-01 18:21:59
134                                           fMetasCompras                             gender            2         163          0       160  2026-05-01 18:21:59   2026-05-01 18:21:59
135                                           fMetasCompras                             amount           39           0       1133       344  2026-05-01 18:21:59   2026-05-01 18:21:59
136                                           fMetasCompras                             weight           19           0       1133       312  2026-05-01 18:21:59   2026-05-01 18:21:59
137                                           fMetasCompras                        arrobavalue           35           0       1133       480  2026-05-01 18:21:59   2026-05-01 18:21:59
138                                           fMetasCompras                       arrobaweight           19           0       1133       272  2026-05-01 18:21:59   2026-05-01 18:21:59
139                                           fMetasCompras                              value           40           0       1133       640  2026-05-01 18:21:59   2026-05-01 18:21:59
140                                           fMetasCompras                         totalvalue           72           0       1165       640  2026-05-01 18:21:59   2026-05-01 18:21:59
141                                           fMetasCompras                          idpropfaz            9        1509          0       208  2026-06-14 23:13:07   2026-06-14 23:13:07
142                                               fMetasDre                         Desembolso         1858           0      33237     39520  2026-10-14 14:57:43   2025-01-31 17:44:33
143                                               fMetasDre                                F/V            4         269          0       176  2026-10-14 14:57:43   2025-01-31 17:45:50
144                                               fMetasDre                            Custeio         1846           0      33333     38136  2026-10-14 14:57:43   2025-01-31 17:46:19
145                                               fMetasDre                         idcustomer            3         369          0       304  2026-05-01 18:21:59   2026-05-01 18:21:59
146                                               fMetasDre                           customer            3         317          0       304  2026-05-01 18:21:59   2026-05-01 18:21:59
147                                               fMetasDre                      valorprevisto         1899           0      33373     39520  2026-05-01 18:21:59   2026-05-01 18:21:59
148                                               fMetasDre                     valorrealizado            1          48          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
149                                               fMetasDre                         costcenter           20        1179          0       480  2026-05-01 18:21:59   2026-05-01 18:21:59
150                                               fMetasDre                     uuidcostcenter           36        3147          0       544  2026-05-01 18:21:59   2026-05-01 18:21:59
151                                               fMetasDre                          classname            6         451          0       184  2026-05-01 18:21:59   2026-05-01 18:21:59
152                                               fMetasDre                          uuidclass           13        1189          0       376  2026-05-01 18:21:59   2026-05-01 18:21:59
153                                               fMetasDre                          subcenter           79        4997          0      2688  2026-05-01 18:21:59   2026-05-01 18:21:59
154                                               fMetasDre                      uuidsubcenter          132       10947          0      2920  2026-05-01 18:21:59   2026-05-01 18:21:59
155                                               fMetasDre                            product            1           0          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
156                                               fMetasDre                        uuidproduct            1           0          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
157                                               fMetasDre                           farmname           17         755          0      6904  2026-05-01 18:21:59   2026-05-01 18:21:59
158                                               fMetasDre                             idfarm           17        1517          0      6904  2026-05-01 18:21:59   2026-05-01 18:21:59
159                                               fMetasDre                           activity            1           0          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
160                                               fMetasDre                       uuidactivity            1           0          0       152  2026-05-01 18:21:59   2026-05-01 18:21:59
161                                               fMetasDre                               date           48         424          0      8760  2026-07-05 15:36:23   2026-07-05 15:53:53
162                                               fMetasDre                               type            2         173          0       160  2026-05-01 18:21:59   2026-05-01 18:21:59
163                                               fMetasDre         classificationanalyticuuid            5         533          0       184  2026-05-01 18:21:59   2026-05-01 18:21:59
164                                               fMetasDre  classificationanalyticdescription            5         351          0       184  2026-05-01 18:21:59   2026-05-01 18:21:59
165                                               fMetasDre                          idpropfaz           17        2741          0      6904  2026-06-14 23:13:07   2026-06-14 23:13:07
166                                               fMetasDre                        custeio_cat            5         247          0       184  2026-07-05 18:14:58   2026-07-05 18:14:58
167                                               fMetasDre                   tipo_custeio_cat            6         259          0       184  2026-07-05 18:14:58   2026-07-05 18:14:58
168                                               fMetasDre                     desembolso_cat            4         231          0       176  2026-07-05 18:14:58   2026-07-05 18:14:58
169                                              fMetasEmPe                          idpropfaz            7        1201          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
170                                              fMetasEmPe                         idcustomer            3         369          0       152  2026-07-24 20:57:46   2026-07-24 20:57:46
171                                              fMetasEmPe                           customer            3         339          0       152  2026-07-24 20:57:46   2026-07-24 20:57:46
172                                              fMetasEmPe                             idfarm            7         697          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
173                                              fMetasEmPe                           farmname            7         379          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
174                                              fMetasEmPe                           idretiro            7         697          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
175                                              fMetasEmPe                         retironame            3         217          0       168  2026-07-24 20:57:46   2026-07-24 20:57:46
176                                              fMetasEmPe                            idowner            6         615          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
177                                              fMetasEmPe                          ownername            6         519          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
178                                              fMetasEmPe                       idplherdtype            6         615          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
179                                              fMetasEmPe                     plherdtypename            5         277          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
180                                              fMetasEmPe                         idcurrency            1         135          0       152  2026-07-24 20:57:46   2026-07-24 20:57:46
181                                              fMetasEmPe                       currencyname            1         141          0       152  2026-07-24 20:57:46   2026-07-24 20:57:46
182                                              fMetasEmPe                              month           12         273          0       192  2026-07-24 20:57:46   2026-07-24 20:57:46
183                                              fMetasEmPe                               date           27         256          0       208  2026-07-24 20:57:46   2026-07-29 02:30:46
184                                              fMetasEmPe                            harvest            6         243          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
185                                              fMetasEmPe                           anosafra            6         243          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
186                                              fMetasEmPe                         idcategory            7         213          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
187                                              fMetasEmPe                       categoryname            7         483          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
188                                              fMetasEmPe                      idanimalgroup            5         183          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
189                                              fMetasEmPe                    animalgroupname            5         309          0       184  2026-07-24 20:57:46   2026-07-24 20:57:46
190                                              fMetasEmPe                                age            3         183          0       168  2026-07-24 20:57:46   2026-07-24 20:57:46
191                                              fMetasEmPe                             gender            2         163          0       160  2026-07-24 20:57:46   2026-07-24 20:57:46
192                                              fMetasEmPe                             amount           56           0       1149       296  2026-07-24 20:57:46   2026-07-24 20:57:46
193                                              fMetasEmPe                             weight           17           0       1133       272  2026-07-24 20:57:46   2026-07-24 20:57:46
194                                              fMetasEmPe                        arrobavalue           18           0       1133       328  2026-07-24 20:57:46   2026-07-24 20:57:46
195                                              fMetasEmPe                       arrobaweight           17           0       1133       240  2026-07-24 20:57:46   2026-07-24 20:57:46
196                                              fMetasEmPe                              value           30           0       1133       392  2026-07-24 20:57:46   2026-07-24 20:57:46
197                                              fMetasEmPe                         totalvalue           71           0       1173       512  2026-07-24 20:57:46   2026-07-24 20:57:46
198                                              fMetasEmPe                              yield            1           0          0       152  2026-07-24 20:57:46   2026-07-24 20:57:46
199                                              fMetasEmPe                               tipo            1         143          0       152  2026-07-24 20:57:46   2026-07-24 20:57:46
..                                                      ...                                ...          ...         ...        ...       ...                  ...                   ...
277                                    fPlanejadoxRealizado                               meta         1429       11472          0     58528  2026-07-28 03:36:59   2026-07-28 03:36:59
278                                    fPlanejadoxRealizado                          realizado        12679      101472          0    186864  2026-07-28 03:36:59   2026-07-28 03:36:59
279                                    fPlanejadoxRealizado                     Classificacao2            5         289          0      9152  2026-10-14 14:57:43   2026-07-28 03:51:25
280                                              fSaldoGado                           farmname           47        2043          0      7832  2025-04-13 14:18:57   2025-04-13 14:18:57
281                                              fSaldoGado                         retironame           53        2075          0      5592  2025-04-13 14:18:57   2025-04-13 14:18:57
282                                              fSaldoGado                              owner           76        4635          0      4176  2025-04-13 14:18:57   2025-04-13 14:18:57
283                                              fSaldoGado                           category          143        6899          0     19360  2025-04-13 14:18:57   2025-04-13 14:18:57
284                                              fSaldoGado             UltimaDataMovimentacao          207        1696          0     19472  2026-07-27 21:42:05   2025-04-14 22:41:38
285                                              fSaldoGado                               date           55         480          0     40112  2025-04-16 16:04:20   2026-07-27 21:46:58
286                                              fSaldoGado                         data_saldo         1292       10376          0     65648  2025-04-16 16:04:20   2026-07-27 21:46:58
287                                              fSaldoGado                          amountacc         1738       13944          0     30240  2025-04-19 16:32:57   2025-04-19 16:32:57
288                                              fSaldoGado                              birth           55        1223          0     23648  2025-04-23 02:10:15   2025-04-23 02:10:15
289                                              fSaldoGado                            harvest            6         243          0      6912  2025-04-23 02:10:15   2025-04-23 02:10:15
290                                              fSaldoGado                          idpropfaz           49        7669          0      7832  2026-06-14 23:13:07   2026-06-14 23:13:07
291                                               fUnidades                         idcustomer           10         943          0       184  2026-05-01 18:21:59   2026-05-01 18:21:59
292                                               fUnidades                           customer           10         747          0       184  2026-05-01 18:21:59   2026-05-01 18:21:59
293                                               fUnidades                             idfarm           70        5863          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
294                                               fUnidades                           farmname           68        3525          0       208  2026-05-01 18:21:59   2026-05-01 18:21:59
295                                               fUnidades                          idpropfaz           70       10903          0       208  2026-06-14 23:13:07   2026-06-14 23:13:07
296                                           financeiroDre                     Type Operation            1           0          0       152  2025-01-22 16:30:53   2024-11-01 03:44:42
297                                           financeiroDre                         Desembolso        59392      475176          0    278240  2026-10-14 14:57:43   2024-11-05 23:01:09
298                                           financeiroDre                            Custeio        58587      468736          0    273504  2026-10-14 14:57:43   2024-11-05 23:45:00
299                                           financeiroDre                    Class subcenter            3         277          0      4824  2026-10-14 14:57:43   2024-11-09 00:39:13
300                                           financeiroDre                                F/V            5         315          0      5080  2026-10-14 14:57:43   2025-01-20 14:09:03
301                                           financeiroDre                         idcustomer            9         861          0     25288  2026-05-01 18:21:59   2026-05-01 18:21:59
302                                           financeiroDre                           customer            9         705          0     25288  2026-05-01 18:21:59   2026-05-01 18:21:59
303                                           financeiroDre                         farmfiscal           52        2579          0     56256  2026-05-01 18:21:59   2026-05-01 18:21:59
304                                           financeiroDre                  idfarmdestination           69        5781          0     85264  2026-05-01 18:21:59   2026-05-01 18:21:59
305                                           financeiroDre                    farmdestination           68        3665          0     85264  2026-05-01 18:21:59   2026-05-01 18:21:59
306                                           financeiroDre                              owner           48        3477          0     42776  2026-05-01 18:21:59   2026-05-01 18:21:59
307                                           financeiroDre                  idfinancialentrie       109589     2898209          0    461464  2026-05-01 18:21:59   2026-05-01 18:21:59
308                                           financeiroDre                          idpayment       158157     4182771          0    524240  2026-05-01 18:21:59   2026-05-01 18:21:59
309                                           financeiroDre                           anosafra           24         603          0     59200  2026-05-01 18:21:59   2026-05-01 18:21:59
310                                           financeiroDre                         costcenter           47        2487          0     18600  2026-05-01 18:21:59   2026-05-01 18:21:59
311                                           financeiroDre                        description        19911     1002861          0    111208  2026-05-01 18:21:59   2026-05-01 18:21:59
312                                           financeiroDre                               code        24641      243880          0    346616  2026-05-01 18:21:59   2026-05-01 18:21:59
313                                           financeiroDre                             classe           14         789          0     10120  2026-05-01 18:21:59   2026-05-01 18:21:59
314                                           financeiroDre                          subcenter          147        8803          0     42168  2026-05-01 18:21:59   2026-05-01 18:21:59
315                                           financeiroDre                           activity           12         643          0      2064  2026-05-01 18:21:59   2026-05-01 18:21:59
316                                           financeiroDre                            doctype            6         293          0     22568  2026-05-01 18:21:59   2026-05-01 18:21:59
317                                           financeiroDre                   conciliationdate         1263       14928          0    219672  2026-05-01 18:21:59   2026-05-01 18:21:59
318                                           financeiroDre                        datepayment         1841       14768          0    250120  2026-08-02 14:36:37   2026-05-01 18:21:59
319                                           financeiroDre                            duedate         5960       47720          0    389016  2026-05-01 18:21:59   2026-07-12 18:18:38
320                                           financeiroDre                               type            2         173          0      1712  2026-05-01 18:21:59   2026-05-01 18:21:59
321                                           financeiroDre                      amountpayable        66712      533736          0    461608  2026-05-01 18:21:59   2026-05-01 18:21:59
322                                           financeiroDre                         amountpaid        66760      534120          0    419024  2026-05-01 18:21:59   2026-05-01 18:21:59
323                                           financeiroDre                           currency            2         163          0       280  2026-05-01 18:21:59   2026-05-01 18:21:59
324                                           financeiroDre                             status            2         169          0     11232  2026-05-01 18:21:59   2026-05-01 18:21:59
325                                           financeiroDre                       emissiondate         2433       28588          0    272568  2026-05-01 18:21:59   2026-05-01 18:21:59
326                                           financeiroDre                             parcel         5009       52482          0    157136  2026-05-01 18:21:59   2026-05-01 18:21:59
327                                           financeiroDre                          idpropfaz           53        8285          0     56256  2026-06-01 10:41:47   2026-06-01 10:41:47
328                                           financeiroDre                        custeio_cat            7         323          0      4528  2026-07-05 18:14:58   2026-07-05 18:14:58
329                                           financeiroDre                   tipo_custeio_cat            8         335          0      5120  2026-07-05 18:14:58   2026-07-05 18:14:58
330                                           financeiroDre                     desembolso_cat            7         323          0      4344  2026-07-05 18:14:58   2026-07-05 18:14:58
331                                         pecuarioCompras                               Paid         1611       12928          0      3824  2026-10-14 14:57:43   2024-10-22 16:21:53
332                                         pecuarioCompras                               DATA          708        5704          0      3208  2025-03-05 01:55:11   2025-01-24 17:57:18
333                                         pecuarioCompras                      categ_fazenda           81        4009          0      1264  2025-01-17 01:11:50   2025-01-17 01:11:50
334                                         pecuarioCompras                                qtd          261           0       4317      3824  2025-01-17 01:11:50   2025-01-17 01:11:50
335                                         pecuarioCompras                         total_peso          364           0       8445      3208  2025-01-17 01:11:50   2025-01-17 01:11:50
336                                         pecuarioCompras                          valor_cab         1581       12688          0      3824  2025-01-17 01:11:50   2025-01-17 01:11:50
337                                         pecuarioCompras                        VALOR TOTAL         1968           0      33437      9336  2025-01-17 01:11:50   2025-01-17 01:11:50
338                                         pecuarioCompras                            valo_kg         1894       15192          0      3824  2025-01-17 01:11:50   2025-01-17 01:11:50
339                                         pecuarioCompras                       valor_arroba          384           0       8421      4744  2025-01-17 01:11:50   2025-01-17 01:11:50
340                                         pecuarioCompras                       categoria_bi           81        4009          0      1264  2025-01-17 01:11:50   2025-01-17 01:11:50
341                                         pecuarioCompras                               sexo            2         165          0       256  2025-01-17 01:11:50   2025-01-17 01:11:50
342                                         pecuarioCompras                        peso_arroba          364        2952          0      2776  2025-01-17 01:11:50   2025-01-17 01:11:50
343                                         pecuarioCompras                            fazenda           44        1929          0       928  2025-01-17 01:11:50   2025-01-17 01:11:50
344                                         pecuarioCompras                         categoryid           90        7503          0      1264  2025-03-05 01:55:11   2025-03-05 01:55:11
345                                         pecuarioCompras                         idcustomer           10         943          0       232  2025-03-05 01:55:11   2025-03-05 01:55:11
346                                         pecuarioCompras                           customer           10         759          0       232  2025-03-05 01:55:11   2025-03-05 01:55:11
347                                         pecuarioCompras                           farmname           44        1929          0       928  2025-03-05 01:55:11   2025-03-05 01:55:11
348                                         pecuarioCompras                           idretiro           56        4715          0       952  2025-03-05 01:55:11   2025-03-05 01:55:11
349                                         pecuarioCompras                         retironame           41        1597          0       824  2025-03-05 01:55:11   2025-03-05 01:55:11
350                                         pecuarioCompras                           anosafra            6         243          0       784  2025-03-05 01:55:11   2025-03-05 01:55:11
351                                         pecuarioCompras                           provider          823       23837          0      3208  2025-03-05 01:55:11   2025-03-05 01:55:11
352                                         pecuarioCompras                       averagevalue         1114           0      16853      4744  2025-03-05 01:55:11   2025-03-05 01:55:11
353                                         pecuarioCompras                        valueweight           38         344          0      1912  2025-03-05 01:55:11   2025-03-05 01:55:11
354                                         pecuarioCompras                         Total de @         1874       15032          0      3824  2026-10-14 14:57:43   2026-05-31 00:20:41
355                                         pecuarioCompras                          idpropfaz           45        7053          0       928  2026-06-01 10:41:47   2026-06-01 10:41:47
356                                         pecuarioCompras                       proprietArio           34        2301          0       416  2026-10-14 14:57:22   2026-10-14 14:57:22
357                                         pecuarioDesmame                               DATA          350        2840          0      2336  2026-05-01 18:21:58   2024-10-22 15:31:44
358                                         pecuarioDesmame                            harvest            6         243          0       880  2024-10-21 20:14:53   2024-10-21 20:14:53
359                                         pecuarioDesmame                             amount          213           0       4229      2544  2026-05-01 18:21:57   2024-10-21 20:14:53
360                                         pecuarioDesmame                             weight          161           0       4205      2336  2026-05-01 18:21:57   2024-10-21 20:14:53
361                                         pecuarioDesmame                             gender            2         163          0       248  2024-10-21 20:14:53   2024-10-21 20:14:53
362                                         pecuarioDesmame                         idcustomer            9         861          0       392  2026-05-01 18:21:59   2026-05-01 18:21:59
363                                         pecuarioDesmame                           customer            9         693          0       392  2026-05-01 18:21:59   2026-05-01 18:21:59
364                                         pecuarioDesmame                             idfarm           31        2665          0      1152  2026-05-01 18:21:59   2026-05-01 18:21:59
365                                         pecuarioDesmame                           farmname           31        1289          0      1152  2026-05-01 18:21:59   2026-05-01 18:21:59
366                                         pecuarioDesmame                           idretiro           39        3321          0      1352  2026-05-01 18:21:59   2026-05-01 18:21:59
367                                         pecuarioDesmame                         retironame           24         821          0       528  2026-05-01 18:21:59   2026-05-01 18:21:59
368                                         pecuarioDesmame                              owner           13         961          0       440  2026-05-01 18:21:59   2026-05-01 18:21:59
369                                         pecuarioDesmame                           anosafra            5         223          0       880  2026-05-01 18:21:59   2026-05-01 18:21:59
370                                         pecuarioDesmame                        oldcategory           21        1007          0       664  2026-05-01 18:21:59   2026-05-01 18:21:59
371                                         pecuarioDesmame                      oldcategoryid           21        1845          0       664  2026-05-01 18:21:59   2026-05-01 18:21:59
372                                         pecuarioDesmame                          birthdate           51        1143          0      1680  2026-05-01 18:21:59   2026-05-01 18:21:59
373                                         pecuarioDesmame                        newcategory           21        1157          0       672  2026-05-01 18:21:59   2026-05-01 18:21:59
374                                         pecuarioDesmame                      newcategoryid           23        2009          0       672  2026-05-01 18:21:59   2026-05-01 18:21:59
375                                         pecuarioDesmame                        valueweight           17         176          0      1128  2026-05-01 18:21:59   2026-05-01 18:21:59
376                                         pecuarioDesmame                          idpropfaz           31        4897          0      1152  2026-06-01 10:41:47   2026-06-01 10:41:47
377                                          pecuarioMortes                                era            5         223          0      2184  2024-10-21 20:14:53   2024-10-21 20:14:53
378                                          pecuarioMortes                              safra            6         243          0      2832  2024-10-21 20:14:53   2024-10-21 20:14:53
379                                          pecuarioMortes                           forecast           47         228          0       424  2026-10-14 14:57:43   2024-10-31 19:28:34
380                                          pecuarioMortes                               DATA         1452       11656          0     11920  2025-01-18 12:29:46   2025-01-18 12:29:56
381                                          pecuarioMortes                      categ_fazenda          126        6125          0      5312  2025-01-18 11:41:32   2025-01-18 11:41:32
382                                          pecuarioMortes                        carimbo_bez            1           0          0       152  2025-01-18 11:41:32   2025-01-18 11:41:32
383                                          pecuarioMortes                                qtd           47         416          0       424  2025-01-18 11:41:32   2025-01-18 11:41:32
384                                          pecuarioMortes                              causa          166        6773          0      4896  2025-01-18 11:41:32   2025-01-18 11:41:32
385                                          pecuarioMortes                          peso_vivo         1294           0      32877     17352  2025-01-18 11:41:32   2025-01-18 11:41:32
386                                          pecuarioMortes                    grupo_categoria            8         419          0      2088  2025-01-18 11:41:32   2025-01-18 11:41:32
387                                          pecuarioMortes                       categoria_bi          126        6125          0      5312  2025-01-18 11:41:32   2025-01-18 11:41:32
388                                          pecuarioMortes                         peso_total         1294           0      32877     17352  2025-01-18 11:41:32   2025-01-18 11:41:32
389                                          pecuarioMortes                               sexo            2         163          0       816  2025-01-18 11:41:32   2025-01-18 11:41:32
390                                          pecuarioMortes                            fazenda           44        1915          0      4336  2025-01-18 11:41:32   2025-01-18 11:41:32
391                                          pecuarioMortes                         categoryid          144       11931          0      5960  2025-03-05 02:28:08   2025-03-05 02:28:08
392                                          pecuarioMortes                              pasto          395       12257          0      2680  2025-03-05 02:28:08   2025-03-05 02:28:08
393                                          pecuarioMortes                          enumgroup            8         409          0      2088  2025-03-05 02:28:08   2025-03-05 02:28:08
394                                          pecuarioMortes                             idfarm           44        3731          0      4336  2025-03-05 02:28:08   2025-03-05 02:28:08
395                                          pecuarioMortes                         idcustomer           10         943          0      1008  2025-03-05 02:28:08   2025-03-05 02:28:08
396                                          pecuarioMortes                           customer           10         759          0      1008  2025-03-05 02:28:08   2025-03-05 02:28:08
397                                          pecuarioMortes                           idretiro           58        1079          0      4360  2025-03-05 02:28:08   2025-03-05 02:28:08
398                                          pecuarioMortes                         retironame           42        1653          0      1944  2025-03-05 02:28:08   2025-03-05 02:28:08
399                                          pecuarioMortes                          idpropfaz           44        6899          0      4336  2026-06-01 10:41:47   2026-06-01 10:41:47
400                                          pecuarioMortes                       proprietArio           51        3151          0      1504  2026-10-14 14:57:22   2026-10-14 14:57:22
401                                      pecuarioNascimento                         idcustomer            9         861          0       312  2026-05-01 18:21:59   2026-05-01 18:21:59
402                                      pecuarioNascimento                           customer            9         693          0       312  2026-05-01 18:21:59   2026-05-01 18:21:59
403                                      pecuarioNascimento                             idfarm           31        2665          0       928  2026-05-01 18:21:59   2026-05-01 18:21:59
404                                      pecuarioNascimento                           farmname           31        1287          0       928  2026-05-01 18:21:59   2026-05-01 18:21:59
405                                      pecuarioNascimento                           idretiro           38        3239          0      1088  2026-05-01 18:21:59   2026-05-01 18:21:59
406                                      pecuarioNascimento                         retironame           23         797          0       456  2026-05-01 18:21:59   2026-05-01 18:21:59
407                                      pecuarioNascimento                              owner           13         961          0       320  2026-05-01 18:21:59   2026-05-01 18:21:59
408                                      pecuarioNascimento                           anosafra            5         223          0       752  2026-05-01 18:21:59   2026-05-01 18:21:59
409                                      pecuarioNascimento                         idcategory           21        1845          0       640  2026-05-01 18:21:59   2026-05-01 18:21:59
410                                      pecuarioNascimento                           category           21        1007          0       640  2026-05-01 18:21:59   2026-05-01 18:21:59
411                                      pecuarioNascimento                            harvest            5         223          0       752  2026-05-01 18:21:59   2026-05-01 18:21:59
412                                      pecuarioNascimento                             amount          242           0       4285      2248  2026-05-01 18:21:59   2026-05-01 18:21:59
413                                      pecuarioNascimento                             gender            2         163          0       232  2026-05-01 18:21:59   2026-05-01 18:21:59
414                                      pecuarioNascimento                               DATA          513        4144          0      2640  2026-05-01 18:21:59   2026-05-01 18:21:59
415                                      pecuarioNascimento                          idpropfaz           31        4897          0       928  2026-06-01 10:41:47   2026-06-01 10:41:47
416                              pecuarioRebanhoMedioMensal                               farm            1         163          0       152  2026-07-27 21:42:05   2024-10-31 16:34:05
417                              pecuarioRebanhoMedioMensal                           Forecast            1           0          0       152  2026-05-01 18:21:59   2024-10-31 19:25:15
418                              pecuarioRebanhoMedioMensal                         idcustomer           10         943          0       616  2026-05-01 18:21:59   2026-05-01 18:21:59
419                              pecuarioRebanhoMedioMensal                           customer           10         747          0       616  2026-05-01 18:21:59   2026-05-01 18:21:59
420                              pecuarioRebanhoMedioMensal                             idfarm           49        4141          0      4320  2026-05-01 18:21:59   2026-05-01 18:21:59
421                              pecuarioRebanhoMedioMensal                           farmname           47        2043          0      4320  2026-05-01 18:21:59   2026-05-01 18:21:59
422                              pecuarioRebanhoMedioMensal                           idretiro           73        6109          0      5384  2026-05-01 18:21:59   2026-05-01 18:21:59
423                              pecuarioRebanhoMedioMensal                         retironame           53        2075          0      3824  2026-05-01 18:21:59   2026-05-01 18:21:59
424                              pecuarioRebanhoMedioMensal                              owner           76        4635          0      4544  2026-05-01 18:21:59   2026-05-01 18:21:59
425                              pecuarioRebanhoMedioMensal                           anosafra            7         263          0     23000  2026-05-01 18:21:59   2026-05-01 18:21:59
426                              pecuarioRebanhoMedioMensal                             amount         3330       26680          0     51984  2026-05-01 18:21:59   2026-05-01 18:21:59
427                              pecuarioRebanhoMedioMensal                             gender            2         163          0      5976  2026-05-01 18:21:59   2026-05-01 18:21:59
428                              pecuarioRebanhoMedioMensal                         idcategory          167       13817          0     33416  2026-05-01 18:21:59   2026-05-01 18:21:59
429                              pecuarioRebanhoMedioMensal                           category          143        6899          0     33416  2026-05-01 18:21:59   2026-05-01 18:21:59
430                              pecuarioRebanhoMedioMensal                               DATA           66         568          0     98696  2026-05-01 18:21:59   2026-05-30 23:49:10
431                              pecuarioRebanhoMedioMensal                          idpropfaz           49        7669          0      4320  2026-06-01 10:41:47   2026-06-01 10:41:47
432                                      pecuarioVendaAbate                        Total Value            1           0          0       152  2025-01-22 16:30:53   2024-10-22 21:25:20
433                                      pecuarioVendaAbate                              teste            1           0          0       152  2025-01-22 16:30:53   2024-10-31 23:05:14
434                                      pecuarioVendaAbate                   Peso Morto Total         2397           0      65701      7736  2026-10-14 14:57:43   2024-11-02 13:11:58
435                                      pecuarioVendaAbate                         Total de @         1088           0      16669      5840  2026-10-14 14:57:43   2024-11-02 13:14:13
436                                      pecuarioVendaAbate                          tipovenda            1         143          0       152  2026-10-14 14:57:43   2024-11-05 22:55:45
437                                      pecuarioVendaAbate                            cliente          135        7549          0      2128  2025-01-18 11:50:32   2025-01-18 11:50:32
438                                      pecuarioVendaAbate                      categ_fazenda           66        3409          0      1408  2025-01-18 11:50:32   2025-01-18 11:50:32
439                                      pecuarioVendaAbate                               DATA          941        7568          0      3944  2025-01-20 19:25:02   2025-01-18 11:50:32
440                                      pecuarioVendaAbate                                qtd          303           0       8357      3400  2025-01-18 11:50:32   2025-01-18 11:50:32
441                                      pecuarioVendaAbate                          peso_vivo          387           0       8421      3944  2025-01-18 11:50:32   2025-01-18 11:50:32
442                                      pecuarioVendaAbate                        peso_arroba           31         288          0      2048  2025-01-18 11:50:32   2025-01-18 11:50:32
443                                      pecuarioVendaAbate                       valor_arroba          234           0       4237      7736  2025-01-18 11:50:32   2025-01-18 11:50:32
444                                      pecuarioVendaAbate                        faturamento         2809           0      65885     11536  2025-01-18 11:50:32   2025-01-18 11:50:32
445                                      pecuarioVendaAbate                       categoria_bi           66        3409          0      1408  2025-01-18 11:50:32   2025-01-18 11:50:32
446                                      pecuarioVendaAbate                               sexo            2         165          0       424  2025-01-18 11:50:32   2025-01-18 11:50:32
447                                      pecuarioVendaAbate                         peso_morto          275           0       4357      3944  2025-01-18 11:50:32   2025-01-18 11:50:32
448                                      pecuarioVendaAbate                     pesovivo_total         2718           0      65813      7736  2025-01-18 11:50:32   2025-01-18 11:50:32
449                                      pecuarioVendaAbate                    pesomorto_total         2397           0      65701      7736  2025-01-18 11:50:32   2025-01-18 11:50:32
450                                      pecuarioVendaAbate                           valor_kg           27         256          0      1816  2025-01-18 11:50:32   2025-01-18 11:50:32
451                                      pecuarioVendaAbate                          valor_cab         2764       22152          0      4704  2025-01-18 11:50:32   2025-01-18 11:50:32
452                                      pecuarioVendaAbate                            fazenda           30        1323          0       752  2025-01-18 11:50:32   2025-01-18 11:50:32
453                                      pecuarioVendaAbate                             retiro           24         975          0       736  2025-01-18 11:50:32   2025-01-18 11:50:32
454                                      pecuarioVendaAbate                          idpropfaz           30        4743          0       752  2026-06-01 10:41:47   2026-06-01 10:41:47
455                                      pecuarioVendaAbate                       proprietArio           10         759          0       360  2026-10-14 14:57:22   2026-10-14 14:57:22
456                                       pecuarioVendaEmPe                         Total de @          505        4080          0       776  2026-07-29 03:13:59   2024-11-02 13:28:14
457                                       pecuarioVendaEmPe                          tipovenda            1         143          0       152  2026-07-27 21:42:05   2024-11-05 22:56:03
458                                       pecuarioVendaEmPe                         Peso Total          505           0       8477      1608  2026-07-27 21:42:05   2025-01-11 12:25:22
459                                       pecuarioVendaEmPe                            cliente          232       13965          0       696  2025-01-18 11:50:32   2025-01-18 11:50:32
460                                       pecuarioVendaEmPe                               DATA          201        1648          0       696  2025-01-20 19:24:35   2025-01-18 11:50:32
461                                       pecuarioVendaEmPe                      categ_fazenda           54        2787          0       584  2025-01-18 11:50:32   2025-01-18 11:50:32
462                                       pecuarioVendaEmPe                                qtd          118           0       2173       776  2025-01-18 11:50:32   2025-01-18 11:50:32
463                                       pecuarioVendaEmPe                          peso_vivo          216           0       4237       880  2025-01-18 11:50:32   2025-01-18 11:50:32
464                                       pecuarioVendaEmPe                     pesovivo_total          505           0       8477      1608  2025-01-18 11:50:32   2025-01-18 11:50:32
465                                       pecuarioVendaEmPe                       valor_arroba          260           0       4285      1608  2025-01-18 11:50:32   2025-01-18 11:50:32
466                                       pecuarioVendaEmPe                          valor_cab          296        2408          0       776  2025-01-18 11:50:32   2025-01-18 11:50:32
467                                       pecuarioVendaEmPe                        faturamento          492           0       8453      1608  2025-01-18 11:50:32   2025-01-18 11:50:32
468                                       pecuarioVendaEmPe                       categoria_bi           54        2787          0       584  2025-01-18 11:50:32   2025-01-18 11:50:32
469                                       pecuarioVendaEmPe                               sexo            2         163          0       216  2025-01-18 11:50:32   2025-01-18 11:50:32
470                                       pecuarioVendaEmPe                           valor_kg           23         224          0       512  2025-01-18 11:50:32   2025-01-18 11:50:32
471                                       pecuarioVendaEmPe                       proprietÁrio            9         665          0       208  2025-01-18 11:50:32   2025-01-18 11:50:32
472                                       pecuarioVendaEmPe                            fazenda           27        1093          0       336  2025-01-18 11:50:32   2025-01-18 11:50:32
473                                       pecuarioVendaEmPe                             retiro           18         735          0       224  2025-01-18 11:50:32   2025-01-18 11:50:32
474                                       pecuarioVendaEmPe                         Peso Morto          505        4080          0       776  2026-07-27 21:42:05   2025-01-20 21:07:01
475                                       pecuarioVendaEmPe                        peso_arroba          216        1768          0       696  2025-03-05 01:14:37   2025-03-05 01:14:37
476                                       pecuarioVendaEmPe                          idpropfaz           27        4281          0       336  2026-06-01 10:41:47   2026-06-01 10:41:47

## Relationships

                 FromTableName FromColumnName ToTableName ToColumnName  IsActive Cardinality CrossFilteringBehavior  FromKeyCount  ToKeyCount  RelyOnReferentialIntegrity
0              pecuarioDesmame           DATA   dCalendar         Data         1         M:1                 Single           353         NaN                           0
1           pecuarioVendaAbate      tipovenda      Tabela    TipoVenda         1         M:1                 Single             4         NaN                           0
2            pecuarioVendaEmPe      tipovenda      Tabela    TipoVenda         1         M:1                 Single             4         NaN                           0
3           pecuarioVendaAbate           DATA   dCalendar         Data         1         M:1                 Single           944         NaN                           0
4            pecuarioVendaEmPe           DATA   dCalendar         Data         1         M:1                 Single           204         NaN                           0
5               pecuarioMortes           DATA   dCalendar         Data         1         M:1                 Single          1455         NaN                           0
6              pecuarioCompras           DATA   dCalendar         Data         1         M:1                 Single           711         NaN                           0
7           pecuarioNascimento         idfarm   fUnidades       idfarm         1         M:1                 Single            34         NaN                           0
8   pecuarioRebanhoMedioMensal         idfarm   fUnidades       idfarm         1         M:1                 Single            52         NaN                           0
9              pecuarioDesmame         idfarm   fUnidades       idfarm         1         M:1                 Single            34         NaN                           0
10              pecuarioMortes         idfarm   fUnidades       idfarm         1         M:1                 Single            47         NaN                           0
11               fMetasCompras         idfarm   fUnidades       idfarm         1         M:1                 Single            12         NaN                           0
12           fMetasNascimentos         idfarm   fUnidades       idfarm         1         M:1                 Single            18         NaN                           0
13                fMetasMortes         idfarm   fUnidades       idfarm         1         M:1                 Single            21         NaN                           0
14                   fMetasDre         idfarm   fUnidades       idfarm         1         M:1                 Single            20         NaN                           0
15          fMetasRebanhoMedio         idfarm   fUnidades       idfarm         1         M:1                 Single            52         NaN                           0
16          pecuarioNascimento     idcategory  Categorias   idcategory         1         M:1                 Single            24         NaN                           0
17  pecuarioRebanhoMedioMensal     idcategory  Categorias   idcategory         1         M:1                 Single           170         NaN                           0
18          fMetasRebanhoMedio     idcategory  Categorias   idcategory         1         M:1                 Single           170         NaN                           0
19  pecuarioRebanhoMedioMensal           DATA   dCalendar         Data         1         M:1                 Single            69         NaN                           0
20          fMetasRebanhoMedio           DATA   dCalendar         Data         1         M:1                 Single            69         NaN                           0
21          pecuarioVendaAbate      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            33         NaN                           0
22           pecuarioVendaEmPe      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            30         NaN                           0
23             pecuarioCompras      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            48         NaN                           0
24               financeiroDre      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            56         NaN                           0
25                     Compras      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            48         NaN                           0
26                  fSaldoGado      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            52         NaN                           0
27                   fMetasDre           date   dCalendar         Data         1         M:1                 Single            51         NaN                           0
28                fMetasMortes           date   dCalendar         Data         1         M:1                 Single            51         NaN                           0
29           fMetasNascimentos           date   dCalendar         Data         1         M:1                 Single            26         NaN                           0
30                 fMetasAbate           date   dCalendar         Data         1         M:1                 Single            46         NaN                           0
31                     Compras           date   dCalendar         Data         0         M:1                 Single           664         NaN                           0
32               fMetasCompras           date   dCalendar         Data         1         M:1                 Single            28         NaN                           0
33               financeiroDre        duedate   dCalendar         Data         1         M:1                 Single          5963         NaN                           0
34                  fSaldoGado           date   dCalendar         Data         1         M:1                   Both            58         NaN                           0
35        fPlanejadoxRealizado      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            76         NaN                           0
36        fPlanejadoxRealizado           data   dCalendar         Data         1         M:1                 Single           134         NaN                           0
37                 fMetasAbate      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            17         NaN                           0
38                  fMetasEmPe      idpropfaz   fUnidades    idpropfaz         1         M:1                 Single            10         NaN                           0
39                  fMetasEmPe           date   dCalendar         Data         1         M:1                 Single            30         NaN                           0

## RLS

(none)

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
### LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf
```dax
Calendar(Date(Year(MIN('pecuarioNascimento'[DATA])), 1, 1), Date(Year(MAX('pecuarioNascimento'[DATA])), 12, 31))
```
### LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3
```dax
Calendar(Date(Year(MIN('financeiroDre'[datepayment])), 1, 1), Date(Year(MAX('financeiroDre'[datepayment])), 12, 31))
```
### LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b
```dax
Calendar(Date(Year(MIN('fSaldoGado'[data_saldo])), 1, 1), Date(Year(MAX('fSaldoGado'[data_saldo])), 12, 31))
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
pecuarioCompras[valo_kg] * pecuarioCompras[total_peso]
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
IF(financeiroDre[desembolso_cat]="DCM",'financeiroDre'[amountpaid] *-1,0)
```
### financeiroDre[Custeio]
```dax
IF(financeiroDre[custeio_cat] = "CCM" ,'financeiroDre'[amountpaid] ,0)
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
### financeiroDre[F/V]
```dax
IF(financeiroDre[tipo_custeio_cat] IN {"Receita Pec","Receita outras","Receita Agr"}, "A - RECEITAS",
        IF(financeiroDre[tipo_custeio_cat] = "CF","B - CUSTO FIXO",
            IF(financeiroDre[tipo_custeio_cat] = "CV","C - CUSTO VARIAVEL",
                IF(financeiroDre[tipo_custeio_cat] = "Financiamentos","D - FINANCIAMENTOS","VERIFICAR"

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
IF(fMetasDre[desembolso_cat]="DCM",'fMetasDre'[valorprevisto] *-1,0)
```
### fMetasDre[F/V]
```dax
IF(fMetasDre[tipo_custeio_cat] IN {"Receita Pec","Receita outras","Receita Agr"}, "A - RECEITAS",
        IF(fMetasDre[tipo_custeio_cat] = "CF","B - CUSTO FIXO",
            IF(fMetasDre[tipo_custeio_cat] = "CV","C - CUSTO VARIAVEL",
                IF(fMetasDre[tipo_custeio_cat] = "Financiamentos","D - FINANCIAMENTOS","VERIFICAR"

                )
            )
        )
    )
```
### fMetasDre[Custeio]
```dax
IF(fMetasDre[custeio_cat] = "CCM" ,'fMetasDre'[valorprevisto] ,0)
```
### fMetasAbate[pesomorto_total]
```dax
(fMetasAbate[weight] * (fMetasAbate[yield]/100)) * fMetasAbate[amount]
```
### fSaldoGado[UltimaDataMovimentacao]
```dax

VAR Retiro = fSaldoGado[retironame]
VAR category = fSaldoGado[category]
VAR farm = fSaldoGado[farmname]
VAR Owner = fSaldoGado[owner]
VAR DataLinha = fSaldoGado[date]

VAR UltimaDataMovimentacao =
    CALCULATE(
        MAX(fSaldoGado[date]),
        FILTER(
            fSaldoGado,
            fSaldoGado[owner] = Owner  &&
            fSaldoGado[farmname] = farm &&
            fSaldoGado[category] = category &&
            fSaldoGado[retironame] = Retiro 
        )
    )
VAR calc = 
CALCULATE(
            SUM(fSaldoGado[amountacc]),
            FILTER(
                ALLEXCEPT(fSaldoGado,fSaldoGado[farmname],fSaldoGado[owner],fSaldoGado[category],fSaldoGado[retironame]),
                fSaldoGado[date] = UltimaDataMovimentacao
            )
        )
RETURN calc
```
### LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf[Ano]
```dax
YEAR([Date])
```
### LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf[MonthNo]
```dax
MONTH([Date])
```
### LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf[Mês]
```dax
FORMAT([Date], "MMMM")
```
### LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf[QuarterNo]
```dax
INT(([MonthNo] + 2) / 3)
```
### LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf[Trimestre]
```dax
"Qtr " & [QuarterNo]
```
### LocalDateTable_96757441-ca41-4d4d-b0d7-f41fbdf01cbf[Dia]
```dax
DAY([Date])
```
### LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3[Ano]
```dax
YEAR([Date])
```
### LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3[MonthNo]
```dax
MONTH([Date])
```
### LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3[Mês]
```dax
FORMAT([Date], "MMMM")
```
### LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3[QuarterNo]
```dax
INT(([MonthNo] + 2) / 3)
```
### LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3[Trimestre]
```dax
"Qtr " & [QuarterNo]
```
### LocalDateTable_8f782874-0750-40ce-aedf-4ace0af9edf3[Dia]
```dax
DAY([Date])
```
### pecuarioCompras[Total de @]
```dax
pecuarioCompras[peso_arroba] * pecuarioCompras[qtd]
```
### Analytics Measures[Purchased Quantity MALE]
```dax

CALCULATE(
    [Purchased Quantity],
    pecuarioCompras[sexo] = "MACHO"
)
```
### LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b[Ano]
```dax
YEAR([Date])
```
### LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b[MonthNo]
```dax
MONTH([Date])
```
### LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b[Mês]
```dax
FORMAT([Date], "MMMM")
```
### LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b[QuarterNo]
```dax
INT(([MonthNo] + 2) / 3)
```
### LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b[Trimestre]
```dax
"Qtr " & [QuarterNo]
```
### LocalDateTable_de147448-cc2e-40d0-9372-6bac62d2da1b[Dia]
```dax
DAY([Date])
```
### fPlanejadoxRealizado[Classificacao2]
```dax

SWITCH(fPlanejadoxRealizado[costcenter],
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
### fMetasAbate[pesovivo_total]
```dax
fMetasAbate[weight] *fMetasAbate[amount]
```
### fMetasAbate[Total de @]
```dax
fMetasAbate[arrobaweight] * fMetasAbate[amount]
```
### fMetasEmPe[Total de @]
```dax
(fMetasEmPe[weight] * fMetasEmPe[amount]) / 30
```
### fMetasEmPe[pesovivo_total]
```dax
fMetasEmPe[weight] *fMetasEmPe[amount]
```
### fMetasEmPe[pesomorto_total]
```dax
(fMetasEmPe[weight] * fMetasEmPe[amount]) * fMetasEmPe[yield]
```

## Measures

### Analytics Measures[Purchased Quantity]  folder=Purchase Measures
```dax

CALCULATE(SUM(pecuarioCompras[qtd]))+0
```
### Analytics Measures[Total Paid]  folder=Purchase Measures
```dax

CALCULATE(SUM(pecuarioCompras[Paid]))
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
SUM(pecuarioMortes[qtd])+0
```
### Analytics Measures[Birth Quantity]  folder=Birth Measures
```dax
CALCULATE(SUM(pecuarioNascimento[amount]))+0
```
### Analytics Measures[Average Birth Weight]  folder=Birth Measures
```dax
CALCULATE(SUM(pecuarioNascimento[peso_nasc])) /  CALCULATE(SUM(pecuarioNascimento[qtd])) 
```
### Analytics Measures[Expenses]  folder=Finance Measures
```dax
CALCULATE(
                     SUM('financeiroDre'[amountpaid]),
                     'financeiroDre'[type]="Débito"--,
                    -- pecuarioRebanhoMedioMensal[amount] > 0
                     ) * -1
```
### Analytics Measures[Revenues]  folder=Finance Measures
```dax
CALCULATE(SUM('financeiroDre'[amountpaid]),'financeiroDre'[type]="Crédito",financeiroDre[tipo_custeio_cat] IN {"Receita Pec", "Receita Agr"})
```
### Analytics Measures[Balance]  folder=Finance Measures
```dax
[Revenues] + [Expenses]
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
### Analytics Measures[Amount Saled (Abate)]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaAbate[qtd])
```
### Analytics Measures[IN - Invoicing]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaEmPe[Faturamento])+SUM(pecuarioVendaAbate[Faturamento])
```
### Analytics Measures[AVG Price @ Dead Sale]  folder=IN - General Sales Measures
```dax

CALCULATE(SUM(pecuarioVendaAbate[Faturamento]) / (SUM(pecuarioVendaAbate[Total de @])))
```
### Analytics Measures[AVG Price @ Sale Venda em Pe]  folder=IN - General Sales Measures
```dax

CALCULATE(SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[Total de @]))
```
### Analytics Measures[AVG Ticket Dead Sale]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaAbate[Faturamento]) / SUM(pecuarioVendaAbate[qtd])
```
### Analytics Measures[AVG Ticket Sale]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[qtd])
```
### Analytics Measures[Expenses Graph]  folder=Finance Measures
```dax
CALCULATE(SUM('financeiroDre'[amountpaid]),'financeiroDre'[type]="Débito") 
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
CALCULATE( SUM(pecuarioRebanhoMedioMensal[amount]) / [Count of Selected Month])
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

CALCULATE(SUM(fMetasMortes[amount]),USERELATIONSHIP(dCalendar[Data],fMetasMortes[date]))
```
### Analytics Measures[% Forecast Indicator]  folder=Dead Measures
```dax
DIVIDE([Dead Quantity forecast],SUM(fMetasRebanhoMedio[amount]))
```
### Analytics Measures[% Realized Indicator]  folder=Dead Measures
```dax
DIVIDE([Dead Quantity],SUM(pecuarioRebanhoMedioMensal[amount]))
```
### Analytics Measures[Dead Quantity Accumulated]  folder=Dead Measures
```dax

    CALCULATE(
        [Dead Quantity],
        FILTER(
            ALL(dCalendar),
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
        SUM(fMetasRebanhoMedio[amount]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        ),fMetasRebanhoMedio[amount] <> BLANK()
    )
```
### Analytics Measures[% Forecast Indicator Accumulated]  folder=Dead Measures
```dax

CALCULATE(DIVIDE([Dead Quantity Accumulated - Forecast], ([Mean Month Accumulated - Forecast]/[Count Mean Month Accumulated]), 0) )
```
### Analytics Measures[Total de @]  folder=IN - General Sales Measures
```dax

[Arroba Value] * [Amount Saled (Abate)]
```
### Analytics Measures[Arroba Value]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaAbate[ArrobaAVG]) + SUM(pecuarioVendaEmPe[arrobaAvg])
```
### Analytics Measures[Amount Saled - Forecast (Abate)]  folder=IN - General Sales Measures
```dax


VAR calc1 = CALCULATE(SUM(fMetasAbate[amount]))

RETURN calc1
```
### Analytics Measures[Incoicing - Forecast]  folder=IN - General Sales Measures
```dax


VAR calc1 = CALCULATE(SUM(fMetasAbate[totalvalue]))

--VAR calc2 = CALCULATE(SUM(fMetasEmPe))

RETURN calc1
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
        SUM(fMetasRebanhoMedio[amount]) / [Count of Selected Month],
        USERELATIONSHIP(fMetasRebanhoMedio[idfarm],fUnidades[idfarm]),
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
CALCULATE(SUM(Compras[amount]))
```
### Analytics Measures[Sell]  folder=Stock Measures
```dax
CALCULATE(sum(pecuarioVendaAbate[qtd]))
```
### Analytics Measures[Birth]  folder=Stock Measures
```dax
CALCULATE(SUM(pecuarioNascimento[amount]))
```
### Analytics Measures[Change Category entry]  folder=Stock Measures
```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Mud. de Categoria", fMovGado[Type Operation] = "Entrada")
```
### Analytics Measures[Death]  folder=Stock Measures
```dax
CALCULATE(SUM(pecuarioMortes[qtd]))
```
### Analytics Measures[comsuption / donation]  folder=Stock Measures
```dax
CALCULATE(SUM(pecuarioMortes[qtd]),pecuarioMortes[causa] = "Consumo Abate")
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
        [IN - Invoicing],
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
        [Amount Saled (Abate)],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[Amount Head Saled - Forecast Accumulated]  folder=IN - General Sales Measures
```dax

    CALCULATE(
        [Amount Saled - Forecast (Abate)],
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
### Analytics Measures[Rendimento Carcaça]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaAbate[pesomorto_total]) / SUM(pecuarioVendaAbate[pesovivo_total])
```
### Analytics Measures[Peso em @ Abate]  folder=IN - General Sales Measures
```dax

(SUM(pecuarioVendaAbate[Peso Morto Total]) / 15 ) / SUM(pecuarioVendaAbate[qtd])
```
### Analytics Measures[AVG Price @]  folder=IN - General Sales Measures
```dax
[AVG Price @ Dead Sale] + [AVG Price @ Sale Venda em Pe]
```
### Analytics Measures[Peso em @ Em Pe]  folder=IN - General Sales Measures
```dax

(SUM( pecuarioVendaEmPe[pesovivo_total])/30) / SUM(pecuarioVendaEmPe[qtd])
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
DIVIDE([IN - Invoicing],[Incoicing - Forecast]) + 0
```
### Analytics Measures[Rebanho Median Month]  folder=nan
```dax
DIVIDE([],[Count Mean Month Accumulated])
```
### Analytics Measures[UA Median Month]  folder=Purchase Measures
```dax
DIVIDE([Mean Month Accumulated - UA],[Count Mean Month Accumulated])
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
0
--Não tem por UA na API
--SUM(pecuarioRebanhoMedioMensal[qtd_ua])
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
### Analytics Measures[AVG Price @ Dead Sale - Forecast]  folder=IN - General Sales Measures
```dax

SUM(fMetasAbate[totalvalue]) / SUM(fMetasAbate[Total de @])
```
### Analytics Measures[AVG Price @ Sale Venda em Pe - Forecast]  folder=IN - General Sales Measures
```dax

CALCULATE(SUM(fMetasEmPe[totalvalue]) / SUM(fMetasEmPe[Total de @]))+0
```
### Analytics Measures[Birth Quantity - Forecast]  folder=Birth Measures
```dax

CALCULATE(SUM(fMetasNascimentos[amount]),
         USERELATIONSHIP(dCalendar[Data],fMetasNascimentos[date])
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
[Dead Quantity Accumulated] / [Birth Quantity Accumulated]
```
### Analytics Measures[% Amount Saled]  folder=IN - General Sales Measures
```dax
DIVIDE([Amount Saled - Forecast (Abate)],[Amount Saled (Abate)])
```
### Analytics Measures[Purchased Quantity - Forecast]  folder=Purchase Measures
```dax

CALCULATE(
        SUM(fMetasCompras[amount]),
        USERELATIONSHIP(dCalendar[Data],fMetasCompras[date])
        )
```
### Analytics Measures[% Purchased Quantity]  folder=Purchase Measures
```dax
DIVIDE([Purchased Quantity],[Purchased Quantity - Forecast])
```
### Analytics Measures[Dead Quantity - Forecast]  folder=Dead Measures
```dax

CALCULATE(SUM(fMetasMortes[amount]),USERELATIONSHIP(dCalendar[Data],fMetasMortes[date]))
```
### Analytics Measures[AVG Price KG Sale Venda em Pe]  folder=IN - General Sales Measures
```dax

CALCULATE(SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[Peso Total]))
```
### Analytics Measures[MAX AVG Price @ Forecast]  folder=IN - General Sales Measures
```dax
[AVG Price @ (Em Pe + Abate) - Forecast] + [AVG Price @ (Em Pe + Abate) - Forecast] * 0.15
```
### Analytics Measures[AVG Price @ (Em Pe + Abate) - Forecast]  folder=IN - General Sales Measures
```dax


VAR fat = SUM(fMetasAbate[totalvalue]) + SUM(fMetasEmPe[totalvalue])

VAR arr = (SUM(fMetasAbate[pesomorto_total])/15) + SUM(fMetasEmPe[pesomorto_total])

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
### Analytics Measures[Count of Selected Month]  folder=Dead Measures
```dax

VAR MesesComDados = 
    FILTER(
        VALUES(dCalendar[Mês]),
        CALCULATE( SUM(pecuarioRebanhoMedioMensal[amount]) ) > 0
    )
RETURN
    COUNTROWS(MesesComDados)
```
### Analytics Measures[Invoicing Abate]  folder=IN - General Sales Measures
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

IF(SELECTEDVALUE(fUnidades[farmname]) = BLANK(),"GRUPO",SELECTEDVALUE(fUnidades[farmname]))
```
### Analytics Measures[Mean Month Accumulated - Aux (Desembolso) - Forecast]  folder=Head Outlay
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
### Analytics Measures[Outlay Forecast]  folder=Finance Measures
```dax

CALCULATE(
        SUM(fMetasDre[Desembolso]),
        USERELATIONSHIP(fMetasDre[idfarm],fUnidades[idfarm]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[date])
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
        USERELATIONSHIP(fMetasDre[idfarm],fUnidades[idfarm]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[date])
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
DIVIDE([Outlay],[Outlay Forecast])
```
### Analytics Measures[Color Desemb Cab Mês]  folder=nan
```dax

    IF([head outlay accumulated] > [head outlat accumulated - forecast], "#870000","#007D08")
```
### Analytics Measures[Color Costing Cab Mês]  folder=nan
```dax

    IF([Costing head Accumulated] > [Costing Head accumulated - forecast], "#870000","#007D08")
```
### Analytics Measures[Color @ Venda Geral]  folder=nan
```dax

    IF([AVG Price @ (Em Pe + Abate)] > [AVG Price @ (Em Pe + Abate) - Forecast],"#007D08", "#870000")
```
### Analytics Measures[IN Venda Geral]  folder=nan
```dax

    IF([IN - Invoicing] > [Incoicing - Forecast],1,-1)
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
### fSaldoGado[Saldo Acumulado]  folder=nan
```dax


VAR UltimaDataMovimentacao = MAX(dCalendar[Data])
   /* CALCULATE(
        MAX(fSaldoGado[date]),
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )*/

VAR calc = 
    CALCULATE(
        SUM(fSaldoGado[amountacc]),
        FILTER(
            ALLEXCEPT(fSaldoGado, fSaldoGado[farmname], fSaldoGado[owner], fSaldoGado[category], fSaldoGado[retironame],fUnidades[farmname],fUnidades[customer]),
            fSaldoGado[date] = UltimaDataMovimentacao
        ),
        ALL(dCalendar)  -- <-- isso remove o cross-filter do dCalendar
    )

RETURN calc
```
### fSaldoGado[Saldo UltimaDataMovimentacao]  folder=nan
```dax


VAR RetiroSelecionado = SELECTEDVALUE(fSaldoGado[retironame])
VAR Retiro = SELECTEDVALUE(fSaldoGado[retironame])
VAR category = SELECTEDVALUE(fSaldoGado[category])
VAR farm = SELECTEDVALUE(fSaldoGado[farmname])
VAR Owner = SELECTEDVALUE(fSaldoGado[owner])
VAR DataLinha = SELECTEDVALUE(fSaldoGado[date]) 
RETURN
    CALCULATE(
        MAX(fSaldoGado[date]),
        FILTER(
            ALL(dCalendar),
          --  fSaldoGado[owner] = Owner  &&
          --  fSaldoGado[farmname] = farm &&
          --  fSaldoGado[category] = category &&
          --  fSaldoGado[retironame] = Retiro &&
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### fSaldoGado[Saldo 32322]  folder=nan
```dax
SUM(fSaldoGado[UltimaDataMovimentacao])
```
### fSaldoGado[SaldoCategoria_Final]  folder=nan
```dax

VAR DataMaximaVisivel =
    MAX(dCalendar[Data])

VAR TabelaRetirosCategorias =
    SUMMARIZE(
        fSaldoGado,
        fSaldoGado[retironame],
        fSaldoGado[category]
    )

VAR TabelaUltimosSaldosComValores =
    ADDCOLUMNS(
        TabelaRetirosCategorias,
        "Valor",
        VAR Retiro = [retironame]
        VAR Categoria = [category]
        VAR DataUltimaMovimentacao =
            CALCULATE(
                MAX(fSaldoGado[date]),
                FILTER(
                    fSaldoGado,
                    fSaldoGado[retironame] = Retiro &&
                    fSaldoGado[category] = Categoria &&
                    fSaldoGado[date] <= DataMaximaVisivel
                )
            )
        RETURN
            CALCULATE(
                MAX(fSaldoGado[amountacc]),
                fSaldoGado[retironame] = Retiro &&
                fSaldoGado[category] = Categoria &&
                fSaldoGado[date] = DataUltimaMovimentacao
            )
    )

RETURN
    SUMX(
        TabelaUltimosSaldosComValores,
        [Valor]
    )

```
### Analytics Measures[@ AVG Price Purchase]  folder=Purchase Measures
```dax

CALCULATE(SUM(pecuarioCompras[VALOR TOTAL]) / (SUM(pecuarioCompras[Total de @])))
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
### Analytics Measures[AVG Purchase Price KG]  folder=Purchase Measures
```dax

CALCULATE(SUM(pecuarioCompras[VALOR TOTAL]) / SUM(pecuarioCompras[total_peso]))+0
```
### Analytics Measures[AVG Purchase Price KG (Forecast)]  folder=Purchase Measures
```dax

CALCULATE(SUM(fMetasCompras[totalvalue]) / SUM(fMetasCompras[weight]))+0
```
### Analytics Measures[IN AVG - Peso Médio de Compra]  folder=Purchase Measures
```dax


VAR calc1 = SUM(pecuarioCompras[qtd])

VAR calc2 = SUM(pecuarioCompras[total_peso])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[IN AVG - Peso Médio de Compra (Forecast)]  folder=Purchase Measures
```dax


VAR calc1 = SUM(fMetasCompras[amount])

VAR calc2 = SUM(fMetasCompras[weight])

RETURN DIVIDE(calc2,calc1)
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
### Analytics Measures[Purchased Quantity FEMALE]  folder=Purchase Measures
```dax

CALCULATE(
    [Purchased Quantity],
    pecuarioCompras[sexo] = "FÊMEA"
)
```
### Analytics Measures[Total Paid - Forecast]  folder=Purchase Measures
```dax

CALCULATE(
        SUM(fMetasCompras[totalvalue]),
        USERELATIONSHIP(dCalendar[Data],fMetasCompras[date])
        )+0
```
### Analytics Measures[UA Median Ha]  folder=Purchase Measures
```dax
[UA Median Month] / (SUM(fArea[Área_total]) / [Count of Selected Month])
```
### Analytics Measures[IN - % Female Birth]  folder=Birth Measures
```dax


VAR tot = [Birth Quantity]

VAR qtdmale = CALCULATE([Birth Quantity], pecuarioNascimento[gender] = "FÊMEA")

RETURN DIVIDE(qtdmale,tot)
```
### Analytics Measures[IN - % Male Birth]  folder=Birth Measures
```dax


VAR tot = [Birth Quantity]

VAR qtdmale = CALCULATE([Birth Quantity], pecuarioNascimento[gender] = "MACHO")

RETURN DIVIDE(qtdmale,tot)
```
### Analytics Measures[% Mortality ( AVG Month)]  folder=Dead Measures
```dax
[Dead Quantity] / [Mean Month]
```
### Analytics Measures[% Variação]  folder=Finance Measures
```dax

DIVIDE(
                            [Valor Último Mês Selecionado]-[Meta Último Mês Selecionado],[Meta Último Mês Selecionado]
                        )

```
### Analytics Measures[Valor Último Mês Selecionado]  folder=Finance Measures
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
        SUM('fPlanejadoxRealizado'[realizado]), 
        FiltrosDeData,
        'fPlanejadoxRealizado'[classificacao] = "A - RECEITAS"
    )

VAR Despesas = 
    CALCULATE(
        SUM('fPlanejadoxRealizado'[realizado]), 
        FiltrosDeData,
        'fPlanejadoxRealizado'[classificacao] IN {"C - INVESTIMENTOS","D - CUSTEIO","E - OUTROS DÉBITOS"}
    )

RETURN 
    IF(
        ISINSCOPE('fPlanejadoxRealizado'[Classificacao]),
        
        -- Cálculo linha a linha (dentro do escopo)
        CALCULATE(
            SUM('fPlanejadoxRealizado'[realizado]), 
            FiltrosDeData
        ),
        
        -- Cálculo do Total Final
        -- O COALESCE garante que se Receitas for BLANK, ele usa 0.
        -- Assim a conta fica: 0 - Despesas = -Despesas (o total aparece negativo corretamente)
        COALESCE(Receitas, 0) - COALESCE(Despesas, 0)
    )
```
### Analytics Measures[Meta Último Mês Selecionado]  folder=Finance Measures
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
        ISINSCOPE('fPlanejadoxRealizado'[Classificacao]),
        CALCULATE(
            SUM('fPlanejadoxRealizado'[meta]), 
            FiltrosDeData
        ),
        CALCULATE(
            SUM('fPlanejadoxRealizado'[meta]), 
            FiltrosDeData,
            'fPlanejadoxRealizado'[Classificacao] = "A - RECEITAS"
        ) - 
        CALCULATE(
            SUM('fPlanejadoxRealizado'[meta]), 
            FiltrosDeData,
            'fPlanejadoxRealizado'[Classificacao] IN {"C - INVESTIMENTOS","D - CUSTEIO","E - OUTROS DÉBITOS"}
        )
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
### Analytics Measures[All Revenues]  folder=Finance Measures
```dax
CALCULATE(SUM('financeiroDre'[amountpaid]),'financeiroDre'[type]="Crédito",financeiroDre[tipo_custeio_cat] IN {"Receita Pec", "Receita Agr","Receita outras"})
```
### Analytics Measures[Expenses Forecast]  folder=Finance Measures
```dax

CALCULATE(
        SUM(fMetasDre[valorprevisto]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[date]),
        'fMetasDre'[type]="Débito"
        )
```
### Analytics Measures[Icon]  folder=Finance Measures
```dax

--IF(
   -- ISINSCOPE(planejadoXRealizado[centro_de_custo_bi]),
    VAR _var = [% Variação]
    VAR _class = SELECTEDVALUE(fPlanejadoxRealizado[classificacao])
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
### Analytics Measures[Icon Acc]  folder=Finance Measures
```dax

--IF(
 --   ISINSCOPE(planejadoXRealizado[centro_de_custo_bi]),
    VAR _var = [%% Variação Acc]
    VAR _class = SELECTEDVALUE(fPlanejadoxRealizado[Classificacao2])
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
### Analytics Measures[Meta Accumulated]  folder=Finance Measures
```dax

VAR _MaxDate = MAX(dCalendar[Data])
VAR _IsClassInScope = ISINSCOPE(fPlanejadoxRealizado[classificacao])

RETURN
IF(
    _IsClassInScope,
    -- Acumulado da própria classificação (quando class está no escopo)
    CALCULATE(
        SUM('fPlanejadoxRealizado'[meta]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= _MaxDate
        )
    ),
    -- Quando não há classificação no escopo: ReceitasAcum - DespesasAcum
    VAR ReceitasAcum =
        CALCULATE(
            SUM('fPlanejadoxRealizado'[meta]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= _MaxDate),
            fPlanejadoxRealizado[Classificacao] = "A - RECEITAS"
        )
    VAR DespesasAcum =
        CALCULATE(
            SUM('fPlanejadoxRealizado'[meta]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= _MaxDate),
            fPlanejadoxRealizado[Classificacao] IN {
                "C - INVESTIMENTOS",
                "D - CUSTEIO",
                "E - OUTROS DÉBITOS"
            }
        )
    RETURN
        ReceitasAcum - DespesasAcum
)

```
### Analytics Measures[Revenues Forecast]  folder=Finance Measures
```dax

CALCULATE(
        SUM(fMetasDre[valorprevisto]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[date]),
        'fMetasDre'[type]="Crédito",
        fMetasDre[tipo_custeio_cat] IN {"ReceitasPec","ReceitasAgr","ReceitaPec","ReceitaAgr"}
        )
```
### Analytics Measures[RL Acumulado]  folder=Finance Measures
```dax
"ACUMULADO"
```
### Analytics Measures[RL Mensal]  folder=Finance Measures
```dax
"MENSAL"
```
### Analytics Measures[Value Accumulated]  folder=Finance Measures
```dax

VAR LastDate2 = MAX(dCalendar[Data])
VAR IsClassInScope = ISINSCOPE(fPlanejadoxRealizado[classificacao])

RETURN
IF(
    IsClassInScope,
    -- Quando o usuário está vendo uma classificação específica: acumulado simples da própria linha
    CALCULATE(
        SUM(fPlanejadoxRealizado[realizado]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= LastDate2
        )
    ),
    -- Quando não está em escopo de classificacao: acumulado = Receitas acumuladas - Despesas acumuladas
    VAR ReceitasAcum =
        CALCULATE(
            SUM(fPlanejadoxRealizado[realizado]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= LastDate2),
            fPlanejadoxRealizado[Classificacao] = "A - RECEITAS"
        )
    VAR DespesasAcum =
        CALCULATE(
            SUM(fPlanejadoxRealizado[realizado]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= LastDate2),
            fPlanejadoxRealizado[Classificacao] IN {
                "C - INVESTIMENTOS",
                "D - CUSTEIO",
                "E - OUTROS DÉBITOS"
            }
        )
    RETURN
        ReceitasAcum - DespesasAcum
)

```
### Analytics Measures[Mean Month Ha]  folder=Head Outlay
```dax
[Mean Month] / (500 / [Count of Selected Month])
```
### Analytics Measures[IN - % Meta]  folder=IN - Data Labels
```dax
"% Em Relação a Meta"
```
### Analytics Measures[IN - Adultos]  folder=IN - Data Labels
```dax
"ADULTOS"
```
### Analytics Measures[IN - Ágio]  folder=IN - Data Labels
```dax
"Ágio"
```
### Analytics Measures[IN - Bezerro]  folder=IN - Data Labels
```dax
"BEZERROS"
```
### Analytics Measures[IN - Cabeças]  folder=IN - Data Labels
```dax
"Cb"
```
### Analytics Measures[IN - Cbs Compradas]  folder=IN - Data Labels
```dax
"Cbs Compradas"
```
### Analytics Measures[IN - Cbs Vendidas]  folder=IN - Data Labels
```dax
"Cabeças Vendidas"
```
### Analytics Measures[IN - Compra]  folder=IN - Data Labels
```dax
"Valor Compra"
```
### Analytics Measures[IN - COMPRA X VENDA]  folder=IN - Data Labels
```dax
"COMPRAS | VENDAS"
```
### Analytics Measures[IN - Compras (Label 2 )]  folder=IN - Data Labels
```dax
"Compras"
```
### Analytics Measures[IN - Compras (Label)]  folder=IN - Data Labels
```dax
"COMPRAS"
```
### Analytics Measures[IN - Data Análise]  folder=IN - Data Labels
```dax
"Análise :"
```
### Analytics Measures[IN - Entrada]  folder=IN - Data Labels
```dax
"ENTRADA"
```
### Analytics Measures[IN - Faturamento]  folder=IN - Data Labels
```dax
"Fat. Realizado"
```
### Analytics Measures[IN - Faturamento Planejado]  folder=IN - Data Labels
```dax
"Fat. Planejado"
```
### Analytics Measures[IN - Fêmea]  folder=IN - Data Labels
```dax
"FÊMEA"
```
### Analytics Measures[IN - Geral]  folder=IN - Data Labels
```dax
"GERAL"
```
### Analytics Measures[IN - Indice de Mortalidade]  folder=IN - Data Labels
```dax
"Índ. Mortalidade"
```
### Analytics Measures[IN - Inv Planejado]  folder=IN - Data Labels
```dax
"Inv. Planejado"
```
### Analytics Measures[IN - Inv Realizado]  folder=IN - Data Labels
```dax
"Inv. Realizado"
```
### Analytics Measures[IN - Jovens]  folder=IN - Data Labels
```dax
"JOVENS"
```
### Analytics Measures[IN - Lotação Cab]  folder=IN - Data Labels
```dax
"Lotação Cab"
```
### Analytics Measures[IN - Lotação UA]  folder=IN - Data Labels
```dax
"Lotação UA"
```
### Analytics Measures[IN - Macho]  folder=IN - Data Labels
```dax
"MACHO"
```
### Analytics Measures[IN - Meta]  folder=IN - Data Labels
```dax
"Planejado"
```
### Analytics Measures[IN - Meta Valor KG]  folder=IN - Data Labels
```dax
"Meta Valor KG" 
```
### Analytics Measures[IN - Mortalidade sobre Nascimento]  folder=IN - Data Labels
```dax
"% Sobre Nascimento"
```
### Analytics Measures[IN - Mortalidade sobre Rebanho Médio]  folder=IN - Data Labels
```dax
"% Sobre Rebanho Médio"
```
### Analytics Measures[IN - Mortes]  folder=IN - Data Labels
```dax
"MORTES"
```
### Analytics Measures[IN - Mortes (2)]  folder=IN - Data Labels
```dax
"Mortes"
```
### Analytics Measures[IN - Nascimentos]  folder=IN - Data Labels
```dax
"% Sobre Sobre o Total"
```
### Analytics Measures[IN - Nascimentos (Label - 2)]  folder=IN - Data Labels
```dax
"NASCIMENTOS"
```
### Analytics Measures[IN - Nascimentos (Label)]  folder=IN - Data Labels
```dax
"Nascimentos"
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
### Analytics Measures[IN - Peso Médio Vivo]  folder=IN - Data Labels
```dax
"Peso Médio Vivo"
```
### Analytics Measures[IN - Planejado]  folder=IN - Data Labels
```dax
"Planejado"
```
### Analytics Measures[IN - Preço do KG]  folder=IN - Data Labels
```dax
"Preço do KG" 
```
### Analytics Measures[IN - Quantidade]  folder=IN - Data Labels
```dax
"QTD" 
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
### Analytics Measures[IN - Relação a Meta]  folder=IN - Data Labels
```dax
"% Em relação a Meta"
```
### Analytics Measures[IN - Rendimento de Carcaça]  folder=IN - Data Labels
```dax
"Rendimento de Carcaça"
```
### Analytics Measures[IN - Saida]  folder=IN - Data Labels
```dax
"SAÍDA"
```
### Analytics Measures[IN - Separador de]  folder=IN - Data Labels
```dax
"de" 
```
### Analytics Measures[IN - Site Terra]  folder=IN - Data Labels
```dax
"terradesenvolvimento.com.br"
```
### Analytics Measures[IN - TRANSFERÊNCIAS]  folder=IN - Data Labels
```dax
"TRANSFERÊNCIAS"
```
### Analytics Measures[IN - Valor da @]  folder=IN - Data Labels
```dax
"Preço de Venda da @"
```
### Analytics Measures[IN - Valor da @ Compra]  folder=IN - Data Labels
```dax
"Preço de @ de Compra"
```
### Analytics Measures[IN - Vendas (Geral)]  folder=IN - Data Labels
```dax
"VENDAS"
```
### Analytics Measures[IN - Vendas (Label)]  folder=IN - Data Labels
```dax
"Vendas"
```
### Analytics Measures[IN Peso Médio]  folder=IN - Data Labels
```dax
"PESO MÉDIO"
```
### Analytics Measures[IN Valor@]  folder=IN - Data Labels
```dax
"VALOR @"
```
### Analytics Measures[IN - Invoicing - Forecast (Abate)]  folder=nan
```dax


VAR calc1 = CALCULATE(SUM(fMetasAbate[totalvalue]))

RETURN calc1+0
```
### Analytics Measures[Invoicing Accumulated (Abate)]  folder=IN - General Sales Measures
```dax

    CALCULATE(
        SUM(pecuarioVendaAbate[qtd])+0,
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[IN - AVG Live Weight]  folder=IN - General Sales Measures
```dax


VAR calc1 = SUM(pecuarioVendaAbate[qtd])

VAR calc2 = SUM(pecuarioVendaAbate[pesovivo_total])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[IN - AVG Live Weight (Forecast)]  folder=IN - General Sales Measures
```dax


VAR calc1 = SUM(fMetasAbate[amount])

VAR calc2 = SUM(fMetasAbate[weight])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[IN - Rendimento Carcaça (Forecast)]  folder=IN - General Sales Measures
```dax
SUM(fMetasAbate[pesomorto_total]) / SUM(fMetasAbate[pesovivo_total])

```
### Analytics Measures[Invoicing (Em Pe )]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaEmPe[Faturamento])+0
```
### Analytics Measures[Incoicing - Forecast (Em Pe)]  folder=IN - General Sales Measures
```dax


VAR calc1 = CALCULATE(SUM(fMetasEmPe[totalvalue]))

RETURN calc1
```
### Analytics Measures[Amount Saled Accumulated (Em Pe)]  folder=IN - General Sales Measures
```dax

    CALCULATE(
        SUM(pecuarioVendaEmPe[qtd])+0,
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```
### Analytics Measures[Amount Saled (Em pe)]  folder=IN - General Sales Measures
```dax
SUM(pecuarioVendaEmPe[qtd])
```
### Analytics Measures[Amount Saled - Forecast (Em Pe)]  folder=IN - General Sales Measures
```dax


VAR calc1 = CALCULATE(SUM(fMetasEmPe[amount]))


RETURN calc1
```
### Analytics Measures[IN - AVG Live Weight (Em Pe)]  folder=IN - General Sales Measures
```dax


VAR calc1 = SUM(pecuarioVendaEmPe[qtd])

VAR calc2 = SUM(pecuarioVendaEmPe[pesovivo_total])

RETURN DIVIDE(calc2,calc1)+0
```
### Analytics Measures[IN - AVG Live Weight (Forecast - Em Pe)]  folder=IN - General Sales Measures
```dax


VAR calc1 = SUM(fMetasEmPe[amount])

VAR calc2 = SUM(fMetasEmPe[pesovivo_total])

RETURN DIVIDE(calc2,calc1)
```
### Analytics Measures[AVG Price KG Sale Venda em Pe - Forecast]  folder=IN - General Sales Measures
```dax

CALCULATE(SUM(fMetasEmPe[totalvalue]) / SUM(fMetasEmPe[pesovivo_total]))+0
```

## Power Query (M)

### pecuarioNascimento
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT idcustomer, customer, idfarm, farmname, idretiro, retironame, owner, anosafra, idcategory, category, harvest, amount, gender, date,#(lf)#(tab)CONCAT(idcustomer,idfarm) as idpropfaz#(lf)#(tab)FROM ""DATABASE"".stg_nascimentos;"),
    #"Colunas Renomeadas" = Table.RenameColumns(Fonte,{{"date", "DATA"}}),
    #"Valor Substituído" = Table.ReplaceValue(#"Colunas Renomeadas"," 00:00:00.000","",Replacer.ReplaceText,{"DATA"}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Valor Substituído",{{"DATA", type date}}),
    #"Linhas Filtradas" = Table.SelectRows(#"Tipo Alterado", each ([idfarm] <> null))
in
    #"Linhas Filtradas"
```
### pecuarioRebanhoMedioMensal
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT idcustomer, customer, idfarm, farmname, idretiro, retironame, owner, anosafra, amount, gender, idcategory, category, month,#(lf)#(tab)CONCAT(idcustomer,idfarm) as idpropfaz#(lf)#(tab)FROM ""DATABASE"".stg_rebanho_medio#(lf)        WHERE idfarm is not null;"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"month", type date}}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Tipo Alterado",{{"month", "DATA"}})
in
    #"Colunas Renomeadas"
```
### pecuarioVendaAbate
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT#(lf)#(tab)t.client as cliente,#(lf)#(tab)t.category as categ_fazenda,#(lf)#(tab)t.date as ""DATA"",#(lf)#(tab)t.amount as qtd,#(lf)#(tab)t.liveweightavg as peso_vivo,#(lf)#(tab)t.deadarrobaavg as peso_arroba,#(lf)#(tab)t.valuearroba as valor_arroba,#(lf)#(tab)t.totalfaturamento as faturamento,#(lf)#(tab)t.category as categoria_bi,#(lf)#(tab)t.gender as sexo,#(lf)#(tab)t.deadweightavg as peso_morto,#(lf)#(tab)t.weighttotal as pesovivo_total,#(lf)#(tab)t.amount * t.deadweightavg as pesomorto_total,#(lf)#(tab)t.valueweight as valor_kg,#(lf)#(tab)t.totalfaturamento / t.amount as valor_cab,#(lf)#(tab)t.customer as ""proprietArio"",#(lf)#(tab)t.farmname as fazenda,#(lf)#(tab)t.retironame as retiro,#(lf)        CONCAT(t.idcustomer,t1.idfarm) as idpropfaz#(lf)#(tab)FROM ""DATABASE"".stg_vendas t#(lf)#(tab)LEFT JOIN ""DATABASE"".stg_farm t1 on t1.idcustomer = t.idcustomer and t1.farmname = t.farmname#(lf)where deadarrobaavg is not null and t1.idfarm is not null#(lf)"),
    #"Tipo Alterado1" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado1"
```
### pecuarioVendaEmPe
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "#(lf)SELECT#(lf)#(tab)t.client as cliente,#(lf)#(tab)t.category as categ_fazenda,#(lf)#(tab)t.date as ""DATA"",#(lf)#(tab)t.amount as qtd,#(lf)#(tab)t.liveweightavg as peso_vivo,#(lf)#(tab)t.liveweightavg / 15 as peso_arroba,#(lf)#(tab)t.valuearroba as valor_arroba,#(lf)#(tab)t.totalfaturamento as faturamento,#(lf)#(tab)t.category as categoria_bi,#(lf)#(tab)t.gender as sexo,#(lf)#(tab)--deadweightavg as peso_morto,#(lf)#(tab)t.weighttotal as pesovivo_total,#(lf)#(tab)--amount * deadweightavg as pesomorto_total,#(lf)#(tab)t.valueweight as valor_kg,#(lf)#(tab)t.totalfaturamento / t.amount as valor_cab,#(lf)#(tab)t.customer as ""proprietÁrio"",#(lf)#(tab)t.farmname as fazenda,#(lf)#(tab)t.retironame as retiro,#(lf)#(tab)CONCAT(t.idcustomer,t1.idfarm) as idpropfaz#(lf)#(tab)--idcustomer, customer, farmname, idretiro, retironame, owner, date, anosafra, gender, , , , , valueweight, , , discounts, harvest, birth, additions#(lf)#(tab)FROM ""DATABASE"".stg_vendas t#(lf)#(tab)LEFT JOIN ""DATABASE"".stg_farm t1 on t1.idcustomer = t.idcustomer and t1.farmname = t.farmname#(lf)where deadarrobaavg is null and t1.idfarm is not null#(lf)"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### pecuarioCompras
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "#(lf)SELECT #(lf)#(tab)t.date as ""DATA"",#(lf)#(tab)t.category as categ_fazenda, #(lf)#(tab)t.amount as qtd, #(lf)#(tab)t.weighttotal as total_peso,#(lf)#(tab)t.totalfaturamento / t.amount as valor_cab,#(lf)#(tab)t.totalfaturamento as ""VALOR TOTAL"",#(lf)#(tab)--(t.amount * t.weighttotal),#(lf)#(tab)t.totalfaturamento / (t.amount * t.weighttotal) as valo_kg,#(lf)#(tab)t.valuearroba as valor_arroba, #(lf)#(tab)t.category as categoria_bi,#(lf)#(tab)t.gender as sexo,#(lf)#(tab)t.weighttotal / 15 as peso_arroba,#(lf)#(tab)t.owner as ""proprietArio"",#(lf)#(tab)t.farmname as fazenda,#(lf)#(tab)t.categoryid, #(lf)#(tab)t.idcustomer,#(lf)#(tab)t.customer, #(lf)#(tab)t.farmname, #(lf)#(tab)t.idretiro, #(lf)#(tab)t.retironame, #(lf)#(tab)t.anosafra,#(lf)#(tab)t.provider, #(lf)#(tab)t.averagevalue, #(lf)#(tab)t.valueweight,#(lf)#(tab)CONCAT(t.idcustomer,t1.idfarm) as idpropfaz#(lf)FROM ""DATABASE"".stg_compras t#(lf)LEFT JOIN ""DATABASE"".stg_farm t1 on t1.idcustomer = t.idcustomer and t1.farmname = t.farmname#(lf)WHERE t1.idfarm is not null"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### pecuarioDesmame
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT idcustomer, customer, idfarm, farmname, idretiro, retironame, owner, anosafra, date, oldcategory, oldcategoryid, birthdate, harvest, newcategory, newcategoryid, amount, weight, valueweight, gender, CONCAT(idcustomer,idfarm) as idpropfaz#(tab)FROM ""DATABASE"".stg_desmames WHERE idfarm is not null;"),
    #"Colunas Renomeadas" = Table.RenameColumns(Fonte,{{"date", "DATA"}}),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Colunas Renomeadas",{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### pecuarioMortes
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT #(lf)#(tab)date AS ""DATA"",#(lf)#(tab)categoryid,#(lf)#(tab)category AS categ_fazenda,#(lf)#(tab)null as carimbo_bez,#(lf)#(tab)amount as qtd,#(lf)#(tab)cause as causa, #(tab)#(lf)#(tab)locale as pasto,#(lf)#(tab)totalweight as peso_vivo,#(tab) #(lf)#(tab)anosafra as safra, #(lf)#(tab)enumgroup, #(lf)#(tab)namegroup as grupo_categoria,#(tab)#(lf)#(tab)era, #(lf)#(tab)category as categoria_bi,#(lf)#(tab)totalweight as peso_total,#(lf)#(tab)gender as sexo,#(tab)#(lf)#(tab)owner as ""proprietArio"",#(lf)#(tab)idfarm,#(lf)#(tab)farmname as fazenda,#(lf)#(tab)idcustomer, #(lf)#(tab)customer, #(lf)#(tab)idretiro,#(lf)#(tab)retironame,#(lf)#(tab)CONCAT(idcustomer,idfarm) as idpropfaz#(lf)#(tab)#(lf)FROM ""DATABASE"".stg_mortes#(lf)WHERE idfarm is not null"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"DATA", type date}})
in
    #"Tipo Alterado"
```
### financeiroDre
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "WITH mapa (costcenter, custeio_cat, tipo_custeio_cat, desembolso_cat) AS (#(lf)    VALUES#(lf)    (U&'Almoxarifado',                                      '0,0',            '0,0',            '0,0'),#(lf)    (U&'Arrendamento',                                      'Receita outras', 'Receita outras', 'Receita outras'),#(lf)    (U&'Cultura - Receita',                                 'Receita Agr',    'Receita Agr',    'Receita Agr'),#(lf)    (U&'Culturas - Despesa',                                'CCM',            'CV',             'DCM'),#(lf)    (U&'Dividendos',                                        '0,0',            '0,0',            '0,0'),#(lf)    (U&'Empr\00E9stimos s\00F3cios d\00E9bito',             '0,0',            '0,0',            '0,0'),#(lf)    (U&'Financiamentos cr\00E9ditos',                       'Financiamentos', 'Financiamentos', 'Financiamentos'),#(lf)    (U&'Financiamentos d\00E9bitos',                        '0,0',            '0,0',            'DCM'),#(lf)    (U&'Forrageiras e Culturas Anuais',                     'CCM',            'CV',             'DCM'),#(lf)    (U&'Insumos do rebanho',                                'CCM',            'CV',             'DCM'),#(lf)    (U&'Investimentos em RH',                               '0,0',            '0,0',            'DCM'),#(lf)    (U&'Investimentos em infraestrutura',                   'CCM',            'CF',             'DCM'),#(lf)    (U&'Investimentos em outros animais',                   'CCM',            'CF',             'DCM'),#(lf)    (U&'Manuten\00E7\00E3o da fazenda',                     'CCM',            'CF',             'DCM'),  -- revisar#(lf)    (U&'Milheto',                                           '0,0',            '0,0',            '0,0'),#(lf)    (U&'Milho Safrinha',                                    'CCM',            'CV',             'DCM'),#(lf)    (U&'M\00E3o de Obra Geral',                             'CCM',            'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Administra\00E7\00E3o',  'CCM',            'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Cultura',                'CCM',            'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Manuten\00E7\00E3o da Fazenda', 'CCM',     'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Parque de M\00E1quinas', 'CCM',            'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Rebanho',                'CCM',            'CF',             'DCM'),#(lf)    (U&'Outros animais',                                    'CCM',            'CF',             'DCM'),#(lf)    (U&'Pastagens',                                         'CCM',            'CV',             'DCM'),#(lf)    (U&'Rebanho',                                           'Receita Pec',    'Receita Pec',    'Receita Pec'),#(lf)    (U&'Rebanho Investimento',                              'CCM',            'CV',             'DCM'),#(lf)    (U&'Receitas Parque de m\00E1quinas',                   'Receita outras', 'Receita outras', 'Receita outras'),#(lf)    (U&'Receitas financeiras',                              'Financiamentos', 'Financiamentos', 'Financiamentos'),#(lf)    (U&'Receitas outros',                                   'Receita outras', 'Receita outras', 'Receita outras'),#(lf)    (U&'Silagem de Capim',                                  'CCM',            'CV',             'DCM'),#(lf)    (U&'Silagem de Milheto',                                'CCM',            'CV',             'DCM'),#(lf)    (U&'Silagem de Milho',                                  'CCM',            'CV',             'DCM'),#(lf)    (U&'Silagem',                                           'CCM',            'CV',             'DCM'),#(lf)    (U&'Soja',                                              'CCM',            'CV',             'DCM'),#(lf)    (U&'Sorgo Gr\00E3o',                                    'CCM',            'CV',             'DCM'),#(lf)    (U&'Suporte \00E0 Produ\00E7\00E3o Administra\00E7\00E3o', 'CCM',         'CF',             'DCM'),#(lf)    (U&'Suporte \00E0 Produ\00E7\00E3o Parque de m\00E1quinas', 'CCM',        'CF',             'DCM'),#(lf)    (U&'Taxas e impostos',                                  'CCM',            'CF',             'DCM'),  -- revisar#(lf)    (U&'Vendas outros animais',                             'Receita outras', 'Receita outras', 'Receita outras')#(lf))#(lf)SELECT#(lf)    t.idcustomer,#(lf)    translate(t.customer,          chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS customer,#(lf)    translate(t.farmfiscal,        chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS farmfiscal,#(lf)    t.idfarmdestination,#(lf)    translate(t.farmdestination,   chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS farmdestination,#(lf)    translate(t.""owner"",           chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS ""owner"",#(lf)    t.idfinancialentrie,#(lf)    t.idpayment,#(lf)    t.anosafra,#(lf)    translate(t.costcenter,        chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS costcenter,#(lf)    translate(t.description,       chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS description,#(lf)    t.code,#(lf)    translate(t.classe,            chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS classe,#(lf)    translate(t.subcenter,         chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS subcenter,#(lf)    translate(t.activity,          chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS activity,#(lf)    t.doctype,#(lf)    t.conciliationdate,#(lf)    t.datepayment,#(lf)    t.duedate,#(lf)    t.""type"",#(lf)    t.amountpayable,#(lf)    t.amountpaid,#(lf)    t.currency,#(lf)    t.status,#(lf)    t.emissiondate,#(lf)    t.parcel,#(lf)    CONCAT(t.idcustomer, t1.idfarm)               AS idpropfaz,#(lf)    COALESCE(m.custeio_cat,      'VERIFICAR')     AS custeio_cat,#(lf)    COALESCE(m.tipo_custeio_cat, 'VERIFICAR')     AS tipo_custeio_cat,#(lf)    COALESCE(m.desembolso_cat,   'VERIFICAR')     AS desembolso_cat#(lf)FROM ""DATABASE"".stg_dre t#(lf)JOIN ""DATABASE"".stg_farm t1#(lf)       ON t1.idcustomer = t.idcustomer#(lf)      AND t1.farmname   = t.farmfiscal#(lf)LEFT JOIN mapa m#(lf)       ON m.costcenter = t.costcenter"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"datepayment", type date}, {"duedate", type date}})
in
    #"Tipo Alterado"
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
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT idcustomer, customer, idcategory, category, categorygroup, agecategory, gender#(lf)#(tab)FROM ""DATABASE"".stg_category;"),
    #"Linhas Filtradas" = Table.SelectRows(Fonte, each ([idcategory] <> null))
in
    #"Linhas Filtradas"
```
### Tabela
```m
let
    Fonte = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i45WckxKLElVitWJVnLNVQgAsmIB", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [TipoVenda = _t]),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"TipoVenda", type text}})
in
    #"Tipo Alterado"
```
### Compras
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT #(lf)#(tab)t.idcustomer, t.customer, t.farmname, t.idretiro,#(lf)#(tab)t.retironame, t.owner, t.date, t.anosafra, t.gender,#(lf)#(tab)t.provider, t.category, t.categoryid, t.amount, #(lf)#(tab)t.weighttotal, t.averagevalue, t.valueweight, #(lf)#(tab)t.valuearroba, t.totalfaturamento, t.harvest, t.birth,#(lf)#(tab)CONCAT(t.idcustomer,t1.idfarm) as idpropfaz#(lf)#(tab)FROM ""DATABASE"".stg_compras t#(lf)#(tab)LEFT JOIN ""DATABASE"".stg_farm t1 on t1.idcustomer = t.idcustomer and t1.farmname = t.farmname#(lf)#(lf)WHERE t1.idfarm is not null"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"date", type date}})
in
    #"Tipo Alterado"
```
### fUnidades
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT idcustomer, customer, idfarm, farmname, concat(idcustomer,idfarm) as idpropfaz#(lf)#(tab)FROM ""DATABASE"".stg_customers#(lf)WHERE idfarm is not null;")
in
    Fonte
```
### fMetasCompras
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "#(lf)SELECT #(lf)#(tab)CONCAT(idcustomer,idfarm) as idpropfaz, idcustomer, customer, idfarm, farmname, idretiro, retironame, idowner, ownername, idplherdtype, plherdtypename, idcurrency, currencyname, month, to_date(date, 'MM/YY') as date, harvest, anosafra, idcategory, categoryname, idanimalgroup, animalgroupname, age, gender, amount, weight, arrobavalue, arrobaweight, value, totalvalue#(lf)#(tab)FROM ""DATABASE"".stg_comprasprevisto#(lf)WHERE idfarm is not null")
in
    Fonte
```
### fMetasAbate
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT CONCAT(idcustomer,idfarm) as idpropfaz, idcustomer, customer, idfarm, farmname, idretiro, retironame, idowner, ownername, idplherdtype, plherdtypename, idcurrency, currencyname, month, date, harvest, anosafra, idcategory, categoryname, idanimalgroup, animalgroupname, age, gender, amount, weight, arrobavalue, arrobaweight, value, totalvalue,yield,tipo#(lf)#(tab)FROM ""DATABASE"".stg_vendasasprevisto#(lf)WHERE idfarm is not null and tipo ilike '%abate%'"),
    #"Data Corrigida" = Table.TransformColumns(Fonte, {{"date", each
        if _ = null then null else
        let
            partes = Text.Split(Text.From(_), "/"),
            mes    = Number.FromText(Text.Trim(partes{0})),
            ano    = Number.FromText(Text.Trim(partes{1})) + 2000
        in
            #date(ano, mes, 1)
    , type date}})
in
    #"Data Corrigida"
```
### fMetasNascimentos
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT CONCAT(idcustomer,idfarm) as idpropfaz, idcustomer, customer, idfarm, farmname, idretiro, retironame, idowner, ownername, idplherdtype, plherdtypename, idcurrency, currencyname, plversioncode, plversionname, month, date, harvest, anosafra, idcategory, categoryname, idanimalgroup, animalgroupname, age, gender, amount#(lf)#(tab)FROM ""DATABASE"".stg_nascimentosprevisto#(lf)WHERE idfarm is not null"),
    #"Data Corrigida" = Table.TransformColumns(Fonte, {{"date", each
        if _ = null then null else
        let
            partes = Text.Split(Text.From(_), "/"),
            mes    = Number.FromText(Text.Trim(partes{0})),
            ano    = Number.FromText(Text.Trim(partes{1})) + 2000
        in
            #date(ano, mes, 1)
    , type date}})
in
    #"Data Corrigida"
```
### fMetasMortes
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT CONCAT(idcustomer,idfarm) as idpropfaz, idcustomer, customer, idfarm, farmname, idretiro, retironame, idowner, ownername, idplherdtype, plherdtypename, idcurrency, currencyname, plversioncode, plversionname, month, date, harvest, anosafra, idcategory, categoryname, idanimalgroup, animalgroupname, age, gender, amount#(lf)#(tab)FROM ""DATABASE"".stg_mortesprevisto#(lf)WHERE idfarm is not null"),
    #"Data Corrigida" = Table.TransformColumns(Fonte, {{"date", each
        if _ = null then null else
        let
            partes = Text.Split(Text.From(_), "/"),
            mes    = Number.FromText(Text.Trim(partes{0})),
            ano    = Number.FromText(Text.Trim(partes{1})) + 2000
        in
            #date(ano, mes, 1)
    , type date}})
in
    #"Data Corrigida"
```
### fMetasDre
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "WITH mapa (costcenter, custeio_cat, tipo_custeio_cat, desembolso_cat) AS (#(lf)    VALUES#(lf)    (U&'Almoxarifado',                                      '0,0',            '0,0',            '0,0'),#(lf)    (U&'Arrendamento',                                      'Receita outras', 'Receita outras', 'Receita outras'),#(lf)    (U&'Cultura - Receita',                                 'Receita Agr',    'Receita Agr',    'Receita Agr'),#(lf)    (U&'Culturas - Despesa',                                'CCM',            'CV',             'DCM'),#(lf)    (U&'Dividendos',                                        '0,0',            '0,0',            '0,0'),#(lf)    (U&'Empr\00E9stimos s\00F3cios d\00E9bito',             '0,0',            '0,0',            '0,0'),#(lf)    (U&'Financiamentos cr\00E9ditos',                       'Financiamentos', 'Financiamentos', 'Financiamentos'),#(lf)    (U&'Financiamentos d\00E9bitos',                        '0,0',            '0,0',            'DCM'),#(lf)    (U&'Forrageiras e Culturas Anuais',                     'CCM',            'CV',             'DCM'),#(lf)    (U&'Insumos do rebanho',                                'CCM',            'CV',             'DCM'),#(lf)    (U&'Investimentos em RH',                               '0,0',            '0,0',            'DCM'),#(lf)    (U&'Investimentos em infraestrutura',                   'CCM',            'CF',             'DCM'),#(lf)    (U&'Investimentos em outros animais',                   'CCM',            'CF',             'DCM'),#(lf)    (U&'Manuten\00E7\00E3o da fazenda',                     'CCM',            'CF',             'DCM'),#(lf)    (U&'Milheto',                                           '0,0',            '0,0',            '0,0'),#(lf)    (U&'Milho Safrinha',                                    'CCM',            'CV',             'DCM'),#(lf)    (U&'M\00E3o de Obra Geral',                             'CCM',            'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Administra\00E7\00E3o',  'CCM',            'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Cultura',                'CCM',            'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Manuten\00E7\00E3o da Fazenda', 'CCM',     'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Parque de M\00E1quinas', 'CCM',            'CF',             'DCM'),#(lf)    (U&'M\00E3o de Obra Permanente Rebanho',                'CCM',            'CF',             'DCM'),#(lf)    (U&'Outros animais',                                    'CCM',            'CF',             'DCM'),#(lf)    (U&'Pastagens',                                         'CCM',            'CV',             'DCM'),#(lf)    (U&'Rebanho',                                           'Receita Pec',    'Receita Pec',    'Receita Pec'),#(lf)    (U&'Rebanho Investimento',                              'CCM',            'CV',             'DCM'),#(lf)    (U&'Receitas Parque de m\00E1quinas',                   'Receita outras', 'Receita outras', 'Receita outras'),#(lf)    (U&'Receitas financeiras',                              'Financiamentos', 'Financiamentos', 'Financiamentos'),#(lf)    (U&'Receitas outros',                                   'Receita outras', 'Receita outras', 'Receita outras'),#(lf)    (U&'Silagem de Capim',                                  'CCM',            'CV',             'DCM'),#(lf)    (U&'Silagem de Milheto',                                'CCM',            'CV',             'DCM'),#(lf)    (U&'Silagem de Milho',                                  'CCM',            'CV',             'DCM'),#(lf)    (U&'Silagem',                                           'CCM',            'CCM',            'DCM'),#(lf)    (U&'Soja',                                              'CCM',            'CV',             'DCM'),#(lf)    (U&'Sorgo Gr\00E3o',                                    'CCM',            'CV',             'DCM'),#(lf)    (U&'Suporte \00E0 Produ\00E7\00E3o Administra\00E7\00E3o', 'CCM',         'CF',             'DCM'),#(lf)    (U&'Suporte \00E0 Produ\00E7\00E3o Parque de m\00E1quinas', 'CCM',        'CF',             'DCM'),#(lf)    (U&'Taxas e impostos',                                  'CCM',            'CF',             'DCM'),#(lf)    (U&'Vendas outros animais',                             'Receita outras', 'Receita outras', 'Receita outras')#(lf))#(lf)SELECT#(lf)    CONCAT(t.idcustomer, t.idfarm)                AS idpropfaz,#(lf)    t.idcustomer,#(lf)    translate(t.customer, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS customer,#(lf)    t.valorprevisto,#(lf)    t.valorrealizado,#(lf)    translate(t.costcenter, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS costcenter,#(lf)    COALESCE(m.custeio_cat,      'VERIFICAR')     AS custeio_cat,#(lf)    COALESCE(m.tipo_custeio_cat, 'VERIFICAR')     AS tipo_custeio_cat,#(lf)    COALESCE(m.desembolso_cat,   'VERIFICAR')     AS desembolso_cat,#(lf)    t.uuidcostcenter,#(lf)    translate(t.classname, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS classname,#(lf)    t.uuidclass,#(lf)    translate(t.subcenter, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS subcenter,#(lf)    t.uuidsubcenter,#(lf)    translate(t.product, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS product,#(lf)    t.uuidproduct,#(lf)    translate(t.farmname, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS farmname,#(lf)    t.idfarm,#(lf)    translate(t.activity, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS activity,#(lf)    t.uuidactivity,#(lf)    t.""date"",#(lf)    t.""type"",#(lf)    t.classificationanalyticuuid,#(lf)    translate(t.classificationanalyticdescription, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS classificationanalyticdescription#(lf)FROM ""DATABASE"".stg_dreprevisto t#(lf)LEFT JOIN mapa m#(lf)       ON m.costcenter = t.costcenter#(lf)WHERE t.idfarm IS NOT NULL"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"date", type date}})
in
    #"Tipo Alterado"
```
### fMetasRebanhoMedio
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT CONCAT(idcustomer,idfarm) as idpropfaz, idcustomer, customer, idfarm, farmname, idretiro, retironame, owner, anosafra, amount, gender, idcategory, category, month#(lf)#(tab)FROM ""DATABASE"".stg_rebanho_medio#(lf)WHERE idfarm is not null"),
    #"Tipo Alterado" = Table.TransformColumnTypes(Fonte,{{"month", type date}}),
    #"Colunas Renomeadas" = Table.RenameColumns(#"Tipo Alterado",{{"month", "DATA"}})
in
    #"Colunas Renomeadas"
```
### fSaldoGado
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "WITH dCalendarioMensal AS (#(lf)    SELECT#(lf)        (date_trunc('month', gs) + interval '1 month - 1 day')::date AS UltimoDiaMes#(lf)    FROM generate_series(#(lf)        DATE '2010-01-01',#(lf)        CURRENT_DATE,#(lf)        INTERVAL '1 month'#(lf)    ) AS gs#(lf)),#(lf)saldo AS (#(lf)    SELECT#(lf)        t.ORIGEM,#(lf)        t.rn,#(lf)        t.idcustomer,#(lf)        t.customer,#(lf)        t.idfarm,#(lf)        t.farmname,#(lf)        t.idretiro,#(lf)        t.retironame,#(lf)        t.owner,#(lf)        t.harvest,#(lf)        t.birth,#(lf)        t.date,#(lf)        t.mesano,#(lf)        t.gender,#(lf)        t.uuidcategory,#(lf)        t.category,#(lf)        t.amountacc#(lf)    FROM (#(lf)        SELECT * FROM (#(lf)            SELECT#(lf)                'BEZERR CHAVE DIFERENTE' AS ORIGEM,#(lf)                t_1.rn,#(lf)                t_1.idcustomer,#(lf)                t_1.customer,#(lf)                t_1.idfarm,#(lf)                t_1.farmname,#(lf)                t_1.idretiro,#(lf)                t_1.retironame,#(lf)                t_1.owner,#(lf)                t_1.harvest,#(lf)                t_1.birth,#(lf)                t_1.date,#(lf)                t_1.mesano,#(lf)                t_1.gender,#(lf)                t_1.uuidcategory,#(lf)                t_1.category,#(lf)                t_1.amountacc#(lf)            FROM (#(lf)                SELECT#(lf)                    row_number() OVER (PARTITION BY t_2.owner, t_2.farmname, t_2.harvest, t_2.category, t_2.birth, t_2.mesano, t_2.retironame ORDER BY t_2.date DESC) AS rn,#(lf)                    t_2.idcustomer,#(lf)                    t_2.customer,#(lf)                    t_2.idfarm,#(lf)                    t_2.farmname,#(lf)                    t_2.idretiro,#(lf)                    t_2.retironame,#(lf)                    t_2.owner,#(lf)                    t_2.harvest,#(lf)                    t_2.birth,#(lf)                    t_2.date,#(lf)                    t_2.mesano,#(lf)                    t_2.gender,#(lf)                    t_2.uuidcategory,#(lf)                    t_2.category,#(lf)                    t_2.amount,#(lf)                    SUM(amount) OVER (PARTITION BY owner, farmname, retironame, category ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) amountacc#(lf)                FROM (#(lf)                    SELECT#(lf)                        t_3.idcustomer,#(lf)                        t_3.customer,#(lf)                        t_3.idfarm,#(lf)                        t_3.farmname,#(lf)                        t_3.idretiro,#(lf)                        t_3.retironame,#(lf)                        t_3.owner,#(lf)                        t_3.harvest,#(lf)                        t_3.birth,#(lf)                        TO_DATE(t_3.date::TEXT, 'YYYY-MM-DD') AS date,#(lf)                        t_3.mesano,#(lf)                        t_3.gender,#(lf)                        t_3.uuidcategory,#(lf)                        t_3.category,#(lf)                        COUNT(*) OVER (PARTITION BY t_3.owner, t_3.farmname, t_3.retironame, t_3.category, t_3.birth, t_3.harvest) AS validador,#(lf)                        CASE#(lf)                            WHEN t_3.categorygroup ~~ '%Bezerros Mamando%' OR t_3.categorygroup ~~ '%Bezerras Mamando%' THEN#(lf)                                CASE#(lf)                                    WHEN t_3.rn = 1 THEN MAX(t_3.amount) OVER (PARTITION BY t_3.owner, t_3.farmname, t_3.harvest, t_3.birth, t_3.category, t_3.mesano, t_3.retironame ORDER BY t_3.date DESC)#(lf)                                    ELSE 0::DOUBLE PRECISION#(lf)                                END#(lf)                            ELSE 0::DOUBLE PRECISION#(lf)                        END AS amount#(lf)                    FROM (#(lf)                        SELECT#(lf)                            stg_balanco_pecuario.idcustomer,#(lf)                            stg_balanco_pecuario.customer,#(lf)                            stg_balanco_pecuario.idfarm,#(lf)                            stg_balanco_pecuario.farmname,#(lf)                            stg_balanco_pecuario.idretiro,#(lf)                            stg_balanco_pecuario.retironame,#(lf)                            stg_balanco_pecuario.owner,#(lf)                            stg_balanco_pecuario.harvest,#(lf)                            stg_balanco_pecuario.birth,#(lf)                            stg_balanco_pecuario.date,#(lf)                            TO_CHAR(TO_DATE(stg_balanco_pecuario.date::TEXT, 'YYYY-MM-DD')::TIMESTAMP WITH TIME ZONE, 'MM-YYYY') AS mesano,#(lf)                            stg_balanco_pecuario.gender,#(lf)                            stg_category.categorygroup,#(lf)                            stg_balanco_pecuario.uuidcategory,#(lf)                            stg_balanco_pecuario.category,#(lf)                            ROW_NUMBER() OVER (PARTITION BY stg_balanco_pecuario.owner, stg_balanco_pecuario.farmname, stg_balanco_pecuario.retironame, stg_balanco_pecuario.category, stg_balanco_pecuario.birth, stg_balanco_pecuario.harvest, (TO_CHAR(TO_DATE(stg_balanco_pecuario.date::TEXT, 'YYYY-MM-DD')::TIMESTAMP WITH TIME ZONE, 'MM-YYYY')) ORDER BY stg_balanco_pecuario.date DESC) AS rn,#(lf)                            stg_balanco_pecuario.amount#(lf)                        FROM ""DATABASE"".stg_balanco_pecuario#(lf)                        LEFT JOIN ""DATABASE"".stg_category ON stg_category.idcategory::TEXT = stg_balanco_pecuario.uuidcategory::TEXT#(lf)                        WHERE stg_category.categorygroup ~~ '%Bezerros Mamando%' OR stg_category.categorygroup ~~ '%Bezerras Mamando%'#(lf)                    ) t_3#(lf)                    WHERE t_3.rn = 1#(lf)                ) t_2#(lf)                WHERE t_2.validador = 1#(lf)            ) t_1#(lf)            WHERE t_1.rn = 1#(lf)#(lf)            UNION ALL#(lf)#(lf)            SELECT#(lf)                'BEZERR MESMA CHAVE' AS ORIGEM,#(lf)                t_1.rn,#(lf)                t_1.idcustomer,#(lf)                t_1.customer,#(lf)                t_1.idfarm,#(lf)                t_1.farmname,#(lf)                t_1.idretiro,#(lf)                t_1.retironame,#(lf)                t_1.owner,#(lf)                t_1.harvest,#(lf)                t_1.birth,#(lf)                t_1.date,#(lf)                t_1.mesano,#(lf)                t_1.gender,#(lf)                t_1.uuidcategory,#(lf)                t_1.category,#(lf)                t_1.amountacc#(lf)            FROM (#(lf)                SELECT#(lf)                    row_number() OVER (PARTITION BY t_2.owner, t_2.farmname, t_2.harvest, t_2.category, t_2.birth, t_2.mesano, t_2.retironame ORDER BY t_2.date DESC) AS rn,#(lf)                    t_2.idcustomer,#(lf)                    t_2.customer,#(lf)                    t_2.idfarm,#(lf)                    t_2.farmname,#(lf)                    t_2.idretiro,#(lf)                    t_2.retironame,#(lf)                    t_2.owner,#(lf)                    t_2.harvest,#(lf)                    t_2.birth,#(lf)                    t_2.date,#(lf)                    t_2.mesano,#(lf)                    t_2.gender,#(lf)                    t_2.uuidcategory,#(lf)                    t_2.category,#(lf)                    t_2.amount,#(lf)                    CASE#(lf)                        WHEN validador <> 1 THEN MAX(amount) OVER (PARTITION BY owner, farmname, retironame, category, birth, harvest ORDER BY date DESC)#(lf)                        ELSE amount#(lf)                    END AS amountacc#(lf)                FROM (#(lf)                    SELECT#(lf)                        t_3.idcustomer,#(lf)                        t_3.customer,#(lf)                        t_3.idfarm,#(lf)                        t_3.farmname,#(lf)                        t_3.idretiro,#(lf)                        t_3.retironame,#(lf)                        t_3.owner,#(lf)                        t_3.harvest,#(lf)                        t_3.birth,#(lf)                        TO_DATE(t_3.date::TEXT, 'YYYY-MM-DD') AS date,#(lf)                        t_3.mesano,#(lf)                        t_3.gender,#(lf)                        t_3.uuidcategory,#(lf)                        t_3.category,#(lf)                        COUNT(*) OVER (PARTITION BY t_3.owner, t_3.farmname, t_3.retironame, t_3.category, t_3.birth, t_3.harvest) AS validador,#(lf)                        CASE#(lf)                            WHEN t_3.categorygroup ~~ '%Bezerros Mamando%' OR t_3.categorygroup ~~ '%Bezerras Mamando%' THEN#(lf)                                CASE#(lf)                                    WHEN t_3.rn = 1 THEN MAX(t_3.amount) OVER (PARTITION BY t_3.owner, t_3.farmname, t_3.harvest, t_3.birth, t_3.category, t_3.mesano, t_3.retironame ORDER BY t_3.date DESC)#(lf)                                    ELSE 0::DOUBLE PRECISION#(lf)                                END#(lf)                            ELSE 0::DOUBLE PRECISION#(lf)                        END AS amount#(lf)                    FROM (#(lf)                        SELECT#(lf)                            stg_balanco_pecuario.idcustomer,#(lf)                            stg_balanco_pecuario.customer,#(lf)                            stg_balanco_pecuario.idfarm,#(lf)                            stg_balanco_pecuario.farmname,#(lf)                            stg_balanco_pecuario.idretiro,#(lf)                            stg_balanco_pecuario.retironame,#(lf)                            stg_balanco_pecuario.owner,#(lf)                            stg_balanco_pecuario.harvest,#(lf)                            stg_balanco_pecuario.birth,#(lf)                            stg_balanco_pecuario.date,#(lf)                            TO_CHAR(TO_DATE(stg_balanco_pecuario.date::TEXT, 'YYYY-MM-DD')::TIMESTAMP WITH TIME ZONE, 'MM-YYYY') AS mesano,#(lf)                            stg_balanco_pecuario.gender,#(lf)                            stg_category.categorygroup,#(lf)                            stg_balanco_pecuario.uuidcategory,#(lf)                            stg_balanco_pecuario.category,#(lf)                            ROW_NUMBER() OVER (PARTITION BY stg_balanco_pecuario.owner, stg_balanco_pecuario.farmname, stg_balanco_pecuario.retironame, stg_balanco_pecuario.category, stg_balanco_pecuario.birth, stg_balanco_pecuario.harvest, (TO_CHAR(TO_DATE(stg_balanco_pecuario.date::TEXT, 'YYYY-MM-DD')::TIMESTAMP WITH TIME ZONE, 'MM-YYYY')) ORDER BY stg_balanco_pecuario.date DESC) AS rn,#(lf)                            stg_balanco_pecuario.amount#(lf)                        FROM ""DATABASE"".stg_balanco_pecuario#(lf)                        LEFT JOIN ""DATABASE"".stg_category ON stg_category.idcategory::TEXT = stg_balanco_pecuario.uuidcategory::TEXT#(lf)                        WHERE stg_category.categorygroup ~~ '%Bezerros Mamando%' OR stg_category.categorygroup ~~ '%Bezerras Mamando%'#(lf)                    ) t_3#(lf)                    WHERE t_3.rn = 1#(lf)                ) t_2#(lf)                WHERE t_2.validador <> 1#(lf)            ) t_1#(lf)            WHERE t_1.rn = 1#(lf)        ) T#(lf)#(lf)        UNION ALL#(lf)#(lf)        SELECT#(lf)            'OUTRAS CAT' AS ORIGEM,#(lf)            t_1.rn,#(lf)            t_1.idcustomer,#(lf)            t_1.customer,#(lf)            t_1.idfarm,#(lf)            t_1.farmname,#(lf)            t_1.idretiro,#(lf)            t_1.retironame,#(lf)            t_1.owner,#(lf)            t_1.anosafra,#(lf)            t_1.birth,#(lf)            t_1.date,#(lf)            t_1.mesano,#(lf)            t_1.gender,#(lf)            t_1.uuidcategory,#(lf)            t_1.category,#(lf)            t_1.amount#(lf)        FROM (#(lf)            SELECT#(lf)                row_number() OVER (PARTITION BY t_2.owner, t_2.farmname, t_2.anosafra, t_2.category, t_2.mesano, t_2.retironame ORDER BY t_2.date DESC) AS rn,#(lf)                t_2.idcustomer,#(lf)                t_2.customer,#(lf)                t_2.idfarm,#(lf)                t_2.farmname,#(lf)                t_2.idretiro,#(lf)                t_2.retironame,#(lf)                t_2.owner,#(lf)                t_2.anosafra,#(lf)                t_2.birth,#(lf)                t_2.date,#(lf)                t_2.mesano,#(lf)                t_2.gender,#(lf)                t_2.uuidcategory,#(lf)                t_2.category,#(lf)                t_2.amount#(lf)            FROM (#(lf)                SELECT#(lf)                    t_3.idcustomer,#(lf)                    t_3.customer,#(lf)                    t_3.idfarm,#(lf)                    t_3.farmname,#(lf)                    t_3.idretiro,#(lf)                    t_3.retironame,#(lf)                    t_3.owner,#(lf)                    t_3.anosafra,#(lf)                    t_3.birth,#(lf)                    TO_DATE(t_3.date::TEXT, 'YYYY-MM-DD') AS date,#(lf)                    t_3.mesano,#(lf)                    t_3.gender,#(lf)                    t_3.uuidcategory,#(lf)                    t_3.category,#(lf)                    MAX(t_3.amount) OVER (PARTITION BY t_3.owner, t_3.farmname, t_3.anosafra, t_3.category, t_3.mesano, t_3.retironame ORDER BY t_3.date DESC) AS amount#(lf)                FROM (#(lf)                    SELECT#(lf)                        stg_balanco_pecuario.idcustomer,#(lf)                        stg_balanco_pecuario.customer,#(lf)                        stg_balanco_pecuario.idfarm,#(lf)                        stg_balanco_pecuario.farmname,#(lf)                        stg_balanco_pecuario.idretiro,#(lf)                        stg_balanco_pecuario.retironame,#(lf)                        stg_balanco_pecuario.owner,#(lf)                        stg_balanco_pecuario.anosafra,#(lf)                        stg_balanco_pecuario.birth,#(lf)                        stg_balanco_pecuario.date,#(lf)                        TO_CHAR(TO_DATE(stg_balanco_pecuario.date::TEXT, 'YYYY-MM-DD')::TIMESTAMP WITH TIME ZONE, 'MM-YYYY') AS mesano,#(lf)                        stg_balanco_pecuario.gender,#(lf)                        stg_category.categorygroup,#(lf)                        stg_balanco_pecuario.uuidcategory,#(lf)                        stg_balanco_pecuario.category,#(lf)                        stg_balanco_pecuario.amount#(lf)                    FROM ""DATABASE"".stg_balanco_pecuario#(lf)                    LEFT JOIN ""DATABASE"".stg_category ON stg_category.idcategory::TEXT = stg_balanco_pecuario.uuidcategory::TEXT#(lf)                    WHERE stg_category.categorygroup !~~ '%Bezerros Mamando%' AND stg_category.categorygroup !~~ '%Bezerras Mamando%'#(lf)                ) t_3#(lf)            ) t_2#(lf)        ) t_1#(lf)        WHERE t_1.rn = 1#(lf)    ) t#(lf)    ORDER BY owner, farmname, retironame, category, birth, harvest, date#(lf)),#(lf)saldo_por_mes AS (#(lf)    SELECT DISTINCT ON (#(lf)        cal.UltimoDiaMes,#(lf)        s.owner,#(lf)        s.farmname,#(lf)        s.retironame,#(lf)        s.category#(lf)    )#(lf)        cal.UltimoDiaMes,#(lf)        s.owner,#(lf)        s.farmname,#(lf)        s.retironame,#(lf)        s.category,#(lf)        CONCAT(s.idcustomer, s.idfarm) AS idpropfaz,  -- ← NOVO#(lf)        s.amountacc,#(lf)        s.date AS data_saldo#(lf)    FROM dCalendarioMensal cal#(lf)    JOIN saldo s ON s.date <= cal.UltimoDiaMes#(lf)    WHERE s.ORIGEM = 'OUTRAS CAT'#(lf)    ORDER BY cal.UltimoDiaMes, s.owner, s.farmname, s.retironame, s.category, s.date DESC#(lf)),#(lf)saldo_por_mes2 AS (#(lf)    SELECT DISTINCT ON (#(lf)        cal.UltimoDiaMes,#(lf)        s.owner,#(lf)        s.farmname,#(lf)        s.retironame,#(lf)        s.category,#(lf)        s.birth,#(lf)        s.harvest#(lf)    )#(lf)        cal.UltimoDiaMes,#(lf)        s.owner,#(lf)        s.farmname,#(lf)        s.retironame,#(lf)        s.category,#(lf)        s.birth,#(lf)        s.harvest,#(lf)        CONCAT(s.idcustomer, s.idfarm) AS idpropfaz,  -- ← NOVO#(lf)        s.amountacc,#(lf)        s.date AS data_saldo#(lf)    FROM dCalendarioMensal cal#(lf)    JOIN saldo s ON s.date <= cal.UltimoDiaMes#(lf)    WHERE s.ORIGEM = 'BEZERR MESMA CHAVE'#(lf)    ORDER BY cal.UltimoDiaMes, s.owner, s.farmname, s.retironame, s.category, s.birth, s.harvest, s.date DESC#(lf)),#(lf)saldo_por_mes3 AS (#(lf)    SELECT DISTINCT ON (#(lf)        cal.UltimoDiaMes,#(lf)        s.owner,#(lf)        s.farmname,#(lf)        s.retironame,#(lf)        s.category#(lf)    )#(lf)        cal.UltimoDiaMes,#(lf)        s.owner,#(lf)        s.farmname,#(lf)        s.retironame,#(lf)        s.category,#(lf)        s.birth,#(lf)        s.harvest,#(lf)        CONCAT(s.idcustomer, s.idfarm) AS idpropfaz,  -- ← NOVO#(lf)        s.amountacc,#(lf)        s.date AS data_saldo#(lf)    FROM dCalendarioMensal cal#(lf)    JOIN saldo s ON s.date <= cal.UltimoDiaMes#(lf)    WHERE s.ORIGEM = 'BEZERR CHAVE DIFERENTE'#(lf)    ORDER BY cal.UltimoDiaMes, s.owner, s.farmname, s.retironame, s.category, s.date DESC#(lf)),#(lf)saldo_por_mes4 AS (#(lf)    SELECT DISTINCT ON (#(lf)        cal.UltimoDiaMes,#(lf)        s.owner,#(lf)        s.farmname,#(lf)        s.retironame,#(lf)        s.category#(lf)    )#(lf)        cal.UltimoDiaMes,#(lf)        s.owner,#(lf)        s.farmname,#(lf)        s.retironame,#(lf)        s.category,#(lf)        NULL AS birth,#(lf)        NULL AS harvest,#(lf)        CONCAT(s.idcustomer, s.idfarm) AS idpropfaz,  -- ← NOVO#(lf)        s.amountacc,#(lf)        s.date AS data_saldo#(lf)    FROM dCalendarioMensal cal#(lf)    JOIN saldo s ON s.date <= cal.UltimoDiaMes#(lf)    WHERE s.ORIGEM = 'OUTRAS CAT'#(lf)    ORDER BY cal.UltimoDiaMes, s.owner, s.farmname, s.retironame, s.category, birth, harvest, data_saldo DESC#(lf))#(lf)#(lf)SELECT * FROM saldo_por_mes4#(lf)UNION#(lf)SELECT * FROM saldo_por_mes3#(lf)UNION#(lf)SELECT * FROM saldo_por_mes2#(lf)ORDER BY owner, farmname, retironame, category, UltimoDiaMes;"),
    #"Colunas Renomeadas" = Table.RenameColumns(Fonte,{{"ultimodiames", "date"}})
in
    #"Colunas Renomeadas"
```
### fMetasEmPe
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "SELECT CONCAT(idcustomer,idfarm) as idpropfaz, idcustomer, customer, idfarm, farmname, idretiro, retironame, idowner, ownername, idplherdtype, plherdtypename, idcurrency, currencyname, month, date, harvest, anosafra, idcategory, categoryname, idanimalgroup, animalgroupname, age, gender, amount, weight, arrobavalue, arrobaweight, value, totalvalue,yield,tipo#(lf)#(tab)FROM ""DATABASE"".stg_vendasasprevisto#(lf)WHERE idfarm is not null and tipo ilike '%em%'"),
    #"Data Corrigida" = Table.TransformColumns(Fonte, {{"date", each
        if _ = null then null else
        let
            partes = Text.Split(Text.From(_), "/"),
            mes    = Number.FromText(Text.Trim(partes{0})),
            ano    = Number.FromText(Text.Trim(partes{1})) + 2000
        in
            #date(ano, mes, 1)
    , type date}})
in
    #"Data Corrigida"
```
### fPlanejadoxRealizado
```m
let
    Fonte = Odbc.Query("dsn=DATALAKE_METRYX", "/*#(lf) * DRE ERP - Previsto x Realizado#(lf) *#(lf) * Fontes:#(lf) *   ""DATABASE"".stg_dre          -> realizado (amountpaid, datepayment, costcenter, idcustomer, idfarmdestination)#(lf) *   ""DATABASE"".stg_dreprevisto  -> previsto  (valorprevisto, date, costcenter, idcustomer, idfarm)#(lf) *#(lf) * Chave: idpropfaz = CONCAT(idcustomer, idfarm)   (equivale ao PROP_FAZ da planilha)#(lf) *   stg_dre:         CONCAT(idcustomer, idfarmdestination)#(lf) *   stg_dreprevisto: CONCAT(idcustomer, idfarm)#(lf) *#(lf) * Acentos escritos como U&'...\00E9...' (Unicode escape); translate() remove#(lf) * caracteres invisiveis (U+200B, U+200C, U+200D, U+FEFF) dos textos.#(lf) *#(lf) * FILTRO TEMPORARIO: lancamentos com valor absoluto >= 1 bilhao sao ignorados no#(lf) * CTE realizado (erro de escala na origem, ex.: Receitas financeiras ~5e16).#(lf) * Remover quando a origem for corrigida.#(lf) */#(lf)#(lf)WITH#(lf)#(lf)-- prop: lista mestre de fazendas com idpropfaz como chave#(lf)prop AS (#(lf)    SELECT DISTINCT#(lf)        CONCAT(idcustomer, idfarmdestination) AS idpropfaz,#(lf)        idcustomer,#(lf)        idfarmdestination                     AS idfarm,#(lf)        translate(owner,           chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS proprietario,#(lf)        translate(farmdestination, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS fazenda#(lf)    FROM ""DATABASE"".stg_dre#(lf)    WHERE idcustomer      IS NOT NULL#(lf)      AND farmdestination IS NOT NULL#(lf)#(lf)    UNION#(lf)#(lf)    SELECT DISTINCT#(lf)        CONCAT(idcustomer, idfarm) AS idpropfaz,#(lf)        idcustomer,#(lf)        idfarm,#(lf)        translate(customer, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS proprietario,#(lf)        translate(farmname, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS fazenda#(lf)    FROM ""DATABASE"".stg_dreprevisto#(lf)    WHERE idcustomer IS NOT NULL#(lf)      AND farmname   IS NOT NULL#(lf)),#(lf)#(lf)-- c_custo: todos os centros de custo (ambas as fontes) x todas as fazendas#(lf)c_custo AS (#(lf)    SELECT DISTINCT#(lf)        cc.costcenter,#(lf)        p.idpropfaz,#(lf)        p.idcustomer,#(lf)        p.idfarm,#(lf)        p.proprietario,#(lf)        p.fazenda#(lf)    FROM (#(lf)        SELECT DISTINCT translate(costcenter, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS costcenter#(lf)        FROM ""DATABASE"".stg_dre#(lf)        WHERE costcenter IS NOT NULL#(lf)        UNION#(lf)        SELECT DISTINCT translate(costcenter, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS costcenter#(lf)        FROM ""DATABASE"".stg_dreprevisto#(lf)        WHERE costcenter IS NOT NULL#(lf)    ) cc#(lf)    CROSS JOIN prop p#(lf)),#(lf)#(lf)-- datas: lista de meses distintos (ambas as fontes)#(lf)datas AS (#(lf)    SELECT DISTINCT#(lf)        DATE_TRUNC('month', datepayment::DATE)::DATE AS primeiro_dia_do_mes#(lf)    FROM ""DATABASE"".stg_dre#(lf)    WHERE datepayment IS NOT NULL#(lf)#(lf)    UNION#(lf)#(lf)    SELECT DISTINCT#(lf)        DATE_TRUNC('month', date::DATE)::DATE AS primeiro_dia_do_mes#(lf)    FROM ""DATABASE"".stg_dreprevisto#(lf)    WHERE date IS NOT NULL#(lf)),#(lf)#(lf)-- base: grade completa fazenda x centro de custo x mes#(lf)base AS (#(lf)    SELECT#(lf)        c.idpropfaz,#(lf)        c.idcustomer,#(lf)        c.idfarm,#(lf)        c.proprietario,#(lf)        c.fazenda,#(lf)        c.costcenter,#(lf)        d.primeiro_dia_do_mes#(lf)    FROM c_custo c#(lf)    CROSS JOIN datas d#(lf)    WHERE d.primeiro_dia_do_mes IS NOT NULL#(lf)),#(lf)#(lf)-- previsto: orcado agregado por idpropfaz + centro de custo + mes (stg_dreprevisto)#(lf)previsto AS (#(lf)    SELECT#(lf)        CONCAT(idcustomer, idfarm)            AS idpropfaz,#(lf)        DATE_TRUNC('month', date::DATE)::DATE AS data_mes,#(lf)        translate(costcenter, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS costcenter,#(lf)        SUM(valorprevisto)                    AS meta#(lf)    FROM ""DATABASE"".stg_dreprevisto#(lf)    WHERE date IS NOT NULL#(lf)    GROUP BY 1, 2, 3#(lf)),#(lf)#(lf)-- realizado: pago agregado por idpropfaz + centro de custo + mes (stg_dre, amountpaid)#(lf)realizado AS (#(lf)    SELECT#(lf)        CONCAT(idcustomer, idfarmdestination)        AS idpropfaz,#(lf)        DATE_TRUNC('month', datepayment::DATE)::DATE AS data_mes,#(lf)        translate(costcenter, chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS costcenter,#(lf)        translate(type,       chr(8203) || chr(8204) || chr(8205) || chr(65279), '') AS operacao,#(lf)        SUM(amountpaid::NUMERIC)                     AS valor#(lf)    FROM ""DATABASE"".stg_dre#(lf)    WHERE datepayment IS NOT NULL#(lf)      AND (amountpaid IS NULL OR ABS(amountpaid::NUMERIC) < 1000000000)  -- TEMPORARIO: ignora valores absurdos da origem#(lf)    GROUP BY 1, 2, 3, 4#(lf)),#(lf)#(lf)-- dados: join base x previsto x realizado + classificacao DRE#(lf)dados AS (#(lf)    SELECT#(lf)        b.idpropfaz,#(lf)        b.idcustomer,#(lf)        b.idfarm,#(lf)        b.proprietario,#(lf)        b.fazenda,#(lf)        b.costcenter,#(lf)        CASE#(lf)            WHEN b.costcenter IN (#(lf)                U&'Arrendamento',#(lf)                U&'Cultura - Receita',#(lf)                U&'Rebanho',#(lf)                U&'Receitas financeiras',#(lf)                U&'Receitas outros',#(lf)                U&'Receitas Parque de m\00E1quinas',#(lf)                U&'Vendas outros animais'#(lf)            ) THEN 'A - RECEITAS'#(lf)#(lf)            WHEN b.costcenter IN (#(lf)                U&'Investimentos em infraestrutura',#(lf)                U&'Investimentos em outros animais',#(lf)                U&'Investimentos em RH',#(lf)                U&'Rebanho Investimento'#(lf)            ) THEN 'C - INVESTIMENTOS'#(lf)#(lf)            WHEN b.costcenter IN (#(lf)                U&'Algod\00E3o',#(lf)                U&'Aveia',#(lf)                U&'Feno',#(lf)                U&'Forrageiras e Culturas Anuais',#(lf)                U&'Insumos do rebanho',#(lf)                U&'Manuten\00E7\00E3o da fazenda',#(lf)                U&'M\00E3o de Obra Geral',#(lf)                U&'M\00E3o de Obra Permanente Administra\00E7\00E3o',#(lf)                U&'M\00E3o de Obra Permanente Cultura',#(lf)                U&'M\00E3o de Obra Permanente Manuten\00E7\00E3o da Fazenda',#(lf)                U&'M\00E3o de Obra Permanente Parque de M\00E1quinas',#(lf)                U&'M\00E3o de Obra Permanente Rebanho',#(lf)                U&'Milho Safrinha',#(lf)                U&'Milho Ver\00E3o',#(lf)                U&'Outros animais',#(lf)                U&'Pastagens',#(lf)                U&'Silagem de Capia\00E7u',#(lf)                U&'Silagem de Capim',#(lf)                U&'Silagem de Milheto',#(lf)                U&'Silagem de Milho',#(lf)                U&'Silagem de Sorgo',#(lf)                U&'Soja',#(lf)                U&'Sorgo Gr\00E3o',#(lf)                U&'Suporte \00E0 Produ\00E7\00E3o Administra\00E7\00E3o',#(lf)                U&'Suporte \00E0 Produ\00E7\00E3o Parque de m\00E1quinas',#(lf)                U&'Taxas e impostos'#(lf)            ) THEN 'D - CUSTEIO'#(lf)#(lf)            WHEN b.costcenter IN (#(lf)                U&'Empr\00E9stimos s\00F3cios cr\00E9dito',#(lf)                U&'Financiamentos cr\00E9ditos'#(lf)            ) THEN U&'E - OUTROS CR\00C9DITOS'#(lf)#(lf)            WHEN b.costcenter IN (#(lf)                U&'Dividendos',#(lf)                U&'Empr\00E9stimos s\00F3cios d\00E9bito',#(lf)                U&'Financiamentos d\00E9bitos',#(lf)                U&'Outros D\00E9bitos'#(lf)            ) THEN U&'F - OUTROS D\00C9BITOS'#(lf)#(lf)            WHEN b.costcenter IN (#(lf)                U&'Almoxarifado',#(lf)                U&'Aporte de capital',#(lf)                U&'Preju\00EDzo Administra\00E7\00E3o',#(lf)                U&'Venda de Im\00F3veis'#(lf)            ) THEN ''#(lf)#(lf)            ELSE NULL#(lf)        END AS classificacao,#(lf)#(lf)        b.primeiro_dia_do_mes                    AS data,#(lf)        ABS(p.meta)                              AS meta,#(lf)        ABS(ROUND(SUM(r.valor), 2))              AS realizado#(lf)#(lf)    FROM base b#(lf)#(lf)    LEFT JOIN previsto p#(lf)        ON  p.idpropfaz  = b.idpropfaz#(lf)        AND p.costcenter = b.costcenter#(lf)        AND p.data_mes   = b.primeiro_dia_do_mes#(lf)#(lf)    LEFT JOIN realizado r#(lf)        ON  r.idpropfaz  = b.idpropfaz#(lf)        AND r.costcenter = b.costcenter#(lf)        AND r.data_mes   = b.primeiro_dia_do_mes#(lf)#(lf)    WHERE p.meta IS NOT NULL#(lf)       OR r.valor IS NOT NULL#(lf)#(lf)    GROUP BY#(lf)        b.idpropfaz,#(lf)        b.idcustomer,#(lf)        b.idfarm,#(lf)        b.proprietario,#(lf)        b.fazenda,#(lf)        b.costcenter,#(lf)        b.primeiro_dia_do_mes,#(lf)        p.meta#(lf))#(lf)#(lf)-- Resultado final: centros de custo individuais + linha sintetica DESEMBOLSO#(lf)-- (= soma de C - INVESTIMENTOS e D - CUSTEIO)#(lf)SELECT#(lf)    t.idpropfaz,#(lf)    t.idcustomer,#(lf)    t.idfarm,#(lf)    t.proprietario,#(lf)    t.fazenda,#(lf)    t.costcenter,#(lf)    t.classificacao,#(lf)    t.data,#(lf)    SUM(t.meta) AS meta,#(lf)    t.realizado#(lf)FROM (#(lf)#(lf)    -- Centros de custo individuais#(lf)    SELECT * FROM dados#(lf)#(lf)    UNION ALL#(lf)#(lf)    -- Linha sintetica: DESEMBOLSO (Investimentos + Custeio)#(lf)    SELECT#(lf)        t1.idpropfaz,#(lf)        t1.idcustomer,#(lf)        t1.idfarm,#(lf)        t1.proprietario,#(lf)        t1.fazenda,#(lf)        'DESEMBOLSO'                          AS costcenter,#(lf)        'B - DESEMBOLSO'                      AS classificacao,#(lf)        t1.data,#(lf)        t1.meta,#(lf)        ABS(ROUND(t1.realizado::NUMERIC, 2))  AS realizado#(lf)    FROM dados t1#(lf)    WHERE t1.classificacao IN ('C - INVESTIMENTOS', 'D - CUSTEIO')#(lf)#(lf)) t#(lf)#(lf)GROUP BY#(lf)    t.idpropfaz,#(lf)    t.idcustomer,#(lf)    t.idfarm,#(lf)    t.proprietario,#(lf)    t.fazenda,#(lf)    t.costcenter,#(lf)    t.classificacao,#(lf)    t.data,#(lf)    t.realizado#(lf)#(lf)ORDER BY#(lf)    t.proprietario,#(lf)    t.fazenda,#(lf)    t.data,#(lf)    t.classificacao,#(lf)    t.costcenter")
in
    Fonte
```