"""Aba Diagnóstico: folga × pontualidade por estado e quanto o atraso custa na avaliação."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horas_app.comum import (AZUL, CINZA_CLARO, L, VERMELHO, caixa, como_ler, em_uma_frase, kpi, layout, num, pct,
                             resultados)

FAIXAS_EN = {
    "8+ dias atrasado": "8+ days late", "4 a 7 atrasado": "4–7 days late", "1 a 3 atrasado": "1–3 days late",
    "no dia": "on the day", "1 a 3 antes": "1–3 days early", "4 a 7 antes": "4–7 days early",
    "8 a 14 antes": "8–14 days early", "15 a 21 antes": "15–21 days early", "22+ antes": "22+ days early",
}


def render():
    R = resultados()
    r = R["resumo"]

    em_uma_frase(
        "na média sobra folga, mas em alguns estados o pedido atrasa muito. E atrasar custa caro na avaliação do cliente.",
        "on average there's spare slack, but in some states orders run very late. And being late is expensive in customer reviews.",
    )

    c = st.columns(4)
    kpi(c[0], pct(r["no_prazo"]), L("dos pedidos chegam no prazo", "of orders arrive on time"))
    kpi(c[1], num(r["prometido"]) + L(" dias", " days"), L("é a promessa típica (mediana)", "is the typical promise (median)"))
    kpi(c[2], num(r["real"]) + L(" dias", " days"), L("é o prazo real típico (mediana)", "is the typical actual lead time (median)"))
    kpi(c[3], num(r["p95"]) + L(" dias", " days"), L("cobrem 95% das entregas", "cover 95% of deliveries"))
    st.caption(L(
        "Pedidos que não chegaram até o fim da base contam como atrasados, porque todos já tinham passado do prazo. "
        "Cancelados ficam de fora.",
        "Orders not delivered by the end of the data count as late, because all of them were already past due. "
        "Cancelled orders are left out.",
    ))

    # ----------------------------------------------------------------- folga x pontualidade
    st.markdown("#### " + L("1. A mesma folga rende pontualidades bem diferentes", "1. The same slack yields very different on-time rates"))
    st.markdown(L(
        "**Folga** é quantos dias antes do prometido o pedido chegou. Se prometeu 20 e chegou em 8, a folga foi de 12 dias. "
        "No pedido típico, sobra bastante folga. O problema está nos pedidos que demoram muito mais que o normal, e isso "
        "muda de estado pra estado.",
        "**Slack** is how many days before the promised date the order arrived. Promised 20 and arrived in 8 means 12 days "
        "of slack. On the typical order there's plenty of slack. The problem is the orders that take far longer than usual, "
        "and that varies by state.",
    ))
    uf = pd.DataFrame(R["por_uf"])
    cores = [VERMELHO if v < 0.88 else AZUL for v in uf.no_prazo]
    # Estados no mesmo ponto: o menor ganha o rótulo do lado de fora, pra não sobrepor
    posicoes, vistos = [], []
    for linha in uf.sort_values("pedidos", ascending=False).itertuples():
        perto = any(abs(linha.folga_mediana - x) < 0.4 and abs(linha.no_prazo - y) < 0.012 for x, y in vistos)
        posicoes.append((linha.Index, "middle right" if perto else "middle center"))
        vistos.append((linha.folga_mediana, linha.no_prazo))
    posicao = pd.Series(dict(posicoes)).reindex(uf.index)
    texto = [f"   {t}" if p_ == "middle right" else t for t, p_ in zip(uf.customer_state, posicao)]
    fig = go.Figure(go.Scatter(
        x=uf.folga_mediana, y=uf.no_prazo, mode="markers+text", text=texto,
        textposition=list(posicao), textfont=dict(size=11, color="#10233a"),
        marker=dict(size=uf.pedidos, sizemode="area", sizeref=2 * uf.pedidos.max() / 60 ** 2, sizemin=10,
                    color=cores, opacity=0.28, line=dict(color=cores, width=1.5)),
        customdata=uf[["pedidos", "prometido_mediana", "real_mediana", "customer_state"]],
        hovertemplate="%{customdata[3]}<br>" + L("no prazo", "on time") + ": %{y:.1%}<br>" + L("folga típica", "typical slack") +
                      ": %{x} " + L("dias", "days") + "<br>" + L("pedidos", "orders") + ": %{customdata[0]:,}<extra></extra>",
    ))
    layout(fig, 460, xaxis_title=L("folga do pedido típico (dias)", "typical order's slack (days)"),
           yaxis_title=L("% no prazo", "% on time"), yaxis_tickformat=".0%", showlegend=False)
    st.plotly_chart(fig, width="stretch")
    como_ler(
        "cada bolha é um estado do cliente, e o tamanho é o volume de pedidos. Quanto mais pra cima, mais pedidos chegam no "
        "prazo. Em vermelho, estados com menos de 88% no prazo. Repare que **RJ e SC têm a mesma folga típica (13 dias)**, "
        "mas o RJ atrasa bem mais.",
        "each bubble is a customer state, sized by order volume. Higher means more orders on time. In red, states below 88% "
        "on time. Notice **RJ and SC have the same typical slack (13 days)**, but RJ runs late far more often.",
    )
    with st.expander(L("Ver a tabela por UF", "See the table by state")):
        t = uf.rename(columns={"customer_state": "UF", "pedidos": L("pedidos", "orders"), "no_prazo": L("no prazo", "on time"),
                               "folga_mediana": L("folga típica", "typical slack"),
                               "prometido_mediana": L("promessa típica", "typical promise"),
                               "real_mediana": L("prazo real típico", "typical actual lead time")})
        st.dataframe(t, hide_index=True, width="stretch",
                     column_config={L("no prazo", "on time"): st.column_config.NumberColumn(format="percent")})

    # ----------------------------------------------------------------- avaliação
    st.markdown("#### " + L("2. Atraso derruba a avaliação. Folga a mais não sobe.", "2. Delays sink reviews. Extra slack doesn't lift them."))
    caixa(L(
        "**O que é a avaliação aqui:** não é NPS. Depois da entrega, a Olist pede pro cliente dar uma nota de **1 a 5 "
        "estrelas** pro pedido. 99% dos pedidos entregues têm essa avaliação. Notas 1 e 2 são, na prática, as reclamações.",
        "**What the review is here:** it's not NPS. After delivery, Olist asks the customer to rate the order from **1 to 5 "
        "stars**. 99% of delivered orders have this review. 1 and 2 stars are, in practice, the complaints.",
    ), "ambar")
    st.markdown(L(
        "Separei os pedidos por quantos dias chegaram antes ou depois do prometido e calculei, em cada grupo, quantos "
        "receberam 1 ou 2 estrelas.",
        "I grouped orders by how many days early or late they arrived and calculated, in each group, how many got 1 or 2 stars.",
    ))
    n = pd.DataFrame(R["notas"])
    n["rotulo"] = n.faixa if L("pt", "en") == "pt" else n.faixa.map(FAIXAS_EN)
    fig = go.Figure(go.Bar(
        x=n.rotulo, y=n.pct_nota_1_2, marker_color=[VERMELHO if "atrasado" in f else AZUL for f in n.faixa],
        text=[pct(v, 0) for v in n.pct_nota_1_2], textposition="outside",
        error_y=dict(type="data", symmetric=False, array=n.ic_sup - n.pct_nota_1_2, arrayminus=n.pct_nota_1_2 - n.ic_inf,
                     color="#5b6776", thickness=1.2),
        customdata=n[["pedidos", "nota_media"]],
        hovertemplate="%{x}<br>" + L("avaliações de 1 e 2 estrelas", "1–2 star reviews") + ": %{y:.1%}<br>" +
                      L("média de estrelas", "average stars") + ": %{customdata[1]:.2f}<br>" + L("pedidos", "orders") +
                      ": %{customdata[0]:,}<extra></extra>",
    ))
    layout(fig, 430, yaxis_tickformat=".0%", yaxis_title=L("% de avaliações com 1 ou 2 estrelas", "% of 1–2 star reviews"),
           showlegend=False, yaxis=dict(range=[0, 0.9]))
    fig.update_yaxes(gridcolor=CINZA_CLARO)
    st.plotly_chart(fig, width="stretch")
    como_ler(
        "da esquerda pra direita, do pedido mais atrasado pro que chegou mais cedo. Em vermelho, os atrasados. **Com 8 dias "
        "ou mais de atraso, 79% das avaliações são de 1 ou 2 estrelas.** Quando o pedido chega antes, fica entre 8% e 11%, "
        "tanto faz chegar 4 ou 22 dias antes. A barrinha preta é a margem de erro (intervalo de confiança de Wilson).",
        "from left to right, from the latest order to the earliest. Red bars are late orders. **With 8+ days of delay, 79% "
        "of reviews are 1 or 2 stars.** When the order arrives early it stays between 8% and 11%, whether 4 or 22 days early. "
        "The black whisker is the margin of error (Wilson confidence interval).",
    )
    caixa(L(
        "**O que isso quer dizer pra promessa:** onde sobra folga, dá pra prometer menos sem perder avaliação, porque "
        "chegar muito cedo não rende estrela a mais. Onde atrasa, vale prometer mais, porque cada atraso custa caro.",
        "**What this means for the promise:** where there's spare slack, you can promise less without losing reviews, "
        "because arriving very early earns no extra stars. Where orders run late, it's worth promising more, because each "
        "delay is expensive.",
    ), "verde")
