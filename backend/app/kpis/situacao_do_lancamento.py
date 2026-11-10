"""A situação dos títulos que entram no realizado do financeiro (pedido do usuário, 10/11/2026).

O MENU e as páginas do financeiro (Previsto × Realizado e Financeiro) filtram os lançamentos pela situação do título:
conciliado (pago e conciliado no banco), pago (sem a conciliação) ou em aberto (sem pagamento; entra no mês do
vencimento). Sem escolha, vale o que foi pago, conciliado ou não, como o relatório do Metryx e o BI de planilhas. A
planilha só traz o que foi pago. Toda consulta do realizado do financeiro lê os lançamentos por
`LANCAMENTOS_DO_FILTRO`, e não direto da view.
"""

SITUACOES = ("conciliado", "pago", "em_aberto")
SITUACOES_PADRAO = ("conciliado", "pago")

# os lançamentos das situações do recorte, com a classificação da conta já resolvida (pode entrar num FROM)
LANCAMENTOS_DO_FILTRO = """(
    SELECT * FROM fato.v_lancamento_financeiro WHERE situacao = ANY (CAST(:situacoes AS text[]))
)"""
