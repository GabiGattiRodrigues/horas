"""Monitoramento: gráfico de controle semanal do % no prazo."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horas_app.comum import em_uma_frase, como_ler, caixa, AZUL, AZUL_FUNDO, CINZA, L, LINKS, VERMELHO, layout, num, pct, resultados


def render():
    em_uma_frase(
        "nenhum modelo prevê um choque. Por isso a promessa precisa de um alarme semanal que diga quando a pontualidade saiu do normal.",
        "no model predicts a shock. That is why the promise needs a weekly alarm saying when on-time performance left its normal range.",
    )
    R = resultados()

    st.markdown(L(
        """**A ideia do gráfico de controle:** toda semana o % no prazo sobe e desce um pouco, só por acaso. A faixa azul
mostra **até onde esse sobe e desce é normal**, dado o número de pedidos da semana. Se o ponto cai abaixo da faixa,
não é mais acaso: alguma coisa mudou de verdade (Black Friday, greve, transportadora com problema).""",
        """**The idea of a control chart:** every week the on-time rate goes up and down a little, by chance alone. The blue
band shows **how far that up-and-down is normal**, given the week's number of orders. If the point falls below the band,
it's no longer chance: something really changed (Black Friday, a strike, a carrier in trouble).""",
    ))

    s = pd.DataFrame(R["semanas"])
    s["dia_compra"] = pd.to_datetime(s.dia_compra)
    fora = s[s.fora]

    fig = go.Figure()
    fig.add_scatter(x=s.dia_compra, y=s.lsc, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=s.dia_compra, y=s.lic, mode="lines", line=dict(width=0), fill="tonexty", fillcolor=AZUL_FUNDO,
                    name=L("faixa normal (3σ)", "normal band (3σ)"), hoverinfo="skip")
    fig.add_hline(y=R["p_barra"], line_dash="dot", line_color=CINZA)
    fig.add_scatter(x=s.dia_compra, y=s.taxa, mode="lines+markers", line=dict(color=AZUL, width=2), marker=dict(size=4),
                    name=L("% no prazo", "% on time"), customdata=s.pedidos,
                    hovertemplate=L("semana de", "week of") + " %{x|%d/%m/%Y}<br>%{y:.1%}<br>" + L("pedidos", "orders") +
                                  ": %{customdata:,}<extra></extra>")
    fig.add_scatter(x=fora.dia_compra, y=fora.taxa, mode="markers", marker=dict(color=VERMELHO, size=11),
                    name=L("fora de controle", "out of control"), hoverinfo="skip")
    layout(fig, 460, yaxis_tickformat=".0%", yaxis_title=L("% no prazo", "% on time"))
    st.plotly_chart(fig, width="stretch")
    como_ler(
        f"cada ponto é uma semana de compras. A linha pontilhada é a média ({pct(R['p_barra'])} no prazo). **Ponto azul "
        "dentro da faixa é semana normal. Ponto vermelho, abaixo da faixa, é semana fora de controle.**",
        f"each point is a week of purchases. The dotted line is the average ({pct(R['p_barra'])} on time). **A blue point "
        "inside the band is a normal week. A red point, below the band, is an out-of-control week.**",
    )

    st.markdown("#### " + L(f"{len(fora)} semanas fora de controle", f"{len(fora)} weeks out of control"))
    st.markdown(L(
        "A maioria está na Black Friday de 2017 e entre fevereiro e março de 2018. A semana de 14 de maio de 2018 "
        "provavelmente pegou a greve dos caminhoneiros com o pedido ainda em trânsito. Quando uma semana sai do limite, a "
        "promessa daquele período tem que ser revista, sem esperar a recalibração do mês.",
        "Most are in Black Friday 2017 and between February and March 2018. The week of May 14, 2018 probably caught the "
        "Brazilian truckers' strike with orders still in transit. When a week falls out of bounds, that period's promise needs "
        "review without waiting for the monthly recalibration.",
    ))
    caixa(L(
        "**O que fazer quando uma semana sai da faixa:** alongar a promessa da região que puxou a queda até a pontualidade "
        "voltar pra faixa normal. A recalibração mensal do modelo pega o resto.",
        "**What to do when a week leaves the band:** lengthen the promise for the region driving the drop until on-time "
        "performance returns to the normal band. The model's monthly recalibration handles the rest.",
    ), "ambar")
    t = fora[["dia_compra", "pedidos", "taxa", "lic"]].copy()
    t["dia_compra"] = t.dia_compra.dt.strftime("%d/%m/%Y")
    t.columns = [L("semana de", "week of"), L("pedidos", "orders"), L("% no prazo", "% on time"), L("limite inferior", "lower limit")]
    st.dataframe(t, hide_index=True, width="stretch", column_config={
        L("% no prazo", "% on time"): st.column_config.NumberColumn(format="percent"),
        L("limite inferior", "lower limit"): st.column_config.NumberColumn(format="percent"),
    })

    st.info(L(
        f"**Próximo passo:** esse monitoramento vai virar o **Vulcão**, agente de logística do "
        f"[Dashboard Inteligente]({LINKS['dashboard']}), que avisa quando a semana sai do controle e qual região puxou a queda.",
        f"**Next step:** this monitoring will become **Vulcão**, the logistics agent in the "
        f"[Intelligent Dashboard]({LINKS['dashboard']}), which flags when a week goes out of control and which region drove the drop.",
    ), icon="🌋")
